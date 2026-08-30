# ==============================================================================
# 🚀 QUANT-LEVEL VIP STRIKE AI (MARKET-AWARE V20 PRO - INSTANT SIGNAL FIX)
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

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*'
}

# ==============================================================================
# 🧠 INFINITE LIFELONG MEMORY (SQLite)
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
            
            step_distribution = {}
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
        
        # 1. DRAGON TREND
        streak = 1
        for i in range(2, len(history)):
            if history[-i] == last: streak += 1
            else: break
            
        if streak >= 3:
            conf = min(99, 70 + (streak * 5))
            return last, conf, f"🔥 Dragon Trend Active ({streak}x {last})"
            
        # 2. ALTERNATING (B-S-B-S)
        if len(history) >= 4:
            if history[-1] != history[-2] and history[-2] != history[-3] and history[-3] != history[-4]:
                pred = 'BIG' if last == 'SMALL' else 'SMALL'
                return pred, 85, "⚡ Alternating/Jump Pattern"
                
        # 3. 2x2 MIRROR (B-B-S-S)
        if len(history) >= 4:
            if history[-1] == history[-2] and history[-3] == history[-4] and history[-1] != history[-3]:
                pred = 'BIG' if last == 'SMALL' else 'SMALL'
                return pred, 80, "🪞 Mirror (2x2) Pattern"

        return None, 0, "No Clear Pattern"

# ==============================================================================
# 🧬 ADVANCED AI ENGINE
# ==============================================================================

class AdvancedAI:
    def __init__(self):
        self.seq_len = 15
        self.tf_model = self._build_model()
        self.xgb_model = xgb.XGBClassifier(n_estimators=50, learning_rate=0.08, max_depth=3)
        self.is_tf_trained = False
        self.is_xgb_trained = False

    def _build_model(self):
        inputs = Input(shape=(self.seq_len, 1))
        x = LSTM(24, return_sequences=True)(inputs)
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
        if len(history) < 30: return
        binary = [1 if h == 'BIG' else 0 for h in history]
        
        X_tf, y_tf = [], []
        for i in range(len(binary) - self.seq_len):
            X_tf.append([[v] for v in binary[i:i+self.seq_len]])
            y_tf.append(binary[i+self.seq_len])
        if X_tf:
            self.tf_model.fit(np.array(X_tf), np.array(y_tf), epochs=3, verbose=0)
            self.is_tf_trained = True

        df = self.feature_engineering(history)
        if len(df) > 10 and len(df['res'].unique()) > 1:
            X_xgb = df.drop(columns=['res']).values
            y_xgb = df['res'].values
            self.xgb_model.fit(X_xgb, y_xgb)
            self.is_xgb_trained = True
        print("🧠 [AI] Fast Training Complete.")

    def predict(self, history):
        tf_pred, xgb_pred = None, None
        
        if self.is_tf_trained and len(history) >= self.seq_len:
            seq = [1 if h == 'BIG' else 0 for h in history[-self.seq_len:]]
            prob = self.tf_model.predict(np.array([[[v] for v in seq]]), verbose=0)[0][0]
            if prob > 0.55: tf_pred = 'BIG'
            elif prob < 0.45: tf_pred = 'SMALL'

        if self.is_xgb_trained and len(history) >= 15:
            df = self.feature_engineering(history)
            if not df.empty:
                try:
                    X_test = df.drop(columns=['res']).tail(1).values
                    idx = list(self.xgb_model.classes_).index(1)
                    prob = self.xgb_model.predict_proba(X_test)[0][idx]
                    if prob > 0.55: xgb_pred = 'BIG'
                    elif prob < 0.45: xgb_pred = 'SMALL'
                except: pass

        return tf_pred, xgb_pred

# ==============================================================================
# TELEGRAM PRO INTERFACE
# ==============================================================================

