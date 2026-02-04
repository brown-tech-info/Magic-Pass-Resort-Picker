import httpx
import logging
import asyncio
from datetime import date, datetime
from typing import Awaitable, Callable, Dict, List, Optional

from config import get_settings
from models.weather import WeatherForecast
from models.resort import Resort
from utils.cache import cache

logger = logging.getLogger(__name__)
settings = get_settings()


class WeatherService:
    """Service for fetching weather forecasts from OpenWeather API."""

    BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"

    def __init__(self):
        self.api_key = settings.openweather_api_key
        self.cache_hours = settings.weather_cache_hours

    def _degrees_to_direction(self, degrees: float) -> str:
        """Convert wind degrees to cardinal direction."""
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        idx = round(degrees / 45) % 8
        return directions[idx]

    def _get_visibility_description(self, cloud_cover: int) -> str:
        """Get visibility description based on cloud cover."""
        if cloud_cover < 30:
            return "Good"
        elif cloud_cover < 70:
            return "Moderate"
        return "Poor"

    async def get_forecast(
        self, lat: float, lon: float, target_date: date
    ) -> Optional[WeatherForecast]:
        """Get weather forecast for specific coordinates and date."""
        cache_key = f"weather:{lat:.4f}:{lon:.4f}:{target_date.isoformat()}"

        # Check cache first
        if settings.cache_enabled:
            cached = cache.get(cache_key)
            if cached:
                return cached

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.BASE_URL,
                    params={
                        "lat": lat,
                        "lon": lon,
                        "appid": self.api_key,
                        "units": "metric",
                    },
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()

            # Parse forecast data for target date
            forecast = self._parse_forecast_data(data, target_date)

            if forecast and settings.cache_enabled:
                cache.set(cache_key, forecast, self.cache_hours)

            return forecast

        except httpx.HTTPStatusError as e:
            logger.error(f"Weather API HTTP error: {e.response.status_code} - {e}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Weather API request error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching weather: {e}")
            return None

    def _parse_forecast_data(
        self, data: dict, target_date: date
    ) -> Optional[WeatherForecast]:
        """Parse OpenWeather API response for the target date."""
        try:
            forecasts_for_date = []

            for item in data.get("list", []):
                dt = datetime.fromtimestamp(item["dt"])
                if dt.date() == target_date:
                    forecasts_for_date.append(item)

            if not forecasts_for_date:
                # Try to find closest date
                logger.warning(f"No forecast found for {target_date}, using nearest")
                return None

            # Aggregate data for the day
            temps = []
            precipitations = []
            snow_amounts = []
            wind_speeds = []
            cloud_covers = []
            conditions = []
            icons = []

            for item in forecasts_for_date:
                temps.append(item["main"]["temp"])
                precipitations.append(item.get("rain", {}).get("3h", 0))
                snow_amounts.append(item.get("snow", {}).get("3h", 0))
                wind_speeds.append(item["wind"]["speed"])
                cloud_covers.append(item["clouds"]["all"])
                if item.get("weather"):
                    conditions.append(item["weather"][0]["description"])
                    icons.append(item["weather"][0]["icon"])

            temp_min = min(temps) if temps else 0
            temp_max = max(temps) if temps else 0
            precipitation_mm = sum(precipitations)
            snowfall_cm = sum(snow_amounts) / 10  # Convert mm to cm
            avg_wind = sum(wind_speeds) / len(wind_speeds) if wind_speeds else 0
            avg_clouds = sum(cloud_covers) / len(cloud_covers) if cloud_covers else 0

            # Get most common condition
            main_condition = max(set(conditions), key=conditions.count) if conditions else "Unknown"
            main_icon = icons[0] if icons else ""

            return WeatherForecast(
                date=target_date,
                temperature_min=round(temp_min, 1),
                temperature_max=round(temp_max, 1),
                precipitation_mm=round(precipitation_mm, 1),
                snowfall_cm=round(snowfall_cm, 1) if snowfall_cm > 0 else None,
                wind_speed=round(avg_wind * 3.6, 1),  # m/s to km/h
                wind_direction=self._degrees_to_direction(
                    forecasts_for_date[0].get("wind", {}).get("deg", 0)
                ),
                cloud_cover=int(avg_clouds),
                visibility=self._get_visibility_description(int(avg_clouds)),
                conditions=main_condition,
                icon=main_icon,
            )

        except Exception as e:
            logger.error(f"Error parsing weather data: {e}")
            return None

    async def get_forecasts_batch(
        self,
        resorts: List[Resort],
        target_date: date,
        on_progress: Optional[Callable[[int, int], Awaitable[None]]] = None,
    ) -> Dict[str, Optional[WeatherForecast]]:
        """Get weather forecasts for multiple resorts in parallel."""
        total = len(resorts)
        completed = 0
        forecasts = {}

        async def fetch_with_progress(resort: Resort):
            nonlocal completed
            result = await self.get_forecast(
                resort.coordinates.latitude,
                resort.coordinates.longitude,
                target_date,
            )
            completed += 1
            if on_progress:
                await on_progress(completed, total)
            return resort.id, result

        tasks = [fetch_with_progress(resort) for resort in resorts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Weather fetch failed: {result}")
            else:
                resort_id, forecast = result
                forecasts[resort_id] = forecast

        return forecasts
