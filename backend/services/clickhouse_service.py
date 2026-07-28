"""
ClickHouse Analytics Service
High-performance time-series analytics for market data, signals, and performance metrics.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from clickhouse_driver import Client as ClickHouseClient
    CLICKHOUSE_AVAILABLE = True
except ImportError:
    CLICKHOUSE_AVAILABLE = False
    logger.warning("clickhouse-driver not installed. ClickHouse features disabled.")


class ClickHouseService:
    """ClickHouse analytics service for time-series data."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 9000,
        database: str = "alphaforge_analytics",
        user: str = "alphaforge",
        password: str = "alphaforge",
    ):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self._client: Optional[Any] = None

    async def initialize(self) -> bool:
        """Initialize ClickHouse connection."""
        if not CLICKHOUSE_AVAILABLE:
            logger.warning("ClickHouse not available")
            return False

        try:
            self._client = ClickHouseClient(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
            )
            # Test connection
            result = self._client.execute("SELECT 1")
            if result == [(1,)]:
                logger.info(f"✅ ClickHouse connected: {self.host}:{self.port}")
                return True
            else:
                logger.error("ClickHouse connection test failed")
                return False
        except Exception as e:
            logger.error(f"❌ ClickHouse initialization failed: {e}")
            return False

    async def close(self):
        """Close ClickHouse connection."""
        if self._client:
            self._client.disconnect()
            logger.info("🔌 ClickHouse connection closed")

    # ==========================================================================
    # Market Data
    # ==========================================================================

    async def insert_market_price(self, data: Dict[str, Any]) -> bool:
        """Insert a market price record."""
        if not self._client:
            return False

        try:
            self._client.execute(
                """
                INSERT INTO market_prices (timestamp, asset, exchange, open, high, low, close, volume, quote_volume)
                VALUES
                """,
                [{
                    "timestamp": data.get("timestamp", datetime.utcnow()),
                    "asset": data["asset"],
                    "exchange": data.get("exchange", "unknown"),
                    "open": data.get("open", 0),
                    "high": data.get("high", 0),
                    "low": data.get("low", 0),
                    "close": data.get("close", 0),
                    "volume": data.get("volume", 0),
                    "quote_volume": data.get("quote_volume", 0),
                }],
            )
            return True
        except Exception as e:
            logger.error(f"Failed to insert market price: {e}")
            return False

    async def insert_market_prices_batch(self, records: List[Dict[str, Any]]) -> bool:
        """Batch insert market prices."""
        if not self._client or not records:
            return False

        try:
            self._client.execute(
                """
                INSERT INTO market_prices (timestamp, asset, exchange, open, high, low, close, volume, quote_volume)
                VALUES
                """,
                records,
            )
            logger.info(f"Inserted {len(records)} market price records")
            return True
        except Exception as e:
            logger.error(f"Failed to batch insert market prices: {e}")
            return False

    # ==========================================================================
    # Signal Events
    # ==========================================================================

    async def insert_signal_event(self, data: Dict[str, Any]) -> bool:
        """Insert a signal event."""
        if not self._client:
            return False

        try:
            self._client.execute(
                """
                INSERT INTO signal_events (timestamp, signal_id, user_id, ticker, signal_type, confidence, entry_price, source)
                VALUES
                """,
                [{
                    "timestamp": data.get("timestamp", datetime.utcnow()),
                    "signal_id": data["signal_id"],
                    "user_id": data.get("user_id", ""),
                    "ticker": data.get("ticker", ""),
                    "signal_type": data.get("signal_type", ""),
                    "confidence": data.get("confidence", 0),
                    "entry_price": data.get("entry_price", 0),
                    "source": data.get("source", "system"),
                }],
            )
            return True
        except Exception as e:
            logger.error(f"Failed to insert signal event: {e}")
            return False

    # ==========================================================================
    # Trade Events
    # ==========================================================================

    async def insert_trade_event(self, data: Dict[str, Any]) -> bool:
        """Insert a trade event."""
        if not self._client:
            return False

        try:
            self._client.execute(
                """
                INSERT INTO trade_events (timestamp, trade_id, user_id, signal_id, ticker, direction, quantity, entry_price, exit_price, pnl, status, exchange)
                VALUES
                """,
                [{
                    "timestamp": data.get("timestamp", datetime.utcnow()),
                    "trade_id": data["trade_id"],
                    "user_id": data.get("user_id", ""),
                    "signal_id": data.get("signal_id", ""),
                    "ticker": data.get("ticker", ""),
                    "direction": data.get("direction", ""),
                    "quantity": data.get("quantity", 0),
                    "entry_price": data.get("entry_price", 0),
                    "exit_price": data.get("exit_price"),
                    "pnl": data.get("pnl"),
                    "status": data.get("status", "open"),
                    "exchange": data.get("exchange", ""),
                }],
            )
            return True
        except Exception as e:
            logger.error(f"Failed to insert trade event: {e}")
            return False

    # ==========================================================================
    # Analytics Queries
    # ==========================================================================

    async def get_signal_stats(
        self,
        ticker: Optional[str] = None,
        hours: int = 24,
    ) -> Dict[str, Any]:
        """Get signal generation statistics."""
        if not self._client:
            return {}

        try:
            where_clause = "WHERE timestamp >= now() - INTERVAL %(hours)s HOUR"
            params = {"hours": hours}

            if ticker:
                where_clause += " AND ticker = %(ticker)s"
                params["ticker"] = ticker

            result = self._client.execute(
                f"""
                SELECT
                    count() as total_signals,
                    avg(confidence) as avg_confidence,
                    countIf(signal_type = 'BUY') as buy_signals,
                    countIf(signal_type = 'SELL') as sell_signals,
                    countIf(signal_type = 'HOLD') as hold_signals,
                    uniq(user_id) as unique_users
                FROM signal_events
                {where_clause}
                """,
                params,
            )

            if result:
                row = result[0]
                return {
                    "total_signals": row[0],
                    "avg_confidence": round(row[1], 4) if row[1] else 0,
                    "buy_signals": row[2],
                    "sell_signals": row[3],
                    "hold_signals": row[4],
                    "unique_users": row[5],
                    "period_hours": hours,
                }
            return {}
        except Exception as e:
            logger.error(f"Failed to get signal stats: {e}")
            return {}

    async def get_trade_performance(
        self,
        user_id: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get trade performance analytics."""
        if not self._client:
            return {}

        try:
            where_clause = "WHERE timestamp >= now() - INTERVAL %(days)s DAY AND pnl IS NOT NULL"
            params = {"days": days}

            if user_id:
                where_clause += " AND user_id = %(user_id)s"
                params["user_id"] = user_id

            result = self._client.execute(
                f"""
                SELECT
                    count() as total_trades,
                    sum(pnl) as total_pnl,
                    avg(pnl) as avg_pnl,
                    min(pnl) as worst_trade,
                    max(pnl) as best_trade,
                    countIf(pnl > 0) as winning_trades,
                    countIf(pnl < 0) as losing_trades
                FROM trade_events
                {where_clause}
                """,
                params,
            )

            if result:
                row = result[0]
                total = row[0] or 1
                win_rate = (row[5] / total * 100) if total > 0 else 0
                return {
                    "total_trades": row[0],
                    "total_pnl": round(row[1], 2) if row[1] else 0,
                    "avg_pnl": round(row[2], 2) if row[2] else 0,
                    "worst_trade": round(row[3], 2) if row[3] else 0,
                    "best_trade": round(row[4], 2) if row[4] else 0,
                    "win_rate": round(win_rate, 2),
                    "winning_trades": row[5],
                    "losing_trades": row[6],
                    "period_days": days,
                }
            return {}
        except Exception as e:
            logger.error(f"Failed to get trade performance: {e}")
            return {}

    async def get_market_price_history(
        self,
        asset: str,
        hours: int = 24,
    ) -> List[Dict[str, Any]]:
        """Get market price history."""
        if not self._client:
            return []

        try:
            result = self._client.execute(
                """
                SELECT
                    toStartOfHour(timestamp) as hour,
                    argMin(close, timestamp) as open,
                    max(high) as high,
                    min(low) as low,
                    argMax(close, timestamp) as close,
                    sum(volume) as volume
                FROM market_prices
                WHERE asset = %(asset)s
                  AND timestamp >= now() - INTERVAL %(hours)s HOUR
                GROUP BY hour
                ORDER BY hour
                """,
                {"asset": asset, "hours": hours},
            )

            return [
                {
                    "timestamp": row[0].isoformat(),
                    "open": row[1],
                    "high": row[2],
                    "low": row[3],
                    "close": row[4],
                    "volume": row[5],
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Failed to get price history: {e}")
            return []

    async def get_user_activity(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """Get user activity summary."""
        if not self._client:
            return {}

        try:
            result = self._client.execute(
                """
                SELECT
                    count() as total_events,
                    uniq(event_type) as unique_events,
                    min(timestamp) as first_event,
                    max(timestamp) as last_event
                FROM user_activity
                WHERE user_id = %(user_id)s
                  AND timestamp >= now() - INTERVAL %(days)s DAY
                """,
                {"user_id": user_id, "days": days},
            )

            if result:
                row = result[0]
                return {
                    "total_events": row[0],
                    "unique_event_types": row[1],
                    "first_event": row[2].isoformat() if row[2] else None,
                    "last_event": row[3].isoformat() if row[3] else None,
                }
            return {}
        except Exception as e:
            logger.error(f"Failed to get user activity: {e}")
            return {}

    # ==========================================================================
    # Health Check
    # ==========================================================================

    def health_check(self) -> Dict[str, Any]:
        """Check ClickHouse health."""
        if not self._client:
            return {"status": "disconnected", "backend": "clickhouse"}

        try:
            result = self._client.execute("SELECT 1")
            return {
                "status": "healthy" if result == [(1,)] else "unhealthy",
                "backend": "clickhouse",
                "host": self.host,
                "database": self.database,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "backend": "clickhouse",
                "error": str(e),
            }


# Global instance
clickhouse_service: Optional[ClickHouseService] = None


async def get_clickhouse_service() -> ClickHouseService:
    """Get or create the global ClickHouse service."""
    global clickhouse_service
    if clickhouse_service is None:
        clickhouse_service = ClickHouseService(
            host=os.getenv("CLICKHOUSE_HOST", "localhost"),
            port=int(os.getenv("CLICKHOUSE_PORT", "9000")),
            database=os.getenv("CLICKHOUSE_DATABASE", "alphaforge_analytics"),
            user=os.getenv("CLICKHOUSE_USER", "alphaforge"),
            password=os.getenv("CLICKHOUSE_PASSWORD", "alphaforge"),
        )
        await clickhouse_service.initialize()
    return clickhouse_service
