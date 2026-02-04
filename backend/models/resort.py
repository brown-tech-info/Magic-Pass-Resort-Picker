from pydantic import BaseModel
from typing import Optional


class Coordinates(BaseModel):
    latitude: float
    longitude: float


class AccessInfo(BaseModel):
    nearest_station: str
    postbus_required: bool = False
    postbus_duration_minutes: Optional[int] = None


class Resort(BaseModel):
    id: str
    name: str
    region: str
    canton: Optional[str] = None  # None for French/Italian resorts
    country: str = "Switzerland"
    coordinates: Coordinates
    elevation_base: int
    elevation_top: int
    access: AccessInfo
    website: str
    magic_pass_valid: bool = True
    snow_forecast_slug: Optional[str] = None
    skiable_terrain_km: Optional[float] = None
