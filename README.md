# JaxStats

A League of Legends stats analysis tool built with FastAPI and XGBoost. Fetches match data from the Riot Games API and provides ML-powered performance scoring, GPI skill breakdown, and AI-driven coaching suggestions.

## Features

- Summoner stats analysis with match history
- Per-champion performance breakdown
- Head-to-head summoner comparison
- XGBoost-powered performance scoring and GPI skill radar
- AI coaching suggestions via Ollama (llama3)
- Live game lookup
- Dark-themed gaming dashboard with charts

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your RIOT_API_KEY
uvicorn app.main:app --reload
```

## Docker

```bash
docker build -t jaxstats:local .
docker run -p 8000:8000 -e RIOT_API_KEY=your_key jaxstats:local
```

## License

MIT
