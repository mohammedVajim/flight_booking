from sqlalchemy.orm import Session
from backend.database import engine, Base, get_db
from backend.models.airport import Airport
from backend.models.flight import Flight
from backend.models.user import User
from backend.models.meal import Meal
from backend.models.seat import Seat

# Create all tables
Base.metadata.create_all(bind=engine)

# Function to populate sample data
def populate_sample_data():
    db: Session = Session(bind=engine)

    # ----------------------
    # Airports
    # ----------------------
    airports = [
        Airport(name="Chennai International", city="Chennai", country="India", code="MAA"),
        Airport(name="Delhi Indira Gandhi", city="Delhi", country="India", code="DEL"),
        Airport(name="Bengaluru International", city="Bengaluru", country="India", code="BLR"),
        Airport(name="Mumbai Chhatrapati Shivaji", city="Mumbai", country="India", code="BOM"),
    ]
    db.add_all(airports)
    db.commit()

    # ----------------------
    # Flights
    # ----------------------
    flights = [
        Flight(
            company_name="IndiGo",
            flight_code="6E123",
            origin_airport_id=1,
            destination_airport_id=2,
            departure_time="2025-10-22T06:30:00",
            arrival_time="2025-10-22T08:30:00",
            duration_minutes=120,
            stops=0,
            base_fare=4000,
            travel_class="Economy"
        ),
        Flight(
            company_name="Air India",
            flight_code="AI456",
            origin_airport_id=2,
            destination_airport_id=3,
            departure_time="2025-10-23T09:00:00",
            arrival_time="2025-10-23T11:30:00",
            duration_minutes=150,
            stops=0,
            base_fare=5000,
            travel_class="Business"
        ),
        Flight(
            company_name="SpiceJet",
            flight_code="SG789",
            origin_airport_id=3,
            destination_airport_id=4,
            departure_time="2025-10-24T14:00:00",
            arrival_time="2025-10-24T16:00:00",
            duration_minutes=120,
            stops=0,
            base_fare=4500,
            travel_class="Economy"
        ),
    ]
    db.add_all(flights)
    db.commit()

    # ----------------------
    # Users
    # ----------------------
    users = [
        User(name="Nagavalli M", email="nagavalli@example.com", phone="9876543210"),
        User(name="Arun Kumar", email="arun@example.com", phone="9123456780"),
    ]
    db.add_all(users)
    db.commit()

    # ----------------------
    # Meals
    # ----------------------
    meals = [
        Meal(meal_name="Veg Meal", description="Vegetarian meal", price=300),
        Meal(meal_name="Non-Veg Meal", description="Non-vegetarian meal", price=350),
        Meal(meal_name="Snacks", description="Light snacks", price=150),
    ]
    db.add_all(meals)
    db.commit()

    # ----------------------
    # Seats
    # ----------------------
    seats = []
    seat_classes = ["Economy", "Business", "First"]
    for flight_id in range(1, 4):  # 3 flights
        seat_number = 1
        for cls in seat_classes:
            for _ in range(5):  # 5 seats per class
                seats.append(
                    Seat(
                        flight_id=flight_id,
                        seat_number=f"{cls[0]}{seat_number}",
                        travel_class=cls,
                        is_booked=0,
                        seat_price=1000 + seat_number * 200
                    )
                )
                seat_number += 1
    db.add_all(seats)
    db.commit()

    print("Sample data populated successfully!")

# ----------------------
# Run the function
# ----------------------
if __name__ == "__main__":
    populate_sample_data()
