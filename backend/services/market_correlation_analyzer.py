"""
Market Correlation Analysis Service
Analyzes cross-asset correlations to improve signal quality and prevent conflicting signals.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import numpy as np

from database.db import Database
from services.data_sources import DataSourceOrchestrator
from services.cache import InMemoryCache, RedisCache
from config import Config

logger = logging.getLogger(__name__)


class MarketCorrelationAnalyzer:
    """Analyzes and tracks correlations between cryptocurrency assets."""
    
    def __init__(self, db: Database):
        self.db = db
        self.data_sources = DataSourceOrchestrator()
        self._init_cache()
    
    def _init_cache(self):
        """Initialize cache for correlation data."""
        cache_backend = Config.CACHE_BACKEND.lower()
        
        if cache_backend == "redis":
            self.cache = RedisCache(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB
            )
        else:
            self.cache = InMemoryCache(max_entries=1000)
    
    async def compute_correlations(
        self,
        asset_pairs: List[tuple] = None,
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """
        Compute correlations between asset pairs.
        
        Default pairs: BTC-ETH, ETH-SOL, BTC-SOL, BNB-SOL
        """
        try:
            if asset_pairs is None:
                asset_pairs = [
                    ("BTC", "ETH"),
                    ("ETH", "SOL"),
                    ("BTC", "SOL"),
                    ("BNB", "SOL"),
                    ("BTC", "BNB"),
                    ("ETH", "BNB"),
                ]
            
            logger.info(f"📊 Computing correlations for {len(asset_pairs)} pairs over {lookback_days} days")
            
            correlations = {}
            
            for asset1, asset2 in asset_pairs:
                corr_data = await self._compute_pair_correlation(
                    asset1,
                    asset2,
                    lookback_days
                )
                
                if corr_data.get("success"):
                    pair_key = f"{asset1}/{asset2}"
                    correlations[pair_key] = corr_data["data"]
            
            logger.info(f"✅ Computed {len(correlations)} correlations")
            return {
                "success": True,
                "correlations": correlations,
                "computed_at": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to compute correlations: {e}")
            return {"success": False, "error": str(e)}
    
    async def _compute_pair_correlation(
        self,
        asset1: str,
        asset2: str,
        lookback_days: int
    ) -> Dict[str, Any]:
        """Compute correlation between two assets."""
        try:
            # Fetch historical OHLCV data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=lookback_days)
            
            # Get candles from cache or API
            candles1 = await self._get_historical_candles(asset1, "1d", lookback_days)
            candles2 = await self._get_historical_candles(asset2, "1d", lookback_days)
            
            if not candles1 or not candles2:
                logger.warning(f"⚠️ Insufficient data for {asset1}/{asset2}")
                return {"success": False, "error": "Insufficient data"}
            
            # Convert to returns (price changes)
            returns1 = self._calculate_returns(candles1)
            returns2 = self._calculate_returns(candles2)
            
            if len(returns1) < 2 or len(returns2) < 2:
                return {"success": False, "error": "Not enough data points"}
            
            # Compute correlation (1D, 7D, 30D)
            corr_1d = self._calculate_correlation(returns1[-1:], returns2[-1:])
            corr_7d = self._calculate_correlation(returns1[-7:], returns2[-7:])
            corr_30d = self._calculate_correlation(returns1, returns2)
            
            # Compute volatility
            vol_1d = np.std(returns1[-1:]) if len(returns1[-1:]) > 0 else 0
            vol_7d = np.std(returns1[-7:]) if len(returns1[-7:]) > 0 else 0
            vol_30d = np.std(returns1)
            
            # Detect divergence (when normally correlated assets diverge)
            divergence_detected, divergence_strength = self._detect_divergence(
                corr_30d,
                corr_7d,
                candles1[-1]["close"],
                candles2[-1]["close"]
            )
            
            correlation_data = {
                "asset1": asset1,
                "asset2": asset2,
                "correlation_1d": float(corr_1d),
                "correlation_7d": float(corr_7d),
                "correlation_30d": float(corr_30d),
                "volatility_1d": float(vol_1d),
                "volatility_7d": float(vol_7d),
                "volatility_30d": float(vol_30d),
                "trend_strength_1d": float(abs(corr_1d)) if corr_1d else 0,
                "trend_strength_7d": float(abs(corr_7d)) if corr_7d else 0,
                "trend_strength_30d": float(abs(corr_30d)) if corr_30d else 0,
                "divergence_detected": divergence_detected,
                "divergence_strength": float(divergence_strength),
                "computed_at": datetime.utcnow().isoformat()
            }
            
            # Store in database
            await self._store_correlation(correlation_data)
            
            logger.info(f"✅ {asset1}/{asset2}: 30d Corr={corr_30d:.2f}, Divergence={divergence_detected}")
            
            return {
                "success": True,
                "data": correlation_data
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to compute pair correlation: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_historical_candles(
        self,
        asset: str,
        interval: str = "1d",
        limit: int = 30
    ) -> Optional[List[Dict[str, Any]]]:
        """Fetch historical candles from cache or API."""
        try:
            cache_key = f"correlation:candles:{asset}:{interval}"
            
            # Try cache first
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"📦 Using cached candles for {asset}")
                return cached
            
            # Fetch from data source
            candles = await self.data_sources.fetch_ohlcv(asset, interval, limit)
            
            if candles:
                # Cache for 1 day
                await self.cache.set(cache_key, candles, 86400)
                return candles
            
            return None
        
        except Exception as e:
            logger.error(f"❌ Failed to get historical candles for {asset}: {e}")
            return None
    
    @staticmethod
    def _calculate_returns(candles: List[Dict[str, Any]]) -> np.ndarray:
        """Calculate daily returns from candles."""
        closes = [float(c["close"]) for c in candles]
        returns = []
        
        for i in range(1, len(closes)):
            ret = (closes[i] - closes[i-1]) / closes[i-1]
            returns.append(ret)
        
        return np.array(returns)
    
    @staticmethod
    def _calculate_correlation(returns1: np.ndarray, returns2: np.ndarray) -> float:
        """Calculate Pearson correlation between two return series."""
        if len(returns1) < 2 or len(returns2) < 2:
            return 0.0
        
        try:
            correlation = np.corrcoef(returns1, returns2)[0, 1]
            # Handle NaN from corrcoef
            return float(correlation) if not np.isnan(correlation) else 0.0
        except:
            return 0.0
    
    @staticmethod
    def _detect_divergence(
        corr_30d: float,
        corr_7d: float,
        price1: float,
        price2: float
    ) -> tuple:
        """
        Detect when historically correlated assets diverge.
        
        Returns:
            (divergence_detected, divergence_strength)
        """
        # If 30d correlation is high (>0.6) but 7d correlation drops significantly
        threshold = 0.6
        divergence_threshold = 0.3
        
        if corr_30d > threshold:
            divergence = corr_30d - corr_7d
            
            if divergence > divergence_threshold:
                divergence_strength = min(divergence / 0.5, 1.0)  # Normalize to 0-1
                return (True, divergence_strength)
        
        return (False, 0.0)
    
    async def _store_correlation(self, correlation_data: Dict[str, Any]) -> bool:
        """Store correlation data in database."""
        try:
            asset1 = correlation_data["asset1"]
            asset2 = correlation_data["asset2"]
            
            # Check if record exists
            response = self.db.supabase.table("market_correlations")\
                .select("*")\
                .eq("asset1", asset1)\
                .eq("asset2", asset2)\
                .execute()
            
            if response.data and len(response.data) > 0:
                # Update existing record
                update_response = self.db.supabase.table("market_correlations")\
                    .update({
                        "correlation_1d": correlation_data["correlation_1d"],
                        "correlation_7d": correlation_data["correlation_7d"],
                        "correlation_30d": correlation_data["correlation_30d"],
                        "volatility_1d": correlation_data["volatility_1d"],
                        "volatility_7d": correlation_data["volatility_7d"],
                        "volatility_30d": correlation_data["volatility_30d"],
                        "trend_strength_1d": correlation_data["trend_strength_1d"],
                        "trend_strength_7d": correlation_data["trend_strength_7d"],
                        "trend_strength_30d": correlation_data["trend_strength_30d"],
                        "divergence_detected": correlation_data["divergence_detected"],
                        "divergence_strength": correlation_data["divergence_strength"],
                        "last_computed_at": datetime.utcnow().isoformat()
                    })\
                    .eq("asset1", asset1)\
                    .eq("asset2", asset2)\
                    .execute()
            else:
                # Create new record
                insert_response = self.db.supabase.table("market_correlations")\
                    .insert({
                        "asset1": asset1,
                        "asset2": asset2,
                        "correlation_1d": correlation_data["correlation_1d"],
                        "correlation_7d": correlation_data["correlation_7d"],
                        "correlation_30d": correlation_data["correlation_30d"],
                        "volatility_1d": correlation_data["volatility_1d"],
                        "volatility_7d": correlation_data["volatility_7d"],
                        "volatility_30d": correlation_data["volatility_30d"],
                        "trend_strength_1d": correlation_data["trend_strength_1d"],
                        "trend_strength_7d": correlation_data["trend_strength_7d"],
                        "trend_strength_30d": correlation_data["trend_strength_30d"],
                        "divergence_detected": correlation_data["divergence_detected"],
                        "divergence_strength": correlation_data["divergence_strength"],
                        "last_computed_at": datetime.utcnow().isoformat()
                    })\
                    .execute()
            
            return True
        
        except Exception as e:
            logger.error(f"❌ Failed to store correlation: {e}")
            return False
    
    async def check_signal_conflicts(
        self,
        primary_asset: str,
        primary_side: str,
        related_assets: List[str] = None
    ) -> Dict[str, Any]:
        """
        Check if a signal conflicts with signals on correlated assets.
        
        Example: Don't BUY BTC if most correlated assets (ETH, SOL) are in SELL signals
        """
        try:
            if related_assets is None:
                related_assets = ["ETH", "SOL", "BNB"]
            
            conflicts = []
            
            for related_asset in related_assets:
                # Get correlation between primary and related
                response = self.db.supabase.table("market_correlations")\
                    .select("*")\
                    .or_(f"and(asset1.eq.{primary_asset},asset2.eq.{related_asset}),and(asset1.eq.{related_asset},asset2.eq.{primary_asset})")\
                    .order("last_computed_at", desc=True)\
                    .limit(1)\
                    .execute()
                
                if response.data and len(response.data) > 0:
                    corr = response.data[0]
                    correlation = float(corr.get("correlation_30d", 0))
                    divergence = corr.get("divergence_detected", False)
                    
                    # If highly correlated and divergence detected, flag as conflict
                    if correlation > 0.6 and divergence:
                        conflicts.append({
                            "related_asset": related_asset,
                            "correlation": correlation,
                            "divergence_detected": True,
                            "risk_level": "HIGH" if correlation > 0.75 else "MEDIUM"
                        })
            
            logger.info(f"✅ Signal conflict check for {primary_asset}: {len(conflicts)} conflicts")
            
            return {
                "success": True,
                "primary_asset": primary_asset,
                "primary_side": primary_side,
                "conflicts": conflicts,
                "has_major_conflicts": len(conflicts) > 0
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to check signal conflicts: {e}")
            return {"success": False, "error": str(e)}
