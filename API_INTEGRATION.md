# Magic Pass Resort Picker - API Integration Guide

This document provides detailed information about integrating with external APIs needed for the Magic Pass Resort Picker.

## Overview of Required APIs

1. **Weather API**: Weather forecasts for Swiss mountain regions
2. **Snow Conditions API**: Current snow depth and conditions
3. **Transport API**: Public transport schedules and connections
4. **Azure OpenAI API**: Natural language generation (already configured)

## 1. Weather API

### Recommended: OpenWeather API

**Why OpenWeather:**
- Free tier: 1000 calls/day (sufficient for MVP)
- Covers Swiss locations with coordinates
- Well-documented
- Reliable data quality
- Easy integration

**Getting Started:**
1. Sign up at: https://openweathermap.org/api
2. Get free API key from your account dashboard
3. Choose "One Call API 3.0" for forecast data

**API Endpoint:**
```
https://api.openweathermap.org/data/3.0/onecall
```

**Request Parameters:**
- `lat`: Latitude (e.g., 46.1097 for Saas-Fee)
- `lon`: Longitude (e.g., 7.9283 for Saas-Fee)
- `appid`: Your API key
- `units`: metric
- `exclude`: hourly,minutely (only need daily forecast)

**Example Request:**
```python
import httpx

async def get_weather(lat: float, lon: float, api_key: str):
    url = "https://api.openweathermap.org/data/3.0/onecall"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric",
        "exclude": "minutely,hourly,alerts"
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, timeout=10.0)
        response.raise_for_status()
        return response.json()
```

**Response Structure:**
```json
{
  "lat": 46.1097,
  "lon": 7.9283,
  "timezone": "Europe/Zurich",
  "daily": [
    {
      "dt": 1642838400,
      "temp": {
        "day": -5.2,
        "min": -10.5,
        "max": -2.1
      },
      "weather": [
        {
          "id": 600,
          "main": "Snow",
          "description": "light snow"
        }
      ],
      "snow": 2.5,
      "wind_speed": 15.2,
      "clouds": 75
    }
  ]
}
```

**Mapping to Our Model:**
```python
def parse_weather_data(data: dict, target_date: date) -> WeatherForecast:
    # Find the daily forecast for target_date
    target_timestamp = int(target_date.timestamp())
    
    for day in data['daily']:
        day_timestamp = day['dt']
        day_date = datetime.fromtimestamp(day_timestamp).date()
        
        if day_date == target_date:
            return WeatherForecast(
                date=target_date,
                temperature_min=day['temp']['min'],
                temperature_max=day['temp']['max'],
                precipitation_mm=day.get('rain', 0) + day.get('snow', 0),
                snowfall_cm=day.get('snow', 0) / 10,  # mm to cm
                wind_speed=day['wind_speed'] * 3.6,  # m/s to km/h
                wind_direction=degrees_to_direction(day.get('wind_deg', 0)),
                cloud_cover=day['clouds'],
                visibility="Good" if day['clouds'] < 30 else "Moderate" if day['clouds'] < 70 else "Poor",
                conditions=day['weather'][0]['description']
            )
```

**Rate Limiting:**
- Free tier: 1000 calls/day
- With 30 resorts × 2 days (Sat/Sun) = 60 calls per recommendation request
- Can make ~16 recommendation requests per day
- **Solution**: Cache weather data for 6 hours

**Cost:**
- Free tier sufficient for MVP
- Upgrade to paid if needed ($40/month for 2000 calls/day)

**Alternative: MeteoSwiss API**

MeteoSwiss has official APIs but:
- More complex authentication
- Limited documentation
- May require account approval

Only use if OpenWeather is insufficient.

## 2. Snow Conditions API

### Challenge: No Single Comprehensive API

Unlike weather, snow conditions don't have one free API covering all resorts.

### Option A: Snow-Forecast.com (Recommended)

**Approach**: Web scraping (no official API)

**URL Pattern:**
```
https://www.snow-forecast.com/resorts/{resort-slug}/6day/mid
```

**Example:**
```
https://www.snow-forecast.com/resorts/Saas-Fee/6day/mid
```

