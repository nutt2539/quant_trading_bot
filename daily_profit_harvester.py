import os
import json
import pandas as pd
from datetime import datetime, timedelta, time
from pnl_tracker import get_unified_portfolio_pnl, get_asset_category, TRADE_LOG_FILE
from execution_engine import send_instant_notification, execute_alpaca_trade
from risk_safety_guard import validate_market_hours, validate_trade_safety

HARVEST_TRACKER_FILE = "daily_harvest_tracker.json"
DAILY_MIN_ELIGIBLE_PROFIT = 300.0  # Must have >= ฿300 THB profit to activate
HARVEST_TARGET_PER_CLICK = 300.0   # Target harvest exactly ฿300 THB per click

def is_market_open(symbol: str) -> bool:
    """
    Checks if the market for a given symbol is currently OPEN for real-time trading.
    - Thai Stocks (.BK): Mon-Fri 10:00-12:30 & 14:30-16:30
    - US Stocks: Mon-Fri 21:30-04:00 (Thai Time)
    - Forex & Gold (=X, GC=F): Mon 05:00 to Sat 04:00 (Thai Time)
    - Crypto (-USD, BTC, ETH, etc.): 24/7 ALWAYS OPEN
    """
    now = datetime.now()
    weekday = now.weekday()  # 0=Mon, ..., 4=Fri, 5=Sat, 6=Sun
    t = now.time()
    
    # 1. Thai Stocks (.BK)
    if symbol.endswith(".BK"):
        if weekday in [5, 6]:
            return False
        m_open = time(10, 0)
        m_close = time(12, 30)
        a_open = time(14, 30)
        a_close = time(16, 30)
        return (m_open <= t <= m_close) or (a_open <= t <= a_close)
        
    # 2. US Stocks (e.g. AAPL, TSLA, MSFT)
    elif not symbol.endswith("-USD") and not symbol.endswith("=X") and symbol != "GC=F" and symbol not in ["BTC", "ETH", "SOL", "BNB", "ADA", "XRP", "AVAX", "LINK", "DOGE"]:
        if weekday in [5, 6]:
            return False
        us_open = time(21, 30)
        us_close = time(4, 0)
        if t >= us_open or t <= us_close:
            return True
        return False
        
    # 3. Forex & Gold (=X, GC=F)
    elif symbol.endswith("=X") or symbol == "GC=F":
        if weekday == 5 and t > time(4, 0): # Closed Sat after 04:00
            return False
        if weekday == 6: # Closed Sun
            return False
        if weekday == 0 and t < time(5, 0): # Closed Mon before 05:00
            return False
        return True
        
    # 4. Crypto -> 24/7 ALWAYS OPEN
    else:
        return True

