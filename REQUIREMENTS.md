# Magic Pass Resort Picker - Requirements

## Functional Requirements

### FR1: Resort Data Management
- **FR1.1**: System shall maintain a complete list of all Magic Pass resorts
- **FR1.2**: Each resort record shall include:
  - Name
  - Location (coordinates, canton, region)
  - Elevation (base and top)
  - Primary access point (nearest train station + PostBus connection)
  - Typical travel time from Geneva
  - Resort website URL
- **FR1.3**: Resort list shall be easily updateable if Magic Pass lineup changes

### FR2: Weather Data Integration
- **FR2.1**: System shall fetch weather forecasts for upcoming weekend (Saturday/Sunday)
- **FR2.2**: Weather data shall include:
  - Temperature (high/low)
  - Precipitation forecast
  - Fresh snowfall expected
  - Wind conditions
  - Cloud cover / visibility
- **FR2.3**: Data shall be fetched from MeteoSwiss or equivalent reliable source
- **FR2.4**: System shall handle API failures gracefully with cached/fallback data

### FR3: Snow Conditions Integration
- **FR3.1**: System shall fetch current snow conditions for each resort
- **FR3.2**: Snow data shall include:
  - Current snow depth at base and summit
  - Snow quality (fresh, packed, icy, etc.)
  - Recent snowfall (24h, 7 days)
- **FR3.3**: Data sources: SLF (Swiss Avalanche Institute), resort websites, or snow-forecast.com
- **FR3.4**: System shall indicate data freshness (last updated timestamp)

### FR4: Transport Information
- **FR4.1**: System shall calculate public transport journey time from Geneva to each resort
- **FR4.2**: Transport calculation shall include:
  - Train (SBB) from Geneva to nearest station
  - PostBus from station to resort (if applicable)
  - Total journey time
  - Typical departure times for Saturday morning
- **FR4.3**: System shall use SBB API or equivalent for real-time schedule data
- **FR4.4**: Journey times shall be estimated for Saturday morning departure (e.g., 7-9 AM)

### FR5: Recommendation Engine
- **FR5.1**: System shall score each resort based on:
  - Weather forecast quality (40% weight)
  - Snow conditions (40% weight)
  - Travel time (20% weight)
- **FR5.2**: System shall rank resorts from best to worst for the weekend
- **FR5.3**: System shall identify top 3-5 recommendations
- **FR5.4**: Scoring algorithm shall be transparent and adjustable

### FR6: AI-Powered Communication
- **FR6.1**: System shall use Azure OpenAI to generate natural language recommendations
- **FR6.2**: LLM responses shall include:
  - Top recommendations with clear reasoning
  - Weather and snow highlights
  - Any warnings or concerns
  - Alternative options if conditions are poor everywhere
- **FR6.3**: LLM shall maintain friendly, conversational tone
- **FR6.4**: Response shall be concise but informative (2-4 paragraphs)

### FR7: User Interface
- **FR7.1**: Home page shall show:
  - Current date and target weekend
  - Top 3 resort recommendations prominently
  - Quick summary of conditions
  - "Get Recommendations" button to trigger analysis
- **FR7.2**: Recommendations view shall display:
  - Resort cards with key details (weather, snow, travel time)
  - AI-generated explanation
  - Visual indicators (icons, colors) for conditions
  - Link to detailed view
- **FR7.3**: Detailed resort view shall show:
  - Complete weather forecast
  - Detailed snow report
  - Transport options with schedules
  - Map/location information
  - Link to resort website
- **FR7.4**: UI shall be responsive and work on desktop and tablet
- **FR7.5**: Design shall be visually appealing with winter/snow theme

### FR8: Daily Updates
- **FR8.1**: System shall be designed to be queried daily Monday-Friday
- **FR8.2**: Each query shall fetch fresh data from all APIs
- **FR8.3**: System shall cache data appropriately to avoid rate limits
- **FR8.4**: User shall see data freshness indicators

## Non-Functional Requirements

