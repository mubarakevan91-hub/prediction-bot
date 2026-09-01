# ==============================================================================
# 🚀 QUANT-LEVEL VIP STRIKE AI (MARKET-AWARE V20 PRO + LOSS STEP TRACKER)
# ==============================================================================

import os
import time
import json
import sqlite3
import threading
import requests
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import math
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

# AI Libraries
import xgboost as xgb
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, LSTM, Dense, GlobalAveragePooling1D
from tensorflow.keras.optimizers import Adam

# ==============================================================================
# CONFIGURATION
# ==============================================================================

TELEGRAM_TOKEN = "8946950031:AAEjErIWu-7H6jnXvUJw30eJ9olA_iuXrzo"
TELEGRAM_CHAT_ID = "8395823375"
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"
DB_FILE = "quant_ai_memory.db"

# ==============================================================================
# 🧠 INFINITE LIFELONG MEMORY (SQLite With Loss-Step Engine)
# ==============================================================================

class SQLiteMemory:
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_tables()
        self._lock = threading.Lock()

    def _create_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS history 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, period TEXT UNIQUE, result TEXT, number INTEGER)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS predictions 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, period TEXT UNIQUE, predicted TEXT, actual TEXT, is_win INTEGER, step INTEGER DEFAULT 1)''')
        self.conn.commit()

    def add_result(self, period, result, number):
        with self._lock:
            try:
                self.cursor.execute("INSERT INTO history (period, result, number) VALUES (?, ?, ?)", (period, result, number))
                self.conn.commit()
            except sqlite3.IntegrityError:
                pass

    def save_prediction(self, period, predicted, step=1):
        with self._lock:
            try:
                self.cursor.execute("INSERT INTO predictions (period, predicted, step) VALUES (?, ?, ?)", (period, predicted, step))
                self.conn.commit()
            except sqlite3.IntegrityError:
                pass

    def update_prediction_result(self, period, actual):
        with self._lock:
            self.cursor.execute("SELECT predicted, step FROM predictions WHERE period=?", (period,))
            row = self.cursor.fetchone()
            if row:
                predicted, step = row[0], row[1]
                is_win = 1 if predicted == actual else 0
                self.cursor.execute("UPDATE predictions SET actual=?, is_win=? WHERE period=?", (actual, is_win, period))
                self.conn.commit()
                return is_win, predicted, step
            return None, None, None

    def get_recent_history(self, limit=500):
        with self._lock:
            self.cursor.execute("SELECT result FROM history ORDER BY id DESC LIMIT ?", (limit,))
            return [r[0] for r in reversed(self.cursor.fetchall())]

    def get_detailed_stats(self):
        with self._lock:
            self.cursor.execute("SELECT is_win, step FROM predictions WHERE is_win IS NOT NULL ORDER BY id ASC")
            rows = self.cursor.fetchall()
            
            if not rows:
                return 0, 0, 0, 0, 0, 0, 0, 1.0, {}

            total = len(rows)
            wins = sum(1 for r in rows if r[0] == 1)
            losses = total - wins

            max_loss_streak = 0
            max_win_streak = 0
            curr_loss = 0
            curr_win = 0
            
            step_distribution = {}  # {Step 1: X wins, Step 2: Y wins, ...}
            win_steps = []

            for is_win, step in rows:
                if is_win == 1:
                    curr_win += 1
                    curr_loss = 0
                    actual_step = step if step else 1
                    win_steps.append(actual_step)
                    step_distribution[actual_step] = step_distribution.get(actual_step, 0) + 1
                else:
                    curr_loss += 1
                    curr_win = 0

                if curr_win > max_win_streak: max_win_streak = curr_win
                if curr_loss > max_loss_streak: max_loss_streak = curr_loss

            avg_step = sum(win_steps) / len(win_steps) if win_steps else 1.0

            return total, wins, losses, curr_win, curr_loss, max_loss_streak, max_win_streak, avg_step, step_distribution

# ==============================================================================
# 🎯 PATTERN RECOGNITION ENGINE
# ==============================================================================

class PatternEngine:
    @staticmethod
    def analyze(history):
        if len(history) < 5:
            return None, 0, "Not Enough Data"

        last = history[-1]
        
        # 1. DRAGON / STREAK DETECTION
        streak = 1
        for i in range(2, len(history)):
            if history[-i] == last:
                streak += 1
            else:
                break
            
        if streak >= 3:
            conf = min(99, 70 + (streak * 5))
            return last, conf, f"🔥 Dragon Trend Active ({streak}x {last})"
            
        # 2. JUMP / ALTERNATING DETECTION (B-S-B-S)
        if len(history) >= 4:
            if history[-1] != history[-2] and history[-2] != history[-3] and history[-3] != history[-4]:
                pred = 'BIG' if last == 'SMALL' else 'SMALL'
                return pred, 85, "⚡ Alternating/Jump Pattern"
                
        # 3. TWO-BY-TWO DETECTION (B-B-S-S)
        if len(history) >= 4:
            if history[-1] == history[-2] and history[-3] == history[-4] and history[-1] != history[-3]:
                pred = 'BIG' if last == 'SMALL' else 'SMALL'
                return pred, 80, "🪞 Mirror (2x2) Pattern"

        return None, 0, "No Clear Pattern"

# ==============================================================================
# 🧬 ADVANCED AI (LSTM + XGBoost)
# ==============================================================================

class AdvancedAI:
    def __init__(self):
        self.seq_len = 20
        self.tf_model = self._build_model()
        self.xgb_model = xgb.XGBClassifier(n_estimators=100, learning_rate=0.05, max_depth=4)
        self.is_tf_trained = False
        self.is_xgb_trained = False

    def _build_model(self):
        inputs = Input(shape=(self.seq_len, 1))
        x = LSTM(32, return_sequences=True)(inputs)
        x = GlobalAveragePooling1D()(x)
        outputs = Dense(1, activation='sigmoid')(x)
        model = Model(inputs=inputs, outputs=outputs)
        model.compile(optimizer=Adam(learning_rate=0.01), loss='binary_crossentropy')
        return model

    def feature_engineering(self, history):
        df = pd.DataFrame({'res': [1 if x=='BIG' else 0 for x in history]})
        df['Rolling_Mean'] = df['res'].rolling(3).mean().fillna(0.5)
        df['Lag1'] = df['res'].shift(1).fillna(0)
        return df.dropna()

    def train_models(self, history):
        if len(history) < 40: return
        binary = [1 if h == 'BIG' else 0 for h in history]
        
        X_tf, y_tf = [], []
        for i in range(len(binary) - self.seq_len):
            X_tf.append([[v] for v in binary[i:i+self.seq_len]])
            y_tf.append(binary[i+self.seq_len])
        if X_tf:
            self.tf_model.fit(np.array(X_tf), np.array(y_tf), epochs=5, verbose=0)
            self.is_tf_trained = True

        df = self.feature_engineering(history)
        if len(df) > 10 and len(df['res'].unique()) > 1:
            X_xgb = df.drop(columns=['res']).values
            y_xgb = df['res'].values
            self.xgb_model.fit(X_xgb, y_xgb)
            self.is_xgb_trained = True

    def predict(self, history):
        tf_pred, xgb_pred = None, None
        
        if self.is_tf_trained and len(history) >= self.seq_len:
            seq = [1 if h == 'BIG' else 0 for h in history[-self.seq_len:]]
            prob = self.tf_model.predict(np.array([[[v] for v in seq]]), verbose=0)[0][0]
            if prob > 0.55: tf_pred = 'BIG'
            elif prob < 0.45: tf_pred = 'SMALL'

        if self.is_xgb_trained and len(history) >= 20:
            df = self.feature_engineering(history)
            if not df.empty:
                try:
                    X_test = df.drop(columns=['res']).tail(1).values
                    idx = list(self.xgb_model.classes_).index(1)
                    prob = self.xgb_model.predict_proba(X_test)[0][idx]
                    if prob > 0.55: xgb_pred = 'BIG'
                    elif prob < 0.45: xgb_pred = 'SMALL'
                except:
                    pass

        return tf_pred, xgb_pred

# ==============================================================================
# PREMIUM TELEGRAM INTERFACE
# ==============================================================================

class TelegramProBot:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.api = f"https://api.telegram.org/bot{token}"
        self.offset = 0

    def send_message(self, text, reply_markup=None):
        payload = {'chat_id': self.chat_id, 'text': text, 'parse_mode': 'HTML', 'disable_web_page_preview': True}
        if reply_markup:
            payload['reply_markup'] = json.dumps(reply_markup)
        requests.post(f"{self.api}/sendMessage", json=payload)

    def send_photo(self, photo_bytes, caption="", reply_markup=None):
        files = {'photo': ('chart.png', photo_bytes, 'image/png')}
        data = {'chat_id': self.chat_id, 'caption': caption, 'parse_mode': 'HTML'}
        if reply_markup:
            data['reply_markup'] = json.dumps(reply_markup)
        requests.post(f"{self.api}/sendPhoto", data=data, files=files)

    def get_inline_keyboard(self):
        return {
            "inline_keyboard": [
                [{"text": "📊 Trend Chart", "callback_data": "cmd_chart"}, 
                 {"text": "📈 Loss & Accuracy Stats", "callback_data": "cmd_stats"}],
                [{"text": "⚙️ Force AI Retrain", "callback_data": "cmd_train"}]
            ]
        }

    def generate_chart(self, history):
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(8, 4))
        b_count = [1 if x=='BIG' else 0 for x in history[-50:]]
        cumulative = np.cumsum([1 if x==1 else -1 for x in b_count])
        ax.plot(cumulative, color='#00ffcc', linewidth=2, marker='o', markersize=4)
        ax.set_title("Market Momentum (Up=BIG, Down=SMALL)", color='white')
        ax.grid(color='#333333', linestyle='--', linewidth=0.5)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', facecolor='#111111')
        buf.seek(0)
        plt.close(fig)
        return buf

    def process_updates(self, controller):
        try:
            res = requests.get(f"{self.api}/getUpdates", params={'offset': self.offset+1, 'timeout': 1}).json()
            for update in res.get('result', []):
                self.offset = update['update_id']
                if 'callback_query' in update:
                    data = update['callback_query']['data']
                    if data == "cmd_chart":
                        hist = controller.db.get_recent_history(50)
                        if len(hist) > 10:
                            img = self.generate_chart(hist)
                            self.send_photo(img, "📈 <b>Live Market Trend</b>", self.get_inline_keyboard())
                    elif data == "cmd_stats":
                        tot, w, l, ws, ls, max_l, max_w, avg_step, steps = controller.db.get_detailed_stats()
                        rate = (w/tot*100) if tot > 0 else 0
                        
                        step_breakdown = "\n".join([f"  • <b>Step {k} Wins:</b> {v} times" for k, v in sorted(steps.items())])
                        if not step_breakdown: step_breakdown = "  • No data yet."

                        msg = (
                            f"🏆 <b>AI PERFORMANCE & LOSS AUDIT</b>\n"
                            f"━━━━━━━━━━━━━━━━━━\n"
                            f"🎯 <b>Total Rounds:</b> {tot}\n"
                            f"✅ <b>Total Wins:</b> {w} ({rate:.1f}%)\n"
                            f"❌ <b>Total Losses:</b> {l}\n"
                            f"━━━━━━━━━━━━━━━━━━\n"
                            f"💀 <b>All-Time Max Loss Step:</b> <code>{max_l} Steps</code>\n"
                            f"🔥 <b>Current Win Streak:</b> {ws}\n"
                            f"⚠️ <b>Current Loss Step:</b> {ls + 1}\n"
                            f"⚡ <b>Avg Recovery Speed:</b> Step {avg_step:.2f}\n"
                            f"━━━━━━━━━━━━━━━━━━\n"
                            f"📊 <b>Step-by-Step Win Breakdown:</b>\n"
                            f"{step_breakdown}\n"
                            f"━━━━━━━━━━━━━━━━━━\n"
                            f"💡 <i>Low Max Loss Step = Strong AI Learning</i>"
                        )
                        self.send_message(msg, self.get_inline_keyboard())
                    elif data == "cmd_train":
                        self.send_message("⚙️ <i>Retraining AI Engine on recent market history...</i>")
                        threading.Thread(target=controller.ai.train_models, args=(controller.db.get_recent_history(300),)).start()
                        self.send_message("✅ <b>AI Re-calibrated & Synced!</b>", self.get_inline_keyboard())
        except:
            pass

# ==============================================================================
# MAIN ENGINE CONTROLLER
# ==============================================================================

class UltimateController:
    def __init__(self):
        self.db = SQLiteMemory()
        self.ai = AdvancedAI()
        self.patterns = PatternEngine()
        self.bot = TelegramProBot(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
        self.last_period = None

    def get_final_prediction(self):
        hist = self.db.get_recent_history(100)
        if not hist: return "BIG", 50, "Waiting for Data"

        # 1. Market Pattern Priority
        pat_pred, pat_conf, pat_name = self.patterns.analyze(hist)
        if pat_pred:
            return pat_pred, pat_conf, pat_name

        # 2. Hybrid AI Consensus
        tf_pred, xgb_pred = self.ai.predict(hist)
        if tf_pred and xgb_pred and tf_pred == xgb_pred:
            return tf_pred, 78, "🤖 Consensus (LSTM + XGB)"
        elif tf_pred:
            return tf_pred, 68, "🧠 Deep LSTM Model"
        elif xgb_pred:
            return xgb_pred, 65, "🌲 XGBoost Decision Tree"
        
        # 3. Mean Reversion fallback
        fallback_pred = 'SMALL' if hist[-1] == 'BIG' else 'BIG'
        return fallback_pred, 55, "⚖️ Market Mean Reversion"

    def get_progress_bar(self, conf):
        filled = int(conf / 10)
        return "🟩" * filled + "⬜" * (10 - filled)

    def loop(self):
        self.bot.send_message("🚀 <b>QUANT AI V20 ONLINE</b>\nLoss-Step Optimization Engine Activated.", self.bot.get_inline_keyboard())
        print("🚀 QUANT AI ENGINE INITIALIZED...")
        
        # Initial Boot Training
        for _ in range(3):
            try:
                data = requests.get(API_URL, params={'t': int(time.time()*1000)}).json()['data']['list']
                for d in reversed(data):
                    num = int(d['number'])
                    self.db.add_result(str(d['issueNumber']), 'BIG' if num>=5 else 'SMALL', num)
                self.ai.train_models(self.db.get_recent_history(200))
                print("✅ AI Trained successfully on past data.")
                break
            except:
                time.sleep(2)

        # Main Real-Time Loop
        while True:
            try:
                self.bot.process_updates(self)
                
                req = requests.get(API_URL, params={'t': int(time.time()*1000)}, timeout=10)
                if req.status_code == 200:
                    data = req.json()['data']['list'][0]
                    current_period = str(data['issueNumber'])
                    
                    if current_period != self.last_period:
                        num = int(data['number'])
                        result = 'BIG' if num >= 5 else 'SMALL'
                        self.db.add_result(current_period, result, num)
                        
                        is_win, past_pred, played_step = self.db.update_prediction_result(current_period, result)
                        
                        outcome_msg = ""
                        if is_win is not None:
                            if is_win == 1:
                                outcome_icon = f"✅ <b>WIN (Step {played_step} Recovery)</b>" if played_step > 1 else "✅ <b>DIRECT WIN (Step 1)</b>"
                            else:
                                outcome_icon = f"❌ <b>LOSS (Failed at Step {played_step})</b>"
                                
                            outcome_msg = (
                                f"📊 <b>Round:</b> <code>{current_period}</code>\n"
                                f"🎯 <b>Result:</b> {'🔴 BIG' if result=='BIG' else '🔵 SMALL'} [{num}]\n"
                                f"⚖️ <b>Status:</b> {outcome_icon}\n"
                                f"━━━━━━━━━━━━━━━━━━\n"
                            )

                        # Determine Next Target Period
                        next_per = str(int(current_period) + 1) if '_' not in current_period else f"{current_period.split('_')[0]}_{int(current_period.split('_')[1])+1:04d}"
                        
                        # Calculate Next Step Level
                        tot, w, l, ws, curr_loss_streak, max_loss, max_win, avg_step, _ = self.db.get_detailed_stats()
                        next_step = curr_loss_streak + 1
                        
                        # Generate Prediction
                        pred, conf, strategy = self.get_final_prediction()
                        self.db.save_prediction(next_per, pred, step=next_step)
                        
                        rate = (w/tot*100) if tot > 0 else 0
                        emoji = "🔴 BIG" if pred == 'BIG' else "🔵 SMALL"
                        prog_bar = self.get_progress_bar(conf)
                        
                        # Step Status Indicator
                        if next_step == 1:
                            step_display = "🟢 Step 1 (Normal Trade)"
                        elif next_step == 2:
                            step_display = "🟡 Step 2 (1st Recovery)"
                        elif next_step == 3:
                            step_display = "🟠 Step 3 (2nd Recovery)"
                        else:
                            step_display = f"🔴 Step {next_step} (High Recovery Mode)"

                        msg = (
                            f"⚡ <b>VIP AI SIGNAL</b> ⚡\n"
                            f"━━━━━━━━━━━━━━━━━━\n"
                            f"{outcome_msg}"
                            f"🔮 <b>Target Period:</b> <code>{next_per}</code>\n"
                            f"🧠 <b>Prediction:</b> <b>{emoji}</b>\n"
                            f"🪜 <b>Current Level:</b> <b>{step_display}</b>\n"
                            f"🚥 [{prog_bar}] {conf}%\n"
                            f"⚙️ <b>Strategy:</b> {strategy}\n"
                            f"━━━━━━━━━━━━━━━━━━\n"
                            f"🏆 <b>Win Rate:</b> {rate:.1f}%\n"
                            f"💀 <b>Max Loss Step:</b> {max_l if 'max_l' in locals() else max_loss} | ⚡ <b>Avg Win:</b> Step {avg_step:.1f}\n"
                        )
                        self.bot.send_message(msg, self.bot.get_inline_keyboard())
                        print(f"[{next_per}] Signal: {pred} | Step: {next_step} | Conf: {conf}%")

                        # Loss Adaptation: If 2+ consecutive losses, instantly trigger background re-training
                        if curr_loss_streak >= 2:
                            print("⚠️ Loss streak detected. Triggering adaptive AI retraining...")
                            threading.Thread(target=self.ai.train_models, args=(self.db.get_recent_history(250),)).start()
                        elif int(str(current_period)[-2:]) % 15 == 0:
                            threading.Thread(target=self.ai.train_models, args=(self.db.get_recent_history(200),)).start()

                        self.last_period = current_period
                        
            except Exception as e:
                pass
            
            time.sleep(2)

# ==============================================================================
# RENDER KEEPALIVE SERVER (FIXED FOR HEAD REQUESTS)
# ==============================================================================

class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"VIP AI is Active.")

    def do_HEAD(self):
        # Render-এর লুপ চেক সফল করার জন্য এই অংশটি অত্যন্ত জরুরি
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

if __name__ == "__main__":
    # Render-এর ডিফল্ট পোর্ট ১০০০০, তাই পরিবেশ ভেরিয়েবল চেক করা হচ্ছে
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(
        target=lambda: HTTPServer(('0.0.0.0', port), DummyHandler).serve_forever(),
        daemon=True
    ).start()
    UltimateController().loop()
