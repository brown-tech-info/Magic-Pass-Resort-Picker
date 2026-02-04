# Magic Pass Resort Picker

A web application that recommends the best Magic Pass ski resorts for weekend snowboarding trips from Geneva, based on weather forecasts, snow conditions, and public transport accessibility.

> **Note**: This project was built entirely with Claude Code. See [note from uri.md](note%20from%20uri.md) for more details and a quick-start guide.

## Features

- **Weather Analysis**: Fetches forecasts from OpenWeather API for all 29 Magic Pass resorts
- **Snow Conditions**: Scrapes snow data from snow-forecast.com
- **Transport Times**: Calculates public transport routes from Geneva using Swiss OpenData API
- **Smart Scoring**: Weighted algorithm (40% weather, 40% snow, 20% transport)
- **AI Recommendations**: Natural language summaries powered by Azure OpenAI
- **Beautiful UI**: Modern React frontend with winter theme

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Azure OpenAI credentials (from Azure Portal)
- OpenWeather API key (free tier)

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
code .env
```

### 2. Configure Environment Variables

Edit `backend/.env` with your credentials:

```bash
# Azure OpenAI (from Azure Portal)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/openai/v1/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4.1-mini
AZURE_OPENAI_API_VERSION=2024-05-01-preview

# Weather API (sign up free at openweathermap.org)
OPENWEATHER_API_KEY=your-key-here

# App Settings (defaults are fine)
START_LOCATION=Geneva
CORS_ORIGINS=http://localhost:5173
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

## Running the Application

**Quick Start with Claude Code**: If you have Claude Code installed, just ask it to "set up and run the backend and frontend" and it will handle everything for you!

### Start Backend

```bash
cd backend
venv\Scripts\Activate.ps1
uvicorn main:app --port 8000
```

The backend API will be available at http://localhost:8000

### Start Frontend (new terminal)

```bash
cd frontend
npm run dev
```

The frontend will be available at http://localhost:5173

### Use the App

1. Open http://localhost:5173 in your browser
2. Click "Get Weekend Recommendations"
3. View AI-powered recommendations with weather, snow, and transport data
4. Click on resort websites for more details

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/health` | GET | Detailed service status |
| `/api/resorts` | GET | List all Magic Pass resorts |
| `/api/resorts/{id}` | GET | Get specific resort |
| `/api/recommendations` | POST | Generate weekend recommendations |
| `/api/recommendations/{id}` | GET | Get detailed resort recommendation |
| `/api/weather/{id}` | GET | Get weather for resort |
| `/api/transport` | GET | Get transport options |

## API Keys Needed

### Azure OpenAI
1. Create an Azure OpenAI resource in the Azure Portal
2. Deploy a model (e.g., `gpt-4.1-mini`)
3. Copy your endpoint and API key from the Keys and Endpoint section
4. Add to `backend/.env`

### OpenWeather API
1. Sign up at https://openweathermap.org/api (free)
2. Go to API keys section in your account
3. Generate a new API key
4. Add to `backend/.env` as `OPENWEATHER_API_KEY`

Note: Free tier allows 1000 calls/day, which is sufficient for this app.

## Project Structure

```
magic-pass-picker/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── .env.example         # Environment template
│   ├── models/              # Pydantic models
│   │   ├── resort.py
│   │   ├── weather.py
│   │   ├── snow.py
│   │   ├── transport.py
│   │   └── recommendation.py
│   ├── services/            # API integrations
│   │   ├── weather_service.py
│   │   ├── snow_service.py
│   │   ├── transport_service.py
│   │   ├── resort_service.py
│   │   └── llm_service.py
│   ├── core/                # Business logic
│   │   ├── scoring.py
│   │   └── recommender.py
│   ├── data/
│   │   └── resorts.json     # Resort database
│   └── utils/
│       ├── cache.py         # Caching utilities
│       └── progress.py      # Progress tracking
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main component
│   │   ├── main.jsx         # Entry point
│   │   ├── components/      # UI components
│   │   │   ├── Header.jsx
│   │   │   ├── RecommendationCard.jsx
│   │   │   ├── WeatherDisplay.jsx
│   │   │   ├── SnowDisplay.jsx
│   │   │   ├── TransportDisplay.jsx
│   │   │   ├── AISummary.jsx
│   │   │   └── LoadingSpinner.jsx
│   │   ├── hooks/
│   │   │   └── useSSERecommendations.js
│   │   └── services/
│   │       └── api.js       # API client
│   └── package.json
├── note from uri.md         # About this project
└── README.md
```

## Scoring Algorithm

Resorts are scored on a 0-10 scale:

**Weather (40% weight)**
- Temperature: Ideal range -5 to -10°C
- Snowfall: More fresh snow = higher score
- Cloud cover: Clear skies preferred
- Wind: Low wind speeds preferred

**Snow (40% weight)**
- Base depth: 150cm+ = excellent
- Fresh snow: Recent snowfall boosts score
- Snow quality: Powder > Packed > Icy

**Transport (20% weight)**
- Duration: <2 hours = excellent
- Changes: Direct connections preferred

## Troubleshooting

### Backend won't start
- Ensure all environment variables are set in `.env`
- Check Python virtual environment is activated
- Verify all dependencies are installed

### Weather API 401 Error
- Verify your OpenWeather API key is correct
- New API keys may take a few hours to activate

### No snow data for some resorts
- This is expected - not all resorts have data on snow-forecast.com
- The app will still work using weather and transport data

### Recommendations take too long
- First request may be slow while caching
- Subsequent requests use cached data (6-24 hour TTL)

### Frontend can't connect to backend
- Ensure backend is running on port 8000
- Check CORS_ORIGINS in .env includes `http://localhost:5173`

## Included Resorts

The app includes 29 Magic Pass resorts across Switzerland:

- **Valais**: Saas-Fee, Grachen, Belalp, Aletsch Arena, Bellwald, Nendaz, Crans-Montana
- **Graubunden**: Davos Klosters, Arosa Lenzerheide, Savognin, Brigels, Disentis, LAAX
- **Bernese Oberland**: Grindelwald-First, Adelboden-Lenk, Meiringen-Hasliberg
- **Central Switzerland**: Melchsee-Frutt, Klewenalp, Sattel-Hochstuckli, Engelberg-Titlis, Andermatt-Sedrun, Sorenberg, Hoch-Ybrig
- **Eastern Switzerland**: Flumserberg, Pizol, Wildhaus, Toggenburg
- **Vaud/Jura**: Les Pleiades, Bugnenets-Savagnieres

## Data Sources

- **Weather**: OpenWeather API (openweathermap.org)
- **Snow Conditions**: snow-forecast.com
- **Transport**: Swiss OpenData transport.opendata.ch
- **AI Summaries**: Azure OpenAI (GPT-4.1-mini)

## License

MIT
