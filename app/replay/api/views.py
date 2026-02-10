from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

from ..services.replay_service import ReplayService

router = APIRouter()
templates = Jinja2Templates(directory="app/replay/templates")
replay_service = ReplayService()

@router.get("/matches/{match_id}/replay", response_class=HTMLResponse)
async def replay_view(request: Request, match_id: str):
    """
    Render the replay view for a specific match.
    """
    try:
        # Load replay data
        replay = replay_service.load_replay(match_id)
        
        # Format game duration for display
        game_duration_formatted = format_game_duration(replay.game_duration)
        
        return templates.TemplateResponse(
            "replay.html",
            {
                "request": request,
                "match_id": match_id,
                "game_duration": replay.game_duration,
                "game_duration_formatted": game_duration_formatted,
                "participants": replay.participants
            }
        )
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Replay for match {match_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def format_game_duration(ms: int) -> str:
    """Format game duration in milliseconds to MM:SS format."""
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02d}" 