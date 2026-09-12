# -*- coding: utf-8 -*-
"""
================================================================================
VIP STRIKE V35.0 ENTERPRISE - MODULE 12: WALK-FORWARD BACKTESTING SIMULATOR
================================================================================
"""

from typing import List, Dict, Any
from .feature_engineering import UltraFeatureExtractor
from .markov_engine import HighOrderMarkovEngine
from .russian_engine import RussianPredictionEngineV35
from .neural_engine import DeepNeuralEngineV35
from .ml_ensemble_engine import MachineLearningMegaEnsemble

class BacktestEngine:
    """Walk-Forward Historical Model Simulator across Large Datasets."""

    @staticmethod
    def run_walk_forward(dataset: List[Dict[str, Any]], start_idx: int = 30) -> Dict[str, Any]:
        if len(dataset) < start_idx + 10:
            return {"error": "ডেটা অপর্যাপ্ত (কমপক্ষে ৫০+ রাউন্ড প্রয়োজন)"}

        extractor = UltraFeatureExtractor()
        ai = HighOrderMarkovEngine()
        ru = RussianPredictionEngineV35()
        dl = DeepNeuralEngineV35()
        ml = MachineLearningMegaEnsemble()

        total_tested = 0
        correct = 0
        current_streak = 0
        max_win_streak = 0
        current_loss = 0
        max_loss_streak = 0

        # Step through historical data
        step = max(1, len(dataset) // 150)  # Sampling step for speed on massive datasets
        for i in range(start_idx, len(dataset), step):
            train_slice = dataset[:i]
            target_round = dataset[i]
            actual = str(target_round.get("result", "")).upper()

            ai.train(train_slice)
            ru.train(train_slice)
            dl.train(train_slice, extractor)
            ml.train(train_slice, extractor)

            p_ai, _ = ai.predict(train_slice)
            p_ru, _, _ = ru.predict(train_slice)
            p_dl, _ = dl.predict(train_slice, extractor)
            p_ml, _ = ml.predict(train_slice, extractor)

            votes = [p for p in [p_ai, p_ru, p_dl, p_ml] if p is not None]
            if not votes:
                continue

            big_count = sum(1 for v in votes if v == "BIG")
            final_pred = "BIG" if big_count >= len(votes) / 2.0 else "SMALL"

            total_tested += 1
            if final_pred == actual:
                correct += 1
                current_streak += 1
                current_loss = 0
                max_win_streak = max(max_win_streak, current_streak)
            else:
                current_loss += 1
                current_streak = 0
                max_loss_streak = max(max_loss_streak, current_loss)

        win_rate = (correct / float(total_tested)) * 100.0 if total_tested > 0 else 0.0
        return {
            "total_tested": total_tested,
            "correct": correct,
            "win_rate": round(win_rate, 2),
            "max_win_streak": max_win_streak,
            "max_loss_streak": max_loss_streak
        }
