# ============================================================
# ULTIMATE VIP STRIKE V15 - RENDER & TELEGRAM EDITION
# No HTML | Persistent Telegram Buttons | Lifelong Meta-Learning
# ============================================================

import requests
import json
import time
import threading
import os
import math
from collections import deque
from http.server import BaseHTTPRequestHandler, HTTPServer

# ============================================================
# TELEGRAM BOT CREDENTIALS
# ============================================================
TELEGRAM_TOKEN   = "8946950031:AAEjErIWu-7H6jnXvUJw30eJ9olA_iuXrzo"
TELEGRAM_CHAT_ID = "8395823375"
API_URL          = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"
DATA_FILE        = "ai_brain_memory.json"

# ============================================================
# OPTIONAL IMPORTS (Machine Learning)
# ============================================================
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
    from tensorflow.keras.optimizers import Adam
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False


# ============================================================
# UTILITY FUNCTIONS
# ============================================================
def safe_divide(a, b, default=0.0):
    return default if b == 0 else a / b

def clamp(value, min_val, max_val):
    return max(min_val, min(max_val, value))

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
# LIFELONG META-LEARNER (The AI Brain)
# ============================================================
class UltimateMetaBrain:
    def __init__(self):
        self.brain_file = DATA_FILE
        self.weights = {
            'TF-LSTM': 3.0, 'XGBOOST': 2.8, 'PATTERN': 2.0, 
            'MARKOV': 1.8, 'DEFAULT': 1.0
        }
        self.learning_rate = 0.05
        self.load_brain()
        self._lock = threading.Lock()

    def load_brain(self):
        if os.path.exists(self.brain_file):
            try:
                with open(self.brain_file, 'r') as f:
                    self.weights.update(json.load(f))
                print("🧠 [META-BRAIN] Memory Loaded.")
            except: pass

    def save_brain(self):
        with open(self.brain_file, 'w') as f:
            json.dump(self.weights, f)

    def learn(self, predictions_list, actual_result):
        if not predictions_list: return
        with self._lock:
            for pred, conf, name in predictions_list:
                base_name = name.split()[1].upper() if name and len(name.split()) > 1 else 'DEFAULT'
                key = next((k for k in self.weights.keys() if k in base_name), 'DEFAULT')
                
                if pred == actual_result:
                    self.weights[key] = min(5.0, self.weights[key] + self.learning_rate)
                else:
                    self.weights[key] = max(0.5, self.weights[key] - (self.learning_rate * 1.5))
            self.save_brain()

    def vote(self, predictions, market_state):
        big_score = sml_score = 0.0
        valid = []
        for pred, conf, name in predictions:
            if not pred or conf == 0: continue
            base_name = name.split()[1].upper() if name and len(name.split()) > 1 else 'DEFAULT'
            key = next((k for k in self.weights.keys() if k in base_name), 'DEFAULT')
            total = (conf / 100.0)**2.0 * self.weights[key]
            
            if pred == 'BIG': big_score += total
            else: sml_score += total
            valid.append((pred, conf, name))

        if not valid: return 'BIG', 65, "📊 DEFAULT", 0.5
        
        total_score = big_score + sml_score
        big_r = safe_divide(big_score, total_score, 0.5)
        final_pred = 'BIG' if big_r >= 0.5 else 'SMALL'
        
        best = max(valid, key=lambda x: x[1])
        final_conf = clamp(best[1] + int(abs(big_r - 0.5) * 20), 60, 99)
        return final_pred, final_conf, best[2], big_r


# ============================================================
# ML MODELS (LSTM & XGBOOST)
# ============================================================
class XGBoostModel:
    def __init__(self):
        self.trained = False
        if XGB_AVAILABLE:
            self.model = xgb.XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.05)
    
    def train(self, hist):
        if not XGB_AVAILABLE or len(hist) < 40: return
        binary = list(reversed(to_binary_list(hist)))
        X, y = [], []
        for i in range(5, len(binary)):
            X.append(binary[i-5:i])
            y.append(binary[i])
        try:
            self.model.fit(np.array(X), np.array(y))
            self.trained = True
        except: pass

    def predict(self, hist):
        if not XGB_AVAILABLE or not self.trained or len(hist) < 5: return None, 0, None
        binary = list(reversed(to_binary_list(hist[:5])))
        try:
            prob = self.model.predict_proba(np.array([binary]))[0][1]
            pred = 'BIG' if prob >= 0.5 else 'SMALL'
            conf = int(55 + abs(prob - 0.5) * 88)
            return pred, min(99, conf), f"🌲 XGBOOST ({pred[0]} {prob*100:.0f}%)"
        except: return None, 0, None

