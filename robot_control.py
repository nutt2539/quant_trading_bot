"""
ROBOT CONTROL & FORCE SELL MODULE (ระบบควบคุมสวิตช์ AI และปุ่มสั่งขายฉุกเฉิน)
Author: Quant AI Engineering Team
"""

import os
import json
from datetime import datetime
from execution_engine import send_instant_notification, execute_alpaca_trade
from pnl_tracker import TRADE_LOG_FILE, get_asset_category
from utils_tz import get_thai_str

STATUS_FILE = "autotrader_status.json"

def get_robot_status() -> bool:
    """
    Returns True if AI Robot Auto-Trading is ENABLED (ON), False if DISABLED (OFF).
    Default is True.
    """
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("ai_autotrader_enabled", True)
        except Exception:
            return True
    return True

def set_robot_status(enabled: bool) -> tuple:
    """
    Sets AI Robot Auto-Trading status (True=ON, False=OFF) and notifies Telegram.
    Returns (success: bool, msg: str)
    """
    try:
        data = {"ai_autotrader_enabled": enabled, "updated_at": get_thai_str()}
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        status_text = "🟢 เปิดการทำงาน (ON 24/7)" if enabled else "🔴 ปิดการทำงานชั่วคราว (OFF/PAUSED)"
        telegram_msg = (
            f"{'🟢' if enabled else '🔴'} [AI ROBOT AUTO-TRADING STATUS UPDATED]\n"
            f"สถานะระบบ: {status_text}\n"
            f"เวลาทำรายการ: {data['updated_at']}\n"
            f"หมายเหตุ: {'ระบบพร้อมสแกนและส่งคำสั่งเทรดอัตโนมัติ 24/7' if enabled else 'ระงับการสแกนและยิงออเดอร์อัตโนมัติทุกชนิด'}"
        )
        send_instant_notification(telegram_msg)
        return True, f"สลับสถานะ AI Robot เป็น {status_text} สำเร็จ และแจ้งเตือน Telegram เรียบร้อยแล้ว!"
    except Exception as e:
        return False, f"เกิดข้อผิดพลาดในการเปลี่ยนสถานะ: {e}"

def execute_force_sell(symbol: str, shares: float, current_price: float, fx_rate: float = 1.0) -> tuple:
    """
    Executes an immediate Force Sell (Market Sell) for a specific held asset position.
    Notifies Telegram instantly with full execution summary.
    Returns (success: bool, msg: str)
    """
    try:
        now_str = get_thai_str()
        total_thb = round(shares * current_price * fx_rate, 2)
        category = get_asset_category(symbol)
        display_sym = "GOLD (ทองคำ)" if symbol in ["GC=F", "XAUUSD=X"] else symbol.replace("-USD", "").replace("=X", "")
        
        # 1. Execute Alpaca API if US Index / Gold / Forex
        if category in ["US_INDEX", "GOLD", "FOREX", "US_STOCK"]:
            res = execute_alpaca_trade(symbol, qty=shares, side="sell")
            alpaca_status = res.get('status', 'executed')
        else:
            alpaca_status = 'executed'
            
        # 2. Record Trade Log in autotrade_logs.json
        logs = []
        if os.path.exists(TRADE_LOG_FILE):
            try:
                with open(TRADE_LOG_FILE, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            except Exception:
                logs = []
                
        log_entry = {
            "timestamp": now_str,
            "symbol": symbol,
            "action": "SELL",
            "shares": shares,
            "price": round(current_price, 2),
            "total_thb": total_thb,
            "reason": "🚨 Force Sell (บังคับขายฉุกเฉินผ่าน Dashboard)",
            "ai_summary": f"ผู้ใช้กดปุ่มสั่งขายฉุกเฉิน (Force Sell) สำหรับ {symbol} จำนวน {shares} หน่วย ในราคา ฿{current_price:,.2f}",
            "status": alpaca_status
        }
        logs.insert(0, log_entry)
        
        with open(TRADE_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
            
        # 3. Send Instant Telegram Notification
        msg = (
            f"🚨 [FORCE SELL - สั่งขายฉุกเฉินสำเร็จ]\n"
            f"-----------------------------------\n"
            f"📌 สินทรัพย์: {display_sym} ({symbol})\n"
            f"📦 จำนวนที่ขาย: {shares} หน่วย\n"
            f"💵 ราคาที่ขาย: ฿{current_price:,.2f}\n"
            f"💰 มูลค่ารวม: ฿{total_thb:,.2f}\n"
            f"⏰ เวลาทำรายการ: {now_str}\n"
            f"👤 ดำเนินการโดย: คำสั่งบังคับขายจากผู้ใช้ผ่าน Dashboard"
        )
        send_instant_notification(msg)
        
        return True, f"สั่งบังคับขาย {display_sym} จำนวน {shares} หน่วย เรียบร้อยแล้ว! (แจ้งเตือน Telegram แล้ว)"
        
    except Exception as e:
        return False, f"เกิดข้อผิดพลาดในการบังคับขาย {symbol}: {e}"