### NFR1: Performance
- **NFR1.1**: Initial page load shall complete in < 2 seconds
- **NFR1.2**: Recommendation generation shall complete in < 10 seconds
- **NFR1.3**: API calls shall be made in parallel where possible
- **NFR1.4**: System shall handle 10+ concurrent API requests efficiently

### NFR2: Reliability
- **NFR2.1**: System shall gracefully handle API failures with meaningful error messages
- **NFR2.2**: If one API fails, system shall still provide partial recommendations
- **NFR2.3**: Backend shall validate all external data before processing
- **NFR2.4**: System shall log errors for debugging

### NFR3: Maintainability
- **NFR3.1**: Code shall be well-structured with clear separation of concerns
- **NFR3.2**: Configuration shall be externalized in .env file
- **NFR3.3**: Resort data shall be in easily editable JSON/CSV format
- **NFR3.4**: API integrations shall be modular and swappable
- **NFR3.5**: Documentation shall be comprehensive

### NFR4: Security
- **NFR4.1**: All API keys shall be stored in .env file (not in code)
- **NFR4.2**: No sensitive data shall be exposed to frontend
- **NFR4.3**: CORS shall be properly configured
- **NFR4.4**: Input validation on all user inputs

### NFR5: Scalability (Future)
- **NFR5.1**: Architecture shall support adding new starting locations
- **NFR5.2**: Design shall allow for user accounts and preferences (future)
- **NFR5.3**: Database layer shall be easy to add when needed

## Data Requirements

### DR1: Magic Pass Resorts List
Minimum required resorts to include (complete Magic Pass lineup):
- **Valais**: Saas-Fee, Grächen, Belalp, Aletsch Arena, Bellwald, Hoch-Ybrig
- **Graubünden**: Davos Klosters, Arosa Lenzerheide, Savognin, Brigels
- **Bernese Oberland**: Adelboden-Lenk, Meiringen-Hasliberg, Grindelwald-First
- **Central Switzerland**: Melchsee-Frutt, Klewenalp, Sattel-Hochstuckli
- **Eastern Switzerland**: Flumserberg, Pizol, Wildhaus, Toggenburg
- **Jura/West**: Les Pléiades, Bugnenets-Savagnières

(This list should be verified against current Magic Pass website)

### DR2: API Endpoints Required
- **Weather**: MeteoSwiss API or OpenWeather API
- **Snow**: SLF API, snow-forecast.com, or individual resort APIs
- **Transport**: SBB/CFF API (transport.opendata.ch)
- **LLM**: Azure OpenAI API (already configured)

### DR3: Data Refresh Strategy
- Weather data: Refresh every 6 hours
- Snow data: Refresh every 12 hours
- Transport data: Real-time or cached with 24h refresh
- Cache all data locally to avoid excessive API calls

## Constraints

### C1: Technology Constraints
- Must use existing time-app-test architecture
- Must use Azure OpenAI (gpt-4.1-mini) as already configured
- Must run locally on Windows machine initially
- Must use free or low-cost APIs where possible

### C2: Data Constraints
- Some resorts may not have real-time snow data available
- Transport schedules may vary (weekend vs weekday)
- Weather forecasts are probabilistic and may change
- API rate limits must be respected

### C3: Time Constraints
- MVP should be buildable by Claude Code CLI in one session
- Focus on core functionality first, enhancements later

## Success Metrics

### Quantitative
- Successfully fetches data for 90%+ of resorts
- Generates recommendations in < 10 seconds
- API success rate > 95%
- Zero crashes during normal operation

### Qualitative
- Recommendations are actionable and make sense
- UI is pleasant to use and easy to understand
- User trusts the recommendations for trip planning
- System provides value over manual checking

## Open Questions / Decisions Needed
1. Which weather API to use? (MeteoSwiss vs OpenWeather vs others)
2. How to handle resorts with missing data? (exclude, estimate, or flag?)
3. Should we show detailed scores/weights or just rankings?
4. How to handle avalanche risk information? (integrate now or later?)
5. Should weekend include Friday afternoon/evening departures?
