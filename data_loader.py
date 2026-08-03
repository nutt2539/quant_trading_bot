import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st

@st.cache_data(ttl=60, show_spinner=False)
def fetch_stock_data(symbol: str, period: str = "2y", interval: str = "1d") -> pd.DataFrame:
    """
    Fetch historical OHLCV data for a given stock symbol using yfinance.
    Calculates technical indicators: SMA_20, SMA_50, SMA_200, RSI, MACD, Bollinger Bands.
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            return pd.DataFrame()
        
        # Clean column names
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
        
        # Technical Indicators
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        
        # RSI (14)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD (12, 26, 9)
        ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema_26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = ema_12 - ema_26
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        
        # Bollinger Bands (20, 2)
        df['BB_Middle'] = df['SMA_20']
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        
        # ATR (Average True Range 14)
        tr1 = df['High'] - df['Low']
        tr2 = (df['High'] - df['Close'].shift()).abs()
        tr3 = (df['Low'] - df['Close'].shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['ATR'] = tr.rolling(window=14).mean()

        df.dropna(inplace=False)
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

def fetch_stock_info(symbol: str) -> dict:
    """
    Fetch fundamental metadata for a stock (PE, ROE, Div Yield, Market Cap, Sector).
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return {
            'symbol': symbol,
            'name': info.get('shortName', symbol),
            'sector': info.get('sector', 'N/A'),
            'pe_ratio': info.get('trailingPE', None),
            'forward_pe': info.get('forwardPE', None),
            'roe': info.get('returnOnEquity', None),
            'dividend_yield': info.get('dividendYield', None),
            'market_cap': info.get('marketCap', None),
            'price': info.get('regularMarketPrice', info.get('currentPrice', None)),
            'currency': info.get('currency', 'USD')
        }
    except Exception as e:
        print(f"Error fetching info for {symbol}: {e}")
        return {'symbol': symbol, 'name': symbol, 'sector': 'N/A'}
