"""
BASE BROKER ADAPTER INTERFACE
Author: Quant AI Engineering Team
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any

class BaseBrokerAdapter(ABC):
    """
    Abstract Base Class defining standard interface for Live Broker Adapters.
    Ensures seamless plug-and-play capability across Thai SET, US, Crypto, and Forex brokers.
    """
    
    @abstractmethod
    def get_account_balance(self) -> Dict[str, float]:
        """
        Returns account balance metrics from Live Broker:
        {'cash_thb': float, 'invested_thb': float, 'equity_thb': float, 'buying_power_thb': float}
        """
        pass
        
    @abstractmethod
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Returns list of active position holdings directly from Live Broker:
        [{'symbol': str, 'shares': float, 'cost_price': float, 'current_price': float, 'pnl_thb': float, 'pnl_pct': float}]
        """
        pass
        
    @abstractmethod
    def get_realtime_price(self, symbol: str) -> float:
        """
        Returns current live market price for a given symbol directly from Broker stream.
        """
        pass
        
    @abstractmethod
    def place_order(self, symbol: str, qty: float, side: str, order_type: str = "market") -> Dict[str, Any]:
        """
        Submits live trading order (BUY / SELL) directly to Broker API.
        Returns execution result dict.
        """
        pass
        
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancels pending order by ID.
        """
        pass
