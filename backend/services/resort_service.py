import json
import logging
from pathlib import Path
from typing import List, Optional

from models.resort import Resort

logger = logging.getLogger(__name__)


class ResortService:
    """Service for loading and querying resort data."""

    def __init__(self, data_file: Optional[str] = None):
        if data_file is None:
            data_file = Path(__file__).parent.parent / "data" / "resorts.json"
        self.data_file = Path(data_file)
        self._resorts: List[Resort] = []
        self._loaded = False

    def load_resorts(self) -> None:
        """Load resorts from JSON file."""
        if self._loaded:
            return

        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._resorts = [Resort(**resort) for resort in data.get("resorts", [])]
            self._loaded = True
            logger.info(f"Loaded {len(self._resorts)} resorts from {self.data_file}")
        except FileNotFoundError:
            logger.error(f"Resort data file not found: {self.data_file}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in resort data file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading resorts: {e}")
            raise

    def get_all_resorts(self) -> List[Resort]:
        """Return all resorts."""
        if not self._loaded:
            self.load_resorts()
        return self._resorts

    def get_resort_by_id(self, resort_id: str) -> Optional[Resort]:
        """Get a specific resort by ID."""
        if not self._loaded:
            self.load_resorts()

        for resort in self._resorts:
            if resort.id == resort_id:
                return resort
        return None

    def get_resorts_by_region(self, region: str) -> List[Resort]:
        """Get resorts filtered by region."""
        if not self._loaded:
            self.load_resorts()

        return [r for r in self._resorts if r.region.lower() == region.lower()]

    def get_resorts_by_canton(self, canton: str) -> List[Resort]:
        """Get resorts filtered by canton."""
        if not self._loaded:
            self.load_resorts()

        return [r for r in self._resorts if r.canton.upper() == canton.upper()]
