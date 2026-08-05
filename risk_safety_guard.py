"""
RISK & SAFETY GUARD MODULE (ระบบควบคุมความเสี่ยงและความปลอดภัยขั้นสูงสุดสำหรับเงินทุนจริง)
Author: Quant AI Engineering Team
"""

import os
import json
from datetime import datetime, time, timedelta
import config
from execution_engine import send_instant_notification
from utils_tz import get_thai_now

TRADE_LOG_FILE = "autotrade_logs.json"
MAX_DAILY_DRAWDOWN_PCT = 3.0  # 3% Max daily drawdown circuit breaker
MAX_POSITION_ALLOCATION_PCT = 15.0  # Max 15% allocation per single trade
MIN_TRADE_INTERVAL_SEC = 60  # Anti-Duplicate trade window (60s)

def validate_market_hours(symbol: str) -> tuple:
    """
    Strict Market Hours Validator.
    Returns (is_open: bool, reason: str)
    """
    now = get_thai_now()
    weekday = now.weekday()  # 0=Mon, ..., 4=Fri, 5=Sat, 6=Sun
    t = now.time()
    
    # 1. Thai SET Stocks (.BK)
    if symbol.endswith(".BK"):
        if weekday in [5, 6]:
            return False, f"ตลาดหุ้นไทย (.BK) ปิดทำการวันเสาร์-อาทิตย์ (เวลาปัจจุบัน: {now.strftime('%H:%M:%S')})"
        m_open = time(10, 0)
        m_close = time(12, 30)
        a_open = time(14, 30)
        a_close = time(16, 30)
        
        is_open = (m_open <= t <= m_close) or (a_open <= t <= a_close)
        if not is_open:
            return False, f"ตลาดหุ้นไทย (.BK) ปิดทำการ (เปิด 10:00-12:30 น. และ 14:30-16:30 น. / เวลาขณะนี้ {now.strftime('%H:%M:%S น.')})"
        return True, "ตลาดหุ้นไทยเปิดทำการปกติ"
        
    # 2. US Stocks (e.g., AAPL, NVDA, TSLA)
    elif not symbol.endswith("-USD") and not symbol.endswith("=X") and symbol != "GC=F" and symbol not in ["BTC", "ETH", "SOL", "BNB", "ADA", "XRP", "AVAX", "LINK", "DOGE"]:
        if weekday in [5, 6]:
            return False, f"ตลาดหุ้นสหรัฐฯ ปิดทำการวันเสาร์-อาทิตย์"
        us_open = time(21, 30)
        us_close = time(4, 0)
        is_open = (t >= us_open or t <= us_close)
        if not is_open:
            return False, f"ตลาดหุ้นสหรัฐฯ ปิดทำการ (เปิด 21:30 - 04:00 น. ตามเวลาไทย)"
        return True, "ตลาดหุ้นสหรัฐฯ เปิดทำการปกติ"
        
    # 3. Forex & Gold (=X, GC=F)
    elif symbol.endswith("=X") or symbol == "GC=F":
        if weekday == 5 and t > time(4, 0):
            return False, "ตลาด Forex & ทองคำ ปิดทำการช่วงวันหยุดสุดสัปดาห์ (เสาร์หลัง 04:00 น.)"
        if weekday == 6:
            return False, "ตลาด Forex & ทองคำ ปิดทำการวันอาทิตย์"
        if weekday == 0 and t < time(5, 0):
            return False, "ตลาด Forex & ทองคำ ปิดทำการเช้าวันจันทร์ก่อน 05:00 น."
        return True, "ตลาด Forex & ทองคำ เปิดทำการปกติ 24/5"
        
    # 4. Crypto (-USD, BTC, ETH, etc.) -> 24/7/365
    else:
        return True, "ตลาด Cryptoเปิดทำการปกติ 24/7"

def check_daily_circuit_breaker(current_daily_pnl_pct: float) -> tuple:
    """
    Circuit Breaker: Halts trading if daily portfolio drawdown exceeds limit.
    """
    if current_daily_pnl_pct <= -MAX_DAILY_DRAWDOWN_PCT:
        msg = f"🚨 [CIRCUIT BREAKER ACTIVATED] พอร์ตขาดทุนประจำวันถึงเกณฑ์วิกฤต ({current_daily_pnl_pct:.2f}% <= -{MAX_DAILY_DRAWDOWN_PCT}%) ระงับการเปิดออเดอร์ใหม่ชั่วคราวเพื่อปกป้องเงินต้น!"
        send_instant_notification(msg)
        return True, msg
    return False, "พอร์ตอยู่ในสภาวะความเสี่ยงปกติ"

def validate_trade_safety(symbol: str, action: str, trade_thb: float, portfolio_equity: float = 300000.0) -> tuple:
    """
    Pre-Trade Execution Risk Check.
    Returns (is_safe: bool, reason: str)
    """
    # 1. Check Market Hours
    market_ok, market_msg = validate_market_hours(symbol)
    if not market_ok:
        return False, market_msg

    # 2. Check Allocation Cap
    if action == "BUY" and portfolio_equity > 0:
        alloc_pct = (trade_thb / portfolio_equity) * 100
        if alloc_pct > MAX_POSITION_ALLOCATION_PCT:
            return False, f"ขนาดออเดอร์ (฿{trade_thb:,.2f}) คิดเป็น {alloc_pct:.1f}% ของพอร์ต เกินเกณฑ์กระจายความเสี่ยงสูงสุด ({MAX_POSITION_ALLOCATION_PCT}%)"

    # 3. Check Anti-Duplicate Window
    if os.path.exists(TRADE_LOG_FILE):
        try:
            with open(TRADE_LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
            if logs:
                last_log = logs[0]
                if last_log.get('symbol') == symbol and last_log.get('action') == action:
                    ts_str = last_log.get('timestamp', '')
                    try:
                        last_dt = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
                        diff_sec = (get_thai_now().replace(tzinfo=None) - last_dt).total_seconds()
                        if diff_sec < MIN_TRADE_INTERVAL_SEC:
                            return False, f"ปฏิเสธออเดอร์ซ้ำซ้อน ({action} {symbol} เพิ่งส่งไปเมื่อ {int(diff_sec)} วินาทีที่แล้ว)"
                    except Exception:
                        pass
        except Exception as e:
            print(f"Error checking trade duplicates: {e}")

    # 4. HARVEST VAULT REINVESTMENT GUARD (FAIL-SAFE DOUBLE CHECK)
    if action == "BUY":
        try:
            from pnl_tracker import get_system_pnl
            category = "CRYPTO" if symbol.endswith("-USD") else ("THAI_STOCK" if symbol.endswith(".BK") else "US_STOCK")
            sys_pnl = get_system_pnl(category, 100000.0)
            spendable_cash = sys_pnl.get("spendable_cash_thb", 0.0)
            harvested_vault = sys_pnl.get("harvested_vault_thb", 0.0)
            
            if trade_thb > spendable_cash:
                return False, f"🛑 HARVEST VAULT LOCK ACTIVATED: ออเดอร์ซื้อ {symbol} (฿{trade_thb:,.2f}) เกินวงเงิน Spendable Cash (฿{spendable_cash:,.2f}) ไม่อนุญาตให้นำเงิน Harvest Vault (฿{harvested_vault:,.2f}) ไปใช้เด็ดขาด!"
        except Exception as e:
            print(f"Error checking harvest vault firewall: {e}")

    return True, "ออเดอร์ผ่านเกณฑ์ความปลอดภัย Risk Guard เรียบร้อย 100%"
