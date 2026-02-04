import httpx
import logging
import asyncio
from datetime import datetime, date
from typing import Awaitable, Callable, Dict, List, Optional

from config import get_settings
from models.transport import Journey, JourneySegment
from models.resort import Resort
from utils.cache import cache

logger = logging.getLogger(__name__)
settings = get_settings()


class TransportService:
    """Service for fetching public transport connections from Swiss OpenData API."""

    BASE_URL = "http://transport.opendata.ch/v1/connections"

    def __init__(self):
        self.cache_hours = settings.transport_cache_hours

    async def get_journey(
        self,
        from_location: str,
        to_location: str,
        travel_date: date,
        time: str = "08:00",
    ) -> Optional[Journey]:
        """Get public transport journey between two locations."""
        cache_key = f"transport:{from_location}:{to_location}:{travel_date.isoformat()}"

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
                        "from": from_location,
                        "to": to_location,
                        "date": travel_date.strftime("%Y-%m-%d"),
                        "time": time,
                        "limit": 3,
                    },
                    timeout=15.0,
                )
                response.raise_for_status()
                data = response.json()

            if not data.get("connections"):
                logger.warning(f"No connections found from {from_location} to {to_location}")
                return None

            # Parse the first (best) connection
            journey = self._parse_connection(data["connections"][0])

            if journey and settings.cache_enabled:
                cache.set(cache_key, journey, self.cache_hours)

            return journey

        except httpx.HTTPStatusError as e:
            logger.error(f"Transport API HTTP error: {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Transport API request error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching transport: {e}")
            return None

    def _parse_connection(self, connection: dict) -> Optional[Journey]:
        """Parse a connection from the Swiss transport API."""
        try:
            # Parse departure time
            departure_str = connection["from"]["departure"]
            if departure_str:
                departure_time = self._parse_datetime(departure_str)
            else:
                return None

            # Parse arrival time
            arrival_str = connection["to"]["arrival"]
            if arrival_str:
                arrival_time = self._parse_datetime(arrival_str)
            else:
                return None

            # Parse duration
            duration_str = connection.get("duration", "00d00:00:00")
            duration_minutes = self._parse_duration(duration_str)

            # Parse segments
            segments = []
            for section in connection.get("sections", []):
                if section.get("journey"):  # Only include actual transport (not walking)
                    segment = self._parse_segment(section)
                    if segment:
                        segments.append(segment)

            return Journey(
                departure_time=departure_time,
                arrival_time=arrival_time,
                duration_minutes=duration_minutes,
                changes=connection.get("transfers", 0),
                segments=segments,
            )

        except Exception as e:
            logger.error(f"Error parsing connection: {e}")
            return None

    def _parse_segment(self, section: dict) -> Optional[JourneySegment]:
        """Parse a journey segment from the API response."""
        try:
            journey_info = section.get("journey", {})
            category = journey_info.get("category", "")

            # Determine transport type
            if category in ["IC", "IR", "RE", "S", "RJ", "EC", "TGV"]:
                transport_type = "train"
            elif category in ["B", "BUS", "NFB"]:
                transport_type = "bus"
            else:
                transport_type = "train"  # Default to train

            departure = section.get("departure", {})
            arrival = section.get("arrival", {})

            return JourneySegment(
                type=transport_type,
                from_station=departure.get("station", {}).get("name", "Unknown"),
                to_station=arrival.get("station", {}).get("name", "Unknown"),
                departure=self._parse_datetime(departure.get("departure", "")),
                arrival=self._parse_datetime(arrival.get("arrival", "")),
                line=journey_info.get("name", ""),
            )
        except Exception as e:
            logger.error(f"Error parsing segment: {e}")
            return None

    def _parse_datetime(self, dt_str: str) -> datetime:
        """Parse datetime string from the API."""
        # Handle different timezone formats
        if not dt_str:
            return datetime.now()

        # Remove timezone offset for parsing
        dt_str = dt_str.replace("+0100", "+01:00").replace("+0200", "+02:00")
        try:
            return datetime.fromisoformat(dt_str)
        except ValueError:
            # Fallback: try without timezone
            return datetime.fromisoformat(dt_str[:19])

    def _parse_duration(self, duration_str: str) -> int:
        """Parse duration string like '00d02:45:00' to minutes."""
        try:
            # Format: "00d02:45:00"
            if "d" in duration_str:
                parts = duration_str.split("d")
                days = int(parts[0])
                time_part = parts[1]
            else:
                days = 0
                time_part = duration_str

            time_parts = time_part.split(":")
            hours = int(time_parts[0])
            minutes = int(time_parts[1])

            return days * 24 * 60 + hours * 60 + minutes
        except Exception:
            return 0

    async def get_resort_journey(
        self, from_location: str, resort: Resort, travel_date: date
    ) -> Optional[Journey]:
        """Get journey to a resort, trying multiple destination options."""
        # First try the resort name directly
        journey = await self.get_journey(from_location, resort.name, travel_date)
        if journey:
            return journey

        # Try the nearest station
        if resort.access.nearest_station:
            journey = await self.get_journey(
                from_location, resort.access.nearest_station, travel_date
            )
            if journey and resort.access.postbus_duration_minutes:
                # Add PostBus time to journey duration
                journey.duration_minutes += resort.access.postbus_duration_minutes
            return journey

        logger.warning(f"No transport route found for {resort.name}")
        return None

    async def get_journeys_batch(
        self,
        from_location: str,
        resorts: List[Resort],
        travel_date: date,
        on_progress: Optional[Callable[[int, int], Awaitable[None]]] = None,
    ) -> Dict[str, Optional[Journey]]:
        """Get journeys to multiple resorts in parallel."""
        # Limit concurrency to be respectful to the API
        semaphore = asyncio.Semaphore(10)
        total = len(resorts)
        completed = 0
        journeys = {}

        async def fetch_with_semaphore(resort: Resort):
            nonlocal completed
            async with semaphore:
                result = await self.get_resort_journey(from_location, resort, travel_date)
                completed += 1
                if on_progress:
                    await on_progress(completed, total)
                return resort.id, result

        tasks = [fetch_with_semaphore(resort) for resort in resorts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Transport fetch failed: {result}")
            else:
                resort_id, journey = result
                journeys[resort_id] = journey

        return journeys
