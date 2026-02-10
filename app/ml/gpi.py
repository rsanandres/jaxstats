"""GPI (Gamer Performance Index) — Mobalytics-style 8-skill scoring.

Each skill is scored 0-100 using weighted formulas derived from match features.
When enough data is collected, XGBoost regressors can be trained for each skill.
For now, formula-based scoring provides instant results without training.
"""

import numpy as np
from typing import Dict, List, Optional
from pathlib import Path
import json
import logging

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

from .features import extract_participant_features, GPI_FEATURE_SETS

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).parent / "models"


def _clamp(val: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, val))


def score_farming(f: Dict[str, float]) -> float:
    """Score farming ability 0-100."""
    cs_score = min(f.get("cs_per_min", 0) / 8.0, 1.0) * 40
    gold_score = min(f.get("gold_per_min", 0) / 500, 1.0) * 30
    lane_cs = min(f.get("lane_cs_10", 0) / 80, 1.0) * 30
    return _clamp(cs_score + gold_score + lane_cs)


def score_vision(f: Dict[str, float]) -> float:
    """Score vision control 0-100."""
    vs = min(f.get("vision_per_min", 0) / 1.5, 1.0) * 30
    wp = min(f.get("wards_placed", 0) / 15, 1.0) * 25
    wk = min(f.get("wards_killed", 0) / 8, 1.0) * 25
    cw = min(f.get("control_wards", 0) / 4, 1.0) * 20
    return _clamp(vs + wp + wk + cw)


def score_aggression(f: Dict[str, float]) -> float:
    """Score aggression 0-100."""
    dpm = min(f.get("dmg_per_min", 0) / 800, 1.0) * 30
    kp = f.get("kill_participation", 0) * 30
    solo = min(f.get("solo_kills", 0) / 3, 1.0) * 20
    early = min(f.get("takedowns_first_x", 0) / 10, 1.0) * 20
    return _clamp(dpm + kp + solo + early)


def score_fighting(f: Dict[str, float]) -> float:
    """Score teamfighting 0-100."""
    kda_score = min(f.get("kda", 0) / 5.0, 1.0) * 30
    tdp = f.get("team_dmg_pct", 0) * 100 * 0.3
    multi = min(f.get("multikills", 0) / 3, 1.0) * 20
    sprees = min(f.get("killing_sprees", 0) / 3, 1.0) * 20
    return _clamp(kda_score + tdp + multi + sprees)


def score_survivability(f: Dict[str, float]) -> float:
    """Score survivability 0-100."""
    death_penalty = f.get("time_dead_pct", 0) * 100
    alive_bonus = min(f.get("longest_living", 0) / 600, 1.0) * 30
    low_hp = min(f.get("survived_low_hp", 0) / 3, 1.0) * 15
    tank_cc = min(f.get("survived_3cc", 0) / 5, 1.0) * 15
    mitigate = min(f.get("dmg_mitigated", 0) / 20000, 1.0) * 15
    base = 25 + alive_bonus + low_hp + tank_cc + mitigate
    return _clamp(base - death_penalty)


def score_objectives(f: Dict[str, float]) -> float:
    """Score objective control 0-100."""
    turret = min(f.get("turret_takedowns", 0) / 4, 1.0) * 25
    dragon = min(f.get("dragon_takedowns", 0) / 3, 1.0) * 25
    baron = min(f.get("baron_takedowns", 0) / 2, 1.0) * 25
    obj_dmg = min(f.get("obj_dmg_per_min", 0) / 400, 1.0) * 25
    return _clamp(turret + dragon + baron + obj_dmg)


SKILL_SCORERS = {
    "farming": score_farming,
    "vision": score_vision,
    "aggression": score_aggression,
    "fighting": score_fighting,
    "survivability": score_survivability,
    "objectives": score_objectives,
}


def compute_gpi(features: Dict[str, float]) -> Dict[str, float]:
    """Compute all 8 GPI skill scores from extracted features.

    Returns dict with skill -> score (0-100) plus overall.
    Consistency and versatility require multi-match data,
    so they default to 50 when called per-match.
    """
    scores = {}
    for skill, scorer in SKILL_SCORERS.items():
        scores[skill] = round(scorer(features), 1)

    # Consistency and versatility are multi-match — default for single match
    scores["consistency"] = 50.0
    scores["versatility"] = 50.0

    # Overall GPI = weighted average
    weights = {
        "farming": 0.15, "vision": 0.10, "aggression": 0.15,
        "fighting": 0.20, "survivability": 0.15, "objectives": 0.15,
        "consistency": 0.05, "versatility": 0.05,
    }
    overall = sum(scores[k] * weights[k] for k in weights)
    scores["overall"] = round(overall, 1)

    return scores


def compute_consistency(match_features_list: List[Dict[str, float]]) -> float:
    """Score consistency across multiple matches (0-100).
    Lower variance = higher score.
    """
    if len(match_features_list) < 2:
        return 50.0

    metrics = ["kda", "cs_per_min", "vision_per_min", "dmg_per_min"]
    cvs = []
    for m in metrics:
        vals = [f.get(m, 0) for f in match_features_list]
        mean = np.mean(vals)
        std = np.std(vals)
        cv = std / max(mean, 0.01)
        cvs.append(cv)

    avg_cv = np.mean(cvs)
    # Lower CV = more consistent = higher score
    # CV of 0 = 100, CV of 1.0 = 0
    return _clamp(100 * (1 - min(avg_cv, 1.0)))


def compute_versatility(match_features_list: List[Dict[str, float]]) -> float:
    """Score versatility across multiple matches (0-100).
    More unique champions/positions = higher score.
    """
    if not match_features_list:
        return 50.0

    champions = set()
    positions = set()
    for f in match_features_list:
        champions.add(f.get("champion_name", ""))
        positions.add(f.get("position", ""))

    n = len(match_features_list)
    champ_ratio = len(champions) / max(n, 1)
    pos_count = len(positions - {""})

    champ_score = min(champ_ratio, 1.0) * 60
    pos_score = min(pos_count / 4, 1.0) * 40
    return _clamp(champ_score + pos_score)


def compute_full_gpi(match_features_list: List[Dict[str, float]]) -> Dict[str, float]:
    """Compute full GPI including consistency/versatility from multiple matches.

    Takes a list of feature dicts (one per match for the same player).
    Returns averaged GPI with proper consistency/versatility.
    """
    if not match_features_list:
        return {k: 0.0 for k in list(SKILL_SCORERS.keys()) + ["consistency", "versatility", "overall"]}

    # Average per-match GPI scores
    all_scores = [compute_gpi(f) for f in match_features_list]
    avg = {}
    for key in all_scores[0]:
        avg[key] = round(np.mean([s[key] for s in all_scores]), 1)

    # Replace with real multi-match metrics
    avg["consistency"] = round(compute_consistency(match_features_list), 1)
    avg["versatility"] = round(compute_versatility(match_features_list), 1)

    # Recompute overall with real values
    weights = {
        "farming": 0.15, "vision": 0.10, "aggression": 0.15,
        "fighting": 0.20, "survivability": 0.15, "objectives": 0.15,
        "consistency": 0.05, "versatility": 0.05,
    }
    avg["overall"] = round(sum(avg[k] * weights[k] for k in weights), 1)

    return avg
