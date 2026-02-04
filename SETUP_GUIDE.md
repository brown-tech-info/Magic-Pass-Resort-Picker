# Magic Pass Resort Picker - Initial Setup Guide

This guide walks through the very first steps to get started with building the Magic Pass Resort Picker using Claude Code CLI.

## Prerequisites Checklist

Before starting, ensure you have:

- ✅ Windows machine (Windows 10/11)
- ✅ Python 3.11 or higher installed
  - Check: `python --version`
- ✅ Node.js 18 or higher installed
  - Check: `node --version`
- ✅ npm installed (comes with Node.js)
  - Check: `npm --version`
- ✅ VS Code or preferred code editor
- ✅ Claude Code CLI installed
  - Check: `claude --version`
- ✅ Azure OpenAI credentials from time-app-test project
  - Endpoint URL
  - API Key
  - Deployment name
- ✅ Git installed (optional but recommended)

## Step 1: Create Project Directory

Create a clean workspace for the project:

```powershell
# Navigate to your development folder
cd "C:\Users\YourUsername\Dev Code - Claude"

# Create project directory
mkdir magic-pass-picker
cd magic-pass-picker
```

## Step 2: Copy Time-App-Test Foundation

Since we're using time-app-test as our architectural foundation, let's start by copying its structure:

```powershell
# Option A: If you have time-app-test in same parent directory
cp -r ../time-app-test/backend ./backend
cp -r ../time-app-test/frontend ./frontend
cp ../time-app-test/.gitignore ./.gitignore

# Option B: Manual creation (if starting fresh)
mkdir backend
mkdir frontend
```

## Step 3: Initialize Backend Structure

Create the backend directory structure:

```powershell
cd backend

# Create directories
mkdir models
mkdir services
mkdir core
mkdir data
mkdir utils

# Create __init__.py files
New-Item models/__init__.py
New-Item services/__init__.py
New-Item core/__init__.py
New-Item utils/__init__.py

cd ..
```

## Step 4: Initialize Frontend Structure

Create the frontend directory structure:

```powershell
cd frontend

# Create directories
mkdir src/components
mkdir src/services
mkdir src/utils

cd ..
```

## Step 5: Copy Documentation Files

Copy all the documentation files you received:

```powershell
# Place these files in the root of magic-pass-picker/
# - PROJECT_BRIEF.md
# - REQUIREMENTS.md
# - ARCHITECTURE.md
# - IMPLEMENTATION_PLAN.md
# - API_INTEGRATION.md
# - SETUP_GUIDE.md (this file)
```

## Step 6: Set Up Backend Environment

### Create Python Virtual Environment

```powershell
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip
```

### Create requirements.txt

Create `backend/requirements.txt` with these dependencies:

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-dotenv==1.0.0
httpx==0.27.2
openai==1.54.3
pydantic==2.5.3
pydantic-settings==2.1.0
beautifulsoup4==4.12.3
```

### Install Dependencies

```powershell
# Make sure venv is activated (you should see (venv) in prompt)
pip install -r requirements.txt
```

## Step 7: Set Up Environment Variables

### Create .env.example

Create `backend/.env.example`:

```bash
# Azure OpenAI Configuration (from time-app-test)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/openai/v1/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4.1-mini
AZURE_OPENAI_API_VERSION=2024-05-01-preview

# Weather API
OPENWEATHER_API_KEY=your-openweather-key-here

# Application Settings
START_LOCATION=Geneva
CORS_ORIGINS=http://localhost:5173
LOG_LEVEL=INFO

# Cache Settings
CACHE_ENABLED=true
WEATHER_CACHE_HOURS=6
SNOW_CACHE_HOURS=12
TRANSPORT_CACHE_HOURS=24
```

### Create Your Actual .env

```powershell
# Copy template
cp .env.example .env

# Edit .env with your actual credentials
code .env
```

**Important**: Copy your Azure OpenAI credentials from your time-app-test `.env` file!

## Step 8: Get OpenWeather API Key

You'll need a free OpenWeather API key:

1. Go to: https://openweathermap.org/api
2. Click "Sign Up" (if you don't have an account)
3. Sign in to your account
4. Go to "API keys" section
5. Copy your API key or generate a new one
6. Add it to your `.env` file:
   ```
   OPENWEATHER_API_KEY=your_actual_key_here
   ```

**Note**: The free tier allows 1000 API calls per day, which is plenty for development.

## Step 9: Initialize Frontend

```powershell
cd ../frontend

