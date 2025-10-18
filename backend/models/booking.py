from sqlalchemy import Column, Integer, String, ForeignKey, Float, CheckConstraint
from sqlalchemy.orm import relationship
from backend.database import Base

class Booking(Base):
    __tablename__ = "bookings"

    booking_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    flight_id = Column(Integer, ForeignKey("flights.flight_id"), nullable=False)
    booking_date = Column(String, nullable=False)  # Use String for ISO datetime
    trip_type = Column(String, nullable=False)
    return_date = Column(String, nullable=True)
    travellers_count = Column(Integer, nullable=False)
    travel_class = Column(String, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    pnr = Column(String, unique=True, nullable=True)
    timer_expiry = Column(String, nullable=True)

    __table_args__ = (
        CheckConstraint("trip_type IN ('One Way', 'Round Trip')", name="check_trip_type"),
    )

    user = relationship("User", backref="bookings")
    flight = relationship("Flight", backref="bookings")
