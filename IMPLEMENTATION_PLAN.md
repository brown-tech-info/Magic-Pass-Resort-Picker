# Magic Pass Resort Picker - Implementation Plan

This document provides a step-by-step implementation plan for Claude Code CLI to build the Magic Pass Resort Picker application.

## Prerequisites
- Python 3.11+ installed
- Node.js 18+ installed
- Azure OpenAI credentials configured (from time-app-test)
- VS Code or preferred editor

## Phase 1: Project Setup and Foundation (Steps 1-5)

### Step 1: Initialize Project Structure
**Goal**: Create the base directory structure and copy time-app-test foundation

**Tasks**:
1. Create main project directory: `magic-pass-picker/`
2. Copy backend structure from time-app-test:
   - `backend/` directory
   - Copy `config.py`, `.env.example`
   - Copy `requirements.txt` as starting point
3. Copy frontend structure from time-app-test:
   - `frontend/` directory with `src/`, `public/`
   - Copy `package.json`, `vite.config.js`, `index.html`
4. Create new directories:
   - `backend/models/`
   - `backend/services/`
   - `backend/core/`
   - `backend/data/`
   - `backend/utils/`
   - `frontend/src/components/`
   - `frontend/src/services/`
5. Copy over `.gitignore` from time-app-test

**Validation**:
- Directory structure matches ARCHITECTURE.md
- All base files present

### Step 2: Create Data Models
**Goal**: Define all Pydantic models for type safety

**Tasks**:
1. Create `backend/models/resort.py`:
   - Resort model
   - Coordinates model
   - AccessInfo model
2. Create `backend/models/weather.py`:
   - WeatherForecast model
3. Create `backend/models/snow.py`:
   - SnowConditions model
4. Create `backend/models/transport.py`:
   - Journey model
   - JourneySegment model
5. Create `backend/models/recommendation.py`:
   - Recommendation model
   - RecommendationsResponse model

**Validation**:
- All models have proper type hints
- Models can be imported without errors
- Pydantic validation works

### Step 3: Create Resort Database
**Goal**: Build the JSON database of all Magic Pass resorts

**Tasks**:
1. Create `backend/data/resorts.json`
2. Research and add all Magic Pass resorts with:
   - Basic information (name, region, canton)
   - Coordinates (can use approximate)
   - Elevation data
   - Nearest train station
   - PostBus connection info if applicable
3. Include at least 20-30 resorts covering major regions
4. Validate JSON structure

**Sample Resort Entry**:
```json
{
  "id": "saas-fee",
  "name": "Saas-Fee",
  "region": "Valais",
  "canton": "VS",
  "coordinates": {
    "latitude": 46.1097,
    "longitude": 7.9283
  },
  "elevation_base": 1800,
  "elevation_top": 3600,
  "access": {
    "nearest_station": "Brig",
    "postbus_required": true,
    "postbus_duration_minutes": 60
  },
  "website": "https://www.saas-fee.ch",
  "magic_pass_valid": true
}
```

**Validation**:
- JSON is valid and parseable
- All required fields present for each resort
- Can be loaded into Resort model

### Step 4: Create Resort Service
**Goal**: Implement service to load and query resort data

**Tasks**:
1. Create `backend/services/resort_service.py`
2. Implement ResortService class:
   - `load_resorts()`: Load from JSON file
   - `get_all_resorts()`: Return all resorts
   - `get_resort_by_id()`: Get specific resort
   - `get_resorts_by_region()`: Filter by region
3. Add error handling for missing file/invalid data
4. Add caching for loaded resorts

**Validation**:
- Can load resorts successfully
- Returns proper Resort objects
- Handles errors gracefully

### Step 5: Update Backend Configuration
**Goal**: Extend config for new services

**Tasks**:
1. Update `backend/config.py`:
   - Add weather API settings
   - Add transport API settings
   - Add caching settings
   - Keep existing Azure OpenAI settings
2. Update `.env.example` with new variables
3. Create your actual `.env` with real credentials

**Validation**:
- All new settings load correctly
- Existing Azure OpenAI config still works
- .env.example is comprehensive

## Phase 2: External API Integration (Steps 6-9)

