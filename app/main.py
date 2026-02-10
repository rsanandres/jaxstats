from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import uvicorn
import traceback
import sys
import logging
from datetime import datetime

from .api.riot_client import RiotAPIClient
from .analysis.stats_analyzer import StatsAnalyzer
from .ml.xgb_model import JaxStatsModels
from .ml.features import extract_participant_features, extract_all_participants
from .ml.gpi import compute_full_gpi
from .analysis.suggestion_engine import generate_suggestion_async
from .llm.ollama_client import check_ollama_health

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="JaxStats - League of Legends Stats Analysis")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Initialize components
riot_client = RiotAPIClient()
ml_models = JaxStatsModels()

# Store debug logs
debug_logs = []

class SummonerRequest(BaseModel):
    summoner_name: str
    region: str
    match_count: int = 5

class DebugLog(BaseModel):
    timestamp: str
    level: str
    message: str
    traceback: Optional[str] = None
    code_context: Optional[Dict] = None

class CompareRequest(BaseModel):
    summoner1_name: str
    summoner1_region: str
    summoner2_name: str
    summoner2_region: str
    match_count: int = 5

def log_debug(level: str, message: str, exc_info=None):
    """Log debug information with timestamp and stack trace."""
    timestamp = datetime.now().isoformat()
    traceback_str = None
    code_context = None

    if exc_info:
        traceback_str = ''.join(traceback.format_exception(*exc_info))
        tb = traceback.extract_tb(exc_info[2])
        if tb:
            last_frame = tb[-1]
            code_context = {
                'filename': last_frame.filename,
                'line_number': last_frame.lineno,
                'function': last_frame.name,
                'code': last_frame.line
            }

    log_entry = DebugLog(
        timestamp=timestamp,
        level=level,
        message=message,
        traceback=traceback_str,
        code_context=code_context
    )
    debug_logs.append(log_entry)
    return log_entry

log_debug("INFO", "Application started")


def _find_player_participant(match_data: dict, puuid: str) -> Optional[dict]:
    """Find the raw participant dict for the given puuid in a match."""
    for p in match_data.get("info", {}).get("participants", []):
        if p.get("puuid") == puuid:
            return p
    return None


def _score_match_for_player(match_data: dict, puuid: str) -> Optional[Dict]:
    """Run ML scoring on a player's match performance."""
    participant = _find_player_participant(match_data, puuid)
    if not participant:
        return None
    duration = match_data.get("info", {}).get("gameDuration", 0)
    features = extract_participant_features(participant, duration)
    return ml_models.score_match(features)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/debug-logs")
