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
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import replay_routes

from .api.riot_client import RiotAPIClient
from .analysis.stats_analyzer import StatsAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="JaxStats API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
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
stats_analyzer = StatsAnalyzer()

# Store debug logs
debug_logs = []

# Include replay system routers
app.include_router(replay_routes.router, prefix="/api", tags=["replays"])

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

@app.get("/")
async def root():
    return {"message": "Welcome to JaxStats API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

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
        logger.error(f"Unhandled exception: {error_msg}", exc_info=True)
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
        
        # Process matches
        match_analyses = []
        for match_data in matches_data:
            # Get basic stats
            basic_stats = stats_analyzer.get_basic_stats(match_data)
            vision_stats = stats_analyzer.get_vision_stats(match_data)
            objective_stats = stats_analyzer.get_objective_stats(match_data)
            damage_stats = stats_analyzer.get_damage_stats(match_data)
            timeline = stats_analyzer.get_timeline(match_data)
            
            # Create match analysis
            match_analysis = MatchAnalysis(
                match_id=match_data["metadata"]["matchId"],
                performance_score=stats_analyzer.calculate_performance_score(match_data),
                analysis=stats_analyzer.generate_analysis(match_data),
                basic_stats=basic_stats,
                vision_stats=vision_stats,
                objective_stats=objective_stats,
                damage_stats=damage_stats,
                timeline=timeline,
                improvement_suggestions=stats_analyzer.get_improvement_suggestions(match_data)
            )
            match_analyses.append(match_analysis)
        
        # Get overall stats
        overall_stats = stats_analyzer.get_player_stats()
        
        # Get champion stats
        champion_stats = stats_analyzer.get_champion_stats()
        
        return {
            "summoner_name": summoner.get("name", "Unknown"),
            "summoner_level": summoner.get("summonerLevel", 0),
            "profile_icon_id": summoner.get("profileIconId", 0),
            "overall_stats": overall_stats,
            "match_analyses": [analysis.dict() for analysis in match_analyses],
            "champion_stats": champion_stats,
            "match_count": {
                "requested": match_count,
                "retrieved": len(match_ids),
                "analyzed": len(matches_data),
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