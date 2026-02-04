from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class JourneySegment(BaseModel):
    type: str  # "train" or "bus"
    from_station: str
    to_station: str
    departure: datetime
    arrival: datetime
    line: str


class Journey(BaseModel):
    departure_time: datetime
    arrival_time: datetime
    duration_minutes: int
    changes: int
    segments: List[JourneySegment] = []
