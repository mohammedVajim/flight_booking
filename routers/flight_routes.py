# backend/routers/flight_routes.py
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.flight import Flight
from backend.models.airport import Airport

router = APIRouter(prefix="/api/flights", tags=["Flights"])

# 1️⃣ Get all flights
@router.get("/")
def get_all_flights(db: Session = Depends(get_db)):
    flights = db.query(Flight).all()
    return flights


# 2️⃣ Search flights by origin, destination, and date
@router.get("/search")
def search_flights(
    origin: str = Query(..., description="Origin airport code"),
    destination: str = Query(..., description="Destination airport code"),
    date: str = Query(..., description="Departure date in YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    origin_airport = db.query(Airport).filter(Airport.code == origin).first()
    dest_airport = db.query(Airport).filter(Airport.code == destination).first()

    if not origin_airport or not dest_airport:
        raise HTTPException(status_code=404, detail="Invalid airport code")

    flights = (
        db.query(Flight)
        .filter(
            Flight.origin_airport_id == origin_airport.airport_id,
            Flight.destination_airport_id == dest_airport.airport_id,
            Flight.departure_time.like(f"{date}%")
        )
        .all()
    )

    if not flights:
        raise HTTPException(status_code=404, detail="No flights found")

    return flights
