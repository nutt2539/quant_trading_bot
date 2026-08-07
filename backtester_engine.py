"""
BACKTESTING & WALK-FORWARD OPTIMIZATION ENGINE
Author: Quant AI Engineering Team
"""

import pandas as pd
import numpy as np
from data_loader import fetch_stock_data
from strategies.quant_strategy_library import generate_quant_signal
from volatility_engine import calculate_atr

def run_historical_backtest(
    symbol: str = "BTC-USD",
    strategy_key: str = "TREND_FOLLOWING",
    period: str = "2y",
    initial_capital_thb: float = 100000.0,
    trade_allocation_thb: float = 20000.0,
    tp_pct: float = 8.0,
    sl_pct: float = -3.5
) -> dict:
    """
    Runs historical backtest simulation over 2-3 years of real market data.
    Computes institutional performance metrics: Sharpe Ratio, Win Rate, Max Drawdown, Profit Factor.
    """
    try:
        df = fetch_stock_data(symbol, period=period, interval="1d")
        if df.empty or len(df) < 30:
            return {"success": False, "error": f"ข้อมูลย้อนหลัง {symbol} ไม่เพียงพอในการทำ Backtest"}
            
        df_sig = generate_quant_signal(df, strategy_key=strategy_key)
        df_sig['ATR'] = calculate_atr(df_sig, 14)
        
        cash = initial_capital_thb
        position_units = 0.0
        entry_price = 0.0
        trades_history = []
        equity_curve = []
        
        for i in range(len(df_sig)):
            row = df_sig.iloc[i]
            idx_val = df_sig.index[i]
            dt = idx_val.strftime('%Y-%m-%d') if hasattr(idx_val, 'strftime') else str(idx_val)
            close_price = float(row['Close'])
            signal = float(row.get('Signal', 0))
            
            # 1. Update Portfolio Value
            current_portfolio_value = cash + (position_units * close_price)
            equity_curve.append({
                "Date": dt,
                "Equity": current_portfolio_value
            })
            
            # 2. Check Exits if holding position
            if position_units > 0:
                pnl_pct = ((close_price - entry_price) / entry_price) * 100.0
                is_tp = (pnl_pct >= tp_pct)
                is_sl = (pnl_pct <= sl_pct)
                is_sig_sell = (signal == -1)
                
                if is_tp or is_sl or is_sig_sell:
                    sell_val = position_units * close_price
                    profit_thb = sell_val - (position_units * entry_price)
                    cash += sell_val
                    
                    reason = "TAKE_PROFIT" if is_tp else ("STOP_LOSS" if is_sl else "SIGNAL_SELL")
                    trades_history.append({
                        "entry_date": entry_dt,
                        "exit_date": dt,
                        "symbol": symbol,
                        "entry_price": entry_price,
                        "exit_price": close_price,
                        "pnl_pct": round(pnl_pct, 2),
                        "profit_thb": round(profit_thb, 2),
                        "reason": reason
                    })
                    position_units = 0.0
                    entry_price = 0.0
                    
            # 3. Check Entries if cash available
            elif position_units == 0 and signal == 1 and cash >= trade_allocation_thb:
                buy_val = min(trade_allocation_thb, cash)
                position_units = buy_val / close_price
                cash -= buy_val
                entry_price = close_price
                entry_dt = dt
                
        # 4. Performance Metrics Calculation
        eq_df = pd.DataFrame(equity_curve)
        if eq_df.empty:
            return {"success": False, "error": "ไม่สามารถคำนวณ Equity Curve ได้"}
            
        final_equity = cash + (position_units * df_sig.iloc[-1]['Close'])
        total_return_pct = ((final_equity - initial_capital_thb) / initial_capital_thb) * 100.0
        
        # Drawdown calculation
        eq_df['Peak'] = eq_df['Equity'].cummax()
        eq_df['Drawdown'] = (eq_df['Equity'] - eq_df['Peak']) / eq_df['Peak']
        max_drawdown_pct = eq_df['Drawdown'].min() * 100.0
        
        # Trades statistics
        winning_trades = [t for t in trades_history if t['profit_thb'] > 0]
        losing_trades = [t for t in trades_history if t['profit_thb'] <= 0]
        
        total_trades = len(trades_history)
        win_rate = (len(winning_trades) / total_trades * 100.0) if total_trades > 0 else 0.0
        
        total_wins_thb = sum(t['profit_thb'] for t in winning_trades)
        total_losses_thb = abs(sum(t['profit_thb'] for t in losing_trades))
        profit_factor = (total_wins_thb / total_losses_thb) if total_losses_thb > 0 else (99.9 if total_wins_thb > 0 else 0.0)
        
        # Sharpe Ratio (Daily returns annualized)
        eq_df['Daily_Return'] = eq_df['Equity'].pct_change()
        mean_ret = eq_df['Daily_Return'].mean()
        std_ret = eq_df['Daily_Return'].std()
        sharpe_ratio = (mean_ret / std_ret * np.sqrt(252)) if std_ret > 0 else 0.0
        
        return {
            "success": True,
            "symbol": symbol,
            "period": period,
            "strategy": strategy_key,
            "initial_capital_thb": initial_capital_thb,
            "final_equity_thb": round(final_equity, 2),
            "total_return_pct": round(total_return_pct, 2),
            "total_trades": total_trades,
            "win_rate_pct": round(win_rate, 2),
            "max_drawdown_pct": round(max_drawdown_pct, 2),
            "profit_factor": round(profit_factor, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "winning_count": len(winning_trades),
            "losing_count": len(losing_trades),
            "trades_history": trades_history,
            "equity_df": eq_df
        }
        
    except Exception as e:
        print(f"Error running backtest for {symbol}: {e}")
        return {"success": False, "error": str(e)}
