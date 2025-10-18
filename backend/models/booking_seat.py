from sqlalchemy import Column, Integer, ForeignKey, Float
from sqlalchemy.orm import relationship
from backend.database import Base

class BookingSeat(Base):
    __tablename__ = "booking_seats"

    booking_seat_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    booking_id = Column(Integer, ForeignKey("bookings.booking_id"), nullable=False)
    traveller_id = Column(Integer, ForeignKey("travellers.traveller_id"), nullable=False)
    seat_id = Column(Integer, ForeignKey("seats.seat_id"), nullable=False)
    seat_price = Column(Float, nullable=False)

    booking = relationship("Booking", backref="booking_seats")
    traveller = relationship("Traveller", backref="booking_seats")
    seat = relationship("Seat", backref="booking_seats")
