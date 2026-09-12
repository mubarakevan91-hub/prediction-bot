# -*- coding: utf-8 -*-
"""
================================================================================
VIP STRIKE V35.0 ENTERPRISE - MODULE 7: 8TH-ORDER MARKOV CHAIN AI ENGINE
================================================================================
"""

from collections import defaultdict
from typing import List, Dict, Any, Tuple, Optional
from .config import CONFIG

def clamp(val: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, val))

class HighOrderMarkovEngine:
    """High-Order Markov Chain (Order 2 through 8) with Hierarchical Backoff."""

    def __init__(self):
        self.markov8 = defaultdict(lambda: [0, 0])
        self.markov7 = defaultdict(lambda: [0, 0])
        self.markov6 = defaultdict(lambda: [0, 0])
        self.markov5 = defaultdict(lambda: [0, 0])
        self.markov4 = defaultdict(lambda: [0, 0])
        self.markov3 = defaultdict(lambda: [0, 0])
        self.markov2 = defaultdict(lambda: [0, 0])
        self.streak_transitions = defaultdict(lambda: [0, 0])
        self.is_trained = False
        self.confidence_score = 0
        self.last_prediction = None

    def train(self, dataset: List[Dict[str, Any]]) -> bool:
        n = len(dataset)
        if n < 20:
            self.is_trained = False
            return False

        self.markov8.clear()
        self.markov7.clear()
        self.markov6.clear()
        self.markov5.clear()
        self.markov4.clear()
        self.markov3.clear()
        self.markov2.clear()
        self.streak_transitions.clear()

        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]

        for i in range(n - 2):
            self.markov2[(seq[i], seq[i + 1])][seq[i + 2]] += 1
        for i in range(n - 3):
            self.markov3[(seq[i], seq[i + 1], seq[i + 2])][seq[i + 3]] += 1
        for i in range(n - 4):
            self.markov4[(seq[i], seq[i + 1], seq[i + 2], seq[i + 3])][seq[i + 4]] += 1
        for i in range(n - 5):
            self.markov5[(seq[i], seq[i + 1], seq[i + 2], seq[i + 3], seq[i + 4])][seq[i + 5]] += 1
        for i in range(n - 6):
            self.markov6[(seq[i], seq[i + 1], seq[i + 2], seq[i + 3], seq[i + 4], seq[i + 5])][seq[i + 6]] += 1
        for i in range(n - 7):
            self.markov7[(seq[i], seq[i + 1], seq[i + 2], seq[i + 3], seq[i + 4], seq[i + 5], seq[i + 6])][seq[i + 7]] += 1
        for i in range(n - 8):
            self.markov8[(seq[i], seq[i + 1], seq[i + 2], seq[i + 3], seq[i + 4], seq[i + 5], seq[i + 6], seq[i + 7])][seq[i + 8]] += 1

        cur_streak = 1
        for i in range(1, n):
            if seq[i] == seq[i - 1]:
                cur_streak += 1
            else:
                self.streak_transitions[min(cur_streak, 18)][seq[i]] += 1
                cur_streak = 1

        self.is_trained = True
        return True

    def predict(self, dataset: List[Dict[str, Any]]) -> Tuple[Optional[str], int]:
        if not self.is_trained or len(dataset) < 8:
            return None, 0

        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        votes: List[float] = []
        weights: List[float] = []

        if len(seq) >= 8:
            counts = self.markov8.get(tuple(seq[-8:]))
            if counts and sum(counts) >= 2:
                votes.append((counts[1] + 1.0) / (sum(counts) + 2.0))
                weights.append(0.35)

        if len(seq) >= 7:
            counts = self.markov7.get(tuple(seq[-7:]))
            if counts and sum(counts) >= 2:
                votes.append((counts[1] + 1.0) / (sum(counts) + 2.0))
                weights.append(0.28)

        if len(seq) >= 6:
            counts = self.markov6.get(tuple(seq[-6:]))
            if counts and sum(counts) >= 2:
                votes.append((counts[1] + 1.0) / (sum(counts) + 2.0))
                weights.append(0.22)

        if len(seq) >= 5:
            counts = self.markov5.get(tuple(seq[-5:]))
            if counts and sum(counts) >= 2:
                votes.append((counts[1] + 1.0) / (sum(counts) + 2.0))
                weights.append(0.18)

        if len(seq) >= 4:
            counts = self.markov4.get(tuple(seq[-4:]))
            if counts and sum(counts) >= 2:
                votes.append((counts[1] + 1.0) / (sum(counts) + 2.0))
                weights.append(0.14)

        if len(seq) >= 3:
            counts = self.markov3.get(tuple(seq[-3:]))
            if counts and sum(counts) >= 2:
                votes.append((counts[1] + 1.0) / (sum(counts) + 2.0))
                weights.append(0.10)

        cur_streak = 1
        for i in range(len(seq) - 2, -1, -1):
            if seq[i] == seq[-1]:
                cur_streak += 1
            else:
                break

        s_counts = self.streak_transitions.get(min(cur_streak, 18))
        if s_counts and sum(s_counts) >= 2:
            votes.append((s_counts[1] + 1.0) / (sum(s_counts) + 2.0))
            weights.append(0.15)

        if not votes:
            fallback = "BIG" if seq[-1] == 1 else "SMALL"
            return fallback, 60

        total_w = sum(weights)
        weighted_prob = sum(v * w for v, w in zip(votes, weights)) / total_w
        pred = "BIG" if weighted_prob >= 0.50 else "SMALL"
        conviction = abs(weighted_prob - 0.50) * 2.0
        conf = int(clamp(conviction * 100 + 68, CONFIG.base_confidence_floor, 99))

        self.confidence_score = conf
        self.last_prediction = pred
        return pred, conf
