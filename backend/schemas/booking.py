from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional

# Step 1: Initiate / Seat selection
class SeatSelectionRequest(BaseModel):
    user_id: int
    flight_id: int
    seat_ids: List[int] = Field(..., min_items=1)
    hold_minutes: Optional[int] = Field(15, description="How long to hold seats (minutes)")

class SeatSelectionResponse(BaseModel):
    booking_id: int
    pnr: str
    flight_id: int
    reserved_seat_ids: List[int]
    total_price: float
    status: str
    timer_expiry: str

# Step 2: Passenger info
class TravellerInfo(BaseModel):
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    dob: Optional[str] = None
    government_id_type: Optional[str] = None
    government_id_number: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class PassengerInfoRequest(BaseModel):
    booking_id: int
    travellers: List[TravellerInfo]

class PassengerInfoResponse(BaseModel):
    booking_id: int
    travellers_created: int

# Step 3: Payment
class PaymentRequest(BaseModel):
    booking_id: int
    simulate_success: Optional[bool] = Field(True, description="True => success, False => fail")

class PaymentResponse(BaseModel):
    booking_id: int
    status: str
    pnr: Optional[str] = None
    message: Optional[str] = None
