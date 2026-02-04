import logging
import asyncio
from datetime import datetime, date, timedelta
from typing import List, Optional

from config import get_settings
from models.resort import Resort
from models.recommendation import Recommendation, RecommendationsResponse
from services.resort_service import ResortService
from services.weather_service import WeatherService
from services.snow_service import SnowService
from services.transport_service import TransportService
from services.llm_service import LLMService
from core.scoring import ScoringEngine
from utils.progress import ProgressTracker, ProgressStage

logger = logging.getLogger(__name__)
settings = get_settings()


class RecommenderEngine:
    """Main engine for generating ski resort recommendations."""

    def __init__(
        self,
        resort_service: Optional[ResortService] = None,
        weather_service: Optional[WeatherService] = None,
        snow_service: Optional[SnowService] = None,
        transport_service: Optional[TransportService] = None,
        llm_service: Optional[LLMService] = None,
    ):
        self.resort_service = resort_service or ResortService()
        self.weather_service = weather_service or WeatherService()
        self.snow_service = snow_service or SnowService()
        self.transport_service = transport_service or TransportService()
        self.llm_service = llm_service or LLMService()
        self.scoring_engine = ScoringEngine()

    def _get_next_weekend_dates(self) -> tuple[date, date]:
        """Get the dates for the upcoming Saturday and Sunday."""
        today = date.today()
        days_until_saturday = (5 - today.weekday()) % 7
        if days_until_saturday == 0 and today.weekday() == 5:
            # If today is Saturday, use today
            saturday = today
        else:
            saturday = today + timedelta(days=days_until_saturday or 7)
        sunday = saturday + timedelta(days=1)
        return saturday, sunday

    async def generate_recommendations(
        self,
        start_location: str = None,
        target_date: date = None,
        num_recommendations: int = 5,
    ) -> RecommendationsResponse:
        """
        Generate ski resort recommendations.

        Args:
            start_location: Starting point for travel (default: Geneva)
            target_date: Target date for the trip (default: upcoming Saturday)
            num_recommendations: Number of top recommendations to return

        Returns:
            RecommendationsResponse with ranked recommendations and AI summary
        """
        start_location = start_location or settings.start_location
        saturday, sunday = self._get_next_weekend_dates()
        target_date = target_date or saturday

        logger.info(
            f"Generating recommendations from {start_location} for {target_date}"
        )

        # Load all resorts
        resorts = self.resort_service.get_all_resorts()
        logger.info(f"Processing {len(resorts)} resorts")

        # Fetch all data in parallel
        weather_task = self.weather_service.get_forecasts_batch(resorts, target_date)
        snow_task = self.snow_service.get_conditions_batch(resorts)
        transport_task = self.transport_service.get_journeys_batch(
            start_location, resorts, target_date
        )

        weather_data, snow_data, transport_data = await asyncio.gather(
            weather_task, snow_task, transport_task
        )

        logger.info(
            f"Data fetched - Weather: {len([w for w in weather_data.values() if w])}, "
            f"Snow: {len([s for s in snow_data.values() if s])}, "
            f"Transport: {len([t for t in transport_data.values() if t])}"
        )

        # Score and create recommendations for each resort
        recommendations = []
        for resort in resorts:
            weather = weather_data.get(resort.id)
            snow = snow_data.get(resort.id)
            transport = transport_data.get(resort.id)

            # Calculate scores
            (
                total_score,
                weather_score,
                snow_score,
                transport_score,
                size_score,
                highlights,
                concerns,
            ) = self.scoring_engine.score_resort(weather, snow, transport, resort)

            # Generate reasoning
            reasoning = self._generate_reasoning(
                resort, total_score, weather_score, snow_score, transport_score
            )

            recommendation = Recommendation(
                resort=resort,
                score=total_score,
                weather_score=weather_score,
                snow_score=snow_score,
                transport_score=transport_score,
                size_score=size_score,
                weather_forecast=weather,
                snow_conditions=snow,
                journey=transport,
                highlights=highlights[:5],  # Limit to top 5
                concerns=concerns[:5],
                reasoning=reasoning,
            )
            recommendations.append(recommendation)

        # Sort by score (highest first)
        recommendations.sort(key=lambda r: r.score, reverse=True)

        # Take top N
        top_recommendations = recommendations[:num_recommendations]

        # Generate AI summary
        target_weekend = f"{saturday.strftime('%b %d')} - {sunday.strftime('%b %d')}"
        ai_summary = await self.llm_service.generate_recommendation_summary(
            top_recommendations, target_weekend
        )

        return RecommendationsResponse(
            recommendations=top_recommendations,
            ai_summary=ai_summary,
            generated_at=datetime.now(),
            target_weekend=target_weekend,
        )

    async def generate_recommendations_with_progress(
        self,
        progress: ProgressTracker,
        start_location: str = None,
        target_date: date = None,
        num_recommendations: int = 5,
    ) -> RecommendationsResponse:
        """
        Generate ski resort recommendations with progress updates.

        Args:
            progress: ProgressTracker to send updates to
            start_location: Starting point for travel (default: Geneva)
            target_date: Target date for the trip (default: upcoming Saturday)
            num_recommendations: Number of top recommendations to return

        Returns:
            RecommendationsResponse with ranked recommendations and AI summary
        """
        start_location = start_location or settings.start_location
        saturday, sunday = self._get_next_weekend_dates()
        target_date = target_date or saturday

        logger.info(
            f"Generating recommendations with progress from {start_location} for {target_date}"
        )

        # Stage 1: Load resorts
        await progress.set_stage(
            ProgressStage.LOADING_RESORTS,
            "Loading resort data...",
        )
        resorts = self.resort_service.get_all_resorts()
        total_resorts = len(resorts)
        logger.info(f"Processing {total_resorts} resorts")

        # Stage 2: Fetch weather
        await progress.set_stage(
            ProgressStage.FETCHING_WEATHER,
            f"Fetching weather from OpenWeather... (0/{total_resorts})",
            total=total_resorts,
        )
        weather_data = await self.weather_service.get_forecasts_batch(
            resorts,
            target_date,
            on_progress=progress.increment,
        )

        # Stage 3: Fetch snow conditions
        await progress.set_stage(
            ProgressStage.SCRAPING_SNOW,
            f"Getting snow conditions from snow-forecast.com... (0/{total_resorts})",
            total=total_resorts,
        )
        snow_data = await self.snow_service.get_conditions_batch(
            resorts,
            on_progress=progress.increment,
        )

        # Stage 4: Fetch transport
        await progress.set_stage(
            ProgressStage.FETCHING_TRANSPORT,
            f"Getting transport from Swiss Transport API... (0/{total_resorts})",
            total=total_resorts,
        )
        transport_data = await self.transport_service.get_journeys_batch(
            start_location,
            resorts,
            target_date,
            on_progress=progress.increment,
        )

        logger.info(
            f"Data fetched - Weather: {len([w for w in weather_data.values() if w])}, "
            f"Snow: {len([s for s in snow_data.values() if s])}, "
            f"Transport: {len([t for t in transport_data.values() if t])}"
        )

        # Stage 5: Score resorts
        await progress.set_stage(
            ProgressStage.SCORING,
            "Scoring resorts...",
        )
        recommendations = []
        for resort in resorts:
            weather = weather_data.get(resort.id)
            snow = snow_data.get(resort.id)
            transport = transport_data.get(resort.id)

            # Calculate scores
            (
                total_score,
                weather_score,
                snow_score,
                transport_score,
                size_score,
                highlights,
                concerns,
            ) = self.scoring_engine.score_resort(weather, snow, transport, resort)

            # Generate reasoning
            reasoning = self._generate_reasoning(
                resort, total_score, weather_score, snow_score, transport_score
            )

            recommendation = Recommendation(
                resort=resort,
                score=total_score,
                weather_score=weather_score,
                snow_score=snow_score,
                transport_score=transport_score,
                size_score=size_score,
                weather_forecast=weather,
                snow_conditions=snow,
                journey=transport,
                highlights=highlights[:5],
                concerns=concerns[:5],
                reasoning=reasoning,
            )
            recommendations.append(recommendation)

        # Sort by score (highest first)
        recommendations.sort(key=lambda r: r.score, reverse=True)

        # Take top N
        top_recommendations = recommendations[:num_recommendations]

        # Stage 6: Generate AI summary
        await progress.set_stage(
            ProgressStage.GENERATING_AI,
            "Generating AI summary...",
        )
        target_weekend = f"{saturday.strftime('%b %d')} - {sunday.strftime('%b %d')}"
        ai_summary = await self.llm_service.generate_recommendation_summary(
            top_recommendations, target_weekend
        )

        # Mark complete
        await progress.complete()

        return RecommendationsResponse(
            recommendations=top_recommendations,
            ai_summary=ai_summary,
            generated_at=datetime.now(),
            target_weekend=target_weekend,
        )

    def _generate_reasoning(
        self,
        resort: Resort,
        total_score: float,
        weather_score: float,
        snow_score: float,
        transport_score: float,
    ) -> str:
        """Generate a brief reasoning for the resort's score."""
        parts = []

        # Overall assessment
        if total_score >= 8:
            parts.append(f"{resort.name} looks excellent this weekend")
        elif total_score >= 6:
            parts.append(f"{resort.name} is a solid choice")
        elif total_score >= 4:
            parts.append(f"{resort.name} is an option worth considering")
        else:
            parts.append(f"{resort.name} may not be ideal this weekend")

        # Individual factor commentary
        factors = []
        if weather_score >= 7:
            factors.append("great weather")
        elif weather_score < 4:
            factors.append("challenging weather")

        if snow_score >= 7:
            factors.append("excellent snow conditions")
        elif snow_score < 4:
            factors.append("limited snow")

        if transport_score >= 7:
            factors.append("easy access")
        elif transport_score < 4:
            factors.append("long travel time")

        if factors:
            parts.append(f"with {', '.join(factors)}")

        return ". ".join(parts) + "."

    async def get_resort_details(
        self, resort_id: str, target_date: date = None
    ) -> Optional[Recommendation]:
        """Get detailed recommendation for a specific resort."""
        resort = self.resort_service.get_resort_by_id(resort_id)
        if not resort:
            return None

        saturday, _ = self._get_next_weekend_dates()
        target_date = target_date or saturday

        # Fetch data for this specific resort
        weather = await self.weather_service.get_forecast(
            resort.coordinates.latitude,
            resort.coordinates.longitude,
            target_date,
        )
        snow = await self.snow_service.get_conditions(resort)
        transport = await self.transport_service.get_resort_journey(
            settings.start_location, resort, target_date
        )

        # Calculate scores
        (
            total_score,
            weather_score,
            snow_score,
            transport_score,
            size_score,
            highlights,
            concerns,
        ) = self.scoring_engine.score_resort(weather, snow, transport, resort)

        reasoning = self._generate_reasoning(
            resort, total_score, weather_score, snow_score, transport_score
        )

        return Recommendation(
            resort=resort,
            score=total_score,
            weather_score=weather_score,
            snow_score=snow_score,
            transport_score=transport_score,
            size_score=size_score,
            weather_forecast=weather,
            snow_conditions=snow,
            journey=transport,
            highlights=highlights,
            concerns=concerns,
            reasoning=reasoning,
        )
