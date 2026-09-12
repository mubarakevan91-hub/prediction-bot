# -*- coding: utf-8 -*-
"""
================================================================================
VIP STRIKE V35.0 ENTERPRISE - MODULE 15: MASTER ENGINE ORCHESTRATOR
================================================================================
"""

import os
import sys
import io
import csv
import time
import signal
import logging
import threading
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

from .config import CONFIG, BD_TZ
from .database import DatabaseManager
from .statistical_audit import StatisticalAuditEngine
from .feature_engineering import UltraFeatureExtractor
from .neural_engine import DeepNeuralEngineV35
from .ml_ensemble_engine import MachineLearningMegaEnsemble
from .markov_engine import HighOrderMarkovEngine
from .resonance_engine import HistoricalSequenceResonanceEngine
from .russian_engine import RussianPredictionEngineV35
from .regime_detection import RegimeAndCycleEngine
from .risk_management import RiskManagementEngine
from .backtester import BacktestEngine
from .telegram_bot import TelegramBotClient, get_vip_inline_keyboard
from .web_server import run_web_dashboard

try:
    import requests
except ImportError:
    pass

logger = logging.getLogger("VIPStrikeMain")
_SHUTDOWN_EVENT = threading.Event()

def get_bd_now() -> datetime:
    return datetime.now(BD_TZ)

def format_bd_time(dt: Optional[datetime] = None) -> str:
    if dt is None:
        dt = get_bd_now()
    return dt.strftime("%I:%M:%S %p")

def result_from_number(num: Any) -> str:
    try:
        n = int(num)
    except (ValueError, TypeError):
        n = 0
    return "BIG" if n >= 5 else "SMALL"

def parity_from_number(num: Any) -> str:
    try:
        n = int(num)
    except (ValueError, TypeError):
        n = 0
    return "EVEN" if n % 2 == 0 else "ODD"

def color_from_number(num: Any) -> str:
    try:
        n = int(num)
    except (ValueError, TypeError):
        n = 0
    if n in (1, 3, 7, 9):
        return "GREEN"
    elif n in (2, 4, 6, 8):
        return "RED"
    elif n == 0:
        return "RED_VIOLET"
    elif n == 5:
        return "GREEN_VIOLET"
    return "UNKNOWN"

def clamp(val: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, val))

def signal_badge(pred: Optional[str]) -> str:
    if pred == "BIG":
        return "🟢"
    if pred == "SMALL":
        return "🔴"
    return "⚪"


