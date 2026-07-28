"""
Bybit Exchange Integration - §9 Architecture Doc
Supports both spot and perpetuals markets via REST and WebSocket APIs.
"""

import asyncio
import hashlib
import hmac
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class BybitExchange:
    """
    Bybit exchange connector for market data and order placement.
    Supports testnet mode for safe development.
    """

    TESTNET_BASE_URL = "https://api-testnet.bybit.com"
    MAINNET_BASE_URL = "https://api.bybit.com"
    WS_PUBLIC_URL = "wss://stream-testnet.bybit.com/v5/public/linear"
    WS_PRIVATE_URL = "wss://stream-testnet.bybit.com/v5/private"

    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        testnet: bool = True,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.base_url = self.TESTNET_BASE_URL if testnet else self.MAINNET_BASE_URL
        self._rate_limit_remaining = 120
        self._rate_limit_reset = time.time()

    def _sign(self, params: Dict[str, Any]) -> str:
        """Generate HMAC signature for authenticated requests."""
        timestamp = str(int(time.time() * 1000))
        params["timestamp"] = timestamp
        query_string = urlencode(sorted(params.items()))
        signature = hmac.new(
            self.api_secret.encode(),
            query_string.encode(),
            hashlib.sha256,
        ).hexdigest()
        return signature

    async def get_server_time(self) -> Dict[str, Any]:
        """Get server time for clock synchronization."""
        return await self._public_request("/v5/market/time")

    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get current ticker data for a symbol."""
        result = await self._public_request("/v5/market/tickers", {"category": "linear", "symbol": symbol})
        if result.get("retCode") == 0 and result.get("result", {}).get("list"):
            ticker = result["result"]["list"][0]
            return {
                "success": True,
                "symbol": symbol,
                "price": float(ticker.get("lastPrice", 0)),
                "bid": float(ticker.get("bid1Price", 0)),
                "ask": float(ticker.get("ask1Price", 0)),
                "volume_24h": float(ticker.get("volume24h", 0)),
                "change_24h_pct": float(ticker.get("price24hPcnt", 0)) * 100,
                "high_24h": float(ticker.get("highPrice24h", 0)),
                "low_24h": float(ticker.get("lowPrice24h", 0)),
            }
        return {"success": False, "error": result.get("retMsg", "Unknown error")}

    async def get_klines(
        self, symbol: str, interval: str = "1h", limit: int = 200
    ) -> Dict[str, Any]:
        """Get candlestick/kline data."""
        result = await self._public_request(
            "/v5/market/kline",
            {"category": "linear", "symbol": symbol, "interval": interval, "limit": str(limit)},
        )
        if result.get("retCode") == 0:
            candles = []
            for k in result.get("result", {}).get("list", []):
                candles.append({
                    "open_time": int(k[0]),
                    "open": float(k[1]),
                    "high": float(k[2]),
                    "low": float(k[3]),
                    "close": float(k[4]),
                    "volume": float(k[5]),
                    "close_time": int(k[0]) + 3600000,
                })
            return {"success": True, "symbol": symbol, "interval": interval, "candles": candles}
        return {"success": False, "error": result.get("retMsg", "Unknown error")}

    async def get_orderbook(self, symbol: str, limit: int = 25) -> Dict[str, Any]:
        """Get order book depth."""
        result = await self._public_request(
            "/v5/market/orderbook",
            {"category": "linear", "symbol": symbol, "limit": str(limit)},
        )
        if result.get("retCode") == 0:
            book = result["result"]
            return {
                "success": True,
                "symbol": symbol,
                "bids": [[float(p), float(q)] for p, q in book.get("b", [])],
                "asks": [[float(p), float(q)] for p, q in book.get("a", [])],
                "timestamp": int(book.get("ts", 0)),
            }
        return {"success": False, "error": result.get("retMsg", "Unknown error")}

    async def get_funding_rate(self, symbol: str) -> Dict[str, Any]:
        """Get current funding rate for perpetuals."""
        result = await self._public_request(
            "/v5/market/funding/history",
            {"category": "linear", "symbol": symbol, "limit": "1"},
        )
        if result.get("retCode") == 0 and result.get("result", {}).get("list"):
            item = result["result"]["list"][0]
            return {
                "success": True,
                "symbol": symbol,
                "funding_rate": float(item.get("fundingRate", 0)),
                "funding_timestamp": int(item.get("fundingRateTimestamp", 0)),
            }
        return {"success": False, "error": result.get("retMsg", "Unknown error")}

    async def get_open_interest(self, symbol: str) -> Dict[str, Any]:
        """Get open interest for perpetuals."""
        result = await self._public_request(
            "/v5/market/open-interest",
            {"category": "linear", "symbol": symbol, "intervalTime": "1h", "limit": "1"},
        )
        if result.get("retCode") == 0 and result.get("result", {}).get("list"):
            item = result["result"]["list"][0]
            return {
                "success": True,
                "symbol": symbol,
                "open_interest": float(item.get("openInterest", 0)),
                "timestamp": int(item.get("timestamp", 0)),
            }
        return {"success": False, "error": result.get("retMsg", "Unknown error")}

    async def validate_api_key(self) -> Dict[str, Any]:
        """Validate API key by fetching wallet balance (read-only test)."""
        try:
            result = await self._authenticated_request("/v5/account/wallet-balance", {"accountType": "UNIFIED"})
            if result.get("retCode") == 0:
                coins = result.get("result", {}).get("list", [{}])[0].get("coin", [])
                total_equity = sum(float(c.get("equity", 0)) for c in coins)
                return {
                    "success": True,
                    "message": "API key valid",
                    "total_equity": total_equity,
                    "coin_count": len(coins),
                }
            return {"success": False, "error": result.get("retMsg", "Invalid API key")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        time_in_force: str = "GTC",
        reduce_only: bool = False,
    ) -> Dict[str, Any]:
        """Place an order on Bybit."""
        params = {
            "category": "linear",
            "symbol": symbol,
            "side": side.upper(),
            "orderType": order_type.upper(),
            "qty": str(quantity),
        }

        if price and order_type.upper() == "LIMIT":
            params["price"] = str(price)
            params["timeInForce"] = time_in_force

        if stop_loss:
            params["stopLoss"] = str(stop_loss)
        if take_profit:
            params["takeProfit"] = str(take_profit)
        if reduce_only:
            params["reduceOnly"] = "true"

        result = await self._authenticated_request("/v5/order/create", params)

        if result.get("retCode") == 0:
            order_data = result.get("result", {})
            return {
                "success": True,
                "order_id": order_data.get("orderId", ""),
                "exchange": "bybit",
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "quantity": quantity,
                "price": price,
                "status": "submitted",
            }
        return {
            "success": False,
            "error": result.get("retMsg", "Order failed"),
            "exchange": "bybit",
        }

    async def get_positions(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get open positions."""
        params = {"category": "linear"}
        if symbol:
            params["symbol"] = symbol

        result = await self._authenticated_request("/v5/position/list", params)
        if result.get("retCode") == 0:
            positions = []
            for p in result.get("result", {}).get("list", []):
                size = float(p.get("size", 0))
                if size > 0:
                    positions.append({
                        "symbol": p.get("symbol"),
                        "side": p.get("side"),
                        "size": size,
                        "entry_price": float(p.get("avgPrice", 0)),
                        "mark_price": float(p.get("markPrice", 0)),
                        "unrealised_pnl": float(p.get("unrealisedPnl", 0)),
                        "leverage": float(p.get("leverage", 1)),
                        "liq_price": float(p.get("liqPrice", 0)),
                    })
            return {"success": True, "positions": positions}
        return {"success": False, "error": result.get("retMsg", "Failed to get positions")}

    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cancel an open order."""
        result = await self._authenticated_request(
            "/v5/order/cancel", {"category": "linear", "orderId": order_id, "symbol": symbol}
        )
        return {
            "success": result.get("retCode") == 0,
            "order_id": order_id,
            "error": result.get("retMsg") if result.get("retCode") != 0 else None,
        }

    async def _public_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a public (unauthenticated) API request."""
        import aiohttp

        url = f"{self.base_url}{endpoint}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    return await resp.json()
        except Exception as e:
            logger.error(f"Bybit public request failed: {e}")
            return {"retCode": -1, "retMsg": str(e)}

    async def _authenticated_request(
        self, endpoint: str, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Make an authenticated API request."""
        import aiohttp

        if params is None:
            params = {}

        timestamp = str(int(time.time() * 1000))
        params["timestamp"] = timestamp
        query_string = urlencode(sorted(params.items()))
        sign = hmac.new(
            self.api_secret.encode(), query_string.encode(), hashlib.sha256
        ).hexdigest()

        url = f"{self.base_url}{endpoint}?{query_string}&sign={sign}"
        headers = {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-SIGN": sign,
            "X-BAPI-TIMESTAMP": timestamp,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    return await resp.json()
        except Exception as e:
            logger.error(f"Bybit authenticated request failed: {e}")
            return {"retCode": -1, "retMsg": str(e)}
