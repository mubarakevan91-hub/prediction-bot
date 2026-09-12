# -*- coding: utf-8 -*-
"""
================================================================================
VIP STRIKE V35.0 ENTERPRISE - MODULE 5: 4-LAYER MLP DEEP NEURAL NETWORK
================================================================================
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from .config import CONFIG
from .feature_engineering import UltraFeatureExtractor

logger = logging.getLogger("VIPStrikeNeural")

try:
    import numpy as np
    from sklearn.neural_network import MLPClassifier
    from sklearn.preprocessing import StandardScaler
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

def clamp(val: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, val))

class DeepNeuralEngineV35:
    """High-Capacity 4-Layer Multi-Layer Perceptron (256 -> 128 -> 64 -> 32)."""

    def __init__(self):
        self.is_trained = False
        self.scaler = None
        self.model = None
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

            self.model = MLPClassifier(
                hidden_layer_sizes=(256, 128, 64, 32),
                activation="relu",
                solver="adam",
                alpha=0.0005,
                learning_rate="adaptive",
                learning_rate_init=0.003,
                max_iter=300,
                random_state=42,
                early_stopping=True,
                n_iter_no_change=15
            )
            self.model.fit(X_scaled, np.array(y))
            self.is_trained = True
            return True
        except Exception as e:
            logger.warning(f"MLP-Ultra Training Exception: {e}")
            self.is_trained = False
            return False

    def predict(self, dataset: List[Dict[str, Any]], extractor: UltraFeatureExtractor) -> Tuple[Optional[str], int]:
        if not self.is_trained or not ML_AVAILABLE or self.model is None or self.scaler is None:
            return None, 0

        feat = extractor.extract_latest(dataset)
        if feat is None:
            return None, 0

        try:
            feat_scaled = self.scaler.transform(np.array([feat]))
            probs = self.model.predict_proba(feat_scaled)[0]
            prob_big = float(probs[1]) if len(probs) > 1 else float(probs[0])

            pred = "BIG" if prob_big >= 0.50 else "SMALL"
            conviction = abs(prob_big - 0.50) * 2.0
            conf = int(clamp(conviction * 100 + 67, CONFIG.base_confidence_floor, CONFIG.base_confidence_ceiling))

            self.confidence_score = conf
            self.last_prediction = pred
            return pred, conf
        except Exception:
            return None, 0
