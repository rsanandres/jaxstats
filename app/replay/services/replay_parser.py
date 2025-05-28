import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import tempfile
import os

from ..models.replay import ProcessedReplay, GameStateSnapshot, Position, ChampionState, GameEvent, Participant, PositionData

logger = logging.getLogger(__name__)

class ReplayParser:
    def __init__(self, rofl_parser_path: Optional[str] = None):
        """
        Initialize the replay parser.
        
        Args:
            rofl_parser_path: Path to the m0w0kuma/ROFL parser binary. If None, will look for it in PATH.
        """
        self.rofl_parser_path = rofl_parser_path or "rofl-parser"
        self.logger = logging.getLogger(__name__)
        
    async def parse_rofl_file(self, file_path: str) -> ProcessedReplay:
        """
        Parse a .rofl file and extract relevant game data.
        This is a placeholder implementation that returns dummy data.
        In a real implementation, you would parse the actual .rofl file format.
        """
        self.logger.info(f"Parsing replay file: {file_path}")
        
        # Extract match ID from filename
        match_id = Path(file_path).stem
        
        # Create dummy data for testing
        participants = [
            Participant(
                puuid="player1",
                champion_id=1,
                team_id=100,
                summoner_name="Player1"
            ),
            Participant(
                puuid="player2",
                champion_id=2,
                team_id=200,
                summoner_name="Player2"
            )
        ]
        
        # Create dummy champion pathing data
        champion_pathing = {
            "player1": [
                PositionData(
                    timestamp=0,
                    position=Position(x=100, y=100)
                ),
                PositionData(
                    timestamp=60000,
                    position=Position(x=200, y=200)
                )
            ],
            "player2": [
                PositionData(
                    timestamp=0,
                    position=Position(x=300, y=300)
                ),
                PositionData(
                    timestamp=60000,
                    position=Position(x=400, y=400)
                )
            ]
        }
        
        # Create dummy game events
        game_events = [
            GameEvent(
                timestamp=300000,
                type="OBJECTIVE_TAKEN",
                team_id=100,
                details={"objective_type": "DRAGON"}
            ),
            GameEvent(
                timestamp=600000,
                type="OBJECTIVE_TAKEN",
                team_id=200,
                details={"objective_type": "BARON"}
            )
        ]
        
        return ProcessedReplay(
            match_id=match_id,
            game_duration=1800000,  # 30 minutes in milliseconds
            participants=participants,
            champion_pathing=champion_pathing,
            game_events=game_events
        )
    
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