from sqlalchemy import Column, Integer, String, Float, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from backend.database import Base

class Flight(Base):
    __tablename__ = "flights"

    flight_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_name = Column(String, nullable=False)
    flight_code = Column(String, nullable=False)
    origin_airport_id = Column(Integer, ForeignKey("airports.airport_id"), nullable=False)
    destination_airport_id = Column(Integer, ForeignKey("airports.airport_id"), nullable=False)
    departure_time = Column(String, nullable=False)  # Use String for ISO datetime
    arrival_time = Column(String, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    stops = Column(Integer, nullable=False)
    base_fare = Column(Float, nullable=False)
    travel_class = Column(String, nullable=False)

    __table_args__ = (
        CheckConstraint("travel_class IN ('Economy', 'Business', 'First')", name="check_travel_class"),
        CheckConstraint("origin_airport_id != destination_airport_id", name="check_airports_different"),
    )

    # Define relationships for easier access if needed
    origin_airport = relationship("Airport", foreign_keys=[origin_airport_id])
    destination_airport = relationship("Airport", foreign_keys=[destination_airport_id])

    seats = relationship("Seat", back_populates="flight", cascade="all, delete-orphan")

