from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from .suggestion_engine import generate_suggestion

@dataclass
class PerkStats:
    defense: int
    flex: int
    offense: int

@dataclass
class PerkStyleSelection:
    perk: int
    var1: int
    var2: int
    var3: int

@dataclass
class PerkStyle:
    description: str
    selections: List[PerkStyleSelection]
    style: int

@dataclass
class Perks:
    statPerks: PerkStats
    styles: List[PerkStyle]

@dataclass
class Participant:
    puuid: str
    summonerId: str
    summonerName: str
    championId: int
    championName: str
    teamId: int
    teamPosition: str
    individualPosition: str
    win: bool
    kills: int
    deaths: int
    assists: int
    totalDamageDealtToChampions: int
    totalDamageTaken: int
    goldEarned: int
    visionScore: int
    timeCCingOthers: int
    totalTimeSpentDead: int
    doubleKills: int
    tripleKills: int
    quadraKills: int
    pentaKills: int
    totalMinionsKilled: int
    neutralMinionsKilled: int
    totalDamageDealt: int
    magicDamageDealt: int
    physicalDamageDealt: int
    trueDamageDealt: int
    perks: Perks
    challenges: Dict

@dataclass
class Team:
    teamId: int
    win: bool
    objectives: Dict

@dataclass
class MatchInfo:
    gameId: int
    gameCreation: int
    gameDuration: int
    gameEndTimestamp: int
    gameStartTimestamp: int
    gameMode: str
    gameType: str
    gameVersion: str
    mapId: int
    participants: List[Participant]
    teams: List[Team]
    queueId: int

@dataclass
class MatchMetadata:
    dataVersion: str
    matchId: str
    participants: List[str]

@dataclass
class Match:
    metadata: MatchMetadata
    info: MatchInfo

