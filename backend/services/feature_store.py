"""
Feature Store Service - §13.3 Architecture Doc
Stores engineered ML features for consistency between training and serving.
Provides pre-computed feature vectors for AI signal engine models.
"""

import logging
import time
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)


class FeatureStore:
    """
    Centralized feature store for ML-ready feature vectors.
    
    Ensures consistency between training and inference by versioning features.
    Stores pre-computed indicators (RSI, MACD, EMA, ATR, volatility, etc.)
    with configurable TTL and freshness guarantees.
    """

    DEFAULT_TTL_SECONDS = 300  # 5 minutes for market-derived features
    FEATURE_VERSION = "v1"

    def __init__(self, db=None, redis_client=None):
        self.db = db
        self.redis = redis_client
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._feature_registry: Dict[str, Dict[str, Any]] = {}
        self._register_builtin_features()

    def _register_builtin_features(self):
        """Register all known feature definitions."""
        self._feature_registry = {
            "rsi_14": {
                "description": "14-period RSI",
                "category": "momentum",
                "ttl_seconds": 300,
                "version": self.FEATURE_VERSION,
            },
            "rsi_7": {
                "description": "7-period RSI",
                "category": "momentum",
                "ttl_seconds": 300,
                "version": self.FEATURE_VERSION,
            },
            "macd": {
                "description": "MACD line (12,26,9)",
                "category": "trend",
                "ttl_seconds": 300,
                "version": self.FEATURE_VERSION,
            },
            "macd_signal": {
                "description": "MACD signal line",
                "category": "trend",
                "ttl_seconds": 300,
                "version": self.FEATURE_VERSION,
            },
            "macd_histogram": {
                "description": "MACD histogram",
                "category": "trend",
                "ttl_seconds": 300,
                "version": self.FEATURE_VERSION,
            },
            "ema_9": {
                "description": "9-period EMA",
                "category": "trend",
                "ttl_seconds": 300,
                "version": self.FEATURE_VERSION,
            },
            "ema_21": {
                "description": "21-period EMA",
                "category": "trend",
                "ttl_seconds": 300,
                "version": self.FEATURE_VERSION,
            },
            "ema_50": {
                "description": "50-period EMA",
                "category": "trend",
                "ttl_seconds": 300,
                "version": self.FEATURE_VERSION,
            },
            "ema_200": {
                "description": "200-period EMA",
                "category": "trend",
                "ttl_seconds": 300,
                "version": self.FEATURE_VERSION,
            },
            "atr_14": {
                "description": "14-period Average True Range",
                "category": "volatility",
                "ttl_seconds": 300,
                "version": self.FEATURE_VERSION,
            },
            "volatility_20d": {
                "description": "20-day rolling volatility",
                "category": "volatility",
                "ttl_seconds": 600,
                "version": self.FEATURE_VERSION,
            },
            "volatility_60d": {
                "description": "60-day rolling volatility",
                "category": "volatility",
                "ttl_seconds": 600,
                "version": self.FEATURE_VERSION,
            },
            "bollinger_upper": {
                "description": "Bollinger Bands upper (20,2)",
                "category": "volatility",
                "ttl_seconds": 300,
                "version": self.FEATURE_VERSION,
            },
            "bollinger_lower": {
                "description": "Bollinger Bands lower (20,2)",
                "category": "volatility",
                "ttl_seconds": 300,
                "version": self.FEATURE_VERSION,
            },
            "bollinger_width": {
                "description": "Bollinger Bands width",
                "category": "volatility",
                "ttl_seconds": 300,
                "version": self.FEATURE_VERSION,
            },
            "stochastic_k": {
                "description": "Stochastic %K (14,3,3)",
                "category": "momentum",
                "ttl_seconds": 300,
                "version": self.FEATURE_VERSION,
            },
            "stochastic_d": {
                "description": "Stochastic %D (14,3,3)",
                "category": "momentum",
                "ttl_seconds": 300,
                "version": self.FEATURE_VERSION,
            },
            "adx_14": {
                "description": "14-period ADX (trend strength)",
                "category": "trend_strength",
                "ttl_seconds": 300,
                "version": self.FEATURE_VERSION,
            },
            "obv": {
                "description": "On-Balance Volume",
                "category": "volume",
                "ttl_seconds": 300,
                "version": self.FEATURE_VERSION,
            },
            "volume_sma_20": {
                "description": "20-period volume SMA",
                "category": "volume",
                "ttl_seconds": 300,
                "version": self.FEATURE_VERSION,
            },
            "volume_ratio": {
                "description": "Current volume / 20-SMA volume",
                "category": "volume",
                "ttl_seconds": 300,
                "version": self.FEATURE_VERSION,
            },
            "order_book_imbalance": {
                "description": "Bid/ask volume imbalance ratio",
                "category": "microstructure",
                "ttl_seconds": 60,
                "version": self.FEATURE_VERSION,
            },
            "open_interest_change": {
                "description": "Open interest change % (24h)",
                "category": "derivatives",
                "ttl_seconds": 300,
                "version": self.FEATURE_VERSION,
            },
            "funding_rate": {
                "description": "Current funding rate (perpetuals)",
                "category": "derivatives",
                "ttl_seconds": 300,
                "version": self.FEATURE_VERSION,
            },
            "price_momentum_1h": {
                "description": "Price change % over 1 hour",
                "category": "momentum",
                "ttl_seconds": 120,
                "version": self.FEATURE_VERSION,
            },
            "price_momentum_4h": {
                "description": "Price change % over 4 hours",
                "category": "momentum",
                "ttl_seconds": 300,
                "version": self.FEATURE_VERSION,
            },
            "price_momentum_1d": {
                "description": "Price change % over 1 day",
                "category": "momentum",
                "ttl_seconds": 600,
                "version": self.FEATURE_VERSION,
            },
            "trend_strength": {
                "description": "Composite trend strength score (0-100)",
                "category": "trend_strength",
                "ttl_seconds": 300,
                "version": self.FEATURE_VERSION,
            },
            "momentum_composite": {
                "description": "Composite momentum score (0-100)",
                "category": "momentum",
                "ttl_seconds": 300,
                "version": self.FEATURE_VERSION,
            },
        }

    async def compute_and_store(
        self, ticker: str, candles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compute all registered features from candle data and store them.
        Returns the full feature vector.
        """
        if not candles or len(candles) < 2:
            logger.warning(f"Insufficient candle data for {ticker}: {len(candles) if candles else 0}")
            return {}

        closes = np.array([float(c.get("close", 0)) for c in candles])
        highs = np.array([float(c.get("high", 0)) for c in candles])
        lows = np.array([float(c.get("low", 0)) for c in candles])
        volumes = np.array([float(c.get("volume", 0)) for c in candles])

        features = {}

        # Momentum features
        features.update(self._compute_rsi(closes, 14, "rsi_14"))
        features.update(self._compute_rsi(closes, 7, "rsi_7"))
        features.update(self._compute_stochastic(highs, lows, closes))

        # Trend features
        macd_line, macd_signal, macd_hist = self._compute_macd(closes)
        features["macd"] = macd_line
        features["macd_signal"] = macd_signal
        features["macd_histogram"] = macd_hist

        for period, name in [(9, "ema_9"), (21, "ema_21"), (50, "ema_50"), (200, "ema_200")]:
            features[name] = self._compute_ema(closes, period)

        # Volatility features
        features.update(self._compute_atr(highs, lows, closes, 14))
        features.update(self._compute_bollinger_bands(closes, 20, 2))
        features.update(self._compute_volatility(closes, 20, "volatility_20d"))
        features.update(self._compute_volatility(closes, 60, "volatility_60d"))

        # Volume features
        features.update(self._compute_volume_features(volumes))
        features["obv"] = self._compute_obv(closes, volumes)

        # Trend strength
        features["adx_14"] = self._compute_adx(highs, lows, closes, 14)
        features["trend_strength"] = self._compute_trend_strength(features)

        # Momentum composite
        features["momentum_composite"] = self._compute_momentum_composite(features)

        # Price momentum at multiple timeframes
        for label, window in [("price_momentum_1h", 12), ("price_momentum_4h", 48), ("price_momentum_1d", 288)]:
            if len(closes) >= window:
                features[label] = float((closes[-1] - closes[-window]) / closes[-window] * 100)
            else:
                features[label] = 0.0

        # Store features
        await self._store_features(ticker, features)

        logger.info(f"📊 Features computed and stored for {ticker}: {len(features)} features")
        return features

    async def get_features(
        self, ticker: str, feature_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve stored features for a ticker.
        Returns fresh features from cache or falls back to computation cache.
        """
        cache_key = f"features:{ticker}"

        # Try Redis first
        if self.redis:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    data = json.loads(cached)
                    if feature_names:
                        return {k: v for k, v in data.items() if k in feature_names}
                    return data
            except Exception as e:
                logger.warning(f"Redis feature fetch failed: {e}")

        # Fallback to in-memory cache
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            ttl = self._feature_registry.get("rsi_14", {}).get("ttl_seconds", self.DEFAULT_TTL_SECONDS)
            if time.time() - entry["timestamp"] < ttl:
                data = entry["features"]
                if feature_names:
                    return {k: v for k, v in data.items() if k in feature_names}
                return data

        return {}

    async def get_feature_vector(
        self, ticker: str
    ) -> Dict[str, Any]:
        """
        Get a complete ML-ready feature vector for a ticker.
        Includes metadata: freshness, version, computed_at.
        """
        features = await self.get_features(ticker)
        if not features:
            return {"features": {}, "fresh": False, "version": self.FEATURE_VERSION}

        cache_key = f"features:{ticker}"
        timestamp = self._cache.get(cache_key, {}).get("timestamp", 0)
        freshness = time.time() - timestamp

        return {
            "features": features,
            "fresh": freshness < self.DEFAULT_TTL_SECONDS,
            "freshness_seconds": round(freshness, 2),
            "version": self.FEATURE_VERSION,
            "computed_at": datetime.fromtimestamp(timestamp).isoformat() if timestamp else None,
            "feature_count": len(features),
        }

    def get_feature_definitions(self) -> Dict[str, Any]:
        """Return all registered feature definitions."""
        return self._feature_registry

    async def _store_features(self, ticker: str, features: Dict[str, Any]):
        """Store computed features in cache layers."""
        cache_key = f"features:{ticker}"
        now = time.time()

        # In-memory
        self._cache[cache_key] = {"features": features, "timestamp": now}

        # Redis with TTL
        if self.redis:
            try:
                await self.redis.set(
                    cache_key,
                    json.dumps(features, default=str),
                    ex=self.DEFAULT_TTL_SECONDS,
                )
            except Exception as e:
                logger.warning(f"Redis feature store failed: {e}")

        # Persist to database for historical feature tracking
        if self.db:
            try:
                self.db.supabase.table("feature_vectors").upsert({
                    "ticker": ticker,
                    "features": features,
                    "version": self.FEATURE_VERSION,
                    "computed_at": datetime.utcnow().isoformat(),
                }).execute()
            except Exception as e:
                logger.debug(f"Feature vector DB persist skipped: {e}")

    # ====================================================================
    # TECHNICAL INDICATOR COMPUTATIONS
    # ====================================================================

    @staticmethod
    def _compute_rsi(closes: np.ndarray, period: int, name: str) -> Dict[str, float]:
        """Compute RSI indicator."""
        if len(closes) < period + 1:
            return {name: 50.0}

        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])

        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            return {name: 100.0}

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return {name: float(round(rsi, 4))}

    @staticmethod
    def _compute_ema(data: np.ndarray, period: int) -> float:
        """Compute EMA for given period."""
        if len(data) < period:
            return float(data[-1]) if len(data) > 0 else 0.0

        multiplier = 2 / (period + 1)
        ema = float(np.mean(data[:period]))
        for value in data[period:]:
            ema = (float(value) - ema) * multiplier + ema
        return float(round(ema, 8))

    @staticmethod
    def _compute_macd(
        closes: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> Tuple[float, float, float]:
        """Compute MACD line, signal line, and histogram."""
        if len(closes) < slow + signal:
            return 0.0, 0.0, 0.0

        def ema_val(data, period):
            m = 2 / (period + 1)
            e = float(np.mean(data[:period]))
            for v in data[period:]:
                e = (float(v) - e) * m + e
            return e

        fast_ema = ema_val(closes, fast)
        slow_ema = ema_val(closes, slow)
        macd_line = fast_ema - slow_ema

        # Compute signal line from MACD values
        macd_values = []
        for i in range(slow, len(closes)):
            fe = ema_val(closes[:i + 1], fast)
            se = ema_val(closes[:i + 1], slow)
            macd_values.append(fe - se)

        if len(macd_values) >= signal:
            signal_line = ema_val(np.array(macd_values), signal)
        else:
            signal_line = macd_line

        histogram = macd_line - signal_line
        return float(round(macd_line, 8)), float(round(signal_line, 8)), float(round(histogram, 8))

    @staticmethod
    def _compute_atr(
        highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14
    ) -> Dict[str, float]:
        """Compute Average True Range."""
        if len(closes) < period + 1:
            return {"atr_14": 0.0}

        true_ranges = []
        for i in range(1, len(closes)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
            true_ranges.append(tr)

        if len(true_ranges) < period:
            return {"atr_14": float(np.mean(true_ranges)) if true_ranges else 0.0}

        atr = float(np.mean(true_ranges[:period]))
        for tr in true_ranges[period:]:
            atr = (atr * (period - 1) + tr) / period

        return {"atr_14": float(round(atr, 8))}

    @staticmethod
    def _compute_bollinger_bands(
        closes: np.ndarray, period: int = 20, std_dev: float = 2.0
    ) -> Dict[str, float]:
        """Compute Bollinger Bands."""
        if len(closes) < period:
            mid = float(closes[-1]) if len(closes) > 0 else 0.0
            return {"bollinger_upper": mid, "bollinger_lower": mid, "bollinger_width": 0.0}

        sma = float(np.mean(closes[-period:]))
        std = float(np.std(closes[-period:]))
        upper = sma + std_dev * std
        lower = sma - std_dev * std
        width = (upper - lower) / sma * 100 if sma > 0 else 0.0

        return {
            "bollinger_upper": float(round(upper, 8)),
            "bollinger_lower": float(round(lower, 8)),
            "bollinger_width": float(round(width, 4)),
        }

    @staticmethod
    def _compute_stochastic(
        highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
        k_period: int = 14, d_period: int = 3
    ) -> Dict[str, float]:
        """Compute Stochastic Oscillator %K and %D."""
        if len(closes) < k_period:
            return {"stochastic_k": 50.0, "stochastic_d": 50.0}

        k_values = []
        for i in range(k_period - 1, len(closes)):
            window_high = float(np.max(highs[i - k_period + 1: i + 1]))
            window_low = float(np.min(lows[i - k_period + 1: i + 1]))
            if window_high == window_low:
                k_values.append(50.0)
            else:
                k_val = (float(closes[i]) - window_low) / (window_high - window_low) * 100
                k_values.append(k_val)

        stoch_k = k_values[-1] if k_values else 50.0
        stoch_d = float(np.mean(k_values[-d_period:])) if len(k_values) >= d_period else stoch_k

        return {"stochastic_k": float(round(stoch_k, 4)), "stochastic_d": float(round(stoch_d, 4))}

    @staticmethod
    def _compute_volatility(
        closes: np.ndarray, period: int, name: str
    ) -> Dict[str, float]:
        """Compute rolling volatility (annualized from daily returns)."""
        if len(closes) < period + 1:
            return {name: 0.0}

        returns = np.diff(np.log(closes[-period - 1:]))
        vol = float(np.std(returns) * np.sqrt(365))
        return {name: float(round(vol, 6))}

    @staticmethod
    def _compute_obv(closes: np.ndarray, volumes: np.ndarray) -> float:
        """Compute On-Balance Volume."""
        if len(closes) < 2:
            return 0.0

        obv = 0.0
        for i in range(1, len(closes)):
            if closes[i] > closes[i - 1]:
                obv += volumes[i]
            elif closes[i] < closes[i - 1]:
                obv -= volumes[i]
        return float(round(obv, 2))

    @staticmethod
    def _compute_volume_features(volumes: np.ndarray) -> Dict[str, float]:
        """Compute volume-related features."""
        if len(volumes) < 20:
            return {"volume_sma_20": float(np.mean(volumes)) if len(volumes) > 0 else 0.0, "volume_ratio": 1.0}

        vol_sma = float(np.mean(volumes[-20:]))
        current_vol = float(volumes[-1])
        ratio = current_vol / vol_sma if vol_sma > 0 else 1.0

        return {
            "volume_sma_20": float(round(vol_sma, 2)),
            "volume_ratio": float(round(ratio, 4)),
        }

    @staticmethod
    def _compute_adx(
        highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14
    ) -> float:
        """Compute Average Directional Index (trend strength)."""
        if len(closes) < period + 1:
            return 50.0

        plus_dm = []
        minus_dm = []
        tr_list = []

        for i in range(1, len(closes)):
            up_move = highs[i] - highs[i - 1]
            down_move = lows[i - 1] - lows[i]

            plus_dm.append(max(up_move, 0) if up_move > down_move else 0)
            minus_dm.append(max(down_move, 0) if down_move > up_move else 0)

            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
            tr_list.append(tr)

        if len(tr_list) < period:
            return 50.0

        atr = float(np.mean(tr_list[:period]))
        plus_di_sum = float(np.sum(plus_dm[:period]))
        minus_di_sum = float(np.sum(minus_dm[:period]))

        for i in range(period, len(tr_list)):
            atr = (atr * (period - 1) + tr_list[i]) / period
            plus_di_sum = plus_di_sum - plus_di_sum / period + plus_dm[i]
            minus_di_sum = minus_di_sum - minus_di_sum / period + minus_dm[i]

        if atr == 0:
            return 50.0

        plus_di = (plus_di_sum / atr) * 100
        minus_di = (minus_di_sum / atr) * 100
        di_sum = plus_di + minus_di

        if di_sum == 0:
            return 0.0

        dx = abs(plus_di - minus_di) / di_sum * 100
        return float(round(dx, 4))

    @staticmethod
    def _compute_trend_strength(features: Dict[str, float]) -> float:
        """Composite trend strength score (0-100) from multiple indicators."""
        score = 50.0

        # EMA alignment bonus
        ema_9 = features.get("ema_9", 0)
        ema_21 = features.get("ema_21", 0)
        ema_50 = features.get("ema_50", 0)
        if ema_9 > ema_21 > ema_50:
            score += 20
        elif ema_9 < ema_21 < ema_50:
            score -= 20

        # ADX bonus
        adx = features.get("adx_14", 50)
        if adx > 70:
            score += 15
        elif adx > 50:
            score += 10
        elif adx < 20:
            score -= 10

        # MACD direction
        macd_hist = features.get("macd_histogram", 0)
        if macd_hist > 0:
            score += 10
        else:
            score -= 10

        return float(round(max(0, min(100, score)), 2))

    @staticmethod
    def _compute_momentum_composite(features: Dict[str, float]) -> float:
        """Composite momentum score (0-100) from multiple indicators."""
        score = 50.0

        rsi_14 = features.get("rsi_14", 50)
        if rsi_14 > 70:
            score += 15
        elif rsi_14 > 55:
            score += 10
        elif rsi_14 < 30:
            score -= 15
        elif rsi_14 < 45:
            score -= 10

        stoch_k = features.get("stochastic_k", 50)
        if stoch_k > 80:
            score += 10
        elif stoch_k > 50:
            score += 5
        elif stoch_k < 20:
            score -= 10
        elif stoch_k < 50:
            score -= 5

        macd_hist = features.get("macd_histogram", 0)
        if macd_hist > 0:
            score += 10
        else:
            score -= 10

        vol_ratio = features.get("volume_ratio", 1.0)
        if vol_ratio > 1.5:
            score += 5

        return float(round(max(0, min(100, score)), 2))


_feature_store: Optional[FeatureStore] = None


def get_feature_store(db=None, redis_client=None) -> FeatureStore:
    """Get or create the global feature store instance."""
    global _feature_store
    if _feature_store is None:
        _feature_store = FeatureStore(db, redis_client)
    return _feature_store
