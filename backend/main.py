from fastapi import FastAPI
from backend.database import Base, engine
from backend.models import (
    airport, flight, user, booking, traveller,
    billing_address, seat, booking_seat, meal, booking_meal, payment
)
from backend.routers import flight_routes
from backend.utils.background_demand import simulate_demand  
import asyncio

from backend.routers import booking_routes

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Flight Booking API")

app.include_router(flight_routes.router)

app.include_router(booking_routes.router)


@app.on_event("startup")
async def start_background_tasks():
    """
    Start background simulation when app starts.
    """
    loop = asyncio.get_event_loop()
    loop.create_task(simulate_demand())
    print("Background demand simulation started...")


@app.get("/")
def home():
    return {"message": "Welcome to Flight Booking API"}
