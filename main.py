#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
👑 VIP STRIKE V35.0 - ULTRA 4485+ PREDICTION ENGINE (RENDER ALL-IN-ONE)
================================================================================
"""

import os
import sys
import io
import csv
import json
import time
import math
import random
import signal
import logging
import sqlite3
import threading
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any, Set, Union
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import warnings

warnings.filterwarnings("ignore")

try:
    import numpy as np
    import requests
    from sklearn.neural_network import MLPClassifier
    from sklearn.ensemble import (
        RandomForestClassifier,
        GradientBoostingClassifier,
        ExtraTreesClassifier
    )
    from sklearn.preprocessing import StandardScaler
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

# ==============================================================================
# CONFIG
# ==============================================================================
@dataclass
class SystemConfig:
    version: str = "35.0-ULTRA-4485"
    telegram_token: str = os.environ.get("TELEGRAM_TOKEN", "8858558197:AAHvvS-rh9j1U9grv3SzmyqPsxN1FHNlv6E")
    default_chat_id: str = os.environ.get("DEFAULT_CHAT_ID", "8395823375")
    db_path: str = os.environ.get("DB_PATH", "vip_strike_data.db")
    chats_file: str = os.environ.get("CHATS_FILE", "allowed_chats.json")
    http_port: int = int(os.environ.get("PORT", 5000))
    http_host: str = os.environ.get("HOST", "0.0.0.0")

    api_domains: List[str] = field(default_factory=lambda: [
        "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json",
        "https://draw.ar-lottery02.com/WinGo/WinGo_30S/GetHistoryIssuePage.json",
        "https://draw.ar-lottery03.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"
    ])

    poll_interval_sec: float = 2.0
    request_timeout_sec: float = 8.0
    max_history_memory: int = 25000
    min_train_samples: int = 15
    feature_window_size: int = 12
    resonance_window_size: int = 10
    base_confidence_floor: int = 62
    base_confidence_ceiling: int = 99
    tz_offset_hours: int = 6

CONFIG = SystemConfig()
BD_TZ = timezone(timedelta(hours=CONFIG.tz_offset_hours))
_SHUTDOWN_EVENT = threading.Event()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("VIPStrike35")

def get_bd_now() -> datetime:
    return datetime.now(BD_TZ)

def format_bd_time(dt: Optional[datetime] = None) -> str:
    if dt is None:
        dt = get_bd_now()
    return dt.strftime("%I:%M:%S %p")

def result_from_number(num: Union[int, str]) -> str:
    try:
        n = int(num)
    except Exception:
        n = 0
    return "BIG" if n >= 5 else "SMALL"

def parity_from_number(num: Union[int, str]) -> str:
    try:
        n = int(num)
    except Exception:
        n = 0
    return "EVEN" if n % 2 == 0 else "ODD"

def color_from_number(num: Union[int, str]) -> str:
    try:
        n = int(num)
    except Exception:
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

# ==============================================================================
# DATABASE LAYER
# ==============================================================================
class DatabaseManager:
    def __init__(self, db_path: str = CONFIG.db_path):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=20.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rounds (
                    issue TEXT PRIMARY KEY,
                    number INTEGER NOT NULL,
                    result TEXT NOT NULL,
                    parity TEXT NOT NULL,
                    color TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    issue TEXT PRIMARY KEY,
                    predicted_outcome TEXT NOT NULL,
                    confidence INTEGER NOT NULL,
                    actual_outcome TEXT,
                    is_correct INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS allowed_chats (
                    chat_id TEXT PRIMARY KEY,
                    username TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 1
                )
            """)
            conn.commit()

    def insert_rounds_bulk(self, records: List[Dict[str, Any]]) -> int:
        with self._lock, self._get_connection() as conn:
            try:
                cursor = conn.cursor()
                data = [(r["issue"], r["number"], r["result"], r["parity"], r["color"], r.get("timestamp", format_bd_time())) for r in records]
                cursor.executemany("INSERT OR IGNORE INTO rounds (issue, number, result, parity, color, timestamp) VALUES (?, ?, ?, ?, ?, ?)", data)
                conn.commit()
                return cursor.rowcount
            except Exception:
                return 0

    def insert_round(self, issue: str, number: int, result: str, parity: str, color: str, timestamp_str: str) -> bool:
        with self._lock, self._get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute("INSERT OR IGNORE INTO rounds (issue, number, result, parity, color, timestamp) VALUES (?, ?, ?, ?, ?, ?)", (issue, number, result, parity, color, timestamp_str))
                conn.commit()
                return cursor.rowcount > 0
            except Exception:
                return False

    def get_recent_rounds(self, limit: int = CONFIG.max_history_memory) -> List[Dict[str, Any]]:
        with self._lock, self._get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT issue, number, result, parity, color, timestamp FROM rounds ORDER BY issue ASC LIMIT ?", (limit,))
                return [dict(r) for r in cursor.fetchall()]
            except Exception:
                return []

    def add_chat(self, chat_id: str, username: str = "") -> None:
        with self._lock, self._get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute("INSERT OR REPLACE INTO allowed_chats (chat_id, username, is_active) VALUES (?, ?, 1)", (str(chat_id), username))
                conn.commit()
            except Exception:
                pass

    def get_all_chats(self) -> Set[str]:
        chats = set()
        if CONFIG.default_chat_id:
            chats.add(str(CONFIG.default_chat_id))
        with self._lock, self._get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT chat_id FROM allowed_chats WHERE is_active = 1")
                for r in cursor.fetchall():
                    chats.add(str(r["chat_id"]))
            except Exception:
                pass
        return chats

