# -*- coding: utf-8 -*-
"""
================================================================================
VIP STRIKE V35.0 ENTERPRISE - MODULE 9: RUSSIAN PREDICTION ENGINE V35
================================================================================
"""

from collections import defaultdict
from typing import List, Dict, Any, Tuple, Optional
from .config import CONFIG

def clamp(val: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, val))

class RussianPredictionEngineV35:
    """Russian Algorithmic Core with Exponential Recency Decay and Trend Matrix."""

    def __init__(self):
        self.markov4 = defaultdict(lambda: [0, 0])
        self.markov3 = defaultdict(lambda: [0, 0])
        self.markov2 = defaultdict(lambda: [0, 0])
        self.streak_profile = defaultdict(lambda: [0, 0])
        self.trained = False
        self.depth = 0
        self.base_rate_big = 0.5
        self.recent_bias_big = 0.5
        self.alternation_score = 0.5
        self.confidence_score = 0
        self.last_prediction = None
        self.debug: Dict[str, Any] = {}

    def train(self, dataset: List[Dict[str, Any]]) -> bool:
        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        n = len(seq)
        if n < 10:
            self.trained = False
            return False

        self.markov4.clear()
        self.markov3.clear()
        self.markov2.clear()
        self.streak_profile.clear()

        self.base_rate_big = sum(seq) / float(n)

        # Exponential recency weighting (decay factor lambda = 0.95)
        recent = seq[-40:]
        weight_sum = 0.0
        weighted_big = 0.0
        for idx, val in enumerate(recent):
            w = 0.95 ** (len(recent) - 1 - idx)
            weight_sum += w
            if val == 1:
                weighted_big += w

        self.recent_bias_big = weighted_big / weight_sum if weight_sum > 0 else 0.5
        changes = sum(1 for i in range(1, n) if seq[i] != seq[i - 1])
        self.alternation_score = changes / float(max(1, n - 1))

        for i in range(n - 2):
            self.markov2[(seq[i], seq[i + 1])][seq[i + 2]] += 1
        for i in range(n - 3):
            self.markov3[(seq[i], seq[i + 1], seq[i + 2])][seq[i + 3]] += 1
        for i in range(n - 4):
            self.markov4[(seq[i], seq[i + 1], seq[i + 2], seq[i + 3])][seq[i + 4]] += 1

        current_streak = 1
        for i in range(1, n):
            if seq[i] == seq[i - 1]:
                current_streak += 1
            else:
                self.streak_profile[min(current_streak, 15)][seq[i]] += 1
                current_streak = 1

        self.depth = n
        self.trained = True
        return True

    def predict(self, dataset: List[Dict[str, Any]]) -> Tuple[Optional[str], int, Dict[str, Any]]:
        if not self.trained or len(dataset) < 5:
            return None, 0, {}

        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        last = seq[-1]
        votes: List[float] = []
        weights: List[float] = []

        if len(seq) >= 5:
            counts = self.markov4.get(tuple(seq[-4:]))
            if counts and sum(counts) >= 2:
                votes.append((counts[1] + 1.0) / (sum(counts) + 2.0))
                weights.append(0.30)

        if len(seq) >= 4:
            counts = self.markov3.get(tuple(seq[-3:]))
            if counts and sum(counts) >= 2:
                votes.append((counts[1] + 1.0) / (sum(counts) + 2.0))
                weights.append(0.22)

        if len(seq) >= 3:
            counts = self.markov2.get(tuple(seq[-2:]))
            if counts and sum(counts) >= 2:
                votes.append((counts[1] + 1.0) / (sum(counts) + 2.0))
                weights.append(0.15)

        votes.append(self.base_rate_big)
        weights.append(0.08)

        votes.append(self.recent_bias_big)
        weights.append(0.12)

        alt = self.alternation_score
        if alt >= 0.56:
            votes.append(0.18 if last == 1 else 0.82)
            weights.append(min(0.24, (alt - 0.50) * 0.95))
        elif alt <= 0.44:
            votes.append(0.82 if last == 1 else 0.18)
            weights.append(min(0.24, (0.50 - alt) * 0.95))

        cur_streak = 1
        for i in range(len(seq) - 2, -1, -1):
            if seq[i] == seq[-1]:
                cur_streak += 1
            else:
                break

        s_counts = self.streak_profile.get(min(cur_streak, 15))
        if s_counts and sum(s_counts) >= 2:
            votes.append((s_counts[1] + 1.0) / (sum(s_counts) + 2.0))
            weights.append(0.18)

        if not votes:
            return None, 0, {}

        total_weight = sum(weights)
        weighted_prob = sum(v * w for v, w in zip(votes, weights)) / total_weight

        pred = "BIG" if weighted_prob >= 0.50 else "SMALL"
        conviction = abs(weighted_prob - 0.50) * 2.0
        depth_boost = min(10.0, self.depth / 40.0)
        conf = int(clamp(63 + conviction * 26 + depth_boost, CONFIG.base_confidence_floor, 98))

        self.confidence_score = conf
        self.last_prediction = pred
        self.debug = {
            "weighted_prob": weighted_prob,
            "alternation": alt,
            "base_rate": self.base_rate_big,
            "recent_bias": self.recent_bias_big,
            "current_streak": cur_streak
        }
        return pred, conf, self.debug
