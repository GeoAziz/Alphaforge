"""
Bitget Exchange Integration - §9 Architecture Doc
Supports both spot and perpetuals markets.
"""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class BitgetExchange:
    """Bitget exchange connector."""

    BASE_URL = "https://api.bitget.com"

    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        passphrase: str = "",
        testnet: bool = True,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.testnet = testnet

    def _sign(self, timestamp: str, method: str, path: str, body: str = "") -> str:
        """Generate Bitget API signature."""
        message = timestamp + method.upper() + path + body
        mac = hmac.new(
            self.api_secret.encode(), message.encode(), hashlib.sha256
        )
        return base64.b64encode(mac.digest()).decode()

    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get current ticker."""
        result = await self._public_request("/api/v2/spot/market/tickers", {"symbol": symbol})
        if result.get("code") == "00000" and result.get("data"):
            t = result["data"][0]
            return {
                "success": True,
                "symbol": symbol,
                "price": float(t.get("lastPr", 0)),
                "bid": float(t.get("bidPr", 0)),
                "ask": float(t.get("askPr", 0)),
                "volume_24h": float(t.get("baseVolume", 0)),
                "change_24h_pct": float(t.get("change24h", 0)),
                "high_24h": float(t.get("high24h", 0)),
                "low_24h": float(t.get("low24h", 0)),
            }
        return {"success": False, "error": result.get("msg", "Unknown error")}

    async def get_klines(
        self, symbol: str, granularity: str = "1H", limit: int = 200
    ) -> Dict[str, Any]:
        """Get candlestick data."""
        result = await self._public_request(
            "/api/v2/spot/market/candles",
            {"symbol": symbol, "granularity": granularity, "limit": str(limit)},
        )
        if result.get("code") == "00000":
            candles = []
            for k in result.get("data", []):
                candles.append({
                    "open_time": int(k[0]),
                    "open": float(k[1]),
                    "high": float(k[2]),
                    "low": float(k[3]),
                    "close": float(k[4]),
                    "volume": float(k[5]),
                })
            return {"success": True, "symbol": symbol, "candles": candles}
        return {"success": False, "error": result.get("msg", "Unknown error")}

    async def get_futures_ticker(self, product_type: str = "USDT-FUTURES", symbol: str = "") -> Dict[str, Any]:
        """Get futures ticker for perpetuals."""
        result = await self._public_request(
            "/api/v2/mix/market/ticker",
            {"productType": product_type, "symbol": symbol},
        )
        if result.get("code") == "00000" and result.get("data"):
            t = result["data"]
            return {
                "success": True,
                "symbol": symbol,
                "price": float(t.get("lastPr", 0)),
                "mark_price": float(t.get("markPrice", 0)),
                "index_price": float(t.get("indexPrice", 0)),
                "volume_24h": float(t.get("baseVolume", 0)),
                "funding_rate": float(t.get("fundRate", 0)),
                "next_funding_rate": float(t.get("nextFundRate", 0)),
            }
        return {"success": False, "error": result.get("msg", "Unknown error")}

    async def get_futures_klines(
        self, product_type: str = "USDT-FUTURES", symbol: str = "",
        granularity: str = "1H", limit: int = 200
    ) -> Dict[str, Any]:
        """Get futures candlestick data."""
        result = await self._public_request(
            "/api/v2/mix/market/candles",
            {"productType": product_type, "symbol": symbol, "granularity": granularity, "limit": str(limit)},
        )
        if result.get("code") == "00000":
            candles = []
            for k in result.get("data", []):
                candles.append({
                    "open_time": int(k[0]),
                    "open": float(k[1]),
                    "high": float(k[2]),
                    "low": float(k[3]),
                    "close": float(k[4]),
                    "volume": float(k[5]),
                })
            return {"success": True, "symbol": symbol, "candles": candles}
        return {"success": False, "error": result.get("msg", "Unknown error")}

    async def validate_api_key(self) -> Dict[str, Any]:
        """Validate API key with read-only balance check."""
        result = await self._authenticated_request("GET", "/api/v2/spot/account/assets")
        if result.get("code") == "00000":
            assets = result.get("data", [])
            total_usdt = sum(float(a.get("available", 0)) for a in assets if a.get("coin") == "USDT")
            return {
                "success": True,
                "message": "API key valid",
                "asset_count": len(assets),
                "usdt_balance": total_usdt,
            }
        return {"success": False, "error": result.get("msg", "Invalid API key")}

    async def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        size: str,
        price: Optional[str] = None,
        trade_type: str = "spot",
    ) -> Dict[str, Any]:
        """Place an order."""
        if trade_type == "futures":
            return await self._place_futures_order(symbol, side, order_type, size, price)
        return await self._place_spot_order(symbol, side, order_type, size, price)

    async def _place_spot_order(
        self, symbol: str, side: str, order_type: str, size: str, price: Optional[str] = None
    ) -> Dict[str, Any]:
        """Place a spot order."""
        params = {
            "symbol": symbol,
            "side": side.lower(),
            "orderType": order_type.lower(),
            "size": size,
        }
        if price:
            params["price"] = price

        result = await self._authenticated_request("POST", "/api/v2/spot/trade/place-order", params)
        if result.get("code") == "00000":
            return {
                "success": True,
                "order_id": result.get("data", {}).get("orderId", ""),
                "exchange": "bitget",
                "symbol": symbol,
                "status": "submitted",
            }
        return {"success": False, "error": result.get("msg", "Order failed"), "exchange": "bitget"}

    async def _place_futures_order(
        self, symbol: str, side: str, order_type: str, size: str, price: Optional[str] = None
    ) -> Dict[str, Any]:
        """Place a futures/perpetual order."""
        params = {
            "productType": "USDT-FUTURES",
            "symbol": symbol,
            "marginMode": "cross",
            "side": side.lower(),
            "orderType": order_type.lower(),
            "size": size,
        }
        if price:
            params["price"] = price

        result = await self._authenticated_request("POST", "/api/v2/mix/trade/place-order", params)
        if result.get("code") == "00000":
            return {
                "success": True,
                "order_id": result.get("data", {}).get("orderId", ""),
                "exchange": "bitget",
                "symbol": symbol,
                "status": "submitted",
            }
        return {"success": False, "error": result.get("msg", "Order failed"), "exchange": "bitget"}

    async def get_positions(self, product_type: str = "USDT-FUTURES") -> Dict[str, Any]:
        """Get open positions."""
        result = await self._authenticated_request(
            "GET", "/api/v2/mix/position/products-position", {"productType": product_type}
        )
        if result.get("code") == "00000":
            positions = []
            for p in result.get("data", []):
                size = float(p.get("size", 0))
                if size != 0:
                    positions.append({
                        "symbol": p.get("symbol"),
                        "side": p.get("holdSide"),
                        "size": size,
                        "entry_price": float(p.get("averageOpenPrice", 0)),
                        "mark_price": float(p.get("markPrice", 0)),
                        "unrealised_pnl": float(p.get("unrealizedPL", 0)),
                        "leverage": float(p.get("leverage", 1)),
                    })
            return {"success": True, "positions": positions}
        return {"success": False, "error": result.get("msg", "Failed")}

    async def _public_request(self, path: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make public API request."""
        import aiohttp

        url = f"{self.BASE_URL}{path}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    return await resp.json()
        except Exception as e:
            logger.error(f"Bitget public request failed: {e}")
            return {"code": "-1", "msg": str(e)}

    async def _authenticated_request(
        self, method: str, path: str, body: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Make authenticated API request."""
        import aiohttp

        timestamp = str(int(time.time() * 1000))
        body_str = json.dumps(body) if body else ""
        sign = self._sign(timestamp, method, path, body_str)

        headers = {
            "ACCESS-KEY": self.api_key,
            "ACCESS-SIGN": sign,
            "ACCESS-TIMESTAMP": timestamp,
            "ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json",
        }

        url = f"{self.BASE_URL}{path}"
        try:
            async with aiohttp.ClientSession() as session:
                if method.upper() == "GET":
                    async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        return await resp.json()
                else:
                    async with session.post(url, headers=headers, data=body_str, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        return await resp.json()
        except Exception as e:
            logger.error(f"Bitget authenticated request failed: {e}")
            return {"code": "-1", "msg": str(e)}
