# Magic Pass Resort Picker - Architecture

## System Overview

The Magic Pass Resort Picker is a full-stack web application following a three-tier architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  - User Interface                                            │
│  - State Management                                          │
│  - API Communication                                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST
                              │
┌─────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                        │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   API       │  │  Business    │  │  Data            │   │
│  │   Routes    │──│  Logic       │──│  Services        │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ API Calls
                              │
┌─────────────────────────────────────────────────────────────┐
│                    External Services                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │ Weather  │  │   Snow   │  │Transport │  │   Azure    │  │
│  │   API    │  │   API    │  │   API    │  │  OpenAI    │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Frontend
- **Framework**: React 18.2
- **Build Tool**: Vite 5.0
- **Styling**: CSS3 with custom styling (following time-app-test design pattern)
- **HTTP Client**: Fetch API (native)
- **State Management**: React Hooks (useState, useEffect)

### Backend
- **Framework**: FastAPI 0.109+
- **Runtime**: Python 3.11+
- **Server**: Uvicorn
- **HTTP Client**: httpx (async)
- **Configuration**: pydantic-settings
- **Environment**: python-dotenv

### External Services
- **Weather API**: MeteoSwiss or OpenWeather API
- **Snow Data**: SLF API / snow-forecast.com
- **Transport**: transport.opendata.ch (Swiss public transport API)
- **LLM**: Azure OpenAI (gpt-4.1-mini)

## Backend Architecture

### Directory Structure
```
backend/
├── main.py                 # FastAPI application entry point
├── config.py               # Configuration management
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not in git)
├── .env.example           # Environment template
├── models/
│   ├── __init__.py
│   ├── resort.py          # Resort data models
│   ├── weather.py         # Weather data models
│   ├── recommendation.py  # Recommendation models
├── services/
│   ├── __init__.py
│   ├── weather_service.py    # Weather API integration
│   ├── snow_service.py       # Snow data integration
│   ├── transport_service.py  # SBB/Transport API integration
│   ├── llm_service.py        # Azure OpenAI integration
│   ├── resort_service.py     # Resort data management
├── core/
│   ├── __init__.py
│   ├── scoring.py         # Resort scoring algorithm
│   ├── recommender.py     # Recommendation engine
├── data/
│   └── resorts.json       # Magic Pass resort database
└── utils/
    ├── __init__.py
    ├── cache.py           # Caching utilities
    └── logger.py          # Logging configuration
```

### API Endpoints

#### `GET /`
- Health check
- Returns: `{"status": "ok", "message": "Magic Pass Picker API"}`

#### `GET /health`
- Detailed health check
- Validates all external service connections
- Returns: Status of each service (weather, snow, transport, LLM)

#### `GET /api/resorts`
- Get list of all Magic Pass resorts
- Returns: Array of resort objects with basic info

#### `GET /api/resorts/{resort_id}`
- Get detailed information for a specific resort
- Returns: Full resort details including current conditions

#### `POST /api/recommendations`
- Generate weekend recommendations
- Request body: 
  ```json
  {
    "start_location": "Geneva",
    "target_date": "2026-01-18",  // Saturday of target weekend
    "preferences": {}  // Optional, for future use
  }
  ```
- Returns:
  ```json
  {
    "recommendations": [
      {
        "resort": {...},
        "score": 8.5,
        "weather": {...},
        "snow": {...},
        "transport": {...},
        "reasoning": "..."
      }
    ],
    "ai_summary": "Natural language recommendation from LLM",
    "generated_at": "2026-01-14T10:00:00Z",
    "target_weekend": "2026-01-18/19"
  }
  ```

#### `GET /api/weather/{resort_id}`
- Get weather forecast for specific resort
- Query params: `?days=2` (for weekend)
- Returns: Detailed weather data

#### `GET /api/transport`
- Get transport options from Geneva to resort
- Query params: `?resort_id=xxx&date=2026-01-18`
- Returns: Journey options with times and connections

## Data Models

### Resort Model
```python
class Resort(BaseModel):
    id: str                      # Unique identifier
    name: str                    # Resort name
    region: str                  # Geographic region
    canton: str                  # Swiss canton
    coordinates: Coordinates     # lat/lon
    elevation_base: int          # meters
    elevation_top: int           # meters
    access: AccessInfo           # Nearest station, PostBus info
    website: str                 # Resort URL
    magic_pass_valid: bool       # Currently on Magic Pass
```

### Weather Model
```python
class WeatherForecast(BaseModel):
    date: date
    temperature_min: float       # Celsius
    temperature_max: float
    precipitation_mm: float      # Millimeters
    snowfall_cm: Optional[float] # Centimeters
    wind_speed: float            # km/h
    wind_direction: str
    cloud_cover: int             # Percentage
    visibility: str              # Good/Moderate/Poor
    conditions: str              # Summary description
```

