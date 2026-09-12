# -*- coding: utf-8 -*-
"""
================================================================================
VIP STRIKE V35.0 ENTERPRISE - MODULE 11: RISK & BANKROLL MANAGEMENT
================================================================================
"""

from typing import List, Dict, Any

def clamp(val: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, val))

class RiskManagementEngine:
    """Fractional Kelly Criterion & Martingale Risk Controller."""

    @staticmethod
    def calculate_kelly_stake(win_probability: float, payout_multiplier: float = 1.96, bankroll: float = 1000.0, kelly_fraction: float = 0.25) -> Dict[str, Any]:
        b = payout_multiplier - 1.0
        p = clamp(win_probability, 0.01, 0.99)
        q = 1.0 - p

        raw_kelly = (b * p - q) / b
        safe_kelly = max(0.0, raw_kelly * kelly_fraction)
        recommended_bet = round(safe_kelly * bankroll, 2)

        return {
            "win_probability": round(p * 100, 1),
            "safe_fraction_pct": round(safe_kelly * 100, 2),
            "recommended_amount": recommended_bet,
            "bankroll": bankroll
        }

    @staticmethod
    def generate_martingale_schedule(base_unit: float = 10.0, max_steps: int = 5, multiplier: float = 2.1) -> List[Dict[str, Any]]:
        schedule = []
        cumulative = 0.0
        for step in range(1, max_steps + 1):
            amount = round(base_unit * (multiplier ** (step - 1)), 2)
            cumulative += amount
            schedule.append({
                "step": step,
                "bet": amount,
                "cumulative_cost": round(cumulative, 2)
            })
        return schedule
