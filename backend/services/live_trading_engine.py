"""
Live trading execution engine with support for Binance, Bybit, OKX, Kraken,
MEXC, and Gate.io via the unified ccxt library.
Handles real-money trade execution with safety guardrails.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from config import ExchangeConfig, DevelopmentConfig

logger = logging.getLogger(__name__)


class OrderSide(str, Enum):
    """Order side types."""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Order types."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"


class ExchangeConnector:
    """Unified exchange connector backed by ccxt."""

    #: ccxt exchange id, overridden per exchange subclass
    CCXT_ID: str = ""

    def __init__(self, exchange_name: str, api_key: str, api_secret: str,
                 testnet: bool = True, password: Optional[str] = None):
        self.exchange_name = exchange_name
        self.api_key = api_key
        self.api_secret = api_secret
        self.password = password
        self.testnet = testnet
        self.client = None
        self._initialize()

    def _initialize(self):
        """Initialize the ccxt exchange client."""
        logger.info(f"Initializing {self.exchange_name} connector (testnet={self.testnet})")

        if DevelopmentConfig.MOCK_EXCHANGE:
            return

        try:
            import ccxt.async_support as ccxt

            exchange_class = getattr(ccxt, self.CCXT_ID)
            params: Dict[str, Any] = {
                "apiKey": self.api_key,
                "secret": self.api_secret,
                "enableRateLimit": True,
            }
            if self.password:
                params["password"] = self.password

            self.client = exchange_class(params)

            if self.testnet:
                try:
                    self.client.set_sandbox_mode(True)
                except Exception:
                    logger.warning(f"{self.exchange_name} ccxt driver has no sandbox mode")

            logger.info(f"✅ {self.exchange_name} client initialized (ccxt/{self.CCXT_ID})")

        except ImportError:
            logger.error("ccxt not installed. Run: pip install ccxt")
            self.client = None
        except AttributeError:
            logger.error(f"Unknown ccxt exchange id: {self.CCXT_ID}")
            self.client = None

    def _symbol(self, symbol: str) -> str:
        """Convert e.g. BTCUSDT -> ccxt's BTC/USDT market symbol."""
        if "/" in symbol:
            return symbol
        for quote in ("USDT", "USDC", "USD", "BTC", "ETH"):
            if symbol.endswith(quote) and len(symbol) > len(quote):
                return f"{symbol[:-len(quote)]}/{quote}"
        return symbol

    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        order_type: OrderType = OrderType.MARKET,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Place a trade order."""
        if DevelopmentConfig.MOCK_EXCHANGE or not self.client:
            return self._mock_order(symbol, side, quantity)

        try:
            ccxt_symbol = self._symbol(symbol)
            ccxt_side = side.value.lower()
            ccxt_type = "market" if order_type == OrderType.MARKET else "limit"

            order = await self.client.create_order(
                symbol=ccxt_symbol,
                type=ccxt_type,
                side=ccxt_side,
                amount=quantity,
                price=price if ccxt_type == "limit" else None,
            )
            logger.info(f"✅ Order placed on {self.exchange_name}: {order.get('id')}")
            return {"success": True, "order": order}

        except (ValueError, KeyError) as e:
            logger.error(f"❌ {self.exchange_name} order validation failed: {e}")
            return {"success": False, "error": f"Validation error: {str(e)}"}
        except Exception as e:
            logger.error(f"❌ {self.exchange_name} order failed (exchange error): {e}")
            return {"success": False, "error": f"Exchange error: {str(e)}"}

    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cancel an open order."""
        if DevelopmentConfig.MOCK_EXCHANGE or not self.client:
            return {"success": True, "order_id": order_id, "status": "CANCELED"}

        try:
            result = await self.client.cancel_order(order_id, self._symbol(symbol))
            return {"success": True, "order": result}
        except (ValueError, KeyError) as e:
            logger.error(f"❌ {self.exchange_name} cancel validation failed: {e}")
            return {"success": False, "error": f"Validation error: {str(e)}"}
        except Exception as e:
            logger.error(f"❌ {self.exchange_name} cancel failed (exchange error): {e}")
            return {"success": False, "error": f"Exchange error: {str(e)}"}

    async def get_balance(self, asset: str = None) -> Dict[str, Any]:
        """Get account balance."""
        if DevelopmentConfig.MOCK_EXCHANGE or not self.client:
            return {"success": True, "asset": asset or "USDT", "free": 10000.0, "locked": 0.0}

        try:
            balance = await self.client.fetch_balance()
            if asset:
                free = balance.get("free", {}).get(asset, 0.0)
                used = balance.get("used", {}).get(asset, 0.0)
                return {"success": True, "asset": asset, "free": free, "locked": used}
            return {"success": True, "balances": balance}
        except (KeyError, TypeError) as e:
            logger.error(f"❌ Failed to parse {self.exchange_name} balance response: {e}")
            return {"success": False, "error": f"Parse error: {str(e)}"}
        except Exception as e:
            logger.error(f"❌ Failed to fetch {self.exchange_name} balance (exchange error): {e}")
            return {"success": False, "error": f"Exchange error: {str(e)}"}

    async def get_open_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Get all open orders."""
        if DevelopmentConfig.MOCK_EXCHANGE or not self.client:
            return []

        try:
            orders = await self.client.fetch_open_orders(self._symbol(symbol) if symbol else None)
            return orders
        except (ValueError, KeyError) as e:
            logger.error(f"❌ Failed to parse {self.exchange_name} open orders: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Failed to fetch {self.exchange_name} open orders (exchange error): {e}")
            return []

    def _mock_order(self, symbol: str, side: OrderSide, quantity: float) -> Dict[str, Any]:
        """Generate mock order response."""
        return {
            "success": True,
            "order": {
                "orderId": f"mock-{self.exchange_name}-order",
                "symbol": symbol,
                "side": side.value,
                "quantity": quantity,
                "status": "FILLED",
                "timestamp": datetime.utcnow().isoformat(),
            }
        }

    async def close(self):
        """Cleanup."""
        if self.client:
            try:
                await self.client.close()
            except Exception:
                pass


class BinanceConnector(ExchangeConnector):
    CCXT_ID = "binance"


class BybitConnector(ExchangeConnector):
    CCXT_ID = "bybit"


class OKXConnector(ExchangeConnector):
    CCXT_ID = "okx"


class KrakenConnector(ExchangeConnector):
    CCXT_ID = "kraken"


class MEXCConnector(ExchangeConnector):
    CCXT_ID = "mexc"


class GateioConnector(ExchangeConnector):
    CCXT_ID = "gateio"


class LiveTradingEngine:
    """Orchestrates live trading across exchanges."""

    def __init__(self):
        self.enabled = ExchangeConfig.LIVE_TRADING_ENABLED
        self.connectors: Dict[str, ExchangeConnector] = {}
        self._initialize_connectors()

    def _initialize_connectors(self):
        """Initialize all configured exchange connectors."""
        if not self.enabled:
            logger.warning("Live trading disabled")
            return

        if ExchangeConfig.BINANCE_API_KEY:
            self.connectors["binance"] = BinanceConnector(
                "binance", ExchangeConfig.BINANCE_API_KEY,
                ExchangeConfig.BINANCE_SECRET, ExchangeConfig.BINANCE_TESTNET,
            )

        if ExchangeConfig.BYBIT_API_KEY:
            self.connectors["bybit"] = BybitConnector(
                "bybit", ExchangeConfig.BYBIT_API_KEY,
                ExchangeConfig.BYBIT_SECRET, ExchangeConfig.BYBIT_TESTNET,
            )

        if ExchangeConfig.OKX_API_KEY:
            self.connectors["okx"] = OKXConnector(
                "okx", ExchangeConfig.OKX_API_KEY, ExchangeConfig.OKX_SECRET,
                ExchangeConfig.OKX_TESTNET, password=ExchangeConfig.OKX_PASSPHRASE,
            )

        if ExchangeConfig.KRAKEN_API_KEY:
            self.connectors["kraken"] = KrakenConnector(
                "kraken", ExchangeConfig.KRAKEN_API_KEY,
                ExchangeConfig.KRAKEN_PRIVATE_KEY, ExchangeConfig.KRAKEN_TESTNET,
            )

        if ExchangeConfig.MEXC_API_KEY:
            self.connectors["mexc"] = MEXCConnector(
                "mexc", ExchangeConfig.MEXC_API_KEY,
                ExchangeConfig.MEXC_SECRET, ExchangeConfig.MEXC_TESTNET,
            )

        if ExchangeConfig.GATEIO_API_KEY:
            self.connectors["gateio"] = GateioConnector(
                "gateio", ExchangeConfig.GATEIO_API_KEY, ExchangeConfig.GATEIO_SECRET,
                ExchangeConfig.GATEIO_TESTNET, password=ExchangeConfig.GATEIO_PASSPHRASE,
            )

        logger.info(f"✅ Live trading engine initialized with {len(self.connectors)} exchanges")

    async def execute_signal(
        self,
        user_id: str,
        signal: Dict[str, Any],
        exchange: str = "binance",
        auto_execute: bool = False,
    ) -> Dict[str, Any]:
        """Execute trading signal on specified exchange."""
        if not self.enabled:
            return {"success": False, "error": "Live trading disabled"}

        if exchange not in self.connectors:
            return {"success": False, "error": f"Exchange {exchange} not configured"}

        try:
            connector = self.connectors[exchange]
            symbol = f"{signal['ticker']}USDT"
            side = OrderSide.BUY if signal["signal_type"] == "BUY" else OrderSide.SELL

            quantity = await self._calculate_position_size(connector, signal)
            if quantity <= 0:
                return {"success": False, "error": "Calculated position size is zero (insufficient balance or invalid signal)"}

            order = await connector.place_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=signal.get("entry_price"),
            )

            logger.info(f"✅ Signal executed for {user_id} on {exchange}: {order}")
            return order

        except KeyError as e:
            logger.error(f"❌ Signal execution: missing required field {e}")
            return {"success": False, "error": f"Missing field: {str(e)}"}
        except ValueError as e:
            logger.error(f"❌ Signal execution: invalid value {e}")
            return {"success": False, "error": f"Invalid value: {str(e)}"}
        except Exception as e:
            logger.error(f"❌ Signal execution failed (unhandled error): {e}")
            return {"success": False, "error": f"Execution failed: {str(e)}"}

    async def _calculate_position_size(
        self, connector: "ExchangeConnector", signal: Dict[str, Any], quote_asset: str = "USDT",
    ) -> float:
        """Calculate position size from the account's real available balance."""
        risk_pct = 0.02  # 2% per trade
        entry_price = float(signal.get("entry_price", 0))
        stop_loss = float(signal.get("stop_loss", entry_price * 0.98))

        if entry_price == 0:
            return 0

        balance = await connector.get_balance(quote_asset)
        if not balance.get("success"):
            logger.warning(f"⚠️  Could not fetch balance for position sizing: {balance.get('error')}")
            return 0

        available = float(balance.get("free", 0))
        risk_per_trade = available * risk_pct
        amount_at_risk = abs(entry_price - stop_loss)
        position_size = risk_per_trade / amount_at_risk if amount_at_risk > 0 else 0

        return min(position_size, ExchangeConfig.MAX_POSITION_SIZE)

    async def get_balance(self, exchange: str = "binance", asset: str = "USDT") -> Dict[str, Any]:
        """Get account balance from exchange."""
        if exchange not in self.connectors:
            return {"success": False, "error": f"Exchange {exchange} not found"}

        connector = self.connectors[exchange]
        return await connector.get_balance(asset)

    async def close(self):
        """Close all exchange connections."""
        for connector in self.connectors.values():
            await connector.close()
        logger.info("🔌 Live trading engine closed")
