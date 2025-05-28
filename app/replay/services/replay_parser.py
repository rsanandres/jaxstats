import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
import aiohttp
import os

from ..models.replay import ProcessedReplay, GameStateSnapshot, Position, ChampionState, GameEvent, Participant, PositionData

logger = logging.getLogger(__name__)

class ReplayParser:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the replay parser.
        
        Args:
            api_key: Riot API key. If None, will use the RIOT_API_KEY environment variable.
        """
        self.api_key = api_key or os.getenv("RIOT_API_KEY")
        if not self.api_key:
            raise ValueError("RIOT_API_KEY environment variable is not set.")
        self.logger = logging.getLogger(__name__)
        
    async def parse_match_timeline(self, match_id: str, region: str = "na1") -> ProcessedReplay:
        """
        Fetch and parse the match timeline from the Riot API.
        This replaces the .rofl file parsing with the match timeline endpoint.
        """
        try:
            self.logger.info(f"Fetching match timeline for match ID: {match_id}")
            
            # Determine the routing value for the region
            routing = self._get_routing_value(region)
            url = f"https://{routing}.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
            headers = {"X-Riot-Token": self.api_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Failed to fetch match timeline: {error_text}")
                        raise RuntimeError(f"Failed to fetch match timeline: {error_text}")
                    
                    timeline_data = await response.json()
            
            # Extract participants from the timeline metadata
            participants = []
            for puuid in timeline_data["metadata"]["participants"]:
                participants.append(Participant(
                    puuid=puuid,
                    champion_id=0,  # Placeholder, as the timeline doesn't provide champion IDs
                    team_id=0,      # Placeholder, as the timeline doesn't provide team IDs
                    summoner_name="Unknown"  # Placeholder, as the timeline doesn't provide summoner names
                ))
            
            # Extract champion pathing data from the frames
            champion_pathing = {}
            for frame in timeline_data["info"]["frames"]:
                for participant_id, frame_data in frame["participantFrames"].items():
                    if participant_id not in champion_pathing:
                        champion_pathing[participant_id] = []
                    
                    champion_pathing[participant_id].append(PositionData(
                        timestamp=frame["timestamp"],
                        position=Position(x=frame_data["position"]["x"], y=frame_data["position"]["y"])
                    ))
            
            # Extract game events from the frames
            game_events = []
            for frame in timeline_data["info"]["frames"]:
                for event in frame["events"]:
                    if event["type"] == "CHAMPION_KILL":
                        game_events.append(GameEvent(
                            timestamp=event["timestamp"],
                            type="CHAMPION_KILL",
                            team_id=0,  # Placeholder, as the timeline doesn't provide team IDs
                            details={"killerId": event["killerId"], "victimId": event["victimId"]}
                        ))
                    elif event["type"] == "OBJECTIVE_TAKEN":
                        game_events.append(GameEvent(
                            timestamp=event["timestamp"],
                            type="OBJECTIVE_TAKEN",
                            team_id=event["teamId"],
                            details={"objective_type": event["monsterType"]}
                        ))
            
            return ProcessedReplay(
                match_id=match_id,
                game_duration=timeline_data["info"]["frameInterval"] * len(timeline_data["info"]["frames"]),
                participants=participants,
                champion_pathing=champion_pathing,
                game_events=game_events
            )
        except Exception as e:
            self.logger.error(f"Error parsing match timeline for match ID {match_id}: {str(e)}")
            raise RuntimeError(f"Failed to parse match timeline: {str(e)}")
    
    def _get_routing_value(self, region: str) -> str:
        """Get the routing value for a given region."""
        routing_map = {
            "na1": "americas",
            "br1": "americas",
            "la1": "americas",
            "la2": "americas",
            "euw1": "europe",
            "eun1": "europe",
            "tr1": "europe",
            "ru": "europe",
            "kr": "asia",
            "jp1": "asia",
            "oc1": "sea",
            "sg2": "sea",
            "tw2": "sea",
            "vn2": "sea"
        }
        routing = routing_map.get(region.lower())
        if not routing:
            raise ValueError(f"Invalid region: {region}")
        return routing
    
    def _extract_stats_json(self, parser_output: Dict) -> Dict:
        """Extract and parse the statsJson data from parser output."""
        try:
            if not isinstance(parser_output, dict):
                raise ValueError(f"Invalid parser output format. Expected dict, got {type(parser_output)}")
            
            stats_json = parser_output.get("statsJson", {})
            if not stats_json:
                raise ValueError("No statsJson data found in parser output")
            return stats_json
        except Exception as e:
            self.logger.error(f"Error extracting statsJson: {str(e)}")
            raise RuntimeError(f"Failed to extract statsJson: {str(e)}")
    
    def _extract_champion_pathing(self, parser_output: Dict) -> List[Dict]:
        """Extract champion position data from parser output."""
        try:
            if not isinstance(parser_output, dict):
                raise ValueError(f"Invalid parser output format. Expected dict, got {type(parser_output)}")
            
            pathing_data = parser_output.get("championPathing", [])
            if not isinstance(pathing_data, list):
                raise ValueError(f"Invalid championPathing format. Expected list, got {type(pathing_data)}")
            
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
        except KeyError as e:
            self.logger.error(f"Missing required field in champion pathing data: {str(e)}")
            raise ValueError(f"Invalid champion pathing data format: missing field {str(e)}")
        except Exception as e:
            self.logger.error(f"Error extracting champion pathing: {str(e)}")
            raise RuntimeError(f"Failed to extract champion pathing: {str(e)}")
    
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