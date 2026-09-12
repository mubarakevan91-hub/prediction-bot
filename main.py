#============================================================
# ULTIMATE VIP STRIKE V29.0 - QUANTUM ENSEMBLE AI (LIVE SYNC)
# 5-LAYER AI + LIVE MARKET SYNC + BULLETPROOF LOOP
#============================================================
"""
Advanced VIP Signal Bot
5-Layer AI Ensemble Core
Live Market Synchronization
Telegram Bot UI
Quantum Pattern Analysis
"""
import os
import json
import time
import threading
import signal
import csv
import io
import math
import random
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler

#============================================================
# CONFIG
#============================================================
TELEGRAM_TOKEN = "8858558197:AAHvvS-rh9j1U9grv3SzmyqPsxN1FHNlv6E"
DEFAULT_CHAT_ID = "8395823375"
CHATS_FILE = "allowed_chats.json"
API_DOMAINS = [
    "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"
]
BD_TZ = timezone(timedelta(hours=6))
_shutdown = threading.Event()

#============================================================
# CORE HELPERS
#============================================================
def signal_handler(sig, frame):
    _shutdown.set()

def get_bd_now():
    return datetime.now(BD_TZ)

def get_session_name(hour):
    if 5 <= hour < 12: return "🌅 সকাল (Morning) "
    elif 12 <= hour < 16: return "☀️ দুপুর (Noon) "
    elif 16 <= hour < 18: return "🌇 বিকাল (Afternoon) "
    elif 18 <= hour < 21: return "🌆 সন্ধ্যা (Evening) "
    else: return "🌙 রাত (Night) "

def load_chats():
    chats = set()
    if DEFAULT_CHAT_ID: chats.add(str(DEFAULT_CHAT_ID))
    if os.path.exists(CHATS_FILE):
        try:
            with open(CHATS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, list): chats.update([str(x) for x in loaded])
        except Exception: pass
    return chats

def save_chats(chats_set):
    try:
        with open(CHATS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(chats_set), f)
    except Exception: pass

def result_from_number(num):
    try: num = int(num)
    except Exception: num = 0
    return "BIG" if num >= 5 else "SMALL"

def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))

#============================================================
# 🧠 1. DEEP PATTERN AI ENGINE
#============================================================
class DeepPatternEngine:
    def __init__(self):
        self.markov4 = defaultdict(lambda: [0, 0])
        self.markov3 = defaultdict(lambda: [0, 0])
        self.markov2 = defaultdict(lambda: [0, 0])
        self.streak_reversion = defaultdict(lambda: [0, 0])
        self.is_fully_trained = False
        self.confidence_score = 0.0

    def train(self, dataset):
        if len(dataset) < 15:
            self.is_fully_trained = False
            return False
        self.markov4.clear(); self.markov3.clear(); self.markov2.clear(); self.streak_reversion.clear()
        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        n = len(seq)
        for i in range(n - 2): self.markov2[(seq[i], seq[i + 1])][seq[i + 2]] += 1
        for i in range(n - 3): self.markov3[(seq[i], seq[i + 1], seq[i + 2])][seq[i + 3]] += 1
        for i in range(n - 4): self.markov4[(seq[i], seq[i + 1], seq[i + 2], seq[i + 3])][seq[i + 4]] += 1
        current_streak = 1
        for i in range(1, n):
            if seq[i] == seq[i - 1]: current_streak += 1
            else:
                self.streak_reversion[min(current_streak, 8)][seq[i]] += 1
                current_streak = 1
        self.is_fully_trained = True
        return True

    def predict(self, dataset):
        if not self.is_fully_trained or len(dataset) < 5: return None, 0
        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        votes, weights = [], []
        if len(seq) >= 4:
            counts = self.markov4.get(tuple(seq[-4:]))
            if counts and sum(counts) >= 2:
                votes.append((counts[1] + 1) / (sum(counts) + 2)); weights.append(0.45)
        if len(seq) >= 3:
            counts = self.markov3.get(tuple(seq[-3:]))
            if counts and sum(counts) >= 2:
                votes.append((counts[1] + 1) / (sum(counts) + 2)); weights.append(0.30)
        if len(seq) >= 2:
            counts = self.markov2.get(tuple(seq[-2:]))
            if counts and sum(counts) >= 2:
                votes.append((counts[1] + 1) / (sum(counts) + 2)); weights.append(0.15)
        if not votes: return "BIG" if seq[-1] == 1 else "SMALL", 60
        total_weight = sum(weights)
        weighted_prob = sum(v * w for v, w in zip(votes, weights)) / total_weight
        pred = "BIG" if weighted_prob >= 0.50 else "SMALL"
        conf = int(clamp(abs(weighted_prob - 0.50) * 240 + 68, 60, 99))
        self.confidence_score = conf
        return pred, conf