# Initialize npm (if starting from scratch)
# npm init -y

# Or copy package.json from time-app-test
```

### Create/Update package.json

Create `frontend/package.json`:

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

### Install Frontend Dependencies

```powershell
npm install
```

## Step 10: Create Initial Backend Files

### Create config.py

Create `backend/config.py`:

```python
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Azure OpenAI settings
    azure_openai_endpoint: str
    azure_openai_api_key: str
    azure_openai_deployment_name: str
    azure_openai_api_version: str = "2024-05-01-preview"
    
    # Weather API settings
    openweather_api_key: str
    
    # Application settings
    start_location: str = "Geneva"
    cors_origins: list[str] = ["http://localhost:5173"]
    log_level: str = "INFO"
    
    # Cache settings
    cache_enabled: bool = True
    weather_cache_hours: int = 6
    snow_cache_hours: int = 12
    transport_cache_hours: int = 24
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

### Create Basic main.py

Create `backend/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import get_settings

app = FastAPI(title="Magic Pass Picker API")
settings = get_settings()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok", 
        "message": "Magic Pass Picker API",
        "version": "0.1.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "api": "ok",
        "azure_openai": "not_tested_yet",
        "weather_api": "not_tested_yet",
        "transport_api": "ok"  # No auth needed
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

## Step 11: Test Backend Setup

```powershell
# Make sure you're in backend directory with venv activated
cd backend
.\venv\Scripts\Activate.ps1

# Start the server
uvicorn main:app --port 8000

# You should see:
# INFO:     Started server process
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://127.0.0.1:8000
```

Open browser to `http://localhost:8000` - you should see:
```json
{
  "status": "ok",
  "message": "Magic Pass Picker API",
  "version": "0.1.0"
}
```

Test health endpoint: `http://localhost:8000/health`

If both work, your backend is set up correctly! ✅

Press `Ctrl+C` to stop the server.

## Step 12: Create Initial Frontend Files

### Create vite.config.js

Create `frontend/vite.config.js`:

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
```

### Create index.html

Create `frontend/index.html`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Magic Pass Resort Picker</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

### Create Basic React App

Create `frontend/src/main.jsx`:

```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

Create `frontend/src/App.jsx`:

```jsx
import { useState } from 'react'

function App() {
  return (
    <div className="container">
      <h1>⛷️ Magic Pass Resort Picker</h1>
      <p>Finding the best snowboarding conditions for your weekend...</p>
      <button className="button">Get Recommendations</button>
    </div>
  )
}

export default App
```

Create `frontend/src/index.css`:

```css
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

#root {
  width: 100%;
  max-width: 800px;
  padding: 2rem;
}

.container {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 3rem;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

h1 {
  color: #667eea;
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

p {
  color: #666;
  font-size: 1.1rem;
  margin-bottom: 2rem;
}

.button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 1rem 3rem;
  font-size: 1.2rem;
  font-weight: 600;
  border-radius: 50px;
  cursor: pointer;
  transition: transform 0.2s;
}

.button:hover {
  transform: translateY(-2px);
}
```

## Step 13: Test Frontend Setup

```powershell
# From frontend directory
npm run dev

# You should see:
#   VITE v5.0.8  ready in XXX ms
#   ➜  Local:   http://localhost:5173/
```

Open browser to `http://localhost:5173` - you should see a beautiful purple gradient page with "Magic Pass Resort Picker" title!

If it works, your frontend is set up correctly! ✅

Press `Ctrl+C` to stop the dev server.

## Step 14: Initialize Git (Optional but Recommended)

```powershell
# From project root
git init

# Create .gitignore (if not copied from time-app-test)
```

Ensure `.gitignore` includes:
```
# Python
__pycache__/
*.py[cod]
venv/
.env

# Node
node_modules/
dist/

# IDE
.vscode/
.idea/
```

```powershell
# Initial commit
git add .
git commit -m "Initial project setup"
```

## Step 15: Prepare for Claude Code CLI

