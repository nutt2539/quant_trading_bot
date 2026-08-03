import requests
import os
from datetime import datetime
import config

# Optional Alpaca SDK import
try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce
    HAS_ALPACA_SDK = True
except ImportError:
    HAS_ALPACA_SDK = False

def send_telegram_notification(message: str, bot_token: str = None, chat_id: str = None) -> tuple:
    """
    Sends an instant push notification to Telegram Bot (100% Free & Unlimited).
    Returns (success_boolean, error_or_success_message).
    """
    token = bot_token or config.TELEGRAM_BOT_TOKEN or os.getenv("TELEGRAM_BOT_TOKEN")
    c_id = chat_id or config.TELEGRAM_CHAT_ID or os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not c_id:
        return False, "กรุณากรอกทั้ง Token และ Chat ID"
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": c_id, "text": message}
    try:
        res = requests.post(url, json=payload, timeout=8)
        if res.status_code == 200:
            return True, "ส่งข้อความเข้า Telegram สำเร็จ!"
        else:
            data = res.json()
            err_desc = data.get('description', '')
            if 'chat not found' in err_desc.lower() or 'forbidden' in err_desc.lower():
                return False, "กรุณาเปิดแอป Telegram ค้นหาชื่อบอทของคุณ แล้วกดปุ่ม START ก่อน!"
            return False, f"Telegram API Error: {err_desc}"
    except Exception as e:
        return False, f"Connection Error: {e}"

def send_discord_webhook(message: str, webhook_url: str = None) -> bool:
    """
    Sends an instant notification to Discord Channel via Webhook.
    """
    url = webhook_url or config.DISCORD_WEBHOOK_URL or os.getenv("DISCORD_WEBHOOK_URL")
    if not url:
        print(f"[ALERT NOTIFICATION (DISCORD NOT CONFIGURED)]: {message}")
        return False
        
    payload = {"content": message}
    try:
        res = requests.post(url, json=payload, timeout=8)
        return res.status_code == 200
    except Exception as e:
        print(f"Discord Webhook Error: {e}")
        return False

def send_instant_notification(message: str) -> bool:
    """
    Broadcasts message to Telegram and Discord channels.
    """
    t_ok, t_msg = send_telegram_notification(message)
    d_ok = send_discord_webhook(message)
    return t_ok or d_ok

def send_hourly_portfolio_summary() -> bool:
    """
    Sends a detailed Hourly Summary Report of all 3 systems (Stocks, Crypto, Forex) to Telegram.
    """
    from pnl_tracker import get_unified_portfolio_pnl
    from utils_tz import get_thai_now
    try:
        unified_pnl = get_unified_portfolio_pnl()
        now_str = get_thai_now().strftime('%H:%M น. (%d/%m/%Y)')
        
        total_eq = unified_pnl['total_equity']
        total_pnl = unified_pnl['total_pnl_thb']
        total_pct = unified_pnl['total_pnl_pct']
        pnl_sign = "+" if total_pnl >= 0 else ""
        pnl_icon = "🟢" if total_pnl >= 0 else "🔴"
        
        s_pnl = unified_pnl['thai_stock_pnl']
        us_pnl = unified_pnl['us_stock_pnl']
        c_pnl = unified_pnl['crypto_pnl']
        
        msg = f"📊 [QUANT AI - สรุปพอร์ตรวม 3 ระบบประจำชั่วโมง]\n"
        msg += f"⏰ เวลาอัปเดต: {now_str}\n"
        msg += f"-----------------------------------\n"
        msg += f"{pnl_icon} มูลค่าพอร์ตรวม 3 ระบบ: ฿{total_eq:,.2f}\n"
        msg += f"📈 กำไร/ขาดทุนรวม: {pnl_sign}฿{total_pnl:,.2f} ({pnl_sign}{total_pct:.2f}%)\n\n"
        
        # 1. Thai Stock System
        s_sign = "+" if s_pnl['total_pnl_thb'] >= 0 else ""
        msg += f"🇹🇭 [1. พอร์ตหุ้นไทย SET100 (ทุน ฿100,000)]\n"
        msg += f"• มูลค่าพอร์ต: ฿{s_pnl['current_equity']:,.2f}\n"
        msg += f"• เงินสดคงเหลือ: ฿{s_pnl['cash_balance_thb']:,.2f}\n"
        msg += f"• กำไร/ขาดทุน: {s_sign}฿{s_pnl['total_pnl_thb']:,.2f} ({s_sign}{s_pnl['total_pnl_pct']:.2f}%)\n"
        s_pos = s_pnl['active_positions_detail']
        if s_pos:
            holdings_str = ", ".join([f"{p['ชื่อสินทรัพย์']} ({p['กำไร/ขาดทุน (%)']})" for p in s_pos])
            msg += f"• ถือครอง ({len(s_pos)}): {holdings_str}\n"
        else:
            msg += f"• ถือครอง: ถือเงินสด 100%\n"
        msg += "\n"
        
        # 2. US Stock System (Transferred Forex capital)
        us_sign = "+" if us_pnl['total_pnl_thb'] >= 0 else ""
        msg += f"🇺🇸 [2. พอร์ตหุ้นอเมริกา US (ทุน ฿100,000 - ย้ายจาก Forex)]\n"
        msg += f"• มูลค่าพอร์ต: ฿{us_pnl['current_equity']:,.2f}\n"
        msg += f"• เงินสดคงเหลือ: ฿{us_pnl['cash_balance_thb']:,.2f}\n"
        msg += f"• กำไร/ขาดทุน: {us_sign}฿{us_pnl['total_pnl_thb']:,.2f} ({us_sign}{us_pnl['total_pnl_pct']:.2f}%)\n"
        us_pos = us_pnl['active_positions_detail']
        if us_pos:
            holdings_str = ", ".join([f"{p['ชื่อสินทรัพย์']} ({p['กำไร/ขาดทุน (%)']})" for p in us_pos])
            msg += f"• ถือครอง ({len(us_pos)}): {holdings_str}\n"
        else:
            msg += f"• ถือครอง: ถือเงินสด 100%\n"
        msg += "\n"

        # 3. Crypto System
        c_sign = "+" if c_pnl['total_pnl_thb'] >= 0 else ""
        msg += f"🪙 [3. พอร์ตคริปโทฯ 24/7 (ทุน ฿100,000)]\n"
        msg += f"• มูลค่าพอร์ต: ฿{c_pnl['current_equity']:,.2f}\n"
        msg += f"• เงินสดคงเหลือ: ฿{c_pnl['cash_balance_thb']:,.2f}\n"
        msg += f"• กำไร/ขาดทุน: {c_sign}฿{c_pnl['total_pnl_thb']:,.2f} ({c_sign}{c_pnl['total_pnl_pct']:.2f}%)\n"
        c_pos = c_pnl['active_positions_detail']
        if c_pos:
            holdings_str = ", ".join([f"{p['ชื่อสินทรัพย์']} ({p['กำไร/ขาดทุน (%)']})" for p in c_pos])
            msg += f"• ถือครอง ({len(c_pos)}): {holdings_str}\n"
        else:
            msg += f"• ถือครอง: ถือเงินสด 100%\n"
            
        return send_instant_notification(msg)
    except Exception as e:
        print(f"Error sending hourly portfolio summary: {e}")
        return False