### Step 6: Implement Weather Service
**Goal**: Integrate with weather API (MeteoSwiss or OpenWeather)

**Decision Point**: Choose weather API based on:
- Availability: Does it cover Swiss mountains?
- Cost: Free tier sufficient?
- Documentation: Easy to integrate?

**Recommended**: Start with OpenWeather API (free tier, well-documented)

**Tasks**:
1. Create `backend/services/weather_service.py`
2. Implement WeatherService class:
   - `get_forecast()`: Get forecast for specific coordinates
   - `get_forecasts_batch()`: Get forecasts for multiple resorts (parallel)
   - Parse API response into WeatherForecast model
3. Add error handling and retries
4. Add caching (6 hour TTL)
5. Write helper function to extract weekend (Sat/Sun) data

**API Integration**:
- Sign up for OpenWeather API key
- Add key to .env
- Test with Geneva coordinates first
- Then test with resort coordinates

**Validation**:
- Can fetch weather for a single location
- Can fetch weather for multiple locations in parallel
- Returns valid WeatherForecast objects
- Caching works correctly
- Errors handled gracefully

### Step 7: Implement Snow Service
**Goal**: Get snow conditions for resorts

**Decision Point**: Snow data sources:
- Option A: SLF (Swiss Avalanche Institute) API if available
- Option B: snow-forecast.com API
- Option C: Web scraping resort websites (fallback)

**Recommended**: Start with snow-forecast.com or web scraping

**Tasks**:
1. Create `backend/services/snow_service.py`
2. Implement SnowService class:
   - `get_conditions()`: Get conditions for one resort
   - `get_conditions_batch()`: Get conditions for multiple resorts
   - Parse data into SnowConditions model
3. Handle missing data gracefully (some resorts may not have data)
4. Add caching (12 hour TTL)

**Fallback Strategy**:
If automated data unavailable:
- Return None for snow data
- System should still provide recommendations based on weather and transport

**Validation**:
- Can fetch snow data for major resorts
- Returns valid SnowConditions objects
- Handles missing data without crashing
- Caching works

### Step 8: Implement Transport Service
**Goal**: Calculate journey times from Geneva to resorts

**Recommended API**: transport.opendata.ch (free, no API key needed)

**Tasks**:
1. Create `backend/services/transport_service.py`
2. Implement TransportService class:
   - `get_journey()`: Get journey from A to B at specific time
   - `get_typical_weekend_journey()`: Get Saturday morning journey
   - Parse API response into Journey model
   - Handle train + PostBus combinations
3. For resorts without direct public transport, estimate or mark as N/A
4. Add caching (24 hour TTL)

**API Details**:
- Endpoint: `http://transport.opendata.ch/v1/connections`
- Query params: `from`, `to`, `date`, `time`
- No authentication required

**Validation**:
- Can get journey from Geneva to Brig (test)
- Can get journey to multiple resorts
- Returns valid Journey objects
- Handles "no route" scenarios
- Caching works

### Step 9: Implement LLM Service
**Goal**: Generate natural language recommendations using Azure OpenAI

**Tasks**:
1. Create `backend/services/llm_service.py`
2. Implement LLMService class (based on time-app-test pattern):
   - `generate_recommendation_summary()`: Create overall summary
   - `explain_resort_choice()`: Explain individual recommendation
3. Design effective prompts:
   - Include all recommendation data in prompt
   - Ask for concise, actionable advice
   - Request 2-3 paragraph response
   - Emphasize key factors (weather, snow, travel)
4. Reuse existing Azure OpenAI client from config

**Example Prompt**:
```
You are a helpful assistant for ski trip planning. Based on the following data 
for Magic Pass resorts this coming weekend, provide a brief recommendation 
(2-3 paragraphs) on where to go snowboarding from Geneva.

Top Recommendations:
1. Saas-Fee - Score: 8.5/10
   - Weather: Sunny, -5°C, 20cm fresh snow expected
   - Snow: 180cm base, excellent conditions
   - Travel: 3h 15min by train + PostBus
   
2. Davos - Score: 8.2/10
   - Weather: Partly cloudy, -3°C, 10cm fresh snow
   - Snow: 150cm base, good conditions
   - Travel: 2h 45min by train

[Include top 3-5]

Provide a conversational recommendation with your reasoning.
```

