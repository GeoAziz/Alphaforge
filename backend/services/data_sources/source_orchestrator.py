"""Data source orchestrator - manages multiple sources with fallback logic."""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

from .base_source import BaseDataSource
from .binance_source import BinanceDataSource
from .coingecko_source import CoinGeckoDataSource
from .polygon_source import PolygonDataSource


class DataSourceOrchestrator:
    """
    Manages multiple data sources with intelligent fallback logic.
    
    Strategy:
    1. Try primary source (Binance for crypto)
    2. If fails or rate limited, try secondary (CoinGecko)
    3. If both fail, return cached/fallback data
    """
    
    def __init__(self, enable_polygon: bool = False):
        self.sources: Dict[str, BaseDataSource] = {}
        self.source_priority = []
        self.asset_type_routing = {}  # Route assets to best source
        
        # Initialize sources
        self._init_sources(enable_polygon)
    
    def _init_sources(self, enable_polygon: bool = False):
        """Initialize all data sources."""
        # Binance (best for crypto)
        self.sources["binance"] = BinanceDataSource()
        
        # CoinGecko (robust fallback for crypto)
        self.sources["coingecko"] = CoinGeckoDataSource()
        
        # Polygon (for stocks/forex)
        if enable_polygon:
            self.sources["polygon"] = PolygonDataSource()
        
        # Set default priority: Binance > CoinGecko > Polygon
        self.source_priority = ["binance", "coingecko"]
        if enable_polygon:
            self.source_priority.append("polygon")
        
        # Route crypto to Binance, fallback to CoinGecko
        crypto_symbols = ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "AVAX", "DOT"]
        for symbol in crypto_symbols:
            self.asset_type_routing[symbol] = ["binance", "coingecko"]
    
    async def fetch_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch ticker with intelligent fallback.
        Tries primary source first, then fallback sources.
        """
        sources_to_try = self.asset_type_routing.get(symbol, self.source_priority)
        
        for source_name in sources_to_try:
            if source_name not in self.sources:
                continue
            
            source = self.sources[source_name]
            
            # Skip if source is unavailable or rate limited
            if not source.is_available or await source.is_rate_limited():
                logger.debug(f"⏭️  Skipping {source_name}: unavailable or rate limited")
                continue
            
            try:
                ticker = await source.fetch_ticker(symbol)
                if ticker:
                    logger.info(f"✅ Fetched {symbol} from {source_name}")
                    return ticker
            except Exception as e:
                logger.warning(f"⚠️ {source_name} fetch failed for {symbol}: {e}")
                source.mark_error(str(e))
        
        logger.warning(f"❌ All sources failed for {symbol}")
        return None
    
    async def fetch_tickers(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch multiple tickers efficiently.
        Uses batch endpoints where available.
        """
        tickers = []
        remaining_symbols = symbols[:]
        
        # Try Binance batch first (most efficient)
        try:
            binance = self.sources.get("binance")
            if binance and binance.is_available:
                binance_tickers = await binance.fetch_tickers(symbols)
                if binance_tickers:
                    tickers.extend(binance_tickers)
                    # Remove successfully fetched symbols
                    fetched = {t["symbol"] for t in binance_tickers}
                    remaining_symbols = [s for s in remaining_symbols if s not in fetched]
        
        except Exception as e:
            logger.warning(f"⚠️ Binance batch fetch failed: {e}")
        
        # Fall back to CoinGecko batch for remaining
        if remaining_symbols:
            try:
                coingecko = self.sources.get("coingecko")
                if coingecko and coingecko.is_available:
                    cg_tickers = await coingecko.fetch_tickers(remaining_symbols)
                    if cg_tickers:
                        tickers.extend(cg_tickers)
                        fetched = {t["symbol"] for t in cg_tickers}
                        remaining_symbols = [s for s in remaining_symbols if s not in fetched]
            
            except Exception as e:
                logger.warning(f"⚠️ CoinGecko batch fetch failed: {e}")
        
        # Try individual fetches for remaining
        for symbol in remaining_symbols:
            ticker = await self.fetch_ticker(symbol)
            if ticker:
                tickers.append(ticker)
        
        logger.info(f"📊 Fetched {len(tickers)}/{len(symbols)} tickers")
        return tickers
    
    async def fetch_ohlcv(self, symbol: str, interval: str = "1h", limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """Fetch OHLCV with fallback logic."""
        sources_to_try = self.asset_type_routing.get(symbol, self.source_priority)
        
        for source_name in sources_to_try:
            if source_name not in self.sources:
                continue
            
            source = self.sources[source_name]
            if not source.is_available:
                continue
            
            try:
                ohlcv = await source.fetch_ohlcv(symbol, interval, limit)
                if ohlcv:
                    logger.info(f"✅ Fetched OHLCV for {symbol} from {source_name}")
                    return ohlcv
            except Exception as e:
                logger.warning(f"⚠️ {source_name} OHLCV fetch failed: {e}")
        
        logger.warning(f"❌ All sources failed OHLCV for {symbol}")
        return None
    
    async def fetch_sentiment(self) -> Optional[Dict[str, Any]]:
        """
        Fetch market sentiment from available sources.
        Aggregates multiple sources if possible.
        """
        sentiment_data = {}
        
        for source_name in self.source_priority:
            if source_name not in self.sources:
                continue
            
            source = self.sources[source_name]
            if not source.is_available:
                continue
            
            try:
                sentiment = await source.fetch_sentiment()
                if sentiment:
                    sentiment_data[source_name] = sentiment
                    logger.info(f"✅ Fetched sentiment from {source_name}")
            except Exception as e:
                logger.warning(f"⚠️ {source_name} sentiment fetch failed: {e}")
        
        if not sentiment_data:
            logger.warning("❌ All sources failed sentiment")
            return None
        
        # Return aggregated sentiment
        return {
            "sources": list(sentiment_data.keys()),
            "data": sentiment_data,
            "timestamp": datetime.utcnow()
        }
    
    async def close(self):
        """Close all source connections."""
        for source in self.sources.values():
            await source.close()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all sources."""
        return {
            source_name: {
                "available": source.is_available,
                "last_error": source.last_error
            }
            for source_name, source in self.sources.items()
        }
