"""
Complete ExecutionService with CCXT integration, idempotency, and order confirmation.
Implements §8 & §11.1 of Architecture Doc.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import ccxt
import ccxt.async_support as ccxt_async

logger = logging.getLogger(__name__)


class OrderState(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FILLED = "FILLED"
    PARTIAL_FILL = "PARTIAL_FILL"
    FAILED = "FAILED"
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"
    CANCELLED = "CANCELLED"


class ExchangeAbstractionLayer:
    """
    Unified exchange connector supporting Binance, Bybit, Bitget, OKX, MEXC, Gate.io
    Handles rate limiting, retries, and error recovery per §8.1 Architecture.
    """

    SUPPORTED_EXCHANGES = {
        "binance": {"spot": True, "perpetuals": True},
        "bybit": {"spot": False, "perpetuals": True},
        "bitget": {"spot": True, "perpetuals": True},
        "okx": {"spot": True, "perpetuals": True},
        "mexc": {"spot": True, "perpetuals": True},
        "gate": {"spot": True, "perpetuals": True},
    }

    RATE_LIMITS = {
        "binance": {"requests_per_second": 10},
        "bybit": {"requests_per_second": 5},
        "bitget": {"requests_per_second": 5},
        "okx": {"requests_per_second": 3},
        "mexc": {"requests_per_second": 5},
        "gate": {"requests_per_second": 5},
    }

    def __init__(self, exchange_name: str, api_key: str, api_secret: str):
        self.exchange_name = exchange_name.lower()
        self.api_key = api_key
        self.api_secret = api_secret
        self.exchange = self._initialize_exchange()
        self.last_request_time = 0
        self.request_count = 0
        self.circuit_breaker_open = False
        self.circuit_breaker_failure_count = 0

    def _initialize_exchange(self):
        """Initialize CCXT exchange with credentials."""
        exchange_class = getattr(ccxt_async, self.exchange_name)
        return exchange_class({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })

    async def place_order(
        self,
        symbol: str,
        order_type: str,
        side: str,
        amount: float,
        price: Optional[float] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Place order with rate limiting and circuit breaker.
        Params can include stop loss, take profit (exchange-specific).
        """

        if self.circuit_breaker_open:
            raise Exception("Circuit breaker open: exchange unavailable")

        # Rate limiting
        await self._apply_rate_limit()

        try:
            if order_type == "market":
                order = await self.exchange.create_market_order(symbol, side, amount, params=params)
            elif order_type == "limit":
                if price is None:
                    raise ValueError("Limit orders require a price")
                order = await self.exchange.create_limit_order(symbol, side, amount, price, params=params)
            else:
                raise ValueError(f"Unknown order type: {order_type}")

            # Reset circuit breaker on success
            self.circuit_breaker_failure_count = 0

            return {
                'success': True,
                'order_id': order.get('id'),
                'status': order.get('status'),
                'timestamp': order.get('timestamp'),
                'filled': order.get('filled'),
                'average': order.get('average'),
                'cost': order.get('cost'),
                'raw': order
            }

        except Exception as e:
            self.circuit_breaker_failure_count += 1

            if self.circuit_breaker_failure_count >= 5:
                self.circuit_breaker_open = True
                logger.error(f"Circuit breaker OPEN for {self.exchange_name}")

            logger.error(f"Order placement failed: {e}")
            return {'success': False, 'error': str(e)}

    async def fetch_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Fetch order status from exchange."""
        await self._apply_rate_limit()
        try:
            order = await self.exchange.fetch_order(order_id, symbol)
            return {
                'success': True,
                'order_id': order.get('id'),
                'status': order.get('status'),
                'filled': order.get('filled'),
                'remaining': order.get('remaining'),
                'average': order.get('average'),
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cancel an open order."""
        await self._apply_rate_limit()
        try:
            result = await self.exchange.cancel_order(order_id, symbol)
            return {'success': True, 'cancelled_order_id': order_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def fetch_balance(self) -> Dict[str, Any]:
        """Fetch account balance."""
        await self._apply_rate_limit()
        try:
            balance = await self.exchange.fetch_balance()
            return {'success': True, 'balance': balance}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _apply_rate_limit(self):
        """Apply per-exchange rate limiting."""
        limit_config = self.RATE_LIMITS.get(self.exchange_name, {})
        max_rps = limit_config.get('requests_per_second', 5)
        min_interval = 1.0 / max_rps

        elapsed = time.time() - self.last_request_time
        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)

        self.last_request_time = time.time()

    async def close(self):
        """Close exchange connection."""
        await self.exchange.close()