# ==============================================================================
# 4,485 RESONANCE SCANNER
# ==============================================================================
class HistoricalSequenceResonanceEngine:
    def __init__(self, fingerprint_len: int = 10, top_k: int = 15):
        self.fingerprint_len = fingerprint_len
        self.top_k = top_k
        self.confidence_score = 0
        self.last_prediction = None

    def predict(self, dataset: List[Dict[str, Any]]) -> Tuple[Optional[str], int]:
        n = len(dataset)
        flen = self.fingerprint_len
        if n < flen + 20:
            return None, 0

        seq_res = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        seq_num = [float(d.get("number", 0)) / 9.0 for d in dataset]

        target_res = seq_res[-flen:]
        target_num = seq_num[-flen:]

        matches = []
        for i in range(n - flen - 1):
            sub_res = seq_res[i:i + flen]
            sub_num = seq_num[i:i + flen]
            next_outcome = seq_res[i + flen]

            res_diff = sum(1 for a, b in zip(target_res, sub_res) if a != b)
            num_dist = sum(abs(a - b) for a, b in zip(target_num, sub_num))
            matches.append((res_diff * 2.0 + num_dist, next_outcome))

        matches.sort(key=lambda x: x[0])
        best_matches = matches[:self.top_k]
        if not best_matches:
            return None, 0

        weights = [1.0 / (1.0 + m[0]) for m in best_matches]
        outcomes = [m[1] for m in best_matches]
        prob_big = sum(w * out for w, out in zip(weights, outcomes)) / sum(weights)

        pred = "BIG" if prob_big >= 0.50 else "SMALL"
        conf = int(clamp(abs(prob_big - 0.50) * 200 + 66, CONFIG.base_confidence_floor, 98))
        self.last_prediction = pred
        self.confidence_score = conf
        return pred, conf

