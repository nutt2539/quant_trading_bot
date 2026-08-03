"""
MASTER BROKER MANAGER & ENVIRONMENT SWITCHER
Author: Quant AI Engineering Team
"""

import os
import json
from broker_bridge.alpaca_broker import AlpacaLiveBroker
from broker_bridge.settrade_broker import SettradeBrokerAdapter
from broker_bridge.bitkub_broker import BitkubBrokerAdapter
from broker_bridge.mt5_broker import MT5BrokerAdapter

CONFIG_FILE = "broker_config.json"

DEFAULT_CONFIG = {
    "broker_mode": "PAPER",  # Options: "PAPER" or "LIVE"
    "active_stock_broker": "SETTRADE",
    "active_crypto_broker": "BITKUB",
    "active_forex_broker": "MT5"
}

def load_broker_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = DEFAULT_CONFIG.copy()
                cfg.update(json.load(f))
                return cfg
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def save_broker_config(cfg: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving broker config: {e}")

def get_broker_mode() -> str:
    """
    Returns current Broker Mode: 'PAPER' (Simulated) or 'LIVE' (Real Broker API).
    """
    cfg = load_broker_config()
    return cfg.get("broker_mode", "PAPER")

def set_broker_mode(mode: str) -> tuple:
    """
    Switches Master Broker Mode ('PAPER' vs 'LIVE').
    Returns (success: bool, msg: str)
    """
    clean_mode = mode.upper().strip()
    if clean_mode not in ["PAPER", "LIVE"]:
        return False, "โหมด Broker ต้องเป็น 'PAPER' หรือ 'LIVE' เท่านั้น"
        
    cfg = load_broker_config()
    cfg["broker_mode"] = clean_mode
    save_broker_config(cfg)
    
    from execution_engine import send_instant_notification
    status_text = "🟢 โหมดเงินจริงผ่าน Broker API (LIVE BROKER MODE)" if clean_mode == "LIVE" else "📝 โหมดจำลองกระดาษ (PAPER TRADING MODE)"
    msg = (
        f"⚙️ [BROKER ENVIRONMENT MODE SWITCHED]\n"
        f"โหมดปัจจุบัน: {status_text}\n"
        f"เวลาปรับเปลี่ยน: {os.path.basename(CONFIG_FILE)}\n"
        f"หมายเหตุ: {'ระบบจะดึงข้อมูลราคา เงินสด พอร์ตถือครอง และยิงออเดอร์ตรงเข้า Broker API จริง 100%' if clean_mode == 'LIVE' else 'ระบบจะรันในโหมดจำลองพอร์ตกระดาษ Paper Trading'}"
    )
    send_instant_notification(msg)
    return True, f"สลับโหมดเป็น {status_text} เรียบร้อยแล้ว (แจ้งเตือน Telegram แล้ว)"

def get_broker_adapter(system_category: str):
    """
    Returns live broker adapter instance for the target system category ('STOCK', 'CRYPTO', 'FOREX').
    """
    sys_cat = system_category.upper().strip()
    cfg = load_broker_config()
    
    if sys_cat == "STOCK":
        if cfg.get("active_stock_broker") == "ALPACA":
            return AlpacaLiveBroker()
        else:
            return SettradeBrokerAdapter()
    elif sys_cat == "CRYPTO":
        return BitkubBrokerAdapter()
    else:
        return MT5BrokerAdapter()
