import httpx
import logging
import asyncio
import re
from datetime import datetime
from typing import Awaitable, Callable, Dict, List, Optional

from bs4 import BeautifulSoup

from config import get_settings
from models.snow import SnowConditions
from models.resort import Resort
from utils.cache import cache

logger = logging.getLogger(__name__)
settings = get_settings()


class SnowService:
    """Service for fetching snow conditions from multiple sources.

    Primary source: snow-forecast.com (if resort has slug configured)
    Fallback source: Open-Meteo API (coordinate-based, 100% coverage)
    """

    SNOW_FORECAST_URL = "https://www.snow-forecast.com/resorts/{slug}/6day/mid"
    OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self):
        self.cache_hours = settings.snow_cache_hours

    async def get_conditions(self, resort: Resort) -> Optional[SnowConditions]:
        """Get snow conditions for a specific resort.

        Strategy:
        1. Try snow-forecast.com if resort has a slug configured
        2. Fall back to Open-Meteo API (coordinate-based) if no slug or if primary fails
        """
        cache_key = f"snow:{resort.id}"

        # Check cache first
        if settings.cache_enabled:
            cached = cache.get(cache_key)
            if cached:
                return cached

        conditions = None

        # Try snow-forecast.com first if slug is available
        if resort.snow_forecast_slug:
            conditions = await self._fetch_from_snow_forecast(resort)

        # Fall back to Open-Meteo if no conditions yet
        if not conditions:
            conditions = await self._fetch_from_open_meteo(resort)

        # Cache the result
        if conditions and settings.cache_enabled:
            cache.set(cache_key, conditions, self.cache_hours)

        return conditions

    async def _fetch_from_snow_forecast(self, resort: Resort) -> Optional[SnowConditions]:
        """Fetch snow conditions from snow-forecast.com."""
        try:
            url = self.SNOW_FORECAST_URL.format(slug=resort.snow_forecast_slug)

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    timeout=15.0,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                )
                response.raise_for_status()

            conditions = self._parse_snow_forecast_data(response.text, resort.id)
            if conditions:
                logger.debug(f"Got snow data from snow-forecast.com for {resort.name}")
            return conditions

        except httpx.HTTPStatusError as e:
            logger.warning(
                f"Snow-forecast.com HTTP error for {resort.name}: {e.response.status_code}"
            )
            return None
        except httpx.RequestError as e:
            logger.warning(f"Snow-forecast.com request error for {resort.name}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error fetching from snow-forecast.com for {resort.name}: {e}")
            return None

    async def _fetch_from_open_meteo(self, resort: Resort) -> Optional[SnowConditions]:
        """Fetch snow conditions from Open-Meteo API (fallback source).

        Open-Meteo provides:
        - snow_depth: Current snow depth in cm
        - snowfall: Daily snowfall amounts in cm
        """
        try:
            # Use resort's top elevation for more accurate mountain snow data
            # Open-Meteo can interpolate to specific elevations
            params = {
                "latitude": resort.coordinates.latitude,
                "longitude": resort.coordinates.longitude,
                "daily": "snowfall_sum,snow_depth_max",
                "past_days": 7,
                "forecast_days": 1,
                "timezone": "auto",
            }

            # If we have elevation data, use it for better accuracy
            if resort.elevation_top:
                params["elevation"] = resort.elevation_top

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.OPEN_METEO_URL,
                    params=params,
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()

            conditions = self._parse_open_meteo_data(data, resort.id)
            if conditions:
                logger.info(f"Got snow data from Open-Meteo for {resort.name}: base={conditions.snow_base}cm, 7d={conditions.new_snow_7d}cm")
            else:
                logger.warning(f"Open-Meteo returned no useful data for {resort.name}")
            return conditions

        except httpx.HTTPStatusError as e:
            logger.warning(
                f"Open-Meteo HTTP error for {resort.name}: {e.response.status_code}"
            )
            return None
        except httpx.RequestError as e:
            logger.warning(f"Open-Meteo request error for {resort.name}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error fetching from Open-Meteo for {resort.name}: {e}")
            return None

    def _parse_open_meteo_data(self, data: dict, resort_id: str) -> Optional[SnowConditions]:
        """Parse Open-Meteo API response to extract snow conditions."""
        try:
            daily = data.get("daily", {})
            snowfall_values = daily.get("snowfall_sum", [])
            snow_depth_values = daily.get("snow_depth_max", [])

            # Filter out None values
            snowfall_values = [v for v in snowfall_values if v is not None]
            snow_depth_values = [v for v in snow_depth_values if v is not None]

            # Calculate snow metrics
            snow_base = None
            new_snow_24h = None
            new_snow_7d = None

            # Snow depth (use most recent value)
            if snow_depth_values:
                # Convert from meters to cm if needed, Open-Meteo returns cm
                snow_base = int(round(snow_depth_values[-1]))

            # Recent snowfall
            if snowfall_values:
                # Last value is today/yesterday's snowfall
                if len(snowfall_values) >= 1:
                    new_snow_24h = int(round(snowfall_values[-1]))

                # Sum of last 7 days
                new_snow_7d = int(round(sum(snowfall_values[-7:])))

            # Determine snow quality based on recent snowfall
            snow_quality = self._determine_snow_quality(snow_base, new_snow_24h, new_snow_7d)

            # Only return if we have some useful data
            if any([snow_base, new_snow_24h, new_snow_7d]):
                return SnowConditions(
                    resort_id=resort_id,
                    date_updated=datetime.now(),
                    snow_base=snow_base if snow_base and snow_base > 0 else None,
                    new_snow_24h=new_snow_24h if new_snow_24h and new_snow_24h > 0 else None,
                    new_snow_7d=new_snow_7d if new_snow_7d and new_snow_7d > 0 else None,
                    snow_quality=snow_quality,
                )

            return None

        except Exception as e:
            logger.error(f"Error parsing Open-Meteo data: {e}")
            return None

    def _determine_snow_quality(
        self,
        snow_base: Optional[int],
        new_snow_24h: Optional[int],
        new_snow_7d: Optional[int]
    ) -> str:
        """Determine snow quality based on available metrics."""
        # Fresh powder if significant recent snowfall
        if new_snow_24h and new_snow_24h >= 15:
            return "Powder"
        if new_snow_24h and new_snow_24h >= 5:
            return "Fresh"

        # Good conditions if decent snowfall in past week
        if new_snow_7d and new_snow_7d >= 20:
            return "Fresh"

        # Packed/groomed if there's a base but no recent snow
        if snow_base and snow_base >= 30:
            if not new_snow_7d or new_snow_7d < 5:
                return "Packed"
            return "Variable"

        # Low snow base
        if snow_base and snow_base < 30:
            return "Variable"

        return "Unknown"

    def _parse_snow_forecast_data(self, html: str, resort_id: str) -> Optional[SnowConditions]:
        """Parse snow-forecast.com HTML to extract snow conditions."""
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Try to extract snow depth from various possible elements
            snow_base = None
            snow_summit = None
            new_snow_24h = None
            new_snow_7d = None
            snow_quality = "Unknown"

            # Look for snow depth table
            depth_table = soup.find("table", class_="snow-depths-table")
            if depth_table:
                rows = depth_table.find_all("tr")
                for row in rows:
                    text = row.get_text().lower()
                    cells = row.find_all("td")
                    if cells:
                        value_text = cells[-1].get_text().strip()
                        # Extract number from text like "120 cm"
                        match = re.search(r"(\d+)", value_text)
                        if match:
                            value = int(match.group(1))
                            if "base" in text or "bottom" in text:
                                snow_base = value
                            elif "top" in text or "summit" in text:
                                snow_summit = value

            # Alternative: look for snow depth in specific divs
            for div in soup.find_all("div", class_=re.compile(r"snow|depth", re.I)):
                text = div.get_text()
                # Look for patterns like "Base: 120cm" or "Summit: 180cm"
                base_match = re.search(r"base[:\s]*(\d+)\s*cm", text, re.I)
                summit_match = re.search(r"(?:summit|top)[:\s]*(\d+)\s*cm", text, re.I)
                if base_match and not snow_base:
                    snow_base = int(base_match.group(1))
                if summit_match and not snow_summit:
                    snow_summit = int(summit_match.group(1))

            # Look for new snow data
            for elem in soup.find_all(string=re.compile(r"new snow|fresh snow", re.I)):
                parent = elem.parent
                if parent:
                    text = parent.get_text()
                    match = re.search(r"(\d+)\s*cm", text)
                    if match:
                        new_snow = int(match.group(1))
                        if "24" in text or "today" in text.lower():
                            new_snow_24h = new_snow
                        elif "7" in text or "week" in text.lower():
                            new_snow_7d = new_snow

            # Determine snow quality based on conditions
            page_text = soup.get_text().lower()
            if "powder" in page_text:
                snow_quality = "Powder"
            elif "fresh" in page_text:
                snow_quality = "Fresh"
            elif "packed" in page_text or "groomed" in page_text:
                snow_quality = "Packed"
            elif "icy" in page_text or "hard" in page_text:
                snow_quality = "Icy"
            elif snow_base and snow_base > 0:
                snow_quality = "Variable"

            # Only return if we found actual useful data
            if any([snow_base, snow_summit, new_snow_24h, new_snow_7d]):
                return SnowConditions(
                    resort_id=resort_id,
                    date_updated=datetime.now(),
                    snow_base=snow_base,
                    snow_summit=snow_summit,
                    new_snow_24h=new_snow_24h,
                    new_snow_7d=new_snow_7d,
                    snow_quality=snow_quality,
                )

            # Return None to trigger fallback to Open-Meteo
            return None

        except Exception as e:
            logger.error(f"Error parsing snow data: {e}")
            return None

    async def get_conditions_batch(
        self,
        resorts: List[Resort],
        on_progress: Optional[Callable[[int, int], Awaitable[None]]] = None,
    ) -> Dict[str, Optional[SnowConditions]]:
        """Get snow conditions for multiple resorts in parallel."""
        # Limit concurrency to avoid overwhelming the server
        semaphore = asyncio.Semaphore(5)
        total = len(resorts)
        completed = 0
        conditions = {}

        async def fetch_with_semaphore(resort: Resort):
            nonlocal completed
            async with semaphore:
                result = await self.get_conditions(resort)
                completed += 1
                if on_progress:
                    await on_progress(completed, total)
                return resort.id, result

        tasks = [fetch_with_semaphore(resort) for resort in resorts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Snow data fetch failed: {result}")
            else:
                resort_id, snow_conditions = result
                conditions[resort_id] = snow_conditions

        return conditions
