from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

class BookingMeal(Base):
    __tablename__ = "booking_meals"

    booking_meal_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    booking_id = Column(Integer, ForeignKey("bookings.booking_id"), nullable=False)
    traveller_id = Column(Integer, ForeignKey("travellers.traveller_id"), nullable=False)
    meal_id = Column(Integer, ForeignKey("meals.meal_id"), nullable=False)

    booking = relationship("Booking", backref="booking_meals")
    traveller = relationship("Traveller", backref="booking_meals")
    meal = relationship("Meal", backref="booking_meals")
