"""XGBoost models for match scoring, tier prediction, and win prediction."""

import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json
import logging

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

from .features import MATCH_SCORE_FEATURES, TIER_ORDER, TIER_TO_IDX
from .gpi import compute_gpi

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).parent / "models"


class MatchScorer:
    """XGBoost regressor that scores match performance 0-100."""

    def __init__(self):
        self.model: Optional[xgb.XGBRegressor] = None
        self._load()

    def _load(self):
        path = MODEL_DIR / "match_scorer.json"
        if path.exists() and XGB_AVAILABLE:
            try:
                self.model = xgb.XGBRegressor()
                self.model.load_model(str(path))
                logger.info("Match scorer model loaded")
            except Exception as e:
                logger.warning(f"Failed to load match scorer: {e}")
                self.model = None

    def predict(self, features: Dict[str, float]) -> float:
        """Predict match performance score 0-100."""
        if self.model is not None:
            x = np.array([[features.get(f, 0) for f in MATCH_SCORE_FEATURES]])
            score = float(self.model.predict(x)[0])
            return max(0, min(100, score))

        # Fallback: derive from GPI
        gpi = compute_gpi(features)
        return gpi["overall"]

    @property
    def is_loaded(self) -> bool:
        return self.model is not None


class TierPredictor:
    """XGBoost classifier predicting what tier the performance resembles."""

    def __init__(self):
        self.model: Optional[xgb.XGBClassifier] = None
        self.class_map: Dict[int, str] = {}
        self._load()

    def _load(self):
        path = MODEL_DIR / "tier_predictor.json"
        mapping_path = MODEL_DIR / "tier_classes.json"
        if path.exists() and XGB_AVAILABLE:
            try:
                self.model = xgb.XGBClassifier()
                self.model.load_model(str(path))
                if mapping_path.exists():
                    import json
                    with open(mapping_path) as f:
                        raw = json.load(f)
                    self.class_map = {int(k): v for k, v in raw.items()}
                logger.info("Tier predictor model loaded")
            except Exception as e:
                logger.warning(f"Failed to load tier predictor: {e}")
                self.model = None

    def predict(self, features: Dict[str, float]) -> Tuple[str, float]:
        """Predict tier and confidence.

        Returns (tier_name, confidence_pct).
        """
        if self.model is not None:
            x = np.array([[features.get(f, 0) for f in MATCH_SCORE_FEATURES]])
            proba = self.model.predict_proba(x)[0]
            idx = int(np.argmax(proba))
            confidence = float(proba[idx]) * 100
            tier = self.class_map.get(idx, TIER_ORDER[min(idx, len(TIER_ORDER) - 1)])
            return tier, round(confidence, 1)

        # Fallback: estimate from GPI overall
        gpi = compute_gpi(features)
        overall = gpi["overall"]
        if overall >= 85:
            return "MASTER", 40.0
        elif overall >= 70:
            return "DIAMOND", 40.0
        elif overall >= 55:
            return "PLATINUM", 40.0
        elif overall >= 40:
            return "GOLD", 40.0
        elif overall >= 25:
            return "SILVER", 40.0
        else:
            return "BRONZE", 40.0

    @property
    def is_loaded(self) -> bool:
        return self.model is not None


class WinPredictor:
    """XGBoost classifier predicting win probability."""

    def __init__(self):
        self.model: Optional[xgb.XGBClassifier] = None
        self._load()

    def _load(self):
        path = MODEL_DIR / "win_predictor.json"
        if path.exists() and XGB_AVAILABLE:
            try:
                self.model = xgb.XGBClassifier()
                self.model.load_model(str(path))
                logger.info("Win predictor model loaded")
            except Exception as e:
                logger.warning(f"Failed to load win predictor: {e}")
                self.model = None

    def predict(self, features: Dict[str, float]) -> float:
        """Predict win probability as percentage."""
        if self.model is not None:
            x = np.array([[features.get(f, 0) for f in MATCH_SCORE_FEATURES]])
            proba = self.model.predict_proba(x)[0]
            return round(float(proba[1]) * 100, 1)

        # Fallback: simple heuristic
        kda = features.get("kda", 1.0)
        kp = features.get("kill_participation", 0.5)
        return round(min(max((kda / 5 * 40 + kp * 60), 10), 90), 1)

    @property
    def is_loaded(self) -> bool:
        return self.model is not None


class JaxStatsModels:
    """Container for all XGBoost models — instantiated once at startup."""

    def __init__(self):
        self.match_scorer = MatchScorer()
        self.tier_predictor = TierPredictor()
        self.win_predictor = WinPredictor()

    def score_match(self, features: Dict[str, float]) -> Dict:
        """Full ML scoring for a match."""
        score = self.match_scorer.predict(features)
        tier, tier_confidence = self.tier_predictor.predict(features)
        win_prob = self.win_predictor.predict(features)
        gpi = compute_gpi(features)

        return {
            "performance_score": round(score, 1),
            "predicted_tier": tier,
            "tier_confidence": tier_confidence,
            "win_probability": win_prob,
            "gpi": gpi,
        }

    @property
    def status(self) -> Dict[str, bool]:
        return {
            "match_scorer": self.match_scorer.is_loaded,
            "tier_predictor": self.tier_predictor.is_loaded,
            "win_predictor": self.win_predictor.is_loaded,
        }
