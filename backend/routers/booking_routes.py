from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import datetime, timedelta
import secrets
import string

from backend.database import get_db
from backend import models
from backend.models.booking import Booking
from backend.models.seat import Seat
from backend.models.traveller import Traveller
from backend.models.booking_seat import BookingSeat
from backend.models.payment import Payment
from backend.utils.dynamic_pricing import calculate_dynamic_price
from backend.schemas.booking import (
    SeatSelectionRequest, SeatSelectionResponse,
    PassengerInfoRequest, PassengerInfoResponse,
    PaymentRequest, PaymentResponse, TravellerInfo
)

router = APIRouter(prefix="/bookings", tags=["Bookings"])


def _gen_pnr(length: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _ensure_unique_pnr(pnr_candidate: str, db: Session) -> bool:
    exists = db.query(Booking).filter(Booking.pnr == pnr_candidate).first()
    return exists is None


@router.post("/initiate", response_model=SeatSelectionResponse, status_code=201)
def initiate_booking(payload: SeatSelectionRequest, db: Session = Depends(get_db)):
 
    # basic checks
    flight = db.query(models.flight.Flight).filter(models.flight.Flight.flight_id == payload.flight_id).first()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")

    seat_ids = list(dict.fromkeys(payload.seat_ids))  # unique preserve order
    seats = db.query(Seat).filter(Seat.seat_id.in_(seat_ids)).all()
    if len(seats) != len(seat_ids):
        raise HTTPException(status_code=400, detail="One or more selected seats not found")

    # ensure seats belong to flight
    for s in seats:
        if s.flight_id != payload.flight_id:
            raise HTTPException(status_code=400, detail=f"Seat {s.seat_id} does not belong to flight {payload.flight_id}")

    # get dynamic price per passenger 
    try:
        pricing = calculate_dynamic_price(payload.flight_id, db)
        dynamic_per_passenger = float(pricing.get("final_price", float(flight.base_fare)))
    except Exception:
        dynamic_per_passenger = float(getattr(flight, "base_fare", 0.0))

    # seat addons
    seat_addons_total = sum(float(getattr(s, "seat_price", 0.0) or 0.0) for s in seats)
    total_price = dynamic_per_passenger * len(seats) + seat_addons_total
    total_price = round(total_price, 2)

    temp_pnr = "TMP" + _gen_pnr(5)
    timer_expiry = datetime.utcnow() + timedelta(minutes=payload.hold_minutes or 15)
    try:
        with db.begin():
            # re-query seats inside transaction
            seats_tx = db.query(Seat).filter(Seat.seat_id.in_(seat_ids)).with_for_update(read=False).all()
            # re-check availability
            for s in seats_tx:
                if int(s.is_booked) == 1:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                        detail=f"Seat {s.seat_id} already booked/reserved")

            for s in seats_tx:
                s.is_booked = 1
                db.add(s)

            new_booking = Booking(
                user_id=payload.user_id,
                flight_id=payload.flight_id,
                booking_date=datetime.utcnow().isoformat(),
                trip_type="One Way",
                return_date=None,
                travellers_count=len(seats_tx),
                travel_class=flight.travel_class,
                total_price=total_price,
                status="PENDING",
                pnr=temp_pnr,
                timer_expiry=timer_expiry.isoformat()
            )
            db.add(new_booking)

        # refresh booking to get id
        db.refresh(new_booking)

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB error during initiate: {e}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    return SeatSelectionResponse(
        booking_id=new_booking.booking_id,
        pnr=new_booking.pnr,
        flight_id=new_booking.flight_id,
        reserved_seat_ids=[int(s.seat_id) for s in seats],
        total_price=new_booking.total_price,
        status=new_booking.status,
        timer_expiry=new_booking.timer_expiry
    )


@router.post("/{booking_id}/passengers", response_model=PassengerInfoResponse)
def add_passengers(booking_id: int, payload: PassengerInfoRequest, db: Session = Depends(get_db)):
  
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if len(payload.travellers) != int(booking.travellers_count):
        raise HTTPException(status_code=400, detail="Number of travellers must match reserved seats count")

    try:
        with db.begin():
            created = 0
            reserved_seats = db.query(Seat).filter(
                Seat.flight_id == booking.flight_id,
                Seat.is_booked == 1
            ).all()

            existing_bs = db.query(BookingSeat).filter(BookingSeat.booking_id == booking_id).all()
            linked_seat_ids = {bs.seat_id for bs in existing_bs}

            assignable = [s for s in reserved_seats if s.seat_id not in linked_seat_ids]
            if len(assignable) < len(payload.travellers):
                raise HTTPException(status_code=400, detail="Not enough reserved seats available to attach travellers")

            for idx, trav_info in enumerate(payload.travellers):
                # create traveller
                t = Traveller(
                    booking_id=booking.booking_id,
                    first_name=trav_info.first_name,
                    middle_name=trav_info.middle_name,
                    last_name=trav_info.last_name,
                    dob=trav_info.dob,
                    government_id_type=trav_info.government_id_type,
                    government_id_number=trav_info.government_id_number,
                    email=trav_info.email,
                    phone=trav_info.phone
                )
                db.add(t)
                db.flush() 

                # attach to a seat
                seat_obj = assignable[idx]
                bs = BookingSeat(
                    booking_id=booking.booking_id,
                    traveller_id=t.traveller_id,
                    seat_id=seat_obj.seat_id,
                    seat_price=seat_obj.seat_price
                )
                db.add(bs)
                created += 1

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB error adding passengers: {e}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected: {e}")

    return PassengerInfoResponse(booking_id=booking_id, travellers_created=created)


