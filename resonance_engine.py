# -*- coding: utf-8 -*-
"""
================================================================================
VIP STRIKE V35.0 ENTERPRISE - MODULE 8: 4,485+ SEQUENCE RESONANCE SCANNER
================================================================================
"""

from typing import List, Dict, Any, Tuple, Optional
from .config import CONFIG

def clamp(val: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, val))

class HistoricalSequenceResonanceEngine:
    """
    Scans entire 4,485+ historical dataset for matching 10-period fingerprints.
    Finds top-K closest pattern matches across history and computes empirical transitions.
    """

    def __init__(self, fingerprint_len: int = 10, top_k_matches: int = 15):
        self.fingerprint_len = fingerprint_len
        self.top_k_matches = top_k_matches
        self.last_prediction: Optional[str] = None
        self.confidence_score: int = 0
        self.match_count: int = 0

    def predict(self, dataset: List[Dict[str, Any]]) -> Tuple[Optional[str], int, Dict[str, Any]]:
        n = len(dataset)
        flen = self.fingerprint_len
        if n < flen + 20:
            return None, 0, {}

        seq_res = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        seq_num = [float(d.get("number", 0)) / 9.0 for d in dataset]

        target_res = seq_res[-flen:]
        target_num = seq_num[-flen:]

        matches = []
        for i in range(n - flen - 1):
            sub_res = seq_res[i:i + flen]
            sub_num = seq_num[i:i + flen]
            next_outcome = seq_res[i + flen]

            res_diff = sum(1 for a, b in zip(target_res, sub_res) if a != b)
            num_dist = sum(abs(a - b) for a, b in zip(target_num, sub_num))
            total_dist = res_diff * 2.0 + num_dist

            matches.append((total_dist, next_outcome, i))

        matches.sort(key=lambda x: x[0])
        best_matches = matches[:self.top_k_matches]

        if not best_matches:
            return None, 0, {}

        weights = [1.0 / (1.0 + m[0]) for m in best_matches]
        outcomes = [m[1] for m in best_matches]

        total_w = sum(weights)
        prob_big = sum(w * out for w, out in zip(weights, outcomes)) / total_w

        pred = "BIG" if prob_big >= 0.50 else "SMALL"
        conviction = abs(prob_big - 0.50) * 2.0
        conf = int(clamp(conviction * 100 + 66, CONFIG.base_confidence_floor, 98))

        self.last_prediction = pred
        self.confidence_score = conf
        self.match_count = len(best_matches)

        debug = {
            "top_k": len(best_matches),
            "prob_big": prob_big,
            "best_dist": best_matches[0][0] if best_matches else 0,
            "outcomes_sampled": outcomes
        }
        return pred, conf, debug
