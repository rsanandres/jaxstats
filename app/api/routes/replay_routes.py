from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from ...replay.services.replay_service import ReplayService
from ...replay.services.replay_parser import ReplayParser
from ...replay.models.replay import ProcessedReplay
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
replay_service = ReplayService()
replay_parser = ReplayParser()

@router.get("/replays", response_model=List[dict])
async def list_replays():
    """List all available replays."""
    try:
        # Get all replay files from the data directory
        replay_files = replay_service.data_dir.glob("*.json")
        replays = []
        
        for file_path in replay_files:
            try:
                replay = replay_service.load_replay(file_path.stem)
                replays.append({
                    "match_id": replay.match_id,
                    "game_duration": replay.game_duration,
                    "timestamp": file_path.stat().st_mtime,
                    "participants": len(replay.participants)
                })
            except Exception as e:
                logger.error(f"Error loading replay {file_path.stem}: {str(e)}")
                continue
        
        return sorted(replays, key=lambda x: x["timestamp"], reverse=True)
    except Exception as e:
        logger.error(f"Error listing replays: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list replays")

@router.get("/replays/{match_id}", response_model=ProcessedReplay)
async def get_replay(match_id: str):
    """Get a specific replay by match ID."""
    try:
        return replay_service.load_replay(match_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Replay not found")
    except Exception as e:
        logger.error(f"Error loading replay {match_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load replay")

@router.post("/replays/upload")
async def upload_replay(replay: UploadFile = File(...)):
    """Upload and process a new replay file."""
    try:
        if not replay.filename.lower().endswith('.rofl'):
            raise HTTPException(status_code=400, detail="Only .rofl files are supported")
        
        # Save the uploaded file temporarily
        temp_path = replay_service.data_dir / "temp" / replay.filename
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(temp_path, "wb") as f:
            content = await replay.read()
            f.write(content)
        
        try:
            # Parse the replay file
            processed_replay = await replay_parser.parse_rofl_file(str(temp_path))
            
            # Save the processed replay
            match_id = replay_service.save_replay(processed_replay)
            
            return {
                "match_id": match_id,
                "game_duration": processed_replay.game_duration,
                "timestamp": temp_path.stat().st_mtime,
                "participants": len(processed_replay.participants)
            }
        finally:
            # Clean up the temporary file
            temp_path.unlink(missing_ok=True)
            
    except Exception as e:
        logger.error(f"Error uploading replay: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process replay") 