# ==============================================================================
# MARKOV ENGINE (ORDER 2 TO 8)
# ==============================================================================
class HighOrderMarkovEngine:
    def __init__(self):
        self.markov8 = defaultdict(lambda: [0, 0])
        self.markov6 = defaultdict(lambda: [0, 0])
        self.markov4 = defaultdict(lambda: [0, 0])
        self.markov2 = defaultdict(lambda: [0, 0])
        self.is_trained = False

    def train(self, dataset: List[Dict[str, Any]]) -> bool:
        n = len(dataset)
        if n < 15:
            return False
        self.markov8.clear()
        self.markov6.clear()
        self.markov4.clear()
        self.markov2.clear()

        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        for i in range(n - 2):
            self.markov2[(seq[i], seq[i + 1])][seq[i + 2]] += 1
        for i in range(n - 4):
            self.markov4[(seq[i], seq[i + 1], seq[i + 2], seq[i + 3])][seq[i + 4]] += 1
        for i in range(n - 6):
            self.markov6[(seq[i], seq[i + 1], seq[i + 2], seq[i + 3], seq[i + 4], seq[i + 5])][seq[i + 6]] += 1
        for i in range(n - 8):
            self.markov8[(seq[i], seq[i + 1], seq[i + 2], seq[i + 3], seq[i + 4], seq[i + 5], seq[i + 6], seq[i + 7])][seq[i + 8]] += 1

        self.is_trained = True
        return True

    def predict(self, dataset: List[Dict[str, Any]]) -> Tuple[Optional[str], int]:
        if not self.is_trained or len(dataset) < 8:
            return None, 0
        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        votes, weights = [], []

        if len(seq) >= 8:
            c = self.markov8.get(tuple(seq[-8:]))
            if c and sum(c) >= 2:
                votes.append((c[1] + 1) / (sum(c) + 2))
                weights.append(0.40)
        if len(seq) >= 6:
            c = self.markov6.get(tuple(seq[-6:]))
            if c and sum(c) >= 2:
                votes.append((c[1] + 1) / (sum(c) + 2))
                weights.append(0.30)
        if len(seq) >= 4:
            c = self.markov4.get(tuple(seq[-4:]))
            if c and sum(c) >= 2:
                votes.append((c[1] + 1) / (sum(c) + 2))
                weights.append(0.20)

        if not votes:
            return ("BIG" if seq[-1] == 1 else "SMALL"), 60

        weighted_prob = sum(v * w for v, w in zip(votes, weights)) / sum(weights)
        pred = "BIG" if weighted_prob >= 0.50 else "SMALL"
        conf = int(clamp(abs(weighted_prob - 0.50) * 200 + 68, CONFIG.base_confidence_floor, 99))
        return pred, conf

# ==============================================================================
# FEATURE EXTRACTOR
# ==============================================================================
class UltraFeatureExtractor:
    def extract_dataset(self, dataset: List[Dict[str, Any]]):
        if len(dataset) <= 25:
            return [], []
        seq_res = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        seq_num = [float(d.get("number", 0)) / 9.0 for d in dataset]
        X, y = [], []
        for i in range(20, len(dataset)):
            row = self._row(seq_res, seq_num, i)
            if row:
                X.append(row)
                y.append(seq_res[i])
        return X, y

    def extract_latest(self, dataset: List[Dict[str, Any]]):
        if len(dataset) < 20:
            return None
        seq_res = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        seq_num = [float(d.get("number", 0)) / 9.0 for d in dataset]
        return self._row(seq_res, seq_num, len(dataset))

    def _row(self, seq_res, seq_num, idx):
        feats = []
        feats.extend(seq_res[idx - 14:idx])
        feats.extend(seq_num[idx - 10:idx])
        for w in [3, 5, 8, 13, 21]:
            feats.append(sum(seq_res[idx - w:idx]) / float(w) if idx >= w else 0.5)
        return feats

# ==============================================================================
# DEEP NEURAL NETWORK (256-128-64-32)
# ==============================================================================
class DeepNeuralEngineV35:
    def __init__(self):
        self.is_trained = False
        self.scaler = None
        self.model = None

    def train(self, dataset, extractor):
        if not ML_AVAILABLE or len(dataset) < 25:
            return False
        X, y = extractor.extract_dataset(dataset)
        if len(X) < 20 or len(set(y)) < 2:
            return False
        try:
            self.scaler = StandardScaler()
            Xs = self.scaler.fit_transform(np.array(X))
            self.model = MLPClassifier(hidden_layer_sizes=(256, 128, 64, 32), max_iter=250, random_state=42, early_stopping=True)
            self.model.fit(Xs, np.array(y))
            self.is_trained = True
            return True
        except Exception:
            return False

    def predict(self, dataset, extractor):
        if not self.is_trained or not ML_AVAILABLE or self.model is None:
            return None, 0
        feat = extractor.extract_latest(dataset)
        if not feat:
            return None, 0
        try:
            feat_s = self.scaler.transform(np.array([feat]))
            prob = float(self.model.predict_proba(feat_s)[0][1])
            pred = "BIG" if prob >= 0.50 else "SMALL"
            conf = int(clamp(abs(prob - 0.50) * 200 + 67, CONFIG.base_confidence_floor, 99))
            return pred, conf
        except Exception:
            return None, 0

