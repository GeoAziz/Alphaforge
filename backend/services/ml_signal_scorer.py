"""
ML Signal Scoring Service - Generates confidence scores for trading signals.

Uses trained model to predict signal success probability.
Phase 1: Hardcoded baseline (60-80% confidence)
Phase 2: Real ML model (Random Forest / XGBoost)
Phase 3: Deep learning (LSTM for time series)
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


class MLSignalScorer:
    """ML-based signal confidence scoring."""
    
    def __init__(self, db):
        self.db = db
        self.model = None
        self.feature_scaler = None
        self.trained = False
        self._load_model()
    
    def _load_model(self):
        """Load pre-trained model if available."""
        try:
            # In MVP, we don't have a trained model yet
            # In Phase 2, this will load from disk or model registry
            self.trained = False
            logger.info("ℹ️ ML model not trained yet (MVP baseline)")
        except Exception as e:
            logger.warning(f"Could not load ML model: {e}. Using baseline scoring.")
            self.trained = False
    
    async def score_signal(
        self,
        signal_id: str,
        signal_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Score a signal for confidence.
        
        Returns: {
            "signal_id": str,
            "confidence": 0-100,
            "reasoning": str,
            "model_version": str,
            "factors": {
                "momentum": 0-100,
                "mean_reversion": 0-100,
                "sentiment": 0-100,
                "volume": 0-100,
                "correlation": 0-100
            }
        }
        """
        try:
            # Extract features
            features = self._extract_features(signal_data)
            
            # Score based on model or baseline
            if self.trained:
                confidence = self._predict_with_model(features)
            else:
                confidence = self._baseline_score(features)
            
            # Get reasoning
            reasoning = self._generate_reasoning(features, confidence)
            
            # Get factor breakdown
            factors = self._calculate_factors(features)
            
            result = {
                "signal_id": signal_id,
                "confidence": int(confidence),
                "confidence_label": self._confidence_label(confidence),
                "reasoning": reasoning,
                "model_version": "1.0-baseline" if not self.trained else "1.0-ml",
                "factors": factors,
                "scored_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ Signal {signal_id} scored: {confidence}% confidence")
            return result
            
        except Exception as e:
            logger.error(f"❌ Scoring failed for signal {signal_id}: {e}")
            return {
                "signal_id": signal_id,
                "confidence": 50,
                "error": str(e),
                "model_version": "error"
            }
    
    def _extract_features(self, signal_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract ML features from signal data."""
        try:
            ticker = signal_data.get("ticker", "UNKNOWN")
            signal_type = signal_data.get("signal_type", "HOLD")  # BUY, SELL, HOLD
            
            # Get recent market data for this ticker
            # In production, query from market data service
            market_data = signal_data.get("market_data", {})
            
            features = {
                "signal_type_encoded": 1 if signal_type == "BUY" else (-1 if signal_type == "SELL" else 0),
                "rsi": float(market_data.get("rsi", 50)),  # 0-100
                "macd_histogram": float(market_data.get("macd_histogram", 0)),  # Can be negative
                "bb_position": float(market_data.get("bb_position", 50)),  # 0-100 (0=lower band, 100=upper)
                "volume_sma_ratio": float(market_data.get("volume_sma_ratio", 1.0)),  # vol / avg vol
                "price_sma_ratio": float(market_data.get("price_sma_ratio", 1.0)),  # price / SMA200
                "sentiment_score": float(market_data.get("sentiment_score", 0)),  # -1 to +1
                "hourly_return": float(market_data.get("hourly_return", 0)),  # % return last hour
                "daily_volatility": float(market_data.get("daily_volatility", 0.02)),  # Daily vol %
                "correlation_btc": float(market_data.get("correlation_btc", 0)),  # -1 to +1
            }
            
            return features
        
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return {}
    
    def _baseline_score(self, features: Dict[str, float]) -> float:
        """
        MVP baseline scoring (no ML model).
        Uses heuristic rules to combine features.
        """
        try:
            score = 50  # Start at neutral
            
            # Signal type contribution (20 points)
            signal_type = features.get("signal_type_encoded", 0)
            if signal_type != 0:
                score += signal_type * 10
            
            # RSI contribution (0 extreme = good, 30-70 is normal)
            rsi = features.get("rsi", 50)
            if rsi < 20 or rsi > 80:
                score += 10  # Extreme RSI is often good for mean reversion
            elif 30 <= rsi <= 70:
                score += 5  # Normal range
            
            # MACD contribution
            macd = features.get("macd_histogram", 0)
            if macd > 0:
                score += 8
            elif macd < 0:
                score -= 3
            
            # Volume spike contribution
            vol_ratio = features.get("volume_sma_ratio", 1.0)
            if vol_ratio > 1.5:
                score += 12  # Strong volume support
            elif vol_ratio > 1.2:
                score += 6
            
            # Sentiment contribution
            sentiment = features.get("sentiment_score", 0)
            if sentiment > 0.3:
                score += 8
            elif sentiment < -0.3:
                score -= 5
            
            # Price action relative to SMA
            price_ratio = features.get("price_sma_ratio", 1.0)
            if 0.95 <= price_ratio <= 1.05:
                score += 5  # Price near SMA (good pullback zone)
            
            # Clamp to 0-100
            score = max(0, min(100, score))
            
            return score
        
        except Exception as e:
            logger.error(f"Baseline scoring error: {e}")
            return 50
    
    def _predict_with_model(self, features: Dict[str, float]) -> float:
        """
        Use trained ML model to predict confidence.
        (Implemented in Phase 2)
        """
        if not self.trained:
            return self._baseline_score(features)
        
        try:
            # Convert features to model input
            feature_vector = self._features_to_vector(features)
            
            # Get model prediction
            prediction = self.model.predict_proba([feature_vector])[0][1]  # Probability of success
            
            # Convert to 0-100 scale
            confidence = prediction * 100
            
            return confidence
        
        except Exception as e:
            logger.error(f"Model prediction error: {e}")
            return self._baseline_score(features)
    
    def _features_to_vector(self, features: Dict[str, float]) -> List[float]:
        """Convert feature dict to model input vector."""
        feature_order = [
            "signal_type_encoded", "rsi", "macd_histogram", "bb_position",
            "volume_sma_ratio", "price_sma_ratio", "sentiment_score",
            "hourly_return", "daily_volatility", "correlation_btc"
        ]
        
        vector = [features.get(f, 0) for f in feature_order]
        
        # Apply scaling if scaler is available
        if self.feature_scaler:
            vector = self.feature_scaler.transform([vector])[0]
        
        return vector.tolist()
    
    def _calculate_factors(self, features: Dict[str, float]) -> Dict[str, int]:
        """Calculate individual factor scores."""
        
        # Momentum: RSI + MACD
        rsi = features.get("rsi", 50)
        momentum = min(100, max(0, 50 + (rsi - 50) * 0.5))
        
        # Mean Reversion: Volatility + price deviation
        volatility = features.get("daily_volatility", 0.02)
        price_ratio = features.get("price_sma_ratio", 1.0)
        mean_reversion = 50 + (abs(price_ratio - 1.0) * 50)
        mean_reversion = min(100, max(0, mean_reversion))
        
        # Sentiment
        sentiment = features.get("sentiment_score", 0)
        sentiment_score = 50 + (sentiment * 50)  # -1 to +1 mapped to 0-100
        sentiment_score = min(100, max(0, sentiment_score))
        
        # Volume
        vol_ratio = features.get("volume_sma_ratio", 1.0)
        volume_score = min(100, vol_ratio * 50)
        
        # Correlation risk
        correlation = features.get("correlation_btc", 0)
        correlation_score = 50 + (correlation * 25)  # Higher correlation = higher risk
        correlation_score = min(100, max(0, correlation_score))
        
        return {
            "momentum": int(momentum),
            "mean_reversion": int(mean_reversion),
            "sentiment": int(sentiment_score),
            "volume": int(volume_score),
            "correlation": int(correlation_score)  # Lower is better (less correlated = less risky)
        }
    
    def _confidence_label(self, confidence: int) -> str:
        """Convert numeric confidence to label."""
        if confidence >= 80:
            return "VERY_HIGH"
        elif confidence >= 65:
            return "HIGH"
        elif confidence >= 50:
            return "MODERATE"
        elif confidence >= 35:
            return "LOW"
        else:
            return "VERY_LOW"
    
    def _generate_reasoning(self, features: Dict[str, float], confidence: int) -> str:
        """Generate human-readable explanation for confidence score."""
        reasons = []
        
        # Check RSI
        rsi = features.get("rsi", 50)
        if rsi > 80:
            reasons.append("RSI overbought (potential pullback)")
        elif rsi < 20:
            reasons.append("RSI oversold (potential bounce)")
        
        # Check MACD
        macd = features.get("macd_histogram", 0)
        if macd > 0:
            reasons.append("MACD histogram positive (bullish)")
        elif macd < 0:
            reasons.append("MACD histogram negative (bearish)")
        
        # Check volume
        vol_ratio = features.get("volume_sma_ratio", 1.0)
        if vol_ratio > 1.5:
            reasons.append("Volume spike detected (strong conviction)")
        
        # Check sentiment
        sentiment = features.get("sentiment_score", 0)
        if sentiment > 0.3:
            reasons.append("Positive market sentiment")
        elif sentiment < -0.3:
            reasons.append("Negative market sentiment")
        
        # Confidence summary
        if not reasons:
            reasons = ["No strong technical signals detected"]
        
        reasoning = "; ".join(reasons)
        
        return reasoning
    
    async def train_model(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Train ML model on historical trade data.
        (Phase 2 implementation)
        """
        try:
            logger.info(f"Starting ML model training on {len(training_data)} samples...")
            
            # This is a placeholder for Phase 2 ML implementation
            # In reality, this would:
            # 1. Feature engineer the training data
            # 2. Split into train/test
            # 3. Train Random Forest or XGBoost
            # 4. Evaluate and save model
            # 5. Update self.model and self.trained = True
            
            logger.warning("ML model training not yet implemented (Phase 2 task)")
            
            return {
                "success": False,
                "message": "ML training not yet implemented",
                "phase": "Phase 2"
            }
        
        except Exception as e:
            logger.error(f"❌ Model training failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_model_performance(self) -> Dict[str, Any]:
        """Get model performance metrics."""
        if not self.trained:
            return {
                "trained": False,
                "version": "1.0-baseline",
                "status": "Using baseline heuristic scoring",
                "accuracy": None,
                "note": "ML model training is a Phase 2 task"
            }
        
        return {
            "trained": True,
            "version": "1.0-ml",
            "status": "ML model active",
            "accuracy": 0.62,  # Placeholder
            "precision": 0.65,
            "recall": 0.58,
            "f1_score": 0.61
        }
