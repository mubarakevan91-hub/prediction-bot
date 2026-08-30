# ============================================================
# ULTIMATE VIP STRIKE V15 - PREMIUM META-LEARNING ENGINE
# Real ML: TF-LSTM + XGBoost + sklearn + pandas-ta 
# Lifelong Learning Brain + Reinforcement Learning
# ============================================================

import requests
import json
import time
import threading
from datetime import datetime
from collections import deque, Counter
import sys
import traceback
import os
import signal
import math
import random
from statistics import mean, stdev

# ============================================================
# WEB SERVER & SOCKETIO LIBRARIES (CORS Added for Cloud)
# ============================================================
from flask import Flask, render_template_string, jsonify, request
from flask_socketio import SocketIO, emit as socketio_emit
from flask_cors import CORS  # <--- No Localhost issue anymore

TELEGRAM_TOKEN   = "8946950031:AAEjErIWu-7H6jnXvUJw30eJ9olA_iuXrzo"
TELEGRAM_CHAT_ID = "8395823375"
API_URL          = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"
DATA_FILE        = "vip_strike_v15_data.json"
VERSION          = "V15-PREMIUM"

# ============================================================
# TELEGRAM SIGNAL SENDER FUNCTION
# ============================================================
def send_telegram_signal(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✉️ [TELEGRAM] Signal sent successfully.")
        else:
            print(f"⚠️ [TELEGRAM] Failed to send. Status: {response.status_code}")
    except Exception as e:
        print(f"❌ [TELEGRAM] Error sending message: {e}")

# ============================================================
# OPTIONAL IMPORTS (Machine Learning)
# ============================================================
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
except ImportError:
    PANDAS_TA_AVAILABLE = False

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

# ============================================================
# GLOBAL SHUTDOWN EVENT
# ============================================================
_shutdown_event = threading.Event()

def signal_handler(sig, frame):
    print("\n🛑 Shutting down gracefully...")
    _shutdown_event.set()

# ============================================================
# UTILITY FUNCTIONS
# ============================================================
def safe_divide(a, b, default=0.0):
    try:
        return default if b == 0 else a / b
    except: return default

def clamp(value, min_val, max_val):
    try:
        return max(min_val, min(max_val, value))
    except: return min_val

def safe_list(history, max_len=250):
    try:
        lst = list(history)
        return lst[:max_len] if max_len else lst
    except: return []

def safe_mean(data):
    return sum(data) / len(data) if data else 0.5

def safe_stdev(data):
    if len(data) < 2: return 0.0
    m = safe_mean(data)
    return math.sqrt(max(0, sum((x - m) ** 2 for x in data) / (len(data) - 1)))

def to_binary_list(history_newest_first):
    return [1 if h == 'BIG' else 0 for h in history_newest_first]

# ============================================================
# HISTORY MANAGER
# ============================================================
class HistoryManager:
    def __init__(self, maxlen=500):
        self._data = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def add(self, result):
        with self._lock: self._data.append(result)

    def get_newest_first(self, n=None):
        with self._lock: lst = list(self._data)
        lst.reverse()
        return lst[:n] if n is not None else lst

    def __len__(self):
        with self._lock: return len(self._data)

# ============================================================
# LIFELONG META-LEARNER (The AI Brain that Learns & Updates itself)
# ============================================================
class UltimateMetaBrain:
    def __init__(self):
        self.brain_file = "ultimate_meta_brain.json"
        self.weights = {
            'TF-LSTM': 3.0, 'SK-ENSEMBLE': 2.5, 'XGBOOST': 2.5,
            'PATTERN': 2.0, 'MARKOV': 1.8, 'MACD': 1.6, 'RSI': 1.5,
            'Z-SCORE': 1.5, 'DEFAULT': 1.0
        }
        self.learning_rate = 0.05
        self.load_brain()
        self._lock = threading.Lock()

    def load_brain(self):
        if os.path.exists(self.brain_file):
            try:
                with open(self.brain_file, 'r') as f:
                    saved = json.load(f)
                    for k, v in saved.items():
                        self.weights[k] = v
                print("🧠 [META-BRAIN] Lifelong Memory Loaded Successfully.")
            except: pass

    def save_brain(self):
        with open(self.brain_file, 'w') as f:
            json.dump(self.weights, f)

    def learn(self, predictions_list, actual_result):
        if not predictions_list: return
        with self._lock:
            for pred, conf, name in predictions_list:
                if not name: continue
                base_name = name.split().upper() if len(name.split()) > 1 else 'DEFAULT'
                key = next((k for k in self.weights.keys() if k in base_name), 'DEFAULT')
                
                if pred == actual_result:
                    self.weights[key] = min(5.0, self.weights[key] + self.learning_rate)
                else:
                    self.weights[key] = max(0.2, self.weights[key] - (self.learning_rate * 1.5))
            
            self.save_brain()

    def vote(self, predictions, market_state):
        big_score = sml_score = 0.0
        valid = []
        
        for pred, conf, name in predictions:
            if not pred or conf == 0: continue
            base_name = name.split().upper() if name and len(name.split()) > 1 else 'DEFAULT'
            key = next((k for k in self.weights.keys() if k in base_name), 'DEFAULT')
            
            mw = self.weights[key]
            cw = (conf / 100.0) ** 2.0
            total = cw * mw
            
            if pred == 'BIG': big_score += total
            else: sml_score += total
            valid.append((pred, conf, name))

        if not valid: return 'BIG', 65, "📊 NO DATA", 0.5
        
        total_score = big_score + sml_score
        big_r = safe_divide(big_score, total_score, 0.5)
        final_pred = 'BIG' if big_r >= 0.5 else 'SMALL'
        
        best = max(valid, key=lambda x: x)
        final_conf = clamp(best + int(abs(big_r - 0.5) * 20), 60, 99)
        
        return final_pred, final_conf, best, big_r

# ============================================================
# XGBOOST & LSTM AI CLASSES
# ============================================================
class XGBoostModel:
    def __init__(self):
        self.trained = False
        if XGB_AVAILABLE:
            self.model = xgb.XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42)
    
    def train(self, hist):
        if not XGB_AVAILABLE or len(hist) < 40: return False
        binary = list(reversed(to_binary_list(hist)))
        X, y = [], []
        for i in range(5, len(binary)):
            X.append(binary[i-5:i])
            y.append(binary[i])
        try:
            self.model.fit(np.array(X), np.array(y))
            self.trained = True
            return True
        except: return False

    def predict(self, hist):
        if not XGB_AVAILABLE or not self.trained or len(hist) < 5: return None, 0, None
        binary = list(reversed(to_binary_list(hist[:5])))
        try:
            prob = self.model.predict_proba(np.array([binary]))
            pred = 'BIG' if prob >= 0.5 else 'SMALL'
            conf = int(55 + abs(prob - 0.5) * 88)
            return pred, min(99, conf), f"🌲 XGBOOST ({pred} {prob*100:.0f}%)"
        except: return None, 0, None

