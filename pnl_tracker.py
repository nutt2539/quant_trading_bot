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
    Categorizes symbol into STOCK, CRYPTO, or FOREX.
    """
    if symbol in config.CRYPTO_WATCHLIST or symbol.endswith("-USD"):
        return "CRYPTO"
    elif symbol in config.FOREX_WATCHLIST or symbol.endswith("=X") or symbol == "GC=F":
        return "FOREX"
    else:
        return "STOCK"

def get_system_pnl(target_category: str = "STOCK", initial_capital: float = 100000.0) -> dict:
    """
    Calculates Real-Time PnL, Remaining Cash Balance, Cumulative Take Profit, Cumulative Cut Loss, and Active Holdings Detail for a specific system.
    """
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
    
    # 1. Parse Logs filtered by target_category
    if os.path.exists(TRADE_LOG_FILE):
        try:
            with open(TRADE_LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
                
            buy_records = {}
            for log in reversed(logs):
                symbol = log.get('symbol', '')
                if get_asset_category(symbol) != target_category:
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
            print(f"Error parsing trade logs for {target_category}: {e}")

    # 2. Live Broker vs Paper Positions Sync
    unrealized_pnl = 0.0
    invested_cash_thb = 0.0
    active_positions_detail = []
    
    if get_broker_mode() == "LIVE":
        adapter = get_broker_adapter(target_category)
        live_bal = adapter.get_account_balance()
        live_pos = adapter.get_positions()
        
        cash_balance_thb = live_bal.get("cash_thb", initial_capital)
        invested_cash_thb = live_bal.get("invested_thb", 0.0)
        current_equity = live_bal.get("equity_thb", initial_capital)
        
        for pos in live_pos:
            active_positions_detail.append({
                'ชื่อสินทรัพย์': pos.get('symbol', ''),
                'raw_symbol': pos.get('raw_symbol', ''),
                'จำนวนหน่วย': pos.get('shares', 0),
                'ต้นทุน/หน่วย': f"฿{pos.get('cost_price', 0):,.2f}",
                'ราคาตลาด (Realtime)': f"฿{pos.get('current_price', 0):,.2f}",
                'เงินลงทุนรวม (บาท)': f"฿{pos.get('shares', 0) * pos.get('cost_price', 0):,.2f}",
                'มูลค่าปัจจุบัน (บาท)': f"฿{pos.get('shares', 0) * pos.get('current_price', 0):,.2f}",
                'กำไร/ขาดทุน (บาท)': f"{'+' if pos.get('pnl_thb', 0) >= 0 else ''}฿{pos.get('pnl_thb', 0):,.2f}",
                'กำไร/ขาดทุน (%)': f"{'+' if pos.get('pnl_pct', 0) >= 0 else ''}{pos.get('pnl_pct', 0):.2f}%",
                'is_profit': pos.get('pnl_thb', 0) >= 0
            })
            
        return {
            'target_category': target_category,
            'broker_mode': 'LIVE',
            'initial_capital': initial_capital,
            'current_equity': round(current_equity, 2),
            'cash_balance_thb': round(cash_balance_thb, 2),
            'invested_cash_thb': round(invested_cash_thb, 2),
            'realized_pnl_thb': round(realized_pnl, 2),
            'total_pnl_thb': round(current_equity - initial_capital, 2),
            'total_pnl_pct': round(((current_equity - initial_capital) / initial_capital) * 100.0, 2),
            'pnl_today': round(pnl_today, 2),
            'pnl_yesterday': round(pnl_yesterday, 2),
            'pnl_3days': round(pnl_3days, 2),
            'pnl_7days': round(pnl_7days, 2),
            'cumulative_take_profit_thb': round(cumulative_take_profit_thb, 2),
            'cumulative_cut_loss_thb': round(cumulative_cut_loss_thb, 2),
            'closed_trades_count': closed_trades_count,
            'win_trades_count': win_trades_count,
            'active_positions_count': len(active_positions_detail),
            'active_positions_detail': active_positions_detail
        }
        
    positions = []
    if target_category == "STOCK":
        positions = fetch_alpaca_positions()
        
    alpaca_symbols = {p.get('symbol') for p in positions}
    for p_sym, p_data in active_paper_positions.items():
        if p_sym not in alpaca_symbols:
            positions.append(p_data)
            
    for pos in positions:
        symbol = pos.get('symbol')
        if get_asset_category(symbol) != target_category:
            continue
            
        qty = float(pos.get('qty', 1.0))
        entry_price = float(pos.get('avg_entry_price', 0.0))
        current_price = float(pos.get('current_price', entry_price))
        
        is_us = not symbol.endswith(".BK")
        fx_rate = 35.0 if is_us else 1.0
        
        if current_price == entry_price and entry_price > 0:
            try:
                df_curr = yf.Ticker(symbol).history(period="1d")
                if not df_curr.empty:
                    current_price = df_curr['Close'].iloc[-1]
            except Exception:
                pass
                
        pos_cost_thb = entry_price * qty * fx_rate
        pos_current_val_thb = current_price * qty * fx_rate
        pos_pnl_thb = pos_current_val_thb - pos_cost_thb
        pos_pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0.0
        
        invested_cash_thb += pos_cost_thb
        unrealized_pnl += pos_pnl_thb
        
        display_name = "GOLD (ทองคำ)" if symbol in ["GC=F", "XAUUSD=X"] else symbol.replace("-USD", "").replace("=X", "")
        unit_currency = "$" if is_us else "฿"
        pos_pnl_sign = "+" if pos_pnl_thb >= 0 else ""
        
        active_positions_detail.append({
            'ชื่อสินทรัพย์': display_name,
            'จำนวนหน่วย': round(qty, 4) if target_category == "CRYPTO" else (round(qty, 2) if target_category == "FOREX" else int(qty)),
            'ต้นทุน/หน่วย': f"{unit_currency}{entry_price:.2f}",
            'ราคาตลาด (Realtime)': f"{unit_currency}{current_price:.2f}",
            'เงินลงทุนรวม (บาท)': f"฿{pos_cost_thb:,.2f}",
            'มูลค่าปัจจุบัน (บาท)': f"฿{pos_current_val_thb:,.2f}",
            'กำไร/ขาดทุน (%)': f"{pos_pnl_sign}{pos_pnl_pct:.2f}%",
            'กำไร/ขาดทุน (บาท)': f"{pos_pnl_sign}฿{pos_pnl_thb:,.2f}",
            'is_profit': pos_pnl_thb >= 0
        })
        
    total_pnl_thb = realized_pnl + unrealized_pnl
    total_pnl_pct = (total_pnl_thb / initial_capital) * 100
    current_equity = initial_capital + total_pnl_thb

    raw_cash = initial_capital + realized_pnl - invested_cash_thb
    cash_balance_thb = max(0.0, raw_cash)
    if raw_cash < 0:
        invested_cash_thb = initial_capital + realized_pnl
        
    pnl_today += unrealized_pnl
    pnl_3days += unrealized_pnl
    pnl_7days += unrealized_pnl
    win_rate = (win_trades_count / closed_trades_count * 100) if closed_trades_count > 0 else 0.0

    return {
        'category': target_category,
        'initial_capital': initial_capital,
        'current_equity': round(current_equity, 2),
        'cash_balance_thb': round(cash_balance_thb, 2),
        'invested_cash_thb': round(invested_cash_thb, 2),
        'total_pnl_thb': round(total_pnl_thb, 2),
        'total_pnl_pct': round(total_pnl_pct, 2),
        'pnl_today': round(pnl_today, 2),
        'pnl_yesterday': round(pnl_yesterday, 2),
        'pnl_3days': round(pnl_3days, 2),
        'pnl_7days': round(pnl_7days, 2),
        'realized_pnl_thb': round(realized_pnl, 2),
        'unrealized_pnl_thb': round(unrealized_pnl, 2),
        'cumulative_take_profit_thb': round(cumulative_take_profit_thb, 2),
        'cumulative_cut_loss_thb': round(cumulative_cut_loss_thb, 2),
        'closed_trades': closed_trades_count,
        'win_rate': round(win_rate, 1),
        'active_positions_detail': active_positions_detail
    }

def get_realtime_portfolio_pnl(initial_capital: float = 100000.0) -> dict:
    return get_system_pnl(target_category="STOCK", initial_capital=initial_capital)

def get_unified_portfolio_pnl() -> dict:
    """
    Computes Master Unified PnL across all 3 systems (Stock, Crypto, Forex).
    Total Initial Capital: 300,000 THB.
    """
    stock_pnl = get_system_pnl("STOCK", 100000.0)
    crypto_pnl = get_system_pnl("CRYPTO", 100000.0)
    forex_pnl = get_system_pnl("FOREX", 100000.0)
    
    total_initial = 300000.0
    total_equity = stock_pnl['current_equity'] + crypto_pnl['current_equity'] + forex_pnl['current_equity']
    total_cash = stock_pnl['cash_balance_thb'] + crypto_pnl['cash_balance_thb'] + forex_pnl['cash_balance_thb']
    total_invested = stock_pnl['invested_cash_thb'] + crypto_pnl['invested_cash_thb'] + forex_pnl['invested_cash_thb']
    total_pnl_thb = stock_pnl['total_pnl_thb'] + crypto_pnl['total_pnl_thb'] + forex_pnl['total_pnl_thb']
    total_pnl_pct = (total_pnl_thb / total_initial) * 100
    
    total_tp_thb = stock_pnl['cumulative_take_profit_thb'] + crypto_pnl['cumulative_take_profit_thb'] + forex_pnl['cumulative_take_profit_thb']
    total_cl_thb = stock_pnl['cumulative_cut_loss_thb'] + crypto_pnl['cumulative_cut_loss_thb'] + forex_pnl['cumulative_cut_loss_thb']
    
    all_active_positions = stock_pnl['active_positions_detail'] + crypto_pnl['active_positions_detail'] + forex_pnl['active_positions_detail']
    
    return {
        'total_initial': total_initial,
        'total_equity': round(total_equity, 2),
        'total_cash': round(total_cash, 2),
        'total_invested': round(total_invested, 2),
        'total_pnl_thb': round(total_pnl_thb, 2),
        'total_pnl_pct': round(total_pnl_pct, 2),
        'total_take_profit_thb': round(total_tp_thb, 2),
        'total_cut_loss_thb': round(total_cl_thb, 2),
        'stock_pnl': stock_pnl,
        'crypto_pnl': crypto_pnl,
        'forex_pnl': forex_pnl,
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
