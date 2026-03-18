"""Binance data source integration."""

import logging
import httpx
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

from .base_source import BaseDataSource


class BinanceDataSource(BaseDataSource):
    """Fetches market data from Binance API."""
    
    def __init__(self):
        super().__init__("Binance")
        self.base_url = "https://api.binance.com/api/v3"
        self.client = httpx.AsyncClient(timeout=10.0)
        self.rate_limit_remaining = 1200
        self.rate_limit_reset = 0
    
    async def fetch_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch single ticker from Binance."""
        try:
            # Normalize symbol (add USDT if not present)
            binance_symbol = symbol if "USDT" in symbol else f"{symbol}USDT"
            
            url = f"{self.base_url}/ticker/24hr"
            params = {"symbol": binance_symbol}
            
            response = await self.client.get(url, params=params)
            self._update_rate_limits(response.headers)
            
            if response.status_code == 200:
                data = response.json()
                self.mark_available()
                
                return {
                    "symbol": symbol,
                    "price": float(data.get("lastPrice", 0)),
                    "change_24h": float(data.get("priceChange", 0)),
                    "change_24h_pct": float(data.get("priceChangePercent", 0)),
                    "volume_24h": float(data.get("quoteAssetVolume", 0)),
                    "market_cap": None,  # Not available from Binance ticker
                    "bid_price": float(data.get("bidPrice", 0)),
                    "ask_price": float(data.get("askPrice", 0)),
                    "high_24h": float(data.get("highPrice", 0)),
                    "low_24h": float(data.get("lowPrice", 0)),
                    "timestamp": datetime.utcnow(),
                    "source": "binance"
                }
            else:
                logger.warning(f"⚠️ Binance ticker fetch failed for {binance_symbol}: {response.status_code}")
                return None
        
        except Exception as e:
            self.mark_error(str(e))
            logger.error(f"❌ Binance ticker error for {symbol}: {e}")
            return None
    
    async def fetch_tickers(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Fetch multiple tickers from Binance."""
        tickers = []
        
        for symbol in symbols:
            ticker = await self.fetch_ticker(symbol)
            if ticker:
                tickers.append(ticker)
        
        return tickers
    
    async def fetch_ohlcv(self, symbol: str, interval: str = "1h", limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch OHLCV candlestick data from Binance.
        
        Intervals: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M
        """
        try:
            binance_symbol = symbol if "USDT" in symbol else f"{symbol}USDT"
            
            url = f"{self.base_url}/klines"
            params = {
                "symbol": binance_symbol,
                "interval": interval,
                "limit": min(limit, 1000)  # Binance max 1000
            }
            
            response = await self.client.get(url, params=params)
            self._update_rate_limits(response.headers)
            
            if response.status_code == 200:
                data = response.json()
                candles = []
                
                for kline in data:
                    candles.append({
                        "timestamp": datetime.fromtimestamp(kline[0] / 1000),
                        "open": float(kline[1]),
                        "high": float(kline[2]),
                        "low": float(kline[3]),
                        "close": float(kline[4]),
                        "volume": float(kline[7]),  # Quote asset volume
                        "trades": int(kline[8])
                    })
                
                self.mark_available()
                return candles
            else:
                logger.warning(f"⚠️ Binance OHLCV fetch failed: {response.status_code}")
                return None
        
        except Exception as e:
            self.mark_error(str(e))
            logger.error(f"❌ Binance OHLCV error: {e}")
            return None
    
    async def fetch_sentiment(self) -> Optional[Dict[str, Any]]:
        """
        Fetch market sentiment from Binance (funding rates, open interest).
        Note: Binance doesn't have a direct sentiment endpoint, 
        but we can derive it from funding rates and open interest.
        """
        try:
            # For MVP, return aggregated market sentiment based on top coins
            # This is a simplified version - can be enhanced
            url = f"{self.base_url}/ticker/24hr"
            response = await self.client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                # Calculate aggregate market sentiment
                gainers = sum(1 for coin in data if float(coin.get("priceChangePercent", 0)) > 0)
                losers = len(data) - gainers
                
                sentiment_score = (gainers / len(data)) * 100 if data else 50
                
                self.mark_available()
                return {
                    "fear_greed_index": sentiment_score,
                    "bullish_signals": gainers,
                    "bearish_signals": losers,
                    "neutral_signals": 0,
                    "timestamp": datetime.utcnow(),
                    "source": "binance"
                }
            
            return None
        
        except Exception as e:
            logger.error(f"❌ Binance sentiment error: {e}")
            return None
    
    async def is_rate_limited(self) -> bool:
        """Check if rate limited based on remaining requests."""
        return self.rate_limit_remaining < 10
    
    def _update_rate_limits(self, headers: Dict[str, str]):
        """Update rate limit tracking from response headers."""
        try:
            self.rate_limit_remaining = int(headers.get("X-MBX-USED-WEIGHT-1M", 0))
            if self.rate_limit_remaining > 1200:
                self.rate_limit_remaining = 1200
        except:
            pass
    
    async def close(self):
        """Clean up HTTP client."""
        await self.client.aclose()
