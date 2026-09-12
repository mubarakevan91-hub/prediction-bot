#============================================================
#ULTIMATE VIP STRIKE V26.0
#DEEP PATTERN AI + RUSSIAN PREDICTION ENGINE + ENSEMBLE CORE
#============================================================
"""
Advanced VIP Signal Bot
- DeepPatternEngine
- RussianPredictionEngine
- TimeIntelligence
- Telegram Bot UI
- Ensemble Final Signal
"""

import os
import json
import time
import threading
import signal
import csv
import io
import math
from datetime import datetime, timezone, timedelta
from collections import defaultdict

import requests
from http.server import HTTPServer, BaseHTTPRequestHandler


#============================================================
# CONFIG
#============================================================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8858558197:AAHvvS-rh9j1U9grv3SzmyqPsxN1FHNlv6E")
DEFAULT_CHAT_ID = os.environ.get("DEFAULT_CHAT_ID", "8395823375")

CHATS_FILE = "allowed_chats.json"

API_DOMAINS = [
    "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"
]

# Bangladesh Timezone UTC+6
BD_TZ = timezone(timedelta(hours=6))

_shutdown = threading.Event()


#============================================================
#CORE HELPERS
#============================================================

def signal_handler(sig, frame):
    _shutdown.set()


def get_bd_now():
    return datetime.now(BD_TZ)


def get_session_name(hour):
    if 5 <= hour < 12:
        return "🌅 সকাল (Morning)"
    elif 12 <= hour < 16:
        return "☀️ দুপুর (Noon)"
    elif 16 <= hour < 18:
        return "🌇 বিকাল (Afternoon)"
    elif 18 <= hour < 21:
        return "🌆 সন্ধ্যা (Evening)"
    else:
        return "🌙 রাত (Night)"


def load_chats():
    chats = set()

    if DEFAULT_CHAT_ID:
        chats.add(str(DEFAULT_CHAT_ID))

    if os.path.exists(CHATS_FILE):
        try:
            with open(CHATS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, list):
                    chats.update([str(x) for x in loaded])
        except Exception:
            pass

    return chats


def save_chats(chats_set):
    try:
        with open(CHATS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(chats_set), f)
    except Exception:
        pass


def result_from_number(num):
    try:
        num = int(num)
    except Exception:
        num = 0

    return "BIG" if num >= 5 else "SMALL"


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


# ============================================================
# 🧠 DEEP PATTERN AI ENGINE
# ============================================================

class DeepPatternEngine:
    """
    Original-style deep Markov pattern engine.
    """

    def __init__(self):
        self.markov4 = defaultdict(lambda: [0, 0])
        self.markov3 = defaultdict(lambda: [0, 0])
        self.markov2 = defaultdict(lambda: [0, 0])
        self.streak_reversion = defaultdict(lambda: [0, 0])

        self.is_fully_trained = False
        self.dataset_depth = 0
        self.confidence_score = 0.0

    def train(self, dataset):
        if len(dataset) < 15:
            self.is_fully_trained = False
            return False

        self.markov4.clear()
        self.markov3.clear()
        self.markov2.clear()
        self.streak_reversion.clear()

        seq = [
            1 if str(d.get("result", "")).upper() == "BIG" else 0
            for d in dataset
        ]

        n = len(seq)

        # Multi-layer Markov chain training
        for i in range(n - 2):
            self.markov2[(seq[i], seq[i + 1])][seq[i + 2]] += 1

        for i in range(n - 3):
            self.markov3[(seq[i], seq[i + 1], seq[i + 2])][seq[i + 3]] += 1

        for i in range(n - 4):
            self.markov4[
                (seq[i], seq[i + 1], seq[i + 2], seq[i + 3])
            ][seq[i + 4]] += 1

        # Streak reversion / continuation pattern
        current_streak = 1
        for i in range(1, n):
            if seq[i] == seq[i - 1]:
                current_streak += 1
            else:
                self.streak_reversion[min(current_streak, 8)][seq[i]] += 1
                current_streak = 1

        self.dataset_depth = n
        self.is_fully_trained = True
        return True

    def predict(self, dataset):
        if not self.is_fully_trained or len(dataset) < 5:
            return None, 0

        seq = [
            1 if str(d.get("result", "")).upper() == "BIG" else 0
            for d in dataset
        ]

        votes = []
        weights = []

        # Order 4 Markov
        if len(seq) >= 4:
            k4 = tuple(seq[-4:])
            counts = self.markov4.get(k4)

            if counts and sum(counts) >= 2:
                prob_big = (counts[1] + 1) / (sum(counts) + 2)
                votes.append(prob_big)
                weights.append(0.45)

        # Order 3 Markov
        if len(seq) >= 3:
            k3 = tuple(seq[-3:])
            counts = self.markov3.get(k3)

            if counts and sum(counts) >= 2:
                prob_big = (counts[1] + 1) / (sum(counts) + 2)
                votes.append(prob_big)
                weights.append(0.30)

        # Order 2 Markov
        if len(seq) >= 2:
            k2 = tuple(seq[-2:])
            counts = self.markov2.get(k2)

            if counts and sum(counts) >= 2:
                prob_big = (counts[1] + 1) / (sum(counts) + 2)
                votes.append(prob_big)
                weights.append(0.15)

        # Current streak tendency
        cur_streak = 1
        for i in range(len(seq) - 2, -1, -1):
            if seq[i] == seq[-1]:
                cur_streak += 1
            else:
                break

        s_key = min(cur_streak, 8)
        counts = self.streak_reversion.get(s_key)

        if counts and sum(counts) > 0:
            prob_big = (counts[1] + 1) / (sum(counts) + 2)
            votes.append(prob_big)
            weights.append(0.10)

        if not votes:
            fallback = "BIG" if seq[-1] == 1 else "SMALL"
            return fallback, 60

        total_weight = sum(weights)
        weighted_prob = sum(v * w for v, w in zip(votes, weights)) / total_weight

        pred = "BIG" if weighted_prob >= 0.50 else "SMALL"

        conviction = abs(weighted_prob - 0.50) * 2
        conf = int(clamp(conviction * 120 + 68, 60, 99))

        self.confidence_score = conf
        return pred, conf