**Validation**:
- Generates coherent, helpful recommendations
- Response is concise (not too long)
- Uses data from recommendations
- Handles API errors gracefully

## Phase 3: Recommendation Engine (Steps 10-11)

### Step 10: Implement Scoring Algorithm
**Goal**: Create the scoring logic that ranks resorts

**Tasks**:
1. Create `backend/core/scoring.py`
2. Implement scoring functions:
   - `score_weather()`: 0-10 score based on weather forecast
     - Factors: temperature, precipitation, fresh snow, visibility
   - `score_snow()`: 0-10 score based on snow conditions
     - Factors: base depth, fresh snow, snow quality
   - `score_transport()`: 0-10 score based on travel time
     - Factors: total duration, number of changes
   - `calculate_total_score()`: Weighted average
3. Define weights:
   - Weather: 40%
   - Snow: 40%
   - Transport: 20%

**Scoring Logic Examples**:

**Weather Scoring**:
- Perfect conditions (10/10): Sunny, -5 to -10°C, 20+ cm fresh snow, good visibility
- Good conditions (7-9/10): Mostly sunny/cloudy, decent temps, some fresh snow
- Poor conditions (0-3/10): Heavy precipitation, warm temps, poor visibility

**Snow Scoring**:
- Perfect (10/10): 150+ cm base, 20+ cm fresh, powder
- Good (7-9/10): 100+ cm base, some fresh snow, good quality
- Poor (0-3/10): <50cm base, no fresh snow, icy

**Transport Scoring**:
- Excellent (10/10): <2 hours, direct
- Good (7-9/10): 2-3 hours, 1-2 changes
- Fair (4-6/10): 3-4 hours
- Poor (0-3/10): 4+ hours

**Validation**:
- Scores are in 0-10 range
- Weighted average calculation correct
- Scoring makes intuitive sense
- Test with mock data

### Step 11: Implement Recommendation Engine
**Goal**: Orchestrate all services to generate recommendations

**Tasks**:
1. Create `backend/core/recommender.py`
2. Implement RecommenderEngine class:
   - Initialize with all service dependencies
   - `generate_recommendations()`: Main entry point
     a. Load all resorts
     b. Get weather forecasts (parallel)
     c. Get snow conditions (parallel)
     d. Get transport info (parallel)
     e. Calculate scores for each resort
     f. Sort by score, take top N
     g. Generate AI summary
     h. Return Recommendations object
3. Handle partial failures gracefully:
   - If weather API fails for one resort, use default score
   - If snow data missing, focus on weather + transport
   - Always return something useful
4. Add comprehensive logging

**Validation**:
- Can generate recommendations end-to-end
- Returns valid Recommendation objects
- Handles API failures gracefully
- Completes in reasonable time (<15 seconds)
- Logging provides good debugging info

## Phase 4: Backend API Endpoints (Steps 12-13)

### Step 12: Create API Routes
**Goal**: Implement FastAPI endpoints

**Tasks**:
1. Update `backend/main.py`:
   - Initialize all services on startup
   - Create RecommenderEngine instance
2. Implement endpoints:
   - `GET /`: Basic health check
   - `GET /health`: Detailed health with service status
   - `GET /api/resorts`: List all resorts
   - `GET /api/resorts/{resort_id}`: Get specific resort
   - `POST /api/recommendations`: Generate recommendations
   - `GET /api/weather/{resort_id}`: Get weather for resort
   - `GET /api/transport`: Get transport info
3. Add request validation
4. Add error handling
5. Add CORS middleware (copy from time-app-test)

**POST /api/recommendations Request Body**:
```json
{
  "start_location": "Geneva",
  "target_date": "2026-01-18"
}
```

**Validation**:
- All endpoints return correct status codes
- Response models match expected structure
- Errors return meaningful messages
- CORS works for frontend

### Step 13: Implement Caching Layer
**Goal**: Add caching to reduce API calls

**Tasks**:
1. Create `backend/utils/cache.py`
2. Implement simple in-memory cache:
   - Dict-based cache with TTL
   - `get(key)`: Retrieve cached value
   - `set(key, value, ttl)`: Store with expiration
   - `clear()`: Clear all cache
   - Background task to clean expired entries
