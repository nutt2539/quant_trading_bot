import pandas as pd
import numpy as np
import os
import json

STRATEGY_CONFIG_FILE = "strategy_config.json"
CUSTOM_CONFIG_FILE = "custom_strategy_config.json"

DEFAULT_CUSTOM_PARAMS = {
    "alloc_pct": 20.0,
    "tp_pct": 8.0,
    "sl_pct": -3.5,
    "rsi_buy": 35,
    "rsi_sell": 65,
    "ema_fast": 10,
    "ema_slow": 20,
    "ai_min_sentiment": 0.10
}

DEFAULT_SYSTEM_STRATEGIES = {
    "US_INDEX": "TREND_FOLLOWING",
    "GOLD": "MEAN_REVERSION",
    "CRYPTO": "VOLATILITY_BREAKOUT",
    "FOREX": "GRID_TRADING"
}

def get_active_strategy(asset_category: str = "US_INDEX") -> str:
    if os.path.exists(STRATEGY_CONFIG_FILE):
        try:
            with open(STRATEGY_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    if asset_category in data:
                        return data[asset_category]
                    elif "active_strategy" in data:
                        return data["active_strategy"]
        except Exception:
            pass
    return DEFAULT_SYSTEM_STRATEGIES.get(asset_category, "TREND_FOLLOWING")

def set_active_strategy(strategy_key: str, asset_category: str = "US_INDEX"):
    try:
        data = {}
        if os.path.exists(STRATEGY_CONFIG_FILE):
            try:
                with open(STRATEGY_CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        if not isinstance(data, dict):
            data = {}
        data[asset_category] = strategy_key
        data["active_strategy"] = strategy_key
        with open(STRATEGY_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving active strategy: {e}")

def get_all_active_strategies() -> dict:
    res = dict(DEFAULT_SYSTEM_STRATEGIES)
    if os.path.exists(STRATEGY_CONFIG_FILE):
        try:
            with open(STRATEGY_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    for k in res.keys():
                        if k in data:
                            res[k] = data[k]
        except Exception:
            pass
    return res

def get_custom_strategy_params() -> dict:
    if os.path.exists(CUSTOM_CONFIG_FILE):
        try:
            with open(CUSTOM_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                res = DEFAULT_CUSTOM_PARAMS.copy()
                res.update(data)
                return res
        except Exception:
            return DEFAULT_CUSTOM_PARAMS.copy()
    return DEFAULT_CUSTOM_PARAMS.copy()

def save_custom_strategy_params(params: dict):
    try:
        current = get_custom_strategy_params()
        current.update(params)
        with open(CUSTOM_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving custom strategy params: {e}")

STRATEGY_DETAILS = {
    "BALANCED_SWING": {
        "name": "Balanced Swing Trading (เน้นสมดุล ปลอดภัยสูง)",
        "icon": "🛡️",
        "risk_level": "Moderate Risk (ปานกลาง - แนะนำสำหรับมือใหม่)",
        "description": "ย่อซื้อในเทรนด์ขาขึ้น (EMA 10 >= EMA 20 & RSI 35-65) ร่วมกับ Gemini AI Sentiment Score >= +0.10 เน้นความปลอดภัย ป้องกันเงินต้นเป็นหลัก",
        "pros": "<ul style='margin-top:6px;'><li>ความเสี่ยงต่ำ ป้องกันเงินต้นสูง</li><li>ไม่ไล่ราคาตอนสูงเกินไป</li><li>เหมาะสำหรับสภาวะตลาดทั่วไปทุกรูปแบบ</li></ul>",
        "cons": "<ul style='margin-top:6px;'><li>พอร์ตเติบโตแบบค่อยเป็นค่อยไป</li><li>ไม่ได้กำไรหวือหวาในแท่งเดียว</li></ul>"
    },
    "MOMENTUM_BREAKOUT": {
        "name": "Momentum Breakout & Volatility Explosion (พุ่งแรงคำโต)",
        "icon": "🚀",
        "risk_level": "High Risk / High Return (เสี่ยงสูง-กำไรสูง)",
        "description": "เข้าซื้อทันทีเมื่อราคาพุ่งทะลุ High 20 วันเดิม ร่วมกับโวลุ่มการซื้อขายและ ATR พุ่งขึ้น ดักจับต้นเทรนด์ใหญ่ที่กำลังจะวิ่งแรง",
        "pros": "<ul style='margin-top:6px;'><li>จับรอบใหญ่ +30% ถึง +100%+ ในเวลาอันสั้น</li><li>ทำกำไรคำโตจากเทรนด์ขาขึ้นรอบใหม่</li></ul>",
        "cons": "<ul style='margin-top:6px;'><li>เสี่ยงเจอสัญญาณหลอก (False Breakout)</li><li>ต้องมี Trailing Stop คอยตัดขาดทุนเร็ว</li></ul>"
    },
    "CRYPTO_SCALPING": {
        "name": "Crypto & FX Volatility Scalping (สายซิ่ง 24/7)",
        "icon": "⚡",
        "risk_level": "High Risk / High Return (เสี่ยงสูง-ซิ่งเร็ว)",
        "description": "จับจังหวะราคาพุ่ง > 3% ใน 15 นาที ร่วมกับคะแนนข่าว Gemini AI ระดับ Super Bullish (> +0.50) เน้นทำกำไรหลายรอบในคริปโทฯ & ทองคำ",
        "pros": "<ul style='margin-top:6px;'><li>รอบทำกำไรไว ได้หลายรอบต่อวัน</li><li>เหมาะกับตลาด 24/7 ที่ผันผวนสูง</li></ul>",
        "cons": "<ul style='margin-top:6px;'><li>กราฟสะบัดผันผวนสูงมาก</li><li>ต้องตั้ง Stop Loss แคบ</li></ul>"
    },
    "OVERSOLD_REBOUND": {
        "name": "Extreme Oversold Rebound (ช้อนมีดตก / Panic Bounce)",
        "icon": "🌊",
        "risk_level": "High Risk / High Return (เสี่ยงสูง-ต้นทุนถูกสุด)",
        "description": "ดักซื้อเมื่อราคาดิ่งลงแรงเกินสถิติปกติ (RSI < 35) ร่วมกับ MACD เริ่มกลับตัวขึ้น โดย AI ประเมินว่าเป็นการ Panic Sell เกินจริง",
        "pros": "<ul style='margin-top:6px;'><li>ได้ต้นทุนที่ถูกที่สุดใต้ฐานราคา</li><li>เมื่อราคาเด้งกลับจะได้กำไรมหาศาลรวดเร็ว</li></ul>",
        "cons": "<ul style='margin-top:6px;'><li>เสี่ยงรับมีดตก หากเป็นเทรนด์ขาลงยาว</li><li>ต้องคัดเลือกสินทรัพย์พื้นฐานดีเท่านั้น</li></ul>"
    },
    "HIGH_CONVICTION": {
        "name": "High Conviction Pyramiding (อัดเงินหนักในตัวเต็ง)",
        "icon": "💎",
        "risk_level": "High Risk / High Return (เสี่ยงสูง-พอร์ตพุ่งก้าวกระโดด)",
        "description": "เมื่อ AI และเทคนิคอลให้สัญญาณสมบูรณ์แบบสูงสุด (> +0.70) จะอัดวงเงินหนัก 35% ต่อตัว และวางเงินซื้อเพิ่มเมื่อเริ่มได้กำไร (Pyramiding)",
        "pros": "<ul style='margin-top:6px;'><li>พอร์ตเติบโตแบบก้าวกระโดดเมื่อทายถูก</li><li>รีดกำไรสูงสุดจากตัวเต็งประจำเดือน</li></ul>",
        "cons": "<ul style='margin-top:6px;'><li>หากทายผิด พอร์ตจะย่อตัวลงแรงกว่าปกติ</li><li>ต้องการการเฝ้าระวังสูง</li></ul>"
    },
    "CUSTOM": {
        "name": "Custom Strategy (กำหนดค่าด้วยตัวเองแบบอิสระ 100%)",
        "icon": "🛠️",
        "risk_level": "Custom / User-Defined (กำหนดโดยผู้ใช้งาน)",
        "description": "ปรับแต่งวงเงินจัดสรรต่อออเดอร์, เป้าหมายกำไร Take Profit, จุดตัดขาดทุน Stop Loss, ค่า RSI และระดับ AI Sentiment ได้อย่างอิสระตามความต้องการ",
        "pros": "<ul style='margin-top:6px;'><li>ยืดหยุ่นสูงสุด ตอบโจทย์สไตล์การเทรดส่วนตัวได้ 100%</li><li>กำหนด Risk/Reward Ratio และ Money Management ได้เป๊ะตามต้องการ</li></ul>",
        "cons": "<ul style='margin-top:6px;'><li>ผู้ใช้งานต้องทดสอบและปรับแต่งพารามิเตอร์ให้เหมาะสมกับสภาวะตลาด</li></ul>"
    }
}

def generate_swing_trading_signals(df: pd.DataFrame, strategy_key: str = None) -> pd.DataFrame:
    """
    Generates trading signals based on the selected Strategy Key.
    """
    if strategy_key is None:
        strategy_key = get_active_strategy()

    if df.empty:
        df = df.copy()
        df['Signal'] = pd.Series(dtype=int)
        df['Position'] = pd.Series(dtype=int)
        return df

    df = df.copy()
    df['EMA_10'] = df['Close'].ewm(span=10, adjust=False).mean()
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    
    df['High_20'] = df['High'].rolling(window=20).max()
    
    df['Signal'] = 0
    if len(df) < 15:
        df['Position'] = 0
        return df

    if strategy_key == "BALANCED_SWING":
        buy_cond = (
            (df['EMA_10'] >= df['EMA_20']) &
            (df['RSI'] >= 35) & (df['RSI'] <= 65) &
            (df['Close'] >= df['EMA_20'] * 0.985)
        )
        sell_cond = (df['Close'] < df['EMA_20'] * 0.97) | (df['RSI'] >= 70)

    elif strategy_key == "MOMENTUM_BREAKOUT":
        buy_cond = (
            (df['Close'] >= df['High_20'].shift(1)) &
            (df['RSI'] >= 50) & (df['RSI'] <= 75)
        )
        sell_cond = (df['Close'] < df['EMA_10']) | (df['RSI'] >= 78)

    elif strategy_key == "CRYPTO_SCALPING":
        pct_change_15 = df['Close'].pct_change(periods=1) * 100
        buy_cond = (pct_change_15 >= 1.2) & (df['RSI'] <= 70)
        sell_cond = (pct_change_15 <= -1.2) | (df['RSI'] >= 75)

    elif strategy_key == "OVERSOLD_REBOUND":
        buy_cond = (df['RSI'] <= 35) & (df['MACD_Hist'] > df['MACD_Hist'].shift(1))
        sell_cond = (df['RSI'] >= 60) | (df['Close'] > df['EMA_20'])

    elif strategy_key == "HIGH_CONVICTION":
        buy_cond = (df['EMA_10'] > df['EMA_20']) & (df['Close'] > df['EMA_50']) & (df['RSI'] >= 45) & (df['RSI'] <= 68)
        sell_cond = (df['Close'] < df['EMA_20']) | (df['RSI'] >= 72)

    elif strategy_key == "CUSTOM":
        c_params = get_custom_strategy_params()
        rsi_b = c_params.get("rsi_buy", 35)
        rsi_s = c_params.get("rsi_sell", 65)
        ema_f_span = int(c_params.get("ema_fast", 10))
        ema_s_span = int(c_params.get("ema_slow", 20))
        sl_pct_limit = abs(c_params.get("sl_pct", -3.5)) / 100.0
        
        df['EMA_Fast_Custom'] = df['Close'].ewm(span=ema_f_span, adjust=False).mean()
        df['EMA_Slow_Custom'] = df['Close'].ewm(span=ema_s_span, adjust=False).mean()
        
        buy_cond = (df['EMA_Fast_Custom'] >= df['EMA_Slow_Custom']) & (df['RSI'] >= rsi_b) & (df['RSI'] <= rsi_s)
        sell_cond = (df['Close'] < df['EMA_Slow_Custom'] * (1 - sl_pct_limit)) | (df['RSI'] >= rsi_s)

    else:
        buy_cond = (df['EMA_10'] >= df['EMA_20']) & (df['RSI'] >= 35) & (df['RSI'] <= 65)
        sell_cond = (df['Close'] < df['EMA_20'] * 0.97) | (df['RSI'] >= 70)

    df.loc[buy_cond, 'Signal'] = 1
    df.loc[sell_cond, 'Signal'] = -1
    df['Position'] = df['Signal'].replace(0, np.nan).ffill().fillna(0)
    
    return df

def ai_recommend_strategy(symbol: str = "BTC-USD") -> dict:
    """
    Analyzes real-time market volatility (ATR %) and trend metrics to recommend optimal strategy.
    """
    import yfinance as yf
    try:
        df = yf.Ticker(symbol).history(period="1mo")
        if df.empty:
            return {"recommended_key": "BALANCED_SWING", "reason": "สภาวะตลาดปกติ แนะนำใช้กลยุทธ์ Balanced Swing Trading"}
            
        close_p = df['Close'].iloc[-1]
        high_p = df['High'].max()
        low_p = df['Low'].min()
        volatility_pct = ((high_p - low_p) / close_p) * 100
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-9)
        rsi = (100 - (100 / (1 + rs))).iloc[-1]
        
        if rsi <= 35:
            return {
                "recommended_key": "OVERSOLD_REBOUND",
                "reason": f"ตลาดเกิด Panic Sell ลึก (RSI = {rsi:.1f}) แนะนำกลยุทธ์ Extreme Oversold Rebound เพื่อช้อนราคาทุนถูกสุด!"
            }
        elif volatility_pct >= 12.0:
            return {
                "recommended_key": "MOMENTUM_BREAKOUT",
                "reason": f"ตลาดมีความผันผวนสูงมากและเตรียมเกิด Breakout (Volatility = {volatility_pct:.1f}%) แนะนำกลยุทธ์ Momentum Breakout!"
            }
        elif symbol.endswith("-USD") or symbol.endswith("=X"):
            return {
                "recommended_key": "CRYPTO_SCALPING",
                "reason": f"สินทรัพย์ชนิดผันผวนสูง 24/7 แนะนำกลยุทธ์ Crypto & FX Volatility Scalping เพื่อเก็บกำไรหลายรอบ!"
            }
        else:
            return {
                "recommended_key": "BALANCED_SWING",
                "reason": f"สภาวะตลาดทรงตัวสม่ำเสมอ (RSI = {rsi:.1f}) แนะนำกลยุทธ์ Balanced Swing Trading เพื่อความปลอดภัยสูงสุด"
            }
    except Exception as e:
        return {"recommended_key": "BALANCED_SWING", "reason": f"แนะนำใช้กลยุทธ์ Balanced Swing Trading (Error: {e})"}
