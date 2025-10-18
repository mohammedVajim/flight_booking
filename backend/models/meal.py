from sqlalchemy import Column, Integer, String, Float
from backend.database import Base

class Meal(Base):
    __tablename__ = "meals"

    meal_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    meal_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
