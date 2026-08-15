import time
import threading
import json
import os
from datetime import datetime
import config
from data_loader import fetch_stock_data
from strategies.quant_strategy_library import generate_quant_signal
from strategies.swing_strategy import get_active_strategy, get_custom_strategy_params
from ai_analyst import analyze_stock_sentiment
from execution_engine import execute_alpaca_trade, send_instant_notification, send_hourly_portfolio_summary
from pnl_tracker import get_system_pnl, get_asset_category, get_unified_portfolio_pnl
from risk_safety_guard import validate_market_hours, validate_trade_safety, check_daily_circuit_breaker
from multi_timeframe_analyzer import analyze_multi_timeframe
from volatility_engine import calculate_atr, get_dynamic_tp_sl, update_trailing_stop, get_asset_fee_pct
from macro_calendar_guard import is_macro_event_near
from kelly_position_sizer import calculate_kelly_allocation
from robot_control import get_robot_status
from utils_tz import get_thai_now, get_thai_now_naive, get_thai_str

LOG_FILE = "autotrade_logs.json"

def is_market_open(symbol: str) -> bool:
    """
    Checks whether the target market (Thai SET, US, Forex 24/5, Crypto 24/7) is OPEN.
    """
    now_dt = get_thai_now_naive()
    weekday = now_dt.weekday() # 0 = Mon, 6 = Sun
    time_now = now_dt.time()
    
    # 1. Crypto Market: 24/7/365
    if symbol in config.CRYPTO_WATCHLIST or symbol.endswith("-USD"):
        return True
        
    # 2. Forex & Gold Market: 24/5 (Mon 05:00 AM to Sat 05:00 AM ICT)
    if symbol in config.FOREX_WATCHLIST or symbol.endswith("=X") or symbol == "GC=F":
        if weekday == 5 and time_now >= datetime.strptime("05:00", "%H:%M").time():
            return False # Closed Saturday after 05:00 AM
        if weekday == 6:
            return False # Closed Sunday
        if weekday == 0 and time_now < datetime.strptime("05:00", "%H:%M").time():
            return False # Closed Monday before 05:00 AM
        return True
        
    # 3. Thai SET Market: Mon-Fri 10:00-12:30 & 14:30-16:30 ICT
    if symbol.endswith(".BK"):
        if weekday in [5, 6]:
            return False
        morning_open = datetime.strptime("10:00", "%H:%M").time()
        morning_close = datetime.strptime("12:30", "%H:%M").time()
        afternoon_open = datetime.strptime("14:30", "%H:%M").time()
        afternoon_close = datetime.strptime("16:30", "%H:%M").time()
        
        return (morning_open <= time_now <= morning_close) or (afternoon_open <= time_now <= afternoon_close)
        
    # 4. US Stocks Market: Mon-Fri 20:30-03:00 ICT
    else:
        us_open = datetime.strptime("20:30", "%H:%M").time()
        us_close = datetime.strptime("03:00", "%H:%M").time()
        
        if weekday in [0, 1, 2, 3, 4] and time_now >= us_open:
            return True
        elif weekday in [1, 2, 3, 4, 5] and time_now <= us_close:
            return True
        return False

