"""
Signal Processor Service - Filters, ranks, and validates signals.
Applies confidence thresholds, deduplication, and ranking logic.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from decimal import Decimal

logger = logging.getLogger(__name__)


class SignalProcessor:
    """Processes and ranks signals."""
    
    # Configuration
    MIN_CONFIDENCE = 0.5
    MAX_SIGNALS_PER_TICKER = 1  # Only keep best signal per ticker
    SIGNAL_EXPIRY_HOURS = 24
    
    def __init__(self):
        self.seen_signals = {}  # Track signal history to avoid duplicates
    
    def process_signals(self, raw_signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Main processing pipeline:
        1. Filter by confidence threshold
        2. Deduplicate
        3. Rank by strength
        4. Limit per ticker
        """
        # Step 1: Filter by confidence
        filtered = self._filter_by_confidence(raw_signals)
        logger.info(f"📊 Confidence filtered: {len(raw_signals)} → {len(filtered)}")
        
        # Step 2: Deduplicate
        deduplicated = self._deduplicate(filtered)
        logger.info(f"📊 Deduplicated: {len(filtered)} → {len(deduplicated)}")
        
        # Step 3: Rank by strength
        ranked = self._rank_by_strength(deduplicated)
        
        # Step 4: Limit per ticker
        limited = self._limit_per_ticker(ranked)
        logger.info(f"📊 Final processed signals: {len(limited)}")
        
        return limited
    
    def _filter_by_confidence(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove signals below minimum confidence threshold."""
        return [
            s for s in signals
            if s.get("confidence", 0) >= self.MIN_CONFIDENCE
        ]
    
    def _deduplicate(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate signals for same ticker/direction.
        Keeps the one with highest confidence.
        """
        signal_map = {}
        
        for signal in signals:
            ticker = signal.get("ticker")
            direction = signal.get("signal_type")
            key = f"{ticker}:{direction}"
            
            # Keep signal with highest confidence
            existing = signal_map.get(key)
            if existing is None or signal.get("confidence", 0) > existing.get("confidence", 0):
                signal_map[key] = signal
                logger.debug(f"✓ Keeping signal: {key} (confidence: {signal.get('confidence')})")
        
        return list(signal_map.values())
    
    def _rank_by_strength(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank signals by composite strength score.
        Formula: confidence * driver_count * recency_bonus
        """
        ranking_data = []
        now = datetime.utcnow()
        
        for signal in signals:
            confidence = signal.get("confidence", 0.5)
            drivers = signal.get("drivers", [])
            driver_count = len(drivers)
            
            # Recency bonus (newer signals score higher)
            created_at = signal.get("created_at", now)
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)
            
            hours_old = (now - created_at).total_seconds() / 3600
            recency_bonus = max(1.0, 1.5 - (hours_old / 24))  # Decay over 24h
            
            strength_score = confidence * (1 + driver_count * 0.1) * recency_bonus
            
            ranking_data.append({
                **signal,
                "strength_score": strength_score
            })
        
        # Sort by strength score descending
        ranking_data.sort(key=lambda x: x["strength_score"], reverse=True)
        
        for i, s in enumerate(ranking_data[:5]):
            logger.info(f"  #{i+1}: {s.get('ticker')} {s.get('signal_type')} (score: {s['strength_score']:.2f})")
        
        return ranking_data
    
    def _limit_per_ticker(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Keep only best signal per ticker."""
        ticker_signals = {}
        
        for signal in signals:
            ticker = signal.get("ticker")
            
            if ticker not in ticker_signals:
                ticker_signals[ticker] = signal
        
        return list(ticker_signals.values())
    
    def calculate_signal_metadata(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate additional metadata for a signal.
        Includes risk score, position sizing, expected moves.
        """
        confidence = signal.get("confidence", 0.5)
        drivers = signal.get("drivers", [])
        
        # Risk score (0-10, lower is better)
        risk_score = (1 - confidence) * 5  # 0-5 range
        risk_score += (3 - min(len(drivers), 3)) * 0.5  # Fewer drivers = more risk
        
        # Expected position size (as % of portfolio)
        base_size = 0.02  # 2% default
        size_multiplier = confidence  # Higher confidence = higher position
        expected_position_size = base_size * size_multiplier
        
        return {
            "risk_score": min(10, risk_score),
            "expected_position_size": expected_position_size,
            "driver_count": len(drivers),
            "recommendation": self._generate_recommendation(confidence, len(drivers))
        }
    
    def _generate_recommendation(self, confidence: float, driver_count: int) -> str:
        """Generate trader-friendly recommendation text."""
        if confidence > 0.8 and driver_count >= 2:
            return "Strong signal - Consider this high priority"
        elif confidence > 0.6:
            return "Moderate signal - Good entry point"
        else:
            return "Weak signal - Use with caution"
    
    def validate_signal_timeframe(self, created_at: datetime) -> bool:
        """Check if signal is still within valid timeframe."""
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        age = datetime.utcnow() - created_at
        max_age = timedelta(hours=self.SIGNAL_EXPIRY_HOURS)
        
        return age <= max_age
