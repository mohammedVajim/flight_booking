from sqlalchemy import Column, Integer, String
from backend.database import Base 

class Airport(Base):
    __tablename__ = "airports"

    airport_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    country = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
"""Airport model: stores airport name, city, country, and unique IATA code."""
