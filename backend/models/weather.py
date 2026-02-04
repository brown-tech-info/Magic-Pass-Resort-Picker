from pydantic import BaseModel
from datetime import date
from typing import Optional


class WeatherForecast(BaseModel):
    date: date
    temperature_min: float
    temperature_max: float
    precipitation_mm: float = 0.0
    snowfall_cm: Optional[float] = None
    wind_speed: float = 0.0
    wind_direction: str = "N"
    cloud_cover: int = 0
    visibility: str = "Good"
    conditions: str = ""
    icon: str = ""
