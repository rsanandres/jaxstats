from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import numpy as np
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
        self.raw_matches: List[Dict] = []  # Keep raw data for ML feature extraction
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
        self.raw_matches.append(match_data)

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

    def get_trend_data(self) -> Dict:
        """Compute performance trends over recent matches.

        Returns per-match metrics and trend direction/magnitude for key stats.
        """
        if not self.puuid:
            return {"matches": [], "trends": {}}

        per_match = []
        for match in self.matches:
            for p in match.info.participants:
                if p.puuid == self.puuid:
                    deaths = max(p.deaths, 1)
                    kda = (p.kills + p.assists) / deaths
                    mins = max(match.info.gameDuration / 60, 1)
                    cs = p.totalMinionsKilled + p.neutralMinionsKilled
                    per_match.append({
                        "match_id": match.metadata.matchId,
                        "win": p.win,
                        "kda": round(kda, 2),
                        "kills": p.kills,
                        "deaths": p.deaths,
                        "assists": p.assists,
                        "cs_per_min": round(cs / mins, 1),
                        "damage_dealt": p.totalDamageDealtToChampions,
                        "gold_earned": p.goldEarned,
                        "vision_score": p.visionScore,
                        "champion": p.championName,
                        "game_duration": match.info.gameDuration,
                    })
                    break

        if len(per_match) < 2:
            return {"matches": per_match, "trends": {}}

        # Compute trends: compare first half vs second half
        mid = len(per_match) // 2
        first_half = per_match[:mid]
        second_half = per_match[mid:]

        def avg(lst, key):
            vals = [m[key] for m in lst]
            return np.mean(vals) if vals else 0

        trend_keys = ["kda", "cs_per_min", "damage_dealt", "gold_earned", "vision_score"]
        trends = {}
        for key in trend_keys:
            old = avg(first_half, key)
            new = avg(second_half, key)
            if old > 0:
                change_pct = ((new - old) / old) * 100
            else:
                change_pct = 0
            direction = "improving" if change_pct > 5 else "declining" if change_pct < -5 else "stable"
            trends[key] = {
                "direction": direction,
                "change_pct": round(change_pct, 1),
            }

        # Win streaks
        current_streak = 0
        streak_type = None
        for m in reversed(per_match):
            if streak_type is None:
                streak_type = "win" if m["win"] else "loss"
                current_streak = 1
            elif (m["win"] and streak_type == "win") or (not m["win"] and streak_type == "loss"):
                current_streak += 1
            else:
                break

        trends["streak"] = {"type": streak_type or "none", "count": current_streak}

        return {"matches": per_match, "trends": trends}

    def get_advanced_stats(self) -> Dict:
        """Compute 10 categories of advanced stats from raw match data."""
        if not self.puuid or not self.raw_matches:
            return {}

        entries = []
        for match_raw in self.raw_matches:
            info = match_raw.get("info", {})
            for p in info.get("participants", []):
                if p.get("puuid") == self.puuid:
                    entries.append({
                        "p": p,
                        "challenges": p.get("challenges", {}),
                        "duration": info.get("gameDuration", 0),
                        "timestamp": info.get("gameStartTimestamp", 0),
                        "champion": p.get("championName", "Unknown"),
                    })
                    break

        if not entries:
            return {}

        n = len(entries)

        # ---- 1. Skillshot Accuracy ----
        skillshot_matches = []
        skillshot_by_champ = {}
        for e in entries:
            c = e["challenges"]
            hits = c.get("skillshotsHit", 0)
            uses = c.get("abilityUses", 0)
            champ = e["champion"]
            if uses > 0:
                match_data = {
                    "hits": hits,
                    "uses": uses,
                    "accuracy": round(hits / uses * 100, 1),
                }
                skillshot_matches.append(match_data)
                skillshot_by_champ.setdefault(champ, []).append(match_data)
        skillshot_avg = round(
            np.mean([m["accuracy"] for m in skillshot_matches]), 1
        ) if skillshot_matches else 0

        # Per-champion skillshot breakdown
        skillshot_per_champion = {}
        for champ, matches in skillshot_by_champ.items():
            accuracies = [m["accuracy"] for m in matches]
            skillshot_per_champion[champ] = {
                "games": len(matches),
                "average": round(float(np.mean(accuracies)), 1),
                "total_hits": sum(m["hits"] for m in matches),
                "total_uses": sum(m["uses"] for m in matches),
                "per_game": matches,
            }

        skillshot_accuracy = {
            "per_match": skillshot_matches,
            "average": skillshot_avg,
            "total_hits": sum(m["hits"] for m in skillshot_matches),
            "total_uses": sum(m["uses"] for m in skillshot_matches),
            "per_champion": skillshot_per_champion,
        }

        # ---- 2. Lane Dominance Score (0-100) ----
        lane_scores = []
        for e in entries:
            c = e["challenges"]
            cs_adv = min(c.get("maxCsAdvantageOnLaneOpponent", 0) / 30, 1) * 20
            lvl_lead = min(c.get("maxLevelLeadLaneOpponent", 0) / 3, 1) * 15
            plates = min(c.get("turretPlatesTaken", 0) / 5, 1) * 20
            early_gold = 10 if c.get("earlyLaningPhaseGoldExpAdvantage", 0) > 0 else 0
            late_gold = 15 if c.get("laningPhaseGoldExpAdvantage", 0) > 0 else 0
            solo = min(c.get("soloKills", 0) / 3, 1) * 20
            score = min(cs_adv + lvl_lead + plates + early_gold + late_gold + solo, 100)
            lane_scores.append(round(score, 1))
        lane_dominance = {
            "per_match": lane_scores,
            "average": round(np.mean(lane_scores), 1) if lane_scores else 0,
        }

        # ---- 3. Clutch Score (0-100) ----
        clutch_scores = []
        for e in entries:
            c = e["challenges"]
            score = 0
            score += min(c.get("survivedSingleDigitHpCount", 0), 5) * 5
            score += min(c.get("outnumberedKills", 0), 3) * 8
            score += c.get("epicMonsterSteals", 0) * 15
            score += c.get("epicMonsterStolenWithoutSmite", 0) * 5
            score += c.get("multikillsAfterAggressiveFlash", 0) * 10
            score += 15 if c.get("perfectGame", 0) else 0
            score += min(c.get("legendaryCount", 0), 2) * 10
            score += min(c.get("saveAllyFromDeath", 0), 3) * 5
            clutch_scores.append(min(round(score, 1), 100))
        clutch_factor = {
            "per_match": clutch_scores,
            "average": round(np.mean(clutch_scores), 1) if clutch_scores else 0,
        }

        # ---- 4. Communication Profile ----
        ping_types = [
            "allInPings", "assistMePings", "commandPings", "dangerPings",
            "enemyMissingPings", "enemyVisionPings", "getBackPings",
            "holdPings", "needVisionPings", "onMyWayPings", "pushPings",
        ]
        total_pings = {pt: 0 for pt in ping_types}
        total_minutes = 0
        for e in entries:
            p = e["p"]
            mins = max(e["duration"] / 60, 1)
            total_minutes += mins
            for pt in ping_types:
                total_pings[pt] += p.get(pt, 0)
        pings_per_min = round(sum(total_pings.values()) / max(total_minutes, 1), 2)

        total_all = sum(total_pings.values())
        if total_all == 0 or pings_per_min < 0.5:
            archetype = "Quiet"
        else:
            info_pings = total_pings["commandPings"] + total_pings["onMyWayPings"] + total_pings["pushPings"]
            danger_pings = total_pings["dangerPings"] + total_pings["getBackPings"] + total_pings["enemyMissingPings"]
            if info_pings > danger_pings and info_pings / max(total_all, 1) > 0.4:
                archetype = "Shotcaller"
            elif danger_pings > info_pings and danger_pings / max(total_all, 1) > 0.4:
                archetype = "Danger Pinger"
            else:
                archetype = "Communicator"

        communication = {
            "pings": total_pings,
            "pings_per_min": pings_per_min,
            "archetype": archetype,
            "total_pings": total_all,
        }

        # ---- 5. Vision Quality ----
        vision_entries = []
        for e in entries:
            c = e["challenges"]
            vision_entries.append({
                "control_ward_coverage": round(c.get("controlWardTimeCoverageInRiverOrEnemyHalf", 0) * 100, 1),
                "vision_advantage": round(c.get("visionScoreAdvantageLaneOpponent", 0), 1),
                "unseen_recalls": c.get("unseenRecalls", 0),
                "two_wards_one_sweeper": c.get("twoWardsOneSweeperCount", 0),
                "ward_takedowns_before_20": c.get("wardTakedownsBefore20M", 0),
            })
        vision_quality = {
            "per_match": vision_entries,
            "avg_control_ward_coverage": round(np.mean([v["control_ward_coverage"] for v in vision_entries]), 1) if vision_entries else 0,
            "avg_vision_advantage": round(np.mean([v["vision_advantage"] for v in vision_entries]), 1) if vision_entries else 0,
            "total_unseen_recalls": sum(v["unseen_recalls"] for v in vision_entries),
            "total_ward_takedowns_early": sum(v["ward_takedowns_before_20"] for v in vision_entries),
        }

        # ---- 6. Counter-Jungle (JUNGLE games only) ----
        jungle_entries = []
        for e in entries:
            p = e["p"]
            pos = p.get("teamPosition", "") or p.get("individualPosition", "")
            if pos.upper() == "JUNGLE":
                c = e["challenges"]
                jungle_entries.append({
                    "buffs_stolen": c.get("buffsStolen", 0),
                    "enemy_jungle_kills": c.get("enemyJungleMonsterKills", 0),
                    "more_enemy_jungle": c.get("moreEnemyJungleThanOpponent", 0),
                    "epic_kills_30s": c.get("epicMonsterKillsWithin30SecondsOfSpawn", 0),
                    "jungle_cs_before_10": c.get("jungleCsBefore10Minutes", 0),
                    "initial_buff_count": c.get("initialBuffCount", 0),
                    "initial_crab_count": c.get("initialCrabCount", 0),
                    "scuttle_kills": c.get("scuttleCrabKills", 0),
                })
        counter_jungle = {
            "games": len(jungle_entries),
            "per_match": jungle_entries,
            "avg_buffs_stolen": round(np.mean([j["buffs_stolen"] for j in jungle_entries]), 1) if jungle_entries else 0,
            "avg_enemy_jungle_kills": round(np.mean([j["enemy_jungle_kills"] for j in jungle_entries]), 1) if jungle_entries else 0,
        } if jungle_entries else None

        # ---- 7. Tank/Frontline (tanky games: damageSelfMitigated > 15000) ----
        tank_entries = []
        for e in entries:
            p = e["p"]
            c = e["challenges"]
            mitigated = p.get("damageSelfMitigated", 0)
            if mitigated > 15000:
                tank_entries.append({
                    "killed_champ_full_team_survived": c.get("killedChampTookFullTeamDamageSurvived", 0),
                    "took_large_damage_survived": c.get("tookLargeDamageSurvived", 0),
                    "survived_three_immobilizes": c.get("survivedThreeImmobilizesInFight", 0),
                    "damage_mitigated": mitigated,
                })
        tank_frontline = {
            "games": len(tank_entries),
            "per_match": tank_entries,
            "avg_damage_mitigated": round(np.mean([t["damage_mitigated"] for t in tank_entries]), 0) if tank_entries else 0,
        } if tank_entries else None

        # ---- 8. Support Value (UTILITY/SUPPORT games only) ----
        support_entries = []
        for e in entries:
            p = e["p"]
            pos = p.get("teamPosition", "") or p.get("individualPosition", "")
            if pos.upper() in ("UTILITY", "SUPPORT"):
                c = e["challenges"]
                support_entries.append({
                    "shields_on_teammates": p.get("totalDamageShieldedOnTeammates", 0),
                    "heals_on_teammates": p.get("totalHealsOnTeammates", 0),
                    "save_ally": c.get("saveAllyFromDeath", 0),
                    "effective_healing_shielding": c.get("effectiveHealAndShielding", 0),
                    "quest_completed_on_time": c.get("completeSupportQuestInTime", 0),
                })
        support_value = {
            "games": len(support_entries),
            "per_match": support_entries,
            "avg_shields": round(np.mean([s["shields_on_teammates"] for s in support_entries]), 0) if support_entries else 0,
            "avg_heals": round(np.mean([s["heals_on_teammates"] for s in support_entries]), 0) if support_entries else 0,
        } if support_entries else None

        # ---- 9. Efficiency Ratios ----
        efficiency_entries = []
        for e in entries:
            p = e["p"]
            dmg = p.get("totalDamageDealtToChampions", 0)
            gold_spent = p.get("goldSpent", 0)
            gold_earned = p.get("goldEarned", 0)
            kills = p.get("kills", 0)
            assists = p.get("assists", 0)
            deaths = max(p.get("deaths", 0), 1)
            cc = p.get("timeCCingOthers", 0)
            efficiency_entries.append({
                "damage_per_gold_spent": round(dmg / max(gold_spent, 1), 2),
                "gold_efficiency": round(gold_spent / max(gold_earned, 1) * 100, 1),
                "kill_participation_ratio": round(kills / max(kills + assists, 1) * 100, 1),
                "cc_per_death": round(cc / deaths, 1),
                "damage_per_gold_earned": round(dmg / max(gold_earned, 1), 2),
            })
        efficiency = {
            "per_match": efficiency_entries,
            "avg_damage_per_gold_spent": round(np.mean([x["damage_per_gold_spent"] for x in efficiency_entries]), 2) if efficiency_entries else 0,
            "avg_gold_efficiency": round(np.mean([x["gold_efficiency"] for x in efficiency_entries]), 1) if efficiency_entries else 0,
            "avg_kill_participation_ratio": round(np.mean([x["kill_participation_ratio"] for x in efficiency_entries]), 1) if efficiency_entries else 0,
            "avg_cc_per_death": round(np.mean([x["cc_per_death"] for x in efficiency_entries]), 1) if efficiency_entries else 0,
            "avg_damage_per_gold_earned": round(np.mean([x["damage_per_gold_earned"] for x in efficiency_entries]), 2) if efficiency_entries else 0,
        }

        # ---- 10. Cross-Match Analytics ----
        sorted_entries = sorted(entries, key=lambda e: e["timestamp"])

        # Tilt detection: win rate after wins vs after losses
        after_win_results = []
        after_loss_results = []
        for i in range(1, len(sorted_entries)):
            prev_win = sorted_entries[i - 1]["p"].get("win", False)
            curr_win = sorted_entries[i]["p"].get("win", False)
            if prev_win:
                after_win_results.append(curr_win)
            else:
                after_loss_results.append(curr_win)
        wr_after_win = round(sum(after_win_results) / len(after_win_results) * 100, 1) if after_win_results else None
        wr_after_loss = round(sum(after_loss_results) / len(after_loss_results) * 100, 1) if after_loss_results else None

        # Time of Day: group by 4-hour UTC buckets
        bucket_labels = ["00-04", "04-08", "08-12", "12-16", "16-20", "20-24"]
        time_buckets = {label: {"games": 0, "wins": 0} for label in bucket_labels}
        for e in sorted_entries:
            ts = e["timestamp"]
            if ts > 0:
                hour = datetime.utcfromtimestamp(ts / 1000).hour
                bucket_idx = hour // 4
                label = bucket_labels[bucket_idx]
                time_buckets[label]["games"] += 1
                if e["p"].get("win", False):
                    time_buckets[label]["wins"] += 1
        time_of_day = {}
        for label, data in time_buckets.items():
            if data["games"] > 0:
                time_of_day[label] = {
                    "games": data["games"],
                    "wins": data["wins"],
                    "win_rate": round(data["wins"] / data["games"] * 100, 1),
                }

        # Surrender stats
        surrenders = 0
        early_surrenders = 0
        for e in entries:
            p = e["p"]
            if p.get("gameEndedInSurrender", False):
                surrenders += 1
            if p.get("gameEndedInEarlySurrender", False):
                early_surrenders += 1

        cross_match = {
            "tilt_detection": {
                "wr_after_win": wr_after_win,
                "wr_after_loss": wr_after_loss,
                "games_after_win": len(after_win_results),
                "games_after_loss": len(after_loss_results),
            },
            "time_of_day": time_of_day,
            "surrender_stats": {
                "total_surrenders": surrenders,
                "early_surrenders": early_surrenders,
                "total_games": n,
                "surrender_rate": round(surrenders / n * 100, 1) if n > 0 else 0,
            },
        }

        return {
            "skillshot_accuracy": skillshot_accuracy,
            "lane_dominance": lane_dominance,
            "clutch_factor": clutch_factor,
            "communication": communication,
            "vision_quality": vision_quality,
            "counter_jungle": counter_jungle,
            "tank_frontline": tank_frontline,
            "support_value": support_value,
            "efficiency": efficiency,
            "cross_match": cross_match,
        }