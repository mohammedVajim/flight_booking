from backend.database import Base, engine
from backend.models import airport, flight, user, booking, traveller, billing_address, seat, booking_seat, meal, booking_meal, payment

# Create all tables
Base.metadata.create_all(bind=engine)

print("✅ Database and tables created successfully!")

