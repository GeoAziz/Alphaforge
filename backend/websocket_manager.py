"""
WebSocket connection manager for real-time updates in FastAPI.
Place this in backend/websocket_manager.py
"""

import asyncio
import json
import logging
from typing import Set, Dict, Any, Callable, Optional
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections and broadcasting.
    
    Usage in main.py:
        ws_manager = WebSocketManager()
        
        @app.websocket("/ws/market-updates")
        async def websocket_market_updates(websocket: WebSocket, user_id: str = Query(...)):
            await ws_manager.connect(websocket, "market", user_id)
            try:
                while True:
                    data = await market_service.get_market_data()
                    await ws_manager.broadcast_to_group("market", {
                        "type": "market_update",
                        "data": data,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    await asyncio.sleep(5)
            except WebSocketDisconnect:
                await ws_manager.disconnect(websocket, "market", user_id)
    """
    
    def __init__(self):
        # Group name -> Set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # User tracking: Group -> Set of user_ids
        self.user_groups: Dict[str, Dict[str, WebSocket]] = {}
        # Connection metadata
        self.connection_meta: Dict[WebSocket, Dict[str, Any]] = {}
    
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
        
        Args:
            group: Group name
            message: Message to broadcast
            exclude_user: Optional user ID to exclude from broadcast
        """
        if group not in self.active_connections:
            return
        
        json_data = json.dumps(message)
        disconnected = []
        
        for websocket in self.active_connections[group]:
            try:
                meta = self.connection_meta.get(websocket, {})
                if exclude_user and meta.get("user_id") == exclude_user:
                    continue
                
                await websocket.send_text(json_data)
                
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for ws in disconnected:
            meta = self.connection_meta.get(ws, {})
            self.disconnect(ws, group, meta.get("user_id"))
    
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
            await websocket.send_json(message)
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
        return {
            group: self.get_group_stats(group)
            for group in self.active_connections.keys()
        }


# Singleton instance
_ws_manager: Optional[WebSocketManager] = None


def get_ws_manager() -> WebSocketManager:
    """Get or create WebSocket manager instance."""
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = WebSocketManager()
    return _ws_manager