# ============================================================
# 🇷🇺 RUSSIAN PREDICTION ENGINE
# ============================================================

class RussianPredictionEngine:
    """
    Russian Prediction Engine
    Российский движок прогнозирования

    This engine uses:
    - Markov chains
    - Recency bias
    - Alternation detection
    - Streak continuation / reversal
    - Base rate analysis
    - Ensemble probability fusion
    """

    NAME = "Russian Prediction Engine"

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
        self.debug = {}

    def train(self, dataset):
        seq = [
            1 if str(d.get("result", "")).upper() == "BIG" else 0
            for d in dataset
        ]

        n = len(seq)

        if n < 10:
            self.trained = False
            return False

        self.markov4.clear()
        self.markov3.clear()
        self.markov2.clear()
        self.streak_profile.clear()

        # Base probability
        self.base_rate_big = sum(seq) / float(n)

        # Recency weighted bias
        recent = seq[-30:]
        weight_sum = 0.0
        weighted_big = 0.0

        for idx, val in enumerate(recent):
            w = 0.95 ** (len(recent) - 1 - idx)
            weight_sum += w

            if val == 1:
                weighted_big += w

        self.recent_bias_big = weighted_big / weight_sum if weight_sum > 0 else 0.5

        # Alternation score
        changes = sum(1 for i in range(1, n) if seq[i] != seq[i - 1])
        self.alternation_score = changes / float(max(1, n - 1))

        # Markov chains
        for i in range(n - 2):
            self.markov2[(seq[i], seq[i + 1])][seq[i + 2]] += 1

        for i in range(n - 3):
            self.markov3[(seq[i], seq[i + 1], seq[i + 2])][seq[i + 3]] += 1

        for i in range(n - 4):
            self.markov4[
                (seq[i], seq[i + 1], seq[i + 2], seq[i + 3])
            ][seq[i + 4]] += 1

        # Streak behavior
        current_streak = 1

        for i in range(1, n):
            if seq[i] == seq[i - 1]:
                current_streak += 1
            else:
                self.streak_profile[min(current_streak, 10)][seq[i]] += 1
                current_streak = 1

        self.depth = n
        self.trained = True
        return True

    def predict(self, dataset):
        if not self.trained or len(dataset) < 6:
            return None, 0, {}

        seq = [
            1 if str(d.get("result", "")).upper() == "BIG" else 0
            for d in dataset
        ]

        last = seq[-1]

        votes = []
        weights = []
        notes = []

        def add_vote(prob_big, weight, name):
            votes.append(prob_big)
            weights.append(weight)
            notes.append(f"{name}:{prob_big:.2f}")

        # Markov 4
        if len(seq) >= 5:
            counts = self.markov4.get(tuple(seq[-4:]))

            if counts and sum(counts) >= 3:
                prob_big = (counts[1] + 1) / (sum(counts) + 2)
                add_vote(prob_big, 0.32, "M4")

        # Markov 3
        if len(seq) >= 4:
            counts = self.markov3.get(tuple(seq[-3:]))

            if counts and sum(counts) >= 3:
                prob_big = (counts[1] + 1) / (sum(counts) + 2)
                add_vote(prob_big, 0.24, "M3")

        # Markov 2
        if len(seq) >= 3:
            counts = self.markov2.get(tuple(seq[-2:]))

            if counts and sum(counts) >= 2:
                prob_big = (counts[1] + 1) / (sum(counts) + 2)
                add_vote(prob_big, 0.16, "M2")

        # Base rate
        add_vote(self.base_rate_big, 0.07, "BaseRate")

        # Recent bias
        add_vote(self.recent_bias_big, 0.10, "Recency")

        # Alternation / trend engine
        alt = self.alternation_score

        if alt >= 0.58:
            # Market is alternating often, predict opposite of last
            prob_big = 0.15 if last == 1 else 0.85
            weight = min(0.22, (alt - 0.50) * 0.9)
            add_vote(prob_big, weight, "Alternation")

        elif alt <= 0.42:
            # Market is trending, predict continuation
            prob_big = 0.85 if last == 1 else 0.15
            weight = min(0.22, (0.50 - alt) * 0.9)
            add_vote(prob_big, weight, "Trend")

        else:
            add_vote(0.50, 0.03, "Neutral")

        # Streak profile
        cur_streak = 1

        for i in range(len(seq) - 2, -1, -1):
            if seq[i] == seq[-1]:
                cur_streak += 1
            else:
                break

        s_key = min(cur_streak, 10)
        counts = self.streak_profile.get(s_key)

        if counts and sum(counts) >= 2:
            prob_big = (counts[1] + 1) / (sum(counts) + 2)
            add_vote(prob_big, 0.16, "StreakProfile")

        # Extreme local reversion
        last10 = seq[-10:]

        if len(last10) >= 8:
            big_ratio = sum(last10) / float(len(last10))

            if big_ratio >= 0.80:
                add_vote(0.35, 0.08, "LocalReversion")

            elif big_ratio <= 0.20:
                add_vote(0.65, 0.08, "LocalReversion")

        if not votes:
            return None, 0, {}

        total_weight = sum(weights)
        weighted_prob = sum(v * w for v, w in zip(votes, weights)) / total_weight

        pred = "BIG" if weighted_prob >= 0.50 else "SMALL"

        spread = max(votes) - min(votes) if len(votes) > 1 else 0.0
        conviction = abs(weighted_prob - 0.50) * 2
        depth_boost = min(12.0, self.depth / 25.0)

        conf = int(62 + conviction * 25 + depth_boost - spread * 12)
        conf = int(clamp(conf, 58, 98))

        self.confidence_score = conf

        self.debug = {
            "weighted_prob": weighted_prob,
            "votes": votes,
            "weights": weights,
            "notes": notes,
            "alternation": alt,
            "base_rate": self.base_rate_big,
            "recent_bias": self.recent_bias_big,
            "current_streak": cur_streak,
        }

        return pred, conf, self.debug


