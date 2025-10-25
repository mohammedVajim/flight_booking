from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class FlightSearchParams(BaseModel):
    origin: str = Field(..., min_length=2)
    destination: str = Field(..., min_length=2)
    date: str
    sort_by: Optional[str] = Field(None, description="Sort by 'price' or 'duration'")

    @validator("date")
    def validate_date(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v

    @validator("sort_by")
    def validate_sort(cls, v):
        if v and v not in ["price", "duration"]:
            raise ValueError("sort_by must be 'price' or 'duration'")
        return v