**Data Available:**
- Current snow depth (base and top)
- Recent snowfall
- Snow forecast

**Implementation:**
```python
import httpx
from bs4 import BeautifulSoup

async def scrape_snow_forecast(resort_slug: str) -> dict:
    url = f"https://www.snow-forecast.com/resorts/{resort_slug}/6day/mid"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
        response.raise_for_status()
        
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract snow depth from page
    # This requires inspecting the HTML structure
    # snow-forecast.com has specific CSS classes for snow data
    
    return {
        "snow_base": extract_base_depth(soup),
        "snow_summit": extract_summit_depth(soup),
        "new_snow_24h": extract_new_snow(soup)
    }
```

**Pros:**
- Free
- Covers most major resorts
- Reliable data

**Cons:**
- Web scraping is fragile (page structure may change)
- Need to maintain resort slug mapping
- No official support

**Resort Slug Mapping:**
Create a mapping file:
```json
{
  "saas-fee": "Saas-Fee",
  "davos": "Davos-Klosters",
  "arosa": "Arosa"
}
```

### Option B: Individual Resort Websites

**Approach**: Each resort has snow report on website

**Pros:**
- Official data
- Most up-to-date

**Cons:**
- Each resort has different format
- Would need 30+ scrapers
- High maintenance

**Recommendation**: Only use as fallback for major resorts

### Option C: SLF (Swiss Avalanche Institute)

**URL**: https://www.slf.ch/

**Status**: 
- No public API for snow depth
- Provides avalanche bulletins
- May have partner access (requires inquiry)

**Future Enhancement**: Could add avalanche risk data

### Fallback Strategy for Snow Data

If snow data unavailable for a resort:
1. Set snow fields to `None`
2. Rely more heavily on weather forecast
3. Display "Snow data unavailable" in UI
4. Don't exclude resort from recommendations

```python
async def get_snow_conditions(resort_id: str) -> Optional[SnowConditions]:
    try:
        return await fetch_snow_data(resort_id)
    except Exception as e:
        logger.warning(f"Could not fetch snow data for {resort_id}: {e}")
        return None  # Gracefully handle missing data
```

## 3. Transport API

### Recommended: Swiss OpenData Transport API

**Why This API:**
- Free and open
- No API key required
- Official Swiss public transport data
- Covers SBB (trains) and PostBus
- Excellent documentation
- JSON responses

**Base URL:**
```
http://transport.opendata.ch/v1/
```

**Key Endpoint: Connections**
```
GET http://transport.opendata.ch/v1/connections
```

**Parameters:**
- `from`: Starting location (e.g., "Geneva" or "Genève")
- `to`: Destination (e.g., "Brig" or "Saas-Fee")
- `date`: Date in YYYY-MM-DD format
- `time`: Time in HH:MM format (24-hour)
- `limit`: Number of connections to return (default 4)

**Example Request:**
```python
async def get_connections(from_location: str, to_location: str, 
                         date: str, time: str = "08:00") -> dict:
    url = "http://transport.opendata.ch/v1/connections"
    params = {
        "from": from_location,
        "to": to_location,
        "date": date,
        "time": time,
        "limit": 3
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, timeout=15.0)
        response.raise_for_status()
        return response.json()
```

**Example Response:**
```json
{
  "connections": [
    {
      "from": {
        "station": {
          "name": "Genève"
        },
        "departure": "2026-01-18T08:06:00+0100"
      },
      "to": {
        "station": {
          "name": "Brig"
        },
        "arrival": "2026-01-18T10:51:00+0100"
      },
      "duration": "02:45:00",
      "transfers": 1,
      "sections": [
        {
          "journey": {
            "name": "IC 1",
            "category": "IC"
          },
          "departure": {
            "station": {
              "name": "Genève"
            },
            "time": "2026-01-18T08:06:00+0100"
          },
          "arrival": {
            "station": {
              "name": "Lausanne"
            },
            "time": "2026-01-18T08:45:00+0100"
          }
        },
        {
          "journey": {
            "name": "IC 8",
            "category": "IC"
          },
          "departure": {
            "station": {
              "name": "Lausanne"
            },
            "time": "2026-01-18T09:06:00+0100"
          },
          "arrival": {
            "station": {
              "name": "Brig"
            },
            "time": "2026-01-18T10:51:00+0100"
          }
        }
      ]
    }
  ]
}
```

