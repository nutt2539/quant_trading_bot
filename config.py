import os
from dotenv import load_dotenv

load_dotenv()

# Portfolio Allocation Config (Total 300,000 THB)
TOTAL_CAPITAL_THB = 300000

# 4 Asset Systems Allocations
US_INDEX_ALLOCATION_THB = 100000  # 40% (฿100,000)
GOLD_ALLOCATION_THB = 90000       # 30% (฿90,000)
CRYPTO_ALLOCATION_THB = 80000     # 20% (฿80,000)
FOREX_ALLOCATION_THB = 30000      # 10% (฿30,000)

SYSTEM_ALLOCATIONS = {
    "US_INDEX": US_INDEX_ALLOCATION_THB,
    "GOLD": GOLD_ALLOCATION_THB,
    "CRYPTO": CRYPTO_ALLOCATION_THB,
    "FOREX": FOREX_ALLOCATION_THB
}

SYSTEM_LABELS = {
    "US_INDEX": "🇺🇸 ดัชนีหุ้นสหรัฐฯ (S&P 500 / NASDAQ / Dow Jones)",
    "GOLD": "🥇 บอททองคำ (Gold / XAUUSD)",
    "CRYPTO": "🪙 บอท Crypto Spot (24/7)",
    "FOREX": "💱 บอท Forex (24/5)"
}

# API Keys (Loaded from environment variables or .env)
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "YOUR_ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "YOUR_ALPACA_SECRET_KEY")
ALPACA_PAPER_BASE_URL = "https://paper-api.alpaca.markets"

