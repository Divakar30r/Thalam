# Timestamp handling utilities

from datetime import datetime, timezone
from typing import Union, Optional
import time

def get_current_timestamp_ms() -> int:
    """Get current timestamp in milliseconds"""
    return int(time.time() * 1000)

def get_current_timestamp_iso() -> str:
    """Get current timestamp in ISO format"""
    return datetime.utcnow().isoformat() + "Z"

def get_mongo_timestamp() -> dict:
    """Get MongoDB compatible timestamp format"""
    return {"$date": get_current_timestamp_iso()}

def timestamp_ms_to_datetime(timestamp_ms: int) -> datetime:
    """Convert millisecond timestamp to datetime"""
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)

def datetime_to_timestamp_ms(dt: datetime) -> int:
    """Convert datetime to millisecond timestamp"""
    return int(dt.timestamp() * 1000)

def format_follow_up_id(order_req_id: str, timestamp_ms: Optional[int] = None) -> str:
    """Generate follow-up ID with timestamp"""
    if timestamp_ms is None:
        timestamp_ms = get_current_timestamp_ms()
    return f"{order_req_id}-{timestamp_ms}"

def is_expired(expiry_ms: int, current_ms: Optional[int] = None) -> bool:
    """Check if timestamp has expired"""
    if current_ms is None:
        current_ms = get_current_timestamp_ms()
    return current_ms > expiry_ms

def add_minutes_to_timestamp(timestamp_ms: int, minutes: int) -> int:
    """Add minutes to a millisecond timestamp"""
    return timestamp_ms + (minutes * 60 * 1000)

def add_expiry_time(minutes: int = 30) -> int:
    """Get expiry timestamp (current time + minutes)"""
    current_ms = get_current_timestamp_ms()
    return add_minutes_to_timestamp(current_ms, minutes)