def calculate_trade_quantity(symbol: str, last_price: float, allocation_thb: float = 15000.0) -> float:
    """
    Calculates exact trade quantity (Shares, Lots, or Crypto Units).
    """
    if last_price <= 0:
        return 1.0
        
    if symbol.endswith(".BK"):
        raw_qty = allocation_thb / last_price
        lots = max(1, int(raw_qty // 100))
        return float(lots * 100)
    elif symbol in config.CRYPTO_WATCHLIST or symbol.endswith("-USD"):
        usd_allocation = allocation_thb / 35.0
        raw_qty = usd_allocation / last_price
        return float(round(raw_qty, 4))
    elif symbol in config.FOREX_WATCHLIST or symbol.endswith("=X") or symbol == "GC=F":
        usd_allocation = allocation_thb / 35.0
        raw_qty = usd_allocation / last_price
        return float(round(raw_qty, 2))
    else:
        usd_allocation = allocation_thb / 35.0
        raw_qty = usd_allocation / last_price
        return float(max(1, int(raw_qty)))

def load_auto_logs() -> list:
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_auto_logs(logs: list):
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving auto logs: {e}")

def run_autotrader_cycle():
    """
    Executes one scanning cycle across watchlists based strictly on the selected Active Strategy.
    - BUY: If BUY signal triggers & AI Sentiment >= strategy threshold & not currently held -> Execute BUY action + Send Notification.
    - SELL: If SELL signal triggers OR Take Profit (TP %) OR Stop Loss (SL %) reached on HELD position -> Execute SELL action + Send Notification.
    """
    active_strategy = get_active_strategy()
    now_str = get_thai_str()
    
    # Check Master AI Robot Toggle Status (ON/OFF)
    if not get_robot_status():
        print(f"[{now_str}] 🔴 AI Auto-Trader is currently DISABLED by user (OFF). Skipping cycle.", flush=True)
        return

    print(f"\n[{now_str}] 🤖 Checking 24/7 AI Auto-Trading Signals [Active Strategy: {active_strategy}]...", flush=True)
    
    # Financial Safety: Circuit Breaker Check
    unified_pnl = get_unified_portfolio_pnl()
    pnl_today_val = unified_pnl.get('total_pnl_thb', 0.0)
    pnl_today_pct = (pnl_today_val / 300000.0) * 100
    
    is_broken, break_msg = check_daily_circuit_breaker(pnl_today_pct)
    if is_broken:
        print(f"[SAFETY CIRCUIT BREAKER ENFORCED]: {break_msg}", flush=True)
        return

    # Financial Safety: Macroeconomic Calendar Guard Check
    is_macro_near, event_name, macro_msg = is_macro_event_near()
    if is_macro_near:
        print(f"[MACRO GUARD ENFORCED]: {macro_msg}", flush=True)
        return
    
    # Load Strategy-Specific Parameters
    if active_strategy == "CUSTOM":
        c_params = get_custom_strategy_params()
        alloc_pct = float(c_params.get("alloc_pct", 20.0))
        tp_pct = float(c_params.get("tp_pct", 8.0))
        sl_pct = float(c_params.get("sl_pct", -3.5))
        min_ai_sentiment = float(c_params.get("ai_min_sentiment", 0.10))
    elif active_strategy == "MOMENTUM_BREAKOUT":
        alloc_pct, tp_pct, sl_pct, min_ai_sentiment = 25.0, 15.0, -5.0, 0.00
    elif active_strategy == "CRYPTO_SCALPING":
        alloc_pct, tp_pct, sl_pct, min_ai_sentiment = 25.0, 5.0, -2.5, 0.20
    elif active_strategy == "OVERSOLD_REBOUND":
        alloc_pct, tp_pct, sl_pct, min_ai_sentiment = 20.0, 10.0, -4.0, 0.00
    elif active_strategy == "HIGH_CONVICTION":
        alloc_pct, tp_pct, sl_pct, min_ai_sentiment = 35.0, 20.0, -6.0, 0.50
    else: # BALANCED_SWING (Default)
        alloc_pct, tp_pct, sl_pct, min_ai_sentiment = 20.0, 8.0, -3.5, 0.10
        
    logs = load_auto_logs()
    all_watchlist = config.US_INDEX_WATCHLIST + config.GOLD_WATCHLIST + config.CRYPTO_WATCHLIST + config.FOREX_WATCHLIST
    
    system_pnls = {
        cat: get_system_pnl(cat, config.SYSTEM_ALLOCATIONS.get(cat, 100000.0))
        for cat in ["US_INDEX", "GOLD", "CRYPTO", "FOREX"]
    }
    
    for symbol in all_watchlist:
        if not is_market_open(symbol):
            continue
            
        category = get_asset_category(symbol)
        active_strategy = get_active_strategy(category)
        display_sym = symbol.replace("-USD", "").replace("=X", "")
        
        # Determine if asset is CURRENTLY HELD in portfolio
        is_currently_held = False
        held_pos_detail = None
        
        target_sys = system_pnls.get(category, system_pnls["US_INDEX"])
        for p in target_sys['active_positions_detail']:
            if p.get('ชื่อสินทรัพย์') in [symbol, display_sym]:
                is_currently_held = True
                held_pos_detail = p
                break
            
        df = fetch_stock_data(symbol, period="6mo")
        if df.empty:
            continue
            
        ai_res = analyze_stock_sentiment(symbol)
        sentiment_score = ai_res.get('sentiment_score', 0.0)

        df_sig = generate_quant_signal(df, strategy_key=active_strategy, news_sentiment=sentiment_score)
        last_signal = df_sig['Signal'].iloc[-1]
        last_price = df_sig['Close'].iloc[-1]
        
        init_cap_fresh = config.SYSTEM_ALLOCATIONS.get(category, 100000.0)
        fresh_sys_pnl = get_system_pnl(category, init_cap_fresh)
        sys_cash = fresh_sys_pnl.get('spendable_cash_thb', fresh_sys_pnl['cash_balance_thb'])
        sys_invested = fresh_sys_pnl['invested_cash_thb']
        active_pos_count = len(fresh_sys_pnl['active_positions_detail'])
        
        # Dynamic Kelly Position Sizing (Maximal spendable cash utilization while protecting Harvested Vault)
        kelly_res = calculate_kelly_allocation(sys_cash, ai_sentiment_score=sentiment_score, base_allocation_thb=max(10000.0, sys_cash / max(1, (10 - active_pos_count))))
        target_alloc_baht = kelly_res["allocated_thb"]
        allocation_amount = min(target_alloc_baht, sys_cash)
        
        # Maximize spendable cash utilization (no idle spendable cash when valid signal is detected)
        if sys_cash >= 1000.0 and active_pos_count < 10:
            if sys_cash <= 25000.0 or active_pos_count >= 8:
                allocation_amount = sys_cash # Fully deploy remaining spendable cash into high-conviction signal
            
        trade_qty = calculate_trade_quantity(symbol, last_price, allocation_thb=allocation_amount)
        fx_rate = 35.0 if not symbol.endswith(".BK") else 1.0
        trade_total_thb = round(trade_qty * last_price * fx_rate, 2)
        
        # CASE 1: UNHELD ASSET -> BUY EVALUATION (UP TO 10 POSITIONS PER SYSTEM, MAXIMIZE SPENDABLE CASH)
        if not is_currently_held:
            # Active buying condition: Signal=BUY OR (AI Sentiment Positive >= 0.0) OR RSI Dip Setup
            if (last_signal == 1 or sentiment_score >= 0.0) and (sentiment_score >= min_ai_sentiment) and (sys_cash >= 1000.0) and (trade_total_thb > 0) and (active_pos_count < 10):
                # Multi-Timeframe Confluence Check
                mtf_res = analyze_multi_timeframe(symbol)
                conf_score = mtf_res.get("confluence_score", 0.50)
                
                if conf_score < 0.35:
                    print(f"🛑 MTF FILTER: {symbol} Confluence Low ({conf_score:.2f})", flush=True)
                    continue

                is_safe, safety_reason = validate_trade_safety(symbol, "BUY", trade_total_thb)
                if not is_safe:
                    print(f"🛑 RISK GUARD BLOCKED BUY {symbol}: {safety_reason}", flush=True)
                    continue

                log_entry = {
                    "timestamp": get_thai_str(),
                    "symbol": symbol,
                    "action": "BUY",
                    "shares": trade_qty,
                    "price": round(last_price, 2),
                    "total_thb": trade_total_thb,
                    "reason": f"[{active_strategy}] Signal=BUY | MTF Score={mtf_res.get('confluence_score')} | {kelly_res['reason']}",
                    "ai_summary": ai_res.get('summary', '')
                }
                print(f"🚀 AUTO BUY TRIGGERED for {symbol} ({trade_qty} units at {last_price}) | Kelly Sizing: ฿{trade_total_thb:,.2f}", flush=True)
                
                if category == "US_STOCK":
                    res = execute_alpaca_trade(symbol, qty=trade_qty, side="buy")
                    log_entry['status'] = res.get('status')
                else:
                    msg = f"🟢 [{category} ACTION - ซื้อตามกลยุทธ์ {active_strategy}]\nเข้าซื้อ: {display_sym}\nจำนวน: {trade_qty} หน่วย (ราคา {last_price:,.2f})\nรวมเงินลงทุน (Kelly Sizing): ฿{trade_total_thb:,.2f}\nเหตุผล: สัญญาณ MTF 3-Timeframe ({mtf_res.get('confluence_score')}) + {kelly_res['conviction_tier']}"
                    send_instant_notification(msg)
                    log_entry['status'] = "notified"
                    
                logs.insert(0, log_entry)
                save_auto_logs(logs)

        # CASE 2: CURRENTLY HELD ASSET -> EVALUATE ADVANCED AI DYNAMIC EXIT & EARLY PROFIT TAKING
        else:
            entry_price = held_pos_detail.get('ต้นทุนเฉลี่ย', last_price) if held_pos_detail else last_price
            hold_qty = held_pos_detail.get('จำนวนหุ้น/หน่วย', trade_qty) if held_pos_detail else trade_qty
            hold_total_thb = round(hold_qty * last_price * fx_rate, 2)
            
            # Dynamic Volatility ATR Targets Calculation
            df_sig["ATR"] = calculate_atr(df_sig, 14)
            last_atr = df_sig.iloc[-1].get("ATR", 0.0) if "ATR" in df_sig.columns else 0.0
            dynamic_targets = get_dynamic_tp_sl(entry_price, last_atr, base_tp_pct=tp_pct, base_sl_pct=sl_pct)
            eff_tp_pct = dynamic_targets["tp_pct"]
            eff_sl_pct = dynamic_targets["sl_pct"]
            
            pnl_pct = ((last_price - entry_price) / entry_price) * 100.0 if entry_price > 0 else 0.0
            rsi_val = float(df_sig["RSI"].iloc[-1]) if "RSI" in df_sig.columns else 50.0
            
            # Multi-Timeframe Confluence Check
            mtf_res = analyze_multi_timeframe(symbol)
            conf_score = float(mtf_res.get("confluence_score", 0.50))

            # Advanced AI Dynamic Exit Evaluation (Global News Shift, Momentum Fading, Early Profit Taking)
            from ai_exit_analyzer import evaluate_ai_dynamic_exit
            fee_pct = get_asset_fee_pct(symbol)
            should_exit, exit_type, sell_reason = evaluate_ai_dynamic_exit(
                symbol=symbol,
                pnl_pct=pnl_pct,
                sentiment_score=sentiment_score,
                rsi_val=rsi_val,
                conf_score=conf_score,
                eff_tp_pct=eff_tp_pct,
                eff_sl_pct=eff_sl_pct,
                last_signal=last_signal,
                fee_pct=fee_pct
            )
            
            if should_exit:
                is_safe, safety_reason = validate_trade_safety(symbol, "SELL", hold_total_thb)
                if not is_safe:
                    print(f"🛑 RISK GUARD BLOCKED SELL {symbol}: {safety_reason}", flush=True)
                    continue
                    
                log_entry = {
                    "timestamp": get_thai_str(),
                    "symbol": symbol,
                    "action": "SELL",
                    "shares": hold_qty,
                    "price": round(last_price, 2),
                    "total_thb": hold_total_thb,
                    "reason": f"[{active_strategy}] [{exit_type}] {sell_reason}",
                    "ai_summary": ai_res.get('summary', '')
                }
                print(f"🔴 AUTO SELL TRIGGERED for {symbol} ({hold_qty} units at {last_price}) | Reason: {sell_reason}", flush=True)
                
                if category == "US_STOCK":
                    res = execute_alpaca_trade(symbol, qty=hold_qty, side="sell")
                    log_entry['status'] = res.get('status')
                else:
                    msg = f"🔴 [{category} ACTION - ขายทำรอบตามกลยุทธ์ {active_strategy}]\nขายปิดออเดอร์: {display_sym}\nจำนวน: {hold_qty} หน่วย (ราคา {last_price:,.2f})\nยอดขายรวม: ฿{hold_total_thb:,.2f}\nผลตอบแทน: {pnl_pct:+.2f}%\nเหตุผล: {sell_reason}"
                    send_instant_notification(msg)
                    log_entry['status'] = "notified"
                    
                logs.insert(0, log_entry)
                save_auto_logs(logs)

def start_daemon_loop(interval_seconds: int = 180):
    print("🤖 24/7 AI Auto-Trader Daemon Service Initialized with Action-Only Alerts & Hourly Summary Reports.", flush=True)
    
    last_hourly_report_time = 0
    
    while True:
        try:
            current_time = time.time()
            if current_time - last_hourly_report_time >= 3600:
                print("📊 Sending Hourly Telegram Portfolio Summary Report...", flush=True)
                send_hourly_portfolio_summary()
            try:
                import scalper_engine
                scalper_engine.run_auto_scalper_cycle()
            except Exception as e:
                print(f"[SCALPER DAEMON HOOK ERROR] {e}", flush=True)

            run_autotrader_cycle()
        except Exception as e:
            print(f"Error in autotrader cycle: {e}", flush=True)
        time.sleep(interval_seconds)

def _background_autotrader_loop(interval_seconds: int = 180):
    """
    Daemon background thread running continuous 24/7 scanning cycle inside web server.
    """
    time.sleep(10)
    print("🤖 [AUTOTRADER DAEMON] 24/7 Background Thread Active & Scanning Portfolio...", flush=True)
    while True:
        try:
            from robot_control import get_robot_status
            try:
                import scalper_engine
                scalper_engine.run_auto_scalper_cycle()
            except Exception:
                pass

            if get_robot_status():
                run_autotrader_cycle()
        except Exception as e:
            print(f"[AUTOTRADER DAEMON ERROR] {e}", flush=True)
        time.sleep(interval_seconds)

def init_autotrader_background_loop():
    """
    Launches autotrader background thread on web app startup if not already running.
    """
    if not getattr(init_autotrader_background_loop, "_started", False):
        init_autotrader_background_loop._started = True
        thread = threading.Thread(target=_background_autotrader_loop, daemon=True)
        thread.start()

if __name__ == "__main__":
    start_daemon_loop(180)
