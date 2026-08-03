"""
RENDER FREE CLOUD KEEP-ALIVE PINGER MODULE
Prevents Render Web Service from going to sleep (Spin Down) after 15 minutes of HTTP inactivity.
Author: Quant AI Engineering Team
"""

import threading
import time
import requests

RENDER_APP_URL = "https://quant-trading-bot-wbdu.onrender.com"

def _keep_alive_loop(url: str = RENDER_APP_URL, interval_seconds: int = 600):
    """
    Background thread that sends an HTTP GET request to self every 10 minutes.
    Resets Render 15-minute inactivity timer, keeping container 100% awake 24/7/365.
    """
    time.sleep(15) # Wait 15 seconds after app startup
    print(f"[KEEP-ALIVE] 🚀 Starting Automatic Self-Ping Thread for {url}...", flush=True)
    
    while True:
        try:
            response = requests.get(url, timeout=15)
            print(f"[KEEP-ALIVE PING] Successfully pinged {url} (Status: {response.status_code}) - Container Kept Awake!", flush=True)
        except Exception as e:
            print(f"[KEEP-ALIVE PING] Self-ping warning: {e}", flush=True)
            
        time.sleep(interval_seconds)

def init_keep_alive():
    """
    Launches the keep-alive background thread if not already running.
    """
    if not getattr(init_keep_alive, "_started", False):
        init_keep_alive._started = True
        thread = threading.Thread(target=_keep_alive_loop, daemon=True)
        thread.start()
