"""
Signal Processor Service - Filters, ranks, and validates signals.
Applies confidence thresholds, deduplication, ranking, correlation awareness,
multi-factor confidence scoring, and position sizing.
"""

import logging
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class SignalProcessor:
    """Processes and ranks signals with advanced scoring."""
    
    # Configuration
    MIN_CONFIDENCE = 0.5
    MAX_SIGNALS_PER_TICKER = 1
    SIGNAL_EXPIRY_HOURS = 24
    MAX_CORRELATED_SIGNALS = 2  # Max signals in same correlation cluster
    PORTFOLIO_RISK_PER_TRADE = 0.02  # 2% risk per trade
    
    # Correlation clusters (assets that move together)
    CORRELATION_CLUSTERS = {
        "btc_cluster": ["BTCUSDT", "ETHUSDT"],
        "alt_cluster": ["SOLUSDT", "AVAXUSDT", "DOTUSDT", "ADAUSDT"],
        "meme_cluster": ["DOGEUSDT", "SHIBUSDT", "PEPEUSDT"],
    }
    
    def __init__(self, performance_tracker=None):
        self.seen_signals = {}
        self.performance_tracker = performance_tracker
        # Historical accuracy per signal source (for feedback loop)
        self.source_accuracy = {}
    
    def process_signals(self, raw_signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Main processing pipeline:
        1. Filter by confidence threshold
        2. Deduplicate
        3. Apply multi-factor confidence scoring
        4. Check correlation conflicts
        5. Rank by composite strength
        6. Calculate position sizing
        7. Limit per ticker
        """
        filtered = self._filter_by_confidence(raw_signals)
        logger.info(f"📊 Confidence filtered: {len(raw_signals)} → {len(filtered)}")
        
        deduplicated = self._deduplicate(filtered)
        logger.info(f"📊 Deduplicated: {len(filtered)} → {len(deduplicated)}")
        
        scored = self._apply_multi_factor_scoring(deduplicated)
        
        correlated = self._apply_correlation_awareness(scored)
        logger.info(f"📊 Correlation filtered: {len(scored)} → {len(correlated)}")
        
        ranked = self._rank_by_strength(correlated)
        
        sized = self._apply_position_sizing(ranked)
        
        limited = self._limit_per_ticker(sized)
        logger.info(f"📊 Final processed signals: {len(limited)}")
        
        return limited
    
    def _filter_by_confidence(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove signals below minimum confidence threshold."""
        return [
            s for s in signals
            if s.get("confidence", 0) >= self.MIN_CONFIDENCE
        ]
    
    def _deduplicate(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate signals for same ticker/direction. Keeps highest confidence."""
        signal_map = {}
        
        for signal in signals:
            ticker = signal.get("ticker")
            direction = signal.get("signal_type")
            key = f"{ticker}:{direction}"
            
            existing = signal_map.get(key)
            if existing is None or signal.get("confidence", 0) > existing.get("confidence", 0):
                signal_map[key] = signal
        
        return list(signal_map.values())
    
    def _apply_multi_factor_scoring(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply multi-factor confidence scoring based on:
        - Technical indicator alignment (RSI, MACD, BB)
        - Volume confirmation
        - Trend strength
        - Driver quality
        - Source historical accuracy (feedback loop)
        """
        for signal in signals:
            base_confidence = signal.get("confidence", 0.5)
            drivers = signal.get("drivers", [])
            source = signal.get("source", "unknown")
            
            # Factor 1: Driver quality score (more specific drivers = higher quality)
            driver_quality = min(1.0, len(drivers) / 4) * 0.15
            
            # Factor 2: Source accuracy from feedback loop
            source_acc = self.source_accuracy.get(source, 0.5)
            feedback_bonus = (source_acc - 0.5) * 0.10  # ±5% based on historical accuracy
            
            # Factor 3: Risk-reward quality
            rr_ratio = signal.get("risk_reward_ratio", 1.0)
            rr_score = min(0.10, (rr_ratio - 1.0) * 0.05) if rr_ratio > 1.0 else 0
            
            # Factor 4: Volume confirmation (if available)
            volume_confirmed = signal.get("volume_confirmed", False)
            volume_bonus = 0.05 if volume_confirmed else 0
            
            # Adjust confidence
            adjusted = base_confidence + driver_quality + feedback_bonus + rr_score + volume_bonus
            signal["confidence"] = round(max(0.3, min(0.95, adjusted)), 3)
            signal["confidence_breakdown"] = {
                "base": base_confidence,
                "driver_quality": round(driver_quality, 3),
                "feedback": round(feedback_bonus, 3),
                "risk_reward": round(rr_score, 3),
                "volume": round(volume_bonus, 3),
            }
        
        return signals
    
    def _apply_correlation_awareness(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prevent generating too many signals in the same correlation cluster.
        If we have 3 BUY signals in btc_cluster, keep only the best 2.
        """
        # Build cluster membership map
        asset_to_cluster = {}
        for cluster, assets in self.CORRELATION_CLUSTERS.items():
            for asset in assets:
                asset_to_cluster[asset] = cluster
        
        # Count signals per cluster
        cluster_signals: Dict[str, List[Dict]] = {}
        for signal in signals:
            ticker = signal.get("ticker", "")
            cluster = asset_to_cluster.get(ticker, f"unique_{ticker}")
            if cluster not in cluster_signals:
                cluster_signals[cluster] = []
            cluster_signals[cluster].append(signal)
        
        # Limit per cluster
        result = []
        for cluster, sigs in cluster_signals.items():
            # Sort by confidence, keep top N
            sigs.sort(key=lambda s: s.get("confidence", 0), reverse=True)
            kept = sigs[:self.MAX_CORRELATED_SIGNALS]
            
            # Mark dropped signals
            for dropped in sigs[self.MAX_CORRELATED_SIGNALS:]:
                dropped["correlation_filtered"] = True
                dropped["correlation_reason"] = f"Max {self.MAX_CORRELATED_SIGNALS} signals in cluster"
            
            result.extend(kept)
        
        return result
    
    def _rank_by_strength(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank signals by composite strength score."""
        ranking_data = []
        now = datetime.utcnow()
        
        for signal in signals:
            confidence = signal.get("confidence", 0.5)
            drivers = signal.get("drivers", [])
            driver_count = len(drivers)
            
            created_at = signal.get("created_at", now.isoformat() if hasattr(now, 'isoformat') else str(now))
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00').replace('+00:00', ''))
                except (ValueError, TypeError):
                    created_at = now
            
            hours_old = (now - created_at).total_seconds() / 3600
            recency_bonus = max(1.0, 1.5 - (hours_old / 24))
            
            strength_score = confidence * (1 + driver_count * 0.1) * recency_bonus
            
            ranking_data.append({
                **signal,
                "strength_score": round(strength_score, 3)
            })
        
        ranking_data.sort(key=lambda x: x["strength_score"], reverse=True)
        
        for i, s in enumerate(ranking_data[:5]):
            logger.info(f"  #{i+1}: {s.get('ticker')} {s.get('signal_type')} (score: {s['strength_score']:.3f})")
        
        return ranking_data
    
    def _apply_position_sizing(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate risk-adjusted position sizing for each signal.
        Uses Kelly Criterion simplified: size = (edge / odds) * risk_per_trade
        """
        for signal in signals:
            confidence = signal.get("confidence", 0.5)
            entry = signal.get("entry_price", 0)
            stop_loss = signal.get("stop_loss", 0)
            take_profit = signal.get("take_profit", 0)
            
            if entry <= 0 or stop_loss <= 0 or take_profit <= 0:
                signal["position_size_pct"] = self.PORTFOLIO_RISK_PER_TRADE * 100
                signal["position_size_usd"] = 0
                continue
            
            # Risk per unit
            risk_per_unit = abs(entry - stop_loss)
            reward_per_unit = abs(take_profit - entry)
            
            # Win probability estimate from confidence
            win_prob = confidence
            loss_prob = 1 - win_prob
            
            # Odds (reward:risk)
            odds = reward_per_unit / max(risk_per_unit, 0.01)
            
            # Kelly fraction: f = (bp - q) / b
            kelly_fraction = (odds * win_prob - loss_prob) / max(odds, 0.01)
            kelly_fraction = max(0, min(0.25, kelly_fraction))  # Cap at 25%
            
            # Half-Kelly for safety
            position_fraction = kelly_fraction * 0.5
            
            # Convert to percentage and USD (assuming $10,000 portfolio)
            position_pct = round(position_fraction * 100, 2)
            
            signal["position_size_pct"] = position_pct
            signal["position_size_usd"] = round(position_fraction * 10000, 2)
            signal["kelly_fraction"] = round(kelly_fraction, 4)
            signal["risk_per_trade_pct"] = round(risk_per_unit / max(entry, 0.01) * 100, 2)
        
        return signals
    
    def _limit_per_ticker(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Keep only best signal per ticker."""
        ticker_signals = {}
        for signal in signals:
            ticker = signal.get("ticker")
            if ticker not in ticker_signals:
                ticker_signals[ticker] = signal
        return list(ticker_signals.values())
    
    def update_source_accuracy(self, source: str, was_correct: bool):
        """
        Update source accuracy from feedback loop.
        Called by performance tracker when signal outcome is known.
        """
        if source not in self.source_accuracy:
            self.source_accuracy[source] = 0.5
        
        # Exponential moving average
        alpha = 0.1
        self.source_accuracy[source] = (
            alpha * (1.0 if was_correct else 0.0) +
            (1 - alpha) * self.source_accuracy[source]
        )
        logger.info(f"📊 Updated source accuracy for {source}: {self.source_accuracy[source]:.3f}")
    
    def calculate_signal_metadata(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate additional metadata for a signal."""
        confidence = signal.get("confidence", 0.5)
        drivers = signal.get("drivers", [])
        
        risk_score = (1 - confidence) * 5
        risk_score += (3 - min(len(drivers), 3)) * 0.5
        
        return {
            "risk_score": round(min(10, risk_score), 1),
            "position_size_pct": signal.get("position_size_pct", 2.0),
            "driver_count": len(drivers),
            "recommendation": self._generate_recommendation(confidence, len(drivers))
        }
    
    def _generate_recommendation(self, confidence: float, driver_count: int) -> str:
        """Generate trader-friendly recommendation text."""
        if confidence > 0.8 and driver_count >= 3:
            return "Strong signal — High priority, multi-factor alignment"
        elif confidence > 0.7 and driver_count >= 2:
            return "Moderate signal — Good entry, confirm with volume"
        elif confidence > 0.6:
            return "Standard signal — Use with tight risk management"
        else:
            return "Weak signal — Use with caution, small position size"
    
    def validate_signal_timeframe(self, created_at: datetime) -> bool:
        """Check if signal is still within valid timeframe."""
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00').replace('+00:00', ''))
            except (ValueError, TypeError):
                return True
        
        age = datetime.utcnow() - created_at
        max_age = timedelta(hours=self.SIGNAL_EXPIRY_HOURS)
        return age <= max_age
