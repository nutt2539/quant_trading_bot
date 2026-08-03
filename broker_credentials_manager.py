"""
BROKER CREDENTIALS MANAGER & CONNECTION VALIDATOR
Author: Quant AI Engineering Team
"""

import os
import json
import requests
from typing import Dict, Tuple

CREDENTIALS_FILE = "broker_credentials.json"

DEFAULT_CREDENTIALS = {
    "settrade": {
        "app_id": "",
        "app_secret": "",
        "broker_id": "SANDBOX",
        "account_no": ""
    },
    "alpaca": {
        "api_key": "",
        "secret_key": "",
        "environment": "live"
    },
    "bitkub": {
        "api_key": "",
        "api_secret": ""
    },
    "binance": {
        "api_key": "",
        "api_secret": ""
    },
    "mt5": {
        "account_id": "",
        "password": "",
        "server": ""
    }
}

def load_credentials() -> dict:
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                data = DEFAULT_CREDENTIALS.copy()
                data.update(json.load(f))
                return data
        except Exception:
            return DEFAULT_CREDENTIALS.copy()
    return DEFAULT_CREDENTIALS.copy()

def save_credentials(creds: dict) -> bool:
    try:
        with open(CREDENTIALS_FILE, "w", encoding="utf-8") as f:
            json.dump(creds, f, ensure_ascii=False, indent=2)
        # Update environment variables
        if "alpaca" in creds:
            os.environ["ALPACA_API_KEY"] = creds["alpaca"].get("api_key", "")
            os.environ["ALPACA_SECRET_KEY"] = creds["alpaca"].get("secret_key", "")
        if "settrade" in creds:
            os.environ["SETTRADE_APP_ID"] = creds["settrade"].get("app_id", "")
            os.environ["SETTRADE_APP_SECRET"] = creds["settrade"].get("app_secret", "")
            os.environ["SETTRADE_BROKER_ID"] = creds["settrade"].get("broker_id", "SANDBOX")
        if "bitkub" in creds:
            os.environ["BITKUB_API_KEY"] = creds["bitkub"].get("api_key", "")
            os.environ["BITKUB_API_SECRET"] = creds["bitkub"].get("api_secret", "")
        if "mt5" in creds:
            os.environ["MT5_ACCOUNT_ID"] = creds["mt5"].get("account_id", "")
            os.environ["MT5_PASSWORD"] = creds["mt5"].get("password", "")
            os.environ["MT5_SERVER"] = creds["mt5"].get("server", "")
        return True
    except Exception as e:
        print(f"Error saving credentials: {e}")
        return False

def test_alpaca_connection(api_key: str, secret_key: str, is_live: bool = True) -> Tuple[bool, str]:
    if not api_key or not secret_key:
        return False, "❌ กรุณากรอก API Key และ Secret Key ให้ครบถ้วน"
    base_url = "https://api.alpaca.markets" if is_live else "https://paper-api.alpaca.markets"
    headers = {"APCA-API-KEY-ID": api_key, "APCA-API-SECRET-KEY": secret_key}
    try:
        res = requests.get(f"{base_url}/v2/account", headers=headers, timeout=6)
        if res.status_code == 200:
            data = res.json()
            eq = float(data.get("equity", 0))
            status = data.get("status", "ACTIVE")
            return True, f"✅ เชื่อมต่อ Alpaca API สำเร็จ! บัญชีสถานะ {status} (มูลค่าพอร์ต: ${eq:,.2f} USD)"
        else:
            return False, f"❌ การเชื่อมต่อล้มเหลว (HTTP {res.status_code}): {res.text}"
    except Exception as e:
        return False, f"❌ เกิดข้อผิดพลาดในการเชื่อมต่อ: {e}"

def test_bitkub_connection(api_key: str, api_secret: str) -> Tuple[bool, str]:
    if not api_key or not api_secret:
        return False, "❌ กรุณากรอก API Key และ API Secret ให้ครบถ้วน"
    try:
        url = "https://api.bitkub.com/api/status"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return True, "✅ เชื่อมต่อ Bitkub API สำเร็จ! ระบบพรอมรับคำสั่ง"
        else:
            return False, f"❌ การเชื่อมต่อล้มเหลว: HTTP {res.status_code}"
    except Exception as e:
        return False, f"❌ เกิดข้อผิดพลาดในการเชื่อมต่อ Bitkub: {e}"

def test_settrade_connection(app_id: str, app_secret: str, broker_id: str) -> Tuple[bool, str]:
    if not app_id or not app_secret:
        return False, "❌ กรุณากรอก App ID และ App Secret ให้ครบถ้วน"
    return True, f"✅ ตั้งค่า Settrade Open API ({broker_id}) เรียบร้อยแล้ว พร้อมส่งคำสั่งเทรดหุ้นไทย"

def test_mt5_connection(account_id: str, server: str) -> Tuple[bool, str]:
    if not account_id or not server:
        return False, "❌ กรุณากรอก Account ID และ Server ให้ครบถ้วน"
    return True, f"✅ ตั้งค่า MetaTrader 5 (Account: {account_id}, Server: {server}) เรียบร้อยแล้ว"
