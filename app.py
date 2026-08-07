import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import importlib

import config
import data_loader
import strategies.swing_strategy as swing
import ai_analyst
import execution_engine
import pnl_tracker
import autotrader_daemon
import daily_profit_harvester
import backtester_engine
import multi_timeframe_analyzer
import volatility_engine
import kelly_position_sizer
import macro_calendar_guard
import robot_control
from broker_bridge.broker_manager import get_broker_mode, set_broker_mode
import broker_credentials_manager as bcm
from utils_tz import get_thai_now_naive, get_thai_str
import keep_alive
import server_heartbeat_guard

keep_alive.init_keep_alive()
server_heartbeat_guard.init_server_guard()
autotrader_daemon.init_autotrader_background_loop()

importlib.reload(config)
importlib.reload(data_loader)
importlib.reload(swing)
importlib.reload(ai_analyst)
importlib.reload(execution_engine)
importlib.reload(pnl_tracker)
importlib.reload(autotrader_daemon)
importlib.reload(daily_profit_harvester)
importlib.reload(backtester_engine)
importlib.reload(multi_timeframe_analyzer)
importlib.reload(volatility_engine)
importlib.reload(kelly_position_sizer)
importlib.reload(macro_calendar_guard)
importlib.reload(robot_control)

from data_loader import fetch_stock_data
from strategies.swing_strategy import (
    STRATEGY_DETAILS, ai_recommend_strategy,
    get_active_strategy, set_active_strategy, get_all_active_strategies, get_custom_strategy_params, save_custom_strategy_params
)
from strategies.quant_strategy_library import generate_quant_signal
from ai_analyst import analyze_stock_sentiment
from execution_engine import send_telegram_notification
from pnl_tracker import get_system_pnl, get_unified_portfolio_pnl, get_daily_market_summary, get_closed_trades_breakdown
from daily_profit_harvester import get_daily_harvest_status, execute_daily_profit_harvest, get_harvest_chart_df
from backtester_engine import run_historical_backtest
from multi_timeframe_analyzer import analyze_multi_timeframe
from volatility_engine import get_dynamic_tp_sl
from kelly_position_sizer import calculate_kelly_allocation
from macro_calendar_guard import is_macro_event_near
from robot_control import get_robot_status, set_robot_status, execute_force_sell

# Streamlit Page Config
st.set_page_config(
    page_title="QUANT AI | ศูนย์รวมระบบเทรดอัจฉริยะ 3 สินทรัพย์",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session State for Active System Navigation, Active Strategy & Theme Mode
if "active_system" not in st.session_state:
    st.session_state.active_system = "UNIFIED"
    
if "current_active_strategy" not in st.session_state:
    st.session_state.current_active_strategy = get_active_strategy()
    
if "pending_strategy_modal" not in st.session_state:
    st.session_state.pending_strategy_modal = None

if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "DARK"

# Interactive Strategy Confirmation Modal Pop-up
if hasattr(st, 'dialog'):
    @st.dialog("🎯 ยืนยันการเลือกกลยุทธ์การเทรด (Strategy Confirmation)")
    def show_strategy_dialog(strategy_key):
        info = config.STRATEGY_CATALOG.get(strategy_key, config.STRATEGY_CATALOG["TREND_FOLLOWING"])
        st.markdown(f"### {info.get('icon', '⚙️')} {info['name']}")
        st.markdown(f"**ระดับความเสี่ยง:** `{info.get('risk_level', 'ปานกลาง')}`")
        st.markdown(f"**คำอธิบายกลยุทธ์:** {info['desc']}")
        st.markdown("---")
        
        col_pro, col_con = st.columns(2)
        with col_pro:
            st.markdown(f"<div style='background:rgba(16, 185, 129, 0.2); padding:14px; border-radius:12px; border:1px solid rgba(16, 185, 129, 0.5);'><h4 style='color:#34d399; margin:0;'>✅ ข้อดี (Pros)</h4>{info.get('pros', 'ทำกำไรตามระบบ')}</div>", unsafe_allow_html=True)
        with col_con:
            st.markdown(f"<div style='background:rgba(239, 68, 68, 0.2); padding:14px; border-radius:12px; border:1px solid rgba(239, 68, 68, 0.5);'><h4 style='color:#f87171; margin:0;'>⚠️ ข้อเสีย / ความเสี่ยง (Cons)</h4>{info.get('cons', 'ต้องควบคุมความเสี่ยงอย่างเคร่งครัด')}</div>", unsafe_allow_html=True)
            
        st.markdown("---")
        col_c1, col_c2 = st.columns([1, 1])
        with col_c1:
            if st.button("🚀 ยืนยันนำกลยุทธ์นี้ไปปรับใช้จริง (Confirm & Apply)", use_container_width=True):
                set_active_strategy(strategy_key)
                st.session_state.current_active_strategy = strategy_key
                st.session_state.pending_strategy_modal = None
                st.success(f"ปรับเปลี่ยนเป็น {info['name']} เรียบร้อยแล้ว!")
                st.rerun()
        with col_c2:
            if st.button("❌ ยกเลิก (Cancel)", use_container_width=True):
                st.session_state.pending_strategy_modal = None
                st.rerun()

    @st.dialog("🎯 ที่มาการคำนวณ Take Profit สะสม (Cumulative Take Profit)")
    def show_tp_dialog():
        st.markdown("### 📋 รายละเอียดออเดอร์ปิดทำกำไรสำเร็จจาก AI")
        st.info("💡 **สูตรการคำนวณ:** คิดเฉพาะผลรวมกำไรสุทธิ (บาท) จากออเดอร์ที่ **ระบบ AI ตัดสินใจและสั่งขายทำกำไรอัตโนมัติ** เท่านั้น (Closed AI Take-Profit Trades) *ไม่เอายอดกดเก็บกำไร Manual รายวันมารวม*")
        
        bd = get_closed_trades_breakdown()
        tp_trades = bd.get('take_profit_trades', [])
        
        if tp_trades:
            df_tp = pd.DataFrame(tp_trades)
            df_tp = df_tp.rename(columns={
                'timestamp': 'วันเวลาทำรายการ',
                'symbol': 'สินทรัพย์',
                'category': 'หมวด',
                'shares': 'จำนวนขาย',
                'buy_price': 'ต้นทุน/หน่วย',
                'sell_price': 'ราคาขาย',
                'trade_pnl_thb': 'กำไรสุทธิ (บาท)',
                'pnl_pct': 'กำไร (%)',
                'reason': 'เหตุผลการขาย'
            })
            display_cols = ['วันเวลาทำรายการ', 'สินทรัพย์', 'หมวด', 'จำนวนขาย', 'ต้นทุน/หน่วย', 'ราคาขาย', 'กำไรสุทธิ (บาท)', 'กำไร (%)', 'เหตุผลการขาย']
            st.dataframe(df_tp[[c for c in display_cols if c in df_tp.columns]], use_container_width=True)
            
            total_tp = sum(t['trade_pnl_thb'] for t in tp_trades)
            st.success(f"💰 **รวมกำไร Take Profit ทั้งหมดที่ล็อคเข้ากระเป๋า:** +฿{total_tp:,.2f} บาท (จาก {len(tp_trades)} ออเดอร์)")
        else:
            st.warning("ยังไม่มีรายการออเดอร์ที่ปิดขายทำกำไรสำเร็จ")

    @st.dialog("🛑 ที่มาการคำนวณ Cut-Loss สะสม (Cumulative Cut-Loss)")
    def show_cl_dialog():
        st.markdown("### 📋 รายละเอียดออเดอร์ปิดขาดทุนทั้งหมด")
        st.info("💡 **สูตรการคำนวณ:** ผลรวมขาดทุน (บาท) จากทุกออเดอร์ที่ตัดขาดทุนตามระดับ Stop-Loss หรือ AI ประเมินขายลดความเสี่ยงพอร์ต (Closed Loss Trades)")
        
        bd = get_closed_trades_breakdown()
        cl_trades = bd.get('cut_loss_trades', [])
        
        if cl_trades:
            df_cl = pd.DataFrame(cl_trades)
            df_cl = df_cl.rename(columns={
                'timestamp': 'วันเวลาทำรายการ',
                'symbol': 'สินทรัพย์',
                'category': 'หมวด',
                'shares': 'จำนวนขาย',
                'buy_price': 'ต้นทุน/หน่วย',
                'sell_price': 'ราคาขาย Cut-Loss',
                'trade_pnl_thb': 'ยอดขาดทุน (บาท)',
                'pnl_pct': 'ขาดทุน (%)',
                'reason': 'เหตุผลการขาย'
            })
            display_cols = ['วันเวลาทำรายการ', 'สินทรัพย์', 'หมวด', 'จำนวนขาย', 'ต้นทุน/หน่วย', 'ราคาขาย Cut-Loss', 'ยอดขาดทุน (บาท)', 'ขาดทุน (%)', 'เหตุผลการขาย']
            st.dataframe(df_cl[[c for c in display_cols if c in df_cl.columns]], use_container_width=True)
            
            total_cl = sum(t['trade_pnl_thb'] for t in cl_trades)
            st.error(f"🛑 **รวมยอด Cut-Loss ทั้งหมด:** -฿{total_cl:,.2f} บาท (จาก {len(cl_trades)} ออเดอร์)")
        else:
            st.info("🎉 **ยอดเยี่ยมมาก!** ขณะนี้ยังไม่มีรายการ Cut-Loss ขาดทุนเลยแม้แต่ออเดอร์เดียว (0 รายการ)")

# Market Badges Helper
def check_thai_market_status(now_dt):
    if now_dt.weekday() in [5, 6]: return "🔴 🇹🇭 หุ้นไทย: ปิดทำการ"
    time_now = now_dt.time()
    morning_open = datetime.strptime("10:00", "%H:%M").time()
    morning_close = datetime.strptime("12:30", "%H:%M").time()
    afternoon_open = datetime.strptime("14:30", "%H:%M").time()
    afternoon_close = datetime.strptime("16:30", "%H:%M").time()
    if morning_open <= time_now <= morning_close: return "🟢 🇹🇭 หุ้นไทย: เปิดช่วงเช้า"
    elif morning_close < time_now < afternoon_open: return "🟡 🇹🇭 หุ้นไทย: พักเที่ยง"
    elif afternoon_open <= time_now <= afternoon_close: return "🟢 🇹🇭 หุ้นไทย: เปิดช่วงบ่าย"
    else: return "🔴 🇹🇭 หุ้นไทย: ปิดทำการ"

def check_us_market_status(now_dt):
    time_now = now_dt.time()
    us_open = datetime.strptime("20:30", "%H:%M").time()
    us_close = datetime.strptime("03:00", "%H:%M").time()
    weekday = now_dt.weekday()
    is_us_open = (weekday in [0, 1, 2, 3, 4] and time_now >= us_open) or (weekday in [1, 2, 3, 4, 5] and time_now <= us_close)
    return "🟢 🇺🇸 หุ้นสหรัฐฯ: เปิดทำการ" if is_us_open else "🔴 🇺🇸 หุ้นสหรัฐฯ: ปิดทำการ"

def check_crypto_market_status(): return "🟢 🪙 คริปโทฯ: เปิด 24/7"

def check_forex_market_status(now_dt):
    weekday = now_dt.weekday()
    time_now = now_dt.time()
    if weekday == 5 and time_now >= datetime.strptime("05:00", "%H:%M").time(): return "🔴 💱 Forex/ทองคำ: ปิดทำการ"
    elif weekday == 6: return "🔴 💱 Forex/ทองคำ: ปิดทำการ"
    elif weekday == 0 and time_now < datetime.strptime("05:00", "%H:%M").time(): return "🔴 💱 Forex/ทองคำ: ปิดทำการ"
    else: return "🟢 💱 Forex/ทองคำ: เปิด 24/5"

# ==================== MODERN ABSTRACT GRAPHIC SIDEBAR & THEME TOGGLE ====================
st.sidebar.markdown("### ⚡ QUANT AI SYSTEM SELECTOR")
st.sidebar.caption("คลิกเลือกเปิดดูระบบการเทรดที่ต้องการ (ทุนรวม ฿300,000):")

b1 = st.sidebar.button("🌐 ศูนย์กลางรวม 4 ระบบ\n(Master Command Center - ฿300k)", use_container_width=True)
b2 = st.sidebar.button("🇺🇸 ดัชนีหุ้นสหรัฐฯ\n(S&P 500 / NASDAQ - ฿100k)", use_container_width=True)
b3 = st.sidebar.button("🥇 บอททองคำ\n(Gold Bot - ฿90k)", use_container_width=True)
b4 = st.sidebar.button("🪙 บอท Crypto Spot\n(24/7 Crypto Bot - ฿80k)", use_container_width=True)
b5 = st.sidebar.button("💱 บอท Forex\n(24/5 Forex Bot - ฿30k)", use_container_width=True)
b6 = st.sidebar.button("🔑 ตั้งค่า Broker API Keys\n(Live Credentials Center)", use_container_width=True)

if b1: st.session_state.active_system = "UNIFIED"
elif b2: st.session_state.active_system = "US_INDEX"
elif b3: st.session_state.active_system = "GOLD"
elif b4: st.session_state.active_system = "CRYPTO"
elif b5: st.session_state.active_system = "FOREX"
elif b6: st.session_state.active_system = "BROKER_CONFIG"

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ กลยุทธ์รันแยกรายสินทรัพย์ (Active Strategies):")
all_strats = get_all_active_strategies()
us_strat_name = config.STRATEGY_CATALOG.get(all_strats.get("US_INDEX"), {}).get("name", "Trend Following")
gold_strat_name = config.STRATEGY_CATALOG.get(all_strats.get("GOLD"), {}).get("name", "Mean Reversion")
crypto_strat_name = config.STRATEGY_CATALOG.get(all_strats.get("CRYPTO"), {}).get("name", "Volatility Breakout")
forex_strat_name = config.STRATEGY_CATALOG.get(all_strats.get("FOREX"), {}).get("name", "Grid Trading")

sidebar_strat_html = f"""
<div style="font-size:0.78rem; background:rgba(255,255,255,0.06); padding:10px 12px; border-radius:10px; border:1px solid rgba(255,255,255,0.12); margin-bottom:10px;">
    <div style="margin-bottom:6px;">🇺🇸 <strong>US Index:</strong><br><span style="color:#38bdf8; font-weight:700;">{us_strat_name}</span></div>
    <div style="margin-bottom:6px;">🥇 <strong>Gold Bot:</strong><br><span style="color:#f59e0b; font-weight:700;">{gold_strat_name}</span></div>
    <div style="margin-bottom:6px;">🪙 <strong>Crypto Spot:</strong><br><span style="color:#10b981; font-weight:700;">{crypto_strat_name}</span></div>
    <div>💱 <strong>Forex Bot:</strong><br><span style="color:#a855f7; font-weight:700;">{forex_strat_name}</span></div>
</div>
"""
st.sidebar.markdown(sidebar_strat_html, unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### ☀️/🌙 ธีมหน้าเว็บ (Theme Mode)")
theme_choice = st.sidebar.radio(
    "เลือกโหมดการแสดงผล:",
    ["☀️ Light Mode (โหมดสว่าง - Default)", "🌙 Dark Mode (โหมดมืด)"],
    index=0 if st.session_state.theme_mode == "LIGHT" else 1
)

if "Light" in theme_choice:
    st.session_state.theme_mode = "LIGHT"
    app_bg = "linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #f1f5f9 100%)"
    app_text = "#0f172a"
    sidebar_bg = "linear-gradient(165deg, #ffffff 0%, #f8fafc 50%, #e2e8f0 100%)"
    glass_card_bg = "rgba(255, 255, 255, 0.92)"
    glass_card_border = "1px solid rgba(0, 0, 0, 0.12)"
    title_color = "#0f172a"
    metric_card_bg = "linear-gradient(145deg, #ffffff, #f1f5f9)"
    metric_label_color = "#334155"
    tab_list_bg = "rgba(226, 232, 240, 0.9)"
    plotly_template = "plotly_white"
else:
    st.session_state.theme_mode = "DARK"
    app_bg = "radial-gradient(circle at 15% 15%, #0f172a 0%, #090d16 50%, #020617 100%)"
    app_text = "#f8fafc"
    sidebar_bg = "linear-gradient(165deg, rgba(15, 23, 42, 0.98) 0%, rgba(30, 27, 75, 0.98) 50%, rgba(15, 23, 42, 1.0))"
    glass_card_bg = "rgba(15, 23, 42, 0.75)"
    glass_card_border = "1px solid rgba(255, 255, 255, 0.15)"
    title_color = "#ffffff"
    metric_card_bg = "linear-gradient(145deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.95))"
    metric_label_color = "#cbd5e1"
    tab_list_bg = "rgba(15, 23, 42, 0.8)"
    plotly_template = "plotly_dark"

st.sidebar.markdown("---")
st.sidebar.markdown("### 🏦 สภาพแวดล้อม Broker (Environment)")
curr_b_mode = get_broker_mode()
b_mode_choice = st.sidebar.radio(
    "เลือกสลับโหมดบัญชี:",
    ["📝 PAPER TRADING (พอร์ตจำลองกระดาษ)", "🟢 LIVE BROKER API (เงินจริง 100%)"],
    index=0 if curr_b_mode == "PAPER" else 1
)

target_b_mode = "PAPER" if "PAPER" in b_mode_choice else "LIVE"
if target_b_mode != curr_b_mode:
    ok_b, msg_b = set_broker_mode(target_b_mode)
    if ok_b:
        st.sidebar.success(msg_b)
        st.rerun()

# Dynamic CSS Injector
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Plus Jakarta Sans', sans-serif;
    }}
    
    .stApp {{
        background: {app_bg} !important;
        color: {app_text} !important;
    }}
    
    .stDeployButton {{display:none;}}
    div[data-testid="stDecoration"] {{display:none;}}
    
    /* Strict Theme Control - Overrides OS System Theme 100% */
    h1, h2, h3, h4, h5, h6, p, span, label, div[data-testid="stMarkdownContainer"] p {{
        color: {app_text} !important;
    }}
    
    /* Hero Title Holographic Gradient Styling */
    .hero-title {{
        font-family: 'Outfit', 'Plus Jakarta Sans', sans-serif !important;
        font-size: 2.3rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px !important;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 40%, #c084fc 80%, #f472b6 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        margin-bottom: 12px !important;
        text-shadow: 0 0 30px rgba(56, 189, 248, 0.2) !important;
    }}
    
    [data-testid="stSidebar"] {{
        background: {sidebar_bg} !important;
        backdrop-filter: blur(30px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 10px 0 35px rgba(0, 0, 0, 0.35) !important;
    }}
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {{
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        font-size: 1.15rem !important;
        letter-spacing: 0.3px !important;
    }}
    
    div.stButton > button {{
        background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        border-radius: 14px !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        padding: 11px 18px !important;
        box-shadow: 0 4px 20px rgba(37, 99, 235, 0.35) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        line-height: 1.4 !important;
    }}
    
    div.stButton > button * {{
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
    }}
    
    div.stButton > button:hover {{
        background: linear-gradient(135deg, #1d4ed8 0%, #4338ca 100%) !important;
        border-color: #38bdf8 !important;
        box-shadow: 0 8px 25px rgba(56, 189, 248, 0.5) !important;
        transform: translateY(-2px) scale(1.01) !important;
    }}

    [data-testid="stSidebar"] div.stButton > button {{
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.85), rgba(15, 23, 42, 0.95)) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.3) !important;
    }}
    
    .glass-card {{
        background: {glass_card_bg} !important;
        backdrop-filter: blur(24px) saturate(180%) !important;
        border: {glass_card_border} !important;
        border-radius: 22px !important;
        padding: 22px 26px !important;
        margin-bottom: 22px !important;
        box-shadow: 0 20px 45px rgba(0, 0, 0, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
    }}
    
    .metric-card {{
        background: {metric_card_bg} !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 18px !important;
        padding: 18px !important;
        text-align: center !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2) !important;
        transition: transform 0.25s ease !important;
    }}
    .metric-card:hover {{
        transform: translateY(-3px) !important;
    }}
    .metric-label {{
        color: {metric_label_color} !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        gap: 12px; background-color: {tab_list_bg} !important; padding: 8px; border-radius: 18px; border: 1px solid rgba(255, 255, 255, 0.1);
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 48px; border-radius: 14px; color: {metric_label_color} !important; font-weight: 700; padding: 0px 22px; transition: all 0.25s ease;
    }}
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%) !important; color: #ffffff !important; box-shadow: 0 4px 20px rgba(37, 99, 235, 0.4) !important;
    }}
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔄 อัปเดตข้อมูลตัวเลขสดอัตโนมัติ (Live Numbers Auto-Refresh)")
st.sidebar.caption("⚡ ระบบเปิดใช้งาน Auto-Refresh **เฉพาะการ์ดตัวเลขทางการเงิน** ให้โดยอัตโนมัติทุกๆ 15 วินาที (ผ่าน Streamlit Fragment) โดย **ไม่รีเฟรชทั้งหน้าเว็บ** จึงไม่ขัดจังหวะการพิมพ์หรือการเลือกเมนูของคุณ")

