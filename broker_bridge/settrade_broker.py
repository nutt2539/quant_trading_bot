"""
SETTRADE OPEN API BROKER ADAPTER (THAI SET STOCKS REALTIME API)
Author: Quant AI Engineering Team
"""

import os
import requests
from typing import Dict, List, Any
from broker_bridge.base_broker import BaseBrokerAdapter

class SettradeBrokerAdapter(BaseBrokerAdapter):
    """
    Live Trading Adapter for Settrade Open API (Thai SET Stocks).
    Supports Streaming Realtime Prices, Equity Balance, Portfolio Holdings, and Stock Orders.
    """
    
    def __init__(self, app_id: str = None, app_secret: str = None, broker_id: str = "SANDBOX"):
        self.app_id = app_id or os.getenv("SETTRADE_APP_ID", "")
        self.app_secret = app_secret or os.getenv("SETTRADE_APP_SECRET", "")
        self.broker_id = broker_id or os.getenv("SETTRADE_BROKER_ID", "SANDBOX")
        self.base_url = "https://api.settrade.com/api/v2" if broker_id != "SANDBOX" else "https://sandbox-api.settrade.com/api/v2"

    def get_account_balance(self) -> Dict[str, float]:
        if not self.app_id:
            return {"cash_thb": 100000.0, "invested_thb": 0.0, "equity_thb": 100000.0, "buying_power_thb": 100000.0}
            
        try:
            url = f"{self.base_url}/equity/account"
            res = requests.get(url, headers={"X-App-ID": self.app_id, "X-App-Secret": self.app_secret}, timeout=5)
            if res.status_code == 200:
                data = res.json()
                cash = float(data.get("cash_balance", 100000.0))
                portfolio_val = float(data.get("portfolio_value", 0.0))
                return {
                    "cash_thb": round(cash, 2),
                    "invested_thb": round(portfolio_val, 2),
                    "equity_thb": round(cash + portfolio_val, 2),
                    "buying_power_thb": round(cash, 2)
                }
        except Exception as e:
            print(f"Settrade API Account Balance Error: {e}")
            
        return {"cash_thb": 100000.0, "invested_thb": 0.0, "equity_thb": 100000.0, "buying_power_thb": 100000.0}

    def get_positions(self) -> List[Dict[str, Any]]:
        if not self.app_id:
            return []
            
        try:
            url = f"{self.base_url}/equity/portfolio"
            res = requests.get(url, headers={"X-App-ID": self.app_id, "X-App-Secret": self.app_secret}, timeout=5)
            if res.status_code == 200:
                raw_positions = res.json().get("portfolio_list", [])
                positions = []
                for p in raw_positions:
                    sym = p.get("symbol", "")
                    clean_sym = sym if sym.endswith(".BK") else f"{sym}.BK"
                    qty = float(p.get("actual_volume", 0))
                    cost = float(p.get("average_price", 0))
                    curr = float(p.get("market_price", 0))
                    pnl_thb = float(p.get("unrealized_pnl", 0))
                    pnl_pct = float(p.get("unrealized_pnl_pct", 0))
                    
                    positions.append({
                        "symbol": clean_sym,
                        "raw_symbol": clean_sym,
                        "shares": qty,
                        "cost_price": round(cost, 2),
                        "current_price": round(curr, 2),
                        "pnl_thb": round(pnl_thb, 2),
                        "pnl_pct": round(pnl_pct, 2)
                    })
                return positions
        except Exception as e:
            print(f"Settrade API Portfolio Error: {e}")
            
        return []

    def get_realtime_price(self, symbol: str) -> float:
        clean_sym = symbol.replace(".BK", "")
        try:
            url = f"{self.base_url}/market/price/{clean_sym}"
            res = requests.get(url, headers={"X-App-ID": self.app_id, "X-App-Secret": self.app_secret}, timeout=4)
            if res.status_code == 200:
                return float(res.json().get("last_price", 0.0))
        except Exception:
            pass
        return 0.0

    def place_order(self, symbol: str, qty: float, side: str, order_type: str = "market") -> Dict[str, Any]:
        clean_sym = symbol.replace(".BK", "")
        if not self.app_id:
            return {"success": False, "status": "simulated", "message": f"Settrade Simulated {side} {qty} {symbol}"}
            
        try:
            url = f"{self.base_url}/equity/orders"
            payload = {
                "symbol": clean_sym,
                "volume": int(qty),
                "side": side.upper(),
                "price_type": "MP"
            }
            res = requests.post(url, json=payload, headers={"X-App-ID": self.app_id, "X-App-Secret": self.app_secret}, timeout=8)
            if res.status_code in [200, 201]:
                return {"success": True, "status": "submitted", "order_data": res.json()}
            else:
                return {"success": False, "status": "error", "message": res.text}
        except Exception as e:
            return {"success": False, "status": "error", "message": str(e)}

    def cancel_order(self, order_id: str) -> bool:
        try:
            url = f"{self.base_url}/equity/orders/{order_id}"
            res = requests.delete(url, headers={"X-App-ID": self.app_id, "X-App-Secret": self.app_secret}, timeout=5)
            return res.status_code == 200
        except Exception:
            return False
