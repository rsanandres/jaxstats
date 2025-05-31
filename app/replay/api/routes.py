from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List, Optional
import os
import shutil
from pathlib import Path
import tempfile

from ..models.replay import ProcessedReplay, GameStateSnapshot
from ..services.replay_parser import ReplayParser
from ..services.replay_service import ReplayService

router = APIRouter(prefix="/api/replays", tags=["replays"])

# Initialize services
replay_parser = ReplayParser()
replay_service = ReplayService()

@router.get("/matches/{match_id}/replays")
async def list_replays(match_id: str):
    """
    List available processed replays for a match.
    """
    try:
        # Check if a processed replay exists for this match
        replay_path = Path(f"data/replays/{match_id}.json")
        if replay_path.exists():
            return {
                "match_id": match_id,
                "replays": [match_id]
            }
        return {
            "match_id": match_id,
            "replays": []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{replay_id}")
async def get_replay(replay_id: str):
    """
    Get the complete processed replay data.
    """
    try:
        replay = replay_service.load_replay(replay_id)
        return replay
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Replay {replay_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{replay_id}/gamestate")
async def get_game_state(replay_id: str, timestamp: int):
    """
    Get the game state at a specific timestamp.
    """
    try:
        replay = replay_service.load_replay(replay_id)
        game_state = replay_service.get_game_state(replay, timestamp)
        return game_state
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Replay {replay_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process")
async def process_replay(match_id: str, region: str = "na1"):
    """
    Process a match timeline from the Riot API and store the extracted data.
    """
    try:
        # Parse the match timeline
        replay = await replay_parser.parse_match_timeline(match_id, region)
        
        # Save the processed replay
        replay_id = replay_service.save_replay(replay)
        
        # Log the command
        with open("/tmp/command_log.txt", "a") as f:
            f.write(f"$ process_replay(match_id={match_id}, region={region})\n")
            f.write(f"Replay ID: {replay_id}\n\n")
        
        return {
            "replay_id": replay_id,
            "status": "success"
        }
    except Exception as e:
        # Log the error
        with open("/tmp/command_log.txt", "a") as f:
            f.write(f"$ process_replay(match_id={match_id}, region={region})\n")
            f.write(f"Error: {str(e)}\n\n")
        raise HTTPException(status_code=500, detail=str(e)) 