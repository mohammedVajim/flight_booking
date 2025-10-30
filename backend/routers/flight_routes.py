from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload, aliased
from backend import models, database
from backend.schemas.flight import FlightSearchParams

from backend.mock_airline_api import fetch_external_flights
from datetime import datetime

from backend.utils.dynamic_pricing import calculate_dynamic_price

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

@router.get("/search")
def search_flights(
    origin: str = Query(..., description="Origin city name"),
    destination: str = Query(..., description="Destination city name"),
    date: str = Query(..., description="Departure date (YYYY-MM-DD)"),
    sort_by: str = Query(None, description="Sort by 'price' or 'duration'"),
    db: Session = Depends(database.get_db)
):

    origin_airport = aliased(models.airport.Airport)
    destination_airport = aliased(models.airport.Airport)

    # Base query
    query = (
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
    )

    # Apply sorting before fetching results
    if sort_by == "price":
        query = query.order_by(models.flight.Flight.base_fare)
    elif sort_by == "duration":
        query = query.order_by(models.flight.Flight.duration_minutes)

    flights = query.all()
    if not flights:
        raise HTTPException(status_code=404, detail="No flights found for given criteria")

    # Build response list with dynamic price
    results = []
    for f in flights:
        try:
            pricing = calculate_dynamic_price(f.flight_id, db)
            dynamic_price = pricing.get("final_price", f.base_fare)
        except Exception:
            dynamic_price = f.base_fare  # fallback if pricing fails

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
            "dynamic_price": dynamic_price, 
            "travel_class": f.travel_class
        })

    if sort_by == "price":
        results.sort(key=lambda x: x["dynamic_price"])
    elif sort_by == "duration":
        results.sort(key=lambda x: x["duration_minutes"])

    return results




@router.post("/sync")
def sync_external_flights(db: Session = Depends(database.get_db)):
   
    external_flights = fetch_external_flights()
    added_count = 0

    for flight_data in external_flights:
        # Match origin and destination airports
        origin = db.query(models.airport.Airport).filter(
            models.airport.Airport.city.ilike(flight_data["origin"])
        ).first()
        destination = db.query(models.airport.Airport).filter(
            models.airport.Airport.city.ilike(flight_data["destination"])
        ).first()

        if not origin or not destination:
            continue

        existing = db.query(models.flight.Flight).filter(
            models.flight.Flight.flight_code == flight_data["flight_code"],
            models.flight.Flight.origin_airport_id == origin.airport_id,
            models.flight.Flight.destination_airport_id == destination.airport_id,
        ).first()
        if existing:
            continue

        # Create new flight
        new_flight = models.flight.Flight(
            company_name=flight_data["company_name"],
            flight_code=flight_data["flight_code"],
            origin_airport_id=origin.airport_id,
            destination_airport_id=destination.airport_id,
            departure_time=datetime.fromisoformat(flight_data["departure_time"]),
            arrival_time=datetime.fromisoformat(flight_data["arrival_time"]),
            duration_minutes=flight_data["duration_minutes"],
            stops=flight_data["stops"],
            base_fare=flight_data["base_fare"],
            travel_class=flight_data["travel_class"]
        )

        db.add(new_flight)
        added_count += 1

    db.commit()

    if added_count == 0:
        raise HTTPException(status_code=200, detail="No new flights added. All routes up to date.")
    return {"message": f"{added_count} new flights synced successfully!"}

@router.get("/{flight_id}/dynamic_price", summary="Get dynamic price for a flight")
def get_dynamic_price(flight_id: int, db: Session = Depends(database.get_db)):
    """
    Returns dynamic price breakdown and final price for the given flight_id.
    """
    try:
        breakdown = calculate_dynamic_price(flight_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate price: {e}")

    return breakdown