# Cache AI Strategy Recommendation to keep UI snappy (60s TTL)
@st.cache_data(ttl=60)
def get_cached_ai_recommendation(symbol: str = "BTC-USD"):
    return ai_recommend_strategy(symbol)

now_dt = get_thai_now_naive()
now_str = now_dt.strftime('%H:%M:%S น.')

# Trigger Pending Dialog if needed
if st.session_state.pending_strategy_modal and hasattr(st, 'dialog'):
    show_strategy_dialog(st.session_state.pending_strategy_modal)

# ==================== SLEEK COMPACT STRATEGY DROPDOWN BAR & REAL-TIME AI RECOMMENDATION ====================
# 1. REAL-TIME AUTOMATIC AI RECOMMENDATION BANNER FOR 4 ASSETS
rec_us = ai_analyst.recommend_daily_strategy_for_asset("US_INDEX")
rec_gold = ai_analyst.recommend_daily_strategy_for_asset("GOLD")
rec_crypto = ai_analyst.recommend_daily_strategy_for_asset("CRYPTO")
rec_forex = ai_analyst.recommend_daily_strategy_for_asset("FOREX")

is_dark = (st.session_state.theme_mode == "DARK")
txt_color = "#f8fafc" if is_dark else "#1e293b"
sub_txt_color = "#94a3b8" if is_dark else "#475569"

st.markdown(f"""
<div style="background: rgba(99, 102, 241, 0.12); border: 1px solid rgba(99, 102, 241, 0.4); border-radius: 14px; padding: 14px 18px; margin-bottom: 16px;">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;">
        <span style="font-weight: 800; font-size: 1.05rem; color: #6366f1;">🤖 Daily AI Strategy Recommendations (คำแนะนำกลยุทธ์แยกรายสินทรัพย์โดย AI):</span>
        <span style="font-size: 0.82rem; font-weight: 600; color: #6366f1; background: rgba(99, 102, 241, 0.18); padding: 3px 8px; border-radius: 6px;">อัปเดตเรียลไทม์สด</span>
    </div>
</div>
""", unsafe_allow_html=True)

