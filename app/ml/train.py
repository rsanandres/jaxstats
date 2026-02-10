"""Training pipeline for all XGBoost models.

Usage: python -m app.ml.train
Trains on cached match data from data/ directory.
Saves models to app/ml/models/ as .json files.
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
import logging

import xgboost as xgb
from sklearn.model_selection import train_test_split

from .features import (
    extract_all_participants,
    MATCH_SCORE_FEATURES,
    TIER_ORDER,
    TIER_TO_IDX,
)
from .gpi import compute_gpi

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
MODEL_DIR = Path(__file__).parent / "models"


def load_all_matches() -> List[dict]:
    """Load all cached match JSON files."""
    matches = []
    for f in sorted(DATA_DIR.glob("match_*.json")):
        try:
            with open(f) as fh:
                matches.append(json.load(fh))
        except Exception as e:
            logger.warning(f"Skipping {f.name}: {e}")
    logger.info(f"Loaded {len(matches)} matches")
    return matches


def build_dataset(matches: List[dict]) -> Tuple[List[Dict], List[float], List[float]]:
    """Extract features and labels from all matches.

    Returns:
        features_list: list of feature dicts (one per participant per match)
        scores: synthetic performance scores (labels for match scorer)
        wins: 0/1 labels for win predictor
    """
    features_list = []
    scores = []
    wins = []

    for match in matches:
        participants = extract_all_participants(match)
        for p in participants:
            # Synthetic score from GPI as training target
            gpi = compute_gpi(p)
            score = gpi["overall"]

            # Bonus for winning
            if p["win"] > 0.5:
                score = min(100, score + 5)
            else:
                score = max(0, score - 5)

            features_list.append(p)
            scores.append(score)
            wins.append(p["win"])

    logger.info(f"Built dataset: {len(features_list)} samples from {len(matches)} matches")
    return features_list, scores, wins


def features_to_array(features_list: List[Dict], feature_names: List[str]) -> np.ndarray:
    """Convert feature dicts to numpy array for given feature names."""
    return np.array([[f.get(name, 0) for name in feature_names] for f in features_list])


def train_match_scorer(features_list: List[Dict], scores: List[float]):
    """Train the match performance scorer."""
    X = features_to_array(features_list, MATCH_SCORE_FEATURES)
    y = np.array(scores)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        random_state=42,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    logger.info(f"Match scorer — train R²: {train_score:.3f}, test R²: {test_score:.3f}")

    path = MODEL_DIR / "match_scorer.json"
    model.save_model(str(path))
    logger.info(f"Saved match scorer to {path}")


def derive_tier_labels(features_list: List[Dict], scores: List[float]) -> List[int]:
    """Derive tier labels from performance scores.

    Maps score ranges to tier indices:
    0-10: IRON, 10-20: BRONZE, 20-35: SILVER, 35-50: GOLD,
    50-60: PLATINUM, 60-70: EMERALD, 70-80: DIAMOND,
    80-88: MASTER, 88-95: GRANDMASTER, 95+: CHALLENGER
    """
    thresholds = [10, 20, 35, 50, 60, 70, 80, 88, 95]
    labels = []
    for s in scores:
        tier = 0
        for i, t in enumerate(thresholds):
            if s >= t:
                tier = i + 1
        labels.append(min(tier, len(TIER_ORDER) - 1))
    return labels


def train_tier_predictor(features_list: List[Dict], scores: List[float]):
    """Train the tier prediction classifier."""
    X = features_to_array(features_list, MATCH_SCORE_FEATURES)
    raw_labels = derive_tier_labels(features_list, scores)

    # Remap labels to consecutive 0..N-1 for XGBoost
    unique_tiers = sorted(set(raw_labels))
    tier_map = {old: new for new, old in enumerate(unique_tiers)}
    y = np.array([tier_map[l] for l in raw_labels])

    # Save the reverse mapping so the predictor can map back to tier names
    reverse_map = {new: TIER_ORDER[old] for old, new in tier_map.items()}

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    n_classes = len(unique_tiers)
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        num_class=n_classes,
        objective="multi:softprob",
        random_state=42,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    train_acc = model.score(X_train, y_train)
    test_acc = model.score(X_test, y_test)
    logger.info(f"Tier predictor — train acc: {train_acc:.3f}, test acc: {test_acc:.3f}")

    path = MODEL_DIR / "tier_predictor.json"
    model.save_model(str(path))

    # Save the tier class mapping
    mapping_path = MODEL_DIR / "tier_classes.json"
    with open(mapping_path, "w") as f:
        json.dump({str(k): v for k, v in reverse_map.items()}, f)

    logger.info(f"Saved tier predictor to {path} ({n_classes} classes)")


def train_win_predictor(features_list: List[Dict], wins: List[float]):
    """Train the win prediction classifier."""
    X = features_to_array(features_list, MATCH_SCORE_FEATURES)
    y = np.array(wins, dtype=int)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        random_state=42,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    train_acc = model.score(X_train, y_train)
    test_acc = model.score(X_test, y_test)
    logger.info(f"Win predictor — train acc: {train_acc:.3f}, test acc: {test_acc:.3f}")

    path = MODEL_DIR / "win_predictor.json"
    model.save_model(str(path))
    logger.info(f"Saved win predictor to {path}")


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    matches = load_all_matches()
    if not matches:
        logger.error("No match data found in data/ directory")
        return

    features_list, scores, wins = build_dataset(matches)

    logger.info("Training match scorer...")
    train_match_scorer(features_list, scores)

    logger.info("Training tier predictor...")
    train_tier_predictor(features_list, scores)

    logger.info("Training win predictor...")
    train_win_predictor(features_list, wins)

    logger.info("All models trained successfully!")


if __name__ == "__main__":
    main()