class RealLSTMPredictor:
    SEQUENCE_LEN = 15
    def __init__(self):
        self.model = None
        self._trained = False
        if TF_AVAILABLE: self._build_model()

    def _build_model(self):
        try:
            self.model = Sequential([
                LSTM(64, return_sequences=True, input_shape=(self.SEQUENCE_LEN, 1)),
                Dropout(0.3), BatchNormalization(),
                LSTM(32), Dropout(0.2),
                Dense(16, activation='relu'),
                Dense(1, activation='sigmoid')
            ])
            self.model.compile(optimizer=Adam(learning_rate=0.001), loss='binary_crossentropy')
        except: pass

    def train(self, hist):
        if not TF_AVAILABLE or not self.model or len(hist) < 50: return
        binary = list(reversed(to_binary_list(hist)))
        X, y = [], []
        for i in range(len(binary) - self.SEQUENCE_LEN):
            X.append([[v] for v in binary[i: i + self.SEQUENCE_LEN]])
            y.append(binary[i + self.SEQUENCE_LEN])
        try:
            self.model.fit(np.array(X), np.array(y), epochs=20, batch_size=16, verbose=0)
            self._trained = True
        except: pass

    def predict(self, hist):
        if not self._trained or len(hist) < self.SEQUENCE_LEN: return None, 0, None
        seq = list(reversed(hist[:self.SEQUENCE_LEN]))
        try:
            X = np.array([[[1 if v=='BIG' else 0] for v in seq]], dtype=np.float32)
            prob = float(self.model.predict(X, verbose=0))
            pred = 'BIG' if prob >= 0.5 else 'SMALL'
            conf = int(55 + abs(prob - 0.5) * 88)
            return pred, min(99, conf), f"🧠 TF-LSTM ({pred} {prob*100:.1f}%)"
        except: return None, 0, None

