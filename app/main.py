from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from pydantic import BaseModel
from typing import Optional, List, Dict
import uvicorn
import traceback
import sys
import logging
from datetime import datetime

from .api.riot_client import RiotAPIClient
from .analysis.stats_analyzer import StatsAnalyzer
from .ml.performance_model import PerformanceModel

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(title="JaxStats - League of Legends Stats Analysis")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Initialize components
riot_client = RiotAPIClient()
stats_analyzer = StatsAnalyzer()
performance_model = PerformanceModel()

# Store debug logs
debug_logs = []

class SummonerRequest(BaseModel):
    summoner_name: str
    region: str
    match_count: int = 5

class MatchAnalysis(BaseModel):
    match_id: str
    performance_score: float
    analysis: str
    basic_stats: dict
    vision_stats: dict
    objective_stats: dict
    damage_stats: dict
    timeline: dict
    improvement_suggestions: List[str]

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
        # Get the last frame from the traceback
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

# Add test debug logs
log_debug("INFO", "Application started")
log_debug("WARNING", "This is a test warning message")
log_debug("ERROR", "This is a test error message", sys.exc_info())

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
    """Analyze a summoner's match history and provide insights (GET endpoint)."""
    try:
        # Validate match_count
        if match_count < 1 or match_count > 20:
            error_msg = "Match count must be between 1 and 20"
            log_debug("ERROR", error_msg)
            raise ValueError(error_msg)
            
        # Split the summoner name into game name and tag line
        if '#' not in summoner_name:
            error_msg = "Summoner name must be in the format 'GameName#TAG'"
            log_debug("ERROR", error_msg)
            raise ValueError(error_msg)
            
        game_name, tag_line = summoner_name.split('#')
        
        # Get account info using Riot ID
        log_debug("INFO", f"Fetching account info for {game_name}#{tag_line} in {region}")
        account = await riot_client.get_account_by_riot_id(game_name, tag_line, region)
        puuid = account['puuid']
        
        # Get summoner info
        log_debug("INFO", f"Fetching summoner info for PUUID {puuid}")
        summoner = await riot_client.get_summoner_by_puuid(puuid, region)
        
        # Get match history with specified count
        log_debug("INFO", f"Fetching {match_count} matches for PUUID {puuid}")
        match_ids = await riot_client.get_match_history(puuid, region, count=match_count)
        
        # Get match details for each match
        matches_data = []
        cached_matches = []
        new_matches = []
        
        for match_id in match_ids:
            # Try to get cached match data first
            cached_data = riot_client._load_match_data(match_id)
            if cached_data and use_cache:
                cached_matches.append(cached_data)
            else:
                log_debug("INFO", f"Fetching details for match {match_id}")
                match_data = await riot_client.get_match_details(match_id, region)
                if match_data:
                    new_matches.append(match_data)
        
        # Combine cached and new matches
        matches_data = cached_matches + new_matches
        
        # If we have no matches at all, return early
        if not matches_data:
            return {
                "summoner_name": summoner.get("name", "Unknown"),
                "summoner_level": summoner.get("summonerLevel", 0),
                "profile_icon_id": summoner.get("profileIconId", 0),
                "overall_stats": {},
                "match_analyses": [],
                "champion_stats": {},
                "match_count": {
                    "requested": match_count,
                    "retrieved": len(match_ids),
                    "analyzed": 0,
                    "cached": 0,
                    "new": 0
                }
            }
        
        # Analyze matches
        stats_analyzer = StatsAnalyzer()
        stats_analyzer.puuid = puuid
        for match in matches_data:
            stats_analyzer.add_match(match)
        
        overall_stats = stats_analyzer.get_player_stats()
        match_analyses = [stats_analyzer.get_match_details(m.get('metadata', {}).get('matchId', '')) for m in matches_data]
        match_analyses = [m for m in match_analyses if m]
        champion_stats = stats_analyzer.get_champion_stats()
        
        return {
            "summoner_name": summoner.get("name", "Unknown"),
            "summoner_level": summoner.get("summonerLevel", 0),
            "profile_icon_id": summoner.get("profileIconId", 0),
            "overall_stats": overall_stats,
            "match_analyses": match_analyses,
            "champion_stats": champion_stats,
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

@app.get("/api/champion-stats/{summoner_name}")
async def get_champion_stats(summoner_name: str, region: str = "na1", match_count: int = 20):
    """Get champion statistics for a summoner."""
    try:
        # Validate match_count
        if match_count < 1 or match_count > 20:
            error_msg = "Match count must be between 1 and 20"
            log_debug("ERROR", error_msg)
            raise ValueError(error_msg)
            
        # Split the summoner name into game name and tag line
        if '#' not in summoner_name:
            error_msg = "Summoner name must be in the format 'GameName#TAG'"
            log_debug("ERROR", error_msg)
            raise ValueError(error_msg)
            
        game_name, tag_line = summoner_name.split('#')
        
        # Get account info using Riot ID
        log_debug("INFO", f"Fetching account info for {game_name}#{tag_line} in {region}")
        account = await riot_client.get_account_by_riot_id(game_name, tag_line, region)
        puuid = account['puuid']
        
        # Get match history with specified count
        log_debug("INFO", f"Fetching {match_count} matches for PUUID {puuid}")
        match_ids = await riot_client.get_match_history(puuid, region, count=match_count)
        
        # Get match details for each match
        matches_data = []
        for match_id in match_ids:
            log_debug("INFO", f"Fetching details for match {match_id}")
            match_data = await riot_client.get_match_details(match_id, region)
            if match_data:
                matches_data.append(match_data)
            else:
                log_debug("WARNING", f"No data for match {match_id}")
        
        # Analyze matches
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

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 