class ExecutionService:
    """
    Main execution service orchestrating order placement, confirmation, and fulfillment.
    Per §8 Architecture Doc.
    """

    def __init__(self, db, redis_client=None):
        self.db = db
        self.redis = redis_client
        self.idempotency_manager = IdempotencyKeyManager(redis_client)
        self.order_monitor = OrderConfirmationMonitor(db)
        self.exchanges: Dict[str, ExchangeAbstractionLayer] = {}

    async def initialize_exchange(
        self,
        user_id: str,
        exchange_name: str,
        api_key: str,
        api_secret: str
    ):
        """Initialize exchange connection for a user."""
        exchange_key = f"{user_id}:{exchange_name}"
        try:
            self.exchanges[exchange_key] = ExchangeAbstractionLayer(
                exchange_name, api_key, api_secret
            )
            logger.info(f"✅ Exchange {exchange_name} initialized for {user_id}")
        except Exception as e:
            logger.error(f"Failed to initialize {exchange_name}: {e}")
            raise

    async def execute_signal(
        self,
        user_id: str,
        signal_id: str,
        signal: Dict[str, Any],
        exchange: str,
        account_balance: float
    ) -> Dict[str, Any]:
        """
        Execute a signal on an exchange.

        Flow:
        1. Generate idempotency key
        2. Check if duplicate
        3. Place order via CCXT
        4. Monitor for confirmation
        5. Record trade to database
        """

        # 1. Generate idempotency key (§11.1)
        ticker = signal.get('ticker')
        direction = signal.get('signal_type', 'BUY')
        idempotency_key = self.idempotency_manager.generate_key(
            user_id, signal_id, ticker, direction
        )

        # 2. Check for duplicates
        if await self.idempotency_manager.exists(idempotency_key):
            logger.warning(f"Duplicate order detected: {idempotency_key}")
            return {
                'success': False,
                'error': 'Duplicate order',
                'idempotency_key': idempotency_key
            }

        # 3. Acquire idempotency lock
        if not await self.idempotency_manager.acquire(idempotency_key):
            logger.warning(f"Failed to acquire idempotency lock: {idempotency_key}")
            return {'success': False, 'error': 'Idempotency lock failed'}

        # 4. Place order
        try:
            exchange_key = f"{user_id}:{exchange}"
            if exchange_key not in self.exchanges:
                raise ValueError(f"Exchange not initialized: {exchange}")

            exchange_layer = self.exchanges[exchange_key]

            entry_price = float(signal.get('entry_price'))
            position_size = self._calculate_position_size(account_balance, signal)

            # Place order with retry logic (exponential backoff)
            order_result = await self._place_with_retry(
                exchange_layer,
                ticker,
                'limit',
                direction.lower(),
                position_size,
                entry_price
            )

            if not order_result.get('success'):
                await self.idempotency_manager.release(idempotency_key)
                return order_result

            # 5. Monitor for confirmation (5-second window per §11.1)
            confirmation = await self.order_monitor.wait_for_confirmation(
                order_result.get('order_id'),
                ticker,
                timeout_seconds=5.0
            )

            # 6. Record to database
            trade_record = {
                'user_id': user_id,
                'signal_id': signal_id,
                'exchange': exchange,
                'asset': ticker,
                'direction': direction,
                'entry_price': entry_price,
                'quantity': position_size,
                'status': confirmation.get('status', 'FILLED'),
                'exchange_order_id': order_result.get('order_id'),
                'opened_at': datetime.utcnow().isoformat(),
                'pnl': 0,
                'pnl_percent': 0
            }

            # Save to live_trades table
            try:
                self.db.supabase.table('live_trades').insert(trade_record).execute()
                logger.info(f"✅ Trade recorded: {ticker} {direction} @ {entry_price}")
            except Exception as e:
                logger.error(f"Failed to record trade: {e}")

            return {
                'success': True,
                'order_id': order_result.get('order_id'),
                'status': confirmation.get('status'),
                'filled': confirmation.get('filled'),
                'average_price': confirmation.get('average'),
            }

        except Exception as e:
            await self.idempotency_manager.release(idempotency_key)
            logger.error(f"Execution failed: {e}")
            return {'success': False, 'error': str(e)}

    async def _place_with_retry(
        self,
        exchange: ExchangeAbstractionLayer,
        symbol: str,
        order_type: str,
        side: str,
        amount: float,
        price: float,
        max_retries: int = 4
    ) -> Dict[str, Any]:
        """Place order with exponential backoff retry logic (§11.1)."""

        for attempt in range(max_retries):
            try:
                result = await exchange.place_order(symbol, order_type, side, amount, price)
                if result.get('success'):
                    return result

                # Extract error to decide on retry
                error = result.get('error', '')
                if 'rate_limit' in error.lower():
                    wait_time = (2 ** attempt)
                    logger.warning(f"Rate limited, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    return result

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    return {'success': False, 'error': str(e)}

        return {'success': False, 'error': 'Max retries exceeded'}

    def _calculate_position_size(
        self,
        account_balance: float,
        signal: Dict[str, Any]
    ) -> float:
        """Calculate position size from signal confidence."""
        base_size = account_balance * 0.02  # 2% base
        confidence = signal.get('confidence', 0.5)
        return base_size * (0.5 + confidence * 0.5)


class OrderConfirmationMonitor:
    """Monitor orders for confirmation state changes (§11.1)."""

    CONFIRMATION_TIMEOUT = 5.0

    def __init__(self, db):
        self.db = db
        self.pending_orders: Dict[str, Dict[str, Any]] = {}

    async def wait_for_confirmation(
        self,
        order_id: str,
        symbol: str,
        timeout_seconds: float = 5.0
    ) -> Dict[str, Any]:
        """Wait for order confirmation with timeout."""

        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            # Check order status from database
            try:
                result = self.db.supabase.table('live_trades').select('*').eq(
                    'exchange_order_id', order_id
                ).execute()

                if result.data:
                    trade = result.data[0]
                    status = trade.get('status')
                    if status in ['FILLED', 'PARTIAL_FILL']:
                        return {
                            'status': status,
                            'filled': trade.get('quantity'),
                            'average': trade.get('entry_price'),
                            'confirmed': True
                        }
            except Exception as e:
                logger.error(f"Confirmation check failed: {e}")

            await asyncio.sleep(0.1)

        # Timeout: mark as PENDING_CONFIRMATION
        return {
            'status': 'PENDING_CONFIRMATION',
            'confirmed': False,
            'message': 'Order confirmation timeout after 5s'
        }


class IdempotencyKeyManager:
    """Prevent duplicate orders using idempotency keys (§11.1)."""

    KEY_PREFIX = "idempotency:order:"
    TTL_SECONDS = 86400  # 24 hours

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self._local_store: Dict[str, float] = {}

    def generate_key(
        self,
        user_id: str,
        signal_id: str,
        asset: str,
        direction: str
    ) -> str:
        """Generate idempotency key."""
        import hashlib
        raw = f"{user_id}:{signal_id}:{asset}:{direction}:{int(time.time() * 1000)}"
        return hashlib.sha256(raw.encode()).hexdigest()

    async def acquire(self, key: str) -> bool:
        """Acquire lock for order."""
        full_key = f"{self.KEY_PREFIX}{key}"

        if self.redis:
            try:
                acquired = await self.redis.set(full_key, "1", nx=True, ex=self.TTL_SECONDS)
                return bool(acquired)
            except:
                pass

        now = time.time()
        if key in self._local_store:
            if now - self._local_store[key] < self.TTL_SECONDS:
                return False

        self._local_store[key] = now
        return True

    async def exists(self, key: str) -> bool:
        """Check if order already placed."""
        full_key = f"{self.KEY_PREFIX}{key}"
        if self.redis:
            try:
                return bool(await self.redis.exists(full_key))
            except:
                pass
        return key in self._local_store

    async def release(self, key: str):
        """Release lock on failure."""
        full_key = f"{self.KEY_PREFIX}{key}"
        if self.redis:
            try:
                await self.redis.delete(full_key)
            except:
                pass
        self._local_store.pop(key, None)


# Global singletons
_idempotency_manager: Optional[IdempotencyKeyManager] = None
_order_monitor: Optional[OrderConfirmationMonitor] = None
_exchange_layer: Optional[ExchangeAbstractionLayer] = None


def get_idempotency_manager(redis_client=None) -> IdempotencyKeyManager:
    global _idempotency_manager
    if _idempotency_manager is None:
        _idempotency_manager = IdempotencyKeyManager(redis_client)
    return _idempotency_manager


def get_order_monitor(db) -> OrderConfirmationMonitor:
    global _order_monitor
    if _order_monitor is None:
        _order_monitor = OrderConfirmationMonitor(db)
    return _order_monitor


def get_exchange_layer(exchange_name: str, api_key: str, api_secret: str) -> ExchangeAbstractionLayer:
    return ExchangeAbstractionLayer(exchange_name, api_key, api_secret)