#============================================================
# 🇷🇺 2. RUSSIAN PREDICTION ENGINE
#============================================================
class RussianPredictionEngine:
    def __init__(self):
        self.markov4 = defaultdict(lambda: [0, 0])
        self.markov3 = defaultdict(lambda: [0, 0])
        self.markov2 = defaultdict(lambda: [0, 0])
        self.streak_profile = defaultdict(lambda: [0, 0])
        self.trained = False
        self.base_rate_big = 0.5
        self.recent_bias_big = 0.5
        self.alternation_score = 0.5
        self.confidence_score = 0
        self.debug = {}

    def train(self, dataset):
        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        n = len(seq)
        if n < 10: self.trained = False; return False
        self.markov4.clear(); self.markov3.clear(); self.markov2.clear(); self.streak_profile.clear()
        self.base_rate_big = sum(seq) / float(n)
        recent = seq[-30:]
        weight_sum, weighted_big = 0.0, 0.0
        for idx, val in enumerate(recent):
            w = 0.95 ** (len(recent) - 1 - idx)
            weight_sum += w
            if val == 1: weighted_big += w
        self.recent_bias_big = weighted_big / weight_sum if weight_sum > 0 else 0.5
        changes = sum(1 for i in range(1, n) if seq[i] != seq[i - 1])
        self.alternation_score = changes / float(max(1, n - 1))
        for i in range(n - 2): self.markov2[(seq[i], seq[i + 1])][seq[i + 2]] += 1
        for i in range(n - 3): self.markov3[(seq[i], seq[i + 1], seq[i + 2])][seq[i + 3]] += 1
        for i in range(n - 4): self.markov4[(seq[i], seq[i + 1], seq[i + 2], seq[i + 3])][seq[i + 4]] += 1
        self.trained = True
        return True

    def predict(self, dataset):
        if not self.trained or len(dataset) < 6: return None, 0, {}
        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        last = seq[-1]
        votes, weights = [], []
        def add_vote(prob_big, weight): votes.append(prob_big); weights.append(weight)
        if len(seq) >= 5:
            counts = self.markov4.get(tuple(seq[-4:]))
            if counts and sum(counts) >= 3: add_vote((counts[1] + 1) / (sum(counts) + 2), 0.32)
        if len(seq) >= 4:
            counts = self.markov3.get(tuple(seq[-3:]))
            if counts and sum(counts) >= 3: add_vote((counts[1] + 1) / (sum(counts) + 2), 0.24)
        add_vote(self.base_rate_big, 0.07)
        add_vote(self.recent_bias_big, 0.10)
        alt = self.alternation_score
        if alt >= 0.58: add_vote(0.15 if last == 1 else 0.85, min(0.22, (alt - 0.50) * 0.9))
        elif alt <= 0.42: add_vote(0.85 if last == 1 else 0.15, min(0.22, (0.50 - alt) * 0.9))
        else: add_vote(0.50, 0.03)
        if not votes: return None, 0, {}
        total_weight = sum(weights)
        weighted_prob = sum(v * w for v, w in zip(votes, weights)) / total_weight
        pred = "BIG" if weighted_prob >= 0.50 else "SMALL"
        conf = int(clamp(62 + abs(weighted_prob - 0.50) * 50, 58, 98))
        self.confidence_score = conf
        self.debug = {"weighted_prob": weighted_prob, "alternation": alt}
        return pred, conf, self.debug

#============================================================
# 🧮 3. BAYESIAN SEQUENCE ENGINE
#============================================================
class BayesianSequenceEngine:
    def __init__(self):
        self.transitions = defaultdict(lambda: defaultdict(int))
        self.priors = {"BIG": 0.5, "SMALL": 0.5}
        self.trained = False
        self.confidence_score = 0

    def train(self, dataset):
        seq = [str(d.get("result", "")).upper() for d in dataset]
        n = len(seq)
        if n < 10: self.trained = False; return False
        big_count = seq.count("BIG")
        self.priors["BIG"] = (big_count + 1) / (n + 2)
        self.priors["SMALL"] = 1.0 - self.priors["BIG"]
        self.transitions.clear()
        for i in range(n - 1): self.transitions[seq[i]][seq[i+1]] += 1
        self.trained = True
        return True

    def predict(self, dataset):
        if not self.trained or len(dataset) < 2: return None, 0
        seq = [str(d.get("result", "")).upper() for d in dataset]
        last = seq[-1]
        prior_big, prior_small = self.priors["BIG"], self.priors["SMALL"]
        trans_big = self.transitions[last].get("BIG", 0) + 1
        trans_small = self.transitions[last].get("SMALL", 0) + 1
        total_trans = trans_big + trans_small
        likelihood_big = trans_big / total_trans
        likelihood_small = trans_small / total_trans
        post_big = prior_big * likelihood_big
        post_small = prior_small * likelihood_small
        total_post = post_big + post_small
        prob_big = post_big / total_post if total_post > 0 else 0.5
        pred = "BIG" if prob_big >= 0.5 else "SMALL"
        conf = int(clamp(60 + abs(prob_big - 0.5) * 60, 55, 95))
        self.confidence_score = conf
        return pred, conf

