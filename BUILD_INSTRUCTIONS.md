# BUILD INSTRUCTIONS FOR CLAUDE CODE CLI

## Project Overview
Build the **Magic Pass Resort Picker** - a web app that recommends the best Magic Pass ski resorts for weekend snowboarding from Geneva based on weather, snow conditions, and public transport.

## Context Documents
Read these files in the current directory to understand the project:
1. `PROJECT_BRIEF.md` - What we're building and why
2. `REQUIREMENTS.md` - All functional requirements
3. `ARCHITECTURE.md` - System design and structure
4. `API_INTEGRATION.md` - External API details
5. `IMPLEMENTATION_PLAN.md` - Step-by-step build guide

## Your Mission
Build the complete application from scratch following IMPLEMENTATION_PLAN.md (all 20 steps across 6 phases).

## Technical Foundation
This project is based on the **time-app-test** architecture (which works and is proven):
- Backend: Python + FastAPI + Azure OpenAI
- Frontend: React + Vite
- Same patterns, extended functionality

## Environment Setup You'll Need to Do First

### 1. Create Project Structure
```
magic-pass-picker/
├── backend/
│   ├── models/
│   ├── services/
│   ├── core/
│   ├── data/
│   └── utils/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   └── utils/
│   └── public/
└── [documentation files]
```

### 2. Backend Setup

**Create `backend/requirements.txt`:**
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-dotenv==1.0.0
httpx==0.27.2
openai==1.54.3
pydantic==2.5.3
pydantic-settings==2.1.0
beautifulsoup4==4.12.3
```

**Create `backend/.env.example`:**
```bash
# Azure OpenAI (user will provide from their time-app-test)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/openai/v1/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4.1-mini
AZURE_OPENAI_API_VERSION=2024-05-01-preview

# Weather API (user needs to sign up at openweathermap.org)
OPENWEATHER_API_KEY=your-key-here

# App Settings
START_LOCATION=Geneva
CORS_ORIGINS=http://localhost:5173
LOG_LEVEL=INFO
CACHE_ENABLED=true
WEATHER_CACHE_HOURS=6
SNOW_CACHE_HOURS=12
TRANSPORT_CACHE_HOURS=24
```

**Tell user they need to:**
- Copy `.env.example` to `.env`
- Fill in Azure OpenAI credentials from their time-app-test project
- Sign up for free OpenWeather API key at https://openweathermap.org/api
- Add the OpenWeather key to `.env`

### 3. Frontend Setup

**Create `frontend/package.json`:**
```json
{
  "name": "magic-pass-picker-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@vitejs/plugin-react": "^4.2.1",
    "vite": "^5.0.8"
  }
}
```

**Tell user to run:**
```bash
cd frontend
npm install
```

## Implementation Order

Follow IMPLEMENTATION_PLAN.md exactly:

### Phase 1: Foundation (Steps 1-5)
1. ✅ Create directory structure (you'll do this)
2. Create all Pydantic models in `backend/models/`
3. Create `backend/data/resorts.json` with 20-30 Magic Pass resorts
4. Create `backend/services/resort_service.py`
5. Create `backend/config.py` for environment configuration

### Phase 2: External APIs (Steps 6-9)
6. Implement `backend/services/weather_service.py` (OpenWeather API)
7. Implement `backend/services/snow_service.py` (scraping snow-forecast.com)
8. Implement `backend/services/transport_service.py` (transport.opendata.ch API)
9. Implement `backend/services/llm_service.py` (Azure OpenAI - reuse time-app pattern)

### Phase 3: Recommendation Engine (Steps 10-11)
10. Implement `backend/core/scoring.py` (scoring algorithm)
11. Implement `backend/core/recommender.py` (orchestrates everything)

### Phase 4: Backend API (Steps 12-13)
12. Create `backend/main.py` with all API endpoints
13. Implement `backend/utils/cache.py` for caching

### Phase 5: Frontend (Steps 14-17)
14. Create `frontend/src/services/api.js`
15. Create all React components in `frontend/src/components/`
16. Create `frontend/src/App.jsx` (main application)
17. Create `frontend/src/index.css` (beautiful ski-themed styling)

### Phase 6: Integration (Steps 18-20)
18. Test end-to-end flow
19. Create `README.md` with setup and usage instructions
20. Final polish and optimization

## Critical Implementation Notes

### Weather Service (Step 6)
- Use OpenWeather "One Call API 3.0"
- Endpoint: `https://api.openweathermap.org/data/3.0/onecall`
- Parse daily forecasts for weekend (Saturday/Sunday)
- Cache for 6 hours
- Handle missing data gracefully

