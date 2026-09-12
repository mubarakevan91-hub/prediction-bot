# -*- coding: utf-8 -*-
"""
================================================================================
VIP STRIKE V35.0 ENTERPRISE - MODULE 3: STATISTICAL & MATHEMATICAL AUDIT
================================================================================
"""

import math
from typing import List, Dict, Any, Tuple
from .config import CONFIG

def clamp(val: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, val))

class StatisticalAuditEngine:
    """Shannon Information Entropy, Runs Randomness Audit, and Bayesian Updating."""

    @staticmethod
    def calculate_shannon_entropy(binary_seq: List[int]) -> Tuple[float, float]:
        if not binary_seq:
            return 0.0, 0.0
        n = len(binary_seq)
        p1 = sum(binary_seq) / float(n)
        p0 = 1.0 - p1

        if p0 <= 0 or p1 <= 0:
            return 0.0, 0.0

        entropy = -(p0 * math.log2(p0) + p1 * math.log2(p1))
        return entropy, entropy / 1.0

    @staticmethod
    def wald_wolfowitz_runs_test(binary_seq: List[int]) -> Dict[str, Any]:
        n = len(binary_seq)
        if n < 10:
            return {"z_score": 0.0, "is_non_random": False, "runs": 0}

        n1 = sum(binary_seq)
        n0 = n - n1

        if n1 == 0 or n0 == 0:
            return {"z_score": -99.0, "is_non_random": True, "runs": 1}

        runs = 1
        for i in range(1, n):
            if binary_seq[i] != binary_seq[i - 1]:
                runs += 1

        mu = ((2.0 * n0 * n1) / float(n)) + 1.0
        numerator = 2.0 * n0 * n1 * (2.0 * n0 * n1 - n)
        denominator = float((n ** 2) * (n - 1))
        var = numerator / denominator if denominator > 0 else 1.0
        std = math.sqrt(max(var, 0.00001))

        z = (runs - mu) / std
        return {
            "z_score": round(z, 3),
            "runs": runs,
            "expected_runs": round(mu, 2),
            "is_non_random": bool(abs(z) > 1.96)
        }

    @staticmethod
    def chi_square_goodness_of_fit(numbers: List[int]) -> Dict[str, Any]:
        if len(numbers) < 20:
            return {"chi2_stat": 0.0, "is_digit_biased": False}

        observed = [0] * 10
        for num in numbers:
            if 0 <= num <= 9:
                observed[num] += 1

        expected = len(numbers) / 10.0
        chi2 = sum(((obs - expected) ** 2) / expected for obs in observed)
        return {
            "chi2_stat": round(chi2, 2),
            "is_digit_biased": chi2 > 16.92
        }

    @staticmethod
    def bayesian_beta_binomial_posterior(binary_seq: List[int]) -> Tuple[float, float, float]:
        k = sum(binary_seq)
        n = len(binary_seq)
        alpha_post = 1.0 + k
        beta_post = 1.0 + (n - k)

        mean_post = alpha_post / (alpha_post + beta_post)
        var_post = (alpha_post * beta_post) / (((alpha_post + beta_post) ** 2) * (alpha_post + beta_post + 1))
        std_post = math.sqrt(var_post)

        ci_low = clamp(mean_post - 1.645 * std_post, 0.0, 1.0)
        ci_high = clamp(mean_post + 1.645 * std_post, 0.0, 1.0)
        return mean_post, ci_low, ci_high