3. Integrate caching into services:
   - Weather service: 6 hour cache
   - Snow service: 12 hour cache
   - Transport service: 24 hour cache
4. Add cache control to config (enable/disable)

**Validation**:
- Cache stores and retrieves values
- TTL expiration works
- Services use cache correctly
- Can disable caching for testing

## Phase 5: Frontend Development (Steps 14-17)

### Step 14: Create API Client
**Goal**: Build frontend service to communicate with backend

**Tasks**:
1. Create `frontend/src/services/api.js`
2. Implement API client functions:
   - `getResorts()`: GET /api/resorts
   - `getRecommendations(targetDate)`: POST /api/recommendations
   - `getResortDetails(resortId)`: GET /api/resorts/{id}
3. Add error handling
4. Add loading states

**Validation**:
- Can successfully call backend endpoints
- Errors are caught and returned
- Responses are parsed correctly

### Step 15: Create Core Components
**Goal**: Build reusable UI components

**Tasks**:
1. Create `frontend/src/components/Header.jsx`:
   - App title
   - Current date indicator
2. Create `frontend/src/components/RecommendationCard.jsx`:
   - Resort name and region
   - Weather summary with icons
   - Snow conditions
   - Travel time
   - Score/rating indicator
3. Create `frontend/src/components/WeatherDisplay.jsx`:
   - Temperature
   - Conditions (sunny/cloudy/snow)
   - Icons for weather
4. Create `frontend/src/components/SnowDisplay.jsx`:
   - Base depth
   - Fresh snow
   - Quality indicator
5. Create `frontend/src/components/TransportDisplay.jsx`:
   - Journey duration
   - Departure time
   - Connection info
6. Create `frontend/src/components/LoadingSpinner.jsx`:
   - Animated loading indicator

**Design Notes**:
- Follow time-app-test styling patterns
- Use gradients and modern design
- Make it visually appealing for ski/snow theme
- Use emojis/icons where appropriate

**Validation**:
- Components render correctly
- Props are properly typed
- Styling matches design vision

### Step 16: Build Main Application View
**Goal**: Assemble components into main app

**Tasks**:
1. Update `frontend/src/App.jsx`:
   - State management for recommendations
   - Date selector (shows target weekend)
   - "Get Recommendations" button
   - Loading state
   - Display recommendations when loaded
   - Error handling UI
2. Implement flow:
   - Calculate next weekend date on load
   - Button click triggers API call
   - Show loading spinner
   - Display results with animations
   - Show AI summary prominently
   - Display recommendation cards
3. Add smooth transitions and animations

**Validation**:
- Can request recommendations
- Loading states work
- Recommendations display correctly
- UI is responsive
- Errors show user-friendly messages

### Step 17: Style and Polish Frontend
**Goal**: Make UI beautiful and professional

**Tasks**:
1. Update `frontend/src/index.css`:
   - Create ski/snow themed design
   - Use winter color palette (blues, whites, grays)
   - Add subtle animations
   - Ensure responsive design
2. Add weather/snow icons or emojis:
   - ☀️ Sunny
   - ⛅ Partly cloudy
   - 🌨️ Snow
   - 🚂 Train
   - 🚌 Bus
3. Polish recommendation cards:
   - Hover effects
   - Score visualization (bars/circles)
   - Clear visual hierarchy
4. Add favicon and page title

**Validation**:
- UI looks professional
- Colors and fonts are consistent
- Animations are smooth
- Works on different screen sizes

## Phase 6: Integration and Testing (Steps 18-20)

### Step 18: End-to-End Testing
**Goal**: Test complete workflow

**Tasks**:
1. Start backend: `uvicorn main:app --port 8000`
2. Start frontend: `npm run dev`
3. Test full flow:
   - Load application
   - Click "Get Recommendations"
   - Verify recommendations appear
   - Check data accuracy
   - Test error scenarios
4. Test with different dates
5. Test with network issues (simulate API failures)

**Validation Checklist**:
- [ ] Backend starts without errors
- [ ] Frontend loads correctly
- [ ] Can get recommendations successfully
- [ ] Recommendations make sense
- [ ] Weather data is accurate
- [ ] Snow data displays correctly
- [ ] Transport times are reasonable
- [ ] AI summary is helpful
- [ ] Error handling works
- [ ] Loading states work
- [ ] UI is responsive

