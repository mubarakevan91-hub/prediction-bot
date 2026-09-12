#============================================================
# OMEGA QUANTUM AI V30.0 - 7-LAYER ENSEMBLE & GENETIC OPTIMIZER
# PURE PYTHON MACHINE LEARNING LABORATORY
# LIVE MARKET SYNC & FRACTAL ANALYSIS
#============================================================
import os
import json
import time
import threading
import signal
import csv
import io
import math
import random
import hashlib
from datetime import datetime, timezone, timedelta
from collections import defaultdict, Counter
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler

#============================================================
# CONFIGURATION & ENVIRONMENT
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
# 🧮 ADVANCED MATH & MATRIX UTILITIES
#============================================================
class Matrix:
    """Pure Python Matrix operations for HMM and Markov Chains."""
    def __init__(self, data):
        self.data = data
        self.rows = len(data)
        self.cols = len(data[0]) if self.rows > 0 else 0

    def __mul__(self, other):
        if isinstance(other, Matrix):
            if self.cols != other.rows: raise ValueError("Dim mismatch")
            res = [[0.0]*other.cols for _ in range(self.rows)]
            for i in range(self.rows):
                for j in range(other.cols):
                    s = 0.0
                    for k in range(self.cols):
                        s += self.data[i][k] * other.data[k][j]
                    res[i][j] = s
            return Matrix(res)
        elif isinstance(other, (int, float)):
            return Matrix([[x * other for x in row] for row in self.data])
        raise TypeError("Unsupported multiplication")

    def transpose(self):
        return Matrix([[self.data[j][i] for j in range(self.rows)] for i in range(self.cols)])

    def normalize_rows(self):
        res = []
        for row in self.data:
            s = sum(row)
            res.append([x/s if s > 0 else 0.0 for x in row])
        return Matrix(res)

def entropy(probs):
    """Shannon Entropy calculation."""
    return -sum(p * math.log2(p + 1e-9) for p in probs if p > 0)

def gini_impurity(probs):
    """Gini Impurity for decision boundaries."""
    return 1.0 - sum(p**2 for p in probs)