### Snow Service (Step 7)
- Use web scraping from snow-forecast.com
- Pattern: `https://www.snow-forecast.com/resorts/{resort-slug}/6day/mid`
- Parse snow depth from HTML (use BeautifulSoup)
- If data unavailable for a resort, return None (don't crash)
- Cache for 12 hours

### Transport Service (Step 8)
- Use Swiss OpenData: `http://transport.opendata.ch/v1/connections`
- No API key needed (it's free and open)
- Query from "Geneva" to resort or nearest station
- Parse journey time and connections
- Cache for 24 hours

### LLM Service (Step 9)
- Reuse the pattern from time-app-test
- Use OpenAI client (not AzureOpenAI class)
- Create comprehensive prompts with all recommendation data
- Ask for 2-3 paragraph conversational summary
- Keep it friendly and actionable

### Resort Database (Step 3)
Include major Magic Pass resorts like:
- Saas-Fee, Davos, Arosa, Grindelwald, Meiringen, Adelboden
- Flumserberg, Pizol, Klewenalp, Melchsee-Frutt
- At least 20-30 resorts total
- Include coordinates, elevation, nearest station

### Scoring Algorithm (Step 10)
**Weights:**
- Weather: 40%
- Snow: 40%
- Transport: 20%

**Weather Scoring (0-10):**
- Perfect: Sunny, -5 to -10°C, 20+ cm fresh snow
- Good: Partly cloudy, decent temps, some fresh snow
- Poor: Rain, warm temps, bad visibility

**Snow Scoring (0-10):**
- Perfect: 150+ cm base, 20+ cm fresh, powder
- Good: 100+ cm base, some fresh
- Poor: <50 cm base, icy

**Transport Scoring (0-10):**
- Perfect: <2 hours
- Good: 2-3 hours
- Poor: 4+ hours

## User Instructions to Provide

After building, create a `README.md` that tells the user:

```markdown
# Magic Pass Resort Picker

## Setup

1. **Backend Setup:**
   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\Activate.ps1  # Windows
   pip install -r requirements.txt
   
   # Copy .env.example to .env and fill in:
   # - Azure OpenAI credentials (from your time-app-test)
   # - OpenWeather API key (sign up free at openweathermap.org)
   cp .env.example .env
   code .env  # Edit with your credentials
   ```

2. **Frontend Setup:**
   ```bash
   cd frontend
   npm install
   ```

## Running

1. **Start Backend:**
   ```bash
   cd backend
   venv\Scripts\Activate.ps1
   uvicorn main:app --port 8000
   ```

2. **Start Frontend (new terminal):**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Open App:**
   - Go to http://localhost:5173
   - Click "Get Recommendations"
   - View weekend snowboarding recommendations!

## API Keys Needed

- **Azure OpenAI**: Use credentials from time-app-test project
- **OpenWeather**: Free key from https://openweathermap.org/api
  - Sign up, get API key, add to .env

## Troubleshooting

- **Backend won't start**: Check .env has all required variables
- **Weather API 401**: Verify OpenWeather key is correct
- **No recommendations**: Check console for API errors
```

## Success Criteria

The app is complete when:
- ✅ Backend starts without errors on port 8000
- ✅ Frontend starts on port 5173
- ✅ User can click "Get Recommendations"
- ✅ System fetches weather, snow, transport data
- ✅ Recommendations display with scores
- ✅ AI summary explains choices
- ✅ UI is beautiful with ski/winter theme
- ✅ Error handling works gracefully

## Key Patterns to Follow

1. **Error Handling**: Every API call wrapped in try/except
2. **Parallel Requests**: Use `asyncio.gather()` for multiple resorts
3. **Caching**: Simple in-memory dict with TTL
4. **Logging**: Log all API calls and errors
5. **Validation**: Use Pydantic models everywhere
6. **UI**: Follow time-app-test styling (gradients, smooth animations)

## What to Tell the User

When complete, tell the user:

"✅ **Magic Pass Resort Picker is ready!**

I've built the complete application with:
- Backend API with weather, snow, and transport integration
- Intelligent recommendation engine with scoring
- Beautiful React frontend with ski theme
- Azure OpenAI for natural language explanations

**Next steps:**
1. Set up your environment variables in `backend/.env`
   - Copy Azure OpenAI credentials from your time-app-test
   - Get free OpenWeather API key from openweathermap.org
2. Install dependencies (see README.md)
3. Start backend: `uvicorn main:app --port 8000`
4. Start frontend: `npm run dev`
5. Open http://localhost:5173 and plan your weekend! 🎿

Check README.md for detailed setup and troubleshooting."

## Notes
- Be autonomous - implement everything without asking for confirmation on standard implementation decisions
- Follow the architecture exactly as specified
- Make the UI beautiful - this is a consumer-facing app
- Handle missing data gracefully (some resorts may not have snow data)
- Test each component as you build it
- Keep the user updated on major milestones

Let's build this! 🏔️