class BasicStatsPredictors:
    def markov_predict(self, hist):
        if len(hist) < 4: return None, 0, None
        b_count = hist[:4].count('BIG')
        pred = 'BIG' if b_count >= 2 else 'SMALL'
        return pred, 70, f"🔗 MARKOV ({pred})"
        
    def pattern_predict(self, hist):
        if len(hist) < 4: return None, 0, None
        if hist[0] == hist[1] == hist[2]:
            opp = 'SMALL' if hist[0] == 'BIG' else 'BIG'
            return opp, 85, f"🐉 DRAGON-PATTERN"
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
        
    def add_loss(self):
        self.total_losses += 1
        self.current_loss_streak += 1
        self.current_win_streak = 0
        self.history.append('L')
        
    def get_win_rate(self):
        t = self.total_wins + self.total_losses
        return (self.total_wins / t * 100) if t > 0 else 0
        
    def get_recent_bar(self, n=10):
        return "".join("🟢" if r=='W' else "🔴" for r in self.history[-n:])

# ============================================================
# TELEGRAM BOT (WITH KEYBOARD BUTTONS)
# ============================================================
class TelegramBot:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = str(chat_id)
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.last_update_id = 0
        
        # Telegram Keyboard Buttons Setup
        self.keyboard_markup = {
            "keyboard": [
                [{"text": "📊 Stats"}, {"text": "🔥 Streak"}],
                [{"text": "📈 Market"}, {"text": "🧠 AI Status"}],
                [{"text": "🔄 Reset"}]
            ],
            "resize_keyboard": True,
            "is_persistent": True
        }

    def send_message(self, text):
        payload = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True,
            'reply_markup': json.dumps(self.keyboard_markup)
        }
        for _ in range(3):
            try:
                res = requests.post(f"{self.base_url}/sendMessage", data=payload, timeout=10)
                if res.status_code == 200: return True
            except: time.sleep(2)
        return False

    def check_commands(self):
        try:
            res = requests.get(f"{self.base_url}/getUpdates", params={'offset': self.last_update_id + 1, 'timeout': 1}, timeout=5)
            if res.status_code == 200:
                data = res.json()
                for update in data.get('result', []):
                    self.last_update_id = update.get('update_id', self.last_update_id)
                    text = update.get('message', {}).get('text', '').strip().lower()
                    if not text: continue
                    
                    if "stats" in text or "📊" in text: return 'stats'
                    if "streak" in text or "🔥" in text: return 'streak'
                    if "market" in text or "📈" in text: return 'market'
                    if "ai status" in text or "🧠" in text: return 'ai_status'
                    if "reset" in text or "🔄" in text: return 'reset'
        except: pass
        return None

    def send_vip_signal(self, ai, prediction, conf, pattern, last_period, last_result, next_period):
        p_emoji = "🐯 BIG" if prediction == "BIG" else "🐭 SMALL"
        r_emoji = "🔴" if last_result == "BIG" else "🔵"
        
        msg = (
            f"🎯 <b>VIP STRIKE AI V15</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🔹 <b>Period:</b> <code>{next_period}</code>\n"
            f"🔹 <b>Prediction:</b> <b>{p_emoji}</b>\n"
            f"🔹 <b>Confidence:</b> {conf}%\n"
            f"🔹 <b>AI Strategy:</b> {pattern}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📊 <b>Last Result:</b> {last_period} = {r_emoji} {last_result}\n"
            f"📈 <b>Win Rate:</b> {ai.tracker.get_win_rate():.1f}%\n"
            f"🔥 <b>Trend:</b> {ai.tracker.get_recent_bar(7)}\n"
        )
        self.send_message(msg)

