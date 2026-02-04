import asyncio
import json
import logging
from datetime import date
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config import get_settings
from models.resort import Resort
from models.recommendation import Recommendation, RecommendationsResponse
from services.resort_service import ResortService
from services.weather_service import WeatherService
from services.snow_service import SnowService
from services.transport_service import TransportService
from services.llm_service import LLMService
from core.recommender import RecommenderEngine
from utils.progress import ProgressTracker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load settings
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title="Magic Pass Resort Picker API",
    description="API for recommending the best Magic Pass ski resorts for weekend trips from Geneva",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
resort_service = ResortService()
weather_service = WeatherService()
snow_service = SnowService()
transport_service = TransportService()
llm_service = LLMService()

# Initialize recommendation engine
recommender = RecommenderEngine(
    resort_service=resort_service,
    weather_service=weather_service,
    snow_service=snow_service,
    transport_service=transport_service,
    llm_service=llm_service,
)


# Request/Response models
class RecommendationRequest(BaseModel):
    start_location: str = "Geneva"
    target_date: Optional[str] = None
    num_recommendations: int = 5


class HealthStatus(BaseModel):
    status: str
    services: dict


# Endpoints
@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Magic Pass Resort Picker API"}


@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Detailed health check with service status."""
    services = {
        "resorts": "ok",
        "weather": "ok" if settings.openweather_api_key else "not configured",
        "llm": "ok" if settings.azure_openai_api_key else "not configured",
        "transport": "ok",  # No API key needed
    }

    # Try to load resorts
    try:
        resorts = resort_service.get_all_resorts()
        services["resorts"] = f"ok ({len(resorts)} resorts loaded)"
    except Exception as e:
        services["resorts"] = f"error: {str(e)}"

    overall_status = "ok" if all(
        "error" not in v for v in services.values()
    ) else "degraded"

    return HealthStatus(status=overall_status, services=services)


@app.get("/api/resorts", response_model=List[Resort])
async def get_resorts():
    """Get all Magic Pass resorts."""
    try:
        resorts = resort_service.get_all_resorts()
        return resorts
    except Exception as e:
        logger.error(f"Error fetching resorts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/resorts/{resort_id}", response_model=Resort)
async def get_resort(resort_id: str):
    """Get a specific resort by ID."""
    resort = resort_service.get_resort_by_id(resort_id)
    if not resort:
        raise HTTPException(status_code=404, detail="Resort not found")
    return resort


@app.post("/api/recommendations", response_model=RecommendationsResponse)
async def get_recommendations(request: RecommendationRequest):
    """Generate weekend ski resort recommendations."""
    try:
        # Parse target date if provided
        target_date = None
        if request.target_date:
            try:
                target_date = date.fromisoformat(request.target_date)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date format. Use YYYY-MM-DD",
                )

        logger.info(
            f"Generating recommendations for {request.start_location}, "
            f"date={target_date}, count={request.num_recommendations}"
        )

        recommendations = await recommender.generate_recommendations(
            start_location=request.start_location,
            target_date=target_date,
            num_recommendations=request.num_recommendations,
        )

        return recommendations

    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/recommendations/stream")
async def stream_recommendations(request: RecommendationRequest):
    """Generate weekend ski resort recommendations with SSE progress updates."""
    # Parse target date if provided
    target_date = None
    if request.target_date:
        try:
            target_date = date.fromisoformat(request.target_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYY-MM-DD",
            )

    logger.info(
        f"Streaming recommendations for {request.start_location}, "
        f"date={target_date}, count={request.num_recommendations}"
    )

    async def event_generator():
        progress = ProgressTracker()

        async def run_recommendations():
            try:
                result = await recommender.generate_recommendations_with_progress(
                    progress=progress,
                    start_location=request.start_location,
                    target_date=target_date,
                    num_recommendations=request.num_recommendations,
                )
                return result
            except Exception as e:
                logger.error(f"Error in recommendation generation: {e}")
                raise

        # Start recommendation generation as a task
        task = asyncio.create_task(run_recommendations())

        # Stream progress updates
        try:
            while not task.done():
                try:
                    # Wait for progress update with timeout
                    update = await asyncio.wait_for(
                        progress.queue.get(),
                        timeout=0.5,
                    )
                    event_data = json.dumps({"type": "progress", "data": update.to_dict()})
                    yield f"data: {event_data}\n\n"
                except asyncio.TimeoutError:
                    # No update available, check if task is still running
                    continue

            # Drain any remaining progress updates
            while not progress.queue.empty():
                update = await progress.queue.get()
                event_data = json.dumps({"type": "progress", "data": update.to_dict()})
                yield f"data: {event_data}\n\n"

            # Get final result
            result = await task

            # Send final result - need custom serialization for Pydantic models
            result_dict = result.model_dump(mode="json")
            event_data = json.dumps({"type": "result", "data": result_dict})
            yield f"data: {event_data}\n\n"

        except Exception as e:
            logger.error(f"Error in SSE stream: {e}")
            error_data = json.dumps({"type": "error", "data": {"message": str(e)}})
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/recommendations/{resort_id}", response_model=Recommendation)
async def get_resort_recommendation(
    resort_id: str,
    target_date: Optional[str] = Query(None, description="Target date (YYYY-MM-DD)"),
):
    """Get detailed recommendation for a specific resort."""
    try:
        parsed_date = None
        if target_date:
            try:
                parsed_date = date.fromisoformat(target_date)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date format. Use YYYY-MM-DD",
                )

        recommendation = await recommender.get_resort_details(
            resort_id=resort_id,
            target_date=parsed_date,
        )

        if not recommendation:
            raise HTTPException(status_code=404, detail="Resort not found")

        return recommendation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting resort recommendation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/weather/{resort_id}")
async def get_resort_weather(
    resort_id: str,
    target_date: Optional[str] = Query(None, description="Target date (YYYY-MM-DD)"),
):
    """Get weather forecast for a specific resort."""
    resort = resort_service.get_resort_by_id(resort_id)
    if not resort:
        raise HTTPException(status_code=404, detail="Resort not found")

    try:
        parsed_date = None
        if target_date:
            try:
                parsed_date = date.fromisoformat(target_date)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date format. Use YYYY-MM-DD",
                )
        else:
            # Default to next Saturday
            from datetime import timedelta
            today = date.today()
            days_until_saturday = (5 - today.weekday()) % 7
            parsed_date = today + timedelta(days=days_until_saturday or 7)

        forecast = await weather_service.get_forecast(
            resort.coordinates.latitude,
            resort.coordinates.longitude,
            parsed_date,
        )

        if not forecast:
            raise HTTPException(
                status_code=503,
                detail="Weather data temporarily unavailable",
            )

        return forecast

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting weather: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/transport")
async def get_transport(
    resort_id: str = Query(..., description="Resort ID"),
    from_location: str = Query("Geneva", description="Starting location"),
    target_date: Optional[str] = Query(None, description="Target date (YYYY-MM-DD)"),
):
    """Get transport options to a resort."""
    resort = resort_service.get_resort_by_id(resort_id)
    if not resort:
        raise HTTPException(status_code=404, detail="Resort not found")

    try:
        parsed_date = None
        if target_date:
            try:
                parsed_date = date.fromisoformat(target_date)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date format. Use YYYY-MM-DD",
                )
        else:
            # Default to next Saturday
            from datetime import timedelta
            today = date.today()
            days_until_saturday = (5 - today.weekday()) % 7
            parsed_date = today + timedelta(days=days_until_saturday or 7)

        journey = await transport_service.get_resort_journey(
            from_location, resort, parsed_date
        )

        if not journey:
            raise HTTPException(
                status_code=503,
                detail="Transport data temporarily unavailable",
            )

        return journey

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transport: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
