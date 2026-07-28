"""
Market Regime Detection - §6.1 Architecture Doc
Classifies market regimes: Bull trend, Bear trend, Sideways range, High volatility.
Signals adapt depending on detected regime.
"""

import logging
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class MarketRegime(str, Enum):
    BULL_TREND = "bull_trend"
    BEAR_TREND = "bear_trend"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"


class RegimeDetector:
    """
    Detects current market regime from price and volume data.
    
    Uses multiple signals:
    - Trend direction (EMA alignment, linear regression slope)
    - Trend strength (ADX, R-squared)
    - Volatility level (ATR ratio, historical volatility percentile)
    - Volume confirmation
    """

    # Thresholds
    TREND_SLOPE_THRESHOLD = 0.001  # 0.1% per bar for trend classification
    HIGH_VOL_PERCENTILE = 80  # Top 20% volatility = high vol regime
    ADX_TREND_THRESHOLD = 25  # ADX > 25 indicates trending market
    SIDEWAYS_THRESHOLD = 0.003  # Price range < 0.3% = sideways

    def __init__(self):
        self._regime_cache: Dict[str, Dict[str, Any]] = {}

    def detect_regime(
        self,
        ticker: str,
        candles: List[Dict[str, Any]],
        historical_vol: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Detect current market regime for a ticker.
        
        Returns:
            {
                "ticker": str,
                "regime": MarketRegime,
                "confidence": float (0-1),
                "indicators": dict,
                "signal_adjustments": dict,
                "detected_at": str
            }
        """
        if not candles or len(candles) < 50:
            return self._default_regime(ticker)

        closes = np.array([float(c.get("close", 0)) for c in candles])
        highs = np.array([float(c.get("high", 0)) for c in candles])
        lows = np.array([float(c.get("low", 0)) for c in candles])
        volumes = np.array([float(c.get("volume", 0)) for c in candles])

        # Compute regime indicators
        indicators = {}

        # 1. Trend direction via EMA alignment
        ema_short = self._ema(closes, 9)
        ema_mid = self._ema(closes, 21)
        ema_long = self._ema(closes, 50)
        indicators["ema_9"] = ema_short
        indicators["ema_21"] = ema_mid
        indicators["ema_50"] = ema_long
        indicators["ema_bullish"] = ema_short > ema_mid > ema_long
        indicators["ema_bearish"] = ema_short < ema_mid < ema_long

        # 2. Linear regression slope (trend direction and strength)
        slope, r_squared = self._linear_regression_slope(closes[-50:])
        indicators["slope"] = slope
        indicators["r_squared"] = r_squared

        # 3. ADX (trend strength)
        adx = self._compute_adx(highs, lows, closes, 14)
        indicators["adx"] = adx

        # 4. Volatility metrics
        atr = self._compute_atr(highs, lows, closes, 14)
        atr_ratio = atr / closes[-1] * 100 if closes[-1] > 0 else 0
        indicators["atr"] = atr
        indicators["atr_ratio_pct"] = atr_ratio

        # Historical volatility percentile
        returns = np.diff(np.log(closes))
        current_vol = float(np.std(returns[-20:]) * np.sqrt(365))
        hist_vol = historical_vol if historical_vol else float(np.std(returns) * np.sqrt(365))
        vol_percentile = self._volatility_percentile(returns, 20)
        indicators["current_volatility"] = current_vol
        indicators["historical_volatility"] = hist_vol
        indicators["volatility_percentile"] = vol_percentile

        # 5. Price range (sideways detection)
        high_20 = float(np.max(closes[-20:]))
        low_20 = float(np.min(closes[-20:]))
        range_pct = (high_20 - low_20) / low_20 if low_20 > 0 else 0
        indicators["price_range_20"] = range_pct

        # 6. Volume trend
        vol_sma = float(np.mean(volumes[-20:])) if len(volumes) >= 20 else float(np.mean(volumes))
        indicators["volume_trend"] = float(volumes[-1] / vol_sma) if vol_sma > 0 else 1.0

        # Classify regime
        regime, confidence = self._classify_regime(indicators)

        # Generate signal adjustments based on regime
        adjustments = self._get_signal_adjustments(regime, indicators)

        result = {
            "ticker": ticker,
            "regime": regime.value,
            "confidence": round(confidence, 4),
            "indicators": {k: round(v, 6) if isinstance(v, float) else v for k, v in indicators.items()},
            "signal_adjustments": adjustments,
            "detected_at": datetime.utcnow().isoformat(),
        }

        # Cache
        self._regime_cache[ticker] = result

        logger.info(f"📊 Regime detected for {ticker}: {regime.value} (confidence: {confidence:.2%})")
        return result

    def get_cached_regime(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get cached regime detection for a ticker."""
        return self._regime_cache.get(ticker)

    def _classify_regime(
        self, indicators: Dict[str, float]
    ) -> Tuple[MarketRegime, float]:
        """
        Classify market regime from computed indicators.
        Returns (regime, confidence).
        """
        vol_pct = indicators.get("volatility_percentile", 50)
        adx = indicators.get("adx", 50)
        slope = indicators.get("slope", 0)
        r_squared = indicators.get("r_squared", 0)
        ema_bullish = indicators.get("ema_bullish", False)
        ema_bearish = indicators.get("ema_bearish", False)
        range_pct = indicators.get("price_range_20", 0)

        # High volatility check (takes priority)
        if vol_pct >= self.HIGH_VOL_PERCENTILE and adx < self.ADX_TREND_THRESHOLD:
            confidence = min(1.0, 0.5 + (vol_pct - self.HIGH_VOL_PERCENTILE) / 20 * 0.5)
            return MarketRegime.HIGH_VOLATILITY, confidence

        # Strong trend detection
        if adx > self.ADX_TREND_THRESHOLD and r_squared > 0.3:
            if slope > 0 and ema_bullish:
                confidence = min(1.0, 0.5 + adx / 100 * 0.3 + r_squared * 0.2)
                return MarketRegime.BULL_TREND, confidence
            elif slope < 0 and ema_bearish:
                confidence = min(1.0, 0.5 + adx / 100 * 0.3 + r_squared * 0.2)
                return MarketRegime.BEAR_TREND, confidence

        # Weak trend with EMA alignment
        if ema_bullish and slope > self.TREND_SLOPE_THRESHOLD:
            return MarketRegime.BULL_TREND, 0.4 + min(0.3, r_squared)
        if ema_bearish and slope < -self.TREND_SLOPE_THRESHOLD:
            return MarketRegime.BEAR_TREND, 0.4 + min(0.3, r_squared)

        # Default: sideways
        sideways_confidence = max(0.3, 1.0 - adx / 100)
        if range_pct < self.SIDEWAYS_THRESHOLD:
            sideways_confidence = min(1.0, sideways_confidence + 0.2)

        return MarketRegime.SIDEWAYS, sideways_confidence

    def _get_signal_adjustments(
        self, regime: MarketRegime, indicators: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Generate signal adjustments based on detected regime.
        These are used by the signal engine to modify confidence and parameters.
        """
        adjustments = {
            "regime": regime.value,
            "position_size_multiplier": 1.0,
            "confidence_adjustment": 0.0,
            "preferred_strategies": [],
            "avoid_strategies": [],
            "risk_adjustment": "normal",
        }

        if regime == MarketRegime.BULL_TREND:
            adjustments["position_size_multiplier"] = 1.1
            adjustments["confidence_adjustment"] = 0.05
            adjustments["preferred_strategies"] = ["momentum_breakout", "trend_following", "breakout"]
            adjustments["avoid_strategies"] = ["mean_reversion"]
            adjustments["risk_adjustment"] = "normal"

        elif regime == MarketRegime.BEAR_TREND:
            adjustments["position_size_multiplier"] = 0.8
            adjustments["confidence_adjustment"] = -0.05
            adjustments["preferred_strategies"] = ["mean_reversion", "short_selling"]
            adjustments["avoid_strategies"] = ["momentum_breakout", "breakout"]
            adjustments["risk_adjustment"] = "conservative"

        elif regime == MarketRegime.SIDEWAYS:
            adjustments["position_size_multiplier"] = 0.9
            adjustments["confidence_adjustment"] = -0.03
            adjustments["preferred_strategies"] = ["mean_reversion", "range_trading"]
            adjustments["avoid_strategies"] = ["trend_following", "breakout"]
            adjustments["risk_adjustment"] = "normal"

        elif regime == MarketRegime.HIGH_VOLATILITY:
            adjustments["position_size_multiplier"] = 0.6
            adjustments["confidence_adjustment"] = -0.10
            adjustments["preferred_strategies"] = ["volatility_trading"]
            adjustments["avoid_strategies"] = ["momentum_breakout", "trend_following"]
            adjustments["risk_adjustment"] = "conservative"

        return adjustments

    def _default_regime(self, ticker: str) -> Dict[str, Any]:
        """Return default regime when insufficient data."""
        return {
            "ticker": ticker,
            "regime": MarketRegime.SIDEWAYS.value,
            "confidence": 0.3,
            "indicators": {},
            "signal_adjustments": self._get_signal_adjustments(MarketRegime.SIDEWAYS, {}),
            "detected_at": datetime.utcnow().isoformat(),
            "note": "Insufficient data for reliable regime detection",
        }

    # ====================================================================
    # HELPER COMPUTATIONS
    # ====================================================================

    @staticmethod
    def _ema(data: np.ndarray, period: int) -> float:
        if len(data) < period:
            return float(data[-1]) if len(data) > 0 else 0.0
        multiplier = 2 / (period + 1)
        ema = float(np.mean(data[:period]))
        for value in data[period:]:
            ema = (float(value) - ema) * multiplier + ema
        return float(round(ema, 8))

    @staticmethod
    def _linear_regression_slope(data: np.ndarray) -> Tuple[float, float]:
        """Compute slope and R-squared of linear regression."""
        if len(data) < 2:
            return 0.0, 0.0

        x = np.arange(len(data))
        y = data

        x_mean = np.mean(x)
        y_mean = np.mean(y)

        ss_xy = np.sum((x - x_mean) * (y - y_mean))
        ss_xx = np.sum((x - x_mean) ** 2)

        if ss_xx == 0:
            return 0.0, 0.0

        slope = ss_xy / ss_xx

        # R-squared
        y_pred = slope * (x - x_mean) + y_mean
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - y_mean) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        return float(slope), float(max(0, r_squared))

    @staticmethod
    def _compute_adx(
        highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14
    ) -> float:
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
            tr_list.append(max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            ))

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
            return 0.0

        plus_di = (plus_di_sum / atr) * 100
        minus_di = (minus_di_sum / atr) * 100
        di_sum = plus_di + minus_di

        if di_sum == 0:
            return 0.0

        return float(round(abs(plus_di - minus_di) / di_sum * 100, 4))

    @staticmethod
    def _compute_atr(
        highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14
    ) -> float:
        if len(closes) < period + 1:
            return 0.0

        true_ranges = []
        for i in range(1, len(closes)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
            true_ranges.append(tr)

        if len(true_ranges) < period:
            return float(np.mean(true_ranges)) if true_ranges else 0.0

        atr = float(np.mean(true_ranges[:period]))
        for tr in true_ranges[period:]:
            atr = (atr * (period - 1) + tr) / period
        return atr

    @staticmethod
    def _volatility_percentile(returns: np.ndarray, window: int = 20) -> float:
        """Compute where current volatility falls in historical distribution."""
        if len(returns) < window * 2:
            return 50.0

        vols = []
        for i in range(window, len(returns)):
            vols.append(float(np.std(returns[i - window:i]) * np.sqrt(365)))

        if not vols:
            return 50.0

        current_vol = vols[-1]
        below = sum(1 for v in vols if v < current_vol)
        return float(round(below / len(vols) * 100, 2))


_regime_detector: Optional[RegimeDetector] = None


def get_regime_detector() -> RegimeDetector:
    """Get or create the global regime detector."""
    global _regime_detector
    if _regime_detector is None:
        _regime_detector = RegimeDetector()
    return _regime_detector
