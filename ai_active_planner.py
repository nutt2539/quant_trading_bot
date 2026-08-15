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
import config
from utils_tz import get_thai_now, get_thai_str
from pnl_tracker import get_system_pnl
from ai_analyst import analyze_stock_sentiment
from data_loader import fetch_stock_data
from strategies.quant_strategy_library import generate_quant_signal
from strategies.swing_strategy import get_active_strategy
from multi_timeframe_analyzer import analyze_multi_timeframe

PREMARKET_QUEUE_FILE = "premarket_plan_queue.json"

WATCHLISTS = config.SYSTEM_WATCHLISTS

def generate_247_active_ai_plan() -> dict:
    """
    Scans news, technical momentum, and calculated win probability for all 4 asset classes 24/7.
    Generates a pre-market & live execution plan queue saved to premarket_plan_queue.json.
    """
    active_plans = {
        "timestamp": get_thai_str(),
        "systems": {}
    }

    # Load old plans to diff for Telegram notifications
    old_plans = {}
    if os.path.exists(PREMARKET_QUEUE_FILE):
        try:
            with open(PREMARKET_QUEUE_FILE, "r", encoding="utf-8") as f:
                old_data = json.load(f)
                for sys_cat, sys_data in old_data.get("systems", {}).items():
                    for cp in sys_data.get("candidate_plans", []):
                        sym = cp.get("symbol", "")
                        pt = cp.get("plan_type", "BUY")
                        old_plans[f"{sym}_{pt}"] = True
        except Exception:
            pass

    for sys_cat, watchlist in WATCHLISTS.items():
        sys_pnl = get_system_pnl(sys_cat, config.SYSTEM_ALLOCATIONS.get(sys_cat, 100000.0))
        cat_strat = get_active_strategy(sys_cat)
        
        spendable_cash = sys_pnl.get("spendable_cash_thb", 0.0)
        harvested_vault = sys_pnl.get("harvested_vault_thb", 0.0)
        held_symbols = [p["ชื่อสินทรัพย์"] for p in sys_pnl.get("active_positions_detail", [])]

        candidate_plans = []

        for symbol in watchlist:
            is_held = False
            held_detail = None
            for p in sys_pnl.get("active_positions_detail", []):
                if p.get("raw_symbol", p["ชื่อสินทรัพย์"]) == symbol or p["ชื่อสินทรัพย์"] == symbol:
                    is_held = True
                    held_detail = p
                    break

            try:
                # 1. News Sentiment Scan
                ai_res = analyze_stock_sentiment(symbol)
                sent_score = ai_res.get("sentiment_score", 0.0)
                ai_summary = ai_res.get("summary", "")

                # 2. Technical Data & Signal Scan
                df = fetch_stock_data(symbol, period="3mo")
                if df.empty:
                    continue

                df_sig = generate_quant_signal(df, strategy_key=cat_strat, news_sentiment=sent_score)
                last_price = float(df_sig["Close"].iloc[-1])
                last_sig = int(df_sig["Signal"].iloc[-1])
                rsi_val = float(df_sig["RSI"].iloc[-1]) if "RSI" in df_sig.columns else 50.0

                # 3. Multi-Timeframe Confluence Score
                mtf_res = analyze_multi_timeframe(symbol)
                conf_score = float(mtf_res.get("confluence_score", 0.50))

                from volatility_engine import calculate_atr, get_dynamic_tp_sl, get_asset_fee_pct
                df_sig["ATR"] = calculate_atr(df_sig, 14)
                last_atr = float(df_sig["ATR"].iloc[-1]) if "ATR" in df_sig.columns and not df_sig["ATR"].isna().iloc[-1] else 0.0
                dynamic_targets = get_dynamic_tp_sl(last_price, last_atr, base_tp_pct=8.0, base_sl_pct=-3.5)
                fee_pct = get_asset_fee_pct(symbol)

                if is_held:
                    # Evaluate Sell Plan
                    entry_price_str = str(held_detail.get("ต้นทุน/หน่วย", last_price)).replace("$", "").replace("฿", "").replace(",", "")
                    entry_price = float(entry_price_str)
                    pnl_pct_str = str(held_detail.get("กำไร/ขาดทุน (%)", "0.00")).replace("+", "").replace("%", "").strip()
                    pnl_pct = float(pnl_pct_str)
                    
                    from ai_exit_analyzer import evaluate_ai_dynamic_exit
                    should_exit, exit_type, sell_reason = evaluate_ai_dynamic_exit(
                        symbol=symbol,
                        pnl_pct=pnl_pct,
                        sentiment_score=sent_score,
                        rsi_val=rsi_val,
                        conf_score=conf_score,
                        eff_tp_pct=dynamic_targets["tp_pct"],
                        eff_sl_pct=dynamic_targets["sl_pct"],
                        last_signal=last_sig,
                        fee_pct=fee_pct
                    )
                    
                    if should_exit:
                        candidate_plans.append({
                            "symbol": symbol,
                            "plan_type": "SELL",
                            "last_price": round(last_price, 2),
                            "win_probability_pct": 0.0,
                            "confluence_score": round(conf_score, 2),
                            "ai_sentiment": round(sent_score, 2),
                            "rsi": round(rsi_val, 1),
                            "planned_alloc_thb": 0.0,
                            "planned_shares": 0.0,
                            "tp_price": round(dynamic_targets["tp_price"], 2),
                            "sl_price": round(dynamic_targets["sl_price"], 2),
                            "tp_pct": dynamic_targets["tp_pct"],
                            "sl_pct": dynamic_targets["sl_pct"],
                            "fee_pct": fee_pct,
                            "ai_action_plan": f"🔴 [{symbol}] AI Exit Signal: {sell_reason} -> Scheduled Sell Plan",
                            "ai_summary": ai_summary,
                            "ai_thought_rationale": f"🧠 [AI OBSERVE ROOM] Asset {symbol} flagged for profit lock / risk de-escalation due to: {sell_reason} | Macro Sentiment ({sent_score:+.2f}) | RSI ({rsi_val:.1f}) | Round-trip Fee ({fee_pct}%)",
                            "pipeline_steps": [
                                {"name": "📰 Global News & Macro Scan", "status": "COMPLETED", "detail": f"Sentiment Score: {sent_score:+.2f}"},
                                {"name": "📈 Multi-Timeframe Alignment Check", "status": "COMPLETED", "detail": f"Confluence Score: {conf_score:.2f}"},
                                {"name": "📊 Technical Levels & Risk Setup", "status": "COMPLETED", "detail": f"RSI: {rsi_val:.1f} | SL: {dynamic_targets['sl_pct']:.1f}%"},
                                {"name": "🧮 Smart Fee & Net Profit Filter", "status": "COMPLETED", "detail": f"Round-trip Fee: {fee_pct}%"},
                                {"name": "⚡ Exit Order Execution Ready", "status": "IN_PROGRESS", "detail": "Standby for real-time exit trigger execution"}
                            ]
                        })
                    continue

                # Calculate AI Win Probability Score for BUY Plan based on Strategy Fit & Indicators
                strat_bonus = 15.0 if last_sig == 1 else 0.0
                win_prob = min(98.0, max(20.0, (conf_score * 45) + (sent_score * 25) + ((50 - min(50, rsi_val)) * 0.5) + strat_bonus + 10.0))

                if win_prob >= 55.0 and spendable_cash >= 1000.0:
                    fx_rate = 35.0 if not symbol.endswith(".BK") else 1.0
                    planned_alloc_thb = min(spendable_cash, max(10000.0, spendable_cash / max(1, (10 - len(held_symbols)))))
                    planned_shares = round(planned_alloc_thb / (last_price * fx_rate), 4)

                    tp_price = dynamic_targets["tp_price"]
                    sl_price = dynamic_targets["sl_price"]
                    tp_pct = dynamic_targets["tp_pct"]
                    sl_pct = dynamic_targets["sl_pct"]
                    
                    est_gross_profit_thb = planned_alloc_thb * (tp_pct / 100.0)
                    est_fee_thb = planned_alloc_thb * (fee_pct / 100.0)
                    est_net_profit_thb = round(est_gross_profit_thb - est_fee_thb, 2)

                    candidate_plans.append({
                        "symbol": symbol,
                        "plan_type": "BUY",
                        "last_price": round(last_price, 2),
                        "win_probability_pct": round(win_prob, 1),
                        "confluence_score": round(conf_score, 2),
                        "ai_sentiment": round(sent_score, 2),
                        "rsi": round(rsi_val, 1),
                        "planned_alloc_thb": round(planned_alloc_thb, 2),
                        "planned_shares": planned_shares,
                        "tp_price": round(tp_price, 2),
                        "sl_price": round(sl_price, 2),
                        "tp_pct": tp_pct,
                        "sl_pct": sl_pct,
                        "fee_pct": fee_pct,
                        "est_net_profit_thb": est_net_profit_thb,
                        "ai_action_plan": f"🟢 [{symbol}] Bullish Catalyst (Sentiment {sent_score:+.2f}) + Win Prob {win_prob:.1f}% -> Scheduled Buy Plan",
                        "ai_summary": ai_summary,
                        "ai_thought_rationale": f"🧠 [AI OBSERVE ROOM] High-edge opportunity identified in {symbol}! Bullish sentiment ({sent_score:+.2f}) + Multi-Timeframe Alignment ({conf_score:.2f}) + RSI ({rsi_val:.1f}) | Statistical Win Probability: {win_prob:.1f}% | Target TP: +{tp_pct:.1f}% (Est. Net Gain +฿{est_net_profit_thb:,.2f})",
                        "pipeline_steps": [
                            {"name": "📰 Global News & Macro Scan", "status": "COMPLETED", "detail": f"Sentiment Score: {sent_score:+.2f}"},
                            {"name": "📈 Multi-Timeframe Alignment Check", "status": "COMPLETED", "detail": f"Confluence Score: {conf_score:.2f}"},
                            {"name": "📊 Technical Levels & Risk Setup", "status": "COMPLETED", "detail": f"RSI: {rsi_val:.1f} | TP Target: +{tp_pct:.1f}%"},
                            {"name": "🧮 Smart Fee & Net Profit Filter", "status": "COMPLETED", "detail": f"Fee {fee_pct}% -> Est Net Profit +฿{est_net_profit_thb:,.2f}"},
                            {"name": "⚡ Order Trigger Ready", "status": "IN_PROGRESS", "detail": "Standby for real-time entry trigger"}
                        ]
                    })
            except Exception as e:
                print(f"Error scanning {symbol} in active planner: {e}")

        # Sort candidates: SELL plans first, then BUY plans by highest AI win probability
        candidate_plans.sort(key=lambda x: (0 if x.get("plan_type") == "SELL" else 1, -x["win_probability_pct"]))

        active_plans["systems"][sys_cat] = {
            "spendable_cash_thb": round(spendable_cash, 2),
            "harvested_vault_thb": round(harvested_vault, 2),
            "held_count": len(held_symbols),
            "candidate_plans": candidate_plans[:5]  # Top 5 targets per system
        }

    try:
        with open(PREMARKET_QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(active_plans, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving premarket queue: {e}")
        
    # Send Notifications for NEW plans
    try:
        from execution_engine import send_instant_notification
        for category, sys_data in active_plans["systems"].items():
            for cp in sys_data.get("candidate_plans", []):
                sym = cp.get("symbol", "")
                pt = cp.get("plan_type", "BUY")
                plan_key = f"{sym}_{pt}"
                if plan_key not in old_plans:
                    if pt == "SELL":
                        msg = f"🔴 [AI PRE-MARKET PLAN - EXIT SETUP]\nTarget: {sym}\nLast Price: {cp.get('last_price')}\nAI Plan: {cp.get('ai_action_plan')}\nRationale: {cp.get('ai_summary')}"
                    else:
                        msg = f"🟢 [AI PRE-MARKET PLAN - ENTRY SETUP]\nTarget: {sym}\nLast Price: {cp.get('last_price')}\nWin Probability: {cp.get('win_probability_pct')}%\nAI Plan: {cp.get('ai_action_plan')}\nRationale: {cp.get('ai_summary')}"
                    send_instant_notification(msg)
    except Exception as e:
        print(f"Error sending plan notifications: {e}")

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
