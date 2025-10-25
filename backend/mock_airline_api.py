# backend/mock_airline_api.py
import random
from datetime import datetime, timedelta

def fetch_external_flights():
    """Simulate external airline API returning mock flights consistent with existing airport data."""
    airlines = ["IndiGo", "Air India", "Vistara", "SpiceJet"]
    routes = [
        ("Chennai", "Delhi", 4100),
        ("Delhi", "Bengaluru", 4800),
        ("Bengaluru", "Mumbai", 4600),
        ("Mumbai", "Chennai", 4300),
    ]

    today = datetime.now().date()
    mock_flights = []

    for route in routes:
        origin, destination, base_fare = route
        dep_time = datetime.combine(today, datetime.min.time()) + timedelta(hours=random.randint(6, 20))
        arr_time = dep_time + timedelta(hours=random.choice([2, 2.5, 3]))

        mock_flights.append({
            "company_name": random.choice(airlines),
            "flight_code": f"{random.choice(['AI', 'SG', '6E', 'UK'])}{random.randint(100,999)}",
            "origin": origin,
            "destination": destination,
            "departure_time": dep_time.isoformat(),
            "arrival_time": arr_time.isoformat(),
            "duration_minutes": int((arr_time - dep_time).total_seconds() / 60),
            "stops": random.choice([0, 1]),
            "base_fare": base_fare,
            "travel_class": random.choice(["Economy", "Business"])
        })

    return mock_flights
