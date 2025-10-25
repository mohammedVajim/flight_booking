import asyncio
import random
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models.flight import Flight
from backend.models.seat import Seat


async def simulate_demand():
    """
    Background process that runs forever.
    Every few minutes it randomly changes seat booking status
    and updates the flight's dynamic price based on current demand.
    """
    while True:
        print("Simulating demand and availability changes...")
        db: Session = SessionLocal()

        try:
            flights = db.query(Flight).all()
            for flight in flights:
                seats = db.query(Seat).filter(Seat.flight_id == flight.flight_id).all()
                total_seats = len(seats)
                if total_seats == 0:
                    continue

                # Random number of seats booked (simulate demand)
                booked_count = random.randint(0, total_seats)

                # Mark seats as booked / available
                for i, seat in enumerate(seats):
                    seat.is_booked = 1 if i < booked_count else 0

                # Compute dynamic price based on demand
                availability_ratio = booked_count / total_seats  # 0.0 to 1.0
                dynamic_price = flight.base_fare * (1 + availability_ratio * 0.5)

                # Add a little random fluctuation (optional realism)
                dynamic_price *= random.uniform(0.95, 1.05)

                # Update flight base_fare or add a separate field if you prefer
                flight.base_fare = round(dynamic_price, 2)

            db.commit()
            print("Demand simulation updated successfully")

        except Exception as e:
            print("Error in background task:", e)
            db.rollback()
        finally:
            db.close()

        # Wait for 5 minutes before next update (you can change this)
        await asyncio.sleep(300)
