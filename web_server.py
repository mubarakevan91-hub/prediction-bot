# -*- coding: utf-8 -*-
"""
================================================================================
VIP STRIKE V35.0 ENTERPRISE - MODULE 14: EMBEDDED WEB DASHBOARD & REST API
================================================================================
"""

import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any
from .config import CONFIG

logger = logging.getLogger("VIPStrikeWeb")

def run_web_dashboard(engine: Any) -> None:
    class RequestHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path in ("/", "/dashboard"):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                
                total = engine.total_wins + engine.total_losses
                wr = (engine.total_wins / total * 100.0) if total > 0 else 0.0
                
                html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VIP Strike V35 Ultra Dashboard</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0b1329; color: #f8fafc; margin: 0; padding: 24px; }}
        .container {{ max-width: 960px; margin: 0 auto; }}
        .card {{ background: #172554; border-radius: 12px; padding: 24px; margin-bottom: 20px; border: 1px solid #1e40af; }}
        h1, h2 {{ color: #60a5fa; margin-top: 0; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }}
        .metric {{ background: #0f172a; padding: 18px; border-radius: 8px; border: 1px solid #334155; text-align: center; }}
        .metric-val {{ font-size: 26px; font-weight: bold; color: #4ade80; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>👑 VIP Strike V35 Ultra 4485+ Enterprise Dashboard</h1>
            <p>Active Historical Records: <b>{len(engine.dataset)}</b> | Status: <span style="color:#4ade80; font-weight:bold;">● RUNNING LIVE</span></p>
            <p>Active Period: <code>{engine.last_issue or 'Syncing...'}</code></p>
        </div>
        <div class="card">
            <h2>🎯 Model Signals Matrix</h2>
            <div class="grid">
                <div class="metric"><div>Final Consensus</div><div class="metric-val">{engine.last_prediction or 'N/A'} ({engine.last_pred_conf}%)</div></div>
                <div class="metric"><div>Deep Neural (256L)</div><div class="metric-val">{engine.last_dl_pred or 'N/A'} ({engine.last_dl_conf}%)</div></div>
                <div class="metric"><div>ML Mega Ensemble</div><div class="metric-val">{engine.last_ml_pred or 'N/A'} ({engine.last_ml_conf}%)</div></div>
                <div class="metric"><div>4485 Resonance</div><div class="metric-val">{engine.last_res_pred or 'N/A'} ({engine.last_res_conf}%)</div></div>
            </div>
        </div>
        <div class="card">
            <h2>📈 Performance Metrics</h2>
            <div class="grid">
                <div class="metric"><div>Total Wins</div><div class="metric-val">{engine.total_wins}</div></div>
                <div class="metric"><div>Total Losses</div><div class="metric-val" style="color:#f87171;">{engine.total_losses}</div></div>
                <div class="metric"><div>Win Rate</div><div class="metric-val">{wr:.1f}%</div></div>
                <div class="metric"><div>Current Win Streak</div><div class="metric-val">{engine.current_win_streak}</div></div>
            </div>
        </div>
    </div>
</body>
</html>"""
                self.wfile.write(html.encode("utf-8"))
            elif self.path in ("/health", "/api/status"):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                payload = {
                    "status": "healthy",
                    "records_loaded": len(engine.dataset),
                    "active_prediction": engine.last_prediction,
                    "confidence": engine.last_pred_conf,
                    "total_wins": engine.total_wins,
                    "total_losses": engine.total_losses
                }
                self.wfile.write(json.dumps(payload, indent=2).encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            return

    server = HTTPServer((CONFIG.http_host, CONFIG.http_port), RequestHandler)
    logger.info(f"🌐 Web Admin & Health API listening on http://{CONFIG.http_host}:{CONFIG.http_port}")
    server.serve_forever()