#============================================================
# 🧬 4. NEURAL NETWORK SIMULATOR (Pure Python MLP)
#============================================================
class NeuralNetworkSimulator:
    def __init__(self, input_size=10, hidden_size=20):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.w1 = [[random.uniform(-0.5, 0.5) for _ in range(hidden_size)] for _ in range(input_size)]
        self.b1 = [0.0] * hidden_size
        self.w2 = [[random.uniform(-0.5, 0.5)] for _ in range(hidden_size)]
        self.b2 = 0.0
        self.learning_rate = 0.01

    def sigmoid(self, x):
        return 1.0 / (1.0 + math.exp(-max(-500, min(500, x))))

    def sigmoid_derivative(self, x):
        s = self.sigmoid(x)
        return s * (1.0 - s)

    def forward(self, inputs):
        self.hidden_inputs, self.hidden_outputs = [], []
        for j in range(self.hidden_size):
            val = self.b1[j]
            for i in range(self.input_size): val += inputs[i] * self.w1[i][j]
            self.hidden_inputs.append(val)
            self.hidden_outputs.append(self.sigmoid(val))
        out_val = self.b2
        for j in range(self.hidden_size): out_val += self.hidden_outputs[j] * self.w2[j][0]
        self.out_val = out_val
        return self.sigmoid(out_val)

    def train_step(self, inputs, target):
        output = self.forward(inputs)
        out_error = target - output
        out_delta = out_error * self.sigmoid_derivative(self.out_val)
        hidden_deltas = []
        for j in range(self.hidden_size):
            error = out_delta * self.w2[j][0]
            hidden_deltas.append(error * self.sigmoid_derivative(self.hidden_inputs[j]))
        for j in range(self.hidden_size):
            self.w2[j][0] += self.learning_rate * out_delta * self.hidden_outputs[j]
            for i in range(self.input_size):
                self.w1[i][j] += self.learning_rate * hidden_deltas[j] * inputs[i]
        self.b2 += self.learning_rate * out_delta
        for j in range(self.hidden_size): self.b1[j] += self.learning_rate * hidden_deltas[j]

    def train_on_dataset(self, dataset, epochs=3):
        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        for _ in range(epochs):
            for i in range(self.input_size, len(seq)):
                self.train_step(seq[i-self.input_size:i], seq[i])

    def predict(self, dataset):
        if len(dataset) < self.input_size: return None, 0
        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        prob = self.forward(seq[-self.input_size:])
        pred = "BIG" if prob >= 0.5 else "SMALL"
        conf = int(clamp(abs(prob - 0.5) * 200 + 55, 55, 95))
        return pred, conf

