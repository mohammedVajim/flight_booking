from fastapi import FastAPI
from backend.database import Base, engine
from backend.models import airport, flight, user, booking, traveller, billing_address, seat, booking_seat, meal, booking_meal, payment
from backend.routers import flight_routes 

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Flight Booking API")

app.include_router(flight_routes.router)

@app.get("/")
def home():
    return {"message": "Welcome to Flight Booking API"}



    