class StatsAnalyzer:
    def __init__(self):
        self.matches: List[Match] = []
        self.puuid: Optional[str] = None

    def _parse_participant(self, data: Dict) -> Participant:
        """Parse participant data from the match response."""
        return Participant(
            puuid=data['puuid'],
            summonerId=data['summonerId'],
            summonerName=data['summonerName'],
            championId=data['championId'],
            championName=data['championName'],
            teamId=data['teamId'],
            teamPosition=data['teamPosition'],
            individualPosition=data['individualPosition'],
            win=data['win'],
            kills=data['kills'],
            deaths=data['deaths'],
            assists=data['assists'],
            totalDamageDealtToChampions=data['totalDamageDealtToChampions'],
            totalDamageTaken=data['totalDamageTaken'],
            goldEarned=data['goldEarned'],
            visionScore=data['visionScore'],
            timeCCingOthers=data['timeCCingOthers'],
            totalTimeSpentDead=data['totalTimeSpentDead'],
            doubleKills=data['doubleKills'],
            tripleKills=data['tripleKills'],
            quadraKills=data['quadraKills'],
            pentaKills=data['pentaKills'],
            totalMinionsKilled=data['totalMinionsKilled'],
            neutralMinionsKilled=data['neutralMinionsKilled'],
            totalDamageDealt=data['totalDamageDealt'],
            magicDamageDealt=data['magicDamageDealt'],
            physicalDamageDealt=data['physicalDamageDealt'],
            trueDamageDealt=data['trueDamageDealt'],
            perks=self._parse_perks(data['perks']),
            challenges=data['challenges']
        )

    def _parse_perks(self, data: Dict) -> Perks:
        """Parse perks data from the match response."""
        return Perks(
            statPerks=PerkStats(**data['statPerks']),
            styles=[
                PerkStyle(
                    description=style['description'],
                    selections=[
                        PerkStyleSelection(**selection)
                        for selection in style['selections']
                    ],
                    style=style['style']
                )
                for style in data['styles']
            ]
        )

    def _parse_team(self, data: Dict) -> Team:
        """Parse team data from the match response."""
        return Team(
            teamId=data['teamId'],
            win=data['win'],
            objectives=data['objectives']
        )

    def _parse_match(self, data: Dict) -> Match:
        """Parse match data from the API response."""
        return Match(
            metadata=MatchMetadata(**data['metadata']),
            info=MatchInfo(
                gameId=data['info']['gameId'],
                gameCreation=data['info']['gameCreation'],
                gameDuration=data['info']['gameDuration'],
                gameEndTimestamp=data['info']['gameEndTimestamp'],
                gameStartTimestamp=data['info']['gameStartTimestamp'],
                gameMode=data['info']['gameMode'],
                gameType=data['info']['gameType'],
                gameVersion=data['info']['gameVersion'],
                mapId=data['info']['mapId'],
                participants=[self._parse_participant(p) for p in data['info']['participants']],
                teams=[self._parse_team(t) for t in data['info']['teams']],
                queueId=data['info']['queueId']
            )
        )

    def add_match(self, match_data: Dict):
        """Add a match to the analyzer."""
        match = self._parse_match(match_data)
        self.matches.append(match)
        
        # Set PUUID if not set and we find it in the participants
        if not self.puuid:
            for participant in match.info.participants:
                if participant.puuid == match_data.get('info', {}).get('participants', [{}])[0].get('puuid'):
                    self.puuid = participant.puuid
                    break

    def get_player_stats(self) -> Dict:
        """Get aggregated stats for the player."""
        if not self.puuid:
            return {
                "total_matches": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0.0,
                "kills": 0,
                "deaths": 0,
                "assists": 0,
                "kda": 0.0,
                "total_damage_dealt": 0,
                "total_damage_taken": 0,
                "total_gold_earned": 0,
                "vision_score": 0,
                "champions_played": {},
                "positions_played": {}
            }

        player_matches = []
        for match in self.matches:
            for participant in match.info.participants:
                if participant.puuid == self.puuid:
                    player_matches.append(participant)
                    break

        if not player_matches:
            return {
                "total_matches": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0.0,
                "kills": 0,
                "deaths": 0,
                "assists": 0,
                "kda": 0.0,
                "total_damage_dealt": 0,
                "total_damage_taken": 0,
                "total_gold_earned": 0,
                "vision_score": 0,
                "champions_played": {},
                "positions_played": {}
            }

        total_matches = len(player_matches)
        wins = sum(1 for p in player_matches if p.win)
        total_kills = sum(p.kills for p in player_matches)
        total_deaths = sum(p.deaths for p in player_matches)
        total_assists = sum(p.assists for p in player_matches)
        
        # Calculate KDA safely
        kda = 0.0
        if total_deaths > 0:
            kda = (total_kills + total_assists) / total_deaths
        elif total_kills + total_assists > 0:
            kda = total_kills + total_assists  # Perfect KDA

        # Calculate win rate safely
        win_rate = (wins / total_matches * 100) if total_matches > 0 else 0.0

        # Calculate champion and position stats
        champions_played = {}
        positions_played = {}
        for participant in player_matches:
            # Update champion stats
            if participant.championName not in champions_played:
                champions_played[participant.championName] = {
                    "games": 0,
                    "wins": 0,
                    "kills": 0,
                    "deaths": 0,
                    "assists": 0
                }
            champ_stats = champions_played[participant.championName]
            champ_stats["games"] += 1
            if participant.win:
                champ_stats["wins"] += 1
            champ_stats["kills"] += participant.kills
            champ_stats["deaths"] += participant.deaths
            champ_stats["assists"] += participant.assists

            # Update position stats
            position = participant.teamPosition
            if position not in positions_played:
                positions_played[position] = {
                    "games": 0,
                    "wins": 0
                }
            pos_stats = positions_played[position]
            pos_stats["games"] += 1
            if participant.win:
                pos_stats["wins"] += 1

        return {
            "total_matches": total_matches,
            "wins": wins,
            "losses": total_matches - wins,
            "win_rate": round(win_rate, 2),
            "kills": total_kills,
            "deaths": total_deaths,
            "assists": total_assists,
            "kda": round(kda, 2),
            "total_damage_dealt": sum(p.totalDamageDealtToChampions for p in player_matches),
            "total_damage_taken": sum(p.totalDamageTaken for p in player_matches),
            "total_gold_earned": sum(p.goldEarned for p in player_matches),
            "vision_score": sum(p.visionScore for p in player_matches),
            "champions_played": champions_played,
            "positions_played": positions_played
        }

    def get_champion_stats(self) -> Dict:
        """Get aggregated statistics for each champion played."""
        if not self.puuid:
            return {}

        champion_stats = {}
        
        for match in self.matches:
            for participant in match.info.participants:
                if participant.puuid == self.puuid:
                    champion = participant.championName
                    if champion not in champion_stats:
                        champion_stats[champion] = {
                            "games_played": 0,
                            "wins": 0,
                            "losses": 0,
                            "kills": 0,
                            "deaths": 0,
                            "assists": 0,
                            "total_damage_dealt": 0,
                            "total_damage_taken": 0,
                            "total_gold_earned": 0,
                            "vision_score": 0,
                            "positions": {}
                        }
                    
                    stats = champion_stats[champion]
                    stats["games_played"] += 1
                    stats["wins"] += 1 if participant.win else 0
                    stats["losses"] += 0 if participant.win else 1
                    stats["kills"] += participant.kills
                    stats["deaths"] += participant.deaths
                    stats["assists"] += participant.assists
                    stats["total_damage_dealt"] += participant.totalDamageDealtToChampions
                    stats["total_damage_taken"] += participant.totalDamageTaken
                    stats["total_gold_earned"] += participant.goldEarned
                    stats["vision_score"] += participant.visionScore
                    
                    # Track positions played
                    position = participant.individualPosition
                    if position not in stats["positions"]:
                        stats["positions"][position] = 0
                    stats["positions"][position] += 1
                    
                    break

        # Calculate averages and rates
        for champion in champion_stats:
            stats = champion_stats[champion]
            games = stats["games_played"]
            
            # Calculate win rate
            stats["win_rate"] = (stats["wins"] / games * 100) if games > 0 else 0
            
            # Calculate KDA
            deaths = stats["deaths"]
            if deaths > 0:
                stats["kda"] = (stats["kills"] + stats["assists"]) / deaths
            else:
                stats["kda"] = stats["kills"] + stats["assists"]
            
            # Calculate averages
            stats["avg_kills"] = stats["kills"] / games if games > 0 else 0
            stats["avg_deaths"] = stats["deaths"] / games if games > 0 else 0
            stats["avg_assists"] = stats["assists"] / games if games > 0 else 0
            stats["avg_damage"] = stats["total_damage_dealt"] / games if games > 0 else 0
            stats["avg_gold"] = stats["total_gold_earned"] / games if games > 0 else 0
            stats["avg_vision"] = stats["vision_score"] / games if games > 0 else 0

        return champion_stats

    def get_match_details(self, match_id: str) -> Optional[Dict]:
        """Get detailed stats for a specific match."""
        for match in self.matches:
            if match.metadata.matchId == match_id:
                for participant in match.info.participants:
                    if participant.puuid == self.puuid:
                        # Calculate KDA safely
                        kda = 0.0
                        if participant.deaths > 0:
                            kda = (participant.kills + participant.assists) / participant.deaths
                        elif participant.kills + participant.assists > 0:
                            kda = participant.kills + participant.assists  # Perfect KDA

                        match_stats = {
                            "champion": participant.championName,
                            "position": participant.teamPosition,
                            "win": participant.win,
                            "kills": participant.kills,
                            "deaths": participant.deaths,
                            "assists": participant.assists,
                            "kda": round(kda, 2),
                            "damage_dealt": participant.totalDamageDealtToChampions,
                            "damage_taken": participant.totalDamageTaken,
                            "gold_earned": participant.goldEarned,
                            "vision_score": participant.visionScore,
                            "time_ccing_others": participant.timeCCingOthers
                        }
                        # Prepare recent match stats (excluding this match)
                        history_stats = []
                        for m in self.matches:
                            if m.metadata.matchId != match_id:
                                for p in m.info.participants:
                                    if p.puuid == self.puuid:
                                        kda_hist = 0.0
                                        if p.deaths > 0:
                                            kda_hist = (p.kills + p.assists) / p.deaths
                                        elif p.kills + p.assists > 0:
                                            kda_hist = p.kills + p.assists
                                        history_stats.append({
                                            "champion": p.championName,
                                            "position": p.teamPosition,
                                            "win": p.win,
                                            "kills": p.kills,
                                            "deaths": p.deaths,
                                            "assists": p.assists,
                                            "kda": round(kda_hist, 2),
                                            "damage_dealt": p.totalDamageDealtToChampions,
                                            "damage_taken": p.totalDamageTaken,
                                            "gold_earned": p.goldEarned,
                                            "vision_score": p.visionScore,
                                            "time_ccing_others": p.timeCCingOthers
                                        })
                        # Only use last 5 matches for context
                        history_stats = history_stats[-5:]
                        suggestion = generate_suggestion(match_stats, history_stats)
                        return {
                            "match_id": match_id,
                            "game_mode": match.info.gameMode,
                            "game_type": match.info.gameType,
                            "game_version": match.info.gameVersion,
                            "game_duration": match.info.gameDuration,
                            "champion": participant.championName,
                            "position": participant.teamPosition,
                            "win": participant.win,
                            "kills": participant.kills,
                            "deaths": participant.deaths,
                            "assists": participant.assists,
                            "kda": round(kda, 2),
                            "damage_dealt": participant.totalDamageDealtToChampions,
                            "damage_taken": participant.totalDamageTaken,
                            "gold_earned": participant.goldEarned,
                            "vision_score": participant.visionScore,
                            "time_ccing_others": participant.timeCCingOthers,
                            "total_time_spent_dead": participant.totalTimeSpentDead,
                            "minions_killed": participant.totalMinionsKilled,
                            "neutral_minions_killed": participant.neutralMinionsKilled,
                            "double_kills": participant.doubleKills,
                            "triple_kills": participant.tripleKills,
                            "quadra_kills": participant.quadraKills,
                            "penta_kills": participant.pentaKills,
                            "challenges": participant.challenges,
                            "analysis": suggestion,
                            "improvement_suggestions": [suggestion] if suggestion else []
                        }
        return None 