class MasterEngine:
    """Master Orchestration Engine for 4,485+ Historical Datasets."""

    def __init__(self):
        self.dataset: List[Dict[str, Any]] = []
        self.db = DatabaseManager()
        self.bot = TelegramBotClient()
        self.extractor = UltraFeatureExtractor()

        # Engine Modules
        self.neural_engine = DeepNeuralEngineV35()
        self.ml_mega = MachineLearningMegaEnsemble()
        self.markov_engine = HighOrderMarkovEngine()
        self.russian_engine = RussianPredictionEngineV35()
        self.resonance_engine = HistoricalSequenceResonanceEngine(
            fingerprint_len=CONFIG.resonance_window_size,
            top_k_matches=CONFIG.top_k_resonance_matches
        )

        self.last_issue: Optional[str] = None
        self.last_prediction: Optional[str] = None
        self.last_pred_conf: int = 0

        self.last_dl_pred: Optional[str] = None
        self.last_dl_conf: int = 0
        self.last_ml_pred: Optional[str] = None
        self.last_ml_conf: int = 0
        self.last_mk_pred: Optional[str] = None
        self.last_mk_conf: int = 0
        self.last_ru_pred: Optional[str] = None
        self.last_ru_conf: int = 0
        self.last_res_pred: Optional[str] = None
        self.last_res_conf: int = 0

        self.active_regime_info: Dict[str, Any] = {}
        self.is_active = False

        # Streaks
        self.current_win_streak = 0
        self.current_loss_streak = 0
        self.max_win_streak = 0
        self.max_loss_streak = 0
        self.total_wins = 0
        self.total_losses = 0

        self._hydrate_from_db()

    def _hydrate_from_db(self) -> None:
        saved_rounds = self.db.get_recent_rounds(limit=CONFIG.max_history_memory)
        if len(saved_rounds) >= CONFIG.min_train_samples:
            self.dataset = saved_rounds
            self.train_all_engines()
            self.last_issue = self.dataset[-1]["issue"]
            self.is_active = True
            logger.info(f"🔄 Hydrated {len(saved_rounds)} rounds into active memory.")

    def train_all_engines(self) -> None:
        self.neural_engine.train(self.dataset, self.extractor)
        self.ml_mega.train(self.dataset, self.extractor)
        self.markov_engine.train(self.dataset)
        self.russian_engine.train(self.dataset)
        self.active_regime_info = RegimeAndCycleEngine.detect_regime(self.dataset)

    def make_predictions(self, dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
        dl_pred, dl_conf = self.neural_engine.predict(dataset, self.extractor)
        ml_pred, ml_conf = self.ml_mega.predict(dataset, self.extractor)
        mk_pred, mk_conf = self.markov_engine.predict(dataset)
        ru_pred, ru_conf, _ = self.russian_engine.predict(dataset)
        res_pred, res_conf, _ = self.resonance_engine.predict(dataset)

        regime = self.active_regime_info.get("regime", "BALANCED_MATRIX")

        w_dl = CONFIG.weight_deep_neural
        w_ml = CONFIG.weight_ml_ensemble
        w_res = CONFIG.weight_sequence_resonance
        w_mk = CONFIG.weight_markov_high_order
        w_ru = CONFIG.weight_russian_core

        if regime == "HIGH_CHOP":
            w_ru += 0.08
            w_mk += 0.05
            w_dl -= 0.06
        elif regime == "DRAGON_STREAK":
            w_dl += 0.08
            w_ml += 0.05
            w_res += 0.04
            w_ru -= 0.08

        models = [
            (dl_pred, dl_conf, w_dl),
            (ml_pred, ml_conf, w_ml),
            (res_pred, res_conf, w_res),
            (mk_pred, mk_conf, w_mk),
            (ru_pred, ru_conf, w_ru)
        ]

        active_votes = []
        active_weights = []
        for pred, conf, weight in models:
            if pred is not None:
                prob = conf / 100.0 if pred == "BIG" else (1.0 - conf / 100.0)
                active_votes.append(prob)
                active_weights.append(weight)

        if active_votes:
            total_w = sum(active_weights)
            final_prob_big = sum(v * w for v, w in zip(active_votes, active_weights)) / total_w
            final_pred = "BIG" if final_prob_big >= 0.50 else "SMALL"
            conviction = abs(final_prob_big - 0.50) * 2.0
            agreeing = sum(1 for p, _, _ in models if p == final_pred)
            bonus = (agreeing - 2) * 3
            final_conf = int(clamp(conviction * 100 + 68 + bonus, CONFIG.base_confidence_floor, CONFIG.base_confidence_ceiling))
        else:
            final_pred = None
            final_conf = 0

        return {
            "dl_pred": dl_pred, "dl_conf": dl_conf,
            "ml_pred": ml_pred, "ml_conf": ml_conf,
            "mk_pred": mk_pred, "mk_conf": mk_conf,
            "ru_pred": ru_pred, "ru_conf": ru_conf,
            "res_pred": res_pred, "res_conf": res_conf,
            "final_pred": final_pred, "final_conf": final_conf
        }

    def refresh_predictions(self) -> None:
        preds = self.make_predictions(self.dataset)

        self.last_dl_pred = preds.get("dl_pred")
        self.last_dl_conf = preds.get("dl_conf", 0)

        self.last_ml_pred = preds.get("ml_pred")
        self.last_ml_conf = preds.get("ml_conf", 0)

        self.last_mk_pred = preds.get("mk_pred")
        self.last_mk_conf = preds.get("mk_conf", 0)

        self.last_ru_pred = preds.get("ru_pred")
        self.last_ru_conf = preds.get("ru_conf", 0)

        self.last_res_pred = preds.get("res_pred")
        self.last_res_conf = preds.get("res_conf", 0)

        self.last_prediction = preds.get("final_pred")
        self.last_pred_conf = preds.get("final_conf", 0)

        if self.last_issue and self.last_prediction:
            next_issue = self.safe_next_issue(self.last_issue)
            now = get_bd_now()
            self.db.insert_prediction(
                issue=next_issue,
                pred=self.last_prediction,
                conf=self.last_pred_conf,
                dl_p=f"{self.last_dl_pred or 'N/A'}:{self.last_dl_conf}",
                ml_p=f"{self.last_ml_pred or 'N/A'}:{self.last_ml_conf}",
                mk_p=f"{self.last_mk_pred or 'N/A'}:{self.last_mk_conf}",
                ru_p=f"{self.last_ru_pred or 'N/A'}:{self.last_ru_conf}",
                res_p=f"{self.last_res_pred or 'N/A'}:{self.last_res_conf}",
                regime=self.active_regime_info.get("regime", "NEUTRAL"),
                hour=now.hour,
                session=self.active_regime_info.get("desc", "Active")
            )

    def broadcast(self, msg: str, keyboard: Optional[Dict] = None) -> None:
        chats = self.db.get_all_chats()
        for cid in chats:
            self.bot.send_message(cid, msg, reply_markup=keyboard)

    def safe_next_issue(self, issue: Optional[str]) -> str:
        if not issue:
            return "N/A"
        try:
            return str(int(issue) + 1)
        except Exception:
            return f"{issue}+1"

    def parse_csv_content(self, content_str: str) -> List[Dict[str, Any]]:
        records = []
        try:
            reader = csv.reader(io.StringIO(content_str))
            for row in reader:
                if not row:
                    continue
                first = str(row[0]).strip().lower()
                if first in {"period", "issue", "issuenumber", "id", "round"}:
                    continue

                issue = str(row[0]).strip()
                num = 0
                if len(row) > 1:
                    txt = str(row[1]).strip()
                    if txt.isdigit():
                        num = int(txt)

                res = None
                if len(row) > 2:
                    r = str(row[2]).strip().upper()
                    if r in {"BIG", "SMALL"}:
                        res = r

                if res is None:
                    res = result_from_number(num)

                par = parity_from_number(num)
                col = color_from_number(num)

                records.append({
                    "issue": issue,
                    "number": num,
                    "result": res,
                    "parity": par,
                    "color": col,
                    "timestamp": format_bd_time()
                })
        except Exception as e:
            logger.error(f"CSV Parse Exception: {e}")
        return records

    def ingest_manual_dataset(self, content_str: str) -> Tuple[bool, int]:
        records = self.parse_csv_content(content_str)
        if len(records) < CONFIG.min_train_samples:
            return False, len(records)

        self.dataset = records
        self.db.insert_rounds_bulk(records)

        logger.info(f"📚 Full Multi-Model Training Started on {len(records)} Records...")
        self.train_all_engines()
        self.is_active = True
        self.last_issue = self.dataset[-1]["issue"]
        self.refresh_predictions()

        next_issue = self.safe_next_issue(self.last_issue)
        now_bd = get_bd_now()
        regime_desc = self.active_regime_info.get("desc", "Active")

        msg = (
            f"👑 <b>ULTRA HYBRID AI/ML/DL TRAINED ({len(records)} ROUNDS)</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📚 <b>Trained Memory:</b> <code>{len(records)} Records Active</code>\n"
            f"🎮 <b>Market Regime:</b> <b>{regime_desc}</b>\n"
            f"🎯 <b>Next Period:</b> <code>{next_issue}</code>\n"
            f"🧬 <b>Final Ensemble:</b> <b>{self.last_prediction or 'N/A'}</b> "
            f"{signal_badge(self.last_prediction)} <b>({self.last_pred_conf}%)</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🧠 <b>Deep Neural (256-128-64-32):</b> <b>{self.last_dl_pred or 'N/A'}</b> ({self.last_dl_conf}%)\n"
            f"🌲 <b>Multi-Tree Ensemble:</b> <b>{self.last_ml_pred or 'N/A'}</b> ({self.last_ml_conf}%)\n"
            f"🔍 <b>Historical Resonance Scanner:</b> <b>{self.last_res_pred or 'N/A'}</b> ({self.last_res_conf}%)\n"
            f"🎲 <b>Markov Chain (Order 2-8):</b> <b>{self.last_mk_pred or 'N/A'}</b> ({self.last_mk_conf}%)\n"
            f"🇷🇺 <b>Russian Core Engine:</b> <b>{self.last_ru_pred or 'N/A'}</b> ({self.last_ru_conf}%)\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🕒 <b>Sync Time:</b> <code>{now_bd.strftime('%I:%M:%S %p')}</code>"
        )
        self.broadcast(msg, get_vip_inline_keyboard())
        return True, len(records)

    def format_live_message(self, last_issue: str, actual_res: str, num: int, outcome_str: str, now_bd: datetime) -> str:
        next_issue = self.safe_next_issue(last_issue)
        regime_desc = self.active_regime_info.get("desc", "Active")

        return (
            f"🎯 <b>Period:</b> <code>{next_issue}</code>\n"
            f"🧬 <b>Final Signal:</b> <b>{self.last_prediction or 'N/A'}</b> "
            f"{signal_badge(self.last_prediction)} <b>({self.last_pred_conf}%)</b>\n"
            f"🎮 <b>Regime:</b> <code>{regime_desc}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🧠 <b>Neural (256L):</b> <b>{self.last_dl_pred or 'N/A'}</b> ({self.last_dl_conf}%) | "
            f"🌲 <b>ML:</b> <b>{self.last_ml_pred or 'N/A'}</b> ({self.last_ml_conf}%)\n"
            f"🔍 <b>Resonance:</b> <b>{self.last_res_pred or 'N/A'}</b> ({self.last_res_conf}%) | "
            f"🇷🇺 <b>Russian:</b> <b>{self.last_ru_pred or 'N/A'}</b> ({self.last_ru_conf}%)\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎲 <b>Last:</b> {last_issue} ➔ <b>{actual_res} ({num})</b> | {outcome_str}\n"
            f"🔥 <b>Final Streak:</b> Win <code>{self.current_win_streak}</code> | "
            f"Loss <code>{self.current_loss_streak}</code>\n"
            f"🏆 <b>Max Win Streak:</b> <code>{self.max_win_streak}</code>\n"
            f"🕒 <b>Time:</b> <code>{now_bd.strftime('%I:%M:%S %p')}</code>"
        )

    def run(self) -> None:
        logger.info("🚀 ULTRA ENTERPRISE PREDICTION SUITE ACTIVE...")
        offset: Optional[int] = None

        while not _SHUTDOWN_EVENT.is_set():
            updates = self.bot.get_updates(offset)
            for u in updates:
                offset = u["update_id"] + 1

                if "callback_query" in u:
                    cb = u["callback_query"]
                    cb_id = cb.get("id")
                    data = cb.get("data", "")
                    chat_id = str(cb.get("message", {}).get("chat", {}).get("id", ""))
                    self.bot.answer_callback(cb_id, "✅")

                    if not chat_id:
                        continue

                    kb = get_vip_inline_keyboard()
                    if data == "btn_live_stats":
                        total = self.total_wins + self.total_losses
                        wr = (self.total_wins / total * 100.0) if total > 0 else 0.0
                        msg = (
                            f"📊 <b>লাইভ পারফরম্যান্স ড্যাশবোর্ড (Ultra Suite)</b>\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"🔥 <b>Current Win Streak:</b> <code>{self.current_win_streak}</code>\n"
                            f"⚠️ <b>Current Loss Streak:</b> <code>{self.current_loss_streak}</code>\n"
                            f"🏆 <b>Max Win Streak:</b> <code>{self.max_win_streak}</code>\n"
                            f"🛑 <b>Max Loss Streak:</b> <code>{self.max_loss_streak}</code>\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"✅ <b>Total Wins:</b> <code>{self.total_wins}</code> | "
                            f"❌ <b>Losses:</b> <code>{self.total_losses}</code>\n"
                            f"📈 <b>Win Rate:</b> <code>{wr:.1f}%</code>"
                        )
                        self.bot.send_message(chat_id, msg, reply_markup=kb)

                    elif data in ("btn_curr_signal", "btn_ensemble"):
                        next_i = self.safe_next_issue(self.last_issue)
                        msg = (
                            f"🎯 <b>Active Period:</b> <code>{next_i}</code>\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"🧬 <b>Final Consensus:</b> <b>{self.last_prediction or 'N/A'}</b> "
                            f"{signal_badge(self.last_prediction)} <b>({self.last_pred_conf}%)</b>\n\n"
                            f"🧠 <b>Deep Neural:</b> {self.last_dl_pred} ({self.last_dl_conf}%)\n"
                            f"🌲 <b>ML Trees:</b> {self.last_ml_pred} ({self.last_ml_conf}%)\n"
                            f"🔍 <b>Resonance:</b> {self.last_res_pred} ({self.last_res_conf}%)\n"
                            f"🎲 <b>Markov O8:</b> {self.last_mk_pred} ({self.last_mk_conf}%)\n"
                            f"🇷🇺 <b>Russian Core:</b> {self.last_ru_pred} ({self.last_ru_conf}%)"
                        )
                        self.bot.send_message(chat_id, msg, reply_markup=kb)

                    elif data == "btn_resonance":
                        msg = (
                            f"🔍 <b>Historical Sequence Resonance Scanner</b>\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"📚 <b>Scanned Dataset:</b> <code>{len(self.dataset)} Rounds</code>\n"
                            f"🎯 <b>Fingerprint Signal:</b> <b>{self.last_res_pred or 'N/A'}</b> ({self.last_res_conf}%)\n"
                            f"🔬 <i>অ্যালগরিদমটি অতীতের সম্পূর্ণ ডেটাসেট স্ক্যান করে হুবহু প্যাটার্ন ম্যাচ বের করে।</i>"
                        )
                        self.bot.send_message(chat_id, msg, reply_markup=kb)

                    elif data == "btn_math_entropy":
                        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in self.dataset]
                        ent, norm_ent = StatisticalAuditEngine.calculate_shannon_entropy(seq)
                        runs = StatisticalAuditEngine.wald_wolfowitz_runs_test(seq)
                        msg = (
                            f"🔬 <b>Mathematical & Entropy Analysis</b>\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"🌀 <b>Shannon Entropy:</b> <code>{ent:.3f} bits</code>\n"
                            f"📊 <b>Randomness Factor:</b> <code>{norm_ent*100:.1f}%</code>\n"
                            f"🏃 <b>Runs Test Z-Score:</b> <code>{runs['z_score']}</code>\n"
                            f"🎲 <b>Pattern Bias:</b> <code>{'Yes (Biased)' if runs['is_non_random'] else 'Random-like'}</code>"
                        )
                        self.bot.send_message(chat_id, msg, reply_markup=kb)

                    elif data == "btn_risk_mgmt":
                        prob = (self.last_pred_conf / 100.0) if self.last_pred_conf > 0 else 0.55
                        kelly = RiskManagementEngine.calculate_kelly_stake(prob)
                        msg = (
                            f"💰 <b>Capital & Risk Management</b>\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"🎯 <b>Safe Fractional Kelly Bet:</b> <b>৳{kelly['recommended_amount']}</b> ({kelly['safe_fraction_pct']}% of fund)\n"
                            f"💎 <b>Bankroll Standard:</b> <code>৳1,000</code>\n"
                            f"🛡️ <i>৩ বার ক্রমাগত লস হলে ২ রাউন্ড বিরত থাকুন।</i>"
                        )
                        self.bot.send_message(chat_id, msg, reply_markup=kb)
                    continue

                msg = u.get("message", {})
                chat_id = str(msg.get("chat", {}).get("id", ""))
                doc = msg.get("document")
                text = msg.get("text", "")

                if not chat_id:
                    continue

                self.db.add_chat(chat_id, msg.get("chat", {}).get("username", ""))

                if doc:
                    self.bot.send_message(
                        chat_id,
                        "⏳ <b>ফাইল অ্যানালাইসিস ও মাল্টি-মডেল ডিপ লার্নিং প্রসেসিং শুরু হয়েছে...</b>"
                    )
                    file_bytes = self.bot.get_file_bytes(doc.get("file_id"))
                    if file_bytes:
                        ok, count = self.ingest_manual_dataset(file_bytes.decode("utf-8", errors="ignore"))
                        if not ok:
                            self.bot.send_message(chat_id, "⚠️ মডেলে ট্রেইনিংয়ের জন্য কমপক্ষে ২০+ রাউন্ড ডেটা প্রয়োজন।")
                    else:
                        self.bot.send_message(chat_id, "⚠️ ফাইল ডাউনলোড করা যায়নি।")
                    continue

                if text.startswith("/start") or text.startswith("/help"):
                    welcome_text = (
                        "👑 <b>স্বাগতম VIP Strike V35.0 Ultra Suite AI-তে!</b>\n"
                        "━━━━━━━━━━━━━━━━━━━━\n"
                        "🧠 <b>Deep Neural Net (4-Layer 256-128-64-32)</b>\n"
                        "🔍 <b>Historical Sequence Resonance Scanner</b>\n"
                        "🌲 <b>Random Forest + GBM + Extra Trees Mega Ensemble</b>\n"
                        "🎲 <b>High-Order Markov Chain (Order 2 to 8)</b>\n"
                        "🇷🇺 <b>Russian Prediction Core V35</b>\n\n"
                        "বট চালু করতে আপনার <code>dataset_export.csv</code> ফাইলটি সেন্ড করুন।"
                    )
                    self.bot.send_message(chat_id, welcome_text, reply_markup=get_vip_inline_keyboard())

            # Real-Time Lottery API Polling Loop
            try:
                for api_url in CONFIG.api_domains:
                    try:
                        resp = requests.get(
                            api_url,
                            params={"pageNo": 1, "pageSize": 10, "t": int(time.time() * 1000)},
                            timeout=CONFIG.request_timeout_sec
                        )
                        if resp.status_code == 200:
                            data_json = resp.json()
                            lst = data_json.get("data", {}).get("list", [])
                            if lst:
                                current_issue = str(lst[0].get("issueNumber"))
                                num = int(lst[0].get("number", 0))
                                actual_res = result_from_number(num)
                                parity = parity_from_number(num)
                                color = color_from_number(num)

                                if current_issue != self.last_issue:
                                    now_bd = get_bd_now()
                                    outcome_str = "⏳"

                                    if self.last_prediction:
                                        is_win = (self.last_prediction == actual_res)
                                        self.db.evaluate_prediction(current_issue, actual_res)

                                        if is_win:
                                            self.total_wins += 1
                                            self.current_win_streak += 1
                                            self.current_loss_streak = 0
                                            self.max_win_streak = max(self.max_win_streak, self.current_win_streak)
                                            outcome_str = "✅ <b>WIN</b>"
                                        else:
                                            self.total_losses += 1
                                            self.current_loss_streak += 1
                                            self.current_win_streak = 0
                                            self.max_loss_streak = max(self.max_loss_streak, self.current_loss_streak)
                                            outcome_str = "❌ <b>LOSS</b>"

                                    new_round = {
                                        "issue": current_issue,
                                        "number": num,
                                        "result": actual_res,
                                        "parity": parity,
                                        "color": color,
                                        "timestamp": format_bd_time(now_bd)
                                    }
                                    self.dataset.append(new_round)
                                    self.db.insert_round(current_issue, num, actual_res, parity, color, new_round["timestamp"])

                                    if len(self.dataset) > CONFIG.max_history_memory:
                                        self.dataset = self.dataset[-CONFIG.max_history_memory:]

                                    self.train_all_engines()
                                    self.last_issue = current_issue
                                    self.is_active = True
                                    self.refresh_predictions()

                                    live_msg = self.format_live_message(
                                        current_issue, actual_res, num, outcome_str, now_bd
                                    )
                                    self.broadcast(live_msg, get_vip_inline_keyboard())
                                break
                    except Exception:
                        continue
            except Exception as e:
                logger.error(f"Live loop exception: {e}")

            time.sleep(CONFIG.poll_interval_sec)


def signal_handler(sig, frame):
    _SHUTDOWN_EVENT.set()
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("================================================================================")
    print("👑 VIP STRIKE V35.0 - ULTRA 4485+ ENTERPRISE AI ENGINE")
    print("================================================================================")

    master = MasterEngine()
    web_t = threading.Thread(target=run_web_dashboard, args=(master,), daemon=True)
    web_t.start()
    master.run()

if __name__ == "__main__":
    main()
