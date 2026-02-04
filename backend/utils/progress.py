import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ProgressStage(str, Enum):
    """Stages of the recommendation generation process."""
    LOADING_RESORTS = "loading_resorts"
    FETCHING_WEATHER = "fetching_weather"
    SCRAPING_SNOW = "scraping_snow"
    FETCHING_TRANSPORT = "fetching_transport"
    SCORING = "scoring"
    GENERATING_AI = "generating_ai"
    COMPLETE = "complete"


@dataclass
class ProgressUpdate:
    """A single progress update to send to the client."""
    stage: ProgressStage
    message: str
    current: int = 0
    total: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "stage": self.stage.value,
            "message": self.message,
            "current": self.current,
            "total": self.total,
        }


class ProgressTracker:
    """Tracks progress and provides updates via an async queue."""

    def __init__(self):
        self.queue: asyncio.Queue[ProgressUpdate] = asyncio.Queue()
        self._current_stage: Optional[ProgressStage] = None
        self._current_count: int = 0
        self._total_count: int = 0

    async def set_stage(
        self,
        stage: ProgressStage,
        message: str,
        total: int = 0,
    ) -> None:
        """Set the current stage and send an update."""
        self._current_stage = stage
        self._current_count = 0
        self._total_count = total

        update = ProgressUpdate(
            stage=stage,
            message=message,
            current=0,
            total=total,
        )
        await self.queue.put(update)

    async def increment(self, current: int, total: int) -> None:
        """Send a progress increment update for the current stage."""
        if self._current_stage is None:
            return

        self._current_count = current
        self._total_count = total

        # Create message based on stage
        messages = {
            ProgressStage.FETCHING_WEATHER: f"Fetching weather from OpenWeather... ({current}/{total})",
            ProgressStage.SCRAPING_SNOW: f"Getting snow conditions from snow-forecast.com... ({current}/{total})",
            ProgressStage.FETCHING_TRANSPORT: f"Getting transport from Swiss Transport API... ({current}/{total})",
        }

        message = messages.get(
            self._current_stage,
            f"Processing... ({current}/{total})"
        )

        update = ProgressUpdate(
            stage=self._current_stage,
            message=message,
            current=current,
            total=total,
        )
        await self.queue.put(update)

    async def complete(self) -> None:
        """Mark the process as complete."""
        update = ProgressUpdate(
            stage=ProgressStage.COMPLETE,
            message="Complete!",
            current=0,
            total=0,
        )
        await self.queue.put(update)