# ==============================================================================
# ML MEGA ENSEMBLE
# ==============================================================================
class MachineLearningMegaEnsemble:
    def __init__(self):
        self.is_trained = False
        self.rf = None
        self.gb = None
        self.scaler = None

    def train(self, dataset, extractor):
        if not ML_AVAILABLE or len(dataset) < 25:
            return False
        X, y = extractor.extract_dataset(dataset)
        if len(X) < 20 or len(set(y)) < 2:
            return False
        try:
            self.scaler = StandardScaler()
            Xs = self.scaler.fit_transform(np.array(X))
            self.rf = RandomForestClassifier(n_estimators=100, max_depth=7, random_state=42)
            self.rf.fit(Xs, np.array(y))
            self.gb = GradientBoostingClassifier(n_estimators=80, max_depth=4, random_state=42)
            self.gb.fit(Xs, np.array(y))
            self.is_trained = True
            return True
        except Exception:
            return False

    def predict(self, dataset, extractor):
        if not self.is_trained or not ML_AVAILABLE or self.rf is None:
            return None, 0
        feat = extractor.extract_latest(dataset)
        if not feat:
            return None, 0
        try:
            feat_s = self.scaler.transform(np.array([feat]))
            p1 = float(self.rf.predict_proba(feat_s)[0][1])
            p2 = float(self.gb.predict_proba(feat_s)[0][1])
            prob = (0.55 * p1) + (0.45 * p2)
            pred = "BIG" if prob >= 0.50 else "SMALL"
            conf = int(clamp(abs(prob - 0.50) * 200 + 66, CONFIG.base_confidence_floor, 98))
            return pred, conf
        except Exception:
            return None, 0

# ==============================================================================
# RUSSIAN PREDICTION ENGINE V35
# ==============================================================================
class RussianPredictionEngineV35:
    def __init__(self):
        self.markov3 = defaultdict(lambda: [0, 0])
        self.streak_profile = defaultdict(lambda: [0, 0])
        self.trained = False

    def train(self, dataset):
        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        if len(seq) < 10:
            return False
        self.markov3.clear()
        self.streak_profile.clear()
        for i in range(len(seq) - 3):
            self.markov3[(seq[i], seq[i + 1], seq[i + 2])][seq[i + 3]] += 1
        self.trained = True
        return True

    def predict(self, dataset):
        if not self.trained or len(dataset) < 4:
            return None, 0
        seq = [1 if str(d.get("result", "")).upper() == "BIG" else 0 for d in dataset]
        c = self.markov3.get(tuple(seq[-3:]))
        if c and sum(c) >= 2:
            prob = (c[1] + 1) / (sum(c) + 2)
            pred = "BIG" if prob >= 0.50 else "SMALL"
            conf = int(clamp(abs(prob - 0.50) * 200 + 64, CONFIG.base_confidence_floor, 98))
            return pred, conf
        return ("BIG" if seq[-1] == 1 else "SMALL"), 63

# ==============================================================================
# TELEGRAM BOT & KEYBOARDS
# ==============================================================================
class TelegramBotClient:
    def __init__(self, token=CONFIG.telegram_token):
        self.url = f"https://api.telegram.org/bot{token}/"

    def send_message(self, chat_id, text, reply_markup=None):
        payload = {"chat_id": str(chat_id), "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        try:
            requests.post(self.url + "sendMessage", json=payload, timeout=CONFIG.request_timeout_sec)
        except Exception:
            pass

    def answer_callback(self, cb_id, text=""):
        try:
            requests.post(self.url + "answerCallbackQuery", data={"callback_query_id": cb_id, "text": text}, timeout=4.0)
        except Exception:
            pass

    def get_file_bytes(self, file_id):
        try:
            res = requests.get(self.url + "getFile", params={"file_id": file_id}, timeout=10.0).json()
            path = res.get("result", {}).get("file_path")
            if path:
                return requests.get(f"https://api.telegram.org/file/bot{CONFIG.telegram_token}/{path}", timeout=40.0).content
        except Exception:
            pass
        return None

    def get_updates(self, offset=None):
        try:
            p = {"timeout": 2}
            if offset:
                p["offset"] = offset
            res = requests.get(self.url + "getUpdates", params=p, timeout=CONFIG.request_timeout_sec)
            return res.json().get("result", []) if res.status_code == 200 else []
        except Exception:
            return []

def get_vip_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📊 লাইভ পরিসংখ্যান", "callback_data": "btn_live_stats"}, {"text": "🎯 বর্তমান সিগন্যাল", "callback_data": "btn_curr_signal"}],
            [{"text": "🔍 ৪,৪৮৫ রেজোন্যান্স স্ক্যান", "callback_data": "btn_resonance"}, {"text": "🧬 কনসেনসাস ম্যাট্রিক্স", "callback_data": "btn_ensemble"}]
        ]
    }

