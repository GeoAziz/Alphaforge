"""
Complete ML Signal Generation Engine with feature engineering, ensemble models, and explainability.
Implements §6 & §7 Architecture Doc (ML Models & Ensemble).
"""

import logging
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import lightgbm as lgb
from sklearn.ensemble import RandomForestClassifier

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Technical feature engineering from OHLCV data.
    Implements indicators per §5 Quant Research Architecture.
    """

    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> List[float]:
        """Calculate Relative Strength Index."""
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        rs = avg_gain / avg_loss if avg_loss != 0 else 1
        rsi = 100 - (100 / (1 + rs))
        return [rsi] * len(prices)

    @staticmethod
    def macd(prices: List[float]) -> Tuple[List[float], List[float]]:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        exp1 = np.exp(-2 / (12 + 1) * np.arange(len(prices)))
        ema12 = np.average(prices, weights=exp1)

        exp2 = np.exp(-2 / (26 + 1) * np.arange(len(prices)))
        ema26 = np.average(prices, weights=exp2)

        macd_line = ema12 - ema26
        exp3 = np.exp(-2 / (9 + 1) * np.arange(len(prices)))
        signal_line = np.average([macd_line] * len(prices), weights=exp3)

        return [macd_line] * len(prices), [signal_line] * len(prices)

    @staticmethod
    def ema(prices: List[float], period: int = 20) -> List[float]:
        """Calculate Exponential Moving Average."""
        ema_values = []
        multiplier = 2 / (period + 1)

        for i, price in enumerate(prices):
            if i == 0:
                ema_values.append(price)
            else:
                ema = (price * multiplier) + (ema_values[i - 1] * (1 - multiplier))
                ema_values.append(ema)

        return ema_values

    @staticmethod
    def atr(high: List[float], low: List[float], close: List[float], period: int = 14) -> List[float]:
        """Calculate Average True Range."""
        tr_values = []

        for i in range(len(high)):
            tr = max(
                high[i] - low[i],
                abs(high[i] - close[i - 1]) if i > 0 else 0,
                abs(low[i] - close[i - 1]) if i > 0 else 0
            )
            tr_values.append(tr)

        atr_values = []
        for i in range(len(tr_values)):
            if i < period:
                atr_values.append(np.mean(tr_values[:i + 1]))
            else:
                atr_values.append(np.mean(tr_values[i - period:i]))

        return atr_values

    @staticmethod
    def volatility(returns: List[float], period: int = 20) -> List[float]:
        """Calculate rolling volatility."""
        vol_values = []
        for i in range(len(returns)):
            if i < period:
                vol = np.std(returns[:i + 1])
            else:
                vol = np.std(returns[i - period:i])
            vol_values.append(vol)

        return vol_values

    @staticmethod
    def extract_features(ohlcv_data: Dict[str, List[float]]) -> Dict[str, List[float]]:
        """
        Extract all technical features from OHLCV data.
        Returns dict of feature arrays.
        """

        close = ohlcv_data.get('close', [])
        high = ohlcv_data.get('high', [])
        low = ohlcv_data.get('low', [])
        volume = ohlcv_data.get('volume', [])

        # Calculate returns
        returns = np.diff(close) / close[:-1]
        returns = np.append([0], returns)

        features = {
            'rsi_14': FeatureEngineer.rsi(close, 14),
            'macd': FeatureEngineer.macd(close)[0],
            'macd_signal': FeatureEngineer.macd(close)[1],
            'ema_20': FeatureEngineer.ema(close, 20),
            'ema_50': FeatureEngineer.ema(close, 50),
            'atr_14': FeatureEngineer.atr(high, low, close, 14),
            'volatility_20': FeatureEngineer.volatility(returns.tolist(), 20),
            'volume_sma': np.convolve(volume, np.ones(20) / 20, mode='same').tolist()
        }

        return features


class EnsembleSignalPredictor:
    """
    Ensemble ML model combining Gradient Boosting + Random Forest.
    Per §8.1 Architecture: model agreement → confidence scoring.
    """

    def __init__(self):
        self.gb_model: Optional[lgb.Booster] = None
        self.rf_model: Optional[RandomForestClassifier] = None
        self.feature_names = [
            'rsi_14', 'macd', 'macd_signal', 'ema_20', 'ema_50',
            'atr_14', 'volatility_20', 'volume_sma'
        ]

    def train(self, X_train: np.ndarray, y_train: np.ndarray):
        """Train ensemble models."""

        try:
            # LightGBM (Gradient Boosting)
            train_data = lgb.Dataset(X_train, label=y_train, feature_names=self.feature_names)
            self.gb_model = lgb.train(
                {'objective': 'binary', 'num_leaves': 31},
                train_data,
                num_boost_round=100
            )
            logger.info("✅ Gradient Boosting model trained")

            # Random Forest
            self.rf_model = RandomForestClassifier(n_estimators=100, max_depth=10)
            self.rf_model.fit(X_train, y_train)
            logger.info("✅ Random Forest model trained")

        except Exception as e:
            logger.error(f"Model training failed: {e}")
            raise

    def predict(self, features: Dict[str, List[float]]) -> Dict[str, Any]:
        """
        Generate signal from ensemble predictions.
        Returns: {direction: 'BUY'|'SELL'|'HOLD', confidence: float, drivers: [...]}
        """

        try:
            # Prepare feature vector
            X = np.array([[
                features.get('rsi_14', [0])[-1],
                features.get('macd', [0])[-1],
                features.get('macd_signal', [0])[-1],
                features.get('ema_20', [0])[-1],
                features.get('ema_50', [0])[-1],
                features.get('atr_14', [0])[-1],
                features.get('volatility_20', [0])[-1],
                features.get('volume_sma', [0])[-1]
            ]])

            # Get predictions
            gb_pred = self.gb_model.predict(X)[0] if self.gb_model else 0.5
            rf_pred = self.rf_model.predict_proba(X)[0][1] if self.rf_model else 0.5

            # Ensemble average
            ensemble_pred = (gb_pred + rf_pred) / 2

            # Determine direction
            if ensemble_pred > 0.6:
                direction = 'BUY'
                confidence = min(ensemble_pred, 0.95)
            elif ensemble_pred < 0.4:
                direction = 'SELL'
                confidence = min(1 - ensemble_pred, 0.95)
            else:
                direction = 'HOLD'
                confidence = 0.5

            # Extract drivers (which features triggered the signal)
            drivers = self._extract_drivers(features)

            return {
                'direction': direction,
                'confidence': confidence,
                'ensemble_pred': ensemble_pred,
                'gb_pred': gb_pred,
                'rf_pred': rf_pred,
                'drivers': drivers,
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return {
                'direction': 'HOLD',
                'confidence': 0.5,
                'error': str(e)
            }

    def _extract_drivers(self, features: Dict[str, List[float]]) -> List[str]:
        """Extract readable signal drivers."""

        drivers = []
        rsi = features.get('rsi_14', [50])[-1]
        macd = features.get('macd', [0])[-1]
        macd_signal = features.get('macd_signal', [0])[-1]

        if rsi > 70:
            drivers.append('RSI overbought')
        elif rsi < 30:
            drivers.append('RSI oversold')

        if macd > macd_signal:
            drivers.append('MACD bullish crossover')
        else:
            drivers.append('MACD bearish crossover')

        return drivers


class SignalGenerator:
    """
    Main signal generation service orchestrating ML and risk checks.
    Per §7 Architecture: generates signals with confidence and explainability.
    """

    def __init__(self, db, ensemble_model: EnsembleSignalPredictor):
        self.db = db
        self.ensemble = ensemble_model
        self.feature_engineer = FeatureEngineer()

    async def generate_signal(
        self,
        ticker: str,
        ohlcv_data: Dict[str, List[float]],
        funding_rate: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate AI signal for an asset.
        Per §7 Architecture: Includes confidence, drivers, and entry/exit levels.
        """

        try:
            # 1. Extract features
            features = self.feature_engineer.extract_features(ohlcv_data)

            # 2. ML prediction
            prediction = self.ensemble.predict(features)

            # 3. Calculate entry/exit levels (§5)
            close_price = ohlcv_data.get('close', [0])[-1]
            atr = features.get('atr_14', [close_price * 0.01])[-1]

            entry_price = close_price
            stop_loss = close_price - (atr * 2)
            take_profit = close_price + (atr * 3)

            signal = {
                'signal_id': f"{ticker}_{int(datetime.utcnow().timestamp())}",
                'ticker': ticker,
                'signal_type': prediction.get('direction'),
                'confidence': prediction.get('confidence'),
                'entry_price': entry_price,
                'stop_loss_price': stop_loss,
                'take_profit_price': take_profit,
                'drivers': prediction.get('drivers', []),
                'rationale': f"Ensemble signal: {prediction.get('confidence'):.0%} confidence",
                'created_at': datetime.utcnow().isoformat(),
                'funding_rate': funding_rate,
                'model_versions': {
                    'gb_pred': prediction.get('gb_pred'),
                    'rf_pred': prediction.get('rf_pred'),
                    'ensemble': prediction.get('ensemble_pred')
                }
            }

            logger.info(f"✅ Signal generated: {ticker} {signal['signal_type']} @ {entry_price:.2f}")

            return signal

        except Exception as e:
            logger.error(f"Signal generation failed: {e}")
            return {
                'error': str(e),
                'ticker': ticker,
                'signal_type': 'HOLD'
            }