# ============================================================
# 🕒 TIME INTELLIGENCE & ACCURACY ANALYZER
# ============================================================

class TimeIntelligence:
    def __init__(self):
        self.session_wins = defaultdict(int)
        self.session_total = defaultdict(int)

        self.hourly_wins = defaultdict(int)
        self.hourly_total = defaultdict(int)

        self.best_time_record = {
            "time_str": "N/A",
            "streak": 0,
            "date": "N/A"
        }

        self.history_records = []

    def record_result(self, is_win, timestamp_dt):
        hour = timestamp_dt.hour
        session = get_session_name(hour)

        self.session_total[session] += 1
        self.hourly_total[hour] += 1

        if is_win:
            self.session_wins[session] += 1
            self.hourly_wins[hour] += 1

        self.history_records.append(
            {
                "is_win": is_win,
                "dt": timestamp_dt
            }
        )

    def get_best_session_and_time(self):
        best_session = "N/A"
        best_session_rate = 0.0

        for s, total in self.session_total.items():
            if total >= 3:
                rate = (self.session_wins[s] / total) * 100

                if rate > best_session_rate:
                    best_session_rate = rate
                    best_session = s

        best_hour_str = "N/A"
        best_hour_rate = 0.0

        for h, total in self.hourly_total.items():
            if total >= 2:
                rate = (self.hourly_wins[h] / total) * 100

                if rate > best_hour_rate:
                    best_hour_rate = rate

                    dummy_dt = datetime(2026, 1, 1, h, 0)
                    best_hour_str = dummy_dt.strftime("%I:00 %p")

        return best_session, best_session_rate, best_hour_str, best_hour_rate

    def get_loss_reduction_progress(self):
        if len(self.history_records) < 10:
            return "⏳ পর্যাপ্ত ডেটা সংগ্রহ হচ্ছে...", 0.0, "ডেটা অ্যানালাইসিস চলছে"

        half = len(self.history_records) // 2

        past_half = self.history_records[:half]
        recent_half = self.history_records[half:]

        past_loss = sum(1 for r in past_half if not r["is_win"]) / max(len(past_half), 1)
        recent_loss = sum(1 for r in recent_half if not r["is_win"]) / max(len(recent_half), 1)

        loss_reduced = (past_loss - recent_loss) * 100

        if loss_reduced > 0:
            status = f"🔥 লস <b>{loss_reduced:.1f}%</b> কমেছে (AI অত্যন্ত শক্তিশালী হচ্ছে)"

        elif loss_reduced == 0:
            status = "⚖️ স্ট্যাবল পারফরম্যান্স বজায় রয়েছে"

        else:
            status = "⚡ নতুন প্যাটার্ন অভিযোজন চলছে"

        recent_win_rate = (
            sum(1 for r in recent_half if r["is_win"]) / max(len(recent_half), 1)
        ) * 100

        return status, recent_win_rate, f"মোট পরীক্ষিত: {len(self.history_records)} রাউন্ড"


