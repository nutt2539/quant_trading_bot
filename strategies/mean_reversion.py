import pandas as pd
import numpy as np

def generate_mean_reversion_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mean Reversion Strategy (Bollinger Bands + Oversold RSI Rebound).
    Returns DataFrame with 'Signal' column: 1 (BUY), -1 (SELL), 0 (HOLD).
    """
    if df.empty:
        df = df.copy()
        df['Signal'] = pd.Series(dtype=int)
        df['Position'] = pd.Series(dtype=int)
        return df

    df = df.copy()
    df['Signal'] = 0
    if len(df) < 20:
        df['Position'] = 0
        return df

    # Buy condition: Price near/below Lower Band AND RSI < 38 (Oversold)
    buy_cond = (df['Close'] <= df['BB_Lower'] * 1.01) & (df['RSI'] <= 38)

    # Sell condition: Price reaches Upper Band OR RSI > 68
    sell_cond = (df['Close'] >= df['BB_Upper'] * 0.99) | (df['RSI'] >= 68)

    df.loc[buy_cond, 'Signal'] = 1
    df.loc[sell_cond, 'Signal'] = -1
    
    df['Position'] = df['Signal'].replace(0, np.nan).ffill().fillna(0)
    return df
