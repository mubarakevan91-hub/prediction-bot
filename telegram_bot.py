# -*- coding: utf-8 -*-
"""
================================================================================
VIP STRIKE V35.0 ENTERPRISE - MODULE 13: TELEGRAM BOT CLIENT & UI MATRIX
================================================================================
"""

import logging
from typing import Dict, Any, Optional, List, Union
from .config import CONFIG

logger = logging.getLogger("VIPStrikeBot")

try:
    import requests
except ImportError:
    pass

class TelegramBotClient:
    """Robust Telegram API Wrapper with Timeout and Retry Guards."""

    def __init__(self, token: str = CONFIG.telegram_token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}/"

    def send_message(self, chat_id: Union[str, int], text: str, reply_markup: Optional[Dict] = None) -> bool:
        payload = {
            "chat_id": str(chat_id),
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        try:
            resp = requests.post(self.base_url + "sendMessage", json=payload, timeout=CONFIG.request_timeout_sec)
            return resp.status_code == 200
        except Exception as e:
            logger.debug(f"Telegram Send Error: {e}")
            return False

    def answer_callback(self, callback_id: str, text: str = "") -> None:
        try:
            requests.post(self.base_url + "answerCallbackQuery", data={"callback_query_id": callback_id, "text": text}, timeout=4.0)
        except Exception:
            pass

    def get_file_bytes(self, file_id: str) -> Optional[bytes]:
        try:
            res = requests.get(self.base_url + "getFile", params={"file_id": file_id}, timeout=10.0).json()
            path = res.get("result", {}).get("file_path")
            if path:
                file_url = f"https://api.telegram.org/file/bot{self.token}/{path}"
                return requests.get(file_url, timeout=40.0).content
        except Exception as e:
            logger.error(f"Telegram getFile error: {e}")
        return None

    def get_updates(self, offset: Optional[int] = None) -> List[Dict[str, Any]]:
        try:
            params = {"timeout": 2}
            if offset is not None:
                params["offset"] = offset
            res = requests.get(self.base_url + "getUpdates", params=params, timeout=CONFIG.request_timeout_sec)
            if res.status_code == 200:
                return res.json().get("result", [])
        except Exception:
            pass
        return []

def get_vip_inline_keyboard() -> Dict[str, Any]:
    return {
        "inline_keyboard": [
            [
                {"text": "📊 লাইভ পরিসংখ্যান", "callback_data": "btn_live_stats"},
                {"text": "🎯 বর্তমান সিগন্যাল", "callback_data": "btn_curr_signal"}
            ],
            [
                {"text": "🔍 ৪,৪৮৫ রেজোন্যান্স স্ক্যান", "callback_data": "btn_resonance"},
                {"text": "🧬 কনসেনসাস ম্যাট্রিক্স", "callback_data": "btn_ensemble"}
            ],
            [
                {"text": "🔬 Entropy & Math", "callback_data": "btn_math_entropy"},
                {"text": "💰 Risk & Bankroll", "callback_data": "btn_risk_mgmt"}
            ]
        ]
    }