#============================================================
# 🌊 5. HARMONIC CYCLE ENGINE
#============================================================
class HarmonicCycleEngine:
    def __init__(self):
        self.trained = False
        self.confidence_score = 0
        self.best_lag = 1
        self.best_corr = 0.0

    def train(self, dataset):
        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        n = len(seq)
        if n < 20: self.trained = False; return False
        mean = sum(seq) / n
        var = sum((x - mean) ** 2 for x in seq) / n
        if var == 0: self.trained = True; return True
        best_corr, best_lag = -1, 1
        for lag in range(1, min(50, n // 2)):
            corr = sum((seq[i] - mean) * (seq[i+lag] - mean) for i in range(n - lag)) / ((n - lag) * var)
            if corr > best_corr: best_corr = corr; best_lag = lag
        self.best_lag = best_lag
        self.best_corr = best_corr
        self.trained = True
        return True

    def predict(self, dataset):
        if not self.trained or len(dataset) < self.best_lag: return None, 0
        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        last_val = seq[-self.best_lag]
        if self.best_corr > 0.1: pred = "BIG" if last_val == 1 else "SMALL"
        elif self.best_corr < -0.1: pred = "SMALL" if last_val == 1 else "BIG"
        else: pred = "BIG" if last_val == 1 else "SMALL"
        conf = int(clamp(60 + abs(self.best_corr) * 30, 55, 95))
        self.confidence_score = conf
        return pred, conf

#============================================================
# 🕒 TIME INTELLIGENCE
#============================================================
class TimeIntelligence:
    def __init__(self):
        self.session_wins = defaultdict(int)
        self.session_total = defaultdict(int)
        self.hourly_wins = defaultdict(int)
        self.hourly_total = defaultdict(int)
        self.history_records = []

    def record_result(self, is_win, timestamp_dt):
        hour = timestamp_dt.hour
        session = get_session_name(hour)
        self.session_total[session] += 1
        self.hourly_total[hour] += 1
        if is_win:
            self.session_wins[session] += 1
            self.hourly_wins[hour] += 1
        self.history_records.append({"is_win": is_win, "dt": timestamp_dt})

    def get_best_session_and_time(self):
        best_session, best_session_rate = "N/A", 0.0
        for s, total in self.session_total.items():
            if total >= 3:
                rate = (self.session_wins[s] / total) * 100
                if rate > best_session_rate: best_session_rate = rate; best_session = s
        best_hour_str, best_hour_rate = "N/A", 0.0
        for h, total in self.hourly_total.items():
            if total >= 2:
                rate = (self.hourly_wins[h] / total) * 100
                if rate > best_hour_rate:
                    best_hour_rate = rate
                    best_hour_str = datetime(2026, 1, 1, h, 0).strftime("%I:00 %p")
        return best_session, best_session_rate, best_hour_str, best_hour_rate

#============================================================
# 🤖 TELEGRAM BOT CLIENT
#============================================================
class TelegramBot:
    def __init__(self, token):
        self.url = f"https://api.telegram.org/bot{token}/"

    def send_message(self, chat_id, text, reply_markup=None):
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
        if reply_markup: payload["reply_markup"] = reply_markup
        try: requests.post(self.url + "sendMessage", json=payload, timeout=8)
        except Exception as e: print(f"⚠️ Telegram Send Error: {e}")

    def answer_callback(self, callback_id, text=""):
        try: requests.post(self.url + "answerCallbackQuery", data={"callback_query_id": callback_id, "text": text}, timeout=4)
        except Exception: pass

    def get_file_bytes(self, file_id):
        try:
            res = requests.get(self.url + "getFile", params={"file_id": file_id}, timeout=10).json()
            path = res.get("result", {}).get("file_path")
            if path:
                file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{path}"
                return requests.get(file_url, timeout=25).content
        except Exception: pass
        return None

    def get_updates(self, offset=None):
        try:
            params = {"timeout": 2}
            if offset is not None: params["offset"] = offset
            res = requests.get(self.url + "getUpdates", params=params, timeout=8)
            if res.status_code == 200: return res.json().get("result", [])
        except Exception: pass
        return []

#============================================================
# VIP INLINE KEYBOARD
#============================================================
def get_vip_inline_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📊 লাইভ পরিসংখ্যান", "callback_data": "btn_live_stats"}, {"text": "🕒 সেরা উইনিং টাইম", "callback_data": "btn_best_time"}],
            [{"text": "🧠 AI লার্নিং", "callback_data": "btn_ai_learning"}, {"text": "🎯 বর্তমান সিগন্যাল", "callback_data": "btn_curr_signal"}],
            [{"text": "🇷🇺 Russian Engine", "callback_data": "btn_russian_engine"}, {"text": "🧬 Ensemble Core", "callback_data": "btn_ensemble"}]
        ]
    }

