import logging
from typing import List, Optional, Tuple

from models.weather import WeatherForecast
from models.snow import SnowConditions
from models.transport import Journey
from models.resort import Resort

logger = logging.getLogger(__name__)


class ScoringEngine:
    """Engine for scoring ski resorts based on weather, snow, transport, and size."""

    # Scoring weights
    WEATHER_WEIGHT = 0.20
    SNOW_WEIGHT = 0.45
    TRANSPORT_WEIGHT = 0.10
    SIZE_WEIGHT = 0.25

    # Penalty score for unavailable snow data
    SNOW_UNAVAILABLE_PENALTY = 2.5

    def score_weather(self, forecast: Optional[WeatherForecast]) -> Tuple[float, List[str], List[str]]:
        """
        Score weather conditions (0-10).

        Perfect (10): Sunny, -5 to -10C, fresh snow expected, good visibility
        Good (7-9): Partly cloudy, decent temps, some fresh snow
        Poor (0-3): Rain, warm temps, poor visibility
        """
        highlights = []
        concerns = []

        if not forecast:
            return 5.0, [], ["Weather data unavailable"]

        score = 5.0  # Base score

        # Temperature scoring (ideal: -5 to -10C)
        avg_temp = (forecast.temperature_min + forecast.temperature_max) / 2
        if -12 <= avg_temp <= -3:
            score += 2.0
            highlights.append(f"Perfect ski temperature ({avg_temp:.0f}C)")
        elif -15 <= avg_temp < -3 or -3 < avg_temp <= 0:
            score += 1.0
            highlights.append(f"Good temperature ({avg_temp:.0f}C)")
        elif avg_temp > 2:
            score -= 2.0
            concerns.append(f"Warm temperatures ({avg_temp:.0f}C) - possible slushy snow")
        elif avg_temp < -15:
            score -= 1.0
            concerns.append(f"Very cold ({avg_temp:.0f}C)")

        # Fresh snowfall scoring (enhanced bonuses for powder days)
        if forecast.snowfall_cm:
            if forecast.snowfall_cm >= 20:
                score += 3.5
                highlights.append(f"Heavy snowfall expected ({forecast.snowfall_cm:.0f}cm)")
            elif forecast.snowfall_cm >= 10:
                score += 2.5
                highlights.append(f"Good snowfall expected ({forecast.snowfall_cm:.0f}cm)")
            elif forecast.snowfall_cm >= 5:
                score += 1.0
                highlights.append(f"Some fresh snow expected ({forecast.snowfall_cm:.0f}cm)")

        # Cloud cover / visibility scoring (reduced bonus when sunny but no snow)
        if forecast.cloud_cover < 30:
            if forecast.snowfall_cm and forecast.snowfall_cm >= 5:
                score += 1.5
                highlights.append("Sunny conditions expected")
            else:
                score += 0.5
                highlights.append("Sunny conditions expected")
                concerns.append("Dry conditions - no fresh snow forecast")
        elif forecast.cloud_cover < 50:
            score += 0.5
            highlights.append("Partly cloudy")
        elif forecast.cloud_cover > 80:
            score -= 1.0
            concerns.append("Overcast conditions")

        # Wind scoring
        if forecast.wind_speed < 20:
            score += 0.5
        elif forecast.wind_speed > 50:
            score -= 2.0
            concerns.append(f"Strong winds ({forecast.wind_speed:.0f}km/h)")
        elif forecast.wind_speed > 35:
            score -= 1.0
            concerns.append(f"Moderate winds ({forecast.wind_speed:.0f}km/h)")

        # Precipitation penalty (rain is bad)
        if forecast.precipitation_mm > 0 and not forecast.snowfall_cm:
            if avg_temp > 0:
                score -= 3.0
                concerns.append("Rain expected")

        # Clamp score to 0-10
        score = max(0.0, min(10.0, score))
        return round(score, 1), highlights, concerns

    def score_snow(self, conditions: Optional[SnowConditions]) -> Tuple[float, List[str], List[str]]:
        """
        Score snow conditions (0-10).

        Perfect (10): 150+ cm base, 20+ cm fresh, powder
        Good (7-9): 100+ cm base, some fresh snow, good quality
        Poor (0-3): <50cm base, no fresh snow, icy
        """
        highlights = []
        concerns = []

        if not conditions:
            return self.SNOW_UNAVAILABLE_PENALTY, [], ["Snow data unavailable - conditions unknown"]

        score = 5.0  # Base score

        # Base depth scoring
        if conditions.snow_base:
            if conditions.snow_base >= 150:
                score += 2.5
                highlights.append(f"Excellent base depth ({conditions.snow_base}cm)")
            elif conditions.snow_base >= 100:
                score += 1.5
                highlights.append(f"Good base depth ({conditions.snow_base}cm)")
            elif conditions.snow_base >= 60:
                score += 0.5
            elif conditions.snow_base < 40:
                score -= 2.0
                concerns.append(f"Low snow base ({conditions.snow_base}cm)")

        # Fresh snow scoring (enhanced bonuses for powder days)
        if conditions.new_snow_24h:
            if conditions.new_snow_24h >= 20:
                score += 3.0
                highlights.append(f"Fresh powder! ({conditions.new_snow_24h}cm in 24h)")
            elif conditions.new_snow_24h >= 10:
                score += 2.0
                highlights.append(f"Fresh snow ({conditions.new_snow_24h}cm in 24h)")
            elif conditions.new_snow_24h >= 5:
                score += 1.0

        # Weekly snowfall can indicate recent good conditions
        if conditions.new_snow_7d:
            if conditions.new_snow_7d >= 50:
                score += 1.0
                highlights.append(f"Great week of snow ({conditions.new_snow_7d}cm)")
            elif conditions.new_snow_7d >= 20:
                score += 0.5

        # Snow quality scoring
        quality = conditions.snow_quality.lower()
        if quality in ["powder", "fresh"]:
            score += 1.5
            highlights.append("Powder conditions")
        elif quality in ["packed", "groomed"]:
            score += 0.5
            highlights.append("Well-groomed slopes")
        elif quality in ["icy", "hard"]:
            score -= 2.0
            concerns.append("Icy conditions reported")
        elif quality in ["wet", "spring"]:
            score -= 1.0
            concerns.append("Wet/spring snow")

        # Clamp score to 0-10
        score = max(0.0, min(10.0, score))
        return round(score, 1), highlights, concerns

    def score_transport(self, journey: Optional[Journey]) -> Tuple[float, List[str], List[str]]:
        """
        Score transport accessibility (0-10).

        Perfect (10): <2 hours, direct or 1 change
        Good (7-9): 2-3 hours, 1-2 changes
        Fair (4-6): 3-4 hours
        Poor (0-3): 4+ hours
        """
        highlights = []
        concerns = []

        if not journey:
            return 3.0, [], ["Transport data unavailable"]

        hours = journey.duration_minutes / 60

        # Duration scoring
        if hours < 2:
            score = 10.0
            highlights.append(f"Quick journey ({hours:.1f}h)")
        elif hours < 2.5:
            score = 8.5
            highlights.append(f"Good travel time ({hours:.1f}h)")
        elif hours < 3:
            score = 7.0
            highlights.append(f"Reasonable travel time ({hours:.1f}h)")
        elif hours < 3.5:
            score = 5.5
        elif hours < 4:
            score = 4.0
            concerns.append(f"Long journey ({hours:.1f}h)")
        else:
            score = 2.0
            concerns.append(f"Very long journey ({hours:.1f}h)")

        # Penalize for many changes
        if journey.changes == 0:
            score += 0.5
            highlights.append("Direct connection")
        elif journey.changes == 1:
            pass  # Neutral
        elif journey.changes == 2:
            score -= 0.5
        elif journey.changes >= 3:
            score -= 1.0
            concerns.append(f"Multiple changes ({journey.changes})")

        # Clamp score to 0-10
        score = max(0.0, min(10.0, score))
        return round(score, 1), highlights, concerns

    def score_size(self, resort: Optional[Resort]) -> Tuple[float, List[str], List[str]]:
        """
        Score resort size based on skiable terrain (0-10).

        Scale:
        - 200+ km: 10.0 (massive resort)
        - 150-199 km: 9.0
        - 100-149 km: 8.0
        - 70-99 km: 7.0
        - 50-69 km: 6.0
        - 30-49 km: 5.0
        - 15-29 km: 4.0
        - 5-14 km: 3.0
        - <5 km: 2.0
        - Unknown: 5.0 (neutral)
        """
        highlights = []
        concerns = []

        if not resort or resort.skiable_terrain_km is None:
            return 5.0, [], ["Resort size unknown"]

        km = resort.skiable_terrain_km

        if km >= 200:
            score = 10.0
            highlights.append(f"Massive ski area ({km:.0f}km)")
        elif km >= 150:
            score = 9.0
            highlights.append(f"Very large ski area ({km:.0f}km)")
        elif km >= 100:
            score = 8.0
            highlights.append(f"Large ski area ({km:.0f}km)")
        elif km >= 70:
            score = 7.0
            highlights.append(f"Good-sized ski area ({km:.0f}km)")
        elif km >= 50:
            score = 6.0
        elif km >= 30:
            score = 5.0
        elif km >= 15:
            score = 4.0
            concerns.append(f"Small ski area ({km:.0f}km)")
        elif km >= 5:
            score = 3.0
            concerns.append(f"Very small ski area ({km:.0f}km)")
        else:
            score = 2.0
            concerns.append(f"Tiny ski area ({km:.0f}km)")

        return round(score, 1), highlights, concerns

    def calculate_total_score(
        self,
        weather_score: float,
        snow_score: float,
        transport_score: float,
        size_score: float,
    ) -> float:
        """Calculate weighted total score."""
        total = (
            weather_score * self.WEATHER_WEIGHT
            + snow_score * self.SNOW_WEIGHT
            + transport_score * self.TRANSPORT_WEIGHT
            + size_score * self.SIZE_WEIGHT
        )
        return round(total, 1)

    def score_resort(
        self,
        weather: Optional[WeatherForecast],
        snow: Optional[SnowConditions],
        transport: Optional[Journey],
        resort: Optional[Resort] = None,
    ) -> Tuple[float, float, float, float, float, List[str], List[str]]:
        """
        Score a resort based on all factors.

        Returns: (total_score, weather_score, snow_score, transport_score, size_score, highlights, concerns)
        """
        weather_score, weather_highlights, weather_concerns = self.score_weather(weather)
        snow_score, snow_highlights, snow_concerns = self.score_snow(snow)
        transport_score, transport_highlights, transport_concerns = self.score_transport(transport)
        size_score, size_highlights, size_concerns = self.score_size(resort)

        total_score = self.calculate_total_score(weather_score, snow_score, transport_score, size_score)

        highlights = weather_highlights + snow_highlights + transport_highlights + size_highlights
        concerns = weather_concerns + snow_concerns + transport_concerns + size_concerns

        return (
            total_score,
            weather_score,
            snow_score,
            transport_score,
            size_score,
            highlights,
            concerns,
        )
