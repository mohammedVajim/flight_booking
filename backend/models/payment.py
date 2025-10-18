from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    booking_id = Column(Integer, ForeignKey("bookings.booking_id"), nullable=False)
    payment_method = Column(String, nullable=False)
    payment_time = Column(String, nullable=False)  # ISO datetime as string
    amount = Column(Float, nullable=False)
    status = Column(String, nullable=False)

    booking = relationship("Booking", backref="payments")
