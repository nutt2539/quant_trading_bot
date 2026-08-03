import os
from dotenv import load_dotenv

load_dotenv()

# Portfolio Allocation Config (Total 100,000 THB)
TOTAL_CAPITAL_THB = 100000
US_ALLOCATION_PCT = 0.60   # 60,000 THB for US Stocks / ETFs
THAI_ALLOCATION_PCT = 0.40 # 40,000 THB for Thai Stocks

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
    """
    Save or update LINE_NOTIFY_TOKEN into environment and .env file.
    """
    global LINE_NOTIFY_TOKEN
    LINE_NOTIFY_TOKEN = token.strip()
    os.environ["LINE_NOTIFY_TOKEN"] = token.strip()
    
    # Save to .env file for persistence
    env_content = f"LINE_NOTIFY_TOKEN={token.strip()}\nGEMINI_API_KEY={GEMINI_API_KEY}\n"
    with open(".env", "w", encoding="utf-8") as f:
        f.write(env_content)
    return True

def update_telegram_config(bot_token: str, chat_id: str):
    """
    Save or update Telegram Bot Token and Chat ID.
    """
    global TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    TELEGRAM_BOT_TOKEN = bot_token.strip()
    TELEGRAM_CHAT_ID = chat_id.strip()
    os.environ["TELEGRAM_BOT_TOKEN"] = bot_token.strip()
    os.environ["TELEGRAM_CHAT_ID"] = chat_id.strip()
    
    with open(".env", "w", encoding="utf-8") as f:
        f.write(f"TELEGRAM_BOT_TOKEN={bot_token.strip()}\nTELEGRAM_CHAT_ID={chat_id.strip()}\nDISCORD_WEBHOOK_URL={DISCORD_WEBHOOK_URL}\n")
    return True

def update_discord_config(webhook_url: str):
    """
    Save or update Discord Webhook URL.
    """
    global DISCORD_WEBHOOK_URL
    DISCORD_WEBHOOK_URL = webhook_url.strip()
    os.environ["DISCORD_WEBHOOK_URL"] = webhook_url.strip()
    
    with open(".env", "w", encoding="utf-8") as f:
        f.write(f"TELEGRAM_BOT_TOKEN={TELEGRAM_BOT_TOKEN}\nTELEGRAM_CHAT_ID={TELEGRAM_CHAT_ID}\nDISCORD_WEBHOOK_URL={webhook_url.strip()}\n")
    return True

# Watchlist Expanded Universes (SET100 & S&P500 / NASDAQ Top Stocks)
US_WATCHLIST = [
    "AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "AMD", "PLTR", 
    "COIN", "NFLX", "DIS", "INTU", "PYPL", "COST", "INTC", "SPY", "QQQ", "IWM"
]

THAI_WATCHLIST = [
    "PTT.BK", "CPALL.BK", "AOT.BK", "BDMS.BK", "DELTA.BK", "ADVANC.BK", "GULF.BK", 
    "KBANK.BK", "SCB.BK", "KCE.BK", "HANA.BK", "OR.BK", "BANPU.BK", "MINT.BK", 
    "BH.BK", "SCC.BK", "CPN.BK", "TRUE.BK", "BBL.BK", "CENTEL.BK"
]

FOREX_WATCHLIST = [
    "EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCHF=X", "USDCAD=X", "XAUUSD=X"
]

CRYPTO_WATCHLIST = [
    "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "DOGE-USD", "ADA-USD", "AVAX-USD", "LINK-USD"
]

# Trading Rules & Risk Management (Swing Trading Optimized)
DEFAULT_STRATEGY = "Swing Trading (3-20 Days)"
MAX_POSITION_SIZE_PCT = 0.15 # Max 15% per stock
STOP_LOSS_PCT = 0.04         # 4% Swing Stop Loss
TAKE_PROFIT_PCT = 0.10       # 10% Swing Take Profit Target
TRAILING_STOP_PCT = 0.03     # 3% Trailing Stop