@router.post("/{booking_id}/pay", response_model=PaymentResponse)
def process_payment(booking_id: int, payload: PaymentRequest, db: Session = Depends(get_db)):
  
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status == "CONFIRMED":
        return PaymentResponse(booking_id=booking_id, status="ALREADY_CONFIRMED", pnr=booking.pnr, message="Booking already confirmed")

    linked_bs = db.query(BookingSeat).filter(BookingSeat.booking_id == booking_id).all()
    linked_seat_ids = [bs.seat_id for bs in linked_bs]

    success = bool(payload.simulate_success)

    try:
        with db.begin():
            pay = Payment(
                booking_id=booking.booking_id,
                payment_method="SIMULATED",
                payment_time=datetime.utcnow().isoformat(),
                amount=booking.total_price,
                status="SUCCESS" if success else "FAILED"
            )
            db.add(pay)
            db.flush()

            if success:
                # generate unique PNR
                pnr_attempts = 0
                pnr = None
                while pnr_attempts < 6:
                    candidate = _gen_pnr(6)
                    if _ensure_unique_pnr(candidate, db):
                        pnr = candidate
                        break
                    pnr_attempts += 1

                if not pnr:
                    pnr = f"PNR{booking.booking_id:06d}"

                booking.status = "CONFIRMED"
                booking.pnr = pnr
                db.add(booking)
            else:
                for seat_id in linked_seat_ids:
                    s = db.query(Seat).filter(Seat.seat_id == seat_id).first()
                    if s:
                        s.is_booked = 0
                        db.add(s)
                booking.status = "FAILED"
                db.add(booking)

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"PNR uniqueness or Integrity error: {e}")
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB error during payment: {e}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error during payment: {e}")

    return PaymentResponse(booking_id=booking.booking_id, status=booking.status, pnr=booking.pnr, message="Payment processed")

# Booking Cancellation
@router.post("/{booking_id}/cancel", status_code=200)
def cancel_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status not in ["CONFIRMED", "PENDING"]:
        raise HTTPException(status_code=400, detail="Only confirmed or pending bookings can be cancelled")

    try:
        with db.begin():
            linked_bs = db.query(BookingSeat).filter(BookingSeat.booking_id == booking_id).all()
            for bs in linked_bs:
                seat = db.query(Seat).filter(Seat.seat_id == bs.seat_id).first()
                if seat:
                    seat.is_booked = 0
                    db.add(seat)

            # update booking
            booking.status = "CANCELLED"
            db.add(booking)

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB error cancelling booking: {e}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    return {"booking_id": booking.booking_id, "status": "CANCELLED", "message": "Booking cancelled and seats released."}

#Booking History Retrieval
@router.get("/history/{user_id}", status_code=200)
def get_booking_history(user_id: int, db: Session = Depends(get_db)):
    bookings = db.query(Booking).filter(Booking.user_id == user_id).all()
    if not bookings:
        raise HTTPException(status_code=404, detail="No bookings found for this user")

    history = []
    for b in bookings:
        # get travellers and seats
        travellers = db.query(Traveller).filter(Traveller.booking_id == b.booking_id).all()
        booking_seats = db.query(BookingSeat).filter(BookingSeat.booking_id == b.booking_id).all()

        seat_details = []
        for bs in booking_seats:
            seat = db.query(Seat).filter(Seat.seat_id == bs.seat_id).first()
            if seat:
                seat_details.append({
                    "seat_number": seat.seat_number,
                    "travel_class": seat.travel_class,
                    "price": seat.seat_price
                })

        history.append({
            "booking_id": b.booking_id,
            "pnr": b.pnr,
            "flight_id": b.flight_id,
            "status": b.status,
            "booking_date": b.booking_date,
            "travel_class": b.travel_class,
            "total_price": b.total_price,
            "travellers": [
                {
                    "first_name": t.first_name,
                    "last_name": t.last_name,
                    "email": t.email,
                    "phone": t.phone
                } for t in travellers
            ],
            "seats": seat_details
        })

    return {"user_id": user_id, "bookings": history}
