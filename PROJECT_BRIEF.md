# Magic Pass Resort Picker - Project Brief

## Overview
A web application that recommends the optimal Magic Pass ski resort for weekend snowboarding trips from Geneva, based on weather forecasts, snow conditions, and public transport accessibility.

## Problem Statement
As a Magic Pass holder living in Geneva, Uri wants to optimize weekend ski trips by knowing which resort will have the best conditions each weekend. Currently, this requires manually checking multiple weather sites, snow reports, and train schedules across dozens of resorts.

## Solution
An intelligent web app that:
- Analyzes weather and snow forecasts for all Magic Pass resorts
- Considers public transport (train + PostBus) travel times from Geneva
- Uses Azure OpenAI to provide natural language recommendations
- Updates daily (Monday-Friday) with recommendations for the upcoming weekend
- Provides a beautiful, easy-to-use interface

## Target User
- Primary: Uri (lives in Geneva, Magic Pass holder, snowboarder, travels by public transport)
- Future: Other Swiss residents with Magic Pass (expandable to other starting locations)

## Key Value Proposition
**"Tell me where to go snowboarding this weekend based on the best conditions and easiest travel from Geneva"**

## Success Criteria
- Accurately fetches and analyzes data from weather, snow, and transport APIs
- Provides clear, actionable recommendations with reasoning
- Runs reliably as a local web application
- Can be checked daily during the work week (Mon-Fri) for weekend planning
- Beautiful, intuitive UI that makes decision-making easy

## Technical Foundation
Built on the proven time-app-test architecture:
- Backend: Python + FastAPI
- Frontend: React + Vite
- AI: Azure OpenAI (gpt-4.1-mini) for natural language generation
- APIs: MeteoSwiss, SLF (snow), SBB/PostBus (transport), Magic Pass resort data
- Deployment: Local first, with future cloud deployment option

## Scope
**Phase 1 (MVP):**
- All Magic Pass resorts included
- Geneva as starting location
- Weekend (Saturday/Sunday) recommendations
- Weather and snow data integration
- Public transport time estimates
- Natural language recommendations

**Future Enhancements:**
- Multiple starting locations
- User preferences (powder vs groomed, altitude preference, etc.)
- Historical accuracy tracking
- Mobile app version
- Real-time webcam integration
- Avalanche risk integration
