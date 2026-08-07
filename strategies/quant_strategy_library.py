"""
QUANT STRATEGY LIBRARY (10 SELECTABLE QUANT STRATEGIES)
Author: Quant AI Engineering Team
"""

import pandas as pd
import numpy as np

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes core indicators: EMA12, EMA26, EMA50, RSI, MACD, Bollinger Bands, ATR, Z-Score.
    """
    df = df.copy()
    if df.empty or len(df) < 14:
        return df

    close = df['Close']
    high = df['High']
    low = df['Low']
    
    # EMA
    df['EMA12'] = close.ewm(span=12, adjust=False).mean()
    df['EMA26'] = close.ewm(span=26, adjust=False).mean()
    df['EMA50'] = close.ewm(span=50, adjust=False).mean()
    
    # MACD
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # RSI 14
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    # Bollinger Bands (20, 2.0)
    df['SMA20'] = close.rolling(window=20).mean()
    df['BB_Std'] = close.rolling(window=20).std()
    df['BB_Upper'] = df['SMA20'] + (df['BB_Std'] * 2.0)
    df['BB_Lower'] = df['SMA20'] - (df['BB_Std'] * 2.0)
    
    # Z-Score
    df['Z_Score'] = (close - df['SMA20']) / (df['BB_Std'] + 1e-9)
    
    # ATR
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['ATR'] = tr.ewm(span=14, adjust=False).mean()

    return df

def generate_quant_signal(df: pd.DataFrame, strategy_key: str = "TREND_FOLLOWING", news_sentiment: float = 0.0) -> pd.DataFrame:
    """
    Generates trading signals (Signal = 1 for BUY, -1 for SELL, 0 for HOLD) based on 10 quant strategies.
    """
    df = calculate_indicators(df)
    if df.empty or len(df) < 20:
        df['Signal'] = 0
        return df
        
    df['Signal'] = 0
    close = df['Close']
    rsi = df['RSI']

    # 1. 🕸️ GRID TRADING (Grid Range Capture)
    if strategy_key == "GRID_TRADING":
        sma20 = df['SMA20']
        bb_lower = df['BB_Lower']
        bb_upper = df['BB_Upper']
        # Buy near grid floor (Lower BB), Sell near grid ceiling (Upper BB)
        df.loc[(close <= bb_lower * 1.01) | (rsi < 40), 'Signal'] = 1
        df.loc[(close >= bb_upper * 0.99) | (rsi > 65), 'Signal'] = -1

    # 2. 📈 SIMPLE TREND FOLLOWING (EMA Cross + RSI + MACD)
    elif strategy_key in ["TREND_FOLLOWING", "BALANCED_SWING", "Swing Trading (3-20 Days)"]:
        ema12 = df['EMA12']
        ema26 = df['EMA26']
        macd = df['MACD']
        macd_sig = df['MACD_Signal']
        
        buy_cond = (ema12 > ema26) & (macd > macd_sig) & (rsi >= 42) & (rsi <= 65)
        sell_cond = (ema12 < ema26) | (rsi >= 70) | (macd < macd_sig)
        df.loc[buy_cond, 'Signal'] = 1
        df.loc[sell_cond, 'Signal'] = -1

    # 3. ⏳ DCA & SMART REBALANCING (Dip Accumulation)
    elif strategy_key == "DCA_REBALANCE":
        sma50 = df['EMA50']
        # Triggers Buy on any pullback >= 2% below 50-day average or RSI < 45
        df.loc[(close <= sma50 * 0.98) | (rsi < 45), 'Signal'] = 1
        df.loc[(close >= sma50 * 1.15) | (rsi > 75), 'Signal'] = -1

    # 4. 🔄 MEAN REVERSION (Z-Score & Bollinger Bands)
    elif strategy_key == "MEAN_REVERSION":
        z_score = df['Z_Score']
        # Buy when price drops 1.8 std below mean (oversold rebound)
        df.loc[z_score < -1.8, 'Signal'] = 1
        df.loc[z_score > 1.8, 'Signal'] = -1

    # 5. 💥 VOLATILITY BREAKOUT & MOMENTUM (BB Squeeze + Volume Spike)
    elif strategy_key == "VOLATILITY_BREAKOUT":
        bb_upper = df['BB_Upper']
        bb_lower = df['BB_Lower']
        vol = df['Volume'] if 'Volume' in df.columns else pd.Series(1, index=df.index)
        vol_avg = vol.rolling(20).mean()
        
        # Breakout above Upper BB with Volume support
        df.loc[(close > bb_upper) & (vol >= vol_avg * 1.1), 'Signal'] = 1
        df.loc[close < df['SMA20'], 'Signal'] = -1

    # 6. 🤖 SUPERVISED ML CLASSIFICATION (Feature Ensemble Rule Simulation)
    elif strategy_key in ["SUPERVISED_ML", "HIGH_CONVICTION"]:
        # Multi-factor ML feature voting (EMA slope + RSI + Z-score + Sentiment)
        ema_slope = (df['EMA12'] - df['EMA12'].shift(3)) / df['EMA12'].shift(3)
        ml_score = (ema_slope * 100) + ((rsi - 50) * 0.1) + (news_sentiment * 2.0)
        df.loc[ml_score >= 0.8, 'Signal'] = 1
        df.loc[ml_score <= -0.8, 'Signal'] = -1

    # 7. ⚖️ STATISTICAL ARBITRAGE & PAIRS TRADING (Cointegration Spread)
    elif strategy_key == "STAT_ARBITRAGE":
        # Relative Spread Z-Score
        rel_spread = (close - df['EMA26']) / (df['ATR'] + 1e-9)
        df.loc[rel_spread < -1.5, 'Signal'] = 1
        df.loc[rel_spread > 1.5, 'Signal'] = -1

    # 8. 📰 SENTIMENT ANALYSIS & NLP TRADING (Gemini NLP Driven)
    elif strategy_key in ["NLP_SENTIMENT", "AGGRESSIVE_SCALPER"]:
        # Trades heavily guided by NLP News Sentiment Score
        df.loc[(news_sentiment >= 0.20) & (rsi <= 65), 'Signal'] = 1
        df.loc[(news_sentiment <= -0.20) | (rsi >= 72), 'Signal'] = -1

    # 9. 🧠 REINFORCEMENT LEARNING (RL Agent Reward Optimization)
    elif strategy_key == "REINFORCEMENT_LEARNING":
        # Policy Agent Reward Matrix Simulation
        reward_matrix = (df['MACD'] / (df['ATR'] + 1e-9)) + (news_sentiment * 1.5)
        df.loc[reward_matrix > 0.4, 'Signal'] = 1
        df.loc[reward_matrix < -0.4, 'Signal'] = -1

    # 10. ⚡ HFT & ORDER FLOW ANALYTICS (Order Imbalance Simulation)
    elif strategy_key == "ORDER_FLOW_HFT":
        micro_momentum = (close - close.shift(1)) / (close.shift(1) + 1e-9) * 100
        df.loc[(micro_momentum > 0.15) & (rsi < 68), 'Signal'] = 1
        df.loc[(micro_momentum < -0.15) | (rsi > 70), 'Signal'] = -1

    else: # Fallback Default
        buy_cond = (df['EMA12'] > df['EMA26']) & (rsi >= 45)
        sell_cond = (df['EMA12'] < df['EMA26']) | (rsi >= 70)
        df.loc[buy_cond, 'Signal'] = 1
        df.loc[sell_cond, 'Signal'] = -1

    return df
