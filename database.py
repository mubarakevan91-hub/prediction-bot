# -*- coding: utf-8 -*-
"""
================================================================================
VIP STRIKE V35.0 ENTERPRISE - MODULE 2: PERSISTENT SQLITE DATABASE LAYER
================================================================================
"""

import sqlite3
import threading
import logging
from typing import List, Dict, Any, Optional, Set
from .config import CONFIG

logger = logging.getLogger("VIPStrikeDB")

class DatabaseManager:
    """Enterprise Thread-Safe SQLite Storage for Massive Historical Datasets."""

    def __init__(self, db_path: str = CONFIG.db_path):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=25.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Rounds Master Table
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
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_created ON rounds(created_at)")
            
            # Predictions Audit Log
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    issue TEXT PRIMARY KEY,
                    predicted_outcome TEXT NOT NULL,
                    confidence INTEGER NOT NULL,
                    actual_outcome TEXT,
                    is_correct INTEGER,
                    dl_pred TEXT,
                    ml_pred TEXT,
                    markov_pred TEXT,
                    russian_pred TEXT,
                    resonance_pred TEXT,
                    regime TEXT,
                    hour INTEGER,
                    session_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User Subscriptions
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
                data = [
                    (
                        r["issue"],
                        r["number"],
                        r["result"],
                        r.get("parity", "UNKNOWN"),
                        r.get("color", "UNKNOWN"),
                        r.get("timestamp", "")
                    )
                    for r in records
                ]
                cursor.executemany("""
                    INSERT OR IGNORE INTO rounds (issue, number, result, parity, color, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, data)
                conn.commit()
                return cursor.rowcount
            except Exception as e:
                logger.error(f"DB Bulk Insert Error: {e}")
                return 0

    def insert_round(self, issue: str, number: int, result: str, parity: str, color: str, timestamp_str: str) -> bool:
        with self._lock, self._get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO rounds (issue, number, result, parity, color, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (issue, number, result, parity, color, timestamp_str))
                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                logger.error(f"DB Insert Round Error: {e}")
                return False

    def insert_prediction(self, issue: str, pred: str, conf: int, dl_p: str, ml_p: str, mk_p: str, ru_p: str, res_p: str, regime: str, hour: int, session: str) -> None:
        with self._lock, self._get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO predictions 
                    (issue, predicted_outcome, confidence, dl_pred, ml_pred, markov_pred, russian_pred, resonance_pred, regime, hour, session_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (issue, pred, conf, dl_p, ml_p, mk_p, ru_p, res_p, regime, hour, session))
                conn.commit()
            except Exception as e:
                logger.error(f"DB Insert Prediction Error: {e}")

    def evaluate_prediction(self, issue: str, actual_outcome: str) -> Optional[bool]:
        with self._lock, self._get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT predicted_outcome FROM predictions WHERE issue = ?", (issue,))
                row = cursor.fetchone()
                if not row:
                    return None

                predicted = row["predicted_outcome"]
                is_correct = 1 if predicted == actual_outcome else 0

                cursor.execute("""
                    UPDATE predictions 
                    SET actual_outcome = ?, is_correct = ? 
                    WHERE issue = ?
                """, (actual_outcome, is_correct, issue))
                conn.commit()
                return bool(is_correct)
            except Exception as e:
                logger.error(f"DB Evaluate Error: {e}")
                return None

    def get_recent_rounds(self, limit: int = CONFIG.max_history_memory) -> List[Dict[str, Any]]:
        with self._lock, self._get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT issue, number, result, parity, color, timestamp 
                    FROM rounds 
                    ORDER BY issue ASC 
                    LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
            except Exception as e:
                logger.error(f"DB Fetch Error: {e}")
                return []

    def add_chat(self, chat_id: str, username: str = "") -> None:
        with self._lock, self._get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO allowed_chats (chat_id, username, is_active)
                    VALUES (?, ?, 1)
                """, (str(chat_id), username))
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
