"""
Adapter classes to integrate Bybit, OKX, Bitget exchange connectors
as BaseDataSource implementations for the DataSourceOrchestrator.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base_source import BaseDataSource
from .bybit_source import BybitExchange
from .okx_source import OKXExchange
from .bitget_source import BitgetExchange

logger = logging.getLogger(__name__)


class BybitDataSource(BaseDataSource):
    """Bybit exchange as a BaseDataSource for market data fallback."""

    def __init__(self, api_key: str = "", api_secret: str = "", testnet: bool = True):
        super().__init__("Bybit")
        self._exchange = BybitExchange(api_key=api_key, api_secret=api_secret, testnet=testnet)
        self._rate_limited = False

    async def fetch_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        try:
            result = await self._exchange.get_ticker(symbol)
            if result.get("success"):
                self.mark_available()
                return {
                    "symbol": symbol,
                    "price": result["price"],
                    "change_24h": 0.0,
                    "change_24h_pct": result.get("change_24h_pct", 0.0),
                    "volume_24h": result.get("volume_24h", 0.0),
                    "market_cap": None,
                    "bid_price": result.get("bid", 0.0),
                    "ask_price": result.get("ask", 0.0),
                    "high_24h": result.get("high_24h", 0.0),
                    "low_24h": result.get("low_24h", 0.0),
                    "timestamp": datetime.utcnow(),
                    "source": "bybit",
                }
            return None
        except Exception as e:
            self.mark_error(str(e))
            return None

    async def fetch_tickers(self, symbols: List[str]) -> List[Dict[str, Any]]:
        tickers = []
        for symbol in symbols:
            ticker = await self.fetch_ticker(symbol)
            if ticker:
                tickers.append(ticker)
        return tickers

    async def fetch_ohlcv(self, symbol: str, interval: str = "1h", limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        try:
            result = await self._exchange.get_klines(symbol, interval, limit)
            if result.get("success"):
                self.mark_available()
                return [
                    {
                        "timestamp": c.get("open_time", 0),
                        "open": c["open"],
                        "high": c["high"],
                        "low": c["low"],
                        "close": c["close"],
                        "volume": c["volume"],
                    }
                    for c in result.get("candles", [])
                ]
            return None
        except Exception as e:
            self.mark_error(str(e))
            return None

    async def fetch_sentiment(self) -> Optional[Dict[str, Any]]:
        return None

    async def is_rate_limited(self) -> bool:
        return self._rate_limited

    async def close(self):
        pass


class OKXDataSource(BaseDataSource):
    """OKX exchange as a BaseDataSource for market data fallback."""

    def __init__(self, api_key: str = "", api_secret: str = "", passphrase: str = "", testnet: bool = True):
        super().__init__("OKX")
        self._exchange = OKXExchange(api_key=api_key, api_secret=api_secret, passphrase=passphrase, testnet=testnet)
        self._rate_limited = False

    async def fetch_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        try:
            result = await self._exchange.get_ticker(symbol)
            if result.get("success"):
                self.mark_available()
                return {
                    "symbol": symbol,
                    "price": result["price"],
                    "change_24h": 0.0,
                    "change_24h_pct": result.get("change_24h_pct", 0.0),
                    "volume_24h": result.get("volume_24h", 0.0),
                    "market_cap": None,
                    "bid_price": result.get("bid", 0.0),
                    "ask_price": result.get("ask", 0.0),
                    "high_24h": result.get("high_24h", 0.0),
                    "low_24h": result.get("low_24h", 0.0),
                    "timestamp": datetime.utcnow(),
                    "source": "okx",
                }
            return None
        except Exception as e:
            self.mark_error(str(e))
            return None

    async def fetch_tickers(self, symbols: List[str]) -> List[Dict[str, Any]]:
        tickers = []
        for symbol in symbols:
            ticker = await self.fetch_ticker(symbol)
            if ticker:
                tickers.append(ticker)
        return tickers

    async def fetch_ohlcv(self, symbol: str, interval: str = "1h", limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        try:
            result = await self._exchange.get_klines(symbol, interval, limit)
            if result.get("success"):
                self.mark_available()
                return [
                    {
                        "timestamp": c.get("open_time", 0),
                        "open": c["open"],
                        "high": c["high"],
                        "low": c["low"],
                        "close": c["close"],
                        "volume": c["volume"],
                    }
                    for c in result.get("candles", [])
                ]
            return None
        except Exception as e:
            self.mark_error(str(e))
            return None

    async def fetch_sentiment(self) -> Optional[Dict[str, Any]]:
        return None

    async def is_rate_limited(self) -> bool:
        return self._rate_limited

    async def close(self):
        pass


class BitgetDataSource(BaseDataSource):
    """Bitget exchange as a BaseDataSource for market data fallback."""

    def __init__(self, api_key: str = "", api_secret: str = "", passphrase: str = "", testnet: bool = True):
        super().__init__("Bitget")
        self._exchange = BitgetExchange(api_key=api_key, api_secret=api_secret, passphrase=passphrase, testnet=testnet)
        self._rate_limited = False

    async def fetch_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        try:
            result = await self._exchange.get_ticker(symbol)
            if result.get("success"):
                self.mark_available()
                return {
                    "symbol": symbol,
                    "price": result["price"],
                    "change_24h": 0.0,
                    "change_24h_pct": result.get("change_24h_pct", 0.0),
                    "volume_24h": result.get("volume_24h", 0.0),
                    "market_cap": None,
                    "bid_price": result.get("bid", 0.0),
                    "ask_price": result.get("ask", 0.0),
                    "high_24h": result.get("high_24h", 0.0),
                    "low_24h": result.get("low_24h", 0.0),
                    "timestamp": datetime.utcnow(),
                    "source": "bitget",
                }
            return None
        except Exception as e:
            self.mark_error(str(e))
            return None

    async def fetch_tickers(self, symbols: List[str]) -> List[Dict[str, Any]]:
        tickers = []
        for symbol in symbols:
            ticker = await self.fetch_ticker(symbol)
            if ticker:
                tickers.append(ticker)
        return tickers

    async def fetch_ohlcv(self, symbol: str, interval: str = "1h", limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        try:
            result = await self._exchange.get_klines(symbol, interval, limit)
            if result.get("success"):
                self.mark_available()
                return [
                    {
                        "timestamp": c.get("open_time", 0),
                        "open": c["open"],
                        "high": c["high"],
                        "low": c["low"],
                        "close": c["close"],
                        "volume": c["volume"],
                    }
                    for c in result.get("candles", [])
                ]
            return None
        except Exception as e:
            self.mark_error(str(e))
            return None

    async def fetch_sentiment(self) -> Optional[Dict[str, Any]]:
        return None

    async def is_rate_limited(self) -> bool:
        return self._rate_limited

    async def close(self):
        pass
