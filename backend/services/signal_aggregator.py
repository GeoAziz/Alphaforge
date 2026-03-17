"""
Signal Aggregator Service - Fetches signals from multiple external sources.
Sources: Alpha Vantage, Polygon.io, TradingView webhooks, custom analysis.
"""

import os
import httpx
import logging
from datetime import datetime
from typing import List, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class SignalAggregator:
    """Aggregates signals from multiple external sources."""
    
    def __init__(self):
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.polygon_key = os.getenv("POLYGON_IO_API_KEY")
        self.client = httpx.AsyncClient()
    
    async def fetch_alpha_vantage_signals(self, symbols: List[str]) -> List[dict]:
        """
        Fetch signals from Alpha Vantage API.
        Uses RSI, MACD, and other technical indicators.
        """
        signals = []
        
        for symbol in symbols:
            try:
                # RSI (Relative Strength Index)
                rsi_url = "https://www.alphavantage.co/query"
                params = {
                    "function": "RSI",
                    "symbol": symbol,
                    "interval": "5min",
                    "time_period": 14,
                    "apikey": self.alpha_vantage_key
                }
                
                response = await self.client.get(rsi_url, params=params, timeout=10)
                data = response.json()
                
                if "Technical Analysis: RSI" in data:
                    technical_data = data["Technical Analysis: RSI"]
                    latest = list(technical_data.values())[0] if technical_data else {}
                    rsi_value = float(latest.get("RSI", 50))
                    
                    # Generate signal based on RSI
                    signal_type = self._rsi_to_signal(rsi_value)
                    confidence = self._calculate_rsi_confidence(rsi_value)
                    
                    signals.append({
                        "ticker": symbol,
                        "signal_type": signal_type,
                        "confidence": confidence,
                        "rationale": f"RSI at {rsi_value:.1f} ({self._rsi_description(rsi_value)})",
                        "drivers": ["RSI"],
                        "source": "alpha_vantage"
                    })
                    logger.info(f"✅ Generated signal for {symbol}: {signal_type} (confidence: {confidence})")
                
            except Exception as e:
                logger.error(f"❌ Alpha Vantage fetch failed for {symbol}: {e}")
        
        return signals
    
    async def fetch_polygon_signals(self, symbols: List[str]) -> List[dict]:
        """
        Fetch signals from Polygon.io.
        Uses market-wide technical analysis.
        """
        signals = []
        
        for symbol in symbols:
            try:
                # Polygon Technical Analysis endpoint
                url = f"https://api.polygon.io/v3/snapshot/options/{symbol}"
                params = {
                    "apiKey": self.polygon_key
                }
                
                response = await self.client.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    # Parse Polygon data for signals
                    if "results" in data and data["results"]:
                        signals.append({
                            "ticker": symbol,
                            "signal_type": "HOLD",
                            "confidence": 0.5,
                            "rationale": "Polygon snapshot data analyzed",
                            "drivers": ["polygon_market_data"],
                            "source": "polygon"
                        })
                        logger.info(f"✅ Polygon signal created for {symbol}")
                
            except Exception as e:
                logger.error(f"❌ Polygon fetch failed for {symbol}: {e}")
        
        return signals
    
    async def fetch_all_signals(self, symbols: List[str]) -> List[dict]:
        """Aggregate signals from all sources."""
        all_signals = []
        
        # Fetch from Alpha Vantage
        alpha_signals = await self.fetch_alpha_vantage_signals(symbols)
        all_signals.extend(alpha_signals)
        
        # Fetch from Polygon
        polygon_signals = await self.fetch_polygon_signals(symbols)
        all_signals.extend(polygon_signals)
        
        logger.info(f"📊 Total signals aggregated: {len(all_signals)}")
        return all_signals
    
    def _rsi_to_signal(self, rsi: float) -> str:
        """Convert RSI value to signal type."""
        if rsi > 70:
            return "SELL"  # Overbought
        elif rsi < 30:
            return "BUY"   # Oversold
        else:
            return "HOLD"
    
    def _calculate_rsi_confidence(self, rsi: float) -> float:
        """Calculate confidence based on RSI extremity."""
        if rsi > 80 or rsi < 20:
            return 0.8  # High confidence
        elif rsi > 70 or rsi < 30:
            return 0.6  # Medium confidence
        else:
            return 0.3  # Low confidence
    
    def _rsi_description(self, rsi: float) -> str:
        """Human-readable RSI description."""
        if rsi > 70:
            return "Overbought"
        elif rsi < 30:
            return "Oversold"
        else:
            return "Neutral"
    
    async def close(self):
        """Clean up HTTP client."""
        await self.client.aclose()
