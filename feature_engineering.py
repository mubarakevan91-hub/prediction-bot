# -*- coding: utf-8 -*-
"""
================================================================================
VIP STRIKE V35.0 ENTERPRISE - MODULE 4: 40-DIMENSIONAL FEATURE EXTRACTION
================================================================================
"""

import math
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from .config import CONFIG, BD_TZ

def get_bd_now() -> datetime:
    return datetime.now(BD_TZ)

def parity_from_number(num: Any) -> str:
    try:
        n = int(num)
    except (ValueError, TypeError):
        n = 0
    return "EVEN" if n % 2 == 0 else "ODD"

class UltraFeatureExtractor:
    """
    High-Dimensional Sequential Representation Builder (38-42 Features):
    - Multi-scale Outcome Lags (1-14)
    - Normalized Digit Lags (0-9)
    - Fibonacci Moving Averages (3, 5, 8, 13, 21, 34)
    - Volatility & Run-Length Statistics
    - Cyclic Diurnal Harmonic Features
    """

    def __init__(self, window_size: int = CONFIG.feature_window_size):
        self.window_size = window_size

    def extract_dataset(self, dataset: List[Dict[str, Any]]) -> Tuple[List[List[float]], List[int]]:
        n = len(dataset)
        min_lookback = 20
        if n <= min_lookback + 5:
            return [], []

        seq_res = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        seq_num = [float(d.get("number", 0)) / 9.0 for d in dataset]
        seq_par = [1 if parity_from_number(d.get("number", 0)) == "EVEN" else 0 for d in dataset]

        X, y = [], []
        for i in range(min_lookback, n):
            feats = self._build_row(seq_res, seq_num, seq_par, i)
            if feats is not None:
                X.append(feats)
                y.append(seq_res[i])

        return X, y

    def extract_latest(self, dataset: List[Dict[str, Any]]) -> Optional[List[float]]:
        min_lookback = 20
        if len(dataset) < min_lookback:
            return None

        seq_res = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        seq_num = [float(d.get("number", 0)) / 9.0 for d in dataset]
        seq_par = [1 if parity_from_number(d.get("number", 0)) == "EVEN" else 0 for d in dataset]

        return self._build_row(seq_res, seq_num, seq_par, len(dataset))

    def _build_row(self, seq_res: List[int], seq_num: List[float], seq_par: List[int], idx: int) -> Optional[List[float]]:
        if idx < 20:
            return None

        feats: List[float] = []

        # 1. Past 14 Outcome Lags
        feats.extend(seq_res[idx - 14:idx])

        # 2. Past 10 Number Lags
        feats.extend(seq_num[idx - 10:idx])

        # 3. Past 4 Parity Lags
        feats.extend(seq_par[idx - 4:idx])

        # 4. Fibonacci Rolling Averages (3, 5, 8, 13, 21)
        for w in [3, 5, 8, 13, 21]:
            if idx >= w:
                sub = seq_res[idx - w:idx]
                feats.append(sum(sub) / float(w))
            else:
                feats.append(0.5)

        # 5. Volatility (W=5, W=10)
        for w in [5, 10]:
            if idx >= w:
                sub = seq_res[idx - w:idx]
                avg = sum(sub) / float(w)
                var = sum((x - avg) ** 2 for x in sub) / float(w)
                feats.append(math.sqrt(var))
            else:
                feats.append(0.5)

        # 6. Streak & Direction
        streak = 1
        for k in range(idx - 1, 0, -1):
            if seq_res[k] == seq_res[k - 1]:
                streak += 1
            else:
                break
        feats.append(min(streak, 15) / 15.0)
        feats.append(1.0 if seq_res[idx - 1] == 1 else -1.0)

        # 7. Alternation Ratios (Short W=5 vs Long W=15)
        alt_5 = sum(1 for k in range(idx - 4, idx) if seq_res[k] != seq_res[k - 1]) / 4.0
        alt_15 = sum(1 for k in range(idx - 14, idx) if seq_res[k] != seq_res[k - 1]) / 14.0
        feats.extend([alt_5, alt_15])

        # 8. Diurnal Time Sin/Cos
        now = get_bd_now()
        minute_of_day = now.hour * 60 + now.minute
        feats.append(math.sin(2.0 * math.pi * minute_of_day / 1440.0))
        feats.append(math.cos(2.0 * math.pi * minute_of_day / 1440.0))

        return feats