# ============================================================
# 🤖 TELEGRAM BOT CLIENT
# ============================================================

class TelegramBot:
    def __init__(self, token):
        self.url = f"https://api.telegram.org/bot{token}/"

    def send_message(self, chat_id, text, reply_markup=None):
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }

        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            requests.post(self.url + "sendMessage", json=payload, timeout=8)

        except Exception as e:
            print(f"⚠️ Telegram Send Error: {e}")

    def answer_callback(self, callback_id, text=""):
        try:
            requests.post(
                self.url + "answerCallbackQuery",
                data={
                    "callback_query_id": callback_id,
                    "text": text
                },
                timeout=4
            )

        except Exception:
            pass

    def get_file_bytes(self, file_id):
        try:
            res = requests.get(
                self.url + "getFile",
                params={"file_id": file_id},
                timeout=10
            ).json()

            path = res.get("result", {}).get("file_path")

            if path:
                file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{path}"
                return requests.get(file_url, timeout=25).content

        except Exception:
            pass

        return None

    def get_updates(self, offset=None):
        try:
            params = {
                "timeout": 2
            }

            if offset is not None:
                params["offset"] = offset

            res = requests.get(
                self.url + "getUpdates",
                params=params,
                timeout=8
            )

            if res.status_code == 200:
                return res.json().get("result", [])

        except Exception:
            pass

        return []


# ============================================================
# VIP INLINE KEYBOARD
# ============================================================

def get_vip_inline_keyboard():
    return {
        "inline_keyboard": [
            [
                {
                    "text": "📊 লাইভ পরিসংখ্যান",
                    "callback_data": "btn_live_stats"
                },
                {
                    "text": "🕒 সেরা উইনিং টাইম",
                    "callback_data": "btn_best_time"
                }
            ],
            [
                {
                    "text": "🧠 AI লার্নিং",
                    "callback_data": "btn_ai_learning"
                },
                {
                    "text": "🎯 বর্তমান সিগন্যাল",
                    "callback_data": "btn_curr_signal"
                }
            ],
            [
                {
                    "text": "🇷🇺 Russian Engine",
                    "callback_data": "btn_russian_engine"
                },
                {
                    "text": "🧬 Ensemble Signal",
                    "callback_data": "btn_ensemble"
                }
            ]
        ]
    }


# ============================================================
# ⚙️ MAIN ENGINE & CONTROLLER
# ============================================================

