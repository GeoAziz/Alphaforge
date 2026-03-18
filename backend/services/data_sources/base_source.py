"""Base class for all data sources."""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseDataSource(ABC):
    """Abstract base class for market data sources."""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.is_available = True
        self.last_error = None
    
    @abstractmethod
    async def fetch_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch ticker data for a single symbol.
        
        Returns:
            Dict with keys: symbol, price, change_24h, change_24h_pct, volume_24h, 
                           market_cap, timestamp, bid_price, ask_price
        """
        pass
    
    @abstractmethod
    async def fetch_tickers(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Fetch ticker data for multiple symbols."""
        pass
    
    @abstractmethod
    async def fetch_ohlcv(self, symbol: str, interval: str = "1h", limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch OHLCV (candlestick) data.
        
        Returns:
            List of candles with keys: timestamp, open, high, low, close, volume
        """
        pass
    
    @abstractmethod
    async def fetch_sentiment(self) -> Optional[Dict[str, Any]]:
        """
        Fetch market sentiment.
        
        Returns:
            Dict with keys: fear_greed_index, bullish_signals, bearish_signals, neutral_signals
        """
        pass
    
    @abstractmethod
    async def is_rate_limited(self) -> bool:
        """Check if the source is currently rate limited."""
        pass
    
    async def close(self):
        """Clean up resources."""
        pass
    
    def mark_error(self, error: str):
        """Mark source as having an error."""
        self.is_available = False
        self.last_error = error
        logger.warning(f"⚠️ {self.source_name} marked unavailable: {error}")
    
    def mark_available(self):
        """Mark source as available."""
        self.is_available = True
        self.last_error = None
        logger.info(f"✅ {self.source_name} marked available")
