"""
Market Data Service - Refactored
Fetches and aggregates market data from multiple sources with intelligent caching.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import os

from services.data_sources import DataSourceOrchestrator
from services.data_sources.bybit_source import BybitExchange
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
        # Initialize data sources with exchange fallbacks
        self.data_sources = DataSourceOrchestrator(
            enable_polygon=Config.ENABLE_POLYGON,
            enable_exchanges=True,
        )
        
        # Initialize cache
        self._init_cache()
        
        # Default crypto assets
        self.default_symbols = ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "AVAX", "DOT"]

        # Forex pairs supported
        self.forex_pairs = [
            "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "AUD/USD",
            "USD/CAD", "NZD/USD", "EUR/GBP", "EUR/JPY", "GBP/JPY"
        ]

        self.last_known_prices = {}  # Fallback data

        # Perpetuals data (funding rates, open interest) - Binance/CoinGecko/
        # Polygon don't expose this, Bybit's public endpoints do.
        self._perp_source = BybitExchange(testnet=False)
    
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
        volume_usd = ticker_data.get("volume_usd", 0) or 0
        change_24h = abs(ticker_data.get("change_24h") or 0)  # Volatility proxy
        
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
        Fetch aggregate market sentiment from sources, shaped to match the
        MarketSentiment response schema (bullish/neutral/bearish counts +
        pcts, a -100..100 composite score, and a market_status label).
        """
        cache_key = "sentiment:global"

        # Check cache
        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug("📦 Cache hit for sentiment")
            return cached

        # Fetch from sources — DataSourceOrchestrator.fetch_sentiment()
        # returns {"sources": [...], "data": {source_name: {...raw...}}}
        raw = await self.data_sources.fetch_sentiment()

        if raw and raw.get("data"):
            bullish = sum(s.get("bullish_signals", 0) for s in raw["data"].values())
            bearish = sum(s.get("bearish_signals", 0) for s in raw["data"].values())
            neutral = sum(s.get("neutral_signals", 0) for s in raw["data"].values())
            total = bullish + bearish + neutral

            if total == 0:
                bullish, neutral, bearish, total = 0, 1, 0, 1

            bullish_pct = bullish / total * 100
            neutral_pct = neutral / total * 100
            bearish_pct = bearish / total * 100
            composite_score = bullish_pct - bearish_pct  # -100..100

            if composite_score > 10:
                market_status = "BULLISH"
            elif composite_score < -10:
                market_status = "BEARISH"
            else:
                market_status = "NEUTRAL"

            sentiment = {
                "bullish_count": bullish,
                "neutral_count": neutral,
                "bearish_count": bearish,
                "bullish_pct": round(bullish_pct, 2),
                "neutral_pct": round(neutral_pct, 2),
                "bearish_pct": round(bearish_pct, 2),
                "composite_score": round(composite_score, 2),
                "market_status": market_status,
                "timestamp": datetime.utcnow().isoformat(),
            }

            await self.cache.set(cache_key, sentiment, Config.CACHE_TTL_SENTIMENT)
            return sentiment

        # Return default sentiment on failure
        logger.warning("⚠️ Failed to fetch sentiment, using default")
        return {
            "bullish_count": 0,
            "neutral_count": 1,
            "bearish_count": 0,
            "bullish_pct": 0.0,
            "neutral_pct": 100.0,
            "bearish_pct": 0.0,
            "composite_score": 0.0,
            "market_status": "NEUTRAL",
            "timestamp": datetime.utcnow().isoformat(),
        }

    # ========================================================================
    # PERPETUALS DATA (Funding Rates, Open Interest)
    # ========================================================================

    async def fetch_funding_rates(self, symbols: List[str] = None) -> List[Dict[str, Any]]:
        """Fetch current perpetual funding rates for the given assets."""
        symbols = symbols or self.default_symbols
        cache_key = self.cache.get_cache_key("funding_rates", ",".join(symbols))

        cached = await self.cache.get(cache_key)
        if cached and isinstance(cached, list):
            return cached

        rates = []
        for symbol in symbols:
            try:
                result = await self._perp_source.get_funding_rate(f"{symbol}USDT")
                if result.get("success"):
                    rates.append({
                        "asset": symbol,
                        "funding_rate": result["funding_rate"],
                        "predicted_rate": None,
                        "interval": "8h",
                        "next_funding_time": None,
                        "timestamp": datetime.utcnow().isoformat(),
                    })
            except Exception as e:
                logger.warning(f"⚠️ Funding rate fetch failed for {symbol}: {e}")

        if rates:
            await self.cache.set(cache_key, rates, Config.CACHE_TTL_OHLCV)

        return rates

    async def fetch_open_interest(self, symbols: List[str] = None) -> List[Dict[str, Any]]:
        """Fetch current open interest for the given assets."""
        symbols = symbols or self.default_symbols
        cache_key = self.cache.get_cache_key("open_interest", ",".join(symbols))

        cached = await self.cache.get(cache_key)
        if cached and isinstance(cached, list):
            return cached

        values = []
        for symbol in symbols:
            try:
                result = await self._perp_source.get_open_interest(f"{symbol}USDT")
                if result.get("success"):
                    ticker = await self.fetch_single_ticker(symbol)
                    price = float(ticker.get("price", 0)) if ticker else 0.0
                    contracts = result["open_interest"]
                    values.append({
                        "asset": symbol,
                        "open_interest_usd": contracts * price,
                        "open_interest_contracts": contracts,
                        "change_24h": 0.0,
                        "change_24h_pct": 0.0,
                        "timestamp": datetime.utcnow().isoformat(),
                    })
            except Exception as e:
                logger.warning(f"⚠️ Open interest fetch failed for {symbol}: {e}")

        if values:
            await self.cache.set(cache_key, values, Config.CACHE_TTL_OHLCV)

        return values

    async def fetch_data_quality(self) -> List[Dict[str, Any]]:
        """Report per-source data quality/health for the market data feeds."""
        health = self.get_data_source_health()
        quality = []

        for source_name, info in health.items():
            available = info.get("available", False)
            quality.append({
                "asset": source_name,
                "status": "HEALTHY" if available else "CRITICAL",
                "last_update": datetime.utcnow().isoformat(),
                "data_points_24h": 0,
                "uptime_pct": 100.0 if available else 0.0,
                "latency_ms": 0.0,
            })

        return quality

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
    # FOREX DATA
    # ========================================================================

    async def fetch_forex_ticker(self, pair: str) -> Optional[Dict[str, Any]]:
        """
        Fetch forex pair ticker data (e.g., EUR/USD).

        Args:
            pair: Forex pair like "EUR/USD"

        Returns:
            Ticker data with price, bid/ask, spread
        """
        cache_key = self.cache.get_cache_key("forex_ticker", pair)

        # Check cache
        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug(f"📦 Cache hit for forex {pair}")
            return cached

        # Fetch from sources (using general ticker endpoint for now)
        ticker = await self.data_sources.fetch_ticker(pair)

        if ticker:
            ticker["asset_class"] = "forex"
            ticker["pair"] = pair
            # TTL 5s for forex - highly liquid, frequently updated
            await self.cache.set(cache_key, ticker, 5)
            self.last_known_prices[pair] = ticker
            return ticker

        # Return last known price as fallback
        if pair in self.last_known_prices:
            logger.warning(f"⚠️ Using stale data for forex {pair}")
            return self.last_known_prices[pair]

        return None

    async def fetch_forex_tickers(self, pairs: List[str] = None) -> List[Dict[str, Any]]:
        """Fetch multiple forex pair tickers with caching."""
        if pairs is None:
            pairs = self.forex_pairs

        tickers = []
        missing_pairs = []

        # Step 1: Try cache
        for pair in pairs:
            cache_key = self.cache.get_cache_key("forex_ticker", pair)
            cached_ticker = await self.cache.get(cache_key)

            if cached_ticker:
                tickers.append(cached_ticker)
                logger.debug(f"📦 Cache hit for {pair}")
            else:
                missing_pairs.append(pair)

        # Step 2: Fetch missing pairs
        if missing_pairs:
            logger.info(f"📡 Fetching {len(missing_pairs)} missing forex pairs")

            fetched_tickers = await self.data_sources.fetch_tickers(missing_pairs)

            # Step 3: Store in cache
            for ticker in fetched_tickers:
                ticker["asset_class"] = "forex"
                cache_key = self.cache.get_cache_key("forex_ticker", ticker["symbol"])
                await self.cache.set(cache_key, ticker, 5)  # 5s TTL for forex
                tickers.append(ticker)
                self.last_known_prices[ticker["symbol"]] = ticker

        return tickers

    async def fetch_forex_ohlcv(self, pair: str, interval: str = "1h", limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch forex pair OHLCV candlestick data.

        Args:
            pair: Forex pair like "EUR/USD"
            interval: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of candles

        Returns:
            List of OHLCV candles
        """
        cache_key = self.cache.get_cache_key("forex_ohlcv", pair, interval)

        # Check cache
        cached = await self.cache.get(cache_key)
        if cached and isinstance(cached, list):
            logger.debug(f"📦 Cache hit for forex OHLCV {pair} {interval}")
            return cached

        # Fetch from sources
        ohlcv = await self.data_sources.fetch_ohlcv(pair, interval, limit)

        if ohlcv:
            # Serialize datetime objects
            ohlcv_serializable = []
            for candle in ohlcv:
                candle_copy = candle.copy()
                if isinstance(candle_copy.get("timestamp"), datetime):
                    candle_copy["timestamp"] = candle_copy["timestamp"].isoformat()
                ohlcv_serializable.append(candle_copy)

            # Store in cache (TTL based on interval)
            ttl = 5 if interval in ["1m", "5m"] else 10 if interval in ["15m", "1h"] else 60
            await self.cache.set(cache_key, ohlcv_serializable, ttl)
            return ohlcv

        logger.warning(f"⚠️ Failed to fetch forex OHLCV for {pair}")
        return None

    def get_supported_forex_pairs(self) -> List[str]:
        """Return list of supported forex pairs."""
        return self.forex_pairs

    def is_forex_pair(self, symbol: str) -> bool:
        """Check if symbol is a forex pair."""
        return "/" in symbol and symbol in self.forex_pairs

    def get_asset_class(self, symbol: str) -> str:
        """Determine asset class (crypto, forex, stock)."""
        if self.is_forex_pair(symbol):
            return "forex"
        elif symbol in self.default_symbols:
            return "crypto"
        else:
            return "unknown"

    # ========================================================================
    # CLEANUP
    # ========================================================================

    async def close(self):
        """Close all connections."""
        await self.cache.close()
        await self.data_sources.close()
        logger.info("🔌 Market data service closed")