class BasicStatsPredictors:
    def markov_predict(self, hist):
        if len(hist) < 4: return None, 0, None
        b_count = hist[:4].count('BIG')
        pred = 'BIG' if b_count >= 2 else 'SMALL'
        return pred, 70, f"🔗 MARKOV ({pred})"
        
    def pattern_predict(self, hist):
        if len(hist) < 4: return None, 0, None
        if hist == hist == hist:
            opp = 'SMALL' if hist == 'BIG' else 'BIG'
            return opp, 85, f"🐉 PATTERN-DRAGON ({hist}x3)"
        return None, 0, None

class MarketStateAnalyzer:
    def analyze(self, hist):
        if not hist: return 'NEUTRAL'
        b_pct = hist[:10].count('BIG') / 10 if len(hist)>=10 else 0.5
        if b_pct > 0.7: return 'BULL'
        if b_pct < 0.3: return 'BEAR'
        return 'NEUTRAL'

class WinLossTracker:
    def __init__(self):
        self.total_wins = 0
        self.total_losses = 0
        self.current_win_streak = 0
        self.current_loss_streak = 0
        self.history = []
    
    def add_win(self):
        self.total_wins += 1
        self.current_win_streak += 1
        self.current_loss_streak = 0
        self.history.append('W')
        return self.current_win_streak
        
    def add_loss(self):
        self.total_losses += 1
        self.current_loss_streak += 1
        self.current_win_streak = 0
        self.history.append('L')
        return self.current_loss_streak
        
    def get_win_rate(self):
        t = self.total_wins + self.total_losses
        return (self.total_wins / t * 100) if t > 0 else 0
        
    def get_recent_bar(self, n=10):
        return "".join("✅" if r=='W' else "❌" for r in self.history[-n:])

# ============================================================
# MAIN AI ENGINE (V15 Premium)
# ============================================================
class StrikeV15Ultimate:
    def __init__(self):
        self.history = HistoryManager(maxlen=500)
        self.tracker = WinLossTracker()
        self.market_analyzer = MarketStateAnalyzer()
        
        self.brain = UltimateMetaBrain()
        self.tf_lstm = RealLSTMPredictor()
        self.xgb = XGBoostModel()
        self.stats = BasicStatsPredictors()
        
        self.last_prediction = None
        self.last_all_preds = []
        self.last_issue_id = None
        self.last_market_state = 'NEUTRAL'
        self._train_count = 0

    def normalize_result(self, raw):
        try:
            num = int(str(raw).strip())
            return ('BIG' if num >= 5 else 'SMALL'), num
        except: return 'BIG', 5

    def add_to_history(self, result):
        self.history.add(result)
        self._train_count += 1
        hist_nf = self.history.get_newest_first()
        
        if self._train_count % 30 == 0:
            threading.Thread(target=self.tf_lstm.train, args=(hist_nf,), daemon=True).start()
            threading.Thread(target=self.xgb.train, args=(hist_nf,), daemon=True).start()

    def predict(self):
        hist_nf = self.history.get_newest_first()
        if len(hist_nf) < 5:
            return 'BIG', 65, "📊 Collecting data..."

        self.last_market_state = self.market_analyzer.analyze(hist_nf)

        all_preds = []
        runners = [
            ('TF-LSTM', self.tf_lstm.predict),
            ('XGBOOST', self.xgb.predict),
            ('PATTERN', self.stats.pattern_predict),
            ('MARKOV', self.stats.markov_predict)
        ]

        for name, fn in runners:
            try:
                r = fn(hist_nf)
                if r and r and r > 0:
                    all_preds.append((r, r, r))
            except: pass

        self.last_all_preds = all_preds
        final_pred, final_conf, final_name, big_ratio = self.brain.vote(all_preds, self.last_market_state)
        return final_pred, final_conf, final_name

    def record_result(self, predicted, actual, period):
        self.brain.learn(self.last_all_preds, actual)


# ============================================================
# WEB SERVER SETUP (FLASK + CORS) & HEALTH CHECK
# ============================================================
flask_app = Flask(__name__)
CORS(flask_app)
flask_app.config['SECRET_KEY'] = 'premium-secret'
socketio  = SocketIO(flask_app, cors_allowed_origins='*', async_mode='threading')

@flask_app.route('/')
def home():
    return "Premium AI Engine is Running Successfully!", 200