# ============================================================
# MAIN AI ENGINE 
# ============================================================
class StrikeV15Ultimate:
    def __init__(self):
        self.history = HistoryManager(maxlen=500)
        self.tracker = WinLossTracker()
        self.market = MarketStateAnalyzer()
        self.brain = UltimateMetaBrain()
        self.xgb = XGBoostModel()
        self.stats = BasicStatsPredictors()
        
        self.last_prediction = None
        self.last_all_preds = []
        self.last_issue_id = None
        self._train_count = 0

    def add_to_history(self, result):
        self.history.add(result)
        self._train_count += 1
        hist_nf = self.history.get_newest_first()
        if self._train_count % 30 == 0:
            threading.Thread(target=self.xgb.train, args=(hist_nf,), daemon=True).start()

    def predict(self):
        hist_nf = self.history.get_newest_first()
        if len(hist_nf) < 5: return 'BIG', 65, "📊 Collecting data..."
        ms = self.market.analyze(hist_nf)

        runners = [
            ('XGBOOST', self.xgb.predict),
            ('PATTERN', self.stats.pattern_predict),
            ('MARKOV', self.stats.markov_predict)
        ]

        all_preds = []
        for name, fn in runners:
            try:
                r = fn(hist_nf)
                if r and r[0] and r[1] > 0: all_preds.append((r[0], r[1], r[2]))
            except: pass

        self.last_all_preds = all_preds
        final_pred, final_conf, final_name, _ = self.brain.vote(all_preds, ms)
        return final_pred, final_conf, final_name

    def record_result(self, predicted, actual, period):
        self.brain.learn(self.last_all_preds, actual)

# ============================================================
# DUMMY SERVER FOR RENDER KEEPALIVE
# ============================================================
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"AI Telegram Bot is Running Successfully on Render!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    print(f"🌐 Render KeepAlive Server running on port {port}")
    server.serve_forever()

# ============================================================
# MAIN LOOP
# ============================================================
def start_bot():
    print("🚀 TELEGRAM VIP BOT STARTED...")
    ai = StrikeV15Ultimate()
    bot = TelegramBot(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    
    # Notify Telegram that bot is online and set up Keyboard Buttons
    bot.send_message("✅ <b>AI Engine Restarted & Online!</b>\nUse the buttons below to interact.")

    last_check_time = 0
    cmd_count = 0
    
    while True:
        try:
            # Check Telegram Commands every few seconds
            cmd_count += 1
            if cmd_count > 3:
                cmd = bot.check_commands()
                if cmd == 'stats':
                    bot.send_message(f"📊 <b>Stats:</b>\nWins: {ai.tracker.total_wins} | Losses: {ai.tracker.total_losses}\nRate: {ai.tracker.get_win_rate():.1f}%")
                elif cmd == 'streak':
                    bot.send_message(f"🔥 <b>Streaks:</b>\nWin Streak: {ai.tracker.current_win_streak}\nLoss Streak: {ai.tracker.current_loss_streak}")
                elif cmd == 'market':
                    bot.send_message(f"📈 <b>Market State:</b> {ai.market.analyze(ai.history.get_newest_first())}")
                elif cmd == 'ai_status':
                    xgb_st = "✅ Active" if ai.xgb.trained else "⏳ Training"
                    bot.send_message(f"🧠 <b>AI Brain Status:</b>\nXGBoost: {xgb_st}\nMeta-Learning: Active")
                elif cmd == 'reset':
                    ai.tracker.__init__()
                    bot.send_message("🔄 All Stats Reset Successfully.")
                cmd_count = 0

            # Main Game Loop
            if time.time() - last_check_time >= 3:
                last_check_time = time.time()
                try:
                    resp = requests.get(API_URL, params={'t': int(time.time()*1000)}, timeout=10)
                    if resp.status_code == 200:
                        lst = resp.json().get('data', {}).get('list', [])
                        if lst:
                            period = str(lst[0].get('issueNumber'))
                            num = int(str(lst[0].get('number', 0)))
                            result = 'BIG' if num >= 5 else 'SMALL'
                            
                            try:
                                next_period = str(int(period) + 1) if '_' not in period else f"{period.split('_')[0]}_{int(period.split('_')[1])+1:04d}"
                            except: next_period = period + "_next"

                            # New Period Detected
                            if ai.last_issue_id and period != ai.last_issue_id:
                                if ai.last_prediction:
                                    is_win = (ai.last_prediction == result)
                                    ai.record_result(ai.last_prediction, result, period)
                                    if is_win: ai.tracker.add_win()
                                    else: ai.tracker.add_loss()
                                
                                ai.add_to_history(result)
                                pred, conf, pattern = ai.predict()
                                ai.last_prediction = pred
                                
                                # Send Telegram Signal
                                print(f"📤 Sending Signal: {next_period} -> {pred}")
                                bot.send_vip_signal(ai, pred, conf, pattern, period, result, next_period)
                                
                            ai.last_issue_id = period
                except Exception as e:
                    print(f"API Error: {e}")
                    
            time.sleep(1)
        except Exception as e:
            print(f"Critical Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # Start Dummy Server for Render Port Binding
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    # Start Main Bot
    start_bot()
