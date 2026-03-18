"""
Market Data Service - Refactored
Fetches and aggregates market data from multiple sources with intelligent caching.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import os

from services.data_sources import DataSourceOrchestrator
from services.cache import InMemoryCache, RedisCache
from config import Config

logger = logging.getLogger(__name__)


class MarketDataService:
    """
    Fetches market data from multiple sources with caching and fallback.
    
    Architecture:
    1. Try to fetch from cache
    2. If miss, fetch from primary data source
    3. On failure, try secondary source
    4. Store result in cache
    5. Serve cached/fallback data if all sources fail
    """
    
    def __init__(self):
        # Initialize data sources
        self.data_sources = DataSourceOrchestrator(
            enable_polygon=Config.ENABLE_POLYGON
        )
        
        # Initialize cache
        self._init_cache()
        
        # Default assets
        self.default_symbols = ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "AVAX", "DOT"]
        self.last_known_prices = {}  # Fallback data
    
    def _init_cache(self):
        """Initialize cache backend based on configuration."""
        cache_backend = Config.CACHE_BACKEND.lower()
        
        if cache_backend == "redis":
            self.cache = RedisCache(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB
            )
            logger.info("🔴 Using Redis cache")
        else:
            self.cache = InMemoryCache(max_entries=10000)
            logger.info("🟢 Using in-memory cache")
    
    async def initialize(self):
        """Initialize async components."""
        if hasattr(self.cache, 'connect'):
            await self.cache.connect()
    
    def _calculate_adaptive_ttl(self, symbol: str, ticker_data: Dict[str, Any]) -> int:
        """
        Calculate adaptive TTL based on asset volatility and volume.
        
        Recommendation: Shorter TTL for high-volume, volatile assets (BTC, ETH)
        Longer TTL for stable, low-volume assets
        
        Args:
            symbol: Asset symbol (BTC, ETH, etc)
            ticker_data: Current ticker data with price, volume, change
            
        Returns:
            TTL in seconds (5-60 range)
        """
        # Top tier assets: more volatile, higher volume, more traders
        tier_1_symbols = ["BTC", "ETH", "BNB"]  # 5s TTL
        # Second tier: moderate activity
        tier_2_symbols = ["SOL", "XRP", "ADA", "AVAX", "DOT", "DOGE"]  # 10s TTL
        # Altcoins and less liquid: lower activity # 20s TTL
        
        # Override based on volume analysis
        volume_usd = ticker_data.get("volume_usd", 0)
        change_24h = abs(ticker_data.get("change_24h", 0))  # Volatility proxy
        
        # Tier 1: Tier 1 assets or very high volume (>$1B) or high volatility (>5%)
        if symbol in tier_1_symbols or volume_usd > 1e9 or change_24h > 5:
            return 5  # 5s TTL for maximum freshness
        
        # Tier 2: Tier 2 assets or good volume (>$100M) or moderate volatility (2-5%)
        elif symbol in tier_2_symbols or volume_usd > 1e8 or change_24h > 2:
            return 10  # 10s TTL
        
        # Tier 3: Lower volume or low volatility
        else:
            return 20  # 20s TTL
    
    # ========================================================================


    # MARKET TICKERS
    # ========================================================================
    
    async def fetch_market_tickers(self, symbols: List[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch market ticker data with caching.
        
        Strategy:
        1. Check cache for all symbols
        2. For missing symbols, fetch from data sources
        3. Store new data in cache
        4. Return all results
        """
        if symbols is None:
            symbols = self.default_symbols
        
        tickers = []
        missing_symbols = []
        
        # Step 1: Try cache
        for symbol in symbols:
            cache_key = self.cache.get_cache_key("ticker", symbol)
            cached_ticker = await self.cache.get(cache_key)
            
            if cached_ticker:
                tickers.append(cached_ticker)
                logger.debug(f"📦 Cache hit for {symbol}")
            else:
                missing_symbols.append(symbol)
        
        # Step 2: Fetch missing symbols from sources
        if missing_symbols:
            logger.info(f"📡 Fetching {len(missing_symbols)} missing tickers from sources")
            
            fetched_tickers = await self.data_sources.fetch_tickers(missing_symbols)
            
            # Step 3: Store in cache with adaptive TTL
            for ticker in fetched_tickers:
                cache_key = self.cache.get_cache_key("ticker", ticker["symbol"])
                # Calculate adaptive TTL based on volume and volatility
                adaptive_ttl = self._calculate_adaptive_ttl(ticker["symbol"], ticker)
                await self.cache.set(cache_key, ticker, adaptive_ttl)
                tickers.append(ticker)
                self.last_known_prices[ticker["symbol"]] = ticker
        
        logger.info(f"✅ Fetched {len(tickers)} tickers (cache: {len(symbols) - len(missing_symbols)}, fresh: {len(fetched_tickers) if missing_symbols else 0})")
        return tickers
    
    async def fetch_single_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch ticker for single symbol."""
        cache_key = self.cache.get_cache_key("ticker", symbol)
        
        # Check cache first
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        # Fetch from sources
        ticker = await self.data_sources.fetch_ticker(symbol)
        
        if ticker:
            # Store in cache
            await self.cache.set(cache_key, ticker, Config.CACHE_TTL_TICKER)
            self.last_known_prices[symbol] = ticker
            return ticker
        
        # Return last known price as fallback
        if symbol in self.last_known_prices:
            logger.warning(f"⚠️ Using stale data for {symbol}")
            return self.last_known_prices[symbol]
        
        return None
    
    # ========================================================================
    # OHLCV (CANDLESTICK) DATA
    # ========================================================================
    
    async def fetch_ohlcv(self, symbol: str, interval: str = "1h", limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch OHLCV candlestick data with caching.
        """
        cache_key = self.cache.get_cache_key("ohlcv", symbol, interval)
        
        # Check cache
        cached = await self.cache.get(cache_key)
        if cached and isinstance(cached, list):
            logger.debug(f"📦 Cache hit for OHLCV {symbol} {interval}")
            return cached
        
        # Fetch from sources
        ohlcv = await self.data_sources.fetch_ohlcv(symbol, interval, limit)
        
        if ohlcv:
            # Convert datetime objects to JSON-serializable format
            ohlcv_serializable = []
            for candle in ohlcv:
                candle_copy = candle.copy()
                if isinstance(candle_copy.get("timestamp"), datetime):
                    candle_copy["timestamp"] = candle_copy["timestamp"].isoformat()
                ohlcv_serializable.append(candle_copy)
            
            # Store in cache
            await self.cache.set(cache_key, ohlcv_serializable, Config.CACHE_TTL_OHLCV)
            return ohlcv
        
        logger.warning(f"⚠️ Failed to fetch OHLCV for {symbol}")
        return None
    
    # ========================================================================
    # MARKET SENTIMENT
    # ========================================================================
    
    async def fetch_market_sentiment(self) -> Dict[str, Any]:
        """
        Fetch aggregate market sentiment from sources.
        """
        cache_key = "sentiment:global"
        
        # Check cache
        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug("📦 Cache hit for sentiment")
            return cached
        
        # Fetch from sources
        sentiment = await self.data_sources.fetch_sentiment()
        
        if sentiment:
            # Store in cache
            await self.cache.set(cache_key, sentiment, Config.CACHE_TTL_SENTIMENT)
            return sentiment
        
        # Return default sentiment on failure
        logger.warning("⚠️ Failed to fetch sentiment, using default")
        return {
            "fear_greed_index": 50,
            "bullish_signals": 0,
            "bearish_signals": 0,
            "neutral_signals": 1,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "fallback"
        }
    
    # ========================================================================
    # HEALTH & STATUS
    # ========================================================================
    
    def get_data_source_health(self) -> Dict[str, Any]:
        """Get health status of all data sources."""
        return self.data_sources.get_health_status()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if hasattr(self.cache, 'get_stats'):
            return self.cache.get_stats()
        return {"status": "unavailable"}
    
    # ========================================================================
    # CLEANUP
    # ========================================================================
    
    async def close(self):
        """Close all connections."""
        await self.cache.close()
        await self.data_sources.close()
        logger.info("🔌 Market data service closed")
