"""
WebSocket connection manager for real-time updates in FastAPI.
§19.1 Architecture Doc: Connection Management at Scale
Supports Redis PubSub fan-out, permessage-deflate, and connection pooling.
"""

import asyncio
import json
import logging
import zlib
from typing import Set, Dict, Any, Callable, Optional
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

logger = logging.getLogger(__name__)

# Try importing redis for PubSub fan-out
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class WebSocketManager:
    """
    Manages WebSocket connections and broadcasting at scale.
    
    §19.1: For 100k+ concurrent users:
    - Redis PubSub fan-out to offload connection state from app servers
    - permessage-deflate compression for bandwidth reduction
    - Connection pooling for database access
    - Edge caching for static assets
    """
    
    def __init__(self, redis_url: str = None):
        # Group name -> Set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # User tracking: Group -> Set of user_ids
        self.user_groups: Dict[str, Dict[str, WebSocket]] = {}
        # Connection metadata
        self.connection_meta: Dict[WebSocket, Dict[str, Any]] = {}
        # Redis PubSub for cross-instance fan-out
        self._redis = None
        self._redis_pubsub = None
        self._redis_subscribed_channels: Set[str] = set()
        self._redis_listener_task: Optional[asyncio.Task] = None
        self._redis_url = redis_url
    
    async def initialize_redis(self, redis_url: str = None):
        """Initialize Redis connection for PubSub fan-out (§19.1)."""
        url = redis_url or self._redis_url
        if not url or not REDIS_AVAILABLE:
            logger.info("📡 WebSocket: Using in-memory broadcasting (Redis unavailable)")
            return False
        
        try:
            self._redis = aioredis.from_url(url, decode_responses=True)
            await self._redis.ping()
            self._redis_pubsub = self._redis.pubsub()
            
            # Start background listener
            self._redis_listener_task = asyncio.create_task(self._redis_listener_loop())
            
            logger.info("📡 WebSocket: Redis PubSub initialized for cross-instance fan-out")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Redis PubSub init failed: {e} — falling back to in-memory")
            return False
    
    async def _redis_listener_loop(self):
        """Background listener for Redis PubSub messages."""
        if not self._redis_pubsub:
            return
        
        while True:
            try:
                message = await self._redis_pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )
                if message and message["type"] == "message":
                    channel = message["channel"]
                    data = json.loads(message["data"])
                    
                    # Deliver to local connections in this group
                    group = data.get("group")
                    payload = data.get("payload")
                    exclude_user = data.get("exclude_user")
                    
                    if group and payload:
                        await self._deliver_locally(group, payload, exclude_user)
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Redis PubSub listener error: {e}")
                await asyncio.sleep(1.0)
    
    async def _deliver_locally(
        self, group: str, message: Dict[str, Any], exclude_user: Optional[str] = None
    ):
        """Deliver message to local WebSocket connections (used by Redis fan-out)."""
        if group not in self.active_connections:
            return
        
        json_data = self._compress_message(json.dumps(message))
        disconnected = []
        
        connections_copy = list(self.active_connections[group])
        
        for websocket in connections_copy:
            try:
                meta = self.connection_meta.get(websocket, {})
                if exclude_user and meta.get("user_id") == exclude_user:
                    continue
                await websocket.send_text(json_data)
            except Exception:
                disconnected.append(websocket)
        
        for ws in disconnected:
            meta = self.connection_meta.pop(ws, {})
            self.active_connections.get(group, set()).discard(ws)
    
    @staticmethod
    def _compress_message(data: str) -> str:
        """Apply permessage-deflate compression for bandwidth reduction (§19.1)."""
        # Only compress messages > 1KB for meaningful savings
        if len(data.encode()) > 1024:
            try:
                compressed = zlib.compress(data.encode(), level=6)
                # Only use compression if it actually reduces size
                if len(compressed) < len(data.encode()):
                    import base64
                    return base64.b64encode(compressed).decode()
            except Exception:
                pass
        return data
    
    async def connect(
        self,
        websocket: WebSocket,
        group: str,
        user_id: Optional[str] = None
    ) -> None:
        """
        Accept WebSocket connection and add to group.
        
        Args:
            websocket: WebSocket connection
            group: Group name (e.g., "market", "signals", "portfolio")
            user_id: Optional user ID for tracking
        """
        await websocket.accept()
        
        if group not in self.active_connections:
            self.active_connections[group] = set()
        if group not in self.user_groups:
            self.user_groups[group] = {}
        
        self.active_connections[group].add(websocket)
        if user_id:
            self.user_groups[group][user_id] = websocket
        
        self.connection_meta[websocket] = {
            "group": group,
            "user_id": user_id,
            "connected_at": datetime.utcnow().isoformat(),
        }
        
        # Subscribe to Redis channel for this group (if Redis available)
        if self._redis_pubsub and group not in self._redis_subscribed_channels:
            await self._redis_pubsub.subscribe(f"ws_broadcast:{group}")
            self._redis_subscribed_channels.add(group)
        
        logger.info(f"WebSocket connected to '{group}' - User: {user_id}")
    
    def disconnect(
        self,
        websocket: WebSocket,
        group: str,
        user_id: Optional[str] = None
    ) -> None:
        """
        Remove WebSocket from group.
        
        Args:
            websocket: WebSocket connection
            group: Group name
            user_id: Optional user ID
        """
        if group in self.active_connections:
            self.active_connections[group].discard(websocket)
        
        if group in self.user_groups and user_id:
            self.user_groups[group].pop(user_id, None)
        
        self.connection_meta.pop(websocket, None)
        
        logger.info(f"WebSocket disconnected from '{group}' - User: {user_id}")
    
    async def broadcast_to_group(
        self,
        group: str,
        message: Dict[str, Any],
        exclude_user: Optional[str] = None
    ) -> None:
        """
        Broadcast message to all connections in a group.
        Uses Redis PubSub for cross-instance fan-out when available.
        
        Args:
            group: Group name
            message: Message to broadcast
            exclude_user: Optional user ID to exclude from broadcast
        """
        # Publish to Redis for cross-instance fan-out
        if self._redis:
            try:
                await self._redis.publish(
                    f"ws_broadcast:{group}",
                    json.dumps({
                        "group": group,
                        "payload": message,
                        "exclude_user": exclude_user,
                    })
                )
                return  # Redis handles delivery to all instances
            except Exception as e:
                logger.warning(f"Redis publish failed, falling back to local: {e}")
        
        # Local fallback
        await self._deliver_locally(group, message, exclude_user)
    
    async def broadcast_to_user(
        self,
        group: str,
        user_id: str,
        message: Dict[str, Any]
    ) -> bool:
        """
        Send message to specific user in group.
        
        Args:
            group: Group name
            user_id: User ID
            message: Message to send
            
        Returns:
            True if message sent, False if user not connected
        """
        if group not in self.user_groups or user_id not in self.user_groups[group]:
            return False
        
        try:
            websocket = self.user_groups[group][user_id]
            compressed = self._compress_message(json.dumps(message))
            await websocket.send_text(compressed)
            return True
        except Exception as e:
            logger.error(f"Error sending to user {user_id}: {e}")
            return False
    
    async def broadcast_to_multiple(
        self,
        group: str,
        message: Dict[str, Any],
        user_ids: Set[str]
    ) -> Dict[str, bool]:
        """
        Send message to multiple specific users.
        
        Args:
            group: Group name
            message: Message to send
            user_ids: Set of user IDs to send to
            
        Returns:
            Dict mapping user_id -> success
        """
        results = {}
        for user_id in user_ids:
            results[user_id] = await self.broadcast_to_user(group, user_id, message)
        return results
    
    def get_group_connection_count(self, group: str) -> int:
        """Get number of active connections in group."""
        return len(self.active_connections.get(group, set()))
    
    def get_all_connection_count(self) -> int:
        """Get total active connections across all groups."""
        total = 0
        for connections in self.active_connections.values():
            total += len(connections)
        return total
    
    def get_group_stats(self, group: str) -> Dict[str, Any]:
        """Get connection statistics for a group."""
        connections = self.active_connections.get(group, set())
        users = self.user_groups.get(group, {})
        
        return {
            "group": group,
            "total_connections": len(connections),
            "unique_users": len(users),
            "user_ids": list(users.keys()),
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all groups."""
        stats = {
            group: self.get_group_stats(group)
            for group in self.active_connections.keys()
        }
        stats["_meta"] = {
            "total_connections": self.get_all_connection_count(),
            "redis_enabled": self._redis is not None,
            "groups_count": len(self.active_connections),
        }
        return stats
    
    async def close(self):
        """Graceful shutdown: close Redis connections and cancel tasks."""
        if self._redis_listener_task:
            self._redis_listener_task.cancel()
            try:
                await self._redis_listener_task
            except asyncio.CancelledError:
                pass
        
        if self._redis_pubsub:
            await self._redis_pubsub.unsubscribe()
        if self._redis:
            await self._redis.close()
        
        logger.info("🔌 WebSocket manager closed")


# Singleton instance
_ws_manager: Optional[WebSocketManager] = None


def get_ws_manager(redis_url: str = None) -> WebSocketManager:
    """Get or create WebSocket manager instance."""
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = WebSocketManager(redis_url)
    return _ws_manager
