"""
Signal Aggregator Service - Refactored
Generates trading signals using multiple data sources and technical indicators.
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import asyncio

from services.data_sources import DataSourceOrchestrator
from services.cache import InMemoryCache, RedisCache
from utils.indicators import TechnicalIndicators
from config import Config

logger = logging.getLogger(__name__)


class SignalAggregator:
    """
    Aggregates signals from multiple sources using:
    1. Technical indicators (RSI, MACD, Bollinger Bands)
    2. Market data from multiple providers
    3. Sentiment analysis
    """
    
    def __init__(self, performance_tracker=None):
        # Initialize data sources
        self.data_sources = DataSourceOrchestrator(
            enable_polygon=Config.ENABLE_POLYGON
        )
        
        # Initialize cache
        self._init_cache()
        
        # Optional: Signal performance tracker (injected from main.py)
        self.performance_tracker = performance_tracker
        
        self.default_symbols = ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "AVAX", "DOT"]
    
    def _init_cache(self):
        """Initialize cache backend."""
        cache_backend = Config.CACHE_BACKEND.lower()
        
        if cache_backend == "redis":
            self.cache = RedisCache(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB
            )
        else:
            self.cache = InMemoryCache(max_entries=10000)
    
    async def initialize(self):
        """Initialize async components."""
        if hasattr(self.cache, 'connect'):
            await self.cache.connect()
    
    # ========================================================================
    # SIGNAL GENERATION
    # ========================================================================
    
    async def fetch_all_signals(self, symbols: List[str] = None) -> List[Dict[str, Any]]:
        """
        Generate signals for multiple symbols using technical analysis.
        
        Process:
        1. Fetch OHLCV data for each symbol
        2. Compute technical indicators
        3. Generate signals based on thresholds
        4. Score confidence
        5. Return ranked signals
        """
        if symbols is None:
            symbols = self.default_symbols
        
        all_signals = []
        
        for symbol in symbols:
            try:
                signal = await self._generate_signal_for_symbol(symbol)
                if signal:
                    all_signals.append(signal)
            except Exception as e:
                logger.error(f"❌ Signal generation error for {symbol}: {e}")
        
        logger.info(f"📊 Generated {len(all_signals)} signals from {len(symbols)} symbols")
        return all_signals
    
    async def _generate_signal_for_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Generate a trading signal for a single symbol.
        
        Process:
        1. Fetch ticker data
        2. Fetch OHLCV data (for indicators)
        3. Compute technical indicators
        4. Evaluate signal drivers
        5. Combine into composite signal
        """
        try:
            # Step 1: Fetch ticker
            ticker = await self.data_sources.fetch_ticker(symbol)
            if not ticker:
                logger.warning(f"⚠️ Could not fetch ticker for {symbol}")
                return None
            
            # Step 2: Fetch OHLCV for indicator calculation
            ohlcv = await self.data_sources.fetch_ohlcv(symbol, interval="1h", limit=100)
            if not ohlcv or len(ohlcv) < 26:  # Need at least 26 for MACD
                logger.warning(f"⚠️ Insufficient OHLCV data for {symbol}")
                return None
            
            # Step 3: Compute technical indicators
            analysis = TechnicalIndicators.analyze_candles(ohlcv)
            if not analysis:
                logger.warning(f"⚠️ Indicator analysis failed for {symbol}")
                return None
            
            # Step 4: Evaluate signal drivers
            drivers = []
            signal_type = "HOLD"
            confidence = 0.0
            rationale_parts = []
            
            # RSI signals
            if "rsi" in analysis:
                rsi = analysis["rsi"]
                if rsi > Config.RSI_OVERBOUGHT:
                    signal_type = "SELL"
                    confidence += 0.3
                    drivers.append("RSI_OVERBOUGHT")
                    rationale_parts.append(f"RSI {rsi:.1f} >overbought")
                elif rsi < Config.RSI_OVERSOLD:
                    signal_type = "BUY"
                    confidence += 0.3
                    drivers.append("RSI_OVERSOLD")
                    rationale_parts.append(f"RSI {rsi:.1f} <oversold")
            
            # MACD signals
            if "macd_line" in analysis and "signal_line" in analysis:
                macd = analysis["macd_line"]
                signal_line = analysis["signal_line"]
                if macd > signal_line and signal_type != "SELL":
                    signal_type = "BUY" if signal_type == "HOLD" else signal_type
                    confidence += 0.2
                    drivers.append("MACD_BULLISH")
                    rationale_parts.append(f"MACD above signal")
                elif macd < signal_line and signal_type != "BUY":
                    signal_type = "SELL" if signal_type == "HOLD" else signal_type
                    confidence += 0.2
                    drivers.append("MACD_BEARISH")
                    rationale_parts.append(f"MACD below signal")
            
            # Bollinger Bands signals
            if "bollinger_bands" in analysis:
                bb = analysis["bollinger_bands"]
                percent_b = bb.get("percent_b", 0.5)
                
                if percent_b > 0.9:
                    confidence += 0.15
                    drivers.append("BB_UPPER")
                    rationale_parts.append(f"Near upper band ({percent_b:.2f})")
                elif percent_b < 0.1:
                    confidence += 0.15
                    drivers.append("BB_LOWER")
                    rationale_parts.append(f"Near lower band ({percent_b:.2f})")
            
            # Price momentum
            if len(ohlcv) >= 2:
                current_close = ohlcv[-1]["close"]
                prev_close = ohlcv[-2]["close"]
                
                if current_close > prev_close:
                    confidence = min(1.0, confidence + 0.1)
                    if "BUY" not in drivers:
                        drivers.append("PRICE_UP")
                else:
                    confidence = min(1.0, confidence + 0.1)
                    if "SELL" not in drivers:
                        drivers.append("PRICE_DOWN")
            
            # Apply minimum confidence threshold
            if confidence < Config.MIN_SIGNAL_CONFIDENCE:
                logger.debug(f"⏭️  {symbol} confidence {confidence:.2f} below threshold")
                return None
            
            # Step 5: Combine into composite signal
            signal = {
                "ticker": symbol,
                "signal_type": signal_type,
                "confidence": min(1.0, confidence),
                "rationale": " | ".join(rationale_parts) if rationale_parts else f"{signal_type} signal",
                "drivers": drivers,
                "source": "multi_source_indicators",
                "created_at": datetime.utcnow(),
                "price": ticker.get("price"),
                "change_24h_pct": ticker.get("change_24h_pct")
            }
            
            logger.info(f"✅ Generated {signal_type} signal for {symbol} (confidence: {confidence:.2f})")
            return signal
        
        except Exception as e:
            logger.error(f"❌ Error generating signal for {symbol}: {e}")
            return None
    
    # ========================================================================
    # SIGNAL FILTERING & RANKING
    # ========================================================================
    
    async def get_top_signals(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Generate and return top N ranked signals.
        """
        all_signals = await self.fetch_all_signals()
        
        # Filter by confidence threshold
        filtered = [s for s in all_signals if s.get("confidence", 0) >= Config.MIN_SIGNAL_CONFIDENCE]
        
        # Sort by composite strength score
        # Score = confidence * (1 + driver_count * 0.1) * recency_bonus
        ranked = sorted(
            filtered,
            key=lambda s: s.get("confidence", 0) * (1 + len(s.get("drivers", [])) * 0.1),
            reverse=True
        )
        
        logger.info(f"📊 Top signals: {len(ranked[:limit])} from {len(filtered)} filtered")
        return ranked[:limit]
    
    # ========================================================================
    # SIGNAL TRACKING (Integration with Performance Tracker)
    # ========================================================================
    
    async def record_signal_execution(self, signal: Dict[str, Any], entry_price: float):
        """
        Record when a signal is executed (e.g., traded).
        Calls performance tracker if available.
        """
        if not self.performance_tracker:
            return
        
        try:
            # Ensure signal has an ID
            signal_id = signal.get("id")
            if not signal_id:
                logger.warning("⚠️  Cannot track signal without ID")
                return
            
            await self.performance_tracker.record_signal_execution(
                signal_id=signal_id,
                ticker=signal.get("ticker"),
                signal_type=signal.get("signal_type"),
                entry_price=entry_price,
                entry_time=datetime.utcnow(),
                confidence=signal.get("confidence", 0.5),
                drivers=signal.get("drivers", [])
            )
            
            logger.info(f"📊 Recorded signal execution for {signal_id}")
        except Exception as e:
            logger.error(f"❌ Failed to record signal execution: {e}")
    
    async def record_signal_closure(self, signal_id: str, exit_price: float, pnl: float):
        """
        Record when a signal trade closes.
        Calls performance tracker if available.
        """
        if not self.performance_tracker:
            return
        
        try:
            roi_pct = (pnl / exit_price * 100) if exit_price > 0 else 0
            
            await self.performance_tracker.record_signal_closure(
                signal_id=signal_id,
                exit_price=exit_price,
                exit_time=datetime.utcnow(),
                pnl=pnl,
                roi_pct=roi_pct
            )
            
            logger.info(f"📊 Recorded signal closure for {signal_id}: PnL={pnl}, ROI={roi_pct:.2f}%")
        except Exception as e:
            logger.error(f"❌ Failed to record signal closure: {e}")
    
    async def set_performance_tracker(self, tracker):
        """Set the performance tracker (for late initialization)."""
        self.performance_tracker = tracker
        logger.info("✅ Performance tracker connected to signal aggregator")
    
    # ========================================================================
    # CLEANUP
    # ========================================================================
    
    async def close(self):
        """Close all connections."""
        await self.cache.close()
        await self.data_sources.close()
        logger.info("🔌 Signal aggregator closed")
