"""Centralized feature extraction from raw Riot match data."""

import numpy as np
from typing import Dict, List, Optional


def safe_get(d: dict, *keys, default=0):
    """Safely traverse nested dicts."""
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k, default)
        else:
            return default
    return d if d is not None else default


def extract_participant_features(participant: dict, game_duration_s: int) -> Dict[str, float]:
    """Extract normalized features from a single participant's match data.

    Returns a flat dict of feature_name -> float value.
    """
    c = participant.get("challenges", {})
    mins = max(game_duration_s / 60, 1)

    kills = participant.get("kills", 0)
    deaths = participant.get("deaths", 0)
    assists = participant.get("assists", 0)
    kda = (kills + assists) / max(deaths, 1)

    cs = participant.get("totalMinionsKilled", 0) + participant.get("neutralMinionsKilled", 0)
    cs_per_min = cs / mins

    gold = participant.get("goldEarned", 0)
    gold_per_min = gold / mins

    dmg_dealt = participant.get("totalDamageDealtToChampions", 0)
    dmg_taken = participant.get("totalDamageTaken", 0)
    dmg_mitigated = participant.get("damageSelfMitigated", 0)
    dmg_per_min = dmg_dealt / mins

    vision_score = participant.get("visionScore", 0)
    wards_placed = participant.get("wardsPlaced", 0)
    wards_killed = participant.get("wardsKilled", 0)
    control_wards = participant.get("detectorWardsPlaced", 0)
    vision_per_min = safe_get(c, "visionScorePerMinute", default=0)

    kill_participation = safe_get(c, "killParticipation", default=0)
    team_dmg_pct = safe_get(c, "teamDamagePercentage", default=0)
    dmg_taken_pct = safe_get(c, "damageTakenOnTeamPercentage", default=0)

    solo_kills = safe_get(c, "soloKills", default=0)
    multikills = safe_get(c, "multikills", default=0)
    killing_sprees = participant.get("killingSprees", 0)

    turret_takedowns = safe_get(c, "turretTakedowns", default=0)
    dragon_takedowns = safe_get(c, "dragonTakedowns", default=0)
    baron_takedowns = safe_get(c, "baronTakedowns", default=0)
    rift_herald_takedowns = safe_get(c, "riftHeraldTakedowns", default=0)

    obj_dmg = participant.get("damageDealtToObjectives", 0)
    obj_dmg_per_min = obj_dmg / mins

    time_dead = participant.get("totalTimeSpentDead", 0)
    time_dead_pct = time_dead / max(game_duration_s, 1)
    longest_living = participant.get("longestTimeSpentLiving", 0)

    cc_score = participant.get("timeCCingOthers", 0)
    immobilizations = safe_get(c, "enemyChampionImmobilizations", default=0)

    skillshots_hit = safe_get(c, "skillshotsHit", default=0)
    skillshots_dodged = safe_get(c, "skillshotsDodged", default=0)
    ability_uses = safe_get(c, "abilityUses", default=0)

    save_ally = safe_get(c, "saveAllyFromDeath", default=0)
    heal_shield = safe_get(c, "effectiveHealAndShielding", default=0)

    survived_low_hp = safe_get(c, "survivedSingleDigitHpCount", default=0)
    survived_3cc = safe_get(c, "survivedThreeImmobilizesInFight", default=0)
    outnumbered_kills = safe_get(c, "outnumberedKills", default=0)

    lane_cs_10 = safe_get(c, "laneMinionsFirst10Minutes", default=0)
    takedowns_first_x = safe_get(c, "takedownsFirstXMinutes", default=0)

    return {
        # Core
        "kills": kills,
        "deaths": deaths,
        "assists": assists,
        "kda": kda,
        "win": 1.0 if participant.get("win", False) else 0.0,

        # Farming
        "cs": cs,
        "cs_per_min": cs_per_min,
        "gold_per_min": gold_per_min,
        "gold_earned": gold,
        "lane_cs_10": lane_cs_10,

        # Vision
        "vision_score": vision_score,
        "vision_per_min": vision_per_min,
        "wards_placed": wards_placed,
        "wards_killed": wards_killed,
        "control_wards": control_wards,

        # Aggression
        "dmg_per_min": dmg_per_min,
        "dmg_dealt": dmg_dealt,
        "kill_participation": kill_participation,
        "solo_kills": solo_kills,
        "takedowns_first_x": takedowns_first_x,

        # Fighting
        "team_dmg_pct": team_dmg_pct,
        "multikills": multikills,
        "killing_sprees": killing_sprees,
        "skillshots_hit": skillshots_hit,
        "ability_uses": ability_uses,

        # Survivability
        "dmg_taken": dmg_taken,
        "dmg_mitigated": dmg_mitigated,
        "dmg_taken_pct": dmg_taken_pct,
        "time_dead_pct": time_dead_pct,
        "longest_living": longest_living,
        "survived_low_hp": survived_low_hp,
        "survived_3cc": survived_3cc,

        # Objectives
        "turret_takedowns": turret_takedowns,
        "dragon_takedowns": dragon_takedowns,
        "baron_takedowns": baron_takedowns,
        "rift_herald_takedowns": rift_herald_takedowns,
        "obj_dmg_per_min": obj_dmg_per_min,

        # Utility
        "cc_score": cc_score,
        "immobilizations": immobilizations,
        "save_ally": save_ally,
        "heal_shield": heal_shield,
        "outnumbered_kills": outnumbered_kills,
        "skillshots_dodged": skillshots_dodged,
    }


