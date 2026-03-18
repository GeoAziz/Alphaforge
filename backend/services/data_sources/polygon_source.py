"""Polygon.io data source integration."""

import logging
import httpx
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

from .base_source import BaseDataSource


class PolygonDataSource(BaseDataSource):
    """Fetches market data from Polygon.io API."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("Polygon")
        self.api_key = api_key or os.getenv("POLYGON_IO_API_KEY")
        self.base_url = "https://api.polygon.io"
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def fetch_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch single ticker from Polygon."""
        if not self.api_key:
            logger.warning("⚠️ Polygon API key not configured")
            return None
        
        try:
            # Polygon expects stock/forex symbols
            url = f"{self.base_url}/v3/snapshot/locale/us/markets/stocks/tickers/{symbol}"
            params = {"apikey": self.api_key}
            
            response = await self.client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if "results" in data:
                    result = data["results"]
                    self.mark_available()
                    
                    return {
                        "symbol": symbol,
                        "price": result.get("lastPrice", 0),
                        "change_24h": result.get("lastUpdate", 0),  # Not exact
                        "change_24h_pct": result.get("lastTrade", {}).get("price", 0),
                        "volume_24h": result.get("volume", 0),
                        "market_cap": None,
                        "bid_price": result.get("todaysChange", 0),
                        "ask_price": result.get("todaysChangePercent", 0),
                        "timestamp": datetime.utcnow(),
                        "source": "polygon"
                    }
            
            return None
        
        except Exception as e:
            self.mark_error(str(e))
            logger.error(f"❌ Polygon ticker error for {symbol}: {e}")
            return None
    
    async def fetch_tickers(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Fetch multiple tickers from Polygon."""
        tickers = []
        
        for symbol in symbols:
            ticker = await self.fetch_ticker(symbol)
            if ticker:
                tickers.append(ticker)
        
        return tickers
    
    async def fetch_ohlcv(self, symbol: str, interval: str = "1d", limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch OHLCV data from Polygon.
        Polygon requires date range queries, so this is simplified.
        """
        if not self.api_key:
            return None
        
        try:
            # Use aggregates endpoint
            url = f"{self.base_url}/v2/aggs/ticker/{symbol}/range/1/{interval}"
            params = {
                "limit": min(limit, 120),
                "apikey": self.api_key
            }
            
            response = await self.client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if "results" in data:
                    candles = []
                    
                    for result in data["results"]:
                        candles.append({
                            "timestamp": datetime.fromtimestamp(result.get("t", 0) / 1000),
                            "open": result.get("o", 0),
                            "high": result.get("h", 0),
                            "low": result.get("l", 0),
                            "close": result.get("c", 0),
                            "volume": result.get("v", 0)
                        })
                    
                    self.mark_available()
                    return candles
            
            return None
        
        except Exception as e:
            logger.error(f"❌ Polygon OHLCV error: {e}")
            return None
    
    async def fetch_sentiment(self) -> Optional[Dict[str, Any]]:
        """Polygon doesn't provide direct sentiment data."""
        return None
    
    async def is_rate_limited(self) -> bool:
        """Polygon free tier: 5 API calls/minute."""
        return False
    
    async def close(self):
        """Clean up HTTP client."""
        await self.client.aclose()