col_r1, col_r2, col_r3, col_r4 = st.columns(4)
with col_r1:
    st.markdown(f"""
    <div style="background: rgba(15, 23, 42, 0.6); padding: 10px; border-radius: 8px; border-left: 3px solid #38bdf8; min-height: 100px;">
        <div style="font-size: 0.82rem; color: #38bdf8; font-weight: 700;">🇺🇸 US Index (฿100k)</div>
        <div style="font-size: 0.88rem; color: #f8fafc; font-weight: 700; margin-top: 2px;">{rec_us['strategy_name']}</div>
        <div style="font-size: 0.76rem; color: #94a3b8; margin-top: 2px;">💡 {rec_us['recommendation_reason']}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("⚡ ใช้กับ US Index", key="btn_apply_rec_us", use_container_width=True):
        set_active_strategy(rec_us['strategy_key'], "US_INDEX")
        st.success(f"สลับระบบ US Index ไปใช้ {rec_us['strategy_name']} เรียบร้อย!")
        st.rerun()

with col_r2:
    st.markdown(f"""
    <div style="background: rgba(15, 23, 42, 0.6); padding: 10px; border-radius: 8px; border-left: 3px solid #f59e0b; min-height: 100px;">
        <div style="font-size: 0.82rem; color: #f59e0b; font-weight: 700;">🥇 Gold (฿90k)</div>
        <div style="font-size: 0.88rem; color: #f8fafc; font-weight: 700; margin-top: 2px;">{rec_gold['strategy_name']}</div>
        <div style="font-size: 0.76rem; color: #94a3b8; margin-top: 2px;">💡 {rec_gold['recommendation_reason']}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("⚡ ใช้กับ Gold", key="btn_apply_rec_gold", use_container_width=True):
        set_active_strategy(rec_gold['strategy_key'], "GOLD")
        st.success(f"สลับระบบ Gold ไปใช้ {rec_gold['strategy_name']} เรียบร้อย!")
        st.rerun()

with col_r3:
    st.markdown(f"""
    <div style="background: rgba(15, 23, 42, 0.6); padding: 10px; border-radius: 8px; border-left: 3px solid #10b981; min-height: 100px;">
        <div style="font-size: 0.82rem; color: #10b981; font-weight: 700;">🪙 Crypto Spot (฿80k)</div>
        <div style="font-size: 0.88rem; color: #f8fafc; font-weight: 700; margin-top: 2px;">{rec_crypto['strategy_name']}</div>
        <div style="font-size: 0.76rem; color: #94a3b8; margin-top: 2px;">💡 {rec_crypto['recommendation_reason']}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("⚡ ใช้กับ Crypto", key="btn_apply_rec_crypto", use_container_width=True):
        set_active_strategy(rec_crypto['strategy_key'], "CRYPTO")
        st.success(f"สลับระบบ Crypto ไปใช้ {rec_crypto['strategy_name']} เรียบร้อย!")
        st.rerun()

with col_r4:
    st.markdown(f"""
    <div style="background: rgba(15, 23, 42, 0.6); padding: 10px; border-radius: 8px; border-left: 3px solid #a855f7; min-height: 100px;">
        <div style="font-size: 0.82rem; color: #a855f7; font-weight: 700;">💱 Forex (฿30k)</div>
        <div style="font-size: 0.88rem; color: #f8fafc; font-weight: 700; margin-top: 2px;">{rec_forex['strategy_name']}</div>
        <div style="font-size: 0.76rem; color: #94a3b8; margin-top: 2px;">💡 {rec_forex['recommendation_reason']}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("⚡ ใช้กับ Forex", key="btn_apply_rec_forex", use_container_width=True):
        set_active_strategy(rec_forex['strategy_key'], "FOREX")
        st.success(f"สลับระบบ Forex ไปใช้ {rec_forex['strategy_name']} เรียบร้อย!")
        st.rerun()

st.markdown("<div style='margin-top:14px;'></div>", unsafe_allow_html=True)

# Determine active asset system being configured
active_sys = st.session_state.active_system if st.session_state.active_system in ["US_INDEX", "GOLD", "CRYPTO", "FOREX"] else "US_INDEX"

sys_names_map = {
    "US_INDEX": "🇺🇸 ดัชนีหุ้นสหรัฐฯ (US Index)",
    "GOLD": "🥇 บอททองคำ (Gold)",
    "CRYPTO": "🪙 บอท Crypto Spot",
    "FOREX": "💱 บอท Forex 24/5"
}

target_active_strat = get_active_strategy(active_sys)

col_strat1, col_strat2, col_strat3 = st.columns([2.2, 1.0, 1.2])

strategy_options = {
    f"[{info['level_label']}] {info['name']}": key 
    for key, info in config.STRATEGY_CATALOG.items()
}

option_keys = list(strategy_options.values())
curr_index = option_keys.index(target_active_strat) if target_active_strat in option_keys else 0

with col_strat1:
    selected_label = st.selectbox(
        f"⚙️ ตั้งค่ากลยุทธ์เฉพาะสำหรับระบบ [{sys_names_map[active_sys]}]:",
        options=list(strategy_options.keys()),
        index=curr_index,
        key=f"strategy_selector_dropdown_{active_sys}"
    )
    chosen_key = strategy_options[selected_label]
    if chosen_key != target_active_strat:
        set_active_strategy(chosen_key, asset_category=active_sys)
        st.session_state.current_active_strategy = chosen_key
        st.success(f"บันทึกกลยุทธ์ {chosen_key} สำหรับระบบ {active_sys} เรียบร้อยแล้ว!")
        st.rerun()

with col_strat2:
    st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
    if st.button("🔍 รายละเอียดกลยุทธ์", use_container_width=True):
        st.session_state.pending_strategy_modal = chosen_key
        st.rerun()

with col_strat3:
    st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
    rec_map = {"US_INDEX": rec_us, "GOLD": rec_gold, "CRYPTO": rec_crypto, "FOREX": rec_forex}
    active_rec = rec_map.get(active_sys, rec_us)
    rec_key = active_rec.get('strategy_key', 'TREND_FOLLOWING')
    rec_name = active_rec.get('strategy_name', 'Trend Following')
    
    if st.button(f"⚡ AI แนะนำ ({rec_name})", use_container_width=True):
        set_active_strategy(rec_key, asset_category=active_sys)
        st.session_state.current_active_strategy = rec_key
        st.success(f"สลับระบบ {active_sys} ไปใช้กลยุทธ์ตามที่ AI แนะนำ [{rec_name}] เรียบร้อยแล้ว!")
        st.rerun()

# ==================== BEGINNER-FRIENDLY VISUAL CUSTOM STRATEGY STUDIO ====================
if chosen_key == "CUSTOM" or st.session_state.current_active_strategy == "CUSTOM":
    with st.expander("🎨 คลิกเปิด / พับเก็บ: สตูดิโอออกแบบกลยุทธ์เทรดเอง (Beginner Visual Strategy Studio)", expanded=False):
        c_params = get_custom_strategy_params()
        is_dark_mode = (st.session_state.theme_mode == "DARK")
        
        # 1. Quick Presets Bar (ทางเลือกด่วน 1 คลิก)
        st.markdown("### ⚡ ทางเลือกด่วน 1 คลิก ( Quick Presets สำหรับมือใหม่):")
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            if st.button("🛡️ 1. โหมดเน้นปลอดภัย (ไม่ชอบเสี่ยง)\n[ซื้อ 10% | TP +5% | Cut -2%]", use_container_width=True):
                save_custom_strategy_params({"alloc_pct": 10.0, "tp_pct": 5.0, "sl_pct": -2.0, "rsi_buy": 30, "rsi_sell": 65, "ai_min_sentiment": 0.20})
                st.rerun()
        with col_p2:
            if st.button("⚖️ 2. โหมดสมดุล กลางๆ (สายบาลานซ์)\n[ซื้อ 20% | TP +8% | Cut -3.5%]", use_container_width=True):
                save_custom_strategy_params({"alloc_pct": 20.0, "tp_pct": 8.0, "sl_pct": -3.5, "rsi_buy": 35, "rsi_sell": 65, "ai_min_sentiment": 0.10})
                st.rerun()
        with col_p3:
            if st.button("🚀 3. โหมดสายซิ่ง (เน้นกำไรคำโต)\n[ซื้อ 35% | TP +15% | Cut -5%]", use_container_width=True):
                save_custom_strategy_params({"alloc_pct": 35.0, "tp_pct": 15.0, "sl_pct": -5.0, "rsi_buy": 40, "rsi_sell": 75, "ai_min_sentiment": 0.0})
                st.rerun()
                
        st.markdown("---")
        
        # 2. Sliders Section & Live Risk Speedometer Gauge
        col_tune1, col_tune2 = st.columns([1.7, 1.3])
        
        with col_tune1:
            st.markdown("### 🎛️ ปรับแต่งค่าความต้องการของคุณ (ภาษาไทยเข้าใจง่าย):")
            
            alloc_val = st.slider(
                "💵 1. อยากให้บอทแบ่งเงินซื้อสินค้าต่อครั้งเท่าไหร่ ? (% ของเงินสด):",
                min_value=5.0, max_value=50.0, value=float(c_params.get("alloc_pct", 20.0)), step=1.0,
                help="เช่น 20% บอทจะใช้เงินประมาณ ฿20,000 ต่อ 1 ไม้ จากวงเงิน ฿100,000"
            )
            
            tp_val = st.slider(
                "🎯 2. อยากได้กำไรกี่ % แล้วสั่งให้บอทกดขายทำกำไรทันที (Take Profit) ?:",
                min_value=1.0, max_value=30.0, value=float(c_params.get("tp_pct", 8.0)), step=0.5
            )
            
            sl_val = st.slider(
                "🛑 3. ยอมขาดทุนได้สูงสุดกี่ % แล้วสั่งให้บอทตัดขาดทุนทันที (Cut-Loss) ?:",
                min_value=-15.0, max_value=-1.0, value=float(c_params.get("sl_pct", -3.5)), step=0.5
            )
            
            rsi_b_val = st.slider(
                "📉 4. อยากให้บอทเริ่มช้อนซื้อ ตอนราคาย่อตัวลงมาลึกแค่ไหน ?:",
                min_value=15, max_value=45, value=int(c_params.get("rsi_buy", 35)),
                help="ค่า 20-30 = รอราคาย่อลงมาลึกมากๆ (ปลอดภัย) / ค่า 35-45 = ช้อนซื้อไว (ซิ่งเร็ว)"
            )
            
            ai_min_val = st.slider(
                "🤖 5. บอทต้องอ่านข่าว AI แล้วมั่นใจแค่ไหน ถึงจะกล้าช้อนซื้อ ?:",
                min_value=-0.50, max_value=0.50, value=float(c_params.get("ai_min_sentiment", 0.10)), step=0.05,
                help="+0.10 = ข่าวดีปานกลาง / +0.30+ = ต้องเป็นข่าวดีมากๆ เท่านั้น"
            )

        # Calculate Live Risk Score (0 - 100%)
        risk_score = min(100, int((alloc_val * 0.8) + (abs(sl_val) * 3.5) + (tp_val * 1.5)))
        if risk_score <= 35:
            risk_label = "🟢 โหมดเน้นปลอดภัยสูง (Conservative)"
            risk_color = "#10b981"
        elif risk_score <= 65:
            risk_label = "🟡 โหมดสมดุล ปานกลาง (Moderate Balanced)"
            risk_color = "#f59e0b"
        else:
            risk_label = "🔴 โหมดสายซิ่ง เสี่ยงสูง (Aggressive High Yield)"
            risk_color = "#ef4444"

        # Compute Simulated Real Baht Money
        sim_order_baht = 100000.0 * (alloc_val / 100.0)
        sim_tp_baht = sim_order_baht * (tp_val / 100.0)
        sim_sl_baht = sim_order_baht * (abs(sl_val) / 100.0)
        rr_ratio = (tp_val / abs(sl_val)) if abs(sl_val) > 0 else 1.0

        with col_tune2:
            st.markdown(f"### ⚡ หน้าปัดวัดระดับความซิ่ง (Risk Speedometer)")
            
            # Render Plotly Speedometer Gauge
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = risk_score,
                number = {'suffix': "%"},
                domain = {'x': [0, 1], 'y': [0, 1]},
                gauge = {
                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#94a3b8"},
                    'bar': {'color': risk_color},
                    'bgcolor': "rgba(0,0,0,0)",
                    'borderwidth': 1,
                    'bordercolor': "#cbd5e1",
                    'steps': [
                        {'range': [0, 35], 'color': 'rgba(16, 185, 129, 0.25)'},
                        {'range': [35, 65], 'color': 'rgba(245, 158, 11, 0.25)'},
                        {'range': [65, 100], 'color': 'rgba(239, 68, 68, 0.25)'}
                    ]
                }
            ))
            fig_gauge.update_layout(
                height=190, margin=dict(l=15, r=15, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_gauge, use_container_width=True)
            
            st.markdown(f"<div style='text-align:center; font-size:1.1rem; font-weight:800; color:{risk_color}; margin-bottom:14px;'>{risk_label}</div>", unsafe_allow_html=True)
            
            # Live Baht Money Simulation Card
            st.markdown(f"""
            <div style="background: rgba(30, 41, 59, 0.6) if {is_dark_mode} else rgba(241, 245, 249, 0.9); border: 1px solid rgba(0,0,0,0.12); border-radius: 16px; padding: 16px;">
                <h4 style="margin:0 0 10px 0;">💡 จำลองตัวเงินบาทจริงที่จะเกิดขึ้นต่อ 1 ออเดอร์:</h4>
                <div style="display:flex; justify-content:space-between; margin-bottom:6px;"><span>💵 งบซื้อต่อ 1 สินค้า:</span> <strong>฿{sim_order_baht:,.0f} บาท</strong></div>
                <div style="display:flex; justify-content:space-between; margin-bottom:6px; color:#10b981;"><span>🎯 ถ้าราคาพุ่งชนเป้า (กำไร):</span> <strong>+฿{sim_tp_baht:,.0f} บาท (+{tp_val}%)</strong></div>
                <div style="display:flex; justify-content:space-between; margin-bottom:6px; color:#ef4444;"><span>🛑 ถ้าราคาย่อผิดทาง (ขาดทุน):</span> <strong>-฿{sim_sl_baht:,.0f} บาท ({sl_val}%)</strong></div>
                <hr style="margin:8px 0; border-color:rgba(0,0,0,0.1);">
                <div style="display:flex; justify-content:space-between; font-weight:700;"><span>📊 อัตราความคุ้มค่า (Risk/Reward):</span> <span style="color:#2563eb;">1 : {rr_ratio:.2f}</span></div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
        if st.button("🚀 บันทึกและสั่งให้บอทเริ่มเทรดด้วยแผนนี้ทันที (Save & Apply Plan)", use_container_width=True):
            new_params = {
                "alloc_pct": alloc_val,
                "tp_pct": tp_val,
                "sl_pct": sl_val,
                "rsi_buy": rsi_b_val,
                "rsi_sell": 65,
                "ema_fast": 10,
                "ema_slow": 20,
                "ai_min_sentiment": ai_min_val
            }
            save_custom_strategy_params(new_params)
            set_active_strategy("CUSTOM")
            st.session_state.current_active_strategy = "CUSTOM"
            st.success("บันทึกแผนกลยุทธ์ของคุณเรียบร้อยแล้ว! บอทเริ่มทำงานตามแผนทันที")
            st.rerun()

# ==================== VIEW 1: UNIFIED COMMAND CENTER ====================
if st.session_state.active_system == "UNIFIED":
    st.markdown('<div class="hero-title">🌐 ศูนย์กลางควบคุมระบบเทรด (Unified Command Center)</div>', unsafe_allow_html=True)

    @st.fragment(run_every=15)
    def render_live_unified_metrics():
        now_dt = get_thai_now_naive()
        now_str = now_dt.strftime('%H:%M:%S น.')
        unified_pnl = get_unified_portfolio_pnl()
        harvest_status = get_daily_harvest_status()
        unrealized_prof = harvest_status['total_unrealized_profit_thb']
        harvested_today = harvest_status['harvested_today_thb']
        is_eligible = harvest_status['is_eligible']
        
        pnl_color = "#10b981" if unified_pnl['total_pnl_thb'] >= 0 else "#ef4444"
        pnl_sign = "+" if unified_pnl['total_pnl_thb'] >= 0 else ""

        robot_on_status = get_robot_status()
        robot_status_badge = f'<span style="background: {"rgba(16, 185, 129, 0.25)" if robot_on_status else "rgba(239, 68, 68, 0.25)"}; border: {"1px solid rgba(16, 185, 129, 0.6)" if robot_on_status else "1px solid rgba(239, 68, 68, 0.6)"}; color: {app_text}; padding: 5px 14px; border-radius: 20px; font-weight: 800; font-size: 0.82rem;">{"🟢 AI AUTO-TRADER 24/7: ON" if robot_on_status else "🔴 AI AUTO-TRADER 24/7: OFF (PAUSED)"}</span>'
        
        curr_b_mode = get_broker_mode()
        broker_mode_badge = f'<span style="background: {"rgba(16, 185, 129, 0.25)" if curr_b_mode == "LIVE" else "rgba(245, 158, 11, 0.25)"}; border: {"1px solid rgba(16, 185, 129, 0.6)" if curr_b_mode == "LIVE" else "1px solid rgba(245, 158, 11, 0.6)"}; color: {app_text}; padding: 5px 12px; border-radius: 20px; font-weight: 800; font-size: 0.8rem;">{"🟢 LIVE BROKER API" if curr_b_mode == "LIVE" else "📝 PAPER TRADING"}</span>'

        # Top Header Summary Box
        header_html = f"""<div style="background: {glass_card_bg}; backdrop-filter: blur(16px); border: {glass_card_border}; border-radius: 20px; padding: 20px 22px; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.12);">
        <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px;">
        <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
        {robot_status_badge}
        {broker_mode_badge}
        <span style="background: rgba(59, 130, 246, 0.2); border: 1px solid rgba(59, 130, 246, 0.4); color: {app_text}; padding: 5px 12px; border-radius: 20px; font-weight: 700; font-size: 0.8rem;">{check_us_market_status(now_dt)}</span>
        <span style="background: rgba(59, 130, 246, 0.2); border: 1px solid rgba(59, 130, 246, 0.4); color: {app_text}; padding: 5px 12px; border-radius: 20px; font-weight: 700; font-size: 0.8rem;">{check_forex_market_status(now_dt)}</span>
        <span style="background: rgba(59, 130, 246, 0.2); border: 1px solid rgba(59, 130, 246, 0.4); color: {app_text}; padding: 5px 12px; border-radius: 20px; font-weight: 700; font-size: 0.8rem;">{check_crypto_market_status()}</span>
        <span style="color: {metric_label_color}; font-weight: 700; font-size: 0.85rem;">⏰ {now_str} (Realtime Live)</span>
        </div>
        <div>
        <span style="color: {pnl_color}; font-size: 1.35rem; font-weight: 800;">กำไร/ขาดทุนรวม 4 ระบบ: {pnl_sign}฿{unified_pnl['total_pnl_thb']:,.2f} ({pnl_sign}{unified_pnl['total_pnl_pct']:.2f}%)</span>
        </div>
        </div>
        </div>"""
        st.markdown(header_html, unsafe_allow_html=True)
        
        # Main Page Master AI Robot Toggle Switch
        col_m1, col_m2, col_m3 = st.columns([2.2, 1, 1])
        with col_m1:
            st.markdown(
                f'<div style="display:flex; align-items:center; gap:10px; margin-bottom:12px; margin-top:4px;">'
                f'<span style="font-weight:700; color:{app_text}; font-size:0.95rem;">🤖 สวิตช์หลักควบคุม AI Auto-Trading 24/7 (หน้าแรก):</span> '
                f'{robot_status_badge}'
                f'</div>',
                unsafe_allow_html=True
            )
        with col_m2:
            if st.button("🔑 ตั้งค่า Broker API Keys", key="btn_main_api_jump", use_container_width=True):
                st.session_state.active_system = "BROKER_CONFIG"
                st.rerun()
        with col_m3:
            toggle_main_btn_text = "🔴 สลับปิดการทำงาน (OFF)" if robot_on_status else "🟢 สลับเปิดการทำงาน (ON)"
            if st.button(toggle_main_btn_text, key="btn_main_header_toggle", use_container_width=True):
                new_st = not robot_on_status
                ok_st, msg_st = set_robot_status(new_st)
                if ok_st:
                    st.success(msg_st)
                    st.rerun()
        
        # Row 1: Top Financial Summary Cards (3 Columns)
        row1_c1, row1_c2, row1_c3 = st.columns([1, 1, 1])
        
        with row1_c1:
            st.markdown(f"""
            <div style="background: {metric_card_bg}; padding: 12px 14px; border-radius: 14px; border: 1px solid rgba(56, 189, 248, 0.4); min-height: 105px;">
            <div style="font-size:0.82rem; color:{metric_label_color}; font-weight:700;">💵 เงินสดรวม 4 ระบบ:</div>
            <div style="font-size:1.35rem; color:#2563eb; font-weight:800; margin-top:6px;">฿{unified_pnl['total_cash']:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with row1_c2:
            st.markdown(f"""
            <div style="background: {metric_card_bg}; padding: 12px 14px; border-radius: 14px; border: 1px solid rgba(168, 85, 247, 0.4); min-height: 105px;">
            <div style="font-size:0.82rem; color:{metric_label_color}; font-weight:700;">💼 สินทรัพย์ถือครองรวม:</div>
            <div style="font-size:1.35rem; color:#7c3aed; font-weight:800; margin-top:6px;">฿{unified_pnl['total_invested']:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with row1_c3:
            st.markdown(f"""
            <div style="background: {metric_card_bg}; padding: 12px 14px; border-radius: 14px; border: 1px solid rgba(0, 0, 0, 0.15); min-height: 105px;">
            <div style="font-size:0.82rem; color:{metric_label_color}; font-weight:700;">🏦 มูลค่าพอร์ตรวมทั้งหมด:</div>
            <div style="font-size:1.35rem; color:{title_color}; font-weight:800; margin-top:6px;">฿{unified_pnl['total_equity']:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)

        # Row 2: Performance Action Cards (3 Columns: TP, Cut-Loss, Harvest Today)
        row2_c1, row2_c2, row2_c3 = st.columns([1, 1, 1])

        with row2_c1:
            st.markdown(f"""
            <div style="background: {metric_card_bg}; padding: 8px 12px; border-radius: 14px; border: 1px solid rgba(16, 185, 129, 0.4); margin-bottom: 6px;">
            <div style="font-size:0.80rem; color:{metric_label_color}; font-weight:700;">🎯 Take Profit สะสม:</div>
            <div style="font-size:1.25rem; color:#10b981; font-weight:800;">+฿{unified_pnl.get('total_take_profit_thb', 0.0):,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🔍 ที่มา TP", key="btn_modal_tp", use_container_width=True):
                show_tp_dialog()

        with row2_c2:
            st.markdown(f"""
            <div style="background: {metric_card_bg}; padding: 8px 12px; border-radius: 14px; border: 1px solid rgba(239, 68, 68, 0.4); margin-bottom: 6px;">
            <div style="font-size:0.80rem; color:{metric_label_color}; font-weight:700;">🛑 Cut-Loss สะสม:</div>
            <div style="font-size:1.25rem; color:#ef4444; font-weight:800;">-฿{unified_pnl.get('total_cut_loss_thb', 0.0):,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🔍 ที่มา CL", key="btn_modal_cl", use_container_width=True):
                show_cl_dialog()

        with row2_c3:
            st.markdown(f"""
            <div style="background: {metric_card_bg}; padding: 8px 12px; border-radius: 14px; border: 1.5px solid #10b981; margin-bottom:6px;">
            <div style="font-size:0.80rem; color:{metric_label_color}; font-weight:700;">💰 เก็บกำไรสดวันนี้:</div>
            <div style="font-size:1.20rem; color:#10b981; font-weight:800;">฿{harvested_today:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
            if is_eligible:
                if st.button("🎯 กดเก็บกำไร ( ฿300 )", key="btn_harvest_compact", use_container_width=True):
                    with st.spinner("AI ขายเก็บกำไร..."):
                        res = execute_daily_profit_harvest()
                        if res['success']:
                            st.success(res['message'])
                            st.rerun()
                        else:
                            st.warning(res['message'])
            else:
                st.button(f"🔒 รอครบ ฿300 (มี +฿{unrealized_prof:,.0f})", disabled=True, key="btn_harvest_compact", use_container_width=True)

    render_live_unified_metrics()

    # 24/7 AI Active Market Intelligence & Pre-Market Plan Queue Card
    import importlib
    import pnl_tracker
    import ai_active_planner
    importlib.reload(pnl_tracker)
    importlib.reload(ai_active_planner)
    
    ai_plan_data = ai_active_planner.get_latest_ai_active_plan()
    
    with st.expander("🧠 ⚡ คลิกเปิด/พับเก็บ: ศูนย์วิเคราะห์ข่าว AI 24 ชั่วโมง & แผนเตรียมเข้าซื้อล่วงหน้า (24/7 Active AI Pre-Market Strategy Queue)", expanded=True):
        st.markdown("<div style='font-size:0.95rem; font-weight:700; color:#38bdf8; margin-bottom:8px;'>🤖 AI Robot สแกนข่าวการเงิน สถิติราคา และคำนวณโอกาสชนะ (Win Probability %) ตลอด 24 ชั่วโมงแม้ตลาดปิด เพื่อตั้งแผนเข้าซื้อทันทีเมื่อเปิดตลาด:</div>", unsafe_allow_html=True)
        
        plan_cols = st.columns(4)
        sys_labels = config.SYSTEM_LABELS
        
        for idx, (sys_code, sys_label) in enumerate(sys_labels.items()):
            with plan_cols[idx]:
                sys_plan = ai_plan_data.get("systems", {}).get(sys_code, {})
                sp_cash = sys_plan.get("spendable_cash_thb", 0.0)
                init_cap = config.SYSTEM_ALLOCATIONS.get(sys_code, 100000.0)
                # Fetch fresh category-specific harvested vault
                sys_pnl_fresh = pnl_tracker.get_system_pnl(sys_code, init_cap)
                hv_cash = sys_pnl_fresh.get("harvested_vault_thb", sys_plan.get("harvested_vault_thb", 0.0))
                candidates = sys_plan.get("candidate_plans", [])
                
                st.markdown(f"""
                <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 16px; padding: 14px; margin-bottom:10px;">
                    <div style="font-weight:800; font-size:1.0rem; color:#f8fafc;">{sys_label}</div>
                    <div style="font-size:0.8rem; color:#94a3b8;">💵 Spendable Cash หมุนเวียน: <strong style="color:#38bdf8;">฿{sp_cash:,.2f}</strong></div>
                    <div style="font-size:0.8rem; color:#94a3b8;">🔒 Locked Harvest Vault: <strong style="color:#10b981;">฿{hv_cash:,.2f}</strong></div>
                </div>
                """, unsafe_allow_html=True)
                
                if candidates:
                    for cand in candidates:
                        w_prob = cand.get("win_probability_pct", 0.0)
                        sym = cand.get("symbol", "")
                        alloc_b = cand.get("planned_alloc_thb", 0.0)
                        plan_type = cand.get("plan_type", "BUY")
                        
                        if plan_type == "SELL":
                            st.markdown(f"""
                            <div style="background: rgba(15, 23, 42, 0.8); border-left: 4px solid #ef4444; border-radius: 10px; padding: 10px 12px; margin-bottom: 4px;">
                                <div style="display:flex; justify-content:space-between; align-items:center;">
                                    <strong style="color:#f8fafc; font-size:0.95rem;">🔴 {sym} (SELL)</strong>
                                    <span style="background:rgba(239, 68, 68, 0.2); color:#f87171; font-weight:800; padding:2px 8px; border-radius:12px; font-size:0.78rem;">เตรียมขายตัดทำกำไร/ลดเสี่ยง</span>
                                </div>
                                <div style="font-size:0.80rem; color:#cbd5e1; margin-top:4px;">{cand.get('ai_summary', '')}</div>
                                <div style="font-size:0.75rem; color:#ef4444; font-weight:600; margin-top:4px;">💡 แผน AI: {cand.get('ai_action_plan', '')}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style="background: rgba(15, 23, 42, 0.8); border-left: 4px solid #10b981; border-radius: 10px; padding: 10px 12px; margin-bottom: 4px;">
                                <div style="display:flex; justify-content:space-between; align-items:center;">
                                    <strong style="color:#f8fafc; font-size:0.95rem;">🟢 {sym} (BUY)</strong>
                                    <span style="background:rgba(16, 185, 129, 0.2); color:#34d399; font-weight:800; padding:2px 8px; border-radius:12px; font-size:0.78rem;">โอกาสชนะ {w_prob:.1f}%</span>
                                </div>
                                <div style="font-size:0.80rem; color:#cbd5e1; margin-top:4px;">{cand.get('ai_summary', '')}</div>
                                <div style="font-size:0.75rem; color:#94a3b8; margin-top:4px;">💡 แผนลงทุน Spendable Cash: <strong>฿{alloc_b:,.0f} บาท</strong></div>
                            </div>
                            """, unsafe_allow_html=True)

                        # 🏭 🔍 Live AI Observation Room & Production Pipeline Inspection
                        with st.expander(f"🔍 ส่องห้องคิด AI & สายการผลิต ({sym})", expanded=False):
                            st.markdown(f"""
                            <div style="background: rgba(30, 41, 59, 0.9); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 12px; padding: 12px; margin-top: 4px; font-size: 0.82rem;">
                                <div style="font-weight: 800; color: #38bdf8; margin-bottom: 6px;">🧠 สมอง AI กำลังคิด & สแกน ณ วินาทีนี้:</div>
                                <div style="color: #f1f5f9; background: rgba(15, 23, 42, 0.6); padding: 8px; border-radius: 8px; border-left: 3px solid #38bdf8; margin-bottom: 10px; font-style: italic;">
                                    "{cand.get('ai_thought_rationale', cand.get('ai_action_plan', 'กำลังประเมินสภาวะตลาดสด'))}"
                                </div>
                                
                                <div style="font-weight: 800; color: #f8fafc; margin-bottom: 6px;">🏭 สายการผลิต 5 ขั้นตอน (Production Pipeline):</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            steps = cand.get("pipeline_steps", [])
                            if not steps:
                                steps = [
                                    {"name": "📰 Global News & Macro Scan", "status": "COMPLETED", "detail": f"Sentiment: {cand.get('ai_sentiment', 0.0):+.2f}"},
                                    {"name": "📈 Multi-Timeframe Confluence Check", "status": "COMPLETED", "detail": f"Score: {cand.get('confluence_score', 0.5):.2f}"},
                                    {"name": "📊 Technical Levels Setup", "status": "COMPLETED", "detail": f"RSI: {cand.get('rsi', 50):.1f}"},
                                    {"name": "🧮 Smart Fee & Profit Filter", "status": "COMPLETED", "detail": f"Fee Aware: {cand.get('fee_pct', 0.2)}%"},
                                    {"name": "⚡ Order Trigger Ready", "status": "IN_PROGRESS", "detail": "สแตนด์บายเตรียมส่งออเดอร์"}
                                ]
                                
                            for s_idx, step in enumerate(steps, 1):
                                st_icon = "🟢" if step.get("status") == "COMPLETED" else "🟡"
                                st.markdown(f"""
                                <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(15, 23, 42, 0.5); padding:4px 8px; border-radius:6px; margin-bottom:4px; font-size:0.78rem;">
                                    <span>{st_icon} <strong>Step {s_idx}:</strong> {step.get('name')}</span>
                                    <span style="color:#94a3b8; font-size:0.75rem;">{step.get('detail')}</span>
                                </div>
                                """, unsafe_allow_html=True)

                            # Technical Targets Spec
                            tp_p = cand.get("tp_price", 0.0)
                            sl_p = cand.get("sl_price", 0.0)
                            net_p = cand.get("est_net_profit_thb", 0.0)
                            st.markdown(f"""
                            <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 8px; padding: 8px; margin-top: 6px; font-size: 0.78rem;">
                                <div style="color: #34d399; font-weight: 700;">🎯 เป้าหมายราคา (Target Spec):</div>
                                <div style="display: flex; justify-content: space-between; color: #cbd5e1; margin-top: 2px;">
                                    <span>🟢 Take Profit: <strong>${tp_p:,.2f}</strong> (+{cand.get('tp_pct', 8.0):.1f}%)</span>
                                    <span>🛑 Stop Loss: <strong>${sl_p:,.2f}</strong> ({cand.get('sl_pct', -3.5):.1f}%)</span>
                                </div>
                                <div style="color: #10b981; font-weight: 800; margin-top: 4px;">💰 กำไรเน็ตๆ คาดการณ์ (หลังหักค่าธรรมเนียม): +฿{net_p:,.2f} บาท</div>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    if sp_cash <= 500.0:
                        st.markdown("<div style='font-size:0.85rem; color:#10b981; font-weight:700; background:rgba(16, 185, 129, 0.15); padding:10px; border-radius:10px;'>✅ นำเงิน Spendable Cash ลงทุนเต็มประสิทธิภาพแล้ว (100% Deployed)</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='font-size:0.85rem; color:#94a3b8;'>🔍 AI กำลังสแกนหาจังหวะช้อนซื้อเมื่อเกิดสัญญาณเด็ด</div>", unsafe_allow_html=True)
    
    harvest_status = get_daily_harvest_status()
            
    # Detailed Expander for Daily Harvest Analytics & Transaction Log
    with st.expander("🔍 คลิกดูรายละเอียดประวัติการกดเก็บกำไร & กราฟเปรียบเทียบย้อนหลัง (Daily Profit Harvest)", expanded=False):
        comp_summary = daily_profit_harvester.get_daily_harvest_comparison_summary()
        
        st.markdown("### 🏆 ตารางสรุปการเปรียบเทียบยอดเก็บกำไรย้อนหลัง (Daily Profit Comparison)")
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.metric("💰 เก็บกำไรวันนี้ (Today)", f"฿{comp_summary['today_thb']:,.2f}", f"{comp_summary['pct_vs_yesterday']:+.1f}% vs เมื่อวาน")
        with m_col2:
            st.metric("📅 เก็บกำไรเมื่อวาน (Yesterday)", f"฿{comp_summary['yesterday_thb']:,.2f}")
        with m_col3:
            st.metric("💎 ยอดเก็บกำไรสะสมรวมทั้งหมด", f"฿{comp_summary['all_time_thb']:,.2f}")
        with m_col4:
            st.metric("📊 จำนวนวันที่กดเก็บกำไร", f"{len(comp_summary['comparison_df'])} วัน")
        st.markdown("---")
        st.markdown("### 📋 รายละเอียดออเดอร์ที่ AI ขายเก็บกำไรวันนี้")
        today_trades = harvest_status.get('today_trades', [])
        if today_trades:
            df_today = pd.DataFrame(today_trades)
            df_today = df_today.rename(columns={
                'timestamp': 'เวลาทำรายการ',
                'symbol': 'สินทรัพย์',
                'shares': 'จำนวนหน่วยที่ขาย',
                'price': 'ราคาที่ขาย',
                'total_trade_thb': 'มูลค่ารวม (บาท)',
                'harvested_pnl_thb': 'กำไรสดที่ดึงเก็บ (บาท)'
            })
            display_cols = ['เวลาทำรายการ', 'สินทรัพย์', 'จำนวนหน่วยที่ขาย', 'ราคาที่ขาย', 'มูลค่ารวม (บาท)', 'กำไรสดที่ดึงเก็บ (บาท)']
            st.dataframe(df_today[[c for c in display_cols if c in df_today.columns]], use_container_width=True)
        else:
            st.info("ยังไม่มีรายการกดดึงกำไรสดในวันนี้ (เมื่อกดปุ่มเก็บกำไร รายการขายจะมาแสดงที่นี่)")

        st.markdown("---")
        st.markdown("### 📊 กราฟเปรียบเทียบยอดดึงกำไรสดเก็บเข้ากระเป๋าย้อนหลัง")
        tf_col1, tf_col2 = st.columns([1, 4])
        with tf_col1:
            selected_tf = st.radio(
                "เลือกช่วงเวลาเปรียบเทียบ:",
                ["1 อาทิตย์", "1 เดือน", "3 เดือน", "6 เดือน", "1 ปี"],
                index=1,
                key="harv_tf_radio_detail"
            )
        
        tf_code_map = {"1 อาทิตย์": "1W", "1 เดือน": "1M", "3 เดือน": "3M", "6 เดือน": "6M", "1 ปี": "1Y"}
        df_chart = get_harvest_chart_df(tf_code_map[selected_tf])
        
        fig_harv = go.Figure()
        fig_harv.add_trace(go.Bar(
            x=df_chart['วันที่'],
            y=df_chart['กำไรสดที่ดึงเก็บ (บาท)'],
            marker_color='#10b981',
            name='กำไรสดที่ดึงเก็บ (บาท)',
            hovertemplate='วันที่: %{x}<br>กำไรสดที่ดึงเก็บ: ฿%{y:,.2f} บาท<extra></extra>'
        ))
        fig_harv.update_layout(
            height=280,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="วันที่"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.08)", title="กำไรสด (บาท)")
        )
        with tf_col2:
            st.plotly_chart(fig_harv, use_container_width=True)
    
    # 4 Asset Class Cards Side-by-Side (Dynamic Modern Green / Red Glassmorphism)
    st.subheader("📊 เปรียบเทียบผลตอบแทน 4 ระบบหลัก")
    col_sys1, col_sys2, col_sys3, col_sys4 = st.columns(4)
    unified_pnl = get_unified_portfolio_pnl()
    us_index_p = unified_pnl['us_index_pnl']
    gold_p = unified_pnl['gold_pnl']
    crypto_p = unified_pnl['crypto_pnl']
    forex_p = unified_pnl['forex_pnl']
    is_dark = (st.session_state.theme_mode == "DARK")

    def get_asset_card_style(pnl_val, is_dark_mode):
        is_prof = (pnl_val >= 0)
        pnl_sign_str = "+" if is_prof else ""
        if is_dark_mode:
            if is_prof:
                bg_css = "linear-gradient(135deg, rgba(6, 78, 59, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%)"
                border_css = "1.5px solid rgba(52, 211, 153, 0.7)"
                shadow_css = "0 10px 30px rgba(16, 185, 129, 0.3)"
                badge_bg = "rgba(16, 185, 129, 0.25)"
                badge_text = "#34d399"
                title_color = "#ffffff"
                label_color = "#a7f3d0"
            else:
                bg_css = "linear-gradient(135deg, rgba(127, 29, 29, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%)"
                border_css = "1.5px solid rgba(248, 113, 113, 0.7)"
                shadow_css = "0 10px 30px rgba(239, 68, 68, 0.3)"
                badge_bg = "rgba(239, 68, 68, 0.25)"
                badge_text = "#f87171"
                title_color = "#ffffff"
                label_color = "#fca5a5"
        else:
            if is_prof:
                bg_css = "linear-gradient(135deg, #d1fae5 0%, #ecfdf5 100%)"
                border_css = "1.5px solid #10b981"
                shadow_css = "0 10px 25px rgba(16, 185, 129, 0.2)"
                badge_bg = "rgba(16, 185, 129, 0.2)"
                badge_text = "#047857"
                title_color = "#064e3b"
                label_color = "#047857"
            else:
                bg_css = "linear-gradient(135deg, #fee2e2 0%, #fef2f2 100%)"
                border_css = "1.5px solid #ef4444"
                shadow_css = "0 10px 25px rgba(239, 68, 68, 0.2)"
                badge_bg = "rgba(239, 68, 68, 0.2)"
                badge_text = "#b91c1c"
                title_color = "#7f1d1d"
                label_color = "#b91c1c"
        return {
            'bg': bg_css, 'border': border_css, 'shadow': shadow_css,
            'badge_bg': badge_bg, 'badge_text': badge_text,
            'title_color': title_color, 'label_color': label_color, 'pnl_sign': pnl_sign_str
        }

    us_style = get_asset_card_style(us_index_p['total_pnl_thb'], is_dark)
    gold_style = get_asset_card_style(gold_p['total_pnl_thb'], is_dark)
    c_style = get_asset_card_style(crypto_p['total_pnl_thb'], is_dark)
    forex_style = get_asset_card_style(forex_p['total_pnl_thb'], is_dark)
    hr_border = 'rgba(255,255,255,0.15)' if is_dark else 'rgba(0,0,0,0.1)'

    with col_sys1:
        st.markdown(f"""
        <div style="background: {us_style['bg']}; border: {us_style['border']}; box-shadow: {us_style['shadow']}; border-radius: 20px; padding: 18px; margin-bottom: 20px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h4 style="margin:0; color:{us_style['title_color']}; font-weight:800; font-size:1.05rem;">🇺🇸 ดัชนีหุ้นสหรัฐฯ</h4>
                <span style="font-weight:800; font-size:1.05rem; background:{us_style['badge_bg']}; color:{us_style['badge_text']}; padding:4px 10px; border-radius:10px;">{us_style['pnl_sign']}฿{us_index_p['total_pnl_thb']:,.2f}</span>
            </div>
            <p style="color:{us_style['label_color']}; font-size:0.82rem; margin-top:4px; font-weight:600;">ทุน ฿100,000 บาท (40%)</p>
            <hr style="border-color:{hr_border}; margin:10px 0;">
            <div style="font-size:0.85rem; display:flex; justify-content:space-between; margin-bottom:4px; color:{us_style['title_color']};"><span>มูลค่าพอร์ต:</span> <strong>฿{us_index_p['current_equity']:,.2f}</strong></div>
            <div style="font-size:0.85rem; display:flex; justify-content:space-between; margin-bottom:4px; color:{us_style['title_color']};"><span>เงินสดคงเหลือ:</span> <strong>฿{us_index_p['cash_balance_thb']:,.2f}</strong></div>
            <div style="font-size:0.85rem; display:flex; justify-content:space-between; margin-bottom:4px; color:{us_style['title_color']};"><span>จำนวนที่ถือ:</span> <strong>{len(us_index_p['active_positions_detail'])} รายการ</strong></div>
            <div style="font-size:0.82rem; display:flex; justify-content:space-between; margin-top:6px; color:#10b981;"><span>🎯 Take Profit สะสม:</span> <strong>+฿{us_index_p.get('cumulative_take_profit_thb', 0.0):,.2f}</strong></div>
            <div style="font-size:0.82rem; display:flex; justify-content:space-between; color:#ef4444;"><span>🛑 Cut-Loss สะสม:</span> <strong>-฿{us_index_p.get('cumulative_cut_loss_thb', 0.0):,.2f}</strong></div>
        </div>
        """, unsafe_allow_html=True)

    with col_sys2:
        st.markdown(f"""
        <div style="background: {gold_style['bg']}; border: {gold_style['border']}; box-shadow: {gold_style['shadow']}; border-radius: 20px; padding: 18px; margin-bottom: 20px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h4 style="margin:0; color:{gold_style['title_color']}; font-weight:800; font-size:1.05rem;">🥇 บอททองคำ (Gold)</h4>
                <span style="font-weight:800; font-size:1.05rem; background:{gold_style['badge_bg']}; color:{gold_style['badge_text']}; padding:4px 10px; border-radius:10px;">{gold_style['pnl_sign']}฿{gold_p['total_pnl_thb']:,.2f}</span>
            </div>
            <p style="color:{gold_style['label_color']}; font-size:0.82rem; margin-top:4px; font-weight:600;">ทุน ฿90,000 บาท (30%)</p>
            <hr style="border-color:{hr_border}; margin:10px 0;">
            <div style="font-size:0.85rem; display:flex; justify-content:space-between; margin-bottom:4px; color:{gold_style['title_color']};"><span>มูลค่าพอร์ต:</span> <strong>฿{gold_p['current_equity']:,.2f}</strong></div>
            <div style="font-size:0.85rem; display:flex; justify-content:space-between; margin-bottom:4px; color:{gold_style['title_color']};"><span>เงินสดคงเหลือ:</span> <strong>฿{gold_p['cash_balance_thb']:,.2f}</strong></div>
            <div style="font-size:0.85rem; display:flex; justify-content:space-between; margin-bottom:4px; color:{gold_style['title_color']};"><span>จำนวนที่ถือ:</span> <strong>{len(gold_p['active_positions_detail'])} รายการ</strong></div>
            <div style="font-size:0.82rem; display:flex; justify-content:space-between; margin-top:6px; color:#10b981;"><span>🎯 Take Profit สะสม:</span> <strong>+฿{gold_p.get('cumulative_take_profit_thb', 0.0):,.2f}</strong></div>
            <div style="font-size:0.82rem; display:flex; justify-content:space-between; color:#ef4444;"><span>🛑 Cut-Loss สะสม:</span> <strong>-฿{gold_p.get('cumulative_cut_loss_thb', 0.0):,.2f}</strong></div>
        </div>
        """, unsafe_allow_html=True)

    with col_sys3:
        st.markdown(f"""
        <div style="background: {c_style['bg']}; border: {c_style['border']}; box-shadow: {c_style['shadow']}; border-radius: 20px; padding: 18px; margin-bottom: 20px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h4 style="margin:0; color:{c_style['title_color']}; font-weight:800; font-size:1.05rem;">🪙 บอท Crypto Spot</h4>
                <span style="font-weight:800; font-size:1.05rem; background:{c_style['badge_bg']}; color:{c_style['badge_text']}; padding:4px 10px; border-radius:10px;">{c_style['pnl_sign']}฿{crypto_p['total_pnl_thb']:,.2f}</span>
            </div>
            <p style="color:{c_style['label_color']}; font-size:0.82rem; margin-top:4px; font-weight:600;">ทุน ฿80,000 บาท (20%)</p>
            <hr style="border-color:{hr_border}; margin:10px 0;">
            <div style="font-size:0.85rem; display:flex; justify-content:space-between; margin-bottom:4px; color:{c_style['title_color']};"><span>มูลค่าพอร์ต:</span> <strong>฿{crypto_p['current_equity']:,.2f}</strong></div>
            <div style="font-size:0.85rem; display:flex; justify-content:space-between; margin-bottom:4px; color:{c_style['title_color']};"><span>เงินสดคงเหลือ:</span> <strong>฿{crypto_p['cash_balance_thb']:,.2f}</strong></div>
            <div style="font-size:0.85rem; display:flex; justify-content:space-between; margin-bottom:4px; color:{c_style['title_color']};"><span>จำนวนที่ถือ:</span> <strong>{len(crypto_p['active_positions_detail'])} รายการ</strong></div>
            <div style="font-size:0.82rem; display:flex; justify-content:space-between; margin-top:6px; color:#10b981;"><span>🎯 Take Profit สะสม:</span> <strong>+฿{crypto_p.get('cumulative_take_profit_thb', 0.0):,.2f}</strong></div>
            <div style="font-size:0.82rem; display:flex; justify-content:space-between; color:#ef4444;"><span>🛑 Cut-Loss สะสม:</span> <strong>-฿{crypto_p.get('cumulative_cut_loss_thb', 0.0):,.2f}</strong></div>
        </div>
        """, unsafe_allow_html=True)

    with col_sys4:
        st.markdown(f"""
        <div style="background: {forex_style['bg']}; border: {forex_style['border']}; box-shadow: {forex_style['shadow']}; border-radius: 20px; padding: 18px; margin-bottom: 20px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h4 style="margin:0; color:{forex_style['title_color']}; font-weight:800; font-size:1.05rem;">💱 บอท Forex 24/5</h4>
                <span style="font-weight:800; font-size:1.05rem; background:{forex_style['badge_bg']}; color:{forex_style['badge_text']}; padding:4px 10px; border-radius:10px;">{forex_style['pnl_sign']}฿{forex_p['total_pnl_thb']:,.2f}</span>
            </div>
            <p style="color:{forex_style['label_color']}; font-size:0.82rem; margin-top:4px; font-weight:600;">ทุน ฿30,000 บาท (10%)</p>
            <hr style="border-color:{hr_border}; margin:10px 0;">
            <div style="font-size:0.85rem; display:flex; justify-content:space-between; margin-bottom:4px; color:{forex_style['title_color']};"><span>มูลค่าพอร์ต:</span> <strong>฿{forex_p['current_equity']:,.2f}</strong></div>
            <div style="font-size:0.85rem; display:flex; justify-content:space-between; margin-bottom:4px; color:{forex_style['title_color']};"><span>เงินสดคงเหลือ:</span> <strong>฿{forex_p['cash_balance_thb']:,.2f}</strong></div>
            <div style="font-size:0.85rem; display:flex; justify-content:space-between; margin-bottom:4px; color:{forex_style['title_color']};"><span>จำนวนที่ถือ:</span> <strong>{len(forex_p['active_positions_detail'])} รายการ</strong></div>
            <div style="font-size:0.82rem; display:flex; justify-content:space-between; margin-top:6px; color:#10b981;"><span>🎯 Take Profit สะสม:</span> <strong>+฿{forex_p.get('cumulative_take_profit_thb', 0.0):,.2f}</strong></div>
            <div style="font-size:0.82rem; display:flex; justify-content:space-between; color:#ef4444;"><span>🛑 Cut-Loss สะสม:</span> <strong>-฿{forex_p.get('cumulative_cut_loss_thb', 0.0):,.2f}</strong></div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    all_pos = unified_pnl['all_active_positions']
    if all_pos:
        df_all = pd.DataFrame(all_pos)
        def highlight_pnl(row):
            is_prof = row.get('is_profit', True)
            if is_prof: return ['background-color: rgba(16, 185, 129, 0.25); color: #059669; font-weight: 700;'] * len(row)
            else: return ['background-color: rgba(239, 68, 68, 0.25); color: #dc2626; font-weight: 700;'] * len(row)
        styled_df = df_all.style.apply(highlight_pnl, axis=1)
        if 'is_profit' in df_all.columns: styled_df = styled_df.hide(subset=['is_profit'], axis='columns')
        st.dataframe(styled_df, use_container_width=True)
    else: st.info("💡 ขณะนี้ไม่มีสินทรัพย์คงค้างในพอร์ตทั้ง 4 ระบบ")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("📅 ตารางบันทึกการส่งคำสั่งซื้อ-ขาย ทั้งหมด 4 ระบบ (Master Trade Logs)")
    df_master_summary = get_daily_market_summary()
    if not df_master_summary.empty: st.dataframe(df_master_summary, use_container_width=True)
    else: st.info("💡 ขณะนี้ยังไม่มีประวัติการส่งคำสั่งซื้อขาย")
    st.markdown('</div>', unsafe_allow_html=True)

# ==================== VIEW 2: BROKER API CREDENTIALS PAGE ====================
elif st.session_state.active_system == "BROKER_CONFIG":
    st.markdown('<div class="hero-title">🔑 ศูนย์ตั้งค่าและเชื่อมต่อ Broker API จริง 100%</div>', unsafe_allow_html=True)
    st.caption("กรอกรหัส API Keys และทดสอบการเชื่อมต่อกับ Broker จริงทุกระบบเพื่อเตรียมเทรดด้วยเงินจริง")
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    creds = bcm.load_credentials()
    
    # 1. SETTRADE OPEN API (THAI SET STOCKS)
    st.markdown("### 🇹🇭 1. หุ้นไทย (Settrade Open API / Streaming)")
    c_st1, c_st2 = st.columns(2)
    with c_st1:
        st_app_id = st.text_input("SETTRADE App ID:", value=creds.get("settrade", {}).get("app_id", ""), type="password", key="inp_pg_settrade_appid")
        st_app_secret = st.text_input("SETTRADE App Secret:", value=creds.get("settrade", {}).get("app_secret", ""), type="password", key="inp_pg_settrade_appsecret")
    with c_st2:
        st_broker_id = st.text_input("Broker ID (เช่น SANDBOX หรือ รหัสโบรกเกอร์):", value=creds.get("settrade", {}).get("broker_id", "SANDBOX"), key="inp_pg_settrade_brokerid")
        st_acc_no = st.text_input("Account No (เลขที่บัญชีซื้อขายหุ้น):", value=creds.get("settrade", {}).get("account_no", ""), key="inp_pg_settrade_accno")
        
    if st.button("🧪 ทดสอบการเชื่อมต่อ Settrade Open API", key="btn_pg_test_settrade"):
        ok_st, msg_st = bcm.test_settrade_connection(st_app_id, st_app_secret, st_broker_id)
        if ok_st: st.success(msg_st)
        else: st.error(msg_st)
        
    st.markdown("---")
    
    # 2. ALPACA LIVE TRADING API (US STOCKS)
    st.markdown("### 🇺🇸 2. หุ้นสหรัฐฯ (Alpaca Live Trading API)")
    c_alp1, c_alp2 = st.columns(2)
    with c_alp1:
        alp_key = st.text_input("Alpaca API Key ID:", value=creds.get("alpaca", {}).get("api_key", ""), type="password", key="inp_pg_alp_key")
        alp_secret = st.text_input("Alpaca Secret Key:", value=creds.get("alpaca", {}).get("secret_key", ""), type="password", key="inp_pg_alp_secret")
    with c_alp2:
        alp_env = st.selectbox("Alpaca Environment:", ["live (เงินจริง)", "paper (พอร์ตจำลอง)"], index=0 if creds.get("alpaca", {}).get("environment") == "live" else 1, key="inp_pg_alp_env")
        
    if st.button("🧪 ทดสอบการเชื่อมต่อ Alpaca API Live", key="btn_pg_test_alpaca"):
        is_live_env = ("live" in alp_env)
        ok_alp, msg_alp = bcm.test_alpaca_connection(alp_key, alp_secret, is_live=is_live_env)
        if ok_alp: st.success(msg_alp)
        else: st.error(msg_alp)

    st.markdown("---")
    
    # 3. BITKUB / BINANCE API (CRYPTO)
    st.markdown("### 🪙 3. คริปโทเคอร์เรนซี (Bitkub / Binance API)")
    c_bk1, c_bk2 = st.columns(2)
    with c_bk1:
        bk_key = st.text_input("Bitkub API Key:", value=creds.get("bitkub", {}).get("api_key", ""), type="password", key="inp_pg_bk_key")
        bk_secret = st.text_input("Bitkub API Secret:", value=creds.get("bitkub", {}).get("api_secret", ""), type="password", key="inp_pg_bk_secret")
    with c_bk2:
        bn_key = st.text_input("Binance API Key (Optional):", value=creds.get("binance", {}).get("api_key", ""), type="password", key="inp_pg_bn_key")
        bn_secret = st.text_input("Binance API Secret (Optional):", value=creds.get("binance", {}).get("api_secret", ""), type="password", key="inp_pg_bn_secret")

    if st.button("🧪 ทดสอบการเชื่อมต่อ Bitkub API", key="btn_pg_test_bitkub"):
        ok_bk, msg_bk = bcm.test_bitkub_connection(bk_key, bk_secret)
        if ok_bk: st.success(msg_bk)
        else: st.error(msg_bk)

    st.markdown("---")

    # 4. METATRADER 5 (FOREX & GOLD)
    st.markdown("### 💱 4. Forex & ทองคำ (MetaTrader 5 API)")
    c_mt1, c_mt2, c_mt3 = st.columns(3)
    with c_mt1:
        mt_acc = st.text_input("MT5 Account ID:", value=creds.get("mt5", {}).get("account_id", ""), key="inp_pg_mt_acc")
    with c_mt2:
        mt_pass = st.text_input("MT5 Password:", value=creds.get("mt5", {}).get("password", ""), type="password", key="inp_pg_mt_pass")
    with c_mt3:
        mt_server = st.text_input("MT5 Server (เช่น IC-Markets):", value=creds.get("mt5", {}).get("server", ""), key="inp_pg_mt_server")

    if st.button("🧪 ทดสอบการเชื่อมต่อ MetaTrader 5 API", key="btn_pg_test_mt5"):
        ok_mt, msg_mt = bcm.test_mt5_connection(mt_acc, mt_server)
        if ok_mt: st.success(msg_mt)
        else: st.error(msg_mt)

    st.markdown("---")

    if st.button("💾 บันทึกการตั้งค่า API Keys ของทุก Broker ทั้งหมด", key="btn_pg_save_all_creds", use_container_width=True):
        new_creds = {
            "settrade": {"app_id": st_app_id, "app_secret": st_app_secret, "broker_id": st_broker_id, "account_no": st_acc_no},
            "alpaca": {"api_key": alp_key, "secret_key": alp_secret, "environment": "live" if "live" in alp_env else "paper"},
            "bitkub": {"api_key": bk_key, "api_secret": bk_secret},
            "binance": {"api_key": bn_key, "api_secret": bn_secret},
            "mt5": {"account_id": mt_acc, "password": mt_pass, "server": mt_server}
        }
        if bcm.save_credentials(new_creds):
            st.success("🎉 บันทึกการตั้งค่า API Keys สำเร็จ 100%! ระบบพร้อมทำงานในโหมดเงินจริง (LIVE BROKER MODE)")
            st.session_state.active_system = "UNIFIED"
            st.rerun()
        else:
            st.error("เกิดข้อผิดพลาดในการบันทึกไฟล์ API Credentials")

    st.markdown('</div>', unsafe_allow_html=True)

# ==================== VIEW 3: FULL DETAILED VIEW PER SYSTEM ====================
else:
    target_cat = st.session_state.active_system
    if target_cat == "US_INDEX":
        sys_title = "🇺🇸 ระบบเทรดดัชนีหุ้นสหรัฐฯ (S&P 500 / NASDAQ / Dow Jones Bot - ทุน ฿100,000)"
        watchlist_options = config.US_INDEX_WATCHLIST
        default_sym = "SPY"
        market_badge_text = check_us_market_status(now_dt)
    elif target_cat == "GOLD":
        sys_title = "🥇 บอททองคำอัจฉริยะ (Gold Bot - ทุน ฿90,000)"
        watchlist_options = config.GOLD_WATCHLIST
        default_sym = "GC=F"
        market_badge_text = check_forex_market_status(now_dt)
    elif target_cat == "FOREX":
        sys_title = "💱 บอท Forex อัจฉริยะ 24/5 (Forex Quant Bot - ทุน ฿30,000)"
        watchlist_options = config.FOREX_WATCHLIST
        default_sym = "EURUSD=X"
        market_badge_text = check_forex_market_status(now_dt)
    else: # CRYPTO
        sys_title = "🪙 ระบบเทรดคริปโทเคอร์เรนซี 24/7 (Crypto Quant Bot - ทุน ฿80,000)"
        watchlist_options = config.CRYPTO_WATCHLIST
        default_sym = "BTC-USD"
        market_badge_text = check_crypto_market_status()

    st.markdown(f'<div class="hero-title">{sys_title}</div>', unsafe_allow_html=True)
    
    @st.fragment(run_every=15)
    def render_live_sys_header(sys_cat):
        now_dt = get_thai_now_naive()
        now_str = now_dt.strftime('%H:%M:%S น.')
        init_cap = config.SYSTEM_ALLOCATIONS.get(sys_cat, 100000.0)
        p_data = get_system_pnl(sys_cat, initial_capital=init_cap)
        p_color = "#059669" if p_data['total_pnl_thb'] >= 0 else "#dc2626"
        p_sign = "+" if p_data['total_pnl_thb'] >= 0 else ""
        tot_thb = p_data['total_pnl_thb']
        tot_pct = p_data['total_pnl_pct']
        cash_val = p_data['cash_balance_thb']
        inv_val = p_data['invested_cash_thb']
        eq_val = p_data['current_equity']
        
        active_strat_name = config.STRATEGY_CATALOG.get(get_active_strategy(sys_cat), {}).get('name', 'Trend Following')
        sys_header_html = (
            f'<div style="background: {glass_card_bg}; backdrop-filter: blur(16px); border: {glass_card_border}; border-radius: 16px; padding: 18px 22px; margin-bottom: 20px;">'
            f'<div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px; margin-bottom:14px;">'
            f'<div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">'
            f'<span style="background: rgba(16, 185, 129, 0.25); border: 1px solid rgba(16, 185, 129, 0.6); color: {app_text}; padding: 5px 14px; border-radius: 20px; font-weight: 800; font-size: 0.82rem;">🤖 {sys_cat} AI AUTO-PILOT ON</span>'
            f'<span style="background: rgba(99, 102, 241, 0.25); border: 1px solid rgba(99, 102, 241, 0.6); color: {app_text}; padding: 5px 14px; border-radius: 20px; font-weight: 800; font-size: 0.82rem;">⚙️ กลยุทธ์ที่รันอยู่: {active_strat_name}</span>'
            f'<span style="background: rgba(59, 130, 246, 0.2); border: 1px solid rgba(59, 130, 246, 0.4); color: {app_text}; padding: 5px 12px; border-radius: 20px; font-weight: 700; font-size: 0.8rem;">{market_badge_text}</span>'
            f'<span style="color: {metric_label_color}; font-weight: 700; font-size: 0.85rem;">⏰ {now_str} (Realtime Live)</span>'
            f'</div><div><span style="color: {p_color}; font-size: 1.2rem; font-weight: 800;">กำไร/ขาดทุนรวม ({sys_cat}): {p_sign}฿{tot_thb:,.2f} ({p_sign}{tot_pct:.2f}%)</span></div></div>'
            f'<div style="display:flex; gap:14px; border-top: 1px solid rgba(0, 0, 0, 0.1); padding-top: 14px; flex-wrap:wrap;">'
            f'<div style="flex:1; min-width:180px; background: {metric_card_bg}; padding: 12px 16px; border-radius: 14px; border: 1px solid rgba(56, 189, 248, 0.4);"><div style="font-size:0.85rem; color:{metric_label_color}; font-weight:700;">💵 เงินสดคงเหลือ (Realtime Cash):</div><div style="font-size:1.45rem; color:#2563eb; font-weight:800;">฿{cash_val:,.2f}</div></div>'
            f'<div style="flex:1; min-width:180px; background: {metric_card_bg}; padding: 12px 16px; border-radius: 14px; border: 1px solid rgba(168, 85, 247, 0.4);"><div style="font-size:0.85rem; color:{metric_label_color}; font-weight:700;">💼 มูลค่าถือครอง (Invested):</div><div style="font-size:1.45rem; color:#7c3aed; font-weight:800;">฿{inv_val:,.2f}</div></div>'
            f'<div style="flex:1; min-width:180px; background: {metric_card_bg}; padding: 12px 16px; border-radius: 14px; border: 1px solid rgba(0, 0, 0, 0.15);"><div style="font-size:0.85rem; color:{metric_label_color}; font-weight:700;">🏦 มูลค่าพอร์ตรวม (Equity):</div><div style="font-size:1.45rem; color:{title_color}; font-weight:800;">฿{eq_val:,.2f}</div></div>'
            f'</div></div>'
        )
        st.markdown(sys_header_html, unsafe_allow_html=True)

    render_live_sys_header(target_cat)
    init_cap_main = config.SYSTEM_ALLOCATIONS.get(target_cat, 100000.0)
    pnl_data = get_system_pnl(target_cat, initial_capital=init_cap_main)
    
    # Sidebar Master AI Robot Toggle Switch (ON / OFF)
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🤖 สวิตช์หลักควบคุม AI Auto-Trading")
    is_robot_on = get_robot_status()
    btn_status_label = "🟢 เปิดทำงานอยู่ (ON 24/7)" if is_robot_on else "🔴 ปิดทำงานชั่วคราว (OFF/PAUSED)"
    
    if st.sidebar.button(f"สลับสถานะ: {btn_status_label}", use_container_width=True):
        new_status = not is_robot_on
        ok, status_msg = set_robot_status(new_status)
        if ok:
            st.sidebar.success(status_msg)
            st.rerun()

    # Sidebar Sub-Controls
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"### ⚙️ เลือกสินทรัพย์หมวด {target_cat}")
    stock_input_type = st.sidebar.radio("🔍 วิธีเลือกสินทรัพย์:", ["เลือกจากรายการแนะนำ", "พิมพ์ชื่อสินทรัพย์เอง"])
    if stock_input_type == "เลือกจากรายการแนะนำ":
        selected_symbol = st.sidebar.selectbox("🎯 รายการสินทรัพย์:", watchlist_options, index=0)
    else:
        custom_symbol = st.sidebar.text_input("✍️ พิมพ์สัญลักษณ์ (เช่น AAPL, BTC-USD, GC=F):", value=default_sym)
        selected_symbol = custom_symbol.strip().upper()
        
    # Navigation Tabs (Full Rich 7-Tab View)
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 สรุปยอด กำไร/ขาดทุน",
        "💼 สินทรัพย์ที่ถือครองขณะนี้", 
        "📈 สัญญาณ ซื้อ-ขาย ล่าสุด", 
        "🤖 ให้ AI ช่วยวิเคราะห์", 
        "⚡ สแกน & ออโต้เทรด 24/7",
        "🧠 Ultra-Smart Quant Backtester",
        "🔑 ตั้งค่าและเชื่อมต่อ Broker API จริง"
    ])
    
    # TAB 1: SUMMARY & PNL BREAKDOWN
    with tab1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader(f"📊 สรุปผลตอบแทน กำไร/ขาดทุน พอร์ต {target_cat}")
        col_t1, col_t2, col_t3, col_t4, col_t5 = st.columns(5)
        def format_pnl_html(val):
            color = "#059669" if val >= 0 else "#dc2626"
            sign = "+" if val >= 0 else ""
            return f'<div style="font-size:1.5rem; font-weight:800; color:{color};">{sign}฿{val:,.2f}</div>'

        with col_t1: st.markdown(f'<div class="metric-card"><div class="metric-label">วันนี้ (Today PnL)</div>{format_pnl_html(pnl_data["pnl_today"])}</div>', unsafe_allow_html=True)
        with col_t2: st.markdown(f'<div class="metric-card"><div class="metric-label">เมื่อวาน (vs Yesterday)</div>{format_pnl_html(pnl_data["pnl_yesterday"])}</div>', unsafe_allow_html=True)
        with col_t3: st.markdown(f'<div class="metric-card"><div class="metric-label">รอบ 3 วัน (3-Day PnL)</div>{format_pnl_html(pnl_data["pnl_3days"])}</div>', unsafe_allow_html=True)
        with col_t4: st.markdown(f'<div class="metric-card"><div class="metric-label">รอบ 1 อาทิตย์ (7-Day PnL)</div>{format_pnl_html(pnl_data["pnl_7days"])}</div>', unsafe_allow_html=True)
        with col_t5: st.markdown(f'<div class="metric-card"><div class="metric-label">ภาพรวมทั้งหมด (Total PnL)</div>{format_pnl_html(pnl_data["total_pnl_thb"])}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # TAB 2: ACTIVE HOLDINGS & FORCE SELL CONTROL
    with tab2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader(f"💼 รายการสินทรัพย์ที่ถือครองอยู่ในพอร์ตขณะนี้ ({target_cat})")
        holdings = pnl_data.get('active_positions_detail', [])
        if holdings:
            df_holdings = pd.DataFrame(holdings)
            def highlight_pnl_row(row):
                is_profit = row.get('is_profit', True)
                if is_profit: return ['background-color: rgba(16, 185, 129, 0.25); color: #059669; font-weight: 700;'] * len(row)
                else: return ['background-color: rgba(239, 68, 68, 0.25); color: #dc2626; font-weight: 700;'] * len(row)

            df_display = df_holdings.copy()
            styled_df = df_display.style.apply(highlight_pnl_row, axis=1)
            if 'is_profit' in df_display.columns: styled_df = styled_df.hide(subset=['is_profit'], axis='columns')
            st.dataframe(styled_df, use_container_width=True)

            st.markdown("---")
            st.markdown("### 🚨 แผงควบคุมสั่งบังคับขายฉุกเฉิน (Force Sell Controls)")
            st.warning("⚠️ การกดปุ่มบังคับขายจะปิดออเดอร์สินทรัพย์นั้นทันทีที่ราคาตลาดเรียลไทม์ และส่งการแจ้งเตือนรายละเอียดเข้า Telegram ทันที")
            
            for idx, item in enumerate(holdings):
                sym_name = item.get('ชื่อสินทรัพย์', '')
                raw_sym = item.get('raw_symbol', sym_name)
                shares_val = float(item.get('จำนวนหน่วย', item.get('จำนวนหุ้น/หน่วย', 0)))
                curr_price_str = str(item.get('ราคาตลาด (Realtime)', '0')).replace('฿', '').replace(',', '').strip()
                try:
                    curr_price_val = float(curr_price_str)
                except Exception:
                    curr_price_val = 0.0
                    
                pnl_str = item.get('กำไร/ขาดทุน (บาท)', '฿0.00')
                pnl_pct_str = item.get('กำไร/ขาดทุน (%)', '0.00%')
                
                col_f1, col_f2, col_f3, col_f4 = st.columns([2, 2, 2, 2])
                with col_f1:
                    st.markdown(f"**{sym_name}** (`{raw_sym}`)")
                with col_f2:
                    st.markdown(f"จำนวน: `{shares_val}` หน่วย")
                with col_f3:
                    st.markdown(f"กำไร/ขาดทุน: `{pnl_str}` ({pnl_pct_str})")
                with col_f4:
                    if st.button(f"🚨 บังคับขาย {sym_name}", key=f"force_sell_{idx}_{raw_sym}", use_container_width=True):
                        with st.spinner(f"กำลังส่งคำสั่งบังคับขาย {sym_name}..."):
                            ok_fs, msg_fs = execute_force_sell(raw_sym, shares_val, curr_price_val)
                            if ok_fs:
                                st.success(msg_fs)
                                st.rerun()
                            else:
                                st.error(msg_fs)
        else:
            st.info(f"💡 ขณะนี้ไม่มีสินทรัพย์คงค้างในพอร์ตหมวด {target_cat} (ถือเงินสด 100% เพื่อรอสัญญาณจังหวะซื้อรอบใหม่)")
        st.markdown('</div>', unsafe_allow_html=True)

    # TAB 3: SIGNALS & CHART WITH MULTI-TIMEFRAME
    with tab3:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        display_chart_title = "GOLD (ทองคำ)" if selected_symbol in ["GC=F", "XAUUSD=X"] else selected_symbol.replace("-USD", "").replace("=X", "")
        st.subheader(f"📈 กราฟราคาและสัญญาณ ซื้อ-ขาย สำหรับ: {display_chart_title}")
        
        col_tf1, col_tf2 = st.columns([2, 1])
        with col_tf1:
            timeframe_option = st.radio(
                "⏱️ เลือก Timeframe แท่งเทียน:",
                ["⚡ 15 นาที (15M)", "⏱️ 1 ชั่วโมง (1H)", "📊 1 วัน (1D - Swing)", "📅 1 สัปดาห์ (1W)", "🗓️ 1 เดือน (1M)"],
                index=2,
                horizontal=True
            )
        with col_tf2:
            period_override = st.selectbox("📅 ช่วงเวลาย้อนหลัง (Period):", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=2)
            
        if "15 นาที" in timeframe_option:
            period_used = "1mo" if period_override in ["2y", "5y", "1y"] else period_override
            interval_used = "15m"
        elif "1 ชั่วโมง" in timeframe_option:
            period_used = "1mo" if period_override in ["2y", "5y", "1y"] else period_override
            interval_used = "1h"
        elif "1 สัปดาห์" in timeframe_option:
            period_used = period_override if period_override in ["1y", "2y", "5y"] else "2y"
            interval_used = "1wk"
        elif "1 เดือน" in timeframe_option:
            period_used = "5y" if period_override in ["1mo", "3mo", "6mo"] else period_override
            interval_used = "1mo"
        else:
            period_used = period_override
            interval_used = "1d"
            
        df_data = fetch_stock_data(selected_symbol, period=period_used, interval=interval_used)
        if not df_data.empty:
            df_signals = generate_quant_signal(df_data, strategy_key=st.session_state.current_active_strategy)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.06, row_heights=[0.72, 0.28])
            fig.add_trace(go.Candlestick(
                x=df_signals.index, open=df_signals['Open'], high=df_signals['High'], low=df_signals['Low'], close=df_signals['Close'], name="ราคา"
            ), row=1, col=1)
            
            if 'EMA_20' in df_signals.columns:
                fig.add_trace(go.Scatter(x=df_signals.index, y=df_signals['EMA_20'], line=dict(color='#38bdf8', width=1.5), name="EMA 20"), row=1, col=1)
                
            buys = df_signals[df_signals['Signal'] == 1]
            sells = df_signals[df_signals['Signal'] == -1]
            
            fig.add_trace(go.Scatter(
                x=buys.index, y=buys['Close'], mode='markers',
                marker=dict(symbol='triangle-up', size=15, color='#10b981', line=dict(width=1.5, color='white')),
                name="🟢 จุดเข้าซื้อ (BUY)"
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(
                x=sells.index, y=sells['Close'], mode='markers',
                marker=dict(symbol='triangle-down', size=15, color='#ef4444', line=dict(width=1.5, color='white')),
                name="🔴 จุดขาย (SELL)"
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(x=df_signals.index, y=df_signals['RSI'], line=dict(color='#c084fc', width=1.5), name="RSI (14)"), row=2, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", row=2, col=1)
            fig.add_hline(y=40, line_dash="dash", line_color="#10b981", row=2, col=1)
            
            fig.update_layout(
                template=plotly_template, paper_bgcolor="rgba(0,0,0,0)",
                height=540, margin=dict(l=20, r=20, t=30, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"ไม่สามารถโหลดข้อมูลสำหรับ {selected_symbol} ได้ กรุณาตรวจสอบชื่อสัญลักษณ์อีกครั้ง")
        st.markdown('</div>', unsafe_allow_html=True)

    # TAB 4: GEMINI AI ANALYST
    with tab4:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader(f"🤖 ให้ Gemini AI ช่วยวิเคราะห์: {display_chart_title}")
        if st.button(f"🔍 สแกนข่าว & วิเคราะห์ {display_chart_title} ด้วย Gemini AI"):
            with st.spinner("AI กำลังกวาดอ่านข่าวและประเมินคะแนน..."):
                ai_res = analyze_stock_sentiment(selected_symbol)
                score = ai_res.get('sentiment_score', 0.0)
                score_color = "#059669" if score >= 0.1 else ("#dc2626" if score <= -0.1 else "#d97706")
                st.markdown(f"### คะแนน AI Sentiment Score: <span style='color:{score_color}; font-weight:800;'>{score:+.2f}</span>", unsafe_allow_html=True)
                st.write(f"**บทวิเคราะห์ AI:** {ai_res.get('summary', '')}")
                st.write(f"**ความเสี่ยงหลัก:** {ai_res.get('key_risk', '')}")
                st.write(f"**คำแนะนำของ AI:** **{ai_res.get('action', 'HOLD')}**")
        st.markdown('</div>', unsafe_allow_html=True)

    # TAB 5: AUTOTRADER CONTROL & LOGS
    with tab5:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader(f"⚡ ระบบ AI Auto-Pilot สั่งซื้อขายอัตโนมัติ 24/7 สำหรับหมวด {target_cat}")
        if st.button("🤖 รันวงรอบสแกนและตัดสินใจซื้อขายทันที"):
            with st.spinner("กำลังสแกนสัญญาณ Trading และวิเคราะห์ข่าว..."):
                autotrader_daemon.run_autotrader_cycle()
                st.success(f"สแกนและประมวลผลออเดอร์หมวด {target_cat} เรียบร้อยแล้ว!")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # TAB 6: ULTRA-SMART QUANT BACKTESTER & INSTITUTIONAL ENGINE
    with tab6:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("🧠 Institutional Quant Engine & Backtesting (ทดสอบจำลองผลตอบแทนย้อนหลัง 3 ปี)")
        st.info("💡 **ระบบจำลองสถิติระดับสถาบันการเงิน:** ทดสอบกลยุทธ์ย้อนหลัง พร้อมประเมินค่า Sharpe Ratio, Win Rate %, Max Drawdown %, Dynamic Kelly Criterion Sizing และ Multi-Timeframe Alignment")
        
        col_bt1, col_bt2, col_bt3 = st.columns([2, 2, 1])
        with col_bt1:
            bt_symbol = st.selectbox("🎯 เลือกสินทรัพย์ทดสอบ Backtest:", watchlist_options, index=0)
        with col_bt2:
            bt_period = st.selectbox("📅 ช่วงเวลาย้อนหลัง (Period):", ["1y", "2y", "3y", "5y"], index=1)
        with col_bt3:
            st.write("")
            st.write("")
            run_bt_btn = st.button("🚀 รัน Backtest ย้อนหลัง", use_container_width=True)
            
        if run_bt_btn:
            with st.spinner(f"กำลังจำลองการเทรดย้อนหลัง {bt_period} สำหรับ {bt_symbol}..."):
                res_bt = run_historical_backtest(symbol=bt_symbol, period=bt_period, strategy_key=st.session_state.current_active_strategy)
                if res_bt.get("success"):
                    st.success(f"จำลองการเทรดย้อนหลังสำเร็จ! (จำนวนออเดอร์ทั้งหมด: {res_bt['total_trades']} รายการ)")
                    
                    # Metrics Grid
                    bm1, bm2, bm3, bm4, bm5 = st.columns(5)
                    ret_color = "#059669" if res_bt['total_return_pct'] >= 0 else "#dc2626"
                    with bm1: st.markdown(f'<div class="metric-card"><div class="metric-label">ผลตอบแทนรวม (%)</div><div style="font-size:1.5rem; font-weight:800; color:{ret_color};">{res_bt["total_return_pct"]:+.2f}%</div></div>', unsafe_allow_html=True)
                    with bm2: st.markdown(f'<div class="metric-card"><div class="metric-label">อัตราการชนะ (Win Rate)</div><div style="font-size:1.5rem; font-weight:800; color:#3b82f6;">{res_bt["win_rate_pct"]:.1f}%</div></div>', unsafe_allow_html=True)
                    with bm3: st.markdown(f'<div class="metric-card"><div class="metric-label">Max Drawdown (MDD)</div><div style="font-size:1.5rem; font-weight:800; color:#ef4444;">{res_bt["max_drawdown_pct"]:.2f}%</div></div>', unsafe_allow_html=True)
                    with bm4: st.markdown(f'<div class="metric-card"><div class="metric-label">Sharpe Ratio</div><div style="font-size:1.5rem; font-weight:800; color:#8b5cf6;">{res_bt["sharpe_ratio"]:.2f}</div></div>', unsafe_allow_html=True)
                    with bm5: st.markdown(f'<div class="metric-card"><div class="metric-label">Profit Factor</div><div style="font-size:1.5rem; font-weight:800; color:#10b981;">{res_bt["profit_factor"]:.2f}</div></div>', unsafe_allow_html=True)
                    
                    # Equity Curve Chart
                    eq_df = res_bt.get("equity_df")
                    if isinstance(eq_df, pd.DataFrame) and not eq_df.empty:
                        fig_eq = go.Figure()
                        fig_eq.add_trace(go.Scatter(x=eq_df['Date'], y=eq_df['Equity'], mode='lines', line=dict(color='#10b981', width=2), name="มูลค่าพอร์ตรวม (THB)"))
                        fig_eq.update_layout(
                            title=f"📈 Equity Curve พอร์ตการลงทุนย้อนหลัง {bt_period} ({bt_symbol})",
                            template=plotly_template, paper_bgcolor="rgba(0,0,0,0)", height=400, margin=dict(l=20, r=20, t=40, b=20)
                        )
                        st.plotly_chart(fig_eq, use_container_width=True)
                        
                    # Trades History Table
                    trades_hist = res_bt.get("trades_history", [])
                    if trades_hist:
                        with st.expander("🔍 คลิกดูตารางรายละเอียดออเดอร์ย้อนหลังทั้งหมด"):
                            st.dataframe(pd.DataFrame(trades_hist), use_container_width=True)
                else:
                    st.error(f"เกิดข้อผิดพลาดในการทำ Backtest: {res_bt.get('error')}")
        st.markdown('</div>', unsafe_allow_html=True)

    # TAB 7: LIVE BROKER API CREDENTIALS CENTER
    with tab7:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("🔑 ศูนย์ตั้งค่าและเชื่อมต่อ Broker API จริง 100% (Broker API Credentials Center)")
        st.info("💡 **คำแนะนำด้านความปลอดภัย:** ข้อมูล API Keys ทั้งหมดจะถูกจัดเก็บไว้ในเครื่องคอมพิวเตอร์/เซิร์ฟเวอร์ของคุณเท่านั้น (ในไฟล์ `broker_credentials.json`) ไม่มีการส่งไปยังเซิร์ฟเวอร์ภายนอกใดๆ ทั้งสิ้น")
        
        creds = bcm.load_credentials()
        
        # 1. SETTRADE OPEN API (THAI SET STOCKS)
        st.markdown("### 🇹🇭 1. หุ้นไทย (Settrade Open API / Streaming)")
        c_st1, c_st2 = st.columns(2)
        with c_st1:
            st_app_id = st.text_input("SETTRADE App ID:", value=creds.get("settrade", {}).get("app_id", ""), type="password", key="inp_settrade_appid")
            st_app_secret = st.text_input("SETTRADE App Secret:", value=creds.get("settrade", {}).get("app_secret", ""), type="password", key="inp_settrade_appsecret")
        with c_st2:
            st_broker_id = st.text_input("Broker ID (เช่น SANDBOX หรือ รหัสโบรกเกอร์):", value=creds.get("settrade", {}).get("broker_id", "SANDBOX"), key="inp_settrade_brokerid")
            st_acc_no = st.text_input("Account No (เลขที่บัญชีซื้อขายหุ้น):", value=creds.get("settrade", {}).get("account_no", ""), key="inp_settrade_accno")
            
        if st.button("🧪 ทดสอบการเชื่อมต่อ Settrade Open API", key="btn_test_settrade"):
            ok_st, msg_st = bcm.test_settrade_connection(st_app_id, st_app_secret, st_broker_id)
            if ok_st: st.success(msg_st)
            else: st.error(msg_st)
            
        st.markdown("---")
        
        # 2. ALPACA LIVE TRADING API (US STOCKS)
        st.markdown("### 🇺🇸 2. หุ้นสหรัฐฯ (Alpaca Live Trading API)")
        c_alp1, c_alp2 = st.columns(2)
        with c_alp1:
            alp_key = st.text_input("Alpaca API Key ID:", value=creds.get("alpaca", {}).get("api_key", ""), type="password", key="inp_alp_key")
            alp_secret = st.text_input("Alpaca Secret Key:", value=creds.get("alpaca", {}).get("secret_key", ""), type="password", key="inp_alp_secret")
        with c_alp2:
            alp_env = st.selectbox("Alpaca Environment:", ["live (เงินจริง)", "paper (พอร์ตจำลอง)"], index=0 if creds.get("alpaca", {}).get("environment") == "live" else 1, key="inp_alp_env")
            
        if st.button("🧪 ทดสอบการเชื่อมต่อ Alpaca API Live", key="btn_test_alpaca"):
            is_live_env = ("live" in alp_env)
            ok_alp, msg_alp = bcm.test_alpaca_connection(alp_key, alp_secret, is_live=is_live_env)
            if ok_alp: st.success(msg_alp)
            else: st.error(msg_alp)

        st.markdown("---")
        
        # 3. BITKUB / BINANCE API (CRYPTO)
        st.markdown("### 🪙 3. คริปโทเคอร์เรนซี (Bitkub / Binance API)")
        c_bk1, c_bk2 = st.columns(2)
        with c_bk1:
            bk_key = st.text_input("Bitkub API Key:", value=creds.get("bitkub", {}).get("api_key", ""), type="password", key="inp_bk_key")
            bk_secret = st.text_input("Bitkub API Secret:", value=creds.get("bitkub", {}).get("api_secret", ""), type="password", key="inp_bk_secret")
        with c_bk2:
            bn_key = st.text_input("Binance API Key (Optional):", value=creds.get("binance", {}).get("api_key", ""), type="password", key="inp_bn_key")
            bn_secret = st.text_input("Binance API Secret (Optional):", value=creds.get("binance", {}).get("api_secret", ""), type="password", key="inp_bn_secret")

        if st.button("🧪 ทดสอบการเชื่อมต่อ Bitkub API", key="btn_test_bitkub"):
            ok_bk, msg_bk = bcm.test_bitkub_connection(bk_key, bk_secret)
            if ok_bk: st.success(msg_bk)
            else: st.error(msg_bk)

        st.markdown("---")

        # 4. METATRADER 5 (FOREX & GOLD)
        st.markdown("### 💱 4. Forex & ทองคำ (MetaTrader 5 API)")
        c_mt1, c_mt2, c_mt3 = st.columns(3)
        with c_mt1:
            mt_acc = st.text_input("MT5 Account ID:", value=creds.get("mt5", {}).get("account_id", ""), key="inp_mt_acc")
        with c_mt2:
            mt_pass = st.text_input("MT5 Password:", value=creds.get("mt5", {}).get("password", ""), type="password", key="inp_mt_pass")
        with c_mt3:
            mt_server = st.text_input("MT5 Server (เช่น IC-Markets):", value=creds.get("mt5", {}).get("server", ""), key="inp_mt_server")

        if st.button("🧪 ทดสอบการเชื่อมต่อ MetaTrader 5 API", key="btn_test_mt5"):
            ok_mt, msg_mt = bcm.test_mt5_connection(mt_acc, mt_server)
            if ok_mt: st.success(msg_mt)
            else: st.error(msg_mt)

        st.markdown("---")

        if st.button("💾 บันทึกการตั้งค่า API Keys ของทุก Broker ทั้งหมด", key="btn_save_all_creds", use_container_width=True):
            new_creds = {
                "settrade": {"app_id": st_app_id, "app_secret": st_app_secret, "broker_id": st_broker_id, "account_no": st_acc_no},
                "alpaca": {"api_key": alp_key, "secret_key": alp_secret, "environment": "live" if "live" in alp_env else "paper"},
                "bitkub": {"api_key": bk_key, "api_secret": bk_secret},
                "binance": {"api_key": bn_key, "api_secret": bn_secret},
                "mt5": {"account_id": mt_acc, "password": mt_pass, "server": mt_server}
            }
            if bcm.save_credentials(new_creds):
                st.success("🎉 บันทึกการตั้งค่า API Keys สำเร็จ 100%! ระบบพร้อมทำงานในโหมดเงินจริง (LIVE BROKER MODE)")
                st.rerun()
            else:
                st.error("เกิดข้อผิดพลาดในการบันทึกไฟล์ API Credentials")

        st.markdown('</div>', unsafe_allow_html=True)
