# -*- coding: utf-8 -*-
"""
================================================================================
VIP STRIKE V35.0 ENTERPRISE - MODULE 1: CONFIGURATION & GLOBAL STATE
================================================================================
"""

import os
from dataclasses import dataclass, field
from typing import List
from datetime import timezone, timedelta

@dataclass
class EnterpriseConfig:
    """Enterprise Configuration and Hyperparameters."""
    version: str = "35.0-ENTERPRISE-ULTRA"
    app_name: str = "VIP Strike AI Intelligence Core"
    
    # Telegram Credentials
    telegram_token: str = os.environ.get("TELEGRAM_TOKEN", "8858558197:AAHvvS-rh9j1U9grv3SzmyqPsxN1FHNlv6E")
    default_chat_id: str = os.environ.get("DEFAULT_CHAT_ID", "8395823375")
    chats_file: str = os.environ.get("CHATS_FILE", "allowed_chats.json")
    
    # Database Configuration
    db_path: str = os.environ.get("DB_PATH", "vip_strike_ultra.db")
    
    # Web & REST API Configuration
    http_host: str = os.environ.get("HOST", "0.0.0.0")
    http_port: int = int(os.environ.get("PORT", 5000))
    
    # API Polling Domains
    api_domains: List[str] = field(default_factory=lambda: [
        "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json",
        "https://draw.ar-lottery02.com/WinGo/WinGo_30S/GetHistoryIssuePage.json",
        "https://draw.ar-lottery03.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"
    ])
    
    # Polling & Networking
    poll_interval_sec: float = 2.0
    request_timeout_sec: float = 8.0
    
    # Dataset Limits & Training Triggers (Tuned for 4485+ Records)
    max_history_memory: int = 25000
    min_train_samples: int = 20
    feature_window_size: int = 14
    resonance_window_size: int = 10
    top_k_resonance_matches: int = 15
    
    # Confidence Bounds
    base_confidence_floor: int = 62
    base_confidence_ceiling: int = 99
    
    # Dynamic Ensemble Baseline Weights
    weight_deep_neural: float = 0.25
    weight_ml_ensemble: float = 0.20
    weight_sequence_resonance: float = 0.20
    weight_markov_high_order: float = 0.18
    weight_russian_core: float = 0.17
    
    # Timezone Offset (Bangladesh Standard Time: UTC+6)
    tz_offset_hours: int = 6

CONFIG = EnterpriseConfig()
BD_TZ = timezone(timedelta(hours=CONFIG.tz_offset_hours))
