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
    """
    Step 1: Flight & Seat Selection
    - Verify flight exists
    - Verify seats exist and belong to flight
    - Compute dynamic per-passenger price using calculate_dynamic_price
    - Compute total = dynamic_price_per_passenger * n + seat_addons
    - Reserve seats in a transaction and create a PENDING booking with timer_expiry
    """

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

    # get dynamic price per passenger (uses your dynamic_pricing engine)
    try:
        pricing = calculate_dynamic_price(payload.flight_id, db)
        dynamic_per_passenger = float(pricing.get("final_price", float(flight.base_fare)))
    except Exception:
        dynamic_per_passenger = float(getattr(flight, "base_fare", 0.0))

    # seat addons
    seat_addons_total = sum(float(getattr(s, "seat_price", 0.0) or 0.0) for s in seats)
    total_price = dynamic_per_passenger * len(seats) + seat_addons_total
    total_price = round(total_price, 2)

    # prepare values
    temp_pnr = "TMP" + _gen_pnr(5)
    timer_expiry = datetime.utcnow() + timedelta(minutes=payload.hold_minutes or 15)

    # transactional reservation
    try:
        with db.begin():
            # re-query seats inside transaction
            seats_tx = db.query(Seat).filter(Seat.seat_id.in_(seat_ids)).with_for_update(read=False).all()
            # re-check availability
            for s in seats_tx:
                if int(s.is_booked) == 1:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                        detail=f"Seat {s.seat_id} already booked/reserved")

            # reserve seats
            for s in seats_tx:
                s.is_booked = 1
                db.add(s)

            # create booking (PENDING)
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
            # flush/commit at context exit

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
    """
    Step 2: Add travellers (passenger info).
    Creates Traveller rows and BookingSeat rows linking traveller -> seat.
    Expects that initiate_booking reserved seats and created the booking.
    """
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # fetch reserved seat ids for this booking (we did not create BookingSeat earlier)
    # But we can match by seats that are marked is_booked and belong to the flight and count matches.
    # Simpler: request must include same number of travellers as booking.travellers_count (validate)
    if len(payload.travellers) != int(booking.travellers_count):
        raise HTTPException(status_code=400, detail="Number of travellers must match reserved seats count")

    try:
        with db.begin():
            created = 0
            # fetch seats that are reserved for this booking's flight and currently is_booked=1 but not yet linked
            # We will assign travellers to any of the reserved seats (best-effort)
            reserved_seats = db.query(Seat).filter(
                Seat.flight_id == booking.flight_id,
                Seat.is_booked == 1
            ).all()

            # Note: This picks from all reserved seats on flight; a production flow should track exact seat_ids reserved per booking.
            # We'll assign the first N seats from reserved_seats that are not already linked in booking_seats.
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
                db.flush()  # to get traveller_id

                # attach to a seat (the next assignable seat)
                seat_obj = assignable[idx]
                bs = BookingSeat(
                    booking_id=booking.booking_id,
                    traveller_id=t.traveller_id,
                    seat_id=seat_obj.seat_id,
                    seat_price=seat_obj.seat_price
                )
                db.add(bs)
                created += 1

            # commit at context exit
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB error adding passengers: {e}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected: {e}")

    return PassengerInfoResponse(booking_id=booking_id, travellers_created=created)


@router.post("/{booking_id}/pay", response_model=PaymentResponse)
def process_payment(booking_id: int, payload: PaymentRequest, db: Session = Depends(get_db)):
    """
    Step 3: Simulated payment.
    If success -> set booking.status = CONFIRMED and generate unique PNR (ensuring uniqueness).
    If fail -> set booking.status = FAILED and release seats (is_booked = 0) that were reserved for this booking.
    Always record a Payment row.
    """
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status == "CONFIRMED":
        return PaymentResponse(booking_id=booking_id, status="ALREADY_CONFIRMED", pnr=booking.pnr, message="Booking already confirmed")

    # fetch linked booking seats
    linked_bs = db.query(BookingSeat).filter(BookingSeat.booking_id == booking_id).all()
    linked_seat_ids = [bs.seat_id for bs in linked_bs]

    # simulate payment
    success = bool(payload.simulate_success)

    try:
        with db.begin():
            # write payment record
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
                    # fallback deterministic PNR
                    pnr = f"PNR{booking.booking_id:06d}"

                booking.status = "CONFIRMED"
                booking.pnr = pnr
                db.add(booking)
                # seats already set is_booked=1 from initiate, keep them booked
            else:
                # payment failed => release seats reserved by this booking
                # find seats linked to this booking via booking_seats
                for seat_id in linked_seat_ids:
                    s = db.query(Seat).filter(Seat.seat_id == seat_id).first()
                    if s:
                        s.is_booked = 0
                        db.add(s)
                booking.status = "FAILED"
                db.add(booking)

            # commit on context exit

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
