import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import logging
from ..models.replay import ProcessedReplay, ReplayListItem, GameState, ChampionState

logger = logging.getLogger(__name__)

class ReplayService:
    def __init__(self, data_dir: str = "data/replays"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def save_replay(self, replay: ProcessedReplay) -> None:
        """Save a processed replay to disk."""
        try:
            file_path = os.path.join(self.data_dir, f"{replay.match_id}.json")
            with open(file_path, 'w') as f:
                json.dump(replay.dict(), f, default=str)
            logger.info(f"Saved replay {replay.match_id}")
        except Exception as e:
            logger.error(f"Error saving replay {replay.match_id}: {str(e)}")
            raise

    def load_replay(self, match_id: str) -> ProcessedReplay:
        """Load a processed replay from disk."""
        try:
            file_path = os.path.join(self.data_dir, f"{match_id}.json")
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Replay {match_id} not found")
            
            with open(file_path, 'r') as f:
                data = json.load(f)
                return ProcessedReplay(**data)
        except Exception as e:
            logger.error(f"Error loading replay {match_id}: {str(e)}")
            raise

    def list_replays(self) -> List[ReplayListItem]:
        """List all available replays."""
        try:
            replays = []
            for filename in os.listdir(self.data_dir):
                if filename.endswith('.json'):
                    match_id = filename[:-5]  # Remove .json extension
                    replay = self.load_replay(match_id)
                    replays.append(ReplayListItem(
                        match_id=replay.match_id,
                        game_duration=replay.game_duration,
                        timestamp=replay.timestamp,
                        participant_count=len(replay.participants)
                    ))
            return sorted(replays, key=lambda x: x.timestamp, reverse=True)
        except Exception as e:
            logger.error(f"Error listing replays: {str(e)}")
            raise

    def get_game_state(self, match_id: str, timestamp: float) -> Optional[GameState]:
        """Get the game state at a specific timestamp."""
        try:
            replay = self.load_replay(match_id)
            if not replay.game_states:
                return None

            # Find the closest game state to the requested timestamp
            closest_state = min(
                replay.game_states,
                key=lambda x: abs(x.timestamp - timestamp)
            )
            return closest_state
        except Exception as e:
            logger.error(f"Error getting game state for {match_id} at {timestamp}: {str(e)}")
            raise

    def delete_replay(self, match_id: str) -> None:
        """Delete a replay file."""
        try:
            file_path = os.path.join(self.data_dir, f"{match_id}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted replay {match_id}")
            else:
                raise FileNotFoundError(f"Replay {match_id} not found")
        except Exception as e:
            logger.error(f"Error deleting replay {match_id}: {str(e)}")
            raise 