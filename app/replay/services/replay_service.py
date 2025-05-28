import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from ..models.replay import ProcessedReplay, GameStateSnapshot

class ReplayService:
    def __init__(self, data_dir: str = "data/replays"):
        """Initialize the replay service with a data directory."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def save_replay(self, replay: ProcessedReplay) -> str:
        """Save a processed replay to disk."""
        match_id = replay.match_id
        file_path = self.data_dir / f"{match_id}.json"
        
        with open(file_path, 'w') as f:
            json.dump(replay.dict(), f, indent=2)
        
        self.logger.info(f"Saved replay data for match {match_id}")
        return match_id

    def load_replay(self, match_id: str) -> Optional[ProcessedReplay]:
        """Load a processed replay from disk."""
        file_path = self.data_dir / f"{match_id}.json"
        
        if not file_path.exists():
            self.logger.warning(f"No replay data found for match {match_id}")
            return None
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return ProcessedReplay(**data)
        except Exception as e:
            self.logger.error(f"Error loading replay data for match {match_id}: {str(e)}")
            return None

    def get_game_state(self, match_id: str, timestamp: int) -> Optional[GameStateSnapshot]:
        """Get the game state at a specific timestamp."""
        replay = self.load_replay(match_id)
        if not replay:
            return None
        
        # Get champion states at timestamp
        champion_states = self._calculate_champion_states(replay, timestamp)
        
        # Get recent events
        recent_events = self._get_recent_events(replay, timestamp)
        
        # Get team objectives
        team_objectives = self._calculate_team_objectives(replay, timestamp)
        
        return GameStateSnapshot(
            timestamp=timestamp,
            champion_states=champion_states,
            recent_events=recent_events,
            team_objectives=team_objectives
        )

    def _calculate_champion_states(self, replay: ProcessedReplay, timestamp: int) -> Dict[str, Dict]:
        """Calculate the state of each champion at the given timestamp."""
        states = {}
        
        for participant in replay.participants:
            # Find the closest position data point
            positions = replay.champion_pathing.get(participant.puuid, [])
            if not positions:
                continue
                
            # Find the closest position to the timestamp
            closest_pos = min(positions, key=lambda p: abs(p.timestamp - timestamp))
            
            # Calculate current stats
            current_gold = self._calculate_current_gold(replay, participant.puuid, timestamp)
            current_cs = self._calculate_current_cs(replay, participant.puuid, timestamp)
            current_level = self._calculate_current_level(replay, participant.puuid, timestamp)
            kda = self._calculate_kda(replay, participant.puuid, timestamp)
            current_items = self._calculate_current_items(replay, participant.puuid, timestamp)
            
            states[participant.puuid] = {
                "position": closest_pos.position.dict(),
                "current_gold": current_gold,
                "current_cs": current_cs,
                "current_level": current_level,
                "kda": kda,
                "current_items": current_items
            }
        
        return states

    def _get_recent_events(self, replay: ProcessedReplay, timestamp: int, window: int = 30000) -> List[Dict]:
        """Get events that occurred within the time window around the timestamp."""
        start_time = timestamp - window
        end_time = timestamp + window
        
        return [
            event.dict() for event in replay.game_events
            if start_time <= event.timestamp <= end_time
        ]

    def _calculate_team_objectives(self, replay: ProcessedReplay, timestamp: int) -> Dict[str, List[str]]:
        """Calculate objectives taken by each team up to the timestamp."""
        team_objectives = {"100": [], "200": []}
        
        for event in replay.game_events:
            if event.timestamp > timestamp:
                break
                
            if event.type == "OBJECTIVE_TAKEN":
                team_id = str(event.team_id)
                if team_id in team_objectives:
                    team_objectives[team_id].append(event.details.get("objective_type", "Unknown"))
        
        return team_objectives

    def _calculate_current_gold(self, replay: ProcessedReplay, puuid: str, timestamp: int) -> int:
        """Calculate the current gold for a participant at the given timestamp."""
        # This is a simplified version - in a real implementation, you'd track gold changes
        return 0

    def _calculate_current_cs(self, replay: ProcessedReplay, puuid: str, timestamp: int) -> int:
        """Calculate the current CS for a participant at the given timestamp."""
        # This is a simplified version - in a real implementation, you'd track CS changes
        return 0

    def _calculate_current_level(self, replay: ProcessedReplay, puuid: str, timestamp: int) -> int:
        """Calculate the current level for a participant at the given timestamp."""
        # This is a simplified version - in a real implementation, you'd track level changes
        return 1

    def _calculate_kda(self, replay: ProcessedReplay, puuid: str, timestamp: int) -> Dict[str, int]:
        """Calculate the KDA for a participant at the given timestamp."""
        # This is a simplified version - in a real implementation, you'd track kills/deaths/assists
        return {"kills": 0, "deaths": 0, "assists": 0}

    def _calculate_current_items(self, replay: ProcessedReplay, puuid: str, timestamp: int) -> List[int]:
        """Calculate the current items for a participant at the given timestamp."""
        # This is a simplified version - in a real implementation, you'd track item purchases
        return [] 