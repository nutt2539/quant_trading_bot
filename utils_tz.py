"""
THAILAND ICT TIMEZONE (UTC+7) UTILITY MODULE
Author: Quant AI Engineering Team
"""

from datetime import datetime, timezone, timedelta

# Thailand Standard Timezone (ICT / UTC+7)
THAI_TZ = timezone(timedelta(hours=7))

def get_thai_now() -> datetime:
    """
    Returns current datetime explicitly converted to Thailand ICT (UTC+7).
    Guarantees 100% accurate Thai time regardless of server location or OS timezone.
    """
    return datetime.now(timezone.utc).astimezone(THAI_TZ)

def get_thai_now_naive() -> datetime:
    """
    Returns naive datetime object representing current Thai time (for yfinance / pandas comparisons).
    """
    return get_thai_now().replace(tzinfo=None)

def get_thai_str(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Returns formatted string of current Thailand local time.
    """
    return get_thai_now().strftime(fmt)