async def get_debug_logs():
    """Get all debug logs."""
    try:
        return {"logs": debug_logs}
    except Exception as e:
        error_msg = f"Error retrieving debug logs: {str(e)}"
        log_debug("ERROR", error_msg, sys.exc_info())
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/analyze")
async def analyze_summoner_post(request: SummonerRequest):
    """Analyze a summoner's match history and provide insights (POST endpoint)."""
    try:
        return await analyze_summoner(request.summoner_name, request.region, request.match_count, use_cache=True)
    except Exception as e:
        error_msg = f"Error analyzing summoner: {str(e)}"
        log_debug("ERROR", error_msg, sys.exc_info())
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/api/analyze/{summoner_name}")
async def analyze_summoner(summoner_name: str, region: str = "na1", match_count: int = 5, use_cache: bool = True):
    """Analyze a summoner's match history and provide insights."""
    try:
        if match_count < 1 or match_count > 20:
            raise ValueError("Match count must be between 1 and 20")

        if '#' not in summoner_name:
            raise ValueError("Summoner name must be in the format 'GameName#TAG'")

        game_name, tag_line = summoner_name.split('#')

        account = await riot_client.get_account_by_riot_id(game_name, tag_line, region)
        puuid = account['puuid']
        summoner = await riot_client.get_summoner_by_puuid(puuid, region)

        match_ids = await riot_client.get_match_history(puuid, region, count=match_count)

        matches_data = []
        cached_matches = []
        new_matches = []

        for match_id in match_ids:
            cached_data = riot_client._load_match_data(match_id)
            if cached_data and use_cache:
                cached_matches.append(cached_data)
            else:
                match_data = await riot_client.get_match_details(match_id, region)
                if match_data:
                    new_matches.append(match_data)

        matches_data = cached_matches + new_matches

        if not matches_data:
            return {
                "summoner_name": summoner.get("name", "Unknown"),
                "summoner_level": summoner.get("summonerLevel", 0),
                "profile_icon_id": summoner.get("profileIconId", 0),
                "overall_stats": {},
                "match_analyses": [],
                "champion_stats": {},
                "gpi": {},
                "trends": {},
                "match_count": {
                    "requested": match_count,
                    "retrieved": len(match_ids),
                    "analyzed": 0, "cached": 0, "new": 0
                }
            }

        # Stats analysis
        stats_analyzer = StatsAnalyzer()
        stats_analyzer.puuid = puuid
        for match in matches_data:
            stats_analyzer.add_match(match)

        overall_stats = stats_analyzer.get_player_stats()
        match_analyses = [stats_analyzer.get_match_details(m.get('metadata', {}).get('matchId', '')) for m in matches_data]
        match_analyses = [m for m in match_analyses if m]
        champion_stats = stats_analyzer.get_champion_stats()
        trend_data = stats_analyzer.get_trend_data()

        # ML scoring per match
        player_features_list = []
        for i, match_data in enumerate(matches_data):
            ml_result = _score_match_for_player(match_data, puuid)
            if ml_result and i < len(match_analyses):
                match_analyses[i]["ml_scores"] = ml_result

            # Collect features for GPI
            participant = _find_player_participant(match_data, puuid)
            if participant:
                duration = match_data.get("info", {}).get("gameDuration", 0)
                feats = extract_participant_features(participant, duration)
                feats["champion_name"] = participant.get("championName", "")
                feats["position"] = participant.get("teamPosition", "")
                player_features_list.append(feats)

        # Full GPI across all matches
        gpi = compute_full_gpi(player_features_list)

        return {
            "summoner_name": summoner.get("name", "Unknown"),
            "summoner_level": summoner.get("summonerLevel", 0),
            "profile_icon_id": summoner.get("profileIconId", 0),
            "overall_stats": overall_stats,
            "match_analyses": match_analyses,
            "champion_stats": champion_stats,
            "gpi": gpi,
            "trends": trend_data.get("trends", {}),
            "trend_matches": trend_data.get("matches", []),
            "match_count": {
                "requested": match_count,
                "retrieved": len(match_ids),
                "analyzed": len(match_analyses),
                "cached": len(cached_matches),
                "new": len(new_matches)
            }
        }
    except Exception as e:
        error_msg = f"Error analyzing summoner: {str(e)}"
        log_debug("ERROR", error_msg, sys.exc_info())
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/api/gpi/{summoner_name}")
async def get_gpi(summoner_name: str, region: str = "na1", match_count: int = 10):
    """Get full GPI (Gamer Performance Index) breakdown for a summoner."""
    try:
        if '#' not in summoner_name:
            raise ValueError("Summoner name must be in the format 'GameName#TAG'")

        game_name, tag_line = summoner_name.split('#')
        account = await riot_client.get_account_by_riot_id(game_name, tag_line, region)
        puuid = account['puuid']

        match_ids = await riot_client.get_match_history(puuid, region, count=min(match_count, 20))

        player_features_list = []
        for match_id in match_ids:
            match_data = await riot_client.get_match_details(match_id, region)
            if match_data:
                participant = _find_player_participant(match_data, puuid)
                if participant:
                    duration = match_data.get("info", {}).get("gameDuration", 0)
                    feats = extract_participant_features(participant, duration)
                    feats["champion_name"] = participant.get("championName", "")
                    feats["position"] = participant.get("teamPosition", "")
                    player_features_list.append(feats)

        gpi = compute_full_gpi(player_features_list)

        return {
            "summoner_name": summoner_name,
            "match_count": len(player_features_list),
            "gpi": gpi,
        }
    except Exception as e:
        error_msg = f"Error computing GPI: {str(e)}"
        log_debug("ERROR", error_msg, sys.exc_info())
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/api/match-timeline/{match_id}")
async def get_match_timeline(match_id: str, region: str = "na1"):
    """Get timeline events for a specific match."""
    try:
        timeline = await riot_client.get_match_timeline(match_id, region)
        if not timeline:
            raise HTTPException(status_code=404, detail="Timeline not found")
        return timeline
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error fetching timeline: {str(e)}"
        log_debug("ERROR", error_msg, sys.exc_info())
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/api/live-game/{summoner_name}")
async def get_live_game(summoner_name: str, region: str = "na1"):
    """Get live game data for a summoner currently in game."""
    try:
        if '#' not in summoner_name:
            raise ValueError("Summoner name must be in the format 'GameName#TAG'")

        game_name, tag_line = summoner_name.split('#')
        account = await riot_client.get_account_by_riot_id(game_name, tag_line, region)
        puuid = account['puuid']

        game_data = await riot_client.get_active_game(puuid, region)
        if not game_data:
            raise HTTPException(status_code=404, detail="Not currently in a game")

        # Enrich each participant with recent stats and GPI
        participants = game_data.get("participants", [])
        enriched = []
        for p in participants:
            player_puuid = p.get("puuid", "")
            entry = {
                "summonerName": p.get("riotId", p.get("summonerId", "Unknown")),
                "championId": p.get("championId", 0),
                "teamId": p.get("teamId", 0),
                "spell1Id": p.get("spell1Id", 0),
                "spell2Id": p.get("spell2Id", 0),
            }

            # Try to get recent match history for GPI (best effort, don't block on errors)
            try:
                recent_ids = await riot_client.get_match_history(player_puuid, region, count=5)
                if recent_ids:
                    features_list = []
                    for mid in recent_ids[:3]:  # Limit to 3 for speed
                        md = await riot_client.get_match_details(mid, region)
                        if md:
                            participant_data = _find_player_participant(md, player_puuid)
                            if participant_data:
                                duration = md.get("info", {}).get("gameDuration", 0)
                                feats = extract_participant_features(participant_data, duration)
                                feats["champion_name"] = participant_data.get("championName", "")
                                feats["position"] = participant_data.get("teamPosition", "")
                                features_list.append(feats)

                    if features_list:
                        gpi = compute_full_gpi(features_list)
                        wins = sum(1 for f in features_list if f.get("win", 0) > 0.5)
                        entry["gpi"] = gpi
                        entry["recent_win_rate"] = round(wins / len(features_list) * 100, 1)
            except Exception:
                pass  # Don't fail the whole request for one player

            enriched.append(entry)

        return {
            "game_id": game_data.get("gameId"),
            "game_mode": game_data.get("gameMode", "CLASSIC"),
            "game_type": game_data.get("gameType", ""),
            "game_length": game_data.get("gameLength", 0),
            "participants": enriched,
        }
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error fetching live game: {str(e)}"
        log_debug("ERROR", error_msg, sys.exc_info())
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/api/champion-stats/{summoner_name}")
async def get_champion_stats(summoner_name: str, region: str = "na1", match_count: int = 20):
    """Get champion statistics for a summoner."""
    try:
        if match_count < 1 or match_count > 20:
            raise ValueError("Match count must be between 1 and 20")

        if '#' not in summoner_name:
            raise ValueError("Summoner name must be in the format 'GameName#TAG'")

        game_name, tag_line = summoner_name.split('#')

        account = await riot_client.get_account_by_riot_id(game_name, tag_line, region)
        puuid = account['puuid']

        match_ids = await riot_client.get_match_history(puuid, region, count=match_count)

        matches_data = []
        for match_id in match_ids:
            match_data = await riot_client.get_match_details(match_id, region)
            if match_data:
                matches_data.append(match_data)

        stats_analyzer = StatsAnalyzer()
        stats_analyzer.puuid = puuid
        for match in matches_data:
            stats_analyzer.add_match(match)

        champion_stats = stats_analyzer.get_champion_stats()

        return {
            "summoner_name": summoner_name,
            "champion_stats": champion_stats,
            "match_count": {
                "requested": match_count,
                "retrieved": len(match_ids),
                "analyzed": len(matches_data)
            }
        }
    except Exception as e:
        error_msg = f"Error getting champion stats: {str(e)}"
        log_debug("ERROR", error_msg, sys.exc_info())
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/compare")
async def compare_summoners(request: CompareRequest):
    """Compare two summoners' stats side by side."""
    try:
        user1_stats = await analyze_summoner(request.summoner1_name, request.summoner1_region, request.match_count)
        user2_stats = await analyze_summoner(request.summoner2_name, request.summoner2_region, request.match_count)
        return {
            "user1": user1_stats,
            "user2": user2_stats
        }
    except Exception as e:
        error_msg = f"Error comparing summoners: {str(e)}"
        log_debug("ERROR", error_msg, sys.exc_info())
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/health")
async def health_check():
    """Service health check."""
    ollama_ok = await check_ollama_health()
    return {
        "status": "ok",
        "riot_api_key": bool(riot_client.api_key),
        "ollama": "connected" if ollama_ok else "unavailable",
        "ml_models": ml_models.status,
    }

@app.get("/health")
async def health_check():
    """Service health check."""
    ollama_ok = await check_ollama_health()
    return {
        "status": "ok",
        "riot_api_key": bool(riot_client.api_key),
        "ollama": "connected" if ollama_ok else "unavailable",
        "ml_models": ml_models.status,
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