Now you're ready to use Claude Code CLI to build the actual application!

### Create a Task File

Create `CLAUDE_CODE_INSTRUCTIONS.md` in project root:

```markdown
# Instructions for Claude Code CLI

Hello Claude Code CLI! Please help me build the Magic Pass Resort Picker application.

## What to Build
An intelligent web app that recommends the best Magic Pass ski resorts for weekend 
snowboarding trips from Geneva, based on weather, snow conditions, and public transport.

## Key Documents
Please read these documents IN ORDER before starting:
1. PROJECT_BRIEF.md - Understand the project goal
2. REQUIREMENTS.md - Know what features are needed
3. ARCHITECTURE.md - Understand the system design
4. IMPLEMENTATION_PLAN.md - Follow the step-by-step build plan
5. API_INTEGRATION.md - Details on external APIs

## Current Status
✅ Project structure created
✅ Backend skeleton ready (config.py, main.py)
✅ Frontend skeleton ready (basic React app)
✅ Dependencies installed
✅ Environment variables configured

## What I Need You to Build
Please follow IMPLEMENTATION_PLAN.md starting from Phase 1, Step 2 (Create Data Models).

Focus on:
1. Creating all the data models
2. Building the resort database (resorts.json)
3. Implementing all service layers (weather, snow, transport, LLM)
4. Building the recommendation engine
5. Creating the API endpoints
6. Building the React frontend components
7. Making it all work together

## Important Notes
- Reuse Azure OpenAI configuration from config.py (already set up)
- Use OpenWeather API for weather (key in .env)
- Use transport.opendata.ch for transport (no key needed)
- Handle missing snow data gracefully
- Make the UI beautiful with ski/snow theme

## Testing
After implementation, I should be able to:
1. Start backend: `uvicorn main:app --port 8000`
2. Start frontend: `npm run dev`
3. Open http://localhost:5173
4. Click "Get Recommendations"
5. See beautiful recommendations with AI explanation

Let's build something awesome! 🎿
```

## Step 16: Running Claude Code CLI

Now you can run Claude Code CLI:

```powershell
# From project root directory
claude

# Or directly with instructions
claude --file CLAUDE_CODE_INSTRUCTIONS.md
```

Claude Code CLI will read all the documentation and start building the application step by step!

## Troubleshooting Initial Setup

### Python Virtual Environment Issues

**Problem**: `.\venv\Scripts\Activate.ps1` gives execution policy error

**Solution**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Port Already in Use

**Problem**: Port 8000 or 5173 already in use

**Solution**:
```powershell
# Find process using port
netstat -ano | findstr :8000

# Kill the process
taskkill /PID <process_id> /F

# Or use different port
uvicorn main:app --port 8001
```

### Missing Azure OpenAI Credentials

**Problem**: Backend fails to start with authentication error

**Solution**: Copy credentials from time-app-test `.env` file:
- AZURE_OPENAI_ENDPOINT
- AZURE_OPENAI_API_KEY
- AZURE_OPENAI_DEPLOYMENT_NAME

### OpenWeather API Key Not Working

**Problem**: Weather API returns 401

**Solution**:
1. Verify key is active in OpenWeather dashboard
2. Check you're using the correct API endpoint
3. Free tier keys may take a few minutes to activate after creation

## Next Steps

Once initial setup is complete:

1. ✅ **Phase 1 Complete**: Project structure ready
2. 🔨 **Phase 2**: Let Claude Code build the services (weather, snow, transport)
3. 🔨 **Phase 3**: Let Claude Code build the recommendation engine
4. 🔨 **Phase 4**: Let Claude Code create API endpoints
5. 🔨 **Phase 5**: Let Claude Code build the frontend
6. 🎉 **Phase 6**: Test and enjoy!

## Summary

You should now have:
- ✅ Project directory created
- ✅ Backend structure with venv
- ✅ Frontend structure with npm
- ✅ All dependencies installed
- ✅ Environment variables configured
- ✅ Basic backend running (test at http://localhost:8000)
- ✅ Basic frontend running (test at http://localhost:5173)
- ✅ All documentation files in place
- ✅ Ready for Claude Code CLI to take over!

**You're all set!** Time to let Claude Code CLI build the rest! 🚀