### Snow Model
```python
class SnowConditions(BaseModel):
    resort_id: str
    date_updated: datetime
    snow_base: Optional[int]     # cm at base
    snow_summit: Optional[int]   # cm at summit
    new_snow_24h: Optional[int]  # cm
    new_snow_7d: Optional[int]   # cm
    snow_quality: str            # powder/packed/icy/etc
    lifts_open: Optional[int]    # Number of open lifts
    runs_open: Optional[int]     # Number of open runs
```

### Transport Model
```python
class Journey(BaseModel):
    departure_time: datetime
    arrival_time: datetime
    duration_minutes: int
    changes: int
    segments: List[JourneySegment]
    
class JourneySegment(BaseModel):
    type: str                    # train/bus
    from_station: str
    to_station: str
    departure: datetime
    arrival: datetime
    line: str
```

### Recommendation Model
```python
class Recommendation(BaseModel):
    resort: Resort
    score: float                 # 0-10
    weather_score: float
    snow_score: float
    transport_score: float
    weather_forecast: WeatherForecast
    snow_conditions: SnowConditions
    journey: Journey
    highlights: List[str]        # Key positive points
    concerns: List[str]          # Warnings or negatives
    reasoning: str               # Why this score
```

## Service Layer Architecture

### WeatherService
```python
class WeatherService:
    async def get_forecast(self, lat: float, lon: float, days: int) -> WeatherForecast
    async def get_forecasts_batch(self, resorts: List[Resort]) -> Dict[str, WeatherForecast]
    def _parse_meteoswiss_data(self, raw_data: dict) -> WeatherForecast
```

### SnowService
```python
class SnowService:
    async def get_conditions(self, resort_id: str) -> SnowConditions
    async def get_conditions_batch(self, resort_ids: List[str]) -> Dict[str, SnowConditions]
    def _scrape_resort_website(self, url: str) -> SnowConditions  # Fallback
```

### TransportService
```python
class TransportService:
    async def get_journey(
        self, 
        from_location: str, 
        to_location: str, 
        date: date, 
        time: str
    ) -> List[Journey]
    
    async def get_typical_weekend_journey(
        self, 
        from_location: str, 
        resort: Resort
    ) -> Journey
```

### LLMService
```python
class LLMService:
    async def generate_recommendation_summary(
        self, 
        recommendations: List[Recommendation]
    ) -> str
    
    async def explain_resort_choice(
        self, 
        recommendation: Recommendation
    ) -> str
```

### RecommenderEngine
```python
class RecommenderEngine:
    def __init__(
        self,
        weather_service: WeatherService,
        snow_service: SnowService,
        transport_service: TransportService,
        llm_service: LLMService
    )
    
    async def generate_recommendations(
        self,
        start_location: str,
        target_date: date,
        num_recommendations: int = 5
    ) -> List[Recommendation]
    
    def _calculate_score(
        self,
        weather: WeatherForecast,
        snow: SnowConditions,
        journey: Journey
    ) -> Tuple[float, float, float, float]  # total, weather, snow, transport
```

## Frontend Architecture

### Directory Structure
```
frontend/
├── src/
│   ├── App.jsx              # Main application component
│   ├── main.jsx             # Entry point
│   ├── index.css            # Global styles
│   ├── components/
│   │   ├── Header.jsx       # App header
│   │   ├── RecommendationCard.jsx
│   │   ├── ResortDetails.jsx
│   │   ├── WeatherDisplay.jsx
│   │   ├── SnowDisplay.jsx
│   │   ├── TransportDisplay.jsx
│   │   └── LoadingSpinner.jsx
│   ├── services/
│   │   └── api.js           # API client
│   └── utils/
│       ├── dateUtils.js
│       └── formatters.js
├── index.html
├── package.json
├── vite.config.js
└── public/
    └── assets/              # Images, icons
```

### Component Hierarchy
```
App
├── Header
├── MainView
│   ├── DateSelector (shows target weekend)
│   ├── ActionButton (Get Recommendations)
│   └── RecommendationsView
│       ├── AISummary (LLM-generated text)
│       ├── RecommendationCard (x3-5)
│       │   ├── ResortHeader
│       │   ├── WeatherDisplay
│       │   ├── SnowDisplay
│       │   └── TransportDisplay
│       └── ShowMoreButton
└── Footer
```

## Data Flow

### Typical Request Flow
1. User clicks "Get Recommendations" for upcoming weekend
2. Frontend sends POST to `/api/recommendations`
3. Backend RecommenderEngine:
   a. Fetches all resort data from resorts.json
   b. Makes parallel API calls to weather service for all resorts
   c. Makes parallel API calls to snow service for all resorts
   d. Calculates transport time for each resort
   e. Scores each resort based on weighted criteria
   f. Ranks resorts and selects top 5
   g. Sends top recommendations to LLM for natural language summary
   h. Returns recommendations + AI summary to frontend