### Step 19: Documentation
**Goal**: Create user and developer documentation

**Tasks**:
1. Create `README.md`:
   - Project overview
   - Setup instructions
   - Environment variables needed
   - Running the application
   - Troubleshooting section
2. Create `SETUP_GUIDE.md`:
   - Detailed step-by-step setup
   - Getting API keys
   - Configuration details
3. Update inline code comments
4. Document API endpoints with examples

**Validation**:
- Documentation is clear and complete
- Another developer could set up the app
- Common issues are documented

### Step 20: Final Polish and Optimization
**Goal**: Optimize performance and user experience

**Tasks**:
1. Backend optimization:
   - Verify parallel API calls working
   - Check cache hit rates
   - Optimize LLM prompts for speed
   - Add request timeouts
2. Frontend optimization:
   - Minimize unnecessary re-renders
   - Optimize images/assets
   - Test load times
3. User experience:
   - Add helpful tooltips
   - Add "About" section explaining methodology
   - Add links to resort websites
4. Final testing across browsers

**Validation**:
- Recommendations generate in <10 seconds
- UI is snappy and responsive
- No console errors
- Professional look and feel

## Phase 7: Deployment Preparation (Optional)

### Step 21: Prepare for Deployment (Future)
**Goal**: Make app ready for cloud deployment

**Tasks** (when ready):
1. Create `docker-compose.yml` for containerization
2. Add production environment configurations
3. Set up proper logging
4. Add monitoring hooks
5. Create deployment documentation

**Not required for MVP** - focus on local development first

## Dependencies Installation Commands

### Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
```

### Frontend Setup
```bash
cd frontend
npm install
```

## Running the Application

### Start Backend
```bash
cd backend
venv\Scripts\activate
uvicorn main:app --port 8000
# Or without reload: uvicorn main:app --port 8000
```

### Start Frontend
```bash
cd frontend
npm run dev
```

### Access Application
Open browser to: http://localhost:5173

## Common Issues and Solutions

### Issue: Azure OpenAI Connection Error
**Solution**: Verify .env has correct endpoint and API key from time-app-test

### Issue: Weather API Returns 401
**Solution**: Check API key is valid and has not expired

### Issue: No Snow Data Available
**Solution**: This is expected for some resorts, app should handle gracefully

### Issue: Transport API Times Out
**Solution**: Increase timeout in httpx calls, or skip transport for that resort

### Issue: Recommendations Take Too Long
**Solution**: 
- Verify parallel API calls working
- Check cache is enabled
- Reduce number of resorts processed (test with subset first)

## Success Criteria

MVP is complete when:
- ✅ Can load all Magic Pass resorts
- ✅ Can fetch weather forecasts for resorts
- ✅ Can fetch snow conditions (even if partial)
- ✅ Can calculate transport times from Geneva
- ✅ Can score and rank resorts
- ✅ Can generate AI-powered recommendations
- ✅ Frontend displays recommendations beautifully
- ✅ Complete workflow works end-to-end
- ✅ Error handling is robust
- ✅ Documentation is complete

## Estimated Timeline

- Phase 1 (Setup): 1-2 hours
- Phase 2 (API Integration): 3-4 hours
- Phase 3 (Recommendation Engine): 2-3 hours
- Phase 4 (Backend API): 1-2 hours
- Phase 5 (Frontend): 3-4 hours
- Phase 6 (Integration & Testing): 2-3 hours

**Total: 12-18 hours of development time**

With Claude Code CLI working autonomously, this could be significantly faster, potentially completing in 1-2 sessions.

## Next Steps After MVP

Once MVP is working:
1. Add user preferences (powder vs groomed, altitude preference)
2. Add historical data tracking
3. Add webcam integration
4. Add avalanche risk information
5. Support multiple starting locations
6. Add favorite resorts
7. Add email/SMS notifications
8. Mobile app version
9. Deploy to cloud
10. Add user accounts

---

This implementation plan provides Claude Code CLI with clear, actionable steps to build the complete Magic Pass Resort Picker application from scratch.
