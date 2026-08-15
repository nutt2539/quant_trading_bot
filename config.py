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
    "US_INDEX": "🇺🇸 US Equities & Indices (S&P 500 / NASDAQ / Dow)",
    "GOLD": "🥇 Gold & Commodities (XAU/USD / GC=F)",
    "CRYPTO": "🪙 Crypto Spot Terminal (24/7)",
    "FOREX": "💱 Forex Currency Pairs (24/5)"
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
        "level_label": "🟢 Beginner Tier (Rule-Based)",
        "name": "Grid Trading (Range Mesh Execution)",
        "icon": "🕸️",
        "risk_level": "Low (Sideway Range Market)",
        "desc": "Places geometric limit buy & sell grids across price corridors to extract consistent alpha from sideways consolidation.",
        "pros": "Reliable passive income in ranging markets without directional forecasting.",
        "cons": "Risk of multiple accumulating long bags during prolonged downward breakdown."
    },
    "TREND_FOLLOWING": {
        "level": "BEGINNER",
        "level_label": "🟢 Beginner Tier (Rule-Based)",
        "name": "Trend Following (EMA / RSI / MACD Momentum)",
        "icon": "📈",
        "risk_level": "Moderate (Momentum Tracking)",
        "desc": "Captures macro breakouts and multi-day trending expansions via EMA Crosses, RSI confirmation, and MACD divergence.",
        "pros": "Captures outsized profit runs during bull rallies with disciplined trailing stop-loss.",
        "cons": "Susceptible to whipsaw chop and false breakout signals in choppy markets."
    },
    "DCA_REBALANCE": {
        "level": "BEGINNER",
        "level_label": "🟢 Beginner Tier (Rule-Based)",
        "name": "DCA Bot & Smart Dynamic Rebalancing",
        "icon": "💰",
        "risk_level": "Very Low (Capital Preservation)",
        "desc": "Systematically accumulates assets at pullback thresholds and automatically rebalances portfolio weights.",
        "pros": "Eliminates timing risk and dollar-cost averages for long-term compound growth.",
        "cons": "Lower short-term velocity compared to high-frequency momentum strategies."
    },
    # 🟡 2.2 Intermediate Level (Statistics & ML)
    "MEAN_REVERSION": {
        "level": "INTERMEDIATE",
        "level_label": "🟡 Intermediate Tier (Statistical)",
        "name": "Mean Reversion (Bollinger Bands & Z-Score)",
        "icon": "⚖️",
        "risk_level": "Moderate (Statistical Arbitrage)",
        "desc": "Detects statistical standard deviation extremes (Z-Score > 2.0) and triggers counter-trend mean reversion trades.",
        "pros": "High mathematical win rate with clear, data-driven entry and exit bounds.",
        "cons": "Vulnerable to runaway momentum trends violating standard distribution boundaries."
    },
    "VOLATILITY_BREAKOUT": {
        "level": "INTERMEDIATE",
        "level_label": "🟡 Intermediate Tier (Statistical)",
        "name": "Volatility Breakout & Volume Surge",
        "icon": "💥",
        "risk_level": "Medium-High (Expansion Surge)",
        "desc": "Monitors volatility contraction (Squeeze) and fires aggressive market orders upon volume expansion breakouts.",
        "pros": "Secures ground-floor entry on explosive market moves with rapid profit realization.",
        "cons": "Requires strict, instantaneous stop-loss management against fakeouts."
    },
    "SUPERVISED_ML": {
        "level": "INTERMEDIATE",
        "level_label": "🟡 Intermediate Tier (Statistical)",
        "name": "Supervised ML Classification (Random Forest / XGBoost)",
        "icon": "🤖",
        "risk_level": "Moderate (Quantitative ML)",
        "desc": "Leverages ensemble machine learning classifiers to forecast next-candle directional probabilities across 15+ technical features.",
        "pros": "Synthesizes multi-dimensional technical features simultaneously with dynamic adaptability.",
        "cons": "Requires periodic hyperparameter tuning and model retraining to avoid overfitting."
    },
    # 🔴 2.3 Professional Level (Quant Funds & Deep AI)
    "STAT_ARBITRAGE": {
        "level": "PROFESSIONAL",
        "level_label": "🔴 Professional Tier (Institutional Quant)",
        "name": "Statistical Arbitrage & Pairs Trading",
        "icon": "📊",
        "risk_level": "Low-Moderate (Market Neutral)",
        "desc": "Identifies cointegrated asset pairs to execute Long undervalued / Short overvalued market-neutral spreads.",
        "pros": "Zero exposure to broader market directional beta (true market-neutral alpha).",
        "cons": "Narrow per-trade margins require precision sizing and tight spread monitoring."
    },
    "NLP_SENTIMENT": {
        "level": "PROFESSIONAL",
        "level_label": "🔴 Professional Tier (Institutional Quant)",
        "name": "AI NLP News Sentiment Analysis (Gemini Flash)",
        "icon": "📰",
        "risk_level": "High (Macro News Catalyst)",
        "desc": "Utilizes Gemini AI NLP to ingest economic headlines, SEC filings, and Fed speeches in real-time for front-running catalyst moves.",
        "pros": "Substantial informational edge by executing orders prior to general market pricing.",
        "cons": "Conflicting news headlines necessitate robust sentiment score filtering."
    },
    "REINFORCEMENT_LEARNING": {
        "level": "PROFESSIONAL",
        "level_label": "🔴 Professional Tier (Institutional Quant)",
        "name": "Deep Reinforcement Learning (Q-Learning Agent)",
        "icon": "🧠",
        "risk_level": "High (Autonomous AI Policy)",
        "desc": "Autonomous policy-gradient agent trained via reward functions to optimize risk-adjusted Sharpe ratios dynamically.",
        "pros": "Discovers non-linear, emergent alpha patterns beyond standard human heuristics.",
        "cons": "High algorithmic complexity requiring robust safety guardrails."
    },
    "ORDER_FLOW_HFT": {
        "level": "PROFESSIONAL",
        "level_label": "🔴 Professional Tier (Institutional Quant)",
        "name": "High-Frequency Order Flow & Microstructure",
        "icon": "⚡",
        "risk_level": "Very High (Microsecond Scalp)",
        "desc": "Analyzes Order Book Imbalance, bid-ask spread liquidity, and tick volume velocity for rapid micro-scalps.",
        "pros": "Captures consistent micro-spread profits independently of macro direction.",
        "cons": "Demands ultra-low latency execution and strict fee-adjusted slippage controls."
    }
}

DEFAULT_STRATEGY = "TREND_FOLLOWING"
