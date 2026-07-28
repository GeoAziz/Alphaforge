"""
OKX Exchange Integration - §9 Architecture Doc
Supports both spot and perpetuals markets.
"""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class OKXExchange:
    """OKX exchange connector."""

    TESTNET_BASE_URL = "https://www.okx.com"
    MAINNET_BASE_URL = "https://www.okx.com"

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
        self.base_url = self.MAINNET_BASE_URL

    def _sign(self, timestamp: str, method: str, path: str, body: str = "") -> str:
        """Generate OKX API signature."""
        message = f"{timestamp}{method}{path}{body}"
        mac = hmac.new(
            self.api_secret.encode(), message.encode(), hashlib.sha256
        )
        return base64.b64encode(mac.digest()).decode()

    async def get_ticker(self, instrument_id: str) -> Dict[str, Any]:
        """Get current ticker."""
        result = await self._public_request("/api/v5/market/ticker", {"instId": instrument_id})
        if result.get("code") == "0" and result.get("data"):
            t = result["data"][0]
            return {
                "success": True,
                "symbol": instrument_id,
                "price": float(t.get("last", 0)),
                "bid": float(t.get("bidPx", 0)),
                "ask": float(t.get("askPx", 0)),
                "volume_24h": float(t.get("vol24h", 0)),
                "change_24h_pct": float(t.get("sodUtc8", 0)),
                "high_24h": float(t.get("high24h", 0)),
                "low_24h": float(t.get("low24h", 0)),
            }
        return {"success": False, "error": result.get("msg", "Unknown error")}

    async def get_klines(
        self, instrument_id: str, bar: str = "1H", limit: int = 200
    ) -> Dict[str, Any]:
        """Get candlestick data."""
        result = await self._public_request(
            "/api/v5/market/candles",
            {"instId": instrument_id, "bar": bar, "limit": str(limit)},
        )
        if result.get("code") == "0":
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
            return {"success": True, "symbol": instrument_id, "candles": candles}
        return {"success": False, "error": result.get("msg", "Unknown error")}

    async def get_orderbook(self, instrument_id: str, depth: int = 25) -> Dict[str, Any]:
        """Get order book."""
        result = await self._public_request(
            "/api/v5/market/books", {"instId": instrument_id, "sz": str(depth)}
        )
        if result.get("code") == "0" and result.get("data"):
            book = result["data"][0]
            return {
                "success": True,
                "symbol": instrument_id,
                "bids": [[float(p), float(q)] for p, q, _, _ in book.get("bids", [])],
                "asks": [[float(p), float(q)] for p, q, _, _ in book.get("asks", [])],
                "timestamp": int(book.get("ts", 0)),
            }
        return {"success": False, "error": result.get("msg", "Unknown error")}

    async def get_funding_rate(self, instrument_id: str) -> Dict[str, Any]:
        """Get current funding rate."""
        result = await self._public_request(
            "/api/v5/public/funding-rate", {"instId": instrument_id}
        )
        if result.get("code") == "0" and result.get("data"):
            item = result["data"][0]
            return {
                "success": True,
                "symbol": instrument_id,
                "funding_rate": float(item.get("fundingRate", 0)),
                "next_funding_rate": float(item.get("nextFundingRate", 0)),
                "funding_time": int(item.get("fundingTime", 0)),
            }
        return {"success": False, "error": result.get("msg", "Unknown error")}

    async def validate_api_key(self) -> Dict[str, Any]:
        """Validate API key with read-only balance check."""
        result = await self._authenticated_request("GET", "/api/v5/account/balance")
        if result.get("code") == "0" and result.get("data"):
            details = result["data"][0].get("details", [])
            total_eq = sum(float(d.get("eqUsd", 0)) for d in details)
            return {
                "success": True,
                "message": "API key valid",
                "total_equity_usd": total_eq,
            }
        return {"success": False, "error": result.get("msg", "Invalid API key")}

    async def place_order(
        self,
        instrument_id: str,
        side: str,
        order_type: str,
        size: str,
        price: Optional[str] = None,
        td_mode: str = "cross",
        stop_loss: Optional[str] = None,
        take_profit: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Place an order on OKX."""
        params = {
            "instId": instrument_id,
            "tdMode": td_mode,
            "side": side.lower(),
            "ordType": order_type.lower(),
            "sz": size,
        }
        if price:
            params["px"] = price
        if stop_loss:
            params["slTriggerPx"] = stop_loss
            params["slOrdPx"] = "-1"
        if take_profit:
            params["tpTriggerPx"] = take_profit
            params["tpOrdPx"] = "-1"

        result = await self._authenticated_request("POST", "/api/v5/trade/order", params)

        if result.get("code") == "0" and result.get("data"):
            order_data = result["data"][0]
            return {
                "success": order_data.get("sCode") == "0",
                "order_id": order_data.get("ordId", ""),
                "exchange": "okx",
                "symbol": instrument_id,
                "side": side,
                "status": "submitted" if order_data.get("sCode") == "0" else "failed",
                "error": order_data.get("sMsg"),
            }
        return {
            "success": False,
            "error": result.get("msg", "Order failed"),
            "exchange": "okx",
        }

    async def get_positions(self, inst_type: str = "SWAP") -> Dict[str, Any]:
        """Get open positions."""
        result = await self._authenticated_request("GET", "/api/v5/account/positions", {"instType": inst_type})
        if result.get("code") == "0":
            positions = []
            for p in result.get("data", []):
                pos = float(p.get("pos", 0))
                if pos != 0:
                    positions.append({
                        "symbol": p.get("instId"),
                        "side": p.get("posSide", "long"),
                        "size": abs(pos),
                        "entry_price": float(p.get("avgPx", 0)),
                        "mark_price": float(p.get("markPx", 0)),
                        "unrealised_pnl": float(p.get("upl", 0)),
                        "leverage": float(p.get("lever", 1)),
                        "liq_price": float(p.get("liqPx", 0)) if p.get("liqPx") else None,
                    })
            return {"success": True, "positions": positions}
        return {"success": False, "error": result.get("msg", "Failed")}

    async def _public_request(self, path: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make public API request."""
        import aiohttp

        url = f"{self.base_url}{path}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    return await resp.json()
        except Exception as e:
            logger.error(f"OKX public request failed: {e}")
            return {"code": "-1", "msg": str(e)}

    async def _authenticated_request(
        self, method: str, path: str, body: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Make authenticated API request."""
        import aiohttp

        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.") + f"{datetime.utcnow().microsecond // 1000:03d}Z"
        body_str = json.dumps(body) if body else ""
        sign = self._sign(timestamp, method.upper(), path, body_str)

        headers = {
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-SIGN": sign,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}{path}"
        try:
            async with aiohttp.ClientSession() as session:
                if method.upper() == "GET":
                    async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        return await resp.json()
                else:
                    async with session.post(url, headers=headers, data=body_str, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        return await resp.json()
        except Exception as e:
            logger.error(f"OKX authenticated request failed: {e}")
            return {"code": "-1", "msg": str(e)}