def fetch_alpaca_positions() -> list:
    """
    Fetches real-time positions from Alpaca Paper Trading API.
    """
    api_key = config.ALPACA_API_KEY or os.getenv("ALPACA_API_KEY")
    secret_key = config.ALPACA_SECRET_KEY or os.getenv("ALPACA_SECRET_KEY")
    
    if not HAS_ALPACA_SDK or not api_key or not secret_key:
        return []
        
    try:
        trading_client = TradingClient(api_key, secret_key, paper=True)
        positions = trading_client.get_all_positions()
        pos_list = []
        for p in positions:
            pos_list.append({
                "symbol": p.symbol,
                "qty": float(p.qty),
                "avg_entry_price": float(p.avg_entry_price),
                "current_price": float(p.current_price),
                "market_value": float(p.market_value),
                "unrealized_pl": float(p.unrealized_pl),
                "unrealized_plpc": float(p.unrealized_plpc) * 100
            })
        return pos_list
    except Exception as e:
        print(f"Alpaca Positions API Error: {e}")
        return []

def execute_alpaca_trade(symbol: str, qty: float, side: str = "buy") -> dict:
    """
    Executes Market Order trade via Alpaca API.
    """
    api_key = config.ALPACA_API_KEY or os.getenv("ALPACA_API_KEY")
    secret_key = config.ALPACA_SECRET_KEY or os.getenv("ALPACA_SECRET_KEY")
    
    if not HAS_ALPACA_SDK or not api_key or not secret_key:
        msg = f"⚠️ [PAPER SIMULATION] สั่งซื้อขาย {side.upper()} {symbol} จำนวน {qty} หน่วย (โหมดจำลอง)"
        send_instant_notification(msg)
        return {"status": "simulated", "message": msg}
        
    try:
        trading_client = TradingClient(api_key, secret_key, paper=True)
        order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
        order_data = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=order_side,
            time_in_force=TimeInForce.DAY
        )
        order = trading_client.submit_order(request_parameters=order_data)
        msg = f"🚀 [ALPACA EXECUTED] สั่งคำสั่ง {side.upper()} {symbol} จำนวน {qty} หน่วยสำเร็จ! (ID: {order.id})"
        send_instant_notification(msg)
        return {"status": "executed", "order_id": str(order.id), "message": msg}
    except Exception as e:
        err_msg = f"❌ [ALPACA ERROR] ไม่สามารถส่งคำสั่ง {side.upper()} {symbol}: {e}"
        send_instant_notification(err_msg)
        return {"status": "error", "message": str(e)}