# Feature subsets for each GPI skill
GPI_FEATURE_SETS = {
    "farming": ["cs_per_min", "gold_per_min", "lane_cs_10", "gold_earned"],
    "vision": ["vision_score", "vision_per_min", "wards_placed", "wards_killed", "control_wards"],
    "aggression": ["dmg_per_min", "kill_participation", "solo_kills", "takedowns_first_x", "dmg_dealt"],
    "fighting": ["kda", "team_dmg_pct", "multikills", "killing_sprees", "skillshots_hit"],
    "survivability": ["time_dead_pct", "longest_living", "survived_low_hp", "survived_3cc", "dmg_mitigated"],
    "objectives": ["turret_takedowns", "dragon_takedowns", "baron_takedowns", "rift_herald_takedowns", "obj_dmg_per_min"],
    "consistency": ["kda", "cs_per_min", "vision_score", "dmg_per_min", "gold_per_min"],
    "versatility": [],  # Computed differently — across matches, not per-match
}

# All features used for the overall XGBoost match score model
MATCH_SCORE_FEATURES = [
    "kda", "kill_participation", "cs_per_min", "gold_per_min",
    "dmg_per_min", "team_dmg_pct", "vision_per_min",
    "turret_takedowns", "dragon_takedowns", "baron_takedowns",
    "time_dead_pct", "obj_dmg_per_min", "solo_kills",
    "multikills", "skillshots_hit", "survived_3cc",
    "outnumbered_kills", "cc_score", "heal_shield",
]

# Tier labels
TIER_ORDER = [
    "IRON", "BRONZE", "SILVER", "GOLD", "PLATINUM",
    "EMERALD", "DIAMOND", "MASTER", "GRANDMASTER", "CHALLENGER"
]
TIER_TO_IDX = {t: i for i, t in enumerate(TIER_ORDER)}


def extract_all_participants(match_data: dict) -> List[Dict[str, float]]:
    """Extract features for all 10 participants in a match."""
    info = match_data.get("info", {})
    duration = info.get("gameDuration", 0)
    participants = info.get("participants", [])
    results = []
    for p in participants:
        feats = extract_participant_features(p, duration)
        feats["game_duration_min"] = duration / 60
        feats["champion_name"] = p.get("championName", "Unknown")
        feats["position"] = p.get("teamPosition", "NONE")
        feats["puuid"] = p.get("puuid", "")
        results.append(feats)
    return results
