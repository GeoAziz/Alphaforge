"""
Binance WebSocket Stream Manager
Real-time market data via Binance WebSocket (reduces latency from 6s to <200ms).
Alternative to polling API for faster signal generation.
"""

import logging
import asyncio
import json
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import websockets
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)


class BinanceWebSocketManager:
    """
    Connects to Binance WebSocket for real-time market data.
    Supports: ticker (24h price change), klines (candlesticks), markPrice (futures).
    """
    
    BINANCE_WS_URL = "wss://stream.binance.com:9443/ws"
    
    def __init__(self):
        self.ws = None
        self.connected = False
        self.subscribed_streams = {}  # {stream_name: callback}
        self.tick_callbacks: List[Callable] = []
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
    
    async def connect(self) -> bool:
        """Establish WebSocket connection to Binance."""
        try:
            self.ws = await websockets.connect(self.BINANCE_WS_URL)
            self.connected = True
            self.reconnect_attempts = 0
            logger.info("✅ Connected to Binance WebSocket")
            return True
        
        except Exception as e:
            logger.error(f"❌ Failed to connect to Binance WebSocket: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Close WebSocket connection."""
        if self.ws:
            await self.ws.close()
            self.connected = False
            logger.info("🔌 WebSocket disconnected")
    
    async def subscribe_ticker(self, symbol: str, callback: Callable):
        """
        Subscribe to 24h ticker updates for a symbol.
        
        Stream name: btcusdt@ticker
        Updates every 1 second
        """
        stream_name = f"{symbol.lower()}@ticker"
        self.subscribed_streams[stream_name] = callback
        
        subscribe_msg = {
            "method": "SUBSCRIBE",
            "params": [stream_name],
            "id": 1
        }
        
        if self.connected and self.ws:
            try:
                await self.ws.send(json.dumps(subscribe_msg))
                logger.info(f"✅ Subscribed to {stream_name}")
            except Exception as e:
                logger.error(f"❌ Failed to subscribe to {stream_name}: {e}")
    
    async def subscribe_klines(
        self,
        symbol: str,
        interval: str = "1m",
        callback: Callable = None
    ):
        """
        Subscribe to kline (candlestick) updates.
        
        Intervals: 1m, 5m, 15m, 1h, 4h, 1d
        Updates when candle closes
        """
        stream_name = f"{symbol.lower()}@klines_{interval}"
        if callback:
            self.subscribed_streams[stream_name] = callback
        
        subscribe_msg = {
            "method": "SUBSCRIBE",
            "params": [f"{symbol.lower()}@klines_{interval}"],
            "id": 2
        }
        
        if self.connected and self.ws:
            try:
                await self.ws.send(json.dumps(subscribe_msg))
                logger.info(f"✅ Subscribed to klines {symbol} {interval}")
            except Exception as e:
                logger.error(f"❌ Failed to subscribe to klines: {e}")
    
    async def subscribe_mark_price(self, symbol: str, callback: Callable = None):
        """
        Subscribe to mark price updates (futures trading).
        Updates every 1 second.
        """
        stream_name = f"{symbol.lower()}@markPrice"
        if callback:
            self.subscribed_streams[stream_name] = callback
        
        subscribe_msg = {
            "method": "SUBSCRIBE",
            "params": [stream_name],
            "id": 3
        }
        
        if self.connected and self.ws:
            try:
                await self.ws.send(json.dumps(subscribe_msg))
                logger.info(f"✅ Subscribed to markPrice {symbol}")
            except Exception as e:
                logger.error(f"❌ Failed to subscribe to markPrice: {e}")
    
    async def listen(self):
        """
        Main listen loop - processes incoming WebSocket messages.
        Should run continuously in background.
        """
        while True:
            try:
                if not self.connected:
                    logger.warning("⚠️ WebSocket disconnected, attempting reconnect...")
                    
                    if self.reconnect_attempts < self.max_reconnect_attempts:
                        await asyncio.sleep(2 ** self.reconnect_attempts)  # Exponential backoff
                        if await self.connect():
                            pass  # Connection restored
                        else:
                            self.reconnect_attempts += 1
                    else:
                        logger.error("❌ Max reconnection attempts reached")
                        break
                    
                    continue
                
                # Receive message from WebSocket
                message = await self.ws.recv()
                data = json.loads(message)
                
                # Route based on stream type
                await self._handle_message(data)
            
            except ConnectionClosed:
                logger.warning("⚠️ WebSocket connection closed, will reconnect...")
                self.connected = False
            
            except Exception as e:
                logger.error(f"❌ Error in WebSocket listen loop: {e}")
                self.connected = False
    
    async def _handle_message(self, data: Dict[str, Any]):
        """Route incoming messages to appropriate handlers."""
        
        # Ticker update (24h price change)
        if "e" in data and data["e"] == "24hrTicker":
            await self._handle_ticker_update(data)
        
        # Kline update (candlestick)
        elif "e" in data and data["e"] == "kline":
            await self._handle_kline_update(data)
        
        # Mark price update (futures)
        elif "e" in data and data["e"] == "markPriceUpdate":
            await self._handle_mark_price_update(data)
    
    async def _handle_ticker_update(self, data: Dict[str, Any]):
        """Process 24h ticker update."""
        try:
            symbol = data.get("s")  # Symbol: BTCUSDT
            price = float(data.get("c", 0))  # Current price
            change_24h = float(data.get("P", 0))  # 24h price change %
            volume = float(data.get("v", 0))  # Volume
            
            ticker_data = {
                "symbol": symbol,
                "price": price,
                "change_24h": change_24h,
                "volume": volume,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "binance_ws"
            }
            
            # Call registered callbacks
            stream_key = f"{symbol.lower()}@ticker"
            if stream_key in self.subscribed_streams:
                callback = self.subscribed_streams[stream_key]
                if asyncio.iscoroutinefunction(callback):
                    await callback(ticker_data)
                else:
                    callback(ticker_data)
            
            # Broadcast to all listeners
            for cb in self.tick_callbacks:
                if asyncio.iscoroutinefunction(cb):
                    await cb(ticker_data)
                else:
                    cb(ticker_data)
        
        except Exception as e:
            logger.error(f"❌ Failed to handle ticker update: {e}")
    
    async def _handle_kline_update(self, data: Dict[str, Any]):
        """Process candle (kline) update."""
        try:
            symbol = data.get("s")
            kline = data.get("k", {})
            
            # Only process when candle is closed (helps with signal generation)
            if not kline.get("x"):  # x = is candle closed
                return
            
            interval = kline.get("i")  # 1m, 5m, etc
            
            kline_data = {
                "symbol": symbol,
                "interval": interval,
                "open": float(kline.get("o", 0)),
                "high": float(kline.get("h", 0)),
                "low": float(kline.get("l", 0)),
                "close": float(kline.get("c", 0)),
                "volume": float(kline.get("v", 0)),
                "quote_volume": float(kline.get("q", 0)),
                "timestamp": kline.get("t"),
                "closed_at": datetime.utcfromtimestamp(kline.get("T", 0) / 1000).isoformat()
            }
            
            stream_key = f"{symbol.lower()}@klines_{interval}"
            if stream_key in self.subscribed_streams:
                callback = self.subscribed_streams[stream_key]
                if asyncio.iscoroutinefunction(callback):
                    await callback(kline_data)
                else:
                    callback(kline_data)
        
        except Exception as e:
            logger.error(f"❌ Failed to handle kline update: {e}")
    
    async def _handle_mark_price_update(self, data: Dict[str, Any]):
        """Process mark price update (futures)."""
        try:
            symbol = data.get("s")
            mark_price = float(data.get("p", 0))
            index_price = float(data.get("i", 0))
            estimated_settle_price = float(data.get("P", 0))
            funding_rate = float(data.get("r", 0))
            
            mark_data = {
                "symbol": symbol,
                "mark_price": mark_price,
                "index_price": index_price,
                "estimated_settle_price": estimated_settle_price,
                "funding_rate": funding_rate,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            stream_key = f"{symbol.lower()}@markPrice"
            if stream_key in self.subscribed_streams:
                callback = self.subscribed_streams[stream_key]
                if asyncio.iscoroutinefunction(callback):
                    await callback(mark_data)
                else:
                    callback(mark_data)
        
        except Exception as e:
            logger.error(f"❌ Failed to handle mark price update: {e}")
    
    def register_tick_callback(self, callback: Callable):
        """Register a global callback for all ticker updates."""
        self.tick_callbacks.append(callback)
        logger.info(f"✅ Registered tick callback")
    
    async def get_connection_status(self) -> Dict[str, Any]:
        """Get current WebSocket connection status."""
        return {
            "connected": self.connected,
            "reconnect_attempts": self.reconnect_attempts,
            "subscribed_streams": list(self.subscribed_streams.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }


# Global instance
ws_manager: Optional[BinanceWebSocketManager] = None


async def initialize_binance_ws() -> BinanceWebSocketManager:
    """Initialize and connect Binance WebSocket manager."""
    global ws_manager
    
    ws_manager = BinanceWebSocketManager()
    
    if await ws_manager.connect():
        # Start listen loop in background
        asyncio.create_task(ws_manager.listen())
        logger.info("✅ Binance WebSocket initialized and listening")
    else:
        logger.warning("⚠️ Failed to initialize Binance WebSocket, falling back to polling")
    
    return ws_manager


def get_ws_manager() -> Optional[BinanceWebSocketManager]:
    """Get current WebSocket manager instance."""
    return ws_manager
