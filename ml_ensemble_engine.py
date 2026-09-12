# -*- coding: utf-8 -*-
"""
================================================================================
VIP STRIKE V35.0 ENTERPRISE - MODULE 6: MULTI-TREE ML ENSEMBLE
================================================================================
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from .config import CONFIG
from .feature_engineering import UltraFeatureExtractor

logger = logging.getLogger("VIPStrikeML")

try:
    import numpy as np
    from sklearn.ensemble import (
        RandomForestClassifier,
        GradientBoostingClassifier,
        ExtraTreesClassifier
    )
    from sklearn.preprocessing import StandardScaler
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

def clamp(val: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, val))

class MachineLearningMegaEnsemble:
    """Random Forest, Gradient Boosting, and Extra Trees Meta-Ensemble."""

    def __init__(self):
        self.is_trained = False
        self.rf = None
        self.gb = None
        self.et = None
        self.scaler = None
        self.confidence_score = 0
        self.last_prediction = None

    def train(self, dataset: List[Dict[str, Any]], extractor: UltraFeatureExtractor) -> bool:
        if not ML_AVAILABLE or len(dataset) < 25:
            self.is_trained = False
            return False

        X, y = extractor.extract_dataset(dataset)
        if len(X) < 20 or len(set(y)) < 2:
            self.is_trained = False
            return False

        try:
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(np.array(X))

            self.rf = RandomForestClassifier(
                n_estimators=120,
                max_depth=7,
                min_samples_split=3,
                random_state=42
            )
            self.rf.fit(X_scaled, np.array(y))

            self.gb = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.05,
                random_state=42
            )
            self.gb.fit(X_scaled, np.array(y))

            self.et = ExtraTreesClassifier(
                n_estimators=100,
                max_depth=6,
                random_state=42
            )
            self.et.fit(X_scaled, np.array(y))

            self.is_trained = True
            return True
        except Exception as e:
            logger.warning(f"Tree Ensemble Training Exception: {e}")
            self.is_trained = False
            return False

    def predict(self, dataset: List[Dict[str, Any]], extractor: UltraFeatureExtractor) -> Tuple[Optional[str], int]:
        if not self.is_trained or not ML_AVAILABLE or self.rf is None or self.gb is None or self.et is None:
            return None, 0

        feat = extractor.extract_latest(dataset)
        if feat is None:
            return None, 0

        try:
            feat_scaled = self.scaler.transform(np.array([feat]))

            rf_p = float(self.rf.predict_proba(feat_scaled)[0][1])
            gb_p = float(self.gb.predict_proba(feat_scaled)[0][1])
            et_p = float(self.et.predict_proba(feat_scaled)[0][1])

            ensemble_prob = (0.40 * rf_p) + (0.35 * gb_p) + (0.25 * et_p)
            pred = "BIG" if ensemble_prob >= 0.50 else "SMALL"
            conviction = abs(ensemble_prob - 0.50) * 2.0
            conf = int(clamp(conviction * 100 + 66, CONFIG.base_confidence_floor, 98))

            self.confidence_score = conf
            self.last_prediction = pred
            return pred, conf
        except Exception:
            return None, 0
