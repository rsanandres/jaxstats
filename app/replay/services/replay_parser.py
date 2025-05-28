import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import tempfile
import os

from ..models.replay import ProcessedReplay, GameStateSnapshot, Position, ChampionState, GameEvent

logger = logging.getLogger(__name__)

class ReplayParser:
    def __init__(self, rofl_parser_path: Optional[str] = None):
        """
        Initialize the replay parser.
        
        Args:
            rofl_parser_path: Path to the m0w0kuma/ROFL parser binary. If None, will look for it in PATH.
        """
        self.rofl_parser_path = rofl_parser_path or "rofl-parser"
        
    async def parse_rofl_file(self, rofl_path: str) -> ProcessedReplay:
        """
        Parse a .rofl file and extract all relevant data.
        
        Args:
            rofl_path: Path to the .rofl file
            
        Returns:
            ProcessedReplay object containing all extracted data
        """
        try:
            # Create temporary directory for parser output
            with tempfile.TemporaryDirectory() as temp_dir:
                # Run the ROFL parser
                output_path = os.path.join(temp_dir, "output.json")
                cmd = [self.rofl_parser_path, rofl_path, "--output", output_path]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"ROFL parser failed: {result.stderr}")
                
                # Read and parse the output
                with open(output_path, 'r') as f:
                    parser_output = json.load(f)
                
                # Extract statsJson data
                stats_json = self._extract_stats_json(parser_output)
                
                # Extract champion pathing data
                champion_pathing = self._extract_champion_pathing(parser_output)
                
                # Extract ward events
                ward_events = self._extract_ward_events(parser_output)
                
                # Extract game events
                game_events = self._extract_game_events(parser_output)
                
                # Calculate objective timers
                objective_timers = self._calculate_objective_timers(game_events)
                
                # Create ProcessedReplay object
                return ProcessedReplay(
                    match_id=stats_json.get("matchId", ""),
                    game_version=stats_json.get("gameVersion", ""),
                    game_duration=stats_json.get("gameLength", 0),
                    game_mode=stats_json.get("gameMode", ""),
                    map_id=stats_json.get("mapId", 0),
                    teams=self._extract_teams(stats_json),
                    participants=self._extract_participants(stats_json),
                    champion_pathing=champion_pathing,
                    ward_events=ward_events,
                    game_events=game_events,
                    objective_timers=objective_timers
                )
                
        except Exception as e:
            logger.error(f"Error parsing ROFL file: {str(e)}")
            raise
    
    def _extract_stats_json(self, parser_output: Dict) -> Dict:
        """Extract and parse the statsJson data from parser output."""
        try:
            stats_json = parser_output.get("statsJson", {})
            if not stats_json:
                raise ValueError("No statsJson data found in parser output")
            return stats_json
        except Exception as e:
            logger.error(f"Error extracting statsJson: {str(e)}")
            raise
    
    def _extract_champion_pathing(self, parser_output: Dict) -> List[Dict]:
        """Extract champion position data from parser output."""
        try:
            pathing_data = parser_output.get("championPathing", [])
            return [
                {
                    "timestamp": entry["timestamp"],
                    "participant_id": entry["participantId"],
                    "position": {
                        "x": entry["x"],
                        "y": entry["y"]
                    }
                }
                for entry in pathing_data
            ]
        except Exception as e:
            logger.error(f"Error extracting champion pathing: {str(e)}")
            raise
    
    def _extract_ward_events(self, parser_output: Dict) -> List[Dict]:
        """Extract ward placement and removal events from parser output."""
        try:
            ward_data = parser_output.get("wardEvents", [])
            return [
                {
                    "timestamp": entry["timestamp"],
                    "type": entry["type"],
                    "position": {
                        "x": entry["x"],
                        "y": entry["y"]
                    },
                    "ward_type": entry["wardType"],
                    "duration": entry["duration"],
                    "owner": entry["owner"]
                }
                for entry in ward_data
            ]
        except Exception as e:
            logger.error(f"Error extracting ward events: {str(e)}")
            raise
    
    def _extract_game_events(self, parser_output: Dict) -> List[GameEvent]:
        """Extract game events from parser output."""
        try:
            events_data = parser_output.get("gameEvents", [])
            return [
                GameEvent(
                    timestamp=event["timestamp"],
                    type=event["type"],
                    position=Position(x=event["x"], y=event["y"]) if "x" in event and "y" in event else None,
                    participant_id=event.get("participantId"),
                    team_id=event.get("teamId"),
                    building_type=event.get("buildingType"),
                    lane_type=event.get("laneType"),
                    tower_type=event.get("towerType"),
                    monster_type=event.get("monsterType"),
                    monster_sub_type=event.get("monsterSubType")
                )
                for event in events_data
            ]
        except Exception as e:
            logger.error(f"Error extracting game events: {str(e)}")
            raise
    
    def _calculate_objective_timers(self, game_events: List[GameEvent]) -> Dict[str, int]:
        """Calculate next spawn timers for objectives based on game events."""
        timers = {
            "nextDragonSpawnTimestamp": 0,
            "nextBaronSpawnTimestamp": 0
        }
        
        # Find the last dragon and baron kills
        last_dragon_kill = 0
        last_baron_kill = 0
        
        for event in game_events:
            if event.type == "ELITE_MONSTER_KILL":
                if event.monster_type == "DRAGON":
                    last_dragon_kill = event.timestamp
                elif event.monster_type == "BARON_NASHOR":
                    last_baron_kill = event.timestamp
        
        # Calculate next spawn times (5 minutes for dragon, 6 minutes for baron)
        if last_dragon_kill > 0:
            timers["nextDragonSpawnTimestamp"] = last_dragon_kill + 300000  # 5 minutes in milliseconds
        if last_baron_kill > 0:
            timers["nextBaronSpawnTimestamp"] = last_baron_kill + 360000  # 6 minutes in milliseconds
        
        return timers
    
    def _extract_teams(self, stats_json: Dict) -> List[Dict]:
        """Extract team information from statsJson."""
        teams = []
        for team_id in [100, 200]:  # Blue and Red teams
            team_data = {
                "teamId": team_id,
                "win": False,
                "objectives": {
                    "dragon": 0,
                    "baron": 0,
                    "tower": 0,
                    "inhibitor": 0
                }
            }
            teams.append(team_data)
        return teams
    
    def _extract_participants(self, stats_json: Dict) -> List[Dict]:
        """Extract participant information from statsJson."""
        participants = []
        for participant in stats_json.get("participants", []):
            participant_data = {
                "participantId": participant.get("participantId"),
                "summonerName": participant.get("summonerName"),
                "championName": participant.get("championName"),
                "teamId": participant.get("teamId"),
                "win": participant.get("win", False),
                "kills": participant.get("kills", 0),
                "deaths": participant.get("deaths", 0),
                "assists": participant.get("assists", 0),
                "goldEarned": participant.get("goldEarned", 0),
                "goldSpent": participant.get("goldSpent", 0),
                "totalMinionsKilled": participant.get("totalMinionsKilled", 0),
                "neutralMinionsKilled": participant.get("neutralMinionsKilled", 0),
                "level": participant.get("level", 1),
                "items": [
                    participant.get(f"item{i}", 0)
                    for i in range(7)  # Items 0-6
                ]
            }
            participants.append(participant_data)
        return participants 