"""
ALPACA LIVE BROKER ADAPTER (US STOCKS & LIVE MARKET STREAMING)
Author: Quant AI Engineering Team
"""

import os
import requests
from typing import Dict, List, Any
from broker_bridge.base_broker import BaseBrokerAdapter

class AlpacaLiveBroker(BaseBrokerAdapter):
    """
    Live Trading Adapter for Alpaca API (US Stocks & ETFs).
    Routes live prices, account balances, active positions, and market orders to Alpaca Live Endpoint.
    """
    
    def __init__(self, api_key: str = None, secret_key: str = None, is_paper: bool = False):
        self.api_key = api_key or os.getenv("ALPACA_API_KEY", "")
        self.secret_key = secret_key or os.getenv("ALPACA_SECRET_KEY", "")
        
        # Base URL: Live vs Paper Endpoint
        if is_paper:
            self.base_url = "https://paper-api.alpaca.markets"
        else:
            self.base_url = "https://api.alpaca.markets"
            
        self.headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key,
            "Content-Type": "application/json"
        }
        
    def get_account_balance(self) -> Dict[str, float]:
        if not self.api_key:
            return {"cash_thb": 100000.0, "invested_thb": 0.0, "equity_thb": 100000.0, "buying_power_thb": 100000.0}
            
        try:
            url = f"{self.base_url}/v2/account"
            res = requests.get(url, headers=self.headers, timeout=8)
            if res.status_code == 200:
                data = res.json()
                cash_usd = float(data.get("cash", 0.0))
                equity_usd = float(data.get("equity", 0.0))
                bp_usd = float(data.get("buying_power", 0.0))
                fx_rate = 35.0  # USD/THB Conversion
                
                return {
                    "cash_thb": round(cash_usd * fx_rate, 2),
                    "invested_thb": round((equity_usd - cash_usd) * fx_rate, 2),
                    "equity_thb": round(equity_usd * fx_rate, 2),
                    "buying_power_thb": round(bp_usd * fx_rate, 2)
                }
        except Exception as e:
            print(f"Alpaca API Account Balance Error: {e}")
            
        return {"cash_thb": 100000.0, "invested_thb": 0.0, "equity_thb": 100000.0, "buying_power_thb": 100000.0}

    def get_positions(self) -> List[Dict[str, Any]]:
        if not self.api_key:
            return []
            
        try:
            url = f"{self.base_url}/v2/positions"
            res = requests.get(url, headers=self.headers, timeout=8)
            if res.status_code == 200:
                positions_raw = res.json()
                fx_rate = 35.0
                positions = []
                
                for p in positions_raw:
                    qty = float(p.get("qty", 0))
                    cost_usd = float(p.get("avg_entry_price", 0))
                    curr_usd = float(p.get("current_price", 0))
                    pnl_usd = float(p.get("unrealized_pl", 0))
                    pnl_pct = float(p.get("unrealized_plpc", 0)) * 100.0
                    
                    positions.append({
                        "symbol": p.get("symbol"),
                        "raw_symbol": p.get("symbol"),
                        "shares": qty,
                        "cost_price": round(cost_usd * fx_rate, 2),
                        "current_price": round(curr_usd * fx_rate, 2),
                        "pnl_thb": round(pnl_usd * fx_rate, 2),
                        "pnl_pct": round(pnl_pct, 2)
                    })
                return positions
        except Exception as e:
            print(f"Alpaca API Get Positions Error: {e}")
            
        return []

    def get_realtime_price(self, symbol: str) -> float:
        try:
            url = f"https://data.alpaca.markets/v2/stocks/{symbol}/trades/latest"
            res = requests.get(url, headers=self.headers, timeout=5)
            if res.status_code == 200:
                data = res.json()
                return float(data.get("trade", {}).get("p", 0.0))
        except Exception as e:
            print(f"Alpaca Realtime Price Error for {symbol}: {e}")
        return 0.0

    def place_order(self, symbol: str, qty: float, side: str, order_type: str = "market") -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "status": "simulated", "message": f"Alpaca Simulated {side} {qty} {symbol}"}
            
        try:
            url = f"{self.base_url}/v2/orders"
            payload = {
                "symbol": symbol,
                "qty": str(qty),
                "side": side.lower(),
                "type": order_type,
                "time_in_force": "gtc"
            }
            res = requests.post(url, json=payload, headers=self.headers, timeout=8)
            if res.status_code in [200, 201]:
                return {"success": True, "status": "submitted", "order_data": res.json()}
            else:
                return {"success": False, "status": "error", "message": res.text}
        except Exception as e:
            return {"success": False, "status": "error", "message": str(e)}

    def cancel_order(self, order_id: str) -> bool:
        try:
            url = f"{self.base_url}/v2/orders/{order_id}"
            res = requests.delete(url, headers=self.headers, timeout=5)
            return res.status_code in [200, 204]
        except Exception:
            return False
