# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

JaxStats is a Python/FastAPI web application for analyzing League of Legends player performance. It integrates with the Riot Games API to fetch match data and provides ML-powered performance scoring using XGBoost, GPI (Gamer Performance Index) skill breakdown, and optional AI coaching suggestions via Ollama.

## Commands

### Run the application
```bash
source .venv/bin/activate
uvicorn app.main:app --reload
# Accessible at http://localhost:8000
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Train ML models
```bash
python -m app.ml.train
# Trains on cached match data in data/ directory
# Saves models to app/ml/models/
```

### Docker
```bash
docker build -t jaxstats:local .
docker run -p 8000:8000 -e RIOT_API_KEY=your_key jaxstats:local
```

### No test suite
There is no formal test framework configured. No pytest, unittest, or CI/CD pipeline exists.

## Architecture

### Request Flow
1. Frontend (`app/templates/index.html` + `app/static/js/main.js`) sends requests to FastAPI endpoints
2. `app/main.py` routes requests and orchestrates services:
   - **RiotAPIClient** (`app/api/riot_client.py`) — async HTTP client for Riot Games API with rate-limit handling (120s backoff on 429) and local JSON file caching in `data/`
   - **StatsAnalyzer** (`app/analysis/stats_analyzer.py`) — parses raw match data into aggregated player/champion/position statistics, computes trends
   - **JaxStatsModels** (`app/ml/xgb_model.py`) — XGBoost match scorer (0-100), tier predictor, and win predictor
   - **GPI** (`app/ml/gpi.py`) — 8-skill Gamer Performance Index scoring (farming, vision, aggression, fighting, survivability, objectives, consistency, versatility)
   - **SuggestionEngine** (`app/analysis/suggestion_engine.py`) — AI coaching via Ollama with rule-based fallback

### ML Pipeline
- `app/ml/features.py` — centralized feature extraction from Riot match data
- `app/ml/gpi.py` — formula-based GPI skill scoring (0-100 per skill)
- `app/ml/xgb_model.py` — XGBoost models for match scoring, tier prediction, win prediction
- `app/ml/train.py` — training pipeline using cached match data (uses all 10 players per match)
- Trained models stored in `app/ml/models/` as XGBoost JSON files

### Key API Endpoints
- `POST /api/analyze` — Analyze summoner stats (supports `use_cache` flag)
- `GET /api/analyze/{summoner_name}` — Summoner stats with GPI, ML scores, trends
- `GET /api/gpi/{summoner_name}` — Full GPI breakdown (8 skills scored 0-100)
- `GET /api/match-timeline/{match_id}` — Match timeline events
- `GET /api/live-game/{summoner_name}` — Live game with all 10 players and their GPI
- `GET /api/champion-stats/{summoner_name}` — Per-champion breakdown
- `POST /api/compare` — Head-to-head summoner comparison
- `GET /health` — Service health check (API key, Ollama, ML models)

### Data Caching
Match data is cached as `data/match_{match_id}.json`. The riot client checks for cached files before making API calls to reduce rate limit pressure.

### Frontend
Single-page app with three tabs (Stats / Head to Head / Live Game). Uses Tailwind CSS via CDN and Chart.js for data visualization. Dark gaming dashboard theme. Charts include GPI radar, performance trend, KDA trend, role distribution, and damage breakdown.

## Git Conventions

- Do NOT include a `Co-Authored-By` line in commit messages. Commits should not credit Claude.

## Environment

- Requires `RIOT_API_KEY` env var (set in `.env` or exported)
- Optional: `OLLAMA_BASE_URL` and `OLLAMA_MODEL` for AI suggestions (falls back to rule-based if unavailable)
- Python 3.10+
- See `.env.example` for all environment variables
