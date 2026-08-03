import pandas as pd
import numpy as np

def run_backtest(df: pd.DataFrame, initial_capital: float = 10000.0, stop_loss_pct: float = 0.05, take_profit_pct: float = 0.15) -> dict:
    """
    Backtests a trading strategy on historical DataFrame containing 'Signal' and 'Close'.
    Returns metrics (Total Return, Sharpe Ratio, Max Drawdown, Win Rate, Equity Curve).
    """
    if df.empty or 'Signal' not in df.columns:
        return {}

    df = df.copy()
    capital = initial_capital
    position = 0 # 0: Cash, >0: Number of shares
    entry_price = 0.0
    
    portfolio_history = []
    trades = []
    
    for date, row in df.iterrows():
        close = row['Close']
        signal = row['Signal']
        
        # Check Stop Loss / Take Profit if in position
        if position > 0:
            price_change = (close - entry_price) / entry_price
            if price_change <= -stop_loss_pct:
                # Stop Loss Triggered
                capital = position * close
                trades.append({'date': date, 'type': 'SELL (Stop Loss)', 'price': close, 'pnl_pct': price_change * 100})
                position = 0
            elif price_change >= take_profit_pct:
                # Take Profit Triggered
                capital = position * close
                trades.append({'date': date, 'type': 'SELL (Take Profit)', 'price': close, 'pnl_pct': price_change * 100})
                position = 0
        
        # Execute Strategy Signals
        if signal == 1 and position == 0:
            # Buy All In for backtest simulation
            position = capital / close
            entry_price = close
            trades.append({'date': date, 'type': 'BUY', 'price': close, 'pnl_pct': 0.0})
            
        elif signal == -1 and position > 0:
            # Sell Position
            pnl_pct = ((close - entry_price) / entry_price) * 100
            capital = position * close
            trades.append({'date': date, 'type': 'SELL (Signal)', 'price': close, 'pnl_pct': pnl_pct})
            position = 0
            
        # Calculate Current Equity
        current_equity = position * close if position > 0 else capital
        portfolio_history.append({'Date': date, 'Equity': current_equity, 'Close': close})
        
    df_equity = pd.DataFrame(portfolio_history).set_index('Date')
    
    if df_equity.empty:
        return {}

    # Performance Metrics
    total_return_pct = ((df_equity['Equity'].iloc[-1] - initial_capital) / initial_capital) * 100
    
    # Daily Returns
    df_equity['Daily_Return'] = df_equity['Equity'].pct_change().fillna(0)
    mean_daily = df_equity['Daily_Return'].mean()
    std_daily = df_equity['Daily_Return'].std()
    
    sharpe_ratio = (mean_daily / (std_daily + 1e-9)) * np.sqrt(252) if std_daily > 0 else 0.0
    
    # Max Drawdown
    df_equity['Peak'] = df_equity['Equity'].cummax()
    df_equity['Drawdown'] = (df_equity['Equity'] - df_equity['Peak']) / df_equity['Peak']
    max_drawdown_pct = abs(df_equity['Drawdown'].min()) * 100
    
    # Trade Stats
    sell_trades = [t for t in trades if 'SELL' in t['type']]
    win_trades = [t for t in sell_trades if t['pnl_pct'] > 0]
    win_rate_pct = (len(win_trades) / len(sell_trades)) * 100 if sell_trades else 0.0
    
    return {
        'initial_capital': initial_capital,
        'final_equity': round(df_equity['Equity'].iloc[-1], 2),
        'total_return_pct': round(total_return_pct, 2),
        'sharpe_ratio': round(sharpe_ratio, 2),
        'max_drawdown_pct': round(max_drawdown_pct, 2),
        'total_trades': len(sell_trades),
        'win_rate_pct': round(win_rate_pct, 1),
        'trades_log': trades,
        'equity_curve': df_equity
    }