**Parsing to Our Model:**
```python
def parse_connection(connection: dict) -> Journey:
    departure_time = datetime.fromisoformat(
        connection['from']['departure'].replace('+0100', '+01:00')
    )
    arrival_time = datetime.fromisoformat(
        connection['to']['arrival'].replace('+0100', '+01:00')
    )
    
    # Parse duration string "02:45:00" to minutes
    duration_parts = connection['duration'].split(':')
    duration_minutes = int(duration_parts[0]) * 60 + int(duration_parts[1])
    
    segments = []
    for section in connection.get('sections', []):
        if section.get('journey'):  # Actual transport (not walking)
            segments.append(JourneySegment(
                type="train" if section['journey']['category'] in ['IC', 'IR', 'RE'] else "bus",
                from_station=section['departure']['station']['name'],
                to_station=section['arrival']['station']['name'],
                departure=datetime.fromisoformat(section['departure']['time'].replace('+0100', '+01:00')),
                arrival=datetime.fromisoformat(section['arrival']['time'].replace('+0100', '+01:00')),
                line=section['journey']['name']
            ))
    
    return Journey(
        departure_time=departure_time,
        arrival_time=arrival_time,
        duration_minutes=duration_minutes,
        changes=connection.get('transfers', 0),
        segments=segments
    )
```

**Handling PostBus Connections:**

For resorts not directly accessible by train (e.g., Saas-Fee):
1. Get connection to nearest train station (e.g., Brig)
2. API automatically includes PostBus connection if needed
3. PostBus appears as segment with category "B" or "BUS"

**Special Cases:**

Some resorts may not be in the system:
```python
async def get_resort_journey(from_location: str, resort: Resort) -> Optional[Journey]:
    try:
        # Try direct to resort name
        return await get_connections(from_location, resort.name, date, time)
    except:
        # Try to nearest station
        if resort.access.nearest_station:
            try:
                return await get_connections(
                    from_location, 
                    resort.access.nearest_station, 
                    date, 
                    time
                )
            except:
                logger.warning(f"No route found for {resort.name}")
                return None
```

**Rate Limiting:**
- No official rate limit documented
- Be respectful: don't hammer the API
- Cache results for 24 hours
- Make parallel requests but limit concurrency (5-10 max)

## 4. Azure OpenAI API

**Status**: Already configured from time-app-test ✅

**Configuration:**
```python
from openai import OpenAI

client = OpenAI(
    base_url=settings.azure_openai_endpoint,
    api_key=settings.azure_openai_api_key,
)
```

**Usage for Recommendations:**
```python
async def generate_summary(recommendations: List[Recommendation]) -> str:
    # Build context from recommendations
    context = format_recommendations_for_llm(recommendations)
    
    prompt = f"""You are a helpful ski trip planning assistant. Based on the following 
weekend forecast for Magic Pass resorts accessible from Geneva, provide a brief 
recommendation (2-3 paragraphs) on where to go snowboarding.

{context}

Provide a friendly, conversational recommendation with clear reasoning. Focus on the 
best options and explain why they're good choices for this weekend."""

    response = client.chat.completions.create(
        model=settings.azure_openai_deployment_name,
        messages=[
            {"role": "system", "content": "You are a helpful ski trip planning assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0.7
    )
    
    return response.choices[0].message.content
```

## API Integration Best Practices

### 1. Error Handling

Always wrap API calls in try-except:
```python
async def fetch_with_retry(url: str, max_retries: int = 3) -> dict:
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### 2. Parallel Requests

Use asyncio to make concurrent API calls:
```python
async def get_all_weather_forecasts(resorts: List[Resort]) -> Dict[str, WeatherForecast]:
    tasks = [
        get_weather_forecast(resort.coordinates.latitude, resort.coordinates.longitude)
        for resort in resorts
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    forecasts = {}
    for resort, result in zip(resorts, results):
        if isinstance(result, Exception):
            logger.error(f"Weather fetch failed for {resort.name}: {result}")
            forecasts[resort.id] = None
        else:
            forecasts[resort.id] = result
    
    return forecasts
```

### 3. Caching

Implement caching to reduce API calls:
```python
from datetime import datetime, timedelta

class SimpleCache:
    def __init__(self):
        self._cache = {}
    
    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            value, expiry = self._cache[key]
            if datetime.now() < expiry:
                return value
            del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl_hours: int):
        expiry = datetime.now() + timedelta(hours=ttl_hours)
        self._cache[key] = (value, expiry)