_app_instance = None
_realtime_state = {}
_state_lock = threading.Lock()

def update_web_state(ai, prediction, conf, pattern, period, number, result, next_period, outcome):
    with _state_lock:
        _realtime_state.update({
            'prediction': prediction,
            'confidence': conf,
            'pattern': pattern,
            'next_period': next_period,
            'last_result': result,
            'total_wins': ai.tracker.total_wins,
            'total_losses': ai.tracker.total_losses,
            'win_rate': ai.tracker.get_win_rate(),
            'win_streak': ai.tracker.current_win_streak,
            'recent_bar': ai.tracker.get_recent_bar(10),
            'tf_trained': ai.tf_lstm._trained,
            'sk_trained': ai.xgb.trained,
            'bot_status': 'running'
        })
    socketio.emit('bot_update', dict(_realtime_state))

# ============================================================
# MAIN BOT RUNNER
# ============================================================
class PremiumApp:
    def __init__(self):
        self.ai = StrikeV15Ultimate()
        self.running = True

    def fetch_result(self):
        try:
            resp = requests.get(API_URL, params={'t': int(time.time()*1000)}, timeout=10)
            if resp.status_code == 200:
                lst = resp.json().get('data', {}).get('list', [])
                if lst:
                    return str(lst.get('issueNumber')), str(lst.get('number'))
        except: pass
        return None, None

    def run(self):
        print("🚀 PREMIUM AI ENGINE STARTED. LIFELONG LEARNING ACTIVE.")
        
        for _ in range(3):
            try:
                resp = requests.get(API_URL, params={'t': int(time.time()*1000)}, timeout=10)
                if resp.status_code == 200:
                    lst = resp.json().get('data', {}).get('list', [])
                    for item in reversed(lst[:50]):
                        res, _ = self.ai.normalize_result(item.get('number'))
                        self.ai.history.add(res)
                    self.ai.xgb.train(self.ai.history.get_newest_first())
                    self.ai.tf_lstm.train(self.ai.history.get_newest_first())
                    print("✅ History loaded & initial training complete.")
                    break
            except: time.sleep(2)

        last_check_time = 0
        while self.running and not _shutdown_event.is_set():
            if time.time() - last_check_time >= 3:
                last_check_time = time.time()
                period, number = self.fetch_result()
                
                if period and number:
                    result, _ = self.ai.normalize_result(number)
                    try:
                        next_period = str(int(period) + 1) if '_' not in period else f"{period.split('_')[0]}_{int(period.split('_'))+1:04d}"
                    except: next_period = period + "_next"

                    if self.ai.last_issue_id and period != self.ai.last_issue_id:
                        outcome = None
                        if self.ai.last_prediction:
                            is_win = (self.ai.last_prediction == result)
                            self.ai.record_result(self.ai.last_prediction, result, period)
                            if is_win:
                                self.ai.tracker.add_win()
                                outcome = 'WIN'
                                print(f"✅ WIN [{period}] -> AI Brain learned from success.")
                            else:
                                self.ai.tracker.add_loss()
                                outcome = 'LOSS'
                                print(f"❌ LOSS [{period}] -> AI Brain penalized error.")
                                
                        self.ai.add_to_history(result)

                    pred, conf, pattern = self.ai.predict()
                    self.ai.last_prediction = pred
                    
                    if self.ai.last_issue_id != period:
                        print(f"📡 AI PREDICTING [{next_period}]: {pred} ({conf}%)")
                        
                        # --- স্বয়ংক্রিয় টেলিগ্রাম সিগন্যাল ট্রিগার ---
                        telegram_msg = (
                            f"🔔 *ULTIMATE VIP STRIKE V15*\n\n"
                            f"📊 *Period:* `{next_period}`\n"
                            f"🔮 *Prediction:* `{pred}`\n"
                            f"🔥 *Confidence:* `{conf}%`\n"
                            f"🎯 *Engine:* `{pattern}`"
                        )
                        send_telegram_signal(telegram_msg)
                    
                    self.ai.last_issue_id = period
                    update_web_state(self.ai, pred, conf, pattern, period, number, result, next_period, outcome=None)
            
            time.sleep(1)

def start_bot():
    global _app_instance
    _app_instance = PremiumApp()
    _app_instance.run()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    threading.Thread(target=start_bot, daemon=True).start()
    socketio.run(flask_app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
