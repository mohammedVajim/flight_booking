# backend/utils/dynamic_pricing.py
from datetime import datetime
from math import ceil
from typing import Dict, Any

from sqlalchemy.orm import Session
from backend import models

def _parse_departure_time(departure_value):
    """
    Normalize departure_time stored as str or datetime.
    Returns a datetime object.
    """
    if departure_value is None:
        return None
    if isinstance(departure_value, datetime):
        return departure_value
    # assume ISO format string
    try:
        return datetime.fromisoformat(departure_value)
    except Exception:
        # last fallback: try common formats
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(departure_value, fmt)
            except Exception:
                continue
    return None


def calculate_dynamic_price(flight_id: int, db: Session) -> Dict[str, Any]:
    """
    Calculate dynamic price for the given flight_id using:
      - remaining seat percentage
      - time until departure
      - simulated demand level
      - base fare & pricing tiers

    Returns a dict with breakdown and final_price.
    """
    # Fetch flight
    flight = db.query(models.flight.Flight).filter(models.flight.Flight.flight_id == flight_id).first()
    if not flight:
        raise ValueError(f"Flight id {flight_id} not found")

    # Base fare
    base_fare = float(getattr(flight, "base_fare", 0) or 0)

    # 1) Seats: total seats for this flight
    total_seats = db.query(models.seat.Seat).filter(models.seat.Seat.flight_id == flight_id).count()

    # booked seats via BookingSeat association
    booked_via_bookingseat = db.query(models.booking_seat.BookingSeat) \
        .join(models.seat.Seat, models.booking_seat.BookingSeat.seat_id == models.seat.Seat.seat_id) \
        .filter(models.seat.Seat.flight_id == flight_id).count()

    # booked seats via seat.is_booked flag (if maintained)
    booked_flag_count = db.query(models.seat.Seat).filter(
        models.seat.Seat.flight_id == flight_id,
        models.seat.Seat.is_booked == 1
    ).count()

    # take the higher (conservative)
    booked_seats = max(booked_via_bookingseat, booked_flag_count)

    # available seats
    available_seats = max(total_seats - booked_seats, 0)

    # safety: if total_seats is 0 then we cannot compute percentage
    if total_seats == 0:
        remaining_pct = 0.0
    else:
        remaining_pct = round(available_seats / total_seats, 4)  # fraction

    # 2) Time until departure (in hours)
    dep_dt = _parse_departure_time(getattr(flight, "departure_time", None))
    now = datetime.utcnow()
    if dep_dt is None:
        hours_until_departure = None
    else:
        # compute hours (could be negative if in past)
        hours_until_departure = max((dep_dt - now).total_seconds() / 3600.0, -1.0)

    # 3) Simulated demand level
    # Use number of bookings for this flight in DB as demand proxy
    demand_count = db.query(models.booking.Booking).filter(models.booking.Booking.flight_id == flight_id).count()

    # Normalize demand: bookings per seat (if seats known)
    if total_seats > 0:
        demand_ratio = demand_count / total_seats
    else:
        demand_ratio = float(demand_count)

    # 4) Pricing logic: start with base_fare, apply multiplicative factors
    price = base_fare

    breakdown = {
        "base_fare": round(base_fare, 2),
        "factors": {},
        "final_price": None
    }

    # Factor A: Remaining seat percentage effect (scarcity)
    # If few seats left -> stronger multiplier
    if total_seats == 0:
        seat_multiplier = 1.0
        breakdown["factors"]["seat_multiplier"] = seat_multiplier
        breakdown["factors"]["available_seats"] = available_seats
        breakdown["factors"]["total_seats"] = total_seats
        breakdown["factors"]["remaining_pct"] = remaining_pct
    else:
        # exact numeric logic:
        # remaining_pct <= 0.05 => 2.0x
        # remaining_pct <= 0.2 => 1.5x
        # remaining_pct <= 0.5 => 1.2x
        # else => 1.0x
        if remaining_pct <= 0.05:
            seat_multiplier = 2.0
        elif remaining_pct <= 0.20:
            seat_multiplier = 1.5
        elif remaining_pct <= 0.50:
            seat_multiplier = 1.2
        else:
            seat_multiplier = 1.0

        price *= seat_multiplier
        breakdown["factors"]["seat_multiplier"] = seat_multiplier
        breakdown["factors"]["available_seats"] = available_seats
        breakdown["factors"]["total_seats"] = total_seats
        breakdown["factors"]["remaining_pct"] = remaining_pct

    # Factor B: Time-to-departure effect
    # If departure very near -> increase price
    time_multiplier = 1.0
    if hours_until_departure is None:
        time_multiplier = 1.0
    else:
        # hours -> apply multipliers conservatively
        # < 6 hours => 1.5x
        # < 24 hours => 1.3x
        # < 72 hours => 1.1x
        # else => 1.0
        if hours_until_departure < 0:
            # flight already departed - keep price same
            time_multiplier = 1.0
        elif hours_until_departure < 6:
            time_multiplier = 1.5
        elif hours_until_departure < 24:
            time_multiplier = 1.3
        elif hours_until_departure < 72:
            time_multiplier = 1.1
        else:
            time_multiplier = 1.0

    price *= time_multiplier
    breakdown["factors"]["time_multiplier"] = time_multiplier
    breakdown["factors"]["hours_until_departure"] = round(hours_until_departure, 2) if hours_until_departure is not None else None

    # Factor C: Simulated demand effect (bookings / seats)
    # If demand_ratio is high -> increase price
    # demand_ratio >= 0.5 => 1.4x, >=0.3 => 1.2x, >=0.1 => 1.1x
    demand_multiplier = 1.0
    if demand_ratio >= 0.5:
        demand_multiplier = 1.4
    elif demand_ratio >= 0.3:
        demand_multiplier = 1.2
    elif demand_ratio >= 0.1:
        demand_multiplier = 1.1
    else:
        demand_multiplier = 1.0

    price *= demand_multiplier
    breakdown["factors"]["demand_multiplier"] = demand_multiplier
    breakdown["factors"]["demand_count"] = demand_count
    breakdown["factors"]["demand_ratio"] = round(demand_ratio, 4)

    # Factor D: Travel class premium
    # If flight has a travel_class attribute use it; otherwise no-op
    travel_class = getattr(flight, "travel_class", None)
    class_multiplier = 1.0
    if travel_class:
        tc = str(travel_class).lower()
        if "business" in tc:
            class_multiplier = 1.6
        elif "first" in tc:
            class_multiplier = 2.2
        else:
            class_multiplier = 1.0

    price *= class_multiplier
    breakdown["factors"]["class_multiplier"] = class_multiplier
    breakdown["factors"]["travel_class"] = travel_class

    # Pricing tiers / caps
    # Minimum fare floor: 0.7 * base_fare
    # Maximum fare cap: 4.0 * base_fare (protective cap)
    min_price = round(base_fare * 0.7, 2)
    max_price = round(base_fare * 4.0, 2)

    # final rounding and clamp
    final_price = round(price, 2)
    if final_price < min_price:
        final_price = min_price
    if final_price > max_price:
        final_price = max_price

    # For friendly UI show integer rupee value (ceil to avoid selling at fraction)
    final_price_display = float(ceil(final_price))

    breakdown["final_price"] = final_price_display
    breakdown["min_price"] = min_price
    breakdown["max_price"] = max_price
    breakdown["raw_calculated_price"] = round(price, 2)

    return breakdown