#============================================================
# ⚙️ MAIN ENGINE & CONTROLLER (LIVE SYNC EDITION)
#============================================================
class Engine:
    def __init__(self):
        self.dataset = []
        self.ai = DeepPatternEngine()
        self.russian = RussianPredictionEngine()
        self.bayesian = BayesianSequenceEngine()
        self.neural = NeuralNetworkSimulator()
        self.harmonic = HarmonicCycleEngine()
        self.time_intel = TimeIntelligence()
        self.bot = TelegramBot(TELEGRAM_TOKEN)
        self.last_issue = None
        self.last_prediction = None
        self.last_pred_conf = 0
        self.last_deep_prediction, self.last_deep_conf = None, 0
        self.last_russian_prediction, self.last_russian_conf = None, 0
        self.last_bayes_prediction, self.last_bayes_conf = None, 0
        self.last_nn_prediction, self.last_nn_conf = None, 0
        self.last_harm_prediction, self.last_harm_conf = None, 0
        self.is_active = False
        self.current_win_streak, self.current_loss_streak = 0, 0
        self.max_win_streak, self.max_loss_streak = 0, 0
        self.total_wins, self.total_losses = 0, 0

    def icon(self, pred):
        if pred == "BIG": return "🟢"
        if pred == "SMALL": return "🔴"
        return "⚪"

    def broadcast(self, msg, keyboard=None):
        chats = load_chats()
        for cid in list(chats): self.bot.send_message(cid, msg, reply_markup=keyboard)

    def safe_next_issue(self, issue):
        try: return str(int(issue) + 1)
        except Exception: return f"{issue}+1"

    def parse_csv_records(self, content_str):
        records = []
        try:
            reader = csv.reader(io.StringIO(content_str))
            for row in reader:
                if not row: continue
                first = str(row[0]).strip().lower()
                if first in {"period", "issue", "issuenumber", "id"}: continue
                issue = str(row[0]).strip()
                num = 0
                if len(row) > 1:
                    txt = str(row[1]).strip()
                    if txt.isdigit(): num = int(txt)
                result = None
                if len(row) > 2:
                    r = str(row[2]).strip().upper()
                    if r in {"BIG", "SMALL"}: result = r
                if result is None: result = result_from_number(num)
                records.append({"issue": issue, "number": num, "result": result})
        except Exception: pass
        return records

    def make_predictions(self, dataset):
        deep_pred, deep_conf = self.ai.predict(dataset)
        ru_pred, ru_conf, ru_debug = self.russian.predict(dataset)
        bayes_pred, bayes_conf = self.bayesian.predict(dataset)
        nn_pred, nn_conf = self.neural.predict(dataset)
        harm_pred, harm_conf = self.harmonic.predict(dataset)

        models = [
            ("Deep", deep_pred, deep_conf, 0.25),
            ("Russian", ru_pred, ru_conf, 0.25),
            ("Bayesian", bayes_pred, bayes_conf, 0.20),
            ("Neural", nn_pred, nn_conf, 0.15),
            ("Harmonic", harm_pred, harm_conf, 0.15)
        ]
        valid_models = [(name, pred, conf, w) for name, pred, conf, w in models if pred is not None]
        if not valid_models:
            return {"final_pred": None, "final_conf": 0, "deep_pred": deep_pred, "deep_conf": deep_conf,
                    "ru_pred": ru_pred, "ru_conf": ru_conf, "ru_debug": ru_debug,
                    "bayes_pred": bayes_pred, "bayes_conf": bayes_conf,
                    "nn_pred": nn_pred, "nn_conf": nn_conf,
                    "harm_pred": harm_pred, "harm_conf": harm_conf}

        total_weight = sum(w for _, _, _, w in valid_models)
        weighted_prob_big = 0.0
        for name, pred, conf, w in valid_models:
            prob_big = conf / 100.0 if pred == "BIG" else 1.0 - conf / 100.0
            weighted_prob_big += prob_big * (w / total_weight)

        final_pred = "BIG" if weighted_prob_big >= 0.50 else "SMALL"
        conviction = abs(weighted_prob_big - 0.50) * 2
        final_conf = int(clamp(65 + conviction * 30, 60, 99))
        
        unique_preds = set(pred for _, pred, _, _ in valid_models)
        if len(unique_preds) == 1: final_conf = min(99, final_conf + 5)

        return {
            "deep_pred": deep_pred, "deep_conf": deep_conf,
            "ru_pred": ru_pred, "ru_conf": ru_conf, "ru_debug": ru_debug,
            "bayes_pred": bayes_pred, "bayes_conf": bayes_conf,
            "nn_pred": nn_pred, "nn_conf": nn_conf,
            "harm_pred": harm_pred, "harm_conf": harm_conf,
            "final_pred": final_pred, "final_conf": final_conf
        }

    def refresh_predictions(self):
        preds = self.make_predictions(self.dataset)
        self.last_deep_prediction, self.last_deep_conf = preds.get("deep_pred"), preds.get("deep_conf", 0)
        self.last_russian_prediction, self.last_russian_conf = preds.get("ru_pred"), preds.get("ru_conf", 0)
        self.last_bayes_prediction, self.last_bayes_conf = preds.get("bayes_pred"), preds.get("bayes_conf", 0)
        self.last_nn_prediction, self.last_nn_conf = preds.get("nn_pred"), preds.get("nn_conf", 0)
        self.last_harm_prediction, self.last_harm_conf = preds.get("harm_pred"), preds.get("harm_conf", 0)
        self.last_prediction, self.last_pred_conf = preds.get("final_pred"), preds.get("final_conf", 0)

    def initialize_live_state(self):
        """Fetches the actual current live period from the website and syncs the bot."""
        try:
            resp = requests.get(API_DOMAINS[0], params={"pageNo": 1, "pageSize": 2, "t": int(time.time() * 1000)}, timeout=6)
            if resp.status_code == 200:
                lst = resp.json().get("data", {}).get("list", [])
                if lst:
                    # lst[0] is the latest completed issue on the website
                    current_live_issue = str(lst[0].get("issueNumber"))
                    self.last_issue = current_live_issue
                    
                    # Generate prediction for the NEXT live issue
                    self.refresh_predictions()
                    
                    next_issue = self.safe_next_issue(self.last_issue)
                    now_bd = get_bd_now()
                    msg = (
                        f"👑 <b>QUANTUM ENSEMBLE AI TRAINED & SYNCED</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"📚 <b>Historical Data Learned:</b> <code>{len(self.dataset)} Rounds</code>\n"
                        f"🌐 <b>Live Market Synced:</b> <code>Period {self.last_issue}</code>\n"
                        f"🎯 <b>Next Live Prediction:</b> <code>{next_issue}</code>\n"
                        f"🧬 <b>Final Signal:</b> <b>{self.last_prediction or 'N/A'}</b> "
                        f"{self.icon(self.last_prediction)} <b>({self.last_pred_conf}%)</b>\n"
                        f"🧠 <b>Deep AI:</b> <b>{self.last_deep_prediction or 'N/A'}</b> ({self.last_deep_conf}%)\n"
                        f"🇷🇺 <b>Russian:</b> <b>{self.last_russian_prediction or 'N/A'}</b> ({self.last_russian_conf}%)\n"
                        f"🧮 <b>Bayesian:</b> <b>{self.last_bayes_prediction or 'N/A'}</b> ({self.last_bayes_conf}%)\n"
                        f"🧬 <b>Neural Net:</b> <b>{self.last_nn_prediction or 'N/A'}</b> ({self.last_nn_conf}%)\n"
                        f"🌊 <b>Harmonic:</b> <b>{self.last_harm_prediction or 'N/A'}</b> ({self.last_harm_conf}%)\n"
                        f"🕒 <b>Sync Time:</b> <code>{now_bd.strftime('%I:%M:%S %p')}</code>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🎓 <i>Live market prediction started based on historical patterns.</i>"
                    )
                    self.broadcast(msg, get_vip_inline_keyboard())
                    return True
        except Exception as e:
            print(f"⚠️ Live sync error: {e}")
        return False

    def load_file_and_train_deeply(self, content_str):
        records = self.parse_csv_records(content_str)
        if len(records) < 15: return False, 0
        
        # 1. Train models on historical data
        self.dataset = records
        self.ai.train(self.dataset)
        self.russian.train(self.dataset)
        self.bayesian.train(self.dataset)
        self.neural.train_on_dataset(self.dataset[-300:] if len(self.dataset) > 300 else self.dataset, epochs=1)
        self.harmonic.train(self.dataset[-300:] if len(self.dataset) > 300 else self.dataset)
        
        self.is_active = True
        
        # 2. Sync with live market (Crucial Fix)
        self.initialize_live_state()
        
        return True, len(records)

    def generate_stats_report(self):
        total = self.total_wins + self.total_losses
        win_rate = (self.total_wins / total * 100) if total > 0 else 0.0
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
            f"📈 <b>Overall Win-Rate:</b> <code>{win_rate:.1f}%</code>"
        )

    def generate_time_report(self):
        best_session, s_rate, best_hour, h_rate = self.time_intel.get_best_session_and_time()
        now_bd = get_bd_now()
        return (
            f"🕒 <b>সেরা উইনিং টাইম ইন্টেলিজেন্স</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 <b>আজকের তারিখ:</b> <code>{now_bd.strftime('%d %b, %Y')}</code>\n"
            f"⏰ <b>বর্তমান সময়:</b> <code>{now_bd.strftime('%I:%M %p')}</code> ({get_session_name(now_bd.hour)})\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🥇 <b>সর্বোচ্চ উইনিং সেশন:</b>\n➔ <b>{best_session}</b> (উইনরেট: <b>{s_rate:.1f}%</b>)\n\n"
            f"👑 <b>নির্দিষ্ট পিক টাইম:</b>\n➔ <b>{best_hour}</b> (উইনরেট: <b>{h_rate:.1f}%</b>)"
        )

    def generate_learning_report(self):
        return (
            f"🧠 <b>AI লার্নিং ও সিস্টেম অডিট</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📚 <b>লার্নিং স্ট্যাটাস:</b> Pattern Synchronized\n"
            f"🔬 <b>পর্যবেক্ষণ:</b> <code>মোট পরীক্ষিত: {len(self.time_intel.history_records)} রাউন্ড</code>\n"
            f"🛡️ <b>ভুল সিগন্যাল ফিল্টার:</b> <b>সক্রিয় (Active)</b>\n"
            f"🎓 <i>Advanced Analytical & Educational Pattern System.</i>"
        )

    def generate_current_signal(self):
        if not self.last_prediction: return "⚠️ এখনো কোনো সিগন্যাল তৈরি হয়নি। প্রথমে CSV ফাইল পাঠান।"
        next_issue = self.safe_next_issue(self.last_issue) if self.last_issue else "N/A"
        return (
            f"🎯 <b>Active Period:</b> <code>{next_issue}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🧬 <b>Final Ensemble Signal:</b>\n➔ <b>{self.last_prediction}</b> {self.icon(self.last_prediction)} <b>({self.last_pred_conf}%)</b>\n\n"
            f"🧠 <b>Deep AI:</b> <b>{self.last_deep_prediction}</b> ({self.last_deep_conf}%)\n"
            f"🇷🇺 <b>Russian:</b> <b>{self.last_russian_prediction}</b> ({self.last_russian_conf}%)\n"
            f"🧮 <b>Bayesian:</b> <b>{self.last_bayes_prediction}</b> ({self.last_bayes_conf}%)\n"
            f"🧬 <b>Neural Net:</b> <b>{self.last_nn_prediction}</b> ({self.last_nn_conf}%)\n"
            f"🌊 <b>Harmonic:</b> <b>{self.last_harm_prediction}</b> ({self.last_harm_conf}%)\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔥 <b>Streak:</b> Win <code>{self.current_win_streak}</code> | Loss <code>{self.current_loss_streak}</code>"
        )

    def format_live_message(self, last_issue, actual_res, num, outcome_str, now_bd):
        next_issue = self.safe_next_issue(last_issue)
        return (
            f"🎯 <b>Period:</b> <code>{next_issue}</code>\n"
            f"🧬 <b>Final Signal:</b> <b>{self.last_prediction}</b> {self.icon(self.last_prediction)} <b>({self.last_pred_conf}%)</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎲 <b>Last:</b> {last_issue} ➔ <b>{actual_res} ({num})</b> | {outcome_str}\n"
            f"🔥 <b>Streak:</b> Win <code>{self.current_win_streak}</code> | Loss <code>{self.current_loss_streak}</code>\n"
            f"🕒 <b>Time:</b> <code>{now_bd.strftime('%I:%M:%S %p')}</code> ({get_session_name(now_bd.hour)})"
        )

    def run(self):
        print("🚀 QUANTUM ENSEMBLE AI ENGINE STARTED (LIVE SYNC MODE)...")
        offset = None
        while not _shutdown.is_set():
            updates = self.bot.get_updates(offset)
            for u in updates:
                offset = u["update_id"] + 1
                if "callback_query" in u:
                    cb = u["callback_query"]
                    chat_id = str(cb.get("message", {}).get("chat", {}).get("id", ""))
                    data = cb.get("data", "")
                    self.bot.answer_callback(cb.get("id"), "✅")
                    if not chat_id: continue
                    keyboard = get_vip_inline_keyboard()
                    if data == "btn_live_stats": self.bot.send_message(chat_id, self.generate_stats_report(), reply_markup=keyboard)
                    elif data == "btn_best_time": self.bot.send_message(chat_id, self.generate_time_report(), reply_markup=keyboard)
                    elif data == "btn_ai_learning": self.bot.send_message(chat_id, self.generate_learning_report(), reply_markup=keyboard)
                    elif data in ["btn_curr_signal", "btn_ensemble", "btn_russian_engine"]: self.bot.send_message(chat_id, self.generate_current_signal(), reply_markup=keyboard)
                    continue
                
                msg = u.get("message", {})
                chat_id = str(msg.get("chat", {}).get("id", ""))
                doc = msg.get("document")
                text = msg.get("text", "")
                if not chat_id: continue
                
                chats = load_chats()
                chats.add(chat_id)
                save_chats(chats)
                
                if doc:
                    self.bot.send_message(chat_id, "⏳ <b>ফাইল অ্যানালাইসিস ও ৫-লেয়ার AI লার্নিং চলছে...</b>")
                    file_bytes = self.bot.get_file_bytes(doc.get("file_id"))
                    if file_bytes:
                        ok, count = self.load_file_and_train_deeply(file_bytes.decode("utf-8", errors="ignore"))
                        if not ok: self.bot.send_message(chat_id, "⚠️ মডেলে ট্রেইনিংয়ের জন্য কমপক্ষে ১৫+ রাউন্ড ডাটা প্রয়োজন।")
                    else: self.bot.send_message(chat_id, "⚠️ ফাইল ডাউনলোড করা যায়নি।")
                    continue
                
                if text == "/start":
                    self.bot.send_message(
                        chat_id,
                        "👑 <b>স্বাগতম VIP Strike Quantum AI Engine-এ!</b>\n"
                        "🧠 5-Layer Ensemble Core (Deep + Russian + Bayesian + Neural + Harmonic)\n\n"
                        "বট চালু করতে আপনার <code>dataset_export.csv</code> ফাইলটি সেন্ড করুন।\n"
                        "ফাইল রিড করে প্যাটার্ন শিখে স্বয়ংক্রিয়ভাবে লাইভ সিগন্যাল শুরু হবে।\n\n"
                        "🎓 Advanced Analytical & Educational Pattern System.",
                        reply_markup=get_vip_inline_keyboard()
                    )

            if not self.is_active:
                time.sleep(2)
                continue

            # Live API monitoring
            try:
                resp = requests.get(API_DOMAINS[0], params={"pageNo": 1, "pageSize": 10, "t": int(time.time() * 1000)}, timeout=6)
                if resp.status_code == 200:
                    lst = resp.json().get("data", {}).get("list", [])
                    if lst:
                        current_issue = str(lst[0].get("issueNumber"))
                        num = int(lst[0].get("number", 0))
                        actual_res = result_from_number(num)
                        
                        if current_issue != self.last_issue:
                            now_bd = get_bd_now()
                            outcome_str = "⏳"
                            
                            # Evaluate the prediction made for THIS current_issue
                            if self.last_prediction:
                                is_win = self.last_prediction == actual_res
                                self.time_intel.record_result(is_win, now_bd)
                                if is_win:
                                    self.total_wins += 1; self.current_win_streak += 1; self.current_loss_streak = 0
                                    if self.current_win_streak > self.max_win_streak: self.max_win_streak = self.current_win_streak
                                    outcome_str = "✅ <b>WIN</b>"
                                else:
                                    self.total_losses += 1; self.current_loss_streak += 1; self.current_win_streak = 0
                                    if self.current_loss_streak > self.max_loss_streak: self.max_loss_streak = self.current_loss_streak
                                    outcome_str = "❌ <b>LOSS</b>"
                            
                            # Update state to the newly completed issue
                            self.last_issue = current_issue
                            
                            # Append to live dataset for continuous learning
                            self.dataset.append({"issue": current_issue, "number": num, "result": actual_res})
                            if len(self.dataset) > 1500: self.dataset = self.dataset[-1500:]
                            
                            # Retrain models with new live data
                            try:
                                train_subset = self.dataset[-300:] if len(self.dataset) > 300 else self.dataset
                                self.ai.train(self.dataset)
                                self.russian.train(self.dataset)
                                self.bayesian.train(self.dataset)
                                self.neural.train_on_dataset(train_subset, epochs=1)
                                self.harmonic.train(train_subset)
                            except Exception as e:
                                print(f"⚠️ AI Training error: {e}")
                                
                            # Generate prediction for the NEXT issue
                            self.refresh_predictions()
                            
                            live_msg = self.format_live_message(current_issue, actual_res, num, outcome_str, now_bd)
                            self.broadcast(live_msg, get_vip_inline_keyboard())
            except Exception as e:
                print(f"⚠️ API Fetch error: {e}")
                
            time.sleep(2)

#============================================================
# WEB KEEP-ALIVE SERVER
#============================================================
def run_web():
    class S(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status":"running", "engine":"VIP Strike V29.0 Quantum Ensemble"}')
        def log_message(self, format, *args): return
    port = int(os.environ.get("PORT", 5000))
    server = HTTPServer(("0.0.0.0", port), S)
    server.serve_forever()

#============================================================
# MAIN ENTRY
#============================================================
if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    threading.Thread(target=run_web, daemon=True).start()
    
    engine = Engine()
    
    if os.path.exists("dataset.csv"):
        print("📂 dataset.csv found. Loading and training 5-Layer AI models...")
        try:
            with open("dataset.csv", "r", encoding="utf-8") as f:
                content = f.read()
            ok, count = engine.load_file_and_train_deeply(content)
            if ok: print(f"✅ Successfully trained on {count} records and synced to live market.")
            else: print("⚠️ Local dataset found but training failed (needs 15+ records).")
        except Exception as e:
            print(f"⚠️ Error reading local dataset: {e}")
    else:
        print("📂 No local dataset.csv found. Waiting for Telegram file upload...")
        
    engine.run()