class TelegramProBot:
    def __init__(self, token, default_chat_id):
        self.token = token
        self.default_chat_id = default_chat_id
        self.api = f"https://api.telegram.org/bot{token}"
        self.offset = 0

    def send_message(self, text, chat_id=None, reply_markup=None):
        target_id = chat_id if chat_id else self.default_chat_id
        payload = {'chat_id': target_id, 'text': text, 'parse_mode': 'HTML', 'disable_web_page_preview': True}
        if reply_markup: payload['reply_markup'] = json.dumps(reply_markup)
        try:
            requests.post(f"{self.api}/sendMessage", json=payload, timeout=10)
        except Exception as e:
            print(f"Telegram Send Error: {e}")

    def send_photo(self, photo_bytes, caption="", chat_id=None, reply_markup=None):
        target_id = chat_id if chat_id else self.default_chat_id
        files = {'photo': ('chart.png', photo_bytes, 'image/png')}
        data = {'chat_id': target_id, 'caption': caption, 'parse_mode': 'HTML'}
        if reply_markup: data['reply_markup'] = json.dumps(reply_markup)
        try:
            requests.post(f"{self.api}/sendPhoto", data=data, files=files, timeout=10)
        except Exception as e:
            print(f"Photo Send Error: {e}")

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
            res = requests.get(f"{self.api}/getUpdates", params={'offset': self.offset + 1, 'timeout': 1}, timeout=5).json()
            for update in res.get('result', []):
                self.offset = update['update_id']
                if 'message' in update:
                    chat_id = update['message']['chat']['id']
                    text = update['message'].get('text', '')
                    if text.startswith('/start'):
                        welcome = (
                            "👋 <b>Welcome to QUANT AI STRIKE BOT!</b>\n\n"
                            "Signals will be broadcasted automatically on every 30s period.\n"
                            "Use the buttons below to check live stats & momentum chart."
                        )
                        self.send_message(welcome, chat_id=chat_id, reply_markup=self.get_inline_keyboard())

                elif 'callback_query' in update:
                    chat_id = update['callback_query']['message']['chat']['id']
                    data = update['callback_query']['data']
                    if data == "cmd_chart":
                        hist = controller.db.get_recent_history(50)
                        if len(hist) > 5:
                            img = self.generate_chart(hist)
                            self.send_photo(img, "📈 <b>Live Market Trend Chart</b>", chat_id=chat_id, reply_markup=self.get_inline_keyboard())
                        else:
                            self.send_message("⏳ Waiting for data...", chat_id=chat_id)
                    elif data == "cmd_stats":
                        tot, w, l, ws, ls, max_l, max_w, avg_step, steps = controller.db.get_detailed_stats()
                        rate = (w/tot*100) if tot > 0 else 0
                        step_breakdown = "\n".join([f"  • <b>Step {k} Wins:</b> {v} times" for k, v in sorted(steps.items())])
                        if not step_breakdown: step_breakdown = "  • Waiting for history..."

                        msg = (
                            f"🏆 <b>AI ACCURACY & LOSS AUDIT</b>\n"
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
                        )
                        self.send_message(msg, chat_id=chat_id, reply_markup=self.get_inline_keyboard())
                    elif data == "cmd_train":
                        self.send_message("⚙️ <i>Retraining AI Engine...</i>", chat_id=chat_id)
                        threading.Thread(target=controller.ai.train_models, args=(controller.db.get_recent_history(300),)).start()
                        self.send_message("✅ <b>AI Re-calibrated!</b>", chat_id=chat_id, reply_markup=self.get_inline_keyboard())
        except: pass

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

    def fetch_api_data(self):
        try:
            res = requests.get(API_URL, headers=HEADERS, params={'t': int(time.time()*1000)}, timeout=8)
            if res.status_code == 200:
                js = res.json()
                data_list = js.get('data', {}).get('list', [])
                if not data_list and isinstance(js.get('data'), list):
                    data_list = js.get('data')
                return data_list
        except Exception as e:
            print(f"API Fetch Error: {e}")
        return []

    def get_final_prediction(self):
        hist = self.db.get_recent_history(100)
        if not hist: return "BIG", 50, "Waiting for Data"

        pat_pred, pat_conf, pat_name = self.patterns.analyze(hist)
        if pat_pred: return pat_pred, pat_conf, pat_name

        tf_pred, xgb_pred = self.ai.predict(hist)
        if tf_pred and xgb_pred and tf_pred == xgb_pred:
            return tf_pred, 78, "🤖 Consensus (LSTM + XGB)"
        elif tf_pred: return tf_pred, 68, "🧠 Deep LSTM Model"
        elif xgb_pred: return xgb_pred, 65, "🌲 XGBoost Algorithm"
        
        fallback_pred = 'SMALL' if hist[-1] == 'BIG' else 'BIG'
        return fallback_pred, 55, "⚖️ Market Mean Reversion"

    def get_progress_bar(self, conf):
        filled = int(conf / 10)
        return "🟩" * filled + "⬜" * (10 - filled)

    def send_prediction_signal(self, current_period, result=None, num=None, is_win=None, played_step=None):
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

        next_per = str(int(current_period) + 1) if '_' not in current_period else f"{current_period.split('_')[0]}_{int(current_period.split('_')[1])+1:04d}"
        tot, w, l, ws, curr_loss_streak, max_loss, max_win, avg_step, _ = self.db.get_detailed_stats()
        next_step = curr_loss_streak + 1
        
        pred, conf, strategy = self.get_final_prediction()
        self.db.save_prediction(next_per, pred, step=next_step)
        
        rate = (w/tot*100) if tot > 0 else 0
        emoji = "🔴 BIG" if pred == 'BIG' else "🔵 SMALL"
        prog_bar = self.get_progress_bar(conf)
        
        step_display = f"🟢 Step 1 (Normal)" if next_step == 1 else (f"🟡 Step 2 (Recovery)" if next_step == 2 else f"🔴 Step {next_step} (High Alert)")

        msg = (
            f"⚡ <b>VIP AI SIGNAL</b> ⚡\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{outcome_msg}"
            f"🔮 <b>Target Period:</b> <code>{next_per}</code>\n"
            f"🧠 <b>Prediction:</b> <b>{emoji}</b>\n"
            f"🪜 <b>Level:</b> <b>{step_display}</b>\n"
            f"🚥 [{prog_bar}] {conf}%\n"
            f"⚙️ <b>Strategy:</b> {strategy}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🏆 <b>Win Rate:</b> {rate:.1f}% | 💀 <b>Max Loss Step:</b> {max_loss}\n"
        )
        self.bot.send_message(msg, reply_markup=self.bot.get_inline_keyboard())
        print(f"[{next_per}] Signal Sent: {pred} | Step: {next_step}")

    def loop(self):
        self.bot.send_message("🚀 <b>QUANT AI V20 ONLINE</b>\nLoss-Step Optimization Engine Activated.", reply_markup=self.bot.get_inline_keyboard())
        print("🚀 QUANT AI ENGINE INITIALIZED...")
        
        # Initial Boot History Sync
        boot_data = self.fetch_api_data()
        if boot_data:
            for d in reversed(boot_data):
                issue = str(d.get('issueNumber') or d.get('issue') or d.get('period'))
                num = int(d.get('number') or d.get('openNum') or d.get('code') or 0)
                self.db.add_result(issue, 'BIG' if num >= 5 else 'SMALL', num)
            
            threading.Thread(target=self.ai.train_models, args=(self.db.get_recent_history(200),)).start()
            
            # Send first instant prediction
            latest = boot_data[0]
            self.last_period = str(latest.get('issueNumber') or latest.get('issue') or latest.get('period'))
            self.send_prediction_signal(self.last_period)

        # Main Real-Time Polling Loop
        while True:
            try:
                self.bot.process_updates(self)
                data_list = self.fetch_api_data()
                
                if data_list:
                    data = data_list[0]
                    current_period = str(data.get('issueNumber') or data.get('issue') or data.get('period'))
                    
                    if current_period != self.last_period:
                        num = int(data.get('number') or data.get('openNum') or data.get('code') or 0)
                        result = 'BIG' if num >= 5 else 'SMALL'
                        self.db.add_result(current_period, result, num)
                        
                        is_win, past_pred, played_step = self.db.update_prediction_result(current_period, result)
                        
                        # Send New Prediction for Next Round
                        self.send_prediction_signal(current_period, result, num, is_win, played_step)

                        # Trigger adaptive retrain on streak loss
                        _, _, _, _, curr_loss_streak, _, _, _, _ = self.db.get_detailed_stats()
                        if curr_loss_streak >= 2:
                            threading.Thread(target=self.ai.train_models, args=(self.db.get_recent_history(250),)).start()

                        self.last_period = current_period
                        
            except Exception as e:
                print(f"Error in main loop: {e}")
            
            time.sleep(2)

# ==============================================================================
# RENDER KEEPALIVE SERVER
# ==============================================================================

class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"VIP AI is Active.")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    threading.Thread(
        target=lambda: HTTPServer(('0.0.0.0', port), DummyHandler).serve_forever(),
        daemon=True
    ).start()
    UltimateController().loop()
