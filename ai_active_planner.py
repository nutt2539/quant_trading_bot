"""
ai_active_planner.py
====================
24/7 Active AI Market Intelligence, News Sentiment Scanner, & Pre-Market Execution Planner.

Features:
1. 24/7 Deep Financial News & Sentiment Analysis across 3 Systems (Thai SET100, US Stocks, Crypto 24/7).
2. Off-Market Strategy Queueing: Pre-calculates target entries & orders while market is CLOSED, so orders fire instantly upon market open.
3. Optimal Spendable Cash Allocation: Maximizes capital productivity without touching the locked Harvest Vault.
"""

import json
import os
from datetime import datetime
from utils_tz import get_thai_now, get_thai_str
from pnl_tracker import get_system_pnl
from ai_analyst import analyze_stock_sentiment
from data_loader import fetch_stock_data
from strategies.swing_strategy import generate_swing_trading_signals
from multi_timeframe_analyzer import analyze_multi_timeframe

PREMARKET_QUEUE_FILE = "premarket_plan_queue.json"

WATCHLISTS = {
    "THAI_STOCK": ["BDMS.BK", "KCE.BK", "MINT.BK", "HANA.BK", "PTT.BK", "SCB.BK", "ADVANC.BK", "CPALL.BK", "AOT.BK", "KBANK.BK"],
    "US_STOCK": ["NVDA", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "AMD", "NFLX", "AAPL", "COST", "PLTR", "COIN", "ORCL"],
    "CRYPTO": ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "LINK-USD", "XRP-USD", "DOGE-USD", "AVAX-USD", "NEAR-USD", "DOT-USD"]
}

def generate_247_active_ai_plan() -> dict:
    """
    Scans news, technical momentum, and calculated win probability for all 3 asset classes 24/7.
    Generates a pre-market & live execution plan queue saved to premarket_plan_queue.json.
    """
    active_plans = {
        "timestamp": get_thai_str(),
        "systems": {}
    }

    for category, symbols in WATCHLISTS.items():
        sys_pnl = get_system_pnl(category, 100000.0)
        spendable_cash = sys_pnl.get("spendable_cash_thb", 0.0)
        harvested_vault = sys_pnl.get("harvested_vault_thb", 0.0)
        held_symbols = [p["ชื่อสินทรัพย์"] for p in sys_pnl.get("active_positions_detail", [])]
        held_raw_symbols = [p.get("raw_symbol", p["ชื่อสินทรัพย์"]) for p in sys_pnl.get("active_positions_detail", [])]

        candidate_plans = []

        for symbol in symbols:
            if symbol in held_symbols or symbol in held_raw_symbols:
                continue

            try:
                # 1. News Sentiment Scan
                ai_res = analyze_stock_sentiment(symbol)
                sent_score = ai_res.get("sentiment_score", 0.0)
                ai_summary = ai_res.get("summary", "")

                # 2. Technical Data & Signal Scan
                df = fetch_stock_data(symbol, period="3mo")
                if df.empty:
                    continue

                df_sig = generate_swing_trading_signals(df, strategy_key="CUSTOM")
                last_price = float(df_sig["Close"].iloc[-1])
                last_sig = int(df_sig["Signal"].iloc[-1])
                rsi_val = float(df_sig["RSI"].iloc[-1]) if "RSI" in df_sig.columns else 50.0

                # 3. Multi-Timeframe Confluence Score
                mtf_res = analyze_multi_timeframe(symbol)
                conf_score = float(mtf_res.get("confluence_score", 0.50))

                # Calculate AI Win Probability Score (0 - 100%)
                win_prob = min(98.0, max(20.0, (conf_score * 50) + (sent_score * 30) + ((50 - min(50, rsi_val)) * 0.6) + (20 if last_sig == 1 else 0)))

                if win_prob >= 55.0 and spendable_cash >= 1000.0:
                    fx_rate = 35.0 if not symbol.endswith(".BK") else 1.0
                    planned_alloc_thb = min(spendable_cash, max(10000.0, spendable_cash / max(1, (10 - len(held_symbols)))))
                    planned_shares = round(planned_alloc_thb / (last_price * fx_rate), 4)

                    candidate_plans.append({
                        "symbol": symbol,
                        "last_price": round(last_price, 2),
                        "win_probability_pct": round(win_prob, 1),
                        "confluence_score": round(conf_score, 2),
                        "ai_sentiment": round(sent_score, 2),
                        "rsi": round(rsi_val, 1),
                        "planned_alloc_thb": round(planned_alloc_thb, 2),
                        "planned_shares": planned_shares,
                        "ai_action_plan": f"🎯 [{symbol}] AI วิเคราะห์ข่าวเด็ด (Sentiment {sent_score:+.2f}) + โอกาสชนะ {win_prob:.1f}% -> ตั้งแผนเข้าซื้อทันทีเมื่อเปิดตลาด",
                        "ai_summary": ai_summary
                    })
            except Exception as e:
                print(f"Error scanning {symbol} in active planner: {e}")

        # Sort candidates by highest AI win probability
        candidate_plans.sort(key=lambda x: x["win_probability_pct"], reverse=True)

        active_plans["systems"][category] = {
            "spendable_cash_thb": round(spendable_cash, 2),
            "harvested_vault_thb": round(harvested_vault, 2),
            "held_count": len(held_symbols),
            "candidate_plans": candidate_plans[:5]  # Top 5 highest conviction targets
        }

    try:
        with open(PREMARKET_QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(active_plans, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving premarket queue: {e}")

    return active_plans

def get_latest_ai_active_plan() -> dict:
    """Load latest cached AI active pre-market plan."""
    if os.path.exists(PREMARKET_QUEUE_FILE):
        try:
            with open(PREMARKET_QUEUE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return generate_247_active_ai_plan()

if __name__ == "__main__":
    plan = generate_247_active_ai_plan()
    print("=== 24/7 ACTIVE AI MARKET INTELLIGENCE PLAN GENERATED ===")
    print(json.dumps(plan, ensure_ascii=False, indent=2))
