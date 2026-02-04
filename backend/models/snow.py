from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SnowConditions(BaseModel):
    resort_id: str
    date_updated: datetime
    snow_base: Optional[int] = None
    snow_summit: Optional[int] = None
    new_snow_24h: Optional[int] = None
    new_snow_7d: Optional[int] = None
    snow_quality: str = "Unknown"
    lifts_open: Optional[int] = None
    runs_open: Optional[int] = None