```

### 4. Timeout Configuration

Set appropriate timeouts:
```python
# Weather API: Usually fast
weather_timeout = 10.0

# Transport API: May be slower (routing calculation)
transport_timeout = 15.0

# LLM API: Can be slow
llm_timeout = 30.0
```

### 5. Logging

Log all API calls for debugging:
```python
import logging

logger = logging.getLogger(__name__)

async def make_api_call(url: str, params: dict):
    logger.info(f"API Request: {url} with params {params}")
    try:
        response = await client.get(url, params=params)
        logger.info(f"API Response: {response.status_code}")
        return response.json()
    except Exception as e:
        logger.error(f"API Error: {url} - {e}")
        raise
```

## Environment Variables

Add these to `.env`:
```bash
# Weather API
OPENWEATHER_API_KEY=your_key_here

# Snow API (if using paid service)
SNOW_API_KEY=optional

# Transport API (no key needed for opendata.ch)
# TRANSPORT_API_KEY=not_needed

# Azure OpenAI (already configured)
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_API_KEY=xxx
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4.1-mini
AZURE_OPENAI_API_VERSION=2024-05-01-preview

# Cache settings
CACHE_ENABLED=true
WEATHER_CACHE_HOURS=6
SNOW_CACHE_HOURS=12
TRANSPORT_CACHE_HOURS=24
```

## Testing APIs Independently

Before integrating, test each API separately:

### Test Weather API:
```bash
curl "https://api.openweathermap.org/data/3.0/onecall?lat=46.1097&lon=7.9283&appid=YOUR_KEY&units=metric&exclude=minutely,hourly"
```

### Test Transport API:
```bash
curl "http://transport.opendata.ch/v1/connections?from=Geneva&to=Brig&date=2026-01-18&time=08:00"
```

### Test Snow-Forecast (in browser):
```
https://www.snow-forecast.com/resorts/Saas-Fee/6day/mid
```

## API Quotas and Costs Summary

| API | Free Tier | Cost | Rate Limit |
|-----|-----------|------|------------|
| OpenWeather | 1000 calls/day | Free / $40/month | 60 calls/min |
| Snow-Forecast | Unlimited | Free (scraping) | Be respectful |
| Swiss Transport | Unlimited | Free | No limit |
| Azure OpenAI | Pay per token | ~$0.01 per call | As configured |

**Estimated Daily Usage:**
- 10 recommendation requests/day
- 30 resorts × 2 days = 60 weather calls (cached 6h)
- 30 resorts = 30 snow calls (cached 12h)
- 30 resorts = 30 transport calls (cached 24h)
- 10 LLM calls

**Total Cost**: ~$1-2/day with moderate usage

## Troubleshooting

### Weather API Issues
- **401 Unauthorized**: Invalid API key
- **404 Not Found**: Wrong endpoint or API version
- **429 Too Many Requests**: Rate limit exceeded, implement backoff

### Snow Data Issues
- **No data for resort**: Normal, fall back to weather-only recommendation
- **Scraping fails**: HTML structure changed, update parsing logic
- **Slow response**: Implement timeout, use cached data

### Transport API Issues
- **No connection found**: Resort may not be in system, use nearest station
- **Timeout**: API can be slow, increase timeout to 15-20s
- **Wrong location**: Check spelling, try German names (e.g., "Genf" vs "Geneva")

### LLM API Issues
- **Connection error**: Verify Azure OpenAI endpoint from time-app-test
- **Authentication failed**: Check API key is correct
- **Slow response**: Normal, LLM can take 5-10 seconds

This API integration guide provides all the details needed to successfully integrate with the required external services for the Magic Pass Resort Picker.
