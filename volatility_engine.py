"""
ADAPTIVE VOLATILITY & DYNAMIC ATR TRAILING STOP ENGINE
Author: Quant AI Engineering Team
"""

import pandas as pd
import numpy as np

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculates Average True Range (ATR 14).
    """
    if df.empty or len(df) < 2:
        return pd.Series([0.0] * len(df))
        
    high = df['High']
    low = df['Low']
    close_prev = df['Close'].shift(1)
    
    tr1 = high - low
    tr2 = (high - close_prev).abs()
    tr3 = (low - close_prev).abs()
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(span=period, adjust=False).mean()
    return atr

def get_dynamic_tp_sl(entry_price: float, atr_value: float, base_tp_pct: float = 8.0, base_sl_pct: float = -3.5) -> dict:
    """
    Calculates dynamic Take Profit & Stop Loss targets based on ATR market volatility.
    - High Volatility: Expands TP target to ride strong trend.
    - Low Volatility: Tightens TP/SL to capture quick gains safely.
    """
    if entry_price <= 0 or atr_value <= 0:
        return {
            "tp_price": round(entry_price * (1 + base_tp_pct/100.0), 2),
            "sl_price": round(entry_price * (1 + base_sl_pct/100.0), 2),
            "tp_pct": base_tp_pct,
            "sl_pct": base_sl_pct,
            "atr_used": 0.0
        }
        
    # Dynamic ATR Multipliers: TP = 3.0x ATR, SL = 1.5x ATR
    tp_distance = 3.0 * atr_value
    sl_distance = 1.5 * atr_value
    
    dynamic_tp_price = entry_price + tp_distance
    dynamic_sl_price = entry_price - sl_distance
    
    dynamic_tp_pct = round(((dynamic_tp_price - entry_price) / entry_price) * 100.0, 2)
    dynamic_sl_pct = round(((dynamic_sl_price - entry_price) / entry_price) * 100.0, 2)
    
    # Bound thresholds for safety (Min 3% TP, Max 25% TP; Min -2% SL, Max -7% SL)
    final_tp_pct = max(3.0, min(25.0, dynamic_tp_pct))
    final_sl_pct = min(-2.0, max(-7.0, dynamic_sl_pct))
    
    return {
        "tp_price": round(entry_price * (1 + final_tp_pct/100.0), 4),
        "sl_price": round(entry_price * (1 + final_sl_pct/100.0), 4),
        "tp_pct": final_tp_pct,
        "sl_pct": final_sl_pct,
        "atr_used": round(atr_value, 4)
    }

def update_trailing_stop(current_price: float, highest_price: float, atr_value: float, multiplier: float = 2.0) -> float:
    """
    Calculates dynamic Trailing Stop price level.
    Trailing Stop locks in profits as price climbs higher.
    """
    if highest_price <= 0 or atr_value <= 0:
        return round(current_price * 0.95, 4) # Default 5% trailing fallback
        
    trailing_level = highest_price - (multiplier * atr_value)
    return round(max(trailing_level, current_price * 0.90), 4)