# ==============================================================================
# MASTER ENGINE ORCHESTRATOR
# ==============================================================================
class MasterEngine:
    def __init__(self):
        self.dataset = []
        self.db = DatabaseManager()
        self.bot = TelegramBotClient()
        self.extractor = UltraFeatureExtractor()

        self.neural_engine = DeepNeuralEngineV35()
        self.ml_mega = MachineLearningMegaEnsemble()
        self.markov_engine = HighOrderMarkovEngine()
        self.russian_engine = RussianPredictionEngineV35()
        self.resonance_engine = HistoricalSequenceResonanceEngine()

        self.last_issue = None
        self.last_prediction = None
        self.last_pred_conf = 0

        self.last_dl_pred, self.last_dl_conf = None, 0
        self.last_ml_pred, self.last_ml_conf = None, 0
        self.last_mk_pred, self.last_mk_conf = None, 0
        self.last_ru_pred, self.last_ru_conf = None, 0
        self.last_res_pred, self.last_res_conf = None, 0

        self.total_wins = 0
        self.total_losses = 0
        self.current_win_streak = 0
        self.current_loss_streak = 0
        self.max_win_streak = 0
        self.is_active = False

        self._hydrate()

    def _hydrate(self):
        saved = self.db.get_recent_rounds()
        if len(saved) >= CONFIG.min_train_samples:
            self.dataset = saved
            self.train_all()
            self.last_issue = self.dataset[-1]["issue"]
            self.is_active = True

    def train_all(self):
        self.neural_engine.train(self.dataset, self.extractor)
        self.ml_mega.train(self.dataset, self.extractor)
        self.markov_engine.train(self.dataset)
        self.russian_engine.train(self.dataset)

    def refresh_predictions(self):
        dl_p, dl_c = self.neural_engine.predict(self.dataset, self.extractor)
        ml_p, ml_c = self.ml_mega.predict(self.dataset, self.extractor)
        mk_p, mk_c = self.markov_engine.predict(self.dataset)
        ru_p, ru_c = self.russian_engine.predict(self.dataset)
        res_p, res_c = self.resonance_engine.predict(self.dataset)

        self.last_dl_pred, self.last_dl_conf = dl_p, dl_c
        self.last_ml_pred, self.last_ml_conf = ml_p, ml_c
        self.last_mk_pred, self.last_mk_conf = mk_p, mk_c
        self.last_ru_pred, self.last_ru_conf = ru_p, ru_c
        self.last_res_pred, self.last_res_conf = res_p, res_c

        models = [(dl_p, dl_c, 0.25), (ml_p, ml_c, 0.20), (res_p, res_c, 0.20), (mk_p, mk_c, 0.18), (ru_p, ru_c, 0.17)]
        votes, weights = [], []
        for p, c, w in models:
            if p:
                votes.append(c / 100.0 if p == "BIG" else (1.0 - c / 100.0))
                weights.append(w)

        if votes:
            prob = sum(v * w for v, w in zip(votes, weights)) / sum(weights)
            self.last_prediction = "BIG" if prob >= 0.50 else "SMALL"
            self.last_pred_conf = int(clamp(abs(prob - 0.50) * 200 + 68, CONFIG.base_confidence_floor, CONFIG.base_confidence_ceiling))
        else:
            self.last_prediction, self.last_pred_conf = None, 0

    def broadcast(self, msg, kb=None):
        for cid in self.db.get_all_chats():
            self.bot.send_message(cid, msg, reply_markup=kb)

    def safe_next_issue(self, issue):
        try:
            return str(int(issue) + 1)
        except Exception:
            return f"{issue}+1"

    def ingest_manual_dataset(self, content_str):
        records = []
        try:
            reader = csv.reader(io.StringIO(content_str))
            for row in reader:
                if not row or str(row[0]).strip().lower() in {"period", "issue", "id"}:
                    continue
                issue = str(row[0]).strip()
                num = int(row[1].strip()) if len(row) > 1 and str(row[1]).strip().isdigit() else 0
                res = str(row[2]).strip().upper() if len(row) > 2 and str(row[2]).strip().upper() in {"BIG", "SMALL"} else result_from_number(num)
                records.append({"issue": issue, "number": num, "result": res, "parity": parity_from_number(num), "color": color_from_number(num), "timestamp": format_bd_time()})
        except Exception:
            pass

        if len(records) < CONFIG.min_train_samples:
            return False, len(records)

        self.dataset = records
        self.db.insert_rounds_bulk(records)
        self.train_all()
        self.is_active = True
        self.last_issue = self.dataset[-1]["issue"]
        self.refresh_predictions()

        next_i = self.safe_next_issue(self.last_issue)
        msg = (
            f"👑 <b>ULTRA HYBRID AI/ML/DL TRAINED ({len(records)} ROUNDS)</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📚 <b>Trained Memory:</b> <code>{len(records)} Records Active</code>\n"
            f"🎯 <b>Next Period:</b> <code>{next_i}</code>\n"
            f"🧬 <b>Final Ensemble:</b> <b>{self.last_prediction or 'N/A'}</b> {signal_badge(self.last_prediction)} <b>({self.last_pred_conf}%)</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🧠 <b>Deep Neural (256L):</b> {self.last_dl_pred} ({self.last_dl_conf}%)\n"
            f"🌲 <b>ML Trees:</b> {self.last_ml_pred} ({self.last_ml_conf}%)\n"
            f"🔍 <b>4485 Resonance:</b> {self.last_res_pred} ({self.last_res_conf}%)\n"
            f"🎲 <b>Markov O8:</b> {self.last_mk_pred} ({self.last_mk_conf}%)\n"
            f"🇷🇺 <b>Russian Core:</b> {self.last_ru_pred} ({self.last_ru_conf}%)\n"
            f"🕒 <b>Sync Time:</b> <code>{format_bd_time()}</code>"
        )
        self.broadcast(msg, get_vip_keyboard())
        return True, len(records)

    def run(self):
        logger.info("🚀 ULTRA ENTERPRISE PREDICTION SUITE RUNNING...")
        offset = None

        while not _SHUTDOWN_EVENT.is_set():
            updates = self.bot.get_updates(offset)
            for u in updates:
                offset = u["update_id"] + 1
                if "callback_query" in u:
                    cb = u["callback_query"]
                    data = cb.get("data", "")
                    chat_id = str(cb.get("message", {}).get("chat", {}).get("id", ""))
                    self.bot.answer_callback(cb.get("id"), "✅")
                    if chat_id:
                        kb = get_vip_keyboard()
                        if data == "btn_live_stats":
                            total = self.total_wins + self.total_losses
                            wr = (self.total_wins / total * 100.0) if total > 0 else 0.0
                            self.bot.send_message(chat_id, f"📊 <b>Live Stats:</b> Wins: <code>{self.total_wins}</code> | Losses: <code>{self.total_losses}</code> | WinRate: <code>{wr:.1f}%</code> | Streak: <code>{self.current_win_streak}</code>", reply_markup=kb)
                        elif data in ("btn_curr_signal", "btn_ensemble"):
                            next_i = self.safe_next_issue(self.last_issue)
                            self.bot.send_message(chat_id, f"🎯 <b>Period:</b> <code>{next_i}</code>\n🧬 <b>Signal:</b> <b>{self.last_prediction}</b> {signal_badge(self.last_prediction)} ({self.last_pred_conf}%)", reply_markup=kb)
                        elif data == "btn_resonance":
                            self.bot.send_message(chat_id, f"🔍 <b>4485 Resonance:</b> {self.last_res_pred} ({self.last_res_conf}%) on {len(self.dataset)} records.", reply_markup=kb)
                    continue

                msg = u.get("message", {})
                chat_id = str(msg.get("chat", {}).get("id", ""))
                doc = msg.get("document")
                text = msg.get("text", "")

                if chat_id:
                    self.db.add_chat(chat_id, msg.get("chat", {}).get("username", ""))
                    if doc:
                        self.bot.send_message(chat_id, "⏳ <b>ফাইল প্রসেসিং ও ৪,৪৮৫+ ডিপ লার্নিং ট্রেনিং চলছে...</b>")
                        b = self.bot.get_file_bytes(doc.get("file_id"))
                        if b:
                            ok, cnt = self.ingest_manual_dataset(b.decode("utf-8", errors="ignore"))
                            if not ok:
                                self.bot.send_message(chat_id, "⚠️ মডেলে ট্রেইনিংয়ের জন্য কমপক্ষে ১৫+ রাউন্ড প্রয়োজন।")
                        else:
                            self.bot.send_message(chat_id, "⚠️ ফাইল ডাউনলোড করা যায়নি।")
                    elif text.startswith("/start"):
                        self.bot.send_message(chat_id, "👑 <b>VIP Strike V35.0 Ultra AI Engine Live!</b>\nআপনার <code>dataset_export.csv</code> ফাইলটি পাঠান।", reply_markup=get_vip_keyboard())

            # Real-Time Lottery API Polling
            try:
                for api_url in CONFIG.api_domains:
                    try:
                        resp = requests.get(api_url, params={"pageNo": 1, "pageSize": 10, "t": int(time.time() * 1000)}, timeout=CONFIG.request_timeout_sec)
                        if resp.status_code == 200:
                            lst = resp.json().get("data", {}).get("list", [])
                            if lst:
                                current_issue = str(lst[0].get("issueNumber"))
                                num = int(lst[0].get("number", 0))
                                actual_res = result_from_number(num)

                                if current_issue != self.last_issue:
                                    outcome_str = "⏳"
                                    if self.last_prediction:
                                        is_win = (self.last_prediction == actual_res)
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
                                            outcome_str = "❌ <b>LOSS</b>"

                                    self.dataset.append({"issue": current_issue, "number": num, "result": actual_res, "parity": parity_from_number(num), "color": color_from_number(num), "timestamp": format_bd_time()})
                                    if len(self.dataset) > CONFIG.max_history_memory:
                                        self.dataset = self.dataset[-CONFIG.max_history_memory:]

                                    self.train_all()
                                    self.last_issue = current_issue
                                    self.is_active = True
                                    self.refresh_predictions()

                                    next_i = self.safe_next_issue(current_issue)
                                    live_msg = (
                                        f"🎯 <b>Period:</b> <code>{next_i}</code>\n"
                                        f"🧬 <b>Final Signal:</b> <b>{self.last_prediction or 'N/A'}</b> {signal_badge(self.last_prediction)} <b>({self.last_pred_conf}%)</b>\n"
                                        f"━━━━━━━━━━━━━━━━━━━━\n"
                                        f"🧠 <b>Neural:</b> {self.last_dl_pred} ({self.last_dl_conf}%) | 🌲 <b>ML:</b> {self.last_ml_pred} ({self.last_ml_conf}%)\n"
                                        f"🔍 <b>Resonance:</b> {self.last_res_pred} ({self.last_res_conf}%) | 🇷🇺 <b>Russian:</b> {self.last_ru_pred} ({self.last_ru_conf}%)\n"
                                        f"━━━━━━━━━━━━━━━━━━━━\n"
                                        f"🎲 <b>Last:</b> {current_issue} ➔ <b>{actual_res} ({num})</b> | {outcome_str}\n"
                                        f"🔥 <b>Streak:</b> Win <code>{self.current_win_streak}</code> | Loss <code>{self.current_loss_streak}</code>\n"
                                        f"🕒 <b>Time:</b> <code>{format_bd_time()}</code>"
                                    )
                                    self.broadcast(live_msg, get_vip_keyboard())
                                break
                    except Exception:
                        continue
            except Exception:
                pass

            time.sleep(CONFIG.poll_interval_sec)

# ==============================================================================
# WEB SERVER FOR RENDER
# ==============================================================================
def run_web(engine):
    class S(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy", "engine": "VIP Strike Ultra V35.0", "records": len(engine.dataset), "signal": engine.last_prediction}).encode("utf-8"))
        def log_message(self, format, *args):
            return
    server = HTTPServer((CONFIG.http_host, CONFIG.http_port), S)
    logger.info(f"🌐 Web Server listening on port {CONFIG.http_port}")
    server.serve_forever()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda s, f: _SHUTDOWN_EVENT.set())
    signal.signal(signal.SIGTERM, lambda s, f: _SHUTDOWN_EVENT.set())
    master = MasterEngine()
    threading.Thread(target=run_web, args=(master,), daemon=True).start()
    master.run()