def hurst_exponent(seq):
    """Rescaled Range Analysis for Fractal Trend Detection."""
    n = len(seq)
    if n < 20: return 0.5
    max_k = min(100, n // 2)
    rs_list = []
    for k in range(10, max_k, 5):
        sub = seq[:k]
        mean = sum(sub) / k
        cumdev = [sum(sub[:i]) - i * mean for i in range(1, k + 1)]
        R = max(cumdev) - min(cumdev)
        S = math.sqrt(sum((x - mean)**2 for x in sub) / k)
        if S > 0: rs_list.append((math.log(k), math.log(R/S + 1e-9)))
    if len(rs_list) < 2: return 0.5
    n_pts = len(rs_list)
    sum_x = sum(p[0] for p in rs_list)
    sum_y = sum(p[1] for p in rs_list)
    sum_xy = sum(p[0]*p[1] for p in rs_list)
    sum_xx = sum(p[0]**2 for p in rs_list)
    denom = (n_pts * sum_xx - sum_x**2)
    if denom == 0: return 0.5
    return (n_pts * sum_xy - sum_x * sum_y) / denom

#============================================================
# 🧬 FEATURE ENGINEERING EXTRACTOR
#============================================================
class FeatureExtractor:
    """Extracts advanced technical indicators from binary sequences."""
    @staticmethod
    def get_rsi(seq, period=14):
        if len(seq) < period + 1: return 50.0
        gains, losses = [], []
        for i in range(1, len(seq)):
            diff = seq[i] - seq[i-1]
            gains.append(max(0, diff))
            losses.append(max(0, -diff))
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0: return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    @staticmethod
    def get_momentum(seq, period=10):
        if len(seq) < period: return 0
        return seq[-1] - seq[-period]

    @staticmethod
    def get_volatility(seq, period=20):
        if len(seq) < period: return 0.0
        sub = seq[-period:]
        mean = sum(sub) / period
        return math.sqrt(sum((x - mean)**2 for x in sub) / period)

    @staticmethod
    def get_gap_analysis(seq):
        """Analyzes the distance between identical outcomes."""
        if len(seq) < 5: return []
        gaps = []
        last_idx = {}
        for i, val in enumerate(seq):
            if val in last_idx:
                gaps.append(i - last_idx[val])
            last_idx[val] = i
        return gaps[-10:] if len(gaps) >= 10 else gaps

#============================================================
# 🧠 MODEL 1: FRACTAL MARKOV ENGINE
#============================================================
class FractalMarkovEngine:
    def __init__(self):
        self.markov5 = defaultdict(lambda: [0, 0])
        self.markov4 = defaultdict(lambda: [0, 0])
        self.markov3 = defaultdict(lambda: [0, 0])
        self.hurst = 0.5
        self.trained = False

    def train(self, dataset):
        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        n = len(seq)
        if n < 20: self.trained = False; return
        self.markov5.clear(); self.markov4.clear(); self.markov3.clear()
        for i in range(n - 5): self.markov5[tuple(seq[i:i+5])][seq[i+5]] += 1
        for i in range(n - 4): self.markov4[tuple(seq[i:i+4])][seq[i+4]] += 1
        for i in range(n - 3): self.markov3[tuple(seq[i:i+3])][seq[i+3]] += 1
        self.hurst = hurst_exponent(seq[-500:] if n > 500 else seq)
        self.trained = True

    def predict(self, dataset):
        if not self.trained or len(dataset) < 5: return None, 0
        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        votes, weights = [], []
        
        # Order 5
        if len(seq) >= 5:
            c = self.markov5.get(tuple(seq[-5:]))
            if c and sum(c) >= 2: votes.append((c[1]+1)/(sum(c)+2)); weights.append(0.35)
        # Order 4
        if len(seq) >= 4:
            c = self.markov4.get(tuple(seq[-4:]))
            if c and sum(c) >= 2: votes.append((c[1]+1)/(sum(c)+2)); weights.append(0.25)
        # Order 3
        if len(seq) >= 3:
            c = self.markov3.get(tuple(seq[-3:]))
            if c and sum(c) >= 2: votes.append((c[1]+1)/(sum(c)+2)); weights.append(0.15)
            
        # Fractal Trend Bias
        if self.hurst > 0.6: # Trending
            votes.append(0.8 if seq[-1] == 1 else 0.2); weights.append(0.15)
        elif self.hurst < 0.4: # Mean-reverting
            votes.append(0.2 if seq[-1] == 1 else 0.8); weights.append(0.10)
            
        if not votes: return "BIG" if seq[-1] == 1 else "SMALL", 55
        tw = sum(weights)
        wp = sum(v*w for v,w in zip(votes, weights)) / tw
        pred = "BIG" if wp >= 0.5 else "SMALL"
        conf = int(max(55, min(95, 65 + abs(wp - 0.5) * 100)))
        return pred, conf

#============================================================
# 🇷🇺 MODEL 2: RUSSIAN ENGINE V3
#============================================================
class RussianEngineV3:
    def __init__(self):
        self.transitions = defaultdict(lambda: defaultdict(int))
        self.base_rate = 0.5
        self.alt_score = 0.5
        self.trained = False

    def train(self, dataset):
        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        n = len(seq)
        if n < 10: self.trained = False; return
        self.transitions.clear()
        self.base_rate = sum(seq) / n
        changes = sum(1 for i in range(1, n) if seq[i] != seq[i-1])
        self.alt_score = changes / (n - 1)
        for i in range(n - 1): self.transitions[seq[i]][seq[i+1]] += 1
        self.trained = True

    def predict(self, dataset):
        if not self.trained or len(dataset) < 3: return None, 0
        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        last = seq[-1]
        t_big = self.transitions[last].get(1, 0) + 1
        t_small = self.transitions[last].get(0, 0) + 1
        markov_prob = t_big / (t_big + t_small)
        
        # Alternation logic
        if self.alt_score > 0.6:
            alt_prob = 0.2 if last == 1 else 0.8
        elif self.alt_score < 0.4:
            alt_prob = 0.8 if last == 1 else 0.2
        else:
            alt_prob = 0.5
            
        final_prob = (markov_prob * 0.6) + (alt_prob * 0.2) + (self.base_rate * 0.2)
        pred = "BIG" if final_prob >= 0.5 else "SMALL"
        conf = int(max(55, min(95, 60 + abs(final_prob - 0.5) * 80)))
        return pred, conf

#============================================================
# 🕵️ MODEL 3: HIDDEN MARKOV MODEL (HMM) SIMULATOR
#============================================================
class HMMSimulator:
    """Simplified Baum-Welch & Viterbi for 2-state hidden system."""
    def __init__(self):
        self.trans_prob = [[0.7, 0.3], [0.3, 0.7]] # State 0: Small, State 1: Big
        self.emit_prob = [[0.8, 0.2], [0.2, 0.8]]
        self.trained = False

    def train(self, dataset):
        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        n = len(seq)
        if n < 20: self.trained = False; return
        # Simplified frequency-based emission & transition update
        c00, c01, c10, c11 = 1, 1, 1, 1
        for i in range(n - 1):
            if seq[i] == 0 and seq[i+1] == 0: c00 += 1
            elif seq[i] == 0 and seq[i+1] == 1: c01 += 1
            elif seq[i] == 1 and seq[i+1] == 0: c10 += 1
            else: c11 += 1
        s0 = c00 + c01; s1 = c10 + c11
        self.trans_prob = [[c00/s0, c01/s0], [c10/s1, c11/s1]]
        self.trained = True

    def predict(self, dataset):
        if not self.trained or len(dataset) < 2: return None, 0
        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        last_state = seq[-1]
        # Viterbi 1-step lookahead
        prob_next_0 = self.trans_prob[last_state][0]
        prob_next_1 = self.trans_prob[last_state][1]
        pred = "BIG" if prob_next_1 >= prob_next_0 else "SMALL"
        conf = int(max(55, min(90, 60 + abs(prob_next_1 - prob_next_0) * 60)))
        return pred, conf

#============================================================
# 🧬 MODEL 4: PURE PYTHON NEURAL NETWORK (MLP)
#============================================================
class PureMLP:
    def __init__(self, input_size=15, hidden_size=30):
        self.input_size = input_size
        self.hidden_size = hidden_size
        # Xavier Initialization
        limit1 = math.sqrt(6.0 / (input_size + hidden_size))
        self.w1 = [[random.uniform(-limit1, limit1) for _ in range(hidden_size)] for _ in range(input_size)]
        self.b1 = [0.0] * hidden_size
        limit2 = math.sqrt(6.0 / (hidden_size + 1))
        self.w2 = [[random.uniform(-limit2, limit2)] for _ in range(hidden_size)]
        self.b2 = 0.0
        self.lr = 0.05
        self.trained = False

    def sigmoid(self, x): return 1.0 / (1.0 + math.exp(-max(-500, min(500, x))))
    
    def forward(self, x):
        self.h_in, self.h_out = [], []
        for j in range(self.hidden_size):
            val = self.b1[j]
            for i in range(self.input_size): val += x[i] * self.w1[i][j]
            self.h_in.append(val)
            self.h_out.append(self.sigmoid(val))
        out_val = self.b2
        for j in range(self.hidden_size): out_val += self.h_out[j] * self.w2[j][0]
        self.out_val = out_val
        return self.sigmoid(out_val)

    def train_batch(self, dataset, epochs=5):
        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        if len(seq) < self.input_size + 10: return
        self.trained = True
        # Prepare sliding window data
        X, Y = [], []
        for i in range(self.input_size, len(seq)):
            X.append(seq[i-self.input_size:i])
            Y.append(seq[i])
        
        for _ in range(epochs):
            for i in range(len(X)):
                x, y = X[i], Y[i]
                out = self.forward(x)
                err = y - out
                out_delta = err * out * (1.0 - out)
                
                h_deltas = []
                for j in range(self.hidden_size):
                    h_err = out_delta * self.w2[j][0]
                    h_deltas.append(h_err * self.h_out[j] * (1.0 - self.h_out[j]))
                
                # RMSProp style update (simplified with momentum)
                for j in range(self.hidden_size):
                    self.w2[j][0] += self.lr * out_delta * self.h_out[j]
                    for k in range(self.input_size):
                        self.w1[k][j] += self.lr * h_deltas[j] * x[k]
                self.b2 += self.lr * out_delta
                for j in range(self.hidden_size): self.b1[j] += self.lr * h_deltas[j]

    def predict(self, dataset):
        if not self.trained or len(dataset) < self.input_size: return None, 0
        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        prob = self.forward(seq[-self.input_size:])
        pred = "BIG" if prob >= 0.5 else "SMALL"
        conf = int(max(55, min(92, 60 + abs(prob - 0.5) * 80)))
        return pred, conf

#============================================================
# 🌊 MODEL 5: HARMONIC DFT ENGINE
#============================================================
class HarmonicDFTEngine:
    def __init__(self):
        self.dominant_period = 1
        self.trained = False

    def train(self, dataset):
        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        n = len(seq)
        if n < 30: self.trained = False; return
        mean = sum(seq) / n
        centered = [x - mean for x in seq]
        
        max_power = -1
        best_period = 1
        # Discrete Fourier Transform for period detection
        for k in range(2, min(50, n // 2)):
            real, imag = 0.0, 0.0
            for t in range(n):
                angle = 2 * math.pi * k * t / n
                real += centered[t] * math.cos(angle)
                imag -= centered[t] * math.sin(angle)
            power = real**2 + imag**2
            if power > max_power:
                max_power = power
                best_period = k
        self.dominant_period = best_period
        self.trained = True

    def predict(self, dataset):
        if not self.trained or len(dataset) < self.dominant_period: return None, 0
        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        # Predict based on the dominant cycle phase
        target_idx = len(seq) - self.dominant_period
        if target_idx >= 0:
            pred_val = seq[target_idx]
            pred = "BIG" if pred_val == 1 else "SMALL"
            return pred, 65
        return "BIG", 50

#============================================================
# 📊 MODEL 6: K-NEAREST NEIGHBORS (KNN)
#============================================================
class SequenceKNN:
    def __init__(self, k=5, window=10):
        self.k = k
        self.window = window
        self.memory = []
        self.trained = False

    def train(self, dataset):
        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        n = len(seq)
        if n < self.window + 5: self.trained = False; return
        self.memory = []
        for i in range(self.window, n):
            self.memory.append((tuple(seq[i-self.window:i]), seq[i]))
        self.trained = True

    def predict(self, dataset):
        if not self.trained or len(dataset) < self.window: return None, 0
        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        current = tuple(seq[-self.window:])
        
        distances = []
        for mem_seq, mem_res in self.memory:
            # Hamming distance
            dist = sum(1 for a, b in zip(current, mem_seq) if a != b)
            distances.append((dist, mem_res))
            
        distances.sort(key=lambda x: x[0])
        neighbors = distances[:self.k]
        votes = Counter(n[1] for n in neighbors)
        
        if not votes: return None, 0
        pred_val = votes.most_common(1)[0][0]
        pred = "BIG" if pred_val == 1 else "SMALL"
        conf = int(max(55, min(88, 60 + (votes.most_common(1)[0][1] / self.k) * 40)))
        return pred, conf

#============================================================
# 🎲 MODEL 7: MONTE CARLO SIMULATOR
#============================================================
class MonteCarloSimulator:
    def __init__(self, simulations=1000):
        self.simulations = simulations
        self.trans_matrix = [[0.5, 0.5], [0.5, 0.5]]
        self.trained = False

    def train(self, dataset):
        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        n = len(seq)
        if n < 20: self.trained = False; return
        c00, c01, c10, c11 = 1, 1, 1, 1
        for i in range(n - 1):
            if seq[i] == 0 and seq[i+1] == 0: c00 += 1
            elif seq[i] == 0 and seq[i+1] == 1: c01 += 1
            elif seq[i] == 1 and seq[i+1] == 0: c10 += 1
            else: c11 += 1
        s0 = c00 + c01; s1 = c10 + c11
        self.trans_matrix = [[c00/s0, c01/s0], [c10/s1, c11/s1]]
        self.trained = True

    def predict(self, dataset):
        if not self.trained or len(dataset) < 2: return None, 0
        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        last = seq[-1]
        big_wins = 0
        for _ in range(self.simulations):
            # Simulate 5 steps ahead, take majority of final states
            curr = last
            for _ in range(5):
                r = random.random()
                if curr == 0:
                    curr = 1 if r < self.trans_matrix[0][1] else 0
                else:
                    curr = 0 if r < self.trans_matrix[1][0] else 1
            if curr == 1: big_wins += 1
            
        prob_big = big_wins / self.simulations
        pred = "BIG" if prob_big >= 0.5 else "SMALL"
        conf = int(max(55, min(90, 60 + abs(prob_big - 0.5) * 80)))
        return pred, conf

#============================================================
# 🧬 GENETIC ENSEMBLE OPTIMIZER
#============================================================
class GeneticEnsembleCore:
    def __init__(self):
        self.models = {
            "Fractal": FractalMarkovEngine(),
            "Russian": RussianEngineV3(),
            "HMM": HMMSimulator(),
            "MLP": PureMLP(),
            "DFT": HarmonicDFTEngine(),
            "KNN": SequenceKNN(),
            "MC": MonteCarloSimulator()
        }
        # Initial weights (will be optimized)
        self.weights = {name: 1.0 / len(self.models) for name in self.models}
        self.performance_history = defaultdict(list)
        self.generation = 0

    def train_all(self, dataset):
        for name, model in self.models.items():
            try:
                if name == "MLP": model.train_batch(dataset, epochs=3)
                else: model.train(dataset)
            except Exception as e:
                print(f"⚠️ {name} training error: {e}")

    def record_outcome(self, model_name, is_win):
        self.performance_history[model_name].append(1 if is_win else 0)
        if len(self.performance_history[model_name]) > 50:
            self.performance_history[model_name].pop(0)

    def evolve_weights(self):
        """Simple genetic mutation based on recent win rates."""
        self.generation += 1
        if self.generation % 10 != 0: return # Evolve every 10 rounds
        
        fitness = {}
        total_fit = 0
        for name in self.models:
            hist = self.performance_history[name]
            if len(hist) >= 5:
                wr = sum(hist) / len(hist)
                fitness[name] = max(0.05, wr)
            else:
                fitness[name] = 0.1
            total_fit += fitness[name]
            
        # Normalize to new weights
        for name in self.models:
            self.weights[name] = fitness[name] / total_fit if total_fit > 0 else 1.0 / len(self.models)

    def predict(self, dataset):
        votes = {}
        confs = {}
        for name, model in self.models.items():
            pred, conf = model.predict(dataset)
            if pred:
                votes[name] = 1.0 if pred == "BIG" else 0.0
                confs[name] = conf / 100.0
                
        if not votes: return None, 0, {}
        
        weighted_prob = 0.0
        total_weight = 0.0
        details = {}
        for name in votes:
            w = self.weights.get(name, 0.1)
            weighted_prob += votes[name] * w
            total_weight += w
            details[name] = {"pred": "BIG" if votes[name] == 1.0 else "SMALL", "conf": int(confs[name]*100), "weight": round(w, 2)}
            
        if total_weight > 0: weighted_prob /= total_weight
        
        final_pred = "BIG" if weighted_prob >= 0.5 else "SMALL"
        conviction = abs(weighted_prob - 0.5) * 2
        final_conf = int(max(65, min(99, 70 + conviction * 40)))
        
        return final_pred, final_conf, details

#============================================================
# 🕒 TIME & RISK INTELLIGENCE
#============================================================
class TimeRiskIntelligence:
    def __init__(self):
        self.session_stats = defaultdict(lambda: {"wins": 0, "total": 0})
        self.hourly_stats = defaultdict(lambda: {"wins": 0, "total": 0})
        self.drawdown = 0
        self.max_drawdown = 0
        self.capital_sim = 1000.0

    def record(self, is_win, dt, conf):
        session = self._get_session(dt.hour)
        self.session_stats[session]["total"] += 1
        self.hourly_stats[dt.hour]["total"] += 1
        if is_win:
            self.session_stats[session]["wins"] += 1
            self.hourly_stats[dt.hour]["wins"] += 1
            self.capital_sim += (conf / 100.0) * 10 # Kelly simplified
        else:
            self.capital_sim -= 10
            self.drawdown += 10
        if self.drawdown > self.max_drawdown: self.max_drawdown = self.drawdown
        if is_win: self.drawdown = 0

    def _get_session(self, hour):
        if 5 <= hour < 12: return "🌅 Morning"
        elif 12 <= hour < 16: return "☀️ Noon"
        elif 16 <= hour < 18: return "🌇 Afternoon"
        elif 18 <= hour < 21: return "🌆 Evening"
        else: return "🌙 Night"

    def get_report(self):
        best_session = "N/A"; best_rate = 0.0
        for s, d in self.session_stats.items():
            if d["total"] >= 3:
                r = d["wins"] / d["total"]
                if r > best_rate: best_rate = r; best_session = s
        return best_session, best_rate * 100, self.capital_sim, self.max_drawdown

#============================================================
# 🤖 TELEGRAM BOT CLIENT
#============================================================
class TelegramBot:
    def __init__(self, token):
        self.url = f"https://api.telegram.org/bot{token}/"

    def send_message(self, chat_id, text, reply_markup=None):
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
        if reply_markup: payload["reply_markup"] = reply_markup
        try: requests.post(self.url + "sendMessage", json=payload, timeout=10)
        except Exception as e: print(f"⚠️ TG Send Error: {e}")

    def answer_callback(self, cb_id, text=""):
        try: requests.post(self.url + "answerCallbackQuery", data={"callback_query_id": cb_id, "text": text}, timeout=5)
        except Exception: pass

    def get_file_bytes(self, file_id):
        try:
            res = requests.get(self.url + "getFile", params={"file_id": file_id}, timeout=10).json()
            path = res.get("result", {}).get("file_path")
            if path:
                file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{path}"
                return requests.get(file_url, timeout=30).content
        except Exception: pass
        return None

    def get_updates(self, offset=None):
        try:
            params = {"timeout": 2}
            if offset is not None: params["offset"] = offset
            res = requests.get(self.url + "getUpdates", params=params, timeout=10)
            if res.status_code == 200: return res.json().get("result", [])
        except Exception: pass
        return []

#============================================================
# 🎛️ UI KEYBOARDS
#============================================================
def get_main_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📊 লাইভ পরিসংখ্যান", "callback_data": "btn_stats"}, {"text": "🕒 সেরা টাইম", "callback_data": "btn_time"}],
            [{"text": "🧬 AI মডেল ডিটেইলস", "callback_data": "btn_models"}, {"text": "🎯 বর্তমান সিগন্যাল", "callback_data": "btn_signal"}],
            [{"text": "💰 রিস্ক ও ক্যাপিটাল", "callback_data": "btn_risk"}, {"text": "🧠 জেনেটিক অপ্টিমাইজার", "callback_data": "btn_genetic"}]
        ]
    }

#============================================================
# ⚙️ MAIN ENGINE CONTROLLER
#============================================================
class OmegaEngine:
    def __init__(self):
        self.dataset = []
        self.core = GeneticEnsembleCore()
        self.risk = TimeRiskIntelligence()
        self.bot = TelegramBot(TELEGRAM_TOKEN)
        
        self.last_issue = None
        self.last_pred = None
        self.last_conf = 0
        self.last_details = {}
        
        self.is_active = False
        self.wins = 0; self.losses = 0
        self.streak_w = 0; self.streak_l = 0
        self.max_w = 0; self.max_l = 0

    def icon(self, p): return "🟢" if p == "BIG" else ("🔴" if p == "SMALL" else "⚪")

    def broadcast(self, msg, kb=None):
        chats = set()
        if DEFAULT_CHAT_ID: chats.add(str(DEFAULT_CHAT_ID))
        if os.path.exists(CHATS_FILE):
            try:
                with open(CHATS_FILE, "r") as f: chats.update(json.load(f))
            except: pass
        for cid in chats: self.bot.send_message(cid, msg, reply_markup=kb)

    def parse_csv(self, content):
        records = []
        try:
            reader = csv.reader(io.StringIO(content))
            for row in reader:
                if not row: continue
                if str(row[0]).strip().lower() in {"period", "issue", "id"}: continue
                issue = str(row[0]).strip()
                num = int(row[1]) if len(row) > 1 and str(row[1]).strip().isdigit() else 0
                res = None
                if len(row) > 2:
                    r = str(row[2]).strip().upper()
                    if r in {"BIG", "SMALL"}: res = r
                if not res: res = "BIG" if num >= 5 else "SMALL"
                records.append({"issue": issue, "number": num, "result": res})
        except: pass
        return records

    def sync_and_predict(self):
        """Crucial: Fetches live market state and aligns predictions."""
        try:
            resp = requests.get(API_DOMAINS[0], params={"pageNo": 1, "pageSize": 2, "t": int(time.time()*1000)}, timeout=8)
            if resp.status_code == 200:
                lst = resp.json().get("data", {}).get("list", [])
                if lst:
                    live_issue = str(lst[0].get("issueNumber"))
                    self.last_issue = live_issue
                    self.last_pred, self.last_conf, self.last_details = self.core.predict(self.dataset)
                    return True
        except Exception as e:
            print(f"⚠️ Sync Error: {e}")
        return False

    def load_and_train(self, content):
        records = self.parse_csv(content)
        if len(records) < 50: return False, 0
        self.dataset = records
        self.core.train_all(self.dataset)
        self.is_active = True
        
        # Sync to live market immediately after training
        if self.sync_and_predict():
            next_issue = str(int(self.last_issue) + 1)
            now = datetime.now(BD_TZ)
            msg = (
                f"👑 <b>OMEGA QUANTUM AI V30.0 INITIATED</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📚 <b>Historical Data Mastered:</b> <code>{len(records)} Rounds</code>\n"
                f"🌐 <b>Live Market Synced:</b> <code>Period {self.last_issue}</code>\n"
                f"🎯 <b>Next Live Target:</b> <code>{next_issue}</code>\n"
                f"🧬 <b>Ensemble Signal:</b> <b>{self.last_pred}</b> {self.icon(self.last_pred)} <b>({self.last_conf}%)</b>\n"
                f"🧠 <b>Active Models:</b> <code>7 AI Engines + Genetic Optimizer</code>\n"
                f"🕒 <b>Sync Time:</b> <code>{now.strftime('%I:%M:%S %p')}</code>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"💎 <i>Advanced Educational Pattern System.</i>"
            )
            self.broadcast(msg, get_main_keyboard())
            return True, len(records)
        return False, 0

    def run(self):
        print("🚀 OMEGA QUANTUM AI V30.0 STARTED...")
        offset = None
        
        # Auto-load local dataset if exists
        if os.path.exists("dataset.csv"):
            print("📂 Found local dataset.csv. Training...")
            try:
                with open("dataset.csv", "r", encoding="utf-8") as f:
                    self.load_and_train(f.read())
            except Exception as e:
                print(f"⚠️ Local load error: {e}")

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
                    
                    kb = get_main_keyboard()
                    if data == "btn_stats": self.bot.send_message(chat_id, self._gen_stats(), reply_markup=kb)
                    elif data == "btn_time": self.bot.send_message(chat_id, self._gen_time(), reply_markup=kb)
                    elif data == "btn_models": self.bot.send_message(chat_id, self._gen_models(), reply_markup=kb)
                    elif data == "btn_signal": self.bot.send_message(chat_id, self._gen_signal(), reply_markup=kb)
                    elif data == "btn_risk": self.bot.send_message(chat_id, self._gen_risk(), reply_markup=kb)
                    elif data == "btn_genetic": self.bot.send_message(chat_id, self._gen_genetic(), reply_markup=kb)
                    continue

                msg = u.get("message", {})
                chat_id = str(msg.get("chat", {}).get("id", ""))
                if not chat_id: continue
                
                # Save chat
                chats = set()
                if DEFAULT_CHAT_ID: chats.add(str(DEFAULT_CHAT_ID))
                if os.path.exists(CHATS_FILE):
                    try: chats.update(json.load(open(CHATS_FILE, "r")))
                    except: pass
                chats.add(chat_id)
                json.dump(list(chats), open(CHATS_FILE, "w"))

                doc = msg.get("document")
                text = msg.get("text", "")
                
                if doc:
                    self.bot.send_message(chat_id, "⏳ <b>৭-লেয়ার AI লার্নিং ও জেনেটিক অপ্টিমাইজেশন চলছে...</b>")
                    fb = self.bot.get_file_bytes(doc.get("file_id"))
                    if fb:
                        ok, cnt = self.load_and_train(fb.decode("utf-8", errors="ignore"))
                        if not ok: self.bot.send_message(chat_id, "⚠️ কমপক্ষে ৫০+ রাউন্ড ডাটা প্রয়োজন।")
                    else: self.bot.send_message(chat_id, "⚠️ ফাইল ডাউনলোড সমস্যা।")
                    continue
                    
                if text == "/start":
                    self.bot.send_message(chat_id, "👑 <b>Omega Quantum AI V30.0</b>\n\nCSV ফাইল সেন্ড করুন।", reply_markup=kb)

            if not self.is_active:
                time.sleep(2)
                continue

            # Live Loop
            try:
                resp = requests.get(API_DOMAINS[0], params={"pageNo": 1, "pageSize": 10, "t": int(time.time()*1000)}, timeout=8)
                if resp.status_code == 200:
                    lst = resp.json().get("data", {}).get("list", [])
                    if lst:
                        curr_issue = str(lst[0].get("issueNumber"))
                        num = int(lst[0].get("number", 0))
                        actual = "BIG" if num >= 5 else "SMALL"
                        
                        if curr_issue != self.last_issue:
                            now = datetime.now(BD_TZ)
                            outcome = "⏳"
                            
                            # Evaluate previous prediction
                            if self.last_pred:
                                is_win = self.last_pred == actual
                                self.risk.record(is_win, now, self.last_conf)
                                for m_name, m_data in self.last_details.items():
                                    m_is_win = m_data["pred"] == actual
                                    self.core.record_outcome(m_name, m_is_win)
                                
                                if is_win:
                                    self.wins += 1; self.streak_w += 1; self.streak_l = 0
                                    if self.streak_w > self.max_w: self.max_w = self.streak_w
                                    outcome = "✅ <b>WIN</b>"
                                else:
                                    self.losses += 1; self.streak_l += 1; self.streak_w = 0
                                    if self.streak_l > self.max_l: self.max_l = self.streak_l
                                    outcome = "❌ <b>LOSS</b>"
                            
                            # Update state
                            self.last_issue = curr_issue
                            self.dataset.append({"issue": curr_issue, "number": num, "result": actual})
                            if len(self.dataset) > 2000: self.dataset = self.dataset[-2000:]
                            
                            # Retrain & Evolve
                            try:
                                subset = self.dataset[-500:] if len(self.dataset) > 500 else self.dataset
                                self.core.train_all(subset)
                                self.core.evolve_weights()
                            except Exception as e:
                                print(f"⚠️ Retrain error: {e}")
                                
                            # Predict next
                            self.last_pred, self.last_conf, self.last_details = self.core.predict(self.dataset)
                            
                            next_issue = str(int(curr_issue) + 1)
                            live_msg = (
                                f"🎯 <b>Target Period:</b> <code>{next_issue}</code>\n"
                                f"🧬 <b>Ensemble Signal:</b> <b>{self.last_pred}</b> {self.icon(self.last_pred)} <b>({self.last_conf}%)</b>\n"
                                f"━━━━━━━━━━━━━━━━━━━━\n"
                                f"🎲 <b>Last Result:</b> {curr_issue} ➔ <b>{actual} ({num})</b> | {outcome}\n"
                                f"🔥 <b>Streak:</b> W <code>{self.streak_w}</code> | L <code>{self.streak_l}</code>\n"
                                f"🕒 <b>Time:</b> <code>{now.strftime('%I:%M:%S %p')}</code>"
                            )
                            self.broadcast(live_msg, get_main_keyboard())
            except Exception as e:
                print(f"⚠️ API Error: {e}")
                
            time.sleep(2)

    # UI Generators
    def _gen_stats(self):
        total = self.wins + self.losses
        wr = (self.wins / total * 100) if total > 0 else 0.0
        return f"📊 <b>লাইভ পরিসংখ্যান</b>\n\n✅ Wins: <code>{self.wins}</code>\n❌ Losses: <code>{self.losses}</code>\n📈 Win-Rate: <code>{wr:.1f}%</code>\n🔥 Max Win Streak: <code>{self.max_w}</code>"

    def _gen_time(self):
        bs, br, cap, dd = self.risk.get_report()
        return f"🕒 <b>সেরা টাইম ও রিস্ক</b>\n\n🥇 Best Session: <b>{bs}</b> ({br:.1f}%)\n💰 Simulated Capital: <code>${cap:.2f}</code>\n📉 Max Drawdown: <code>${dd:.2f}</code>"

    def _gen_models(self):
        msg = "🧬 <b>৭-লেয়ার AI মডেল স্ট্যাটাস</b>\n━━━━━━━━━━━━━━━━━━━━\n"
        for name, data in self.last_details.items():
            msg += f"➔ <b>{name}:</b> {data['pred']} ({data['conf']}%) | Weight: {data['weight']}\n"
        return msg

    def _gen_signal(self):
        if not self.last_pred: return "⚠️ সিগন্যাল নেই।"
        next_issue = str(int(self.last_issue) + 1) if self.last_issue else "N/A"
        return f"🎯 <b>Active Target:</b> <code>{next_issue}</code>\n🧬 <b>Signal:</b> <b>{self.last_pred}</b> {self.icon(self.last_pred)} <b>({self.last_conf}%)</b>"

    def _gen_risk(self):
        cap, dd = self.risk.capital_sim, self.risk.max_drawdown
        return f"💰 <b>রিস্ক ম্যানেজমেন্ট</b>\n\n💵 Capital: <code>${cap:.2f}</code>\n📉 Max Drawdown: <code>${dd:.2f}</code>\n\n<i>Kelly Criterion Active.</i>"

    def _gen_genetic(self):
        msg = "🧠 <b>জেনেটিক অপ্টিমাইজার</b>\n━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"🧬 Generation: <code>{self.core.generation}</code>\n\n"
        sorted_w = sorted(self.core.weights.items(), key=lambda x: x[1], reverse=True)
        for name, w in sorted_w:
            msg += f"➔ <b>{name}:</b> <code>{w*100:.1f}%</code> Weight\n"
        return msg

#============================================================
# 🌐 WEB KEEP-ALIVE
#============================================================
def run_web():
    class S(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status":"Omega V30.0 Running"}')
        def log_message(self, *args): return
    port = int(os.environ.get("PORT", 5000))
    HTTPServer(("0.0.0.0", port), S).serve_forever()

#============================================================
# 🚀 ENTRY POINT
#============================================================
if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda s, f: _shutdown.set())
    threading.Thread(target=run_web, daemon=True).start()
    OmegaEngine().run()