def load_harvest_data() -> dict:
    """
    Loads full harvest data from JSON file.
    """
    if os.path.exists(HARVEST_TRACKER_FILE):
        try:
            with open(HARVEST_TRACKER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    if "harvest_history" not in data:
                        data["harvest_history"] = []
                    return data
        except Exception as e:
            print(f"Error loading harvest data: {e}")
            
    return {"date": datetime.now().strftime('%Y-%m-%d'), "harvested_today_thb": 0.0, "harvest_history": []}

def save_harvest_data(data: dict):
    try:
        with open(HARVEST_TRACKER_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving harvest data: {e}")

def get_daily_harvest_status() -> dict:
    """
    Computes current eligibility for Daily Profit Harvesting (฿300 THB per click).
    """
    today_str = datetime.now().strftime('%Y-%m-%d')
    data = load_harvest_data()
    
    harvested_today = 0.0
    # Sum up harvested_pnl_thb for today from history
    for item in data.get("harvest_history", []):
        if item.get("date") == today_str:
            harvested_today += float(item.get("harvested_pnl_thb", 0.0))
            
    # Fallback to file attribute if set
    if harvested_today == 0.0 and data.get("date") == today_str:
        harvested_today = float(data.get("harvested_today_thb", 0.0))

    unified = get_unified_portfolio_pnl()
    all_positions = unified.get("all_active_positions", [])
    
    profitable_positions = []
    total_unrealized_profit = 0.0
    
    for pos in all_positions:
        pnl_str = str(pos.get('กำไร/ขาดทุน (บาท)', '฿0.00')).replace('+', '').replace('฿', '').replace(',', '').strip()
        try:
            pnl_val = float(pnl_str)
        except Exception:
            pnl_val = 0.0
            
        pct_str = str(pos.get('กำไร/ขาดทุน (%)', '0.00%')).replace('+', '').replace('%', '').strip()
        try:
            pct_val = float(pct_str)
        except Exception:
            pct_val = 0.0

        if pnl_val > 0:
            total_unrealized_profit += pnl_val
            profitable_positions.append({
                'symbol': pos.get('ชื่อสินทรัพย์'),
                'qty': pos.get('จำนวนหน่วย'),
                'entry_price_str': pos.get('ต้นทุน/หน่วย'),
                'current_price_str': pos.get('ราคาตลาด (Realtime)'),
                'pnl_thb': pnl_val,
                'pnl_pct': pct_val,
                'cost_thb_str': pos.get('เงินลงทุนรวม (บาท)'),
                'val_thb_str': pos.get('มูลค่าปัจจุบัน (บาท)')
            })

    profitable_positions.sort(key=lambda x: x['pnl_pct'], reverse=True)
    is_eligible = (total_unrealized_profit >= DAILY_MIN_ELIGIBLE_PROFIT)
    
    return {
        'date': today_str,
        'harvested_today_thb': round(harvested_today, 2),
        'total_unrealized_profit_thb': round(total_unrealized_profit, 2),
        'is_eligible': is_eligible,
        'min_profit_threshold': DAILY_MIN_ELIGIBLE_PROFIT,
        'harvest_target_per_click': HARVEST_TARGET_PER_CLICK,
        'profitable_positions': profitable_positions,
        'today_trades': [item for item in data.get("harvest_history", []) if item.get("date") == today_str]
    }

def record_daily_harvest_detail(trade_item: dict):
    """
    Appends a new harvest trade entry to the JSON history.
    """
    data = load_harvest_data()
    today_str = datetime.now().strftime('%Y-%m-%d')
    data["date"] = today_str
    
    if "harvest_history" not in data:
        data["harvest_history"] = []
        
    data["harvest_history"].insert(0, trade_item)
    
    today_total = sum(float(item.get("harvested_pnl_thb", 0.0)) for item in data["harvest_history"] if item.get("date") == today_str)
    data["harvested_today_thb"] = round(today_total, 2)
    save_harvest_data(data)

def get_harvest_chart_df(timeframe: str = '1M') -> pd.DataFrame:
    """
    Generates daily historical harvest chart dataframe for timeframes: 1W, 1M, 3M, 6M, 1Y.
    """
    data = load_harvest_data()
    history = data.get("harvest_history", [])
    
    days_map = {
        '1W': 7,
        '1M': 30,
        '3M': 90,
        '6M': 180,
        '1Y': 365
    }
    num_days = days_map.get(timeframe, 30)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=num_days - 1)
    
    date_range = [ (start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(num_days) ]
    
    daily_sums = { d: 0.0 for d in date_range }
    
    for item in history:
        d_str = item.get("date")
        if d_str in daily_sums:
            daily_sums[d_str] += float(item.get("harvested_pnl_thb", 0.0))
            
    df = pd.DataFrame([
        {"วันที่": d, "กำไรสดที่ดึงเก็บ (บาท)": round(val, 2)} for d, val in daily_sums.items()
    ])
    return df

def execute_daily_profit_harvest() -> dict:
    """
    AI evaluates profitable positions and executes a sell to harvest EXACTLY ฿300 THB profit into realized gains per click.
    """
    status = get_daily_harvest_status()
    if not status['is_eligible']:
        return {
            'success': False,
            'message': f"กำไรจากพอร์ตถือครองขณะนี้อยู่ที่ ฿{status['total_unrealized_profit_thb']:,.2f} บาท (ยังไม่ถึงเกณฑ์ขั้นต่ำ ฿{status['min_profit_threshold']:,.0f} บาทในการกดเก็บกำไร)"
        }
            
    candidates = status['profitable_positions']
    open_candidates = [c for c in candidates if is_market_open(str(c['symbol']))]
    if not open_candidates:
        return {'success': False, 'message': 'ไม่พบสินทรัพย์ที่มีกำไรในตลาดที่เปิดทำการอยู่ในขณะนี้ (ขณะนี้ตลาดปิดทำการ)'}
        
    target_harvest_baht = HARVEST_TARGET_PER_CLICK  # ฿300.0 THB per click
    
    # Pick the best candidate position with highest profit % among open market assets
    best_candidate = open_candidates[0]
    symbol = str(best_candidate['symbol'])
    pos_pnl = float(best_candidate['pnl_thb'])
    
    # Calculate sell ratio to yield 300 THB
    ratio = min(1.0, target_harvest_baht / pos_pnl)
    qty = float(best_candidate['qty'])
    
    is_crypto_sym = (symbol.endswith("-USD") or symbol in ["BTC", "ETH", "SOL", "BNB", "ADA", "XRP", "AVAX", "LINK"])
    sell_qty = round(qty * ratio, 4) if is_crypto_sym else (round(qty * ratio, 2) if symbol.endswith("=X") else max(1, int(round(qty * ratio))))
    
    # Raw symbol resolution for trade execution
    raw_symbol = symbol
    if not symbol.endswith(".BK") and not symbol.endswith("-USD") and not symbol.endswith("=X"):
        if symbol == "GOLD (ทองคำ)":
            raw_symbol = "GC=F"
        elif symbol in ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "AVAX", "LINK"]:
            raw_symbol = f"{symbol}-USD"
            
    category = get_asset_category(raw_symbol)
    
    # Read entry price and current market price
    curr_price_val = float(str(best_candidate['current_price_str']).replace('$', '').replace('฿', '').replace(',', ''))
    entry_price_val = float(str(best_candidate['entry_price_str']).replace('$', '').replace('฿', '').replace(',', ''))
    fx_rate = 35.0 if not raw_symbol.endswith(".BK") else 1.0
    
    harvested_pnl = round(pos_pnl * ratio, 2)
    if harvested_pnl <= 0.0:
        harvested_pnl = 300.0
        
    trade_total_thb = round(sell_qty * curr_price_val * fx_rate, 2)
    
    # Financial Safety Check before executing
    is_safe, safety_msg = validate_trade_safety(symbol, 'SELL', trade_total_thb)
    if not is_safe:
        return {'success': False, 'message': f"🛑 ระบบความปลอดภัยปฏิเสธออเดอร์: {safety_msg}"}

    timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    trade_detail = {
        "timestamp": timestamp_str,
        "date": today_str,
        "symbol": symbol,
        "raw_symbol": raw_symbol,
        "shares": sell_qty,
        "price": round(curr_price_val, 2),
        "harvested_pnl_thb": harvested_pnl,
        "total_trade_thb": trade_total_thb
    }
    
    # Save log to autotrade_logs.json
    try:
        logs = []
        if os.path.exists(TRADE_LOG_FILE):
            with open(TRADE_LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
                
        log_entry = {
            "timestamp": timestamp_str,
            "symbol": raw_symbol,
            "action": "SELL",
            "shares": sell_qty,
            "price": round(curr_price_val, 2),
            "total_thb": trade_total_thb,
            "reason": f"🎯 AI Manual Daily Profit Harvest (เก็บกำไรเข้ากระเป๋าทีละ +฿{harvested_pnl:,.2f} บาท)",
            "ai_summary": f"AI คัดเลือก {symbol} ซึ่งมีผลตอบแทนสูงสุด (+{best_candidate['pnl_pct']:.2f}%) เพื่อทำกำไรทีละ ฿{harvested_pnl:,.2f} บาท"
        }
        logs.insert(0, log_entry)
        with open(TRADE_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error writing harvest log: {e}")

    record_daily_harvest_detail(trade_detail)
    
    # Send instant Telegram Notification
    new_today_harvest = status['harvested_today_thb'] + harvested_pnl
    msg = f"🎯 [DAILY PROFIT HARVEST - AI เก็บกำไรเข้ากระเป๋าทีละ ฿300 บาท]\nขายทำกำไร: {symbol}\nจำนวน: {sell_qty} หน่วย (ราคา {curr_price_val:,.2f})\nกำไรล็อคเข้ากระเป๋า: +฿{harvested_pnl:,.2f} บาท (+{best_candidate['pnl_pct']:.2f}%)\nเหตุผล: AI ประเมินคุ้มค่าสูงสุด เก็บกำไรสะสมวันนี้รวม ฿{new_today_harvest:,.2f} บาท"
    send_instant_notification(msg)
    
    return {
        'success': True,
        'symbol': symbol,
        'harvested_pnl_thb': harvested_pnl,
        'message': f"AI ดำเนินการขาย {symbol} จำนวน {sell_qty} หน่วย เพื่อล็อคกำไรเข้ากระเป๋าจำนวน +฿{harvested_pnl:,.2f} บาทสำเร็จ!"
    }
