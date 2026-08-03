import pandas as pd
import numpy as np

def generate_momentum_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Dual Momentum Strategy (SMA Crossover + MACD + RSI Filter).
    Returns DataFrame with 'Signal' column: 1 (BUY), -1 (SELL), 0 (HOLD).
    """
    if df.empty:
        df = df.copy()
        df['Signal'] = pd.Series(dtype=int)
        df['Position'] = pd.Series(dtype=int)
        return df

    df = df.copy()
    df['Signal'] = 0
    if len(df) < 50:
        df['Position'] = 0
        return df
    
    # Buy condition:
    # 1. Price > SMA_50 and SMA_50 > SMA_200 (Long-term uptrend)
    # 2. MACD > MACD_Signal (Bullish momentum)
    # 3. RSI between 45 and 70 (Healthy momentum, not overbought)
    buy_cond = (
        (df['Close'] > df['SMA_50']) &
        (df['SMA_50'] > df['SMA_200']) &
        (df['MACD'] > df['MACD_Signal']) &
        (df['RSI'] >= 45) & (df['RSI'] <= 70)
    )

    # Sell condition:
    # 1. Price < SMA_50 OR
    # 2. MACD < MACD_Signal OR
    # 3. RSI > 75 (Overbought)
    sell_cond = (
        (df['Close'] < df['SMA_50']) |
        (df['MACD'] < df['MACD_Signal']) |
        (df['RSI'] > 75)
    )

    df.loc[buy_cond, 'Signal'] = 1
    df.loc[sell_cond, 'Signal'] = -1

    # Clean consecutive duplicate signals to show position entries/exits
    df['Position'] = df['Signal'].replace(0, np.nan).ffill().fillna(0)
    
    return df
