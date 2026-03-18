"""Technical indicators computation utilities."""

import logging
from typing import Dict, List, Any, Optional
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """Compute technical indicators for signal generation."""
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
        """
        Calculate Relative Strength Index (RSI).
        
        RSI = 100 - (100 / (1 + RS))
        where RS = Average Gain / Average Loss
        """
        if len(prices) < period + 1:
            return None
        
        try:
            prices = np.array(prices)
            deltas = np.diff(prices)
            
            gains = deltas.copy()
            gains[gains < 0] = 0
            losses = -deltas.copy()
            losses[losses < 0] = 0
            
            avg_gain = np.mean(gains[-period:])
            avg_loss = np.mean(losses[-period:])
            
            if avg_loss == 0:
                return 100.0 if avg_gain > 0 else 50.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return float(rsi)
        
        except Exception as e:
            logger.error(f"❌ RSI calculation error: {e}")
            return None
    
    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Optional[Dict[str, float]]:
        """
        Calculate MACD (Moving Average Convergence Divergence).
        
        Returns:
            Dict with: macd_line, signal_line, histogram
        """
        if len(prices) < slow + signal:
            return None
        
        try:
            prices = np.array(prices)
            
            # Calculate exponential moving averages
            ema_fast = TechnicalIndicators._ema(prices, fast)
            ema_slow = TechnicalIndicators._ema(prices, slow)
            
            # MACD line
            macd_line = ema_fast - ema_slow
            
            # Signal line
            signal_line = TechnicalIndicators._ema(macd_line, signal)
            
            # Histogram
            histogram = macd_line - signal_line
            
            return {
                "macd_line": float(macd_line[-1]),
                "signal_line": float(signal_line[-1]),
                "histogram": float(histogram[-1])
            }
        
        except Exception as e:
            logger.error(f"❌ MACD calculation error: {e}")
            return None
    
    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Optional[Dict[str, float]]:
        """
        Calculate Bollinger Bands.
        
        Returns:
            Dict with: upper_band, middle_band, lower_band, bandwidth, %B
        """
        if len(prices) < period:
            return None
        
        try:
            prices = np.array(prices[-period:])
            
            middle_band = np.mean(prices)
            std = np.std(prices)
            
            upper_band = middle_band + (std_dev * std)
            lower_band = middle_band - (std_dev * std)
            
            # %B indicator (position between bands)
            current_price = prices[-1]
            percent_b = (current_price - lower_band) / (upper_band - lower_band) if upper_band != lower_band else 0.5
            
            # Bandwidth
            bandwidth = (upper_band - lower_band) / middle_band if middle_band != 0 else 0
            
            return {
                "upper_band": float(upper_band),
                "middle_band": float(middle_band),
                "lower_band": float(lower_band),
                "bandwidth": float(bandwidth),
                "percent_b": float(percent_b)
            }
        
        except Exception as e:
            logger.error(f"❌ Bollinger Bands calculation error: {e}")
            return None
    
    @staticmethod
    def calculate_stochastic(high: List[float], low: List[float], close: List[float], 
                            period: int = 14, smooth_k: int = 3, smooth_d: int = 3) -> Optional[Dict[str, float]]:
        """
        Calculate Stochastic Oscillator.
        
        Returns:
            Dict with: %K, %D
        """
        if len(close) < period:
            return None
        
        try:
            high = np.array(high[-period:])
            low = np.array(low[-period:])
            close = np.array(close[-period:])
            
            # Find highest high and lowest low over period
            highest_high = np.max(high)
            lowest_low = np.min(low)
            
            # Calculate %K
            if highest_high == lowest_low:
                percent_k = 50.0
            else:
                percent_k = 100 * (close[-1] - lowest_low) / (highest_high - lowest_low)
            
            # Smooth %K to get final %K
            # (simplified - full implementation would use smoothing)
            percent_d = percent_k  # Placeholder
            
            return {
                "percent_k": float(percent_k),
                "percent_d": float(percent_d)
            }
        
        except Exception as e:
            logger.error(f"❌ Stochastic calculation error: {e}")
            return None
    
    @staticmethod
    def calculate_atr(high: List[float], low: List[float], close: List[float], period: int = 14) -> Optional[float]:
        """
        Calculate Average True Range (ATR).
        Used for volatility measurement.
        """
        if len(close) < period:
            return None
        
        try:
            high = np.array(high)
            low = np.array(low)
            close = np.array(close)
            
            # Calculate True Range
            tr1 = high - low
            tr2 = np.abs(high - np.roll(close, 1))
            tr3 = np.abs(low - np.roll(close, 1))
            
            tr = np.maximum(tr1, np.maximum(tr2, tr3))
            
            # Calculate ATR
            atr = np.mean(tr[-period:])
            
            return float(atr)
        
        except Exception as e:
            logger.error(f"❌ ATR calculation error: {e}")
            return None
    
    @staticmethod
    def calculate_moving_average(prices: List[float], period: int = 20) -> Optional[float]:
        """Calculate Simple Moving Average (SMA)."""
        if len(prices) < period:
            return None
        
        return float(np.mean(prices[-period:]))
    
    @staticmethod
    def _ema(prices: np.ndarray, period: int) -> np.ndarray:
        """Helper: Calculate Exponential Moving Average."""
        multiplier = 2 / (period + 1)
        ema = np.zeros(len(prices))
        ema[0] = prices[0]
        
        for i in range(1, len(prices)):
            ema[i] = prices[i] * multiplier + ema[i - 1] * (1 - multiplier)
        
        return ema
    
    @staticmethod
    def analyze_candles(ohlcv: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Comprehensive technical analysis of candle data.
        
        Returns all major indicators computed.
        """
        if not ohlcv or len(ohlcv) < 26:  # Need at least 26 for MACD
            return None
        
        try:
            closes = [c["close"] for c in ohlcv]
            highs = [c["high"] for c in ohlcv]
            lows = [c["low"] for c in ohlcv]
            
            analysis = {
                "timestamp": datetime.utcnow(),
                "candle_count": len(ohlcv)
            }
            
            # RSI
            rsi = TechnicalIndicators.calculate_rsi(closes)
            if rsi is not None:
                analysis["rsi"] = rsi
            
            # MACD
            macd = TechnicalIndicators.calculate_macd(closes)
            if macd:
                analysis.update(macd)
            
            # Bollinger Bands
            bb = TechnicalIndicators.calculate_bollinger_bands(closes)
            if bb:
                analysis["bollinger_bands"] = bb
            
            # Stochastic
            stoch = TechnicalIndicators.calculate_stochastic(highs, lows, closes)
            if stoch:
                analysis["stochastic"] = stoch
            
            # ATR
            atr = TechnicalIndicators.calculate_atr(highs, lows, closes)
            if atr:
                analysis["atr"] = atr
            
            # Moving Averages
            sma_20 = TechnicalIndicators.calculate_moving_average(closes, 20)
            sma_50 = TechnicalIndicators.calculate_moving_average(closes, 50)
            if sma_20:
                analysis["sma_20"] = sma_20
            if sma_50:
                analysis["sma_50"] = sma_50
            
            return analysis
        
        except Exception as e:
            logger.error(f"❌ Candle analysis error: {e}")
            return None
