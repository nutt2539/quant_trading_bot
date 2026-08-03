"""
MACROECONOMIC & ECONOMIC CALENDAR GUARD
Author: Quant AI Engineering Team
"""

from datetime import datetime, timedelta

# Major Scheduled Global Economic Calendar Events (ICT / Thai Local Time)
# Pre-populated with recurring & key financial calendar windows
MACRO_SCHEDULE = [
    # Format: ("YYYY-MM-DD HH:MM", "Event Name")
    ("2026-08-05 19:30", "🇺🇸 US Non-Farm Payrolls & Unemployment Rate"),
    ("2026-08-12 19:30", "🇺🇸 US CPI Inflation Report"),
    ("2026-08-20 01:00", "🏛️ US Federal Reserve FOMC Rate Decision"),
    ("2026-08-21 14:00", "🇹🇭 BOT Bank of Thailand Monetary Policy"),
    ("2026-09-04 19:30", "🇺🇸 US Non-Farm Payrolls"),
    ("2026-09-16 19:30", "🇺🇸 US CPI Inflation Report"),
    ("2026-09-17 01:00", "🏛️ US Federal Reserve FOMC Rate Decision")
]

BUFFER_BEFORE_MINUTES = 30.0  # Pause 30 mins before major release
BUFFER_AFTER_MINUTES = 15.0   # Pause 15 mins after major release

def is_macro_event_near() -> tuple:
    """
    Checks if a major macroeconomic announcement is currently imminent or underway.
    Returns (is_near: bool, event_name: str, status_msg: str)
    """
    now = datetime.now()
    
    for dt_str, event_name in MACRO_SCHEDULE:
        try:
            event_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            start_window = event_dt - timedelta(minutes=BUFFER_BEFORE_MINUTES)
            end_window = event_dt + timedelta(minutes=BUFFER_AFTER_MINUTES)
            
            if start_window <= now <= end_window:
                diff_mins = (event_dt - now).total_seconds() / 60.0
                if diff_mins > 0:
                    timing_str = f"จะเริ่มในอีก {int(diff_mins)} นาที"
                else:
                    timing_str = f"กำลังประกาศข่าวสารสด"
                    
                msg = f"⚠️ [MACRO GUARD ACTIVATED] {event_name} ({timing_str}) - ชะลอการยิงออเดอร์ใหม่เพื่อหลีกเลี่ยงความผันผวนสูง!"
                return True, event_name, msg
        except Exception:
            continue
            
    return False, "", "ไม่มีข่าวเศรษฐกิจสำคัญในขณะนี้"