4. Frontend displays results with smooth animations

### Caching Strategy
- **Weather data**: Cache for 6 hours (key: `weather:{resort_id}:{date}`)
- **Snow data**: Cache for 12 hours (key: `snow:{resort_id}`)
- **Transport data**: Cache for 24 hours (key: `transport:{from}:{to}:{date}`)
- Cache implemented using simple dict with TTL in memory (upgradeable to Redis)

## Configuration Management

### Environment Variables (.env)
```bash
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_API_KEY=xxx
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4.1-mini
AZURE_OPENAI_API_VERSION=2024-05-01-preview

# Weather API
WEATHER_API_KEY=xxx
WEATHER_API_URL=https://api.meteoswiss.ch/...

# Snow API (if needed)
SNOW_API_KEY=xxx

# Transport API
TRANSPORT_API_KEY=xxx  # May not be needed for transport.opendata.ch

# Application Settings
START_LOCATION=Geneva
CORS_ORIGINS=http://localhost:5173
LOG_LEVEL=INFO
CACHE_ENABLED=true
CACHE_TTL_HOURS=6
```

## Error Handling

### Backend Error Strategy
1. **API Failures**: Catch and log, return partial data with warnings
2. **Data Validation**: Use Pydantic models, return 422 for invalid data
3. **Service Unavailable**: Return 503 with specific service info
4. **Rate Limiting**: Implement backoff, use cached data when available
5. **Logging**: Comprehensive logging for debugging

### Frontend Error Strategy
1. **Network Errors**: Show user-friendly message with retry option
2. **Partial Data**: Display what's available, indicate missing data
3. **Loading States**: Always show loading indicators
4. **Timeout**: Set reasonable timeout (15s), show timeout message

## Security Considerations

1. **API Keys**: All keys in .env, never exposed to frontend
2. **CORS**: Properly configured for localhost in development
3. **Input Validation**: Validate all inputs on backend
4. **Rate Limiting**: Implement rate limiting on API endpoints (future)
5. **No Authentication**: Not required for MVP (local use only)

## Performance Considerations

1. **Parallel API Calls**: Use asyncio for concurrent external API calls
2. **Caching**: Reduce redundant API calls
3. **Pagination**: If displaying many resorts, implement pagination
4. **Lazy Loading**: Load detailed data only when needed
5. **Optimization**: Keep LLM prompts concise to reduce latency

## Deployment Architecture (Future)

### Local Deployment (MVP)
- Backend: Run uvicorn on localhost:8000
- Frontend: Run vite dev server on localhost:5173
- No database needed (JSON file sufficient)

### Cloud Deployment (Future Phase)
- Backend: Azure App Service or Container Instances
- Frontend: Azure Static Web Apps or Netlify
- Database: Azure PostgreSQL (when needed)
- Caching: Azure Redis Cache
- Monitoring: Azure Application Insights

## Testing Strategy

### Backend Testing
- Unit tests for scoring algorithm
- Integration tests for API endpoints
- Mock external API calls for reliability
- Test error handling scenarios

### Frontend Testing
- Component testing with React Testing Library
- E2E tests with Playwright (optional)
- Manual testing for UI/UX

## Monitoring & Observability

### Logging
- Log all API calls with timestamps
- Log scoring decisions
- Log errors with full context
- Use structured logging (JSON format)

### Metrics (Future)
- API response times
- External service availability
- Cache hit rates
- User engagement metrics

## Extensibility Points

The architecture is designed to be extensible:

1. **New Data Sources**: Modular service layer makes adding sources easy
2. **Additional Start Locations**: Configuration-driven
3. **User Preferences**: Models already support optional preferences
4. **Database Layer**: Easy to swap JSON file for PostgreSQL
5. **Authentication**: Can be added without major refactoring
6. **Mobile App**: API is client-agnostic, can serve mobile clients
7. **ML Models**: Can replace or augment scoring algorithm

## Dependencies

### Python Backend
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-dotenv==1.0.0
httpx==0.27.2
openai==1.54.3
pydantic==2.5.3
pydantic-settings==2.1.0
```

### JavaScript Frontend
```
react==18.2.0
react-dom==18.2.0
vite==5.0.8
@vitejs/plugin-react==4.2.1
```

## Development Workflow

1. **Setup**: Clone repo, create .env, install dependencies
2. **Backend Dev**: Run `uvicorn main:app --reload --port 8000`
3. **Frontend Dev**: Run `npm run dev` in frontend directory
4. **Testing**: Test endpoints with browser/Postman
5. **Iteration**: Make changes, test, commit
6. **Documentation**: Keep docs updated as architecture evolves

This architecture provides a solid foundation that Claude Code CLI can implement systematically, starting with the backend services and building up to the complete application.
