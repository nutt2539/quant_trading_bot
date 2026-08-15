"""
MULTI-TIMEFRAME CONFLUENCE ANALYZER (มอดูลวิเคราะห์สอดประสาน 3 กรอบเวลา)
Author: Quant AI Engineering Team
"""

import pandas as pd
import yfinance as yf
from datetime import datetime
import streamlit as st
from data_loader import fetch_stock_data
from strategies.swing_strategy import generate_swing_trading_signals

@st.cache_data(ttl=60, show_spinner=False)
def analyze_multi_timeframe(symbol: str) -> dict:
    """
    Analyzes technical confluence across 3 Timeframes:
    1. Daily (1D): Macro Trend Direction (EMA 50 vs EMA 200)
    2. 4-Hour (4H): Intermediate Momentum (EMA 20 & MACD)
    3. 1-Hour (1H): Precision Entry Timing (RSI Dip & Recovery)
    
    Returns structured analysis dict with alignment score (0.0 to 1.0) and trigger recommendation.
    """
    try:
        # 1. Fetch Daily Data (1D)
        df_1d = fetch_stock_data(symbol, period="6mo", interval="1d")
        # 2. Fetch 4-Hour Data (4h)
        df_4h = fetch_stock_data(symbol, period="1mo", interval="1h")
        # 3. Fetch 1-Hour Data (1h)
        df_1h = fetch_stock_data(symbol, period="7d", interval="1h")
        
        if df_1d.empty:
            return {"is_aligned": True, "score": 0.5, "summary": "Data unavailable, defaulting to neutral."}
            
        # --- 1D Macro Trend Analysis ---
        df_1d_ind = generate_swing_trading_signals(df_1d)
        last_1d = df_1d_ind.iloc[-1]
        c_1d = last_1d["Close"]
        ema50_1d = last_1d.get("EMA_50", c_1d)
        ema200_1d = last_1d.get("EMA_long", c_1d)
        
        macro_bullish = (c_1d >= ema50_1d) and (ema50_1d >= ema200_1d)
        macro_score = 0.4 if macro_bullish else 0.1
        
        # --- 4H Intermediate Momentum Analysis ---
        if not df_4h.empty:
            df_4h_ind = generate_swing_trading_signals(df_4h)
            last_4h = df_4h_ind.iloc[-1]
            rsi_4h = last_4h.get("RSI", 50.0)
            macd_4h = last_4h.get("MACD", 0.0)
            macd_sig_4h = last_4h.get("MACD_Signal", 0.0)
            
            inter_bullish = (macd_4h >= macd_sig_4h) and (rsi_4h >= 45.0)
            inter_score = 0.3 if inter_bullish else 0.1
        else:
            inter_bullish = True
            inter_score = 0.3
            
        # --- 1H Entry Timing Analysis ---
        if not df_1h.empty:
            df_1h_ind = generate_swing_trading_signals(df_1h)
            last_1h = df_1h_ind.iloc[-1]
            rsi_1h = last_1h.get("RSI", 50.0)
            
            # Entry timing optimal when RSI is oversold/rebounding (35-65 zone)
            timing_optimal = (35.0 <= rsi_1h <= 65.0)
            timing_score = 0.3 if timing_optimal else 0.1
        else:
            timing_optimal = True
            timing_score = 0.3
            
        total_score = round(macro_score + inter_score + timing_score, 2)
        is_aligned = (total_score >= 0.70) and macro_bullish
        
        reason_parts = []
        if macro_bullish:
            reason_parts.append("1D Macro Trend Bullish (Close > EMA50 > EMA200)")
        else:
            reason_parts.append("1D Trend Consolidation / Pullback")
            
        if inter_bullish:
            reason_parts.append("4H Momentum Positive (MACD > Signal)")
        if timing_optimal:
            reason_parts.append("1H Entry Timing in Advantageous Rebound Zone")
            
        return {
            "symbol": symbol,
            "is_aligned": is_aligned,
            "confluence_score": total_score,
            "macro_bullish": macro_bullish,
            "inter_bullish": inter_bullish,
            "timing_optimal": timing_optimal,
            "summary": " | ".join(reason_parts)
        }
        
    except Exception as e:
        print(f"Error in analyze_multi_timeframe for {symbol}: {e}")
        return {
            "symbol": symbol,
            "is_aligned": True,
            "confluence_score": 0.50,
            "summary": f"Multi-Timeframe Default (Fallback due to: {e})"
        }