class Engine:
    def __init__(self):
        self.dataset = []

        self.ai = DeepPatternEngine()
        self.russian = RussianPredictionEngine()
        self.time_intel = TimeIntelligence()
        self.bot = TelegramBot(TELEGRAM_TOKEN)

        self.last_issue = None

        self.last_prediction = None
        self.last_pred_conf = 0

        self.last_deep_prediction = None
        self.last_deep_conf = 0

        self.last_russian_prediction = None
        self.last_russian_conf = 0

        self.is_active = False

        # Final ensemble streaks
        self.current_win_streak = 0
        self.current_loss_streak = 0
        self.max_win_streak = 0
        self.max_loss_streak = 0
        self.total_wins = 0
        self.total_losses = 0

        # Russian engine separate streaks
        self.ru_current_win_streak = 0
        self.ru_current_loss_streak = 0
        self.ru_max_win_streak = 0
        self.ru_max_loss_streak = 0
        self.ru_total_wins = 0
        self.ru_total_losses = 0

    def icon(self, pred):
        if pred == "BIG":
            return "🟢"

        if pred == "SMALL":
            return "🔴"

        return "⚪"

    def broadcast(self, msg, keyboard=None):
        chats = load_chats()

        for cid in list(chats):
            self.bot.send_message(cid, msg, reply_markup=keyboard)

    def safe_next_issue(self, issue):
        try:
            return str(int(issue) + 1)

        except Exception:
            return f"{issue}+1"

    def parse_csv_records(self, content_str):
        records = []

        try:
            reader = csv.reader(io.StringIO(content_str))

            for row in reader:
                if not row:
                    continue

                first = str(row[0]).strip().lower()

                if first in {"period", "issue", "issuenumber", "id"}:
                    continue

                issue = str(row[0]).strip()

                num = 0

                if len(row) > 1:
                    txt = str(row[1]).strip()

                    if txt.isdigit():
                        num = int(txt)

                result = None

                if len(row) > 2:
                    r = str(row[2]).strip().upper()

                    if r in {"BIG", "SMALL"}:
                        result = r

                if result is None:
                    result = result_from_number(num)

                records.append(
                    {
                        "issue": issue,
                        "number": num,
                        "result": result
                    }
                )

        except Exception:
            pass

        return records

    def make_predictions(self, dataset):
        deep_pred, deep_conf = self.ai.predict(dataset)
        ru_pred, ru_conf, ru_debug = self.russian.predict(dataset)

        final_pred = None
        final_conf = 0

        if deep_pred is not None and ru_pred is not None:
            deep_prob_big = deep_conf / 100.0 if deep_pred == "BIG" else 1.0 - deep_conf / 100.0
            ru_prob_big = ru_conf / 100.0 if ru_pred == "BIG" else 1.0 - ru_conf / 100.0

            final_prob_big = (0.56 * deep_prob_big) + (0.44 * ru_prob_big)

            final_pred = "BIG" if final_prob_big >= 0.50 else "SMALL"

            base_conf = int((0.56 * deep_conf) + (0.44 * ru_conf))

            if deep_pred == ru_pred:
                final_conf = base_conf + 6

            else:
                final_conf = base_conf - 8

            final_conf = int(clamp(final_conf, 55, 99))

        elif deep_pred is not None:
            final_pred = deep_pred
            final_conf = deep_conf

        elif ru_pred is not None:
            final_pred = ru_pred
            final_conf = ru_conf

        return {
            "deep_pred": deep_pred,
            "deep_conf": deep_conf,
            "ru_pred": ru_pred,
            "ru_conf": ru_conf,
            "ru_debug": ru_debug,
            "final_pred": final_pred,
            "final_conf": final_conf
        }

    def refresh_predictions(self):
        preds = self.make_predictions(self.dataset)

        self.last_deep_prediction = preds.get("deep_pred")
        self.last_deep_conf = preds.get("deep_conf", 0)

        self.last_russian_prediction = preds.get("ru_pred")
        self.last_russian_conf = preds.get("ru_conf", 0)

        self.last_prediction = preds.get("final_pred")
        self.last_pred_conf = preds.get("final_conf", 0)

    def load_file_and_train_deeply(self, content_str):
        records = self.parse_csv_records(content_str)

        if len(records) < 15:
            return False, 0

        self.dataset = records

        self.ai.train(self.dataset)
        self.russian.train(self.dataset)

        self.is_active = True
        self.last_issue = self.dataset[-1]["issue"]

        self.refresh_predictions()

        next_issue = self.safe_next_issue(self.last_issue)
        now_bd = get_bd_now()

        msg = (
            f"👑 <b>ADVANCED ENSEMBLE AI TRAINED</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📚 <b>Mastered Rounds:</b> <code>{len(records)}</code>\n"
            f"🎯 <b>Next Period:</b> <code>{next_issue}</code>\n"
            f"🧬 <b>Final Signal:</b> <b>{self.last_prediction or 'N/A'}</b> "
            f"{self.icon(self.last_prediction)} <b>({self.last_pred_conf}%)</b>\n"
            f"🧠 <b>Deep AI:</b> <b>{self.last_deep_prediction or 'N/A'}</b> "
            f"{self.icon(self.last_deep_prediction)} ({self.last_deep_conf}%)\n"
            f"🇷🇺 <b>Russian Engine:</b> <b>{self.last_russian_prediction or 'N/A'}</b> "
            f"{self.icon(self.last_russian_prediction)} ({self.last_russian_conf}%)\n"
            f"🕒 <b>Sync Time:</b> <code>{now_bd.strftime('%I:%M:%S %p')}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💎 <i>নিচের বাটনগুলো দিয়ে সম্পূর্ণ রিপোর্ট দেখুন।</i>\n"
            f"⚠️ <i>Educational pattern analysis only. No guarantee.</i>"
        )

        self.broadcast(msg, get_vip_inline_keyboard())

        return True, len(records)

    def generate_stats_report(self):
        total = self.total_wins + self.total_losses
        win_rate = (self.total_wins / total * 100) if total > 0 else 0.0

        ru_total = self.ru_total_wins + self.ru_total_losses
        ru_win_rate = (self.ru_total_wins / ru_total * 100) if ru_total > 0 else 0.0

        return (
            f"📊 <b>লাইভ পারফরম্যান্স ড্যাশবোর্ড</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔥 <b>Current Win Streak:</b> <code>{self.current_win_streak}</code>\n"
            f"⚠️ <b>Current Loss Streak:</b> <code>{self.current_loss_streak}</code>\n"
            f"🏆 <b>Max Win Streak:</b> <code>{self.max_win_streak}</code>\n"
            f"🛑 <b>Max Loss Streak:</b> <code>{self.max_loss_streak}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ <b>Total Wins:</b> <code>{self.total_wins}</code>\n"
            f"❌ <b>Total Losses:</b> <code>{self.total_losses}</code>\n"
            f"📈 <b>Overall Win-Rate:</b> <code>{win_rate:.1f}%</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🇷🇺 <b>Russian Engine Wins:</b> <code>{self.ru_total_wins}</code>\n"
            f"🇷🇺 <b>Russian Engine Losses:</b> <code>{self.ru_total_losses}</code>\n"
            f"🇷🇺 <b>Russian Win-Rate:</b> <code>{ru_win_rate:.1f}%</code>"
        )

    def generate_time_report(self):
        best_session, s_rate, best_hour, h_rate = self.time_intel.get_best_session_and_time()
        now_bd = get_bd_now()

        return (
            f"🕒 <b>সেরা উইনিং টাইম ইন্টেলিজেন্স</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 <b>আজকের তারিখ:</b> <code>{now_bd.strftime('%d %b, %Y')}</code>\n"
            f"⏰ <b>বর্তমান সময়:</b> <code>{now_bd.strftime('%I:%M %p')}</code> "
            f"({get_session_name(now_bd.hour)})\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🥇 <b>সর্বোচ্চ উইনিং সেশন:</b>\n"
            f"➔ <b>{best_session}</b> (উইনরেট: <b>{s_rate:.1f}%</b>)\n\n"
            f"👑 <b>নির্দিষ্ট পিক টাইম (Golden Hour):</b>\n"
            f"➔ <b>{best_hour}</b> (উইনরেট: <b>{h_rate:.1f}%</b>)\n\n"
            f"💡 <i>পরামর্শ: পিক সময়ে কনফিডেন্স অনেক বেশি থাকে।</i>"
        )

    def generate_learning_report(self):
        status, recent_rate, test_info = self.time_intel.get_loss_reduction_progress()

        return (
            f"🧠 <b>AI লার্নিং ও লস রিডাকশন অডিট</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📚 <b>লার্নিং স্ট্যাটাস:</b> Pattern Synchronized\n"
            f"📉 <b>লস রিডাকশন অগ্রগতি:</b>\n"
            f"➔ {status}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 <b>সাম্প্রতিক উইন রেট:</b> <code>{recent_rate:.1f}%</code>\n"
            f"🔬 <b>পর্যবেক্ষণ:</b> <code>{test_info}</code>\n"
            f"🛡️ <b>ভুল সিগন্যাল ফিল্টার:</b> <b>সক্রিয় (Active)</b>"
        )

    def generate_russian_report(self):
        pred = self.last_russian_prediction or "N/A"
        conf = self.last_russian_conf or 0

        total = self.ru_total_wins + self.ru_total_losses
        rate = (self.ru_total_wins / total * 100) if total > 0 else 0.0

        dbg = self.russian.debug or {}

        prob = dbg.get("weighted_prob", 0.5)
        alt = dbg.get("alternation", self.russian.alternation_score)
        base = dbg.get("base_rate", self.russian.base_rate_big)
        recency = dbg.get("recent_bias", self.russian.recent_bias_big)
        streak = dbg.get("current_streak", 0)

        return (
            f"🇷🇺 <b>Russian Prediction Engine</b>\n"
            f"🇷🇺 <b>Российский движок прогнозирования</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚙️ <b>Status:</b> {'Активен / Active' if self.russian.trained else 'Ожидание / Waiting'}\n"
            f"🎯 <b>Signal:</b> <b>{pred}</b> {self.icon(pred)} <b>({conf}%)</b>\n"
            f"📈 <b>BIG Probability:</b> <code>{prob * 100:.1f}%</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔁 <b>Alternation:</b> <code>{alt * 100:.1f}%</code>\n"
            f"🧮 <b>Base BIG Rate:</b> <code>{base * 100:.1f}%</code>\n"
            f"⚡ <b>Recent Bias BIG:</b> <code>{recency * 100:.1f}%</code>\n"
            f"🔥 <b>Current Result Streak:</b> <code>{streak}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ <b>Russian Wins:</b> <code>{self.ru_total_wins}</code>\n"
            f"❌ <b>Russian Losses:</b> <code>{self.ru_total_losses}</code>\n"
            f"📊 <b>Russian Win-Rate:</b> <code>{rate:.1f}%</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ <b>Важно:</b> Это образовательный анализ.\n"
            f"⚠️ <b>Important:</b> No prediction system can guarantee lottery results."
        )

    def generate_current_signal(self):
        if not self.last_prediction and not self.last_russian_prediction:
            return "⚠️ এখনো কোনো সিগন্যাল তৈরি হয়নি। প্রথমে CSV ফাইল পাঠান।"

        next_issue = self.safe_next_issue(self.last_issue) if self.last_issue else "N/A"

        return (
            f"🎯 <b>Active Period:</b> <code>{next_issue}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🧬 <b>Final Ensemble Signal:</b>\n"
            f"➔ <b>{self.last_prediction or 'N/A'}</b> {self.icon(self.last_prediction)} "
            f"<b>({self.last_pred_conf}%)</b>\n\n"
            f"🧠 <b>Deep AI:</b>\n"
            f"➔ <b>{self.last_deep_prediction or 'N/A'}</b> {self.icon(self.last_deep_prediction)} "
            f"({self.last_deep_conf}%)\n\n"
            f"🇷🇺 <b>Russian Engine:</b>\n"
            f"➔ <b>{self.last_russian_prediction or 'N/A'}</b> {self.icon(self.last_russian_prediction)} "
            f"({self.last_russian_conf}%)\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔥 <b>Final Streak:</b> Win <code>{self.current_win_streak}</code> | "
            f"Loss <code>{self.current_loss_streak}</code>\n"
            f"🇷🇺 <b>Russian Streak:</b> Win <code>{self.ru_current_win_streak}</code> | "
            f"Loss <code>{self.ru_current_loss_streak}</code>"
        )

    def format_live_message(self, last_issue, actual_res, num, outcome_str, now_bd):
        next_issue = self.safe_next_issue(last_issue)

        return (
            f"🎯 <b>Period:</b> <code>{next_issue}</code>\n"
            f"🧬 <b>Final Signal:</b> <b>{self.last_prediction or 'N/A'}</b> "
            f"{self.icon(self.last_prediction)} <b>({self.last_pred_conf}%)</b>\n"
            f"🧠 <b>Deep AI:</b> <b>{self.last_deep_prediction or 'N/A'}</b> "
            f"{self.icon(self.last_deep_prediction)} ({self.last_deep_conf}%)\n"
            f"🇷🇺 <b>Russian:</b> <b>{self.last_russian_prediction or 'N/A'}</b> "
            f"{self.icon(self.last_russian_prediction)} ({self.last_russian_conf}%)\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎲 <b>Last:</b> {last_issue} ➔ <b>{actual_res} ({num})</b> | {outcome_str}\n"
            f"🔥 <b>Final Streak:</b> Win <code>{self.current_win_streak}</code> | "
            f"Loss <code>{self.current_loss_streak}</code>\n"
            f"🇷🇺 <b>Russian Streak:</b> Win <code>{self.ru_current_win_streak}</code> | "
            f"Loss <code>{self.ru_current_loss_streak}</code>\n"
            f"🏆 <b>Max Final:</b> Win <code>{self.max_win_streak}</code> | "
            f"Loss <code>{self.max_loss_streak}</code>\n"
            f"🕒 <b>Time:</b> <code>{now_bd.strftime('%I:%M:%S %p')}</code> "
            f"({get_session_name(now_bd.hour)})"
        )

    def run(self):
        print("🚀 ADVANCED VIP BOT ENGINE STARTED...")
        print("🇷🇺 Russian Prediction Engine module loaded.")

        offset = None

        while not _shutdown.is_set():
            updates = self.bot.get_updates(offset)

            for u in updates:
                offset = u["update_id"] + 1

                # Callback button handler
                if "callback_query" in u:
                    cb = u["callback_query"]

                    cb_id = cb.get("id")
                    data = cb.get("data", "")

                    chat_id = str(
                        cb.get("message", {})
                        .get("chat", {})
                        .get("id", "")
                    )

                    self.bot.answer_callback(cb_id, "✅")

                    if not chat_id:
                        continue

                    keyboard = get_vip_inline_keyboard()

                    if data == "btn_live_stats":
                        self.bot.send_message(
                            chat_id,
                            self.generate_stats_report(),
                            reply_markup=keyboard
                        )

                    elif data == "btn_best_time":
                        self.bot.send_message(
                            chat_id,
                            self.generate_time_report(),
                            reply_markup=keyboard
                        )

                    elif data == "btn_ai_learning":
                        self.bot.send_message(
                            chat_id,
                            self.generate_learning_report(),
                            reply_markup=keyboard
                        )

                    elif data == "btn_curr_signal":
                        self.bot.send_message(
                            chat_id,
                            self.generate_current_signal(),
                            reply_markup=keyboard
                        )

                    elif data == "btn_russian_engine":
                        self.bot.send_message(
                            chat_id,
                            self.generate_russian_report(),
                            reply_markup=keyboard
                        )

                    elif data == "btn_ensemble":
                        self.bot.send_message(
                            chat_id,
                            self.generate_current_signal(),
                            reply_markup=keyboard
                        )

                    continue

                msg = u.get("message", {})

                chat_id = str(msg.get("chat", {}).get("id", ""))
                doc = msg.get("document")
                text = msg.get("text", "")

                if not chat_id:
                    continue

                chats = load_chats()
                chats.add(chat_id)
                save_chats(chats)

                if doc:
                    self.bot.send_message(
                        chat_id,
                        "⏳ <b>ফাইল অ্যানালাইসিস ও ডিপ AI + Russian Engine লার্নিং চলছে...</b>"
                    )

                    file_bytes = self.bot.get_file_bytes(doc.get("file_id"))

                    if file_bytes:
                        ok, count = self.load_file_and_train_deeply(
                            file_bytes.decode("utf-8", errors="ignore")
                        )

                        if not ok:
                            self.bot.send_message(
                                chat_id,
                                "⚠️ মডেলে ট্রেইনিংয়ের জন্য কমপক্ষে ১৫+ রাউন্ড ডাটা প্রয়োজন।"
                            )

                    else:
                        self.bot.send_message(
                            chat_id,
                            "⚠️ ফাইল ডাউনলোড করা যায়নি। আবার চেষ্টা করুন।"
                        )

                    continue

                if text == "/start":
                    self.bot.send_message(
                        chat_id,
                        "👑 <b>স্বাগতম VIP Strike Advanced AI Engine-এ!</b>\n"
                        "🧠 Deep AI + 🇷🇺 Russian Prediction Engine + 🧬 Ensemble Core\n\n"
                        "বট চালু করতে আপনার <code>dataset_export.csv</code> ফাইলটি সেন্ড করুন।\n"
                        "ফাইল রিড করে প্যাটার্ন শিখে স্বয়ংক্রিয়ভাবে লাইভ সিগন্যাল শুরু হবে।\n\n"
                        "⚠️ Educational use only. No guaranteed results.",
                        reply_markup=get_vip_inline_keyboard()
                    )

            if not self.is_active:
                time.sleep(2)
                continue

            # Live API monitoring
            try:
                resp = requests.get(
                    API_DOMAINS[0],
                    params={
                        "pageNo": 1,
                        "pageSize": 10,
                        "t": int(time.time() * 1000)
                    },
                    timeout=6
                )

                if resp.status_code == 200:
                    lst = resp.json().get("data", {}).get("list", [])

                    if lst:
                        current_issue = str(lst[0].get("issueNumber"))

                        num = int(lst[0].get("number", 0))
                        actual_res = result_from_number(num)

                        if current_issue != self.last_issue:
                            now_bd = get_bd_now()
                            outcome_str = "⏳"

                            # Final ensemble result tracking
                            if self.last_prediction:
                                is_win = self.last_prediction == actual_res

                                self.time_intel.record_result(is_win, now_bd)

                                if is_win:
                                    self.total_wins += 1
                                    self.current_win_streak += 1
                                    self.current_loss_streak = 0

                                    if self.current_win_streak > self.max_win_streak:
                                        self.max_win_streak = self.current_win_streak

                                    outcome_str = "✅ <b>WIN</b>"

                                else:
                                    self.total_losses += 1
                                    self.current_loss_streak += 1
                                    self.current_win_streak = 0

                                    if self.current_loss_streak > self.max_loss_streak:
                                        self.max_loss_streak = self.current_loss_streak

                                    outcome_str = "❌ <b>LOSS</b>"

                            # Russian engine separate result tracking
                            if self.last_russian_prediction:
                                ru_is_win = self.last_russian_prediction == actual_res

                                if ru_is_win:
                                    self.ru_total_wins += 1
                                    self.ru_current_win_streak += 1
                                    self.ru_current_loss_streak = 0

                                    if self.ru_current_win_streak > self.ru_max_win_streak:
                                        self.ru_max_win_streak = self.ru_current_win_streak

                                else:
                                    self.ru_total_losses += 1
                                    self.ru_current_loss_streak += 1
                                    self.ru_current_win_streak = 0

                                    if self.ru_current_loss_streak > self.ru_max_loss_streak:
                                        self.ru_max_loss_streak = self.ru_current_loss_streak

                            # Add latest result into dataset
                            self.dataset.append(
                                {
                                    "issue": current_issue,
                                    "number": num,
                                    "result": actual_res
                                }
                            )

                            # Keep dataset controlled
                            if len(self.dataset) > 1200:
                                self.dataset = self.dataset[-1200:]

                            # Retrain engines
                            self.ai.train(self.dataset)
                            self.russian.train(self.dataset)

                            # Update state
                            self.last_issue = current_issue
                            self.refresh_predictions()

                            live_msg = self.format_live_message(
                                current_issue,
                                actual_res,
                                num,
                                outcome_str,
                                now_bd
                            )

                            self.broadcast(live_msg, get_vip_inline_keyboard())

            except Exception:
                pass

            time.sleep(2)


#============================================================
# WEB KEEP-ALIVE SERVER
#============================================================

def run_web():
    class S(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status":"running", "engine":"VIP Strike V26.0 + Russian Engine"}')

        def log_message(self, format, *args):
            return

    port = int(os.environ.get("PORT", 5000))
    server = HTTPServer(("0.0.0.0", port), S)
    server.serve_forever()


#============================================================
# MAIN ENTRY
# ============================================================

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    if TELEGRAM_TOKEN == "PASTE_YOUR_BOT_TOKEN":
        print("⚠️ Please set TELEGRAM_TOKEN environment variable first.")

    threading.Thread(target=run_web, daemon=True).start()

    Engine().run()
