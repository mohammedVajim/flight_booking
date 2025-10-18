from sqlalchemy import Column, Integer, String, Float, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from backend.database import Base

class Seat(Base):
    __tablename__ = "seats"

    seat_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    flight_id = Column(Integer, ForeignKey("flights.flight_id"), nullable=False)
    seat_number = Column(String, nullable=False)
    travel_class = Column(String, nullable=False)
    is_booked = Column(Integer, nullable=False, default=0)
    seat_price = Column(Float, nullable=False)

    __table_args__ = (
        CheckConstraint("travel_class IN ('Economy', 'Business', 'First')", name="check_travel_class"),
    )

    flight = relationship("Flight", back_populates="seats")
