# -*- coding: utf-8 -*-
"""
================================================================================
VIP STRIKE V35.0 ENTERPRISE - MODULE 10: REGIME DETECTION & MARKET STATES
================================================================================
"""

from typing import List, Dict, Any

class RegimeAndCycleEngine:
    """Classifies game state into Dragon Streak, High-Chop, or Mean-Reversion."""

    @staticmethod
    def detect_regime(dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
        if len(dataset) < 15:
            return {"regime": "NEUTRAL", "desc": "স্ট্যান্ডার্ড প্যাটার্ন", "alt_rate": 0.5}

        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        recent_20 = seq[-20:]

        changes = sum(1 for i in range(1, len(recent_20)) if recent_20[i] != recent_20[i - 1])
        alt_rate = changes / float(len(recent_20) - 1)

        cur_streak = 1
        for i in range(len(seq) - 2, -1, -1):
            if seq[i] == seq[-1]:
                cur_streak += 1
            else:
                break

        if cur_streak >= 4:
            regime = "DRAGON_STREAK"
            desc = f"🐉 ড্রাগন ট্রেন্ড মোড (Streak: {cur_streak})"
        elif alt_rate >= 0.65:
            regime = "HIGH_CHOP"
            desc = f"⚡ পিং-পং অল্টারনেশন মোড ({alt_rate*100:.0f}%)"
        elif alt_rate <= 0.35:
            regime = "TREND_MOMENTUM"
            desc = "📈 ক্লাস্টার্ড ট্রেন্ড মোড"
        else:
            regime = "BALANCED_MATRIX"
            desc = "⚖️ স্ট্যাবল মডারেট প্যাটার্ন"

        return {
            "regime": regime,
            "desc": desc,
            "alt_rate": alt_rate,
            "current_streak": cur_streak
        }
