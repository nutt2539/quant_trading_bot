import os
import json
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import config
from execution_engine import fetch_alpaca_positions
from broker_bridge.broker_manager import get_broker_mode, get_broker_adapter
from utils_tz import get_thai_now, get_thai_str

TRADE_LOG_FILE = "autotrade_logs.json"

def get_asset_category(symbol: str) -> str:
    """
    Categorizes symbol into US_INDEX, GOLD, CRYPTO, or FOREX.
    """
    if symbol in config.GOLD_WATCHLIST or symbol in ["GC=F", "XAUUSD=X", "GLD", "IAU"]:
        return "GOLD"
    elif symbol in config.CRYPTO_WATCHLIST or symbol.endswith("-USD") or symbol in ["BTC", "ETH", "SOL", "BNB", "ADA", "XRP", "AVAX", "LINK"]:
        return "CRYPTO"
    elif symbol in config.FOREX_WATCHLIST or (symbol.endswith("=X") and symbol not in ["GC=F", "XAUUSD=X"]):
        return "FOREX"
    else:
        return "US_INDEX"

import streamlit as st

@st.cache_data(ttl=30)
def fetch_cached_ticker_price(sym: str) -> float:
    try:
        ticker = yf.Ticker(sym)
        hist = ticker.history(period="1d")
        if not hist.empty:
            return float(hist['Close'].iloc[-1])
    except Exception:
        pass
    return 0.0

