from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from .resort import Resort
from .weather import WeatherForecast
from .snow import SnowConditions
from .transport import Journey


class Recommendation(BaseModel):
    resort: Resort
    score: float
    weather_score: float
    snow_score: float
    transport_score: float
    size_score: float = 5.0
    weather_forecast: Optional[WeatherForecast] = None
    snow_conditions: Optional[SnowConditions] = None
    journey: Optional[Journey] = None
    highlights: List[str] = []
    concerns: List[str] = []
    reasoning: str = ""


class RecommendationsResponse(BaseModel):
    recommendations: List[Recommendation]
    ai_summary: str
    generated_at: datetime
    target_weekend: str
