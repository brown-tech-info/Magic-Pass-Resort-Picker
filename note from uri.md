# A Note from Uri

Hey there!

This project was built entirely using [Claude Code](https://claude.ai/claude-code) - Anthropic's CLI tool for AI-assisted software development.

## Getting Started

If you've cloned this repo and want to get it running, just open Claude Code in the project directory and ask it to:

> "Set up and run the backend and frontend for me"

Claude Code will:
1. Set up the Python virtual environment and install dependencies
2. Install the Node.js packages for the frontend
3. Start both servers for you

## Before You Begin

You'll need to create your own `backend/.env` file with your API keys. Copy the example file to get started:

```
cp backend/.env.example backend/.env
```

Then fill in your own:
- **Azure OpenAI** credentials (from Azure Portal)
- **OpenWeather API** key (free at openweathermap.org)

## Why Claude Code?

I wanted to see how far I could get building a full-stack app with AI assistance. Turns out - pretty far! From initial setup to debugging to writing this very note, Claude Code has been my pair programming partner throughout.

Give it a try yourself and happy coding!

— Uri