LINE_NOTIFY_TOKEN = os.getenv("LINE_NOTIFY_TOKEN", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

def update_line_token(token: str):
    global LINE_NOTIFY_TOKEN
    LINE_NOTIFY_TOKEN = token.strip()
    os.environ["LINE_NOTIFY_TOKEN"] = token.strip()
    env_content = f"LINE_NOTIFY_TOKEN={token.strip()}\nGEMINI_API_KEY={GEMINI_API_KEY}\n"
    with open(".env", "w", encoding="utf-8") as f:
        f.write(env_content)
    return True

def update_telegram_config(bot_token: str, chat_id: str):
    global TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    TELEGRAM_BOT_TOKEN = bot_token.strip()
    TELEGRAM_CHAT_ID = chat_id.strip()
    os.environ["TELEGRAM_BOT_TOKEN"] = bot_token.strip()
    os.environ["TELEGRAM_CHAT_ID"] = chat_id.strip()
    with open(".env", "w", encoding="utf-8") as f:
        f.write(f"TELEGRAM_BOT_TOKEN={bot_token.strip()}\nTELEGRAM_CHAT_ID={chat_id.strip()}\nDISCORD_WEBHOOK_URL={DISCORD_WEBHOOK_URL}\n")
    return True

def update_discord_config(webhook_url: str):
    global DISCORD_WEBHOOK_URL
    DISCORD_WEBHOOK_URL = webhook_url.strip()
    os.environ["DISCORD_WEBHOOK_URL"] = webhook_url.strip()
    with open(".env", "w", encoding="utf-8") as f:
        f.write(f"TELEGRAM_BOT_TOKEN={TELEGRAM_BOT_TOKEN}\nTELEGRAM_CHAT_ID={TELEGRAM_CHAT_ID}\nDISCORD_WEBHOOK_URL={webhook_url.strip()}\n")
    return True

# 4 Asset Watchlists Universes
US_INDEX_WATCHLIST = [
    "SPY", "QQQ", "DIA", "AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "AMD"
]

GOLD_WATCHLIST = [
    "GC=F", "XAUUSD=X", "GLD", "IAU"
]

CRYPTO_WATCHLIST = [
    "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "DOGE-USD", "ADA-USD", "AVAX-USD", "LINK-USD"
]

FOREX_WATCHLIST = [
    "EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X", "USDCHF=X"
]

# Legacy compatibility
US_WATCHLIST = US_INDEX_WATCHLIST
THAI_WATCHLIST = [] # Replaced by 4 systems structure

SYSTEM_WATCHLISTS = {
    "US_INDEX": US_INDEX_WATCHLIST,
    "GOLD": GOLD_WATCHLIST,
    "CRYPTO": CRYPTO_WATCHLIST,
    "FOREX": FOREX_WATCHLIST
}

# 10 Selectable Quant Strategies (Grouped in 3 Levels)
STRATEGY_CATALOG = {
    # 🟢 2.1 Beginner Level (Rule-Based)
    "GRID_TRADING": {
        "level": "BEGINNER",
        "level_label": "🟢 ระดับเริ่มต้น (Beginner)",
        "name": "Grid Trading (การวางตาข่ายซื้อขาย)",
        "icon": "🕸️",
        "risk_level": "ต่ำ (Low Risk - Sideway Market)",
        "desc": "วางคำสั่งซื้อ-ขายเป็นช่วงตาข่าย (Grid) ตามกรอบราคาเพื่อทำกำไรจากแกว่งตัวแคบ (Sideway)",
        "pros": "ทำกำไรสม่ำเสมอในสภาวะตลาดไซด์เวย์ ไม่ต้องคาดเดาทิศทางตลาดสด",
        "cons": "หากราคาเกิดเทรนด์หลุดกรอบตาข่ายลงแรง อาจติดดอยสะสมตำแหน่งหลายชั้น"
    },
    "TREND_FOLLOWING": {
        "level": "BEGINNER",
        "level_label": "🟢 ระดับเริ่มต้น (Beginner)",
        "name": "Simple Trend Following (กลยุทธ์ตามเทรนด์ด้วย EMA/RSI/MACD)",
        "icon": "📈",
        "risk_level": "ปานกลาง (Moderate Risk)",
        "desc": "เกาะเทรนด์ใหญ่ด้วยสัญญาณ EMA Cross, RSI Momentum และ MACD Rebound",
        "pros": "รันเทรนด์ได้กำไรคำโตเมื่อตลาดเป็นเทรนด์ชัดเจน ตัดขาดทุนตามวินัยรวดเร็ว",
        "cons": "อาจเกิดสัญญาณหลอก (Whipsaw) ในช่วงตลาดแกว่งตัวผันผวนไม่มีทิศทาง"
    },
    "DCA_REBALANCE": {
        "level": "BEGINNER",
        "level_label": "🟢 ระดับเริ่มต้น (Beginner)",
        "name": "DCA Bot & Smart Rebalancing (ทยอยสะสมถัวเฉลี่ย)",
        "icon": "💰",
        "risk_level": "ต่ำมาก (Very Low Risk - Capital Saver)",
        "desc": "ทยอยสะสมสินทรัพย์ตามเปอร์เซ็นต์ย่อตัวและปรับพอร์ตถัวเฉลี่ยอัตโนมัติ",
        "pros": "ลดความเสี่ยงจากการเข้าซื้อผิดจังหวะ เหมาะสำหรับสะสมพอร์ตระยะยาว",
        "cons": "ผลตอบแทนอาจไม่หวือหวาเท่ากลยุทธ์ตามเทรนด์แรงๆ ในระยะสั้น"
    },
    # 🟡 2.2 Intermediate Level (Statistics & ML)
    "MEAN_REVERSION": {
        "level": "INTERMEDIATE",
        "level_label": "🟡 ระดับปานกลาง (Intermediate)",
        "name": "Mean Reversion (การย้อนกลับสู่ค่าเฉลี่ย)",
        "icon": "⚖️",
        "risk_level": "ปานกลาง (Moderate Risk)",
        "desc": "ใช้สถิติ Z-Score & Bollinger Bands คำนวณจุดหลุดเบี่ยงเบนเพื่อเทรดสวนทางกลับเข้าหาศูนย์กลาง",
        "pros": "อัตราการชนะ (Win Rate) สูง มีจุดเข้าซื้อที่ชัดเจนตามสถิติเบี่ยงเบน",
        "cons": "หากราคาทะลุแนวรับ/แนวต้านเปิดเทรนด์แรง อาจเข้าซื้อสวนเทรนด์ต่อเนื่อง"
    },
    "VOLATILITY_BREAKOUT": {
        "level": "INTERMEDIATE",
        "level_label": "🟡 ระดับปานกลาง (Intermediate)",
        "name": "Volatility Breakout & Momentum (การทะลุกรอบความผันผวน)",
        "icon": "💥",
        "risk_level": "ปานกลาง-สูง (Med-High Risk)",
        "desc": "ตรวจจับกรอบแคบ (Squeeze) และยิงออเดอร์เมื่อเกิดแรงซื้อทะลุ Volume ผิดปกติ",
        "pros": "เข้าซื้อตอนต้นเทรนด์ได้อย่างรวดเร็ว ทำกำไรตามแรงระเบิดของราคาได้ดี",
        "cons": "ต้องมีวินัย Stop Loss ที่เด็ดขาดเมื่อเกิดการ Breakout หลอก (False Breakout)"
    },
    "SUPERVISED_ML": {
        "level": "INTERMEDIATE",
        "level_label": "🟡 ระดับปานกลาง (Intermediate)",
        "name": "Supervised ML Classification (โมเดล Random Forest/XGBoost)",
        "icon": "🤖",
        "risk_level": "ปานกลาง (Quant Model Risk)",
        "desc": "ใช้โมเดล Machine Learning จำแนกสภาวะตลาดและทายผลลัพธ์ทิศทางแท่งถัดไป",
        "pros": "วิเคราะห์อินดิเคเตอร์หลายมิติพร้อมกันได้อย่างแม่นยำ ปรับตัวตามฟีเจอร์ใหม่",
        "cons": "ต้องคอย Retrain โมเดลเป็นระยะเพื่อป้องกันปัญหา Model Overfitting"
    },
    # 🔴 2.3 Professional Level (Quant Funds & Deep AI)
    "STAT_ARBITRAGE": {
        "level": "PROFESSIONAL",
        "level_label": "🔴 ระดับมืออาชีพ (Professional Quant)",
        "name": "Statistical Arbitrage & Pairs Trading (สถิติอนุพันธ์คู่สินทรัพย์)",
        "icon": "📊",
        "risk_level": "ปานกลาง-ต่ำ (Market Neutral)",
        "desc": "หาคู่สินทรัพย์ Cointegration เพื่อ Long ตัวถูก / Short ตัวแพง รอราคาดึงกลับสมดุล",
        "pros": "ไร้ความเสี่ยงจากทิศทางตลาดใหญ่ (Market Neutral) เน้นส่วนต่างราคา",
        "cons": "กำไรต่อรอบอาจไม่สูงมาก ต้องใช้เลเวอเรจ หรือจัดการคู่สินทรัพย์อย่างใกล้ชิด"
    },
    "NLP_SENTIMENT": {
        "level": "PROFESSIONAL",
        "level_label": "🔴 ระดับมืออาชีพ (Professional Quant)",
        "name": "Sentiment Analysis & NLP Trading (ประมวลข่าวสาร Real-time)",
        "icon": "📰",
        "risk_level": "สูง (Macro Sentiment Sensitive)",
        "desc": "ใช้ Gemini AI NLP อ่านข่าวเศรษฐกิจ งบการเงิน แถลงการณ์ Fed สั่งซื้อขายล่วงหน้าทันที",
        "pros": "ได้เปรียบด้านข้อมูลข่าวสาร ยิงออเดอร์ก่อนที่ราคาจะตอบรับข่าวใหญ่",
        "cons": "ข่าวบางประเภทอาจมีข้อมูลขัดแย้งกัน ต้องมีตัวกรอง Sentiment ที่รัดกุม"
    },
    "REINFORCEMENT_LEARNING": {
        "level": "PROFESSIONAL",
        "level_label": "🔴 ระดับมืออาชีพ (Professional Quant)",
        "name": "Reinforcement Learning (RL Trading Agent)",
        "icon": "🧠",
        "risk_level": "สูง (AI Dynamic Adaptability)",
        "desc": "เอเจนต์ AI เรียนรู้ผ่าน Reward System ลองเทรดจำลองเพื่อปรับตัวตามสภาวะตลาดสด",
        "pros": "สามารถค้นพบรูปแบบกลยุทธ์แปลกใหม่ที่ไม่เคยมีมนุษย์คนไหนคิดมาก่อน",
        "cons": "ความซับซ้อนของเอเจนต์สูง ต้องควบคุมจริยธรรมและกรอบบริหารความเสี่ยงเคร่งครัด"
    },
    "ORDER_FLOW_HFT": {
        "level": "PROFESSIONAL",
        "level_label": "🔴 ระดับมืออาชีพ (Professional Quant)",
        "name": "High-Frequency Trading & Order Flow (วิเคราะห์ Order Book)",
        "icon": "⚡",
        "risk_level": "สูงมาก (High Frequency Micro Execution)",
        "desc": "จำลองการวิเคราะห์ Order Book Imbalance / Spread Capture ความเร็วสูงระดับมิลลิวินาที",
        "pros": "ก็อบปี้การเก็บกำไรช่องเล็กๆ สม่ำเสมอจากส่วนต่างราคา BID/ASK",
        "cons": "ต้องคำนึงถึงค่าธรรมเนียมการเทรดและค่าความหน่วงของเครือข่าย (Latency)"
    }
}

DEFAULT_STRATEGY = "TREND_FOLLOWING"