def get_system_pnl(target_category: str = "US_INDEX", initial_capital: float = None) -> dict:
    """
    Calculates Real-Time PnL, Remaining Cash Balance, Cumulative Take Profit, Cumulative Cut Loss, and Active Holdings Detail for a specific system.
    """
    if initial_capital is None:
        initial_capital = config.SYSTEM_ALLOCATIONS.get(target_category, 100000.0)
        
    target_cats = [target_category]
    if target_category in ["STOCK", "THAI_STOCK", "US_STOCK"]:
        target_cats = ["US_INDEX", target_category]

    realized_pnl = 0.0
    closed_trades_count = 0
    win_trades_count = 0
    cumulative_take_profit_thb = 0.0
    cumulative_cut_loss_thb = 0.0
    
    today_dt = get_thai_now().date()
    yesterday_dt = today_dt - timedelta(days=1)
    three_days_ago_dt = today_dt - timedelta(days=3)
    seven_days_ago_dt = today_dt - timedelta(days=7)
    
    pnl_today = 0.0
    pnl_yesterday = 0.0
    pnl_3days = 0.0
    pnl_7days = 0.0
    
    active_paper_positions = {}
    
    # 1. Parse Logs filtered by target_cats
    if os.path.exists(TRADE_LOG_FILE):
        try:
            with open(TRADE_LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
                
            buy_records = {}
            for log in reversed(logs):
                symbol = log.get('symbol', '')
                if get_asset_category(symbol) not in target_cats:
                    continue
                    
                action = log.get('action')
                price = log.get('price', 0.0)
                shares = log.get('shares', 100.0)
                ts_str = log.get('timestamp', '')
                
                try:
                    log_date = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S').date()
                except Exception:
                    log_date = today_dt

                if action == 'BUY':
                    buy_records[symbol] = (price, log_date, shares)
                    active_paper_positions[symbol] = {
                        "symbol": symbol,
                        "qty": shares,
                        "avg_entry_price": price
                    }
                elif action == 'SELL':
                    is_manual_harvest = ("Harvest" in str(log.get('reason', '')) or "Manual" in str(log.get('reason', '')) or log.get('harvested_pnl_thb') is not None)
                    
                    entry_p = price
                    entry_shares = shares
                    if symbol in buy_records:
                        entry_p, entry_date, entry_shares = buy_records.pop(symbol)
                        if symbol in active_paper_positions:
                            del active_paper_positions[symbol]
                        
                    if entry_p > 0 and not is_manual_harvest:
                        fx_rate = 35.0 if not symbol.endswith(".BK") else 1.0
                        trade_pnl = (price - entry_p) * entry_shares * fx_rate
                        realized_pnl += trade_pnl
                        closed_trades_count += 1
                        
                        if trade_pnl > 0:
                            win_trades_count += 1
                            cumulative_take_profit_thb += trade_pnl
                        elif trade_pnl < 0:
                            cumulative_cut_loss_thb += abs(trade_pnl)
                            
                        if log_date == today_dt:
                            pnl_today += trade_pnl
                        if log_date == yesterday_dt:
                            pnl_yesterday += trade_pnl
                        if log_date >= three_days_ago_dt:
                            pnl_3days += trade_pnl
                        if log_date >= seven_days_ago_dt:
                            pnl_7days += trade_pnl
        except Exception as e:
            print(f"Error parsing trade logs: {e}")

    # 2. Query Live Real-Time Market Prices
    active_positions_detail = []
    invested_cash_thb = 0.0
    unrealized_pnl = 0.0
    
    curr_broker_mode = get_broker_mode()
    
    if curr_broker_mode == "LIVE":
        try:
            alpaca_positions = fetch_alpaca_positions()
            for pos in alpaca_positions:
                sym = pos.get('symbol', '')
                if get_asset_category(sym) not in target_cats:
                    continue
                    
                qty = float(pos.get('qty', 0))
                avg_cost = float(pos.get('avg_entry_price', 0))
                mkt_price = float(pos.get('current_price', 0))
                unrealized_p = float(pos.get('unrealized_pl', 0)) * 35.0
                cost_thb = qty * avg_cost * 35.0
                curr_val_thb = qty * mkt_price * 35.0
                
                invested_cash_thb += cost_thb
                unrealized_pnl += unrealized_p
                
                pnl_pct = ((mkt_price - avg_cost) / avg_cost * 100) if avg_cost > 0 else 0.0
                pnl_sign = "+" if pnl_pct >= 0 else ""
                
                active_positions_detail.append({
                    'ชื่อสินทรัพย์': sym,
                    'จำนวนหน่วย': qty,
                    'ต้นทุน/หน่วย': f"${avg_cost:,.2f}",
                    'ราคาตลาด (Realtime)': f"${mkt_price:,.2f}",
                    'เงินลงทุนรวม (บาท)': f"฿{cost_thb:,.2f}",
                    'มูลค่าปัจจุบัน (บาท)': f"฿{curr_val_thb:,.2f}",
                    'กำไร/ขาดทุน (%)': f"{pnl_sign}{pnl_pct:.2f}%",
                    'กำไร/ขาดทุน (บาท)': f"{pnl_sign}฿{unrealized_p:,.2f}",
                    'is_profit': unrealized_p >= 0
                })
        except Exception as e:
            print(f"Error fetching Live Broker positions for {target_category}: {e}")
    else:
        for sym, pos in active_paper_positions.items():
            qty = pos['qty']
            entry_p = pos['avg_entry_price']
            fx_rate = 35.0 if not sym.endswith(".BK") else 1.0
            
            fetched_p = fetch_cached_ticker_price(sym)
            mkt_price = fetched_p if fetched_p > 0 else entry_p
                
            pos_cost_thb = qty * entry_p * fx_rate
            pos_current_val_thb = qty * mkt_price * fx_rate
            pos_pnl_thb = (mkt_price - entry_p) * qty * fx_rate
            pos_pnl_pct = ((mkt_price - entry_p) / entry_p * 100) if entry_p > 0 else 0.0
            
            invested_cash_thb += pos_cost_thb
            unrealized_pnl += pos_pnl_thb
            
            curr_price_str = f"฿{mkt_price:,.2f}" if sym.endswith(".BK") else f"${mkt_price:,.2f}"
            entry_price_str = f"฿{entry_p:,.2f}" if sym.endswith(".BK") else f"${entry_p:,.2f}"
            pos_pnl_sign = "+" if pos_pnl_thb >= 0 else ""
            
            active_positions_detail.append({
                'ชื่อสินทรัพย์': sym,
                'จำนวนหน่วย': qty,
                'ต้นทุน/หน่วย': entry_price_str,
                'ราคาตลาด (Realtime)': curr_price_str,
                'เงินลงทุนรวม (บาท)': f"฿{pos_cost_thb:,.2f}",
                'มูลค่าปัจจุบัน (บาท)': f"฿{pos_current_val_thb:,.2f}",
                'กำไร/ขาดทุน (%)': f"{pos_pnl_sign}{pos_pnl_pct:.2f}%",
                'กำไร/ขาดทุน (บาท)': f"{pos_pnl_sign}฿{pos_pnl_thb:,.2f}",
                'is_profit': pos_pnl_thb >= 0
            })
        
    # 3. Calculate Total Harvested Profit Vault (FAIL-SAFE MULTI-SOURCE LOCK)
    tracker_vault_thb = 0.0
    log_vault_thb = 0.0
    master_vault_thb = 0.0
    
    cat_key = target_cats[0]
    
    # Source A: daily_harvest_tracker.json
    try:
        harvest_file = "daily_harvest_tracker.json"
        if os.path.exists(harvest_file):
            with open(harvest_file, "r", encoding="utf-8") as f_h:
                h_data = json.load(f_h)
                for item in h_data.get("harvest_history", []):
                    raw_sym = item.get("raw_symbol", item.get("symbol", ""))
                    if get_asset_category(raw_sym) in target_cats:
                        tracker_vault_thb += float(item.get("harvested_pnl_thb", 0.0))
    except Exception as e:
        print(f"Error reading harvest tracker: {e}")

    # Source B: autotrade_logs.json
    try:
        if os.path.exists(TRADE_LOG_FILE):
            with open(TRADE_LOG_FILE, "r", encoding="utf-8") as f_l:
                logs_data = json.load(f_l)
                for log_item in logs_data:
                    if "Daily Profit Harvest" in str(log_item.get("reason", "")) or "เก็บกำไร" in str(log_item.get("reason", "")):
                        raw_sym = log_item.get("raw_symbol", log_item.get("symbol", ""))
                        if get_asset_category(raw_sym) in target_cats:
                            log_vault_thb += float(log_item.get("harvested_pnl_thb", 0.0))
    except Exception as e:
        print(f"Error reading trade logs for harvest vault: {e}")

    # Source C: harvest_vault_master.json (Master Fail-Safe Storage)
    master_vault_file = "harvest_vault_master.json"
    m_data = {}
    try:
        if os.path.exists(master_vault_file):
            with open(master_vault_file, "r", encoding="utf-8") as f_m:
                m_data = json.load(f_m)
                master_vault_thb = float(m_data.get(f"{cat_key}_harvested_thb", 0.0))
    except Exception:
        pass

    # FAIL-SAFE: Always enforce the MAXIMUM cumulative harvested amount across all sources for this specific category
    total_harvested_vault_thb = max(tracker_vault_thb, log_vault_thb, master_vault_thb)

    # Persist the master vault total for this category so it can NEVER drop or reset
    try:
        m_data[f"{cat_key}_harvested_thb"] = total_harvested_vault_thb
        
        # Also compute global total
        global_total = sum(v for k, v in m_data.items() if k.endswith("_harvested_thb") and k != "master_total_harvested_thb")
        if global_total > 0:
            m_data["master_total_harvested_thb"] = max(global_total, float(m_data.get("master_total_harvested_thb", 0.0)))
            
        m_data["last_updated"] = str(today_dt)
        with open(master_vault_file, "w", encoding="utf-8") as f_m_w:
            json.dump(m_data, f_m_w, ensure_ascii=False, indent=2)
    except Exception:
        pass

    total_pnl_thb = realized_pnl + unrealized_pnl
    total_pnl_pct = (total_pnl_thb / initial_capital * 100) if initial_capital > 0 else 0.0
    current_equity = initial_capital + total_pnl_thb

    raw_cash = initial_capital + realized_pnl - invested_cash_thb
    cash_balance_thb = max(0.0, raw_cash)
    spendable_cash_thb = max(0.0, cash_balance_thb - total_harvested_vault_thb)

    if raw_cash < 0:
        invested_cash_thb = initial_capital + realized_pnl
        
    pnl_today += unrealized_pnl
    pnl_yesterday += (unrealized_pnl * 0.8)
    pnl_3days += unrealized_pnl
    pnl_7days += unrealized_pnl
    
    win_rate = (win_trades_count / closed_trades_count * 100) if closed_trades_count > 0 else 0.0

    return {
        'category': target_category,
        'initial_capital': initial_capital,
        'current_equity': current_equity,
        'cash_balance_thb': round(cash_balance_thb, 2),
        'spendable_cash_thb': round(spendable_cash_thb, 2),
        'harvested_vault_thb': round(total_harvested_vault_thb, 2),
        'invested_cash_thb': round(invested_cash_thb, 2),
        'invested_cash_thb': round(invested_cash_thb, 2),
        'total_pnl_thb': total_pnl_thb,
        'total_pnl_pct': total_pnl_pct,
        'pnl_today': pnl_today,
        'pnl_yesterday': pnl_yesterday,
        'pnl_3days': pnl_3days,
        'pnl_7days': pnl_7days,
        'realized_pnl_thb': round(realized_pnl, 2),
        'unrealized_pnl_thb': round(unrealized_pnl, 2),
                        'cumulative_take_profit_thb': round(cumulative_take_profit_thb, 2),
                        'cumulative_cut_loss_thb': round(cumulative_cut_loss_thb, 2),
                        'closed_trades': closed_trades_count,
                        'win_rate': round(win_rate, 1),
                        'active_positions_detail': active_positions_detail
                    }

def get_realtime_portfolio_pnl(initial_capital: float = 100000.0) -> dict:
    return get_system_pnl(target_category="THAI_STOCK", initial_capital=initial_capital)

def get_unified_portfolio_pnl() -> dict:
    """
    Combines PnL metrics across all 4 asset systems (US_INDEX ฿100k, GOLD ฿90k, CRYPTO ฿80k, FOREX ฿30k).
    Total Capital = 300,000 THB.
    """
    us_index_pnl = get_system_pnl("US_INDEX", config.US_INDEX_ALLOCATION_THB)
    gold_pnl = get_system_pnl("GOLD", config.GOLD_ALLOCATION_THB)
    crypto_pnl = get_system_pnl("CRYPTO", config.CRYPTO_ALLOCATION_THB)
    forex_pnl = get_system_pnl("FOREX", config.FOREX_ALLOCATION_THB)

    total_initial = config.TOTAL_CAPITAL_THB
    total_equity = us_index_pnl['current_equity'] + gold_pnl['current_equity'] + crypto_pnl['current_equity'] + forex_pnl['current_equity']
    total_cash = us_index_pnl['cash_balance_thb'] + gold_pnl['cash_balance_thb'] + crypto_pnl['cash_balance_thb'] + forex_pnl['cash_balance_thb']
    total_invested = us_index_pnl['invested_cash_thb'] + gold_pnl['invested_cash_thb'] + crypto_pnl['invested_cash_thb'] + forex_pnl['invested_cash_thb']
    
    total_pnl_thb = total_equity - total_initial
    total_pnl_pct = (total_pnl_thb / total_initial * 100.0) if total_initial > 0 else 0.0
    
    total_tp_thb = (us_index_pnl['cumulative_take_profit_thb'] + gold_pnl['cumulative_take_profit_thb'] +
                    crypto_pnl['cumulative_take_profit_thb'] + forex_pnl['cumulative_take_profit_thb'])
    total_cl_thb = (us_index_pnl['cumulative_cut_loss_thb'] + gold_pnl['cumulative_cut_loss_thb'] +
                    crypto_pnl['cumulative_cut_loss_thb'] + forex_pnl['cumulative_cut_loss_thb'])
    
    all_active_positions = (us_index_pnl['active_positions_detail'] + gold_pnl['active_positions_detail'] +
                            crypto_pnl['active_positions_detail'] + forex_pnl['active_positions_detail'])
    
    return {
        'total_initial': total_initial,
        'total_equity': round(total_equity, 2),
        'total_cash': round(total_cash, 2),
        'total_invested': round(total_invested, 2),
        'total_pnl_thb': round(total_pnl_thb, 2),
        'total_pnl_pct': round(total_pnl_pct, 2),
        'total_take_profit_thb': round(total_tp_thb, 2),
        'total_cut_loss_thb': round(total_cl_thb, 2),
        'us_index_pnl': us_index_pnl,
        'gold_pnl': gold_pnl,
        'crypto_pnl': crypto_pnl,
        'forex_pnl': forex_pnl,
        'thai_stock_pnl': us_index_pnl,  # Alias
        'us_stock_pnl': us_index_pnl,    # Alias
        'stock_pnl': us_index_pnl,       # Alias
        'all_active_positions': all_active_positions
    }

def get_daily_market_summary() -> pd.DataFrame:
    if not os.path.exists(TRADE_LOG_FILE):
        return pd.DataFrame()
        
    try:
        with open(TRADE_LOG_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)
            
        if not logs:
            return pd.DataFrame()
            
        summary_rows = []
        for log in logs:
            ts = log.get('timestamp', '')
            date_str = ts.split(' ')[0] if ' ' in ts else datetime.now().strftime('%Y-%m-%d')
            symbol = log.get('symbol', '')
            cat = get_asset_category(symbol)
            action = log.get('action', '')
            shares = log.get('shares', 0)
            total_thb = log.get('total_thb', 0.0)
            
            market = f"📈 Stock ({symbol})" if cat == "STOCK" else (f"🪙 Crypto ({symbol})" if cat == "CRYPTO" else f"💱 Forex ({symbol})")
            
            summary_rows.append({
                "วันที่": date_str,
                "หมวดสินทรัพย์": cat,
                "สัญลักษณ์": symbol,
                "คำสั่ง": action,
                "จำนวนหน่วย": shares,
                "มูลค่ารวม (บาท)": total_thb
            })
            
        df = pd.DataFrame(summary_rows)
        return df
    except Exception as e:
        print(f"Error building daily summary: {e}")
        return pd.DataFrame()

def get_closed_trades_breakdown() -> dict:
    """
    Returns detailed lists of closed trades contributing to Cumulative Take Profit and Cumulative Cut Loss.
    """
    take_profit_trades = []
    cut_loss_trades = []
    
    if os.path.exists(TRADE_LOG_FILE):
        try:
            with open(TRADE_LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
                
            buy_records = {}
            # Traverse chronological order to pair BUY and SELL trades
            for log in reversed(logs):
                symbol = log.get('symbol', '')
                action = log.get('action')
                price = log.get('price', 0.0)
                shares = log.get('shares', 1.0)
                ts_str = log.get('timestamp', '')
                reason = log.get('reason', 'AI Trading Decision')
                ai_summary = log.get('ai_summary', '')
                harvested_pnl = log.get('harvested_pnl_thb')

                if action == 'BUY':
                    buy_records[symbol] = (price, ts_str, shares)
                elif action == 'SELL':
                    is_manual_harvest = ("Harvest" in str(reason) or "Manual" in str(reason) or harvested_pnl is not None)
                    if is_manual_harvest:
                        continue  # Exclude manual harvest trades as requested by user
                        
                    fx_rate = 35.0 if not symbol.endswith(".BK") else 1.0
                    entry_p = price
                    entry_date = ts_str
                    if symbol in buy_records:
                        entry_p, entry_date, _ = buy_records.pop(symbol)
                    
                    if harvested_pnl is not None:
                        trade_pnl = float(harvested_pnl)
                    else:
                        trade_pnl = (price - entry_p) * shares * fx_rate
                    
                    pnl_pct_val = round(((price - entry_p) / entry_p) * 100, 2) if entry_p > 0 else 0.0
                    
                    trade_item = {
                        "timestamp": ts_str,
                        "symbol": symbol,
                        "category": get_asset_category(symbol),
                        "shares": shares,
                        "buy_price": entry_p,
                        "sell_price": price,
                        "trade_pnl_thb": round(trade_pnl, 2),
                        "pnl_pct": pnl_pct_val,
                        "reason": reason,
                        "ai_summary": ai_summary
                    }
                    
                    if trade_pnl > 0:
                        take_profit_trades.append(trade_item)
                    elif trade_pnl < 0:
                        trade_item["trade_pnl_thb"] = abs(round(trade_pnl, 2))
                        cut_loss_trades.append(trade_item)
        except Exception as e:
            print(f"Error fetching closed trades breakdown: {e}")
            
    return {
        "take_profit_trades": take_profit_trades,
        "cut_loss_trades": cut_loss_trades
    }
