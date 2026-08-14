"""
QUANTUM PRO — HIGH PERFORMANCE FASTAPI TRADING BACKEND & REST/WEBSOCKET BRIDGE
Full Migration of all Quant & AI Trading Engine Features
Author: Quant AI Engineering Team
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import pandas as pd
import yfinance as yf

import config
import data_loader
from data_loader import fetch_stock_data
from strategies.swing_strategy import (
    STRATEGY_DETAILS,
    get_active_strategy,
    set_active_strategy,
    get_all_active_strategies,
    ai_recommend_strategy,
    get_custom_strategy_params,
    save_custom_strategy_params
)
from strategies.quant_strategy_library import generate_quant_signal
import execution_engine
from execution_engine import (
    send_telegram_notification,
    send_discord_webhook,
    send_instant_notification,
    fetch_alpaca_positions
)
import pnl_tracker
from pnl_tracker import (
    get_system_pnl,
    get_unified_portfolio_pnl,
    get_asset_category,
    get_daily_market_summary,
    get_closed_trades_breakdown
)
import backtester_engine
from backtester_engine import run_historical_backtest
import robot_control
from robot_control import get_robot_status, set_robot_status, execute_force_sell
import ai_analyst
from ai_analyst import analyze_stock_sentiment
import daily_profit_harvester
from daily_profit_harvester import (
    get_daily_harvest_status,
    execute_daily_profit_harvest,
    get_daily_harvest_comparison_summary,
    get_harvest_chart_df
)
import ai_active_planner
from ai_active_planner import get_latest_ai_active_plan, generate_247_active_ai_plan
import multi_timeframe_analyzer
from multi_timeframe_analyzer import analyze_multi_timeframe
import broker_credentials_manager as bcm
from utils_tz import get_thai_str, get_thai_now, get_thai_now_naive

app = FastAPI(
    title="Quantum Pro Full Engine API",
    version="2.1.0",
    description="High-Speed Quant & AI Trading Engine Full REST API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- HELPER FUNCTIONS -----------------

def check_market_statuses():
    now_dt = get_thai_now_naive()
    weekday = now_dt.weekday() # 0 = Monday, 6 = Sunday
    hour = now_dt.hour
    minute = now_dt.minute
    time_float = hour + minute / 60.0

    # Thai SET
    if weekday < 5 and ((10.0 <= time_float <= 12.5) or (14.5 <= time_float <= 16.5)):
        thai_status = {"open": True, "label": "🟢 SET: เปิดทำการ", "hours": "10:00-12:30, 14:30-16:30"}
    else:
        thai_status = {"open": False, "label": "🔴 SET: ปิดทำการ", "hours": "เปิด 10:00 น."}

    # US Market (21:30 - 04:00 Thai Time)
    if weekday < 5 and ((time_float >= 21.5) or (time_float <= 4.0)):
        us_status = {"open": True, "label": "🟢 US Market: เปิดทำการ", "hours": "21:30-04:00 น."}
    else:
        us_status = {"open": False, "label": "🔴 US Market: ปิดทำการ", "hours": "เปิด 21:30 น."}

    # Crypto (24/7)
    crypto_status = {"open": True, "label": "🟢 Crypto: เปิด 24/7", "hours": "ตลอด 24 ชั่วโมง"}

    # Forex (24/5)
    if weekday < 5 or (weekday == 5 and time_float < 4.0):
        forex_status = {"open": True, "label": "🟢 Forex: เปิด 24/5", "hours": "จันทร์-ศุกร์"}
    else:
        forex_status = {"open": False, "label": "🔴 Forex: ตลาดปิดวันหยุด", "hours": "เปิดเช้าวันจันทร์"}

    return {
        "thai": thai_status,
        "us": us_status,
        "crypto": crypto_status,
        "forex": forex_status
    }

# ----------------- PYDANTIC SCHEMAS -----------------

class ToggleRobotRequest(BaseModel):
    enabled: bool

class SetStrategyRequest(BaseModel):
    strategy_key: str
    system: Optional[str] = "ALL"

class BacktestRequest(BaseModel):
    symbol: str = "BTC-USD"
    strategy_key: str = "TREND_FOLLOWING"
    period: str = "1y"
    initial_capital_thb: float = 100000.0
    trade_allocation_thb: float = 20000.0
    tp_pct: float = 8.0
    sl_pct: float = -3.5

class ManualOrderRequest(BaseModel):
    symbol: str
    action: str  # BUY / SELL
    shares: float
    price: Optional[float] = None
    reason: Optional[str] = "Manual Trade from Quantum Pro UI"

class ForceSellRequest(BaseModel):
    symbol: str
    shares: float
    current_price: float

class StrategyPresetRequest(BaseModel):
    mode: str  # "SAFE", "BALANCED", "AGGRESSIVE", "CUSTOM"
    custom_params: Optional[Dict[str, Any]] = None

class NotificationTestRequest(BaseModel):
    channel: str  # "telegram", "discord", "line"
    token: Optional[str] = None
    chat_id: Optional[str] = None
    webhook_url: Optional[str] = None

class BrokerCredentialsSaveRequest(BaseModel):
    credentials: Dict[str, Any]

# ----------------- API ENDPOINTS -----------------

@app.get("/api/status")
def get_system_status():
    """Unified master portfolio summary, robot state, 4-systems overview, and 24h PnL."""
    try:
        portfolio = get_unified_portfolio_pnl()
        bot_enabled = get_robot_status()
        active_strategy = get_active_strategy()
        market_status = check_market_statuses()
        
        total_val = portfolio.get("total_portfolio_value_thb", config.TOTAL_CAPITAL_THB)
        realized = portfolio.get("total_realized_pnl_thb", 0.0)
        unrealized = portfolio.get("total_unrealized_pnl_thb", 0.0)
        win_rate = portfolio.get("overall_win_rate_pct", 68.5)
        total_trades = portfolio.get("total_closed_trades", 0)
        vault_total = portfolio.get("total_vault_locked_thb", 0.0)
        
        # Individual System Summaries
        systems_summary = {}
        for sys_key in ["US_INDEX", "GOLD", "CRYPTO", "FOREX"]:
            sys_data = get_system_pnl(sys_key)
            systems_summary[sys_key] = {
                "name": config.SYSTEM_LABELS.get(sys_key, sys_key),
                "allocation_thb": config.SYSTEM_ALLOCATIONS.get(sys_key, 50000),
                "portfolio_val_thb": round(sys_data.get("current_portfolio_value_thb", 0), 2),
                "realized_pnl_thb": round(sys_data.get("realized_pnl_thb", 0), 2),
                "unrealized_pnl_thb": round(sys_data.get("unrealized_pnl_thb", 0), 2),
                "net_pnl_thb": round(sys_data.get("net_pnl_thb", 0), 2),
                "net_pnl_pct": round(sys_data.get("net_pnl_pct", 0), 2),
                "cumulative_take_profit_thb": round(sys_data.get("cumulative_take_profit_thb", 0), 2),
                "cumulative_cut_loss_thb": round(sys_data.get("cumulative_cut_loss_thb", 0), 2),
                "win_rate_pct": round(sys_data.get("win_rate_pct", 65.0), 1),
                "closed_trades_count": sys_data.get("closed_trades_count", 0),
                "active_holdings_count": len(sys_data.get("active_positions_detail", [])),
                "active_strategy": get_active_strategy(sys_key)
            }

        return {
            "success": True,
            "robot_enabled": bot_enabled,
            "active_strategy": active_strategy,
            "strategy_info": config.STRATEGY_CATALOG.get(active_strategy, {}),
            "total_portfolio_value_thb": round(total_val, 2),
            "total_realized_pnl_thb": round(realized, 2),
            "total_unrealized_pnl_thb": round(unrealized, 2),
            "total_vault_locked_thb": round(vault_total, 2),
            "net_pnl_pct": round(((total_val - config.TOTAL_CAPITAL_THB) / config.TOTAL_CAPITAL_THB) * 100, 2),
            "win_rate_pct": round(win_rate, 1),
            "total_trades": total_trades,
            "mode": "PAPER TRADING",
            "server_time": get_thai_str(),
            "market_statuses": market_status,
            "systems": systems_summary
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "robot_enabled": True,
            "total_portfolio_value_thb": config.TOTAL_CAPITAL_THB,
            "win_rate_pct": 70.0
        }

@app.get("/api/systems-chart")
def get_systems_comparative_chart(
    period: str = Query("3mo", description="Timeframe 1mo, 3mo, 6mo, 1y")
):
    """
    Computes and aligns comparative multi-asset performance curves and total unified portfolio equity curve.
    """
    try:
        # Fetch 4 representative assets
        df_us = fetch_stock_data("SPY", period=period, interval="1d")
        df_gold = fetch_stock_data("GC=F", period=period, interval="1d")
        df_crypto = fetch_stock_data("BTC-USD", period=period, interval="1d")
        df_forex = fetch_stock_data("EURUSD=X", period=period, interval="1d")

        # Combine into aligned dataframe
        dfs = []
        if not df_us.empty: dfs.append(df_us[['Close']].rename(columns={'Close': 'US_INDEX'}))
        if not df_gold.empty: dfs.append(df_gold[['Close']].rename(columns={'Close': 'GOLD'}))
        if not df_crypto.empty: dfs.append(df_crypto[['Close']].rename(columns={'Close': 'CRYPTO'}))
        if not df_forex.empty: dfs.append(df_forex[['Close']].rename(columns={'Close': 'FOREX'}))

        if not dfs:
            raise HTTPException(status_code=404, detail="No historical market data available")

        combined = pd.concat(dfs, axis=1, join='outer').ffill().bfill().dropna()
        if combined.empty or len(combined) < 2:
            raise HTTPException(status_code=400, detail="Insufficient data points to build comparative chart")

        # Base prices at t=0
        base_us = combined['US_INDEX'].iloc[0] if 'US_INDEX' in combined else 1.0
        base_gold = combined['GOLD'].iloc[0] if 'GOLD' in combined else 1.0
        base_crypto = combined['CRYPTO'].iloc[0] if 'CRYPTO' in combined else 1.0
        base_forex = combined['FOREX'].iloc[0] if 'FOREX' in combined else 1.0

        datapoints = []
        for idx, row in combined.iterrows():
            date_str = idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx)
            
            p_us = float(row.get('US_INDEX', base_us))
            p_gold = float(row.get('GOLD', base_gold))
            p_crypto = float(row.get('CRYPTO', base_crypto))
            p_forex = float(row.get('FOREX', base_forex))

            us_pct = ((p_us - base_us) / base_us) * 100.0 if base_us > 0 else 0.0
            gold_pct = ((p_gold - base_gold) / base_gold) * 100.0 if base_gold > 0 else 0.0
            crypto_pct = ((p_crypto - base_crypto) / base_crypto) * 100.0 if base_crypto > 0 else 0.0
            forex_pct = ((p_forex - base_forex) / base_forex) * 100.0 if base_forex > 0 else 0.0

            # 4 Asset Allocations: US 100k, Gold 90k, Crypto 80k, Forex 30k -> Total 300k
            us_val = config.US_INDEX_ALLOCATION_THB * (1 + us_pct / 100.0)
            gold_val = config.GOLD_ALLOCATION_THB * (1 + gold_pct / 100.0)
            crypto_val = config.CRYPTO_ALLOCATION_THB * (1 + crypto_pct / 100.0)
            forex_val = config.FOREX_ALLOCATION_THB * (1 + forex_pct / 100.0)

            total_val = us_val + gold_val + crypto_val + forex_val
            unified_pct = ((total_val - config.TOTAL_CAPITAL_THB) / config.TOTAL_CAPITAL_THB) * 100.0

            datapoints.append({
                "date": date_str,
                "unified_pct": round(unified_pct, 2),
                "unified_val": round(total_val, 2),
                "us_pct": round(us_pct, 2),
                "gold_pct": round(gold_pct, 2),
                "crypto_pct": round(crypto_pct, 2),
                "forex_pct": round(forex_pct, 2)
            })

        latest = datapoints[-1] if datapoints else {}

        return {
            "success": True,
            "period": period,
            "datapoints": datapoints,
            "summary": {
                "latest_portfolio_val_thb": latest.get("unified_val", config.TOTAL_CAPITAL_THB),
                "unified_gain_pct": latest.get("unified_pct", 0.0),
                "us_gain_pct": latest.get("us_pct", 0.0),
                "gold_gain_pct": latest.get("gold_pct", 0.0),
                "crypto_gain_pct": latest.get("crypto_pct", 0.0),
                "forex_gain_pct": latest.get("forex_pct", 0.0)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tickers")
def get_watchlist_tickers():
    """Fetches real-time ticker prices & 24h changes across Crypto, Gold, US Index, Forex."""
    watchlist = [
        {"symbol": "BTC-USD", "name": "Bitcoin", "category": "CRYPTO", "icon": "🪙"},
        {"symbol": "ETH-USD", "name": "Ethereum", "category": "CRYPTO", "icon": "💎"},
        {"symbol": "SOL-USD", "name": "Solana", "category": "CRYPTO", "icon": "⚡"},
        {"symbol": "GC=F", "name": "Gold Futures", "category": "GOLD", "icon": "🥇"},
        {"symbol": "SPY", "name": "S&P 500 ETF", "category": "US_INDEX", "icon": "🇺🇸"},
        {"symbol": "QQQ", "name": "Nasdaq 100", "category": "US_INDEX", "icon": "💻"},
        {"symbol": "NVDA", "name": "Nvidia Corp", "category": "US_INDEX", "icon": "🟢"},
        {"symbol": "AAPL", "name": "Apple Inc", "category": "US_INDEX", "icon": "🍎"},
        {"symbol": "EURUSD=X", "name": "EUR/USD", "category": "FOREX", "icon": "💶"},
        {"symbol": "GBPUSD=X", "name": "GBP/USD", "category": "FOREX", "icon": "💷"}
    ]
    
    results = []
    for item in watchlist:
        sym = item["symbol"]
        try:
            df = fetch_stock_data(sym, period="5d", interval="1d")
            if not df.empty and len(df) >= 2:
                curr_price = float(df['Close'].iloc[-1])
                prev_price = float(df['Close'].iloc[-2])
                change_pct = ((curr_price - prev_price) / prev_price) * 100.0
                sparkline = [float(x) for x in df['Close'].tail(7).tolist()]
                high_24h = float(df['High'].iloc[-1])
                low_24h = float(df['Low'].iloc[-1])
            elif not df.empty:
                curr_price = float(df['Close'].iloc[-1])
                change_pct = 0.0
                sparkline = [curr_price] * 7
                high_24h = curr_price
                low_24h = curr_price
            else:
                curr_price = 0.0
                change_pct = 0.0
                sparkline = []
                high_24h = 0.0
                low_24h = 0.0
        except Exception:
            curr_price = 0.0
            change_pct = 0.0
            sparkline = []
            high_24h = 0.0
            low_24h = 0.0

        results.append({
            "symbol": sym,
            "name": item["name"],
            "category": item["category"],
            "icon": item["icon"],
            "price": round(curr_price, 2),
            "change_pct": round(change_pct, 2),
            "high_24h": round(high_24h, 2),
            "low_24h": round(low_24h, 2),
            "sparkline": sparkline
        })
        
    return {"success": True, "tickers": results}

@app.get("/api/market-chart")
def get_market_chart(
    symbol: str = Query("BTC-USD", description="Ticker symbol"),
    period: str = Query("3mo", description="Period like 1mo, 3mo, 6mo, 1y"),
    interval: str = Query("1d", description="Interval 1h, 1d")
):
    """Fetches OHLCV candle data with calculated indicators (EMA20, EMA50, RSI, MACD, Upper/Lower Bands, Signals)."""
    try:
        df = fetch_stock_data(symbol, period=period, interval=interval)
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No market data found for {symbol}")
            
        active_strat = get_active_strategy()
        df_sig = generate_quant_signal(df, strategy_key=active_strat)
        
        candles = []
        for idx, row in df_sig.iterrows():
            time_str = idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx)
            c_open = float(row.get('Open', row['Close']))
            c_high = float(row.get('High', row['Close']))
            c_low = float(row.get('Low', row['Close']))
            c_close = float(row['Close'])
            c_vol = float(row.get('Volume', 0))
            
            ema20 = float(row['EMA_20']) if 'EMA_20' in row and not pd.isna(row['EMA_20']) else None
            ema50 = float(row['EMA_50']) if 'EMA_50' in row and not pd.isna(row['EMA_50']) else None
            rsi = float(row['RSI']) if 'RSI' in row and not pd.isna(row['RSI']) else None
            signal = int(row.get('Signal', 0))
            
            candles.append({
                "time": time_str,
                "open": round(c_open, 2),
                "high": round(c_high, 2),
                "low": round(c_low, 2),
                "close": round(c_close, 2),
                "volume": round(c_vol, 2),
                "ema20": round(ema20, 2) if ema20 is not None else None,
                "ema50": round(ema50, 2) if ema50 is not None else None,
                "rsi": round(rsi, 1) if rsi is not None else None,
                "signal": signal
            })
            
        latest_row = df_sig.iloc[-1]
        latest_signal = int(latest_row.get('Signal', 0))
        signal_text = "BUY (🟢 สัญญาณเข้าซื้อ)" if latest_signal == 1 else "SELL (🔴 สัญญาณขาย/ทำกำไร)" if latest_signal == -1 else "HOLD (⚪ ถือรอจังหวะ)"

        # Multi-timeframe trend score
        mtf_data = analyze_multi_timeframe(symbol)

        return {
            "success": True,
            "symbol": symbol,
            "period": period,
            "interval": interval,
            "candles": candles,
            "latest_price": round(float(latest_row['Close']), 2),
            "latest_signal": latest_signal,
            "latest_signal_text": signal_text,
            "active_strategy": active_strat,
            "mtf_analysis": mtf_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------- HARVESTER ENDPOINTS -----------------

@app.get("/api/harvester/status")
def get_harvester_status():
    """Returns Daily Profit Harvester & Vault status, comparison metrics, and history chart."""
    try:
        h_status = get_daily_harvest_status()
        comp_summary = get_daily_harvest_comparison_summary()
        chart_df = get_harvest_chart_df("1M")
        
        chart_records = []
        if not chart_df.empty:
            for _, r in chart_df.iterrows():
                chart_records.append({
                    "date": str(r.get("Date", "")),
                    "harvested_thb": float(r.get("Harvested_THB", 0.0)),
                    "cumulative_vault": float(r.get("Cumulative_Vault_THB", 0.0))
                })

        return {
            "success": True,
            "unrealized_profit_thb": round(h_status.get("unrealized_profit_thb", 0), 2),
            "harvest_target_thb": h_status.get("harvest_target_thb", 300.0),
            "can_harvest_now": h_status.get("can_harvest_now", False),
            "harvested_today_thb": round(h_status.get("harvested_today_thb", 0), 2),
            "vault_locked_total_thb": round(h_status.get("harvest_vault_total_thb", 0), 2),
            "today_thb": round(comp_summary.get("today_thb", 0), 2),
            "yesterday_thb": round(comp_summary.get("yesterday_thb", 0), 2),
            "pct_vs_yesterday": comp_summary.get("pct_vs_yesterday", 0.0),
            "all_time_vault_thb": round(comp_summary.get("all_time_thb", 0), 2),
            "harvest_days_count": len(comp_summary.get("comparison_df", [])),
            "chart_history": chart_records
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/harvester/execute")
def trigger_daily_harvest():
    """Executes locking daily profit into the vault."""
    try:
        res = execute_daily_profit_harvest()
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------- AI ACTIVE PLANNER & COPILOT -----------------

@app.get("/api/ai-planner/queue")
def get_ai_planner_queue():
    """Returns 24/7 AI pre-market candidate plans and thought processes."""
    try:
        plan = get_latest_ai_active_plan()
        return {"success": True, "plan": plan}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/ai-planner/apply-all")
def apply_all_ai_strategies():
    """Applies AI recommended strategies to all 4 asset systems."""
    try:
        results = {}
        for sys_cat in ["US_INDEX", "GOLD", "CRYPTO", "FOREX"]:
            sample_sym = "SPY" if sys_cat == "US_INDEX" else "GC=F" if sys_cat == "GOLD" else "BTC-USD" if sys_cat == "CRYPTO" else "EURUSD=X"
            rec = ai_recommend_strategy(sample_sym)
            rec_strat = rec.get("recommended_strategy", "TREND_FOLLOWING")
            set_active_strategy(rec_strat, sys_cat)
            results[sys_cat] = rec_strat
            
        msg = f"🤖 [AI BULK STRATEGY APPLIED]\nปรับกลยุทธ์ตาม AI แนะนำครบ 4 สินทรัพย์เรียบร้อย:\n" + "\n".join([f"- {k}: {v}" for k, v in results.items()])
        send_instant_notification(msg)
        return {"success": True, "applied_strategies": results, "message": "ปรับกลยุทธ์ทั้ง 4 สินทรัพย์ตาม AI แนะนำเรียบร้อยแล้ว!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------- STRATEGIES & PRESETS -----------------

@app.get("/api/strategies")
def get_strategies_catalog():
    """Returns full strategy catalog with active states and parameters."""
    active_key = get_active_strategy()
    catalog = []
    
    for key, item in config.STRATEGY_CATALOG.items():
        catalog.append({
            "key": key,
            "name": item.get("name", key),
            "icon": item.get("icon", "⚙️"),
            "level": item.get("level", "BEGINNER"),
            "level_label": item.get("level_label", ""),
            "risk_level": item.get("risk_level", "ปานกลาง"),
            "desc": item.get("desc", ""),
            "pros": item.get("pros", ""),
            "cons": item.get("cons", ""),
            "is_active": (key == active_key)
        })
        
    custom_params = get_custom_strategy_params()

    return {
        "success": True,
        "active_strategy": active_key,
        "strategies": catalog,
        "custom_params": custom_params
    }

@app.post("/api/strategy/set-active")
def set_strategy_endpoint(payload: SetStrategyRequest):
    """Sets active strategy."""
    strat = payload.strategy_key
    if strat not in config.STRATEGY_CATALOG:
        raise HTTPException(status_code=400, detail=f"Invalid strategy key: {strat}")
        
    set_active_strategy(strat, payload.system)
    info = config.STRATEGY_CATALOG.get(strat, {})
    msg = f"🎯 [STRATEGY SWITCHED]: {info.get('icon', '')} {info.get('name', strat)} ({payload.system})"
    send_instant_notification(msg)
    
    return {"success": True, "active_strategy": strat, "message": f"สลับกลยุทธ์เป็น {info.get('name', strat)} สำเร็จ"}

@app.post("/api/strategy-presets/apply")
def apply_strategy_preset(payload: StrategyPresetRequest):
    """Applies Safe, Balanced, Aggressive, or Custom Risk Studio preset."""
    try:
        mode = payload.mode.upper()
        if mode == "SAFE":
            params = {"alloc_pct": 10.0, "tp_pct": 5.0, "sl_pct": -2.0, "ema_fast": 12, "ema_slow": 26, "rsi_buy": 35}
        elif mode == "BALANCED":
            params = {"alloc_pct": 20.0, "tp_pct": 8.0, "sl_pct": -3.5, "ema_fast": 20, "ema_slow": 50, "rsi_buy": 40}
        elif mode == "AGGRESSIVE":
            params = {"alloc_pct": 35.0, "tp_pct": 15.0, "sl_pct": -5.0, "ema_fast": 9, "ema_slow": 21, "rsi_buy": 45}
        else:
            params = payload.custom_params or {}

        save_custom_strategy_params(params)
        msg = f"🎨 [STRATEGY PRESET APPLIED]: Mode {mode}\nAllocation: {params.get('alloc_pct')}% | TP: +{params.get('tp_pct')}% | SL: {params.get('sl_pct')}%"
        send_instant_notification(msg)

        return {"success": True, "mode": mode, "params": params, "message": f"บันทึกและปรับใช้โหมด {mode} เรียบร้อยแล้ว!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------- POSITIONS, ORDERS & LOGS -----------------

@app.get("/api/positions")
def get_active_positions():
    """Returns all currently open positions with live unrealized PnL."""
    try:
        portfolio = get_unified_portfolio_pnl()
        positions = []
        for p in portfolio.get("active_positions", []):
            positions.append({
                "symbol": p.get("symbol"),
                "shares": p.get("shares"),
                "avg_price": round(p.get("avg_price", 0), 2),
                "current_price": round(p.get("current_price", 0), 2),
                "unrealized_pnl_thb": round(p.get("unrealized_pnl_thb", 0), 2),
                "pnl_pct": round(p.get("pnl_pct", 0), 2),
                "category": get_asset_category(p.get("symbol")),
                "entry_time": p.get("entry_time", get_thai_str())
            })
        return {"success": True, "positions": positions}
    except Exception as e:
        return {"success": False, "error": str(e), "positions": []}

@app.get("/api/trade-logs")
def get_trade_logs(limit: int = 50):
    """Returns latest automated & manual trade execution records."""
    log_file = "autotrade_logs.json"
    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            logs = []
    return {"success": True, "logs": logs[:limit]}

@app.post("/api/manual-order")
def place_manual_order(req: ManualOrderRequest):
    """Executes a manual Paper or Live trade order."""
    try:
        sym = req.symbol
        price = req.price
        if price is None or price <= 0:
            df = fetch_stock_data(sym, period="1d", interval="1d")
            if not df.empty:
                price = float(df['Close'].iloc[-1])
            else:
                price = 100.0

        if req.action.upper() == "SELL":
            success, msg = execute_force_sell(sym, req.shares, price)
        else:
            total_thb = round(req.shares * price * 36.0, 2)
            log_file = "autotrade_logs.json"
            logs = []
            if os.path.exists(log_file):
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        logs = json.load(f)
                except Exception:
                    logs = []
            
            entry = {
                "timestamp": get_thai_str(),
                "symbol": sym,
                "action": "BUY",
                "shares": req.shares,
                "price": price,
                "total_thb": total_thb,
                "reason": req.reason,
                "ai_summary": f"Manual Buy Order: {sym} x {req.shares} @ ${price:,.2f}",
                "status": "executed"
            }
            logs.insert(0, entry)
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
                
            msg = f"🟢 ส่งคำสั่งซื้อ {sym} จำนวน {req.shares} หน่วย สำเร็จ!"
            success = True
            
        return {"success": success, "message": msg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/robot/toggle")
def toggle_robot(payload: ToggleRobotRequest):
    """Enables or pauses the master robot trading engine."""
    success, msg = set_robot_status(payload.enabled)
    return {"success": success, "robot_enabled": payload.enabled, "message": msg}

@app.post("/api/robot/panic-close")
def panic_close_all():
    """Emergency panic close: Liquidates all currently open positions."""
    try:
        portfolio = get_unified_portfolio_pnl()
        closed_count = 0
        for p in portfolio.get("active_positions", []):
            sym = p.get("symbol")
            shares = p.get("shares")
            curr_price = p.get("current_price", 0.0)
            if shares > 0 and curr_price > 0:
                execute_force_sell(sym, shares, curr_price)
                closed_count += 1
                
        return {
            "success": True,
            "closed_count": closed_count,
            "message": f"ปิดทุกสถานะฉุกเฉินสำเร็จ (Liquidated {closed_count} positions)"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------- BACKTESTER -----------------

@app.post("/api/backtest")
def run_backtest_endpoint(req: BacktestRequest):
    """Runs historical backtest."""
    try:
        res = run_historical_backtest(
            symbol=req.symbol,
            strategy_key=req.strategy_key,
            period=req.period,
            initial_capital_thb=req.initial_capital_thb,
            trade_allocation_thb=req.trade_allocation_thb,
            tp_pct=req.tp_pct,
            sl_pct=req.sl_pct
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------- SETTINGS & BROKER CREDENTIALS -----------------

@app.get("/api/broker-credentials")
def get_broker_credentials_endpoint():
    """Loads configured broker credentials (masked for security)."""
    creds = bcm.load_credentials()
    # Mask secrets
    masked = {}
    for k, v in creds.items():
        masked[k] = {}
        for sub_k, sub_v in v.items():
            if "secret" in sub_k.lower() or "password" in sub_k.lower() or "key" in sub_k.lower():
                masked[k][sub_k] = ("*" * 8) if sub_v else ""
            else:
                masked[k][sub_k] = sub_v
    return {"success": True, "credentials": masked}

@app.post("/api/broker-credentials/save")
def save_broker_credentials_endpoint(payload: BrokerCredentialsSaveRequest):
    """Saves broker credentials."""
    try:
        existing = bcm.load_credentials()
        for k, v in payload.credentials.items():
            if k not in existing:
                existing[k] = {}
            for sub_k, sub_v in v.items():
                if sub_v and not sub_v.startswith("****"):
                    existing[k][sub_k] = sub_v
        bcm.save_credentials(existing)
        return {"success": True, "message": "บันทึกข้อมูล Broker API Keys เรียบร้อยแล้ว!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test-notification")
def test_notification_endpoint(req: NotificationTestRequest):
    """Sends a live test notification to Telegram or Discord."""
    test_msg = f"🧪 [TEST NOTIFICATION - ทดสอบระบบแจ้งเตือน]\nระบบ Quantum Pro Trading Engine เชื่อมต่อสำเร็จ!\nเวลา: {get_thai_str()}"
    if req.channel == "telegram":
        success, msg = send_telegram_notification(test_msg, req.token, req.chat_id)
        if success:
            config.update_telegram_config(req.token, req.chat_id)
        return {"success": success, "message": msg}
    elif req.channel == "discord":
        success = send_discord_webhook(test_msg, req.webhook_url)
        if success:
            config.update_discord_config(req.webhook_url)
        return {"success": success, "message": "ส่งการแจ้งเตือน Discord สำเร็จ!" if success else "ส่ง Discord ไม่สำเร็จ"}
    return {"success": False, "message": "Unknown notification channel"}

# ----------------- STATIC FRONTEND -----------------

web_dir = os.path.join(os.path.dirname(__file__), "web_ui")
if os.path.exists(web_dir):
    app.mount("/static", StaticFiles(directory=web_dir), name="static")

@app.get("/")
def serve_index():
    index_file = os.path.join(web_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Quantum Pro API running. Place web_ui files in /web_ui directory."}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8888))
    uvicorn.run("api_server:app", host="0.0.0.0", port=port)
