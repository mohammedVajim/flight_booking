from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload, aliased
from backend import models, database

# ✅ Router instance
router = APIRouter(prefix="/flights", tags=["Flights"])

# ----------------------
# 1. Retrieve all flights
# ----------------------
@router.get("/")
def get_all_flights(db: Session = Depends(database.get_db)):
    """
    Retrieve all flights with readable origin and destination
    """
    flights = (
        db.query(models.flight.Flight)
        .options(
            joinedload(models.flight.Flight.origin_airport),
            joinedload(models.flight.Flight.destination_airport)
        )
        .all()
    )

    results = []
    for f in flights:
        results.append({
            "flight_code": f.flight_code,
            "company_name": f.company_name,
            "origin": f.origin_airport.city,
            "destination": f.destination_airport.city,
            "departure_time": f.departure_time,
            "arrival_time": f.arrival_time,
            "duration_minutes": f.duration_minutes,
            "stops": f.stops,
            "base_fare": f.base_fare,
            "travel_class": f.travel_class
        })
    return results

# ----------------------
# 2. Search flights by origin, destination, and date
# ----------------------
@router.get("/search")
def search_flights(origin: str, destination: str, date: str, db: Session = Depends(database.get_db)):
    """
    Search flights by origin city, destination city, and departure date (YYYY-MM-DD)
    """
    origin_airport = aliased(models.airport.Airport)
    destination_airport = aliased(models.airport.Airport)

    flights = (
        db.query(models.flight.Flight)
        .join(origin_airport, models.flight.Flight.origin_airport)
        .join(destination_airport, models.flight.Flight.destination_airport)
        .options(
            joinedload(models.flight.Flight.origin_airport),
            joinedload(models.flight.Flight.destination_airport)
        )
        .filter(origin_airport.city.ilike(f"%{origin}%"))
        .filter(destination_airport.city.ilike(f"%{destination}%"))
        .filter(models.flight.Flight.departure_time.like(f"{date}%"))
        .all()
    )

    if not flights:
        raise HTTPException(status_code=404, detail="No flights found for given criteria")

    results = []
    for f in flights:
        results.append({
            "flight_code": f.flight_code,
            "company_name": f.company_name,
            "origin": f.origin_airport.city,
            "destination": f.destination_airport.city,
            "departure_time": f.departure_time,
            "arrival_time": f.arrival_time,
            "duration_minutes": f.duration_minutes,
            "stops": f.stops,
            "base_fare": f.base_fare,
            "travel_class": f.travel_class
        })
    return results
