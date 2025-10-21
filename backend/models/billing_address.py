from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

class BillingAddress(Base):
    __tablename__ = "billing_address"

    address_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    booking_id = Column(Integer, ForeignKey("bookings.booking_id"), nullable=False)
    pin_code = Column(String, nullable=False)
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)

    booking = relationship("Booking", backref="billing_addresses")
"""Billing address linked to each booking (for invoices or receipts)."""
