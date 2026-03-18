"""Redis initialization and health check utilities."""

import logging
import redis.asyncio as redis
from typing import Optional
from config import Config

logger = logging.getLogger(__name__)


class RedisManager:
    """Manages Redis connection and provides health checks."""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.enabled = False
        self.connection_string = f"redis://{Config.REDIS_HOST}:{Config.REDIS_PORT}/{Config.REDIS_DB}"
    
    async def connect(self) -> bool:
        """
        Attempt to connect to Redis.
        
        Returns:
            True if connection successful, False otherwise
        """
        cache_backend = Config.CACHE_BACKEND.lower()
        
        if cache_backend != "redis":
            logger.info(f"🟢 Cache backend set to: {cache_backend} (Redis disabled)")
            return False
        
        try:
            self.client = await redis.from_url(
                self.connection_string,
                encoding="utf8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True
            )
            
            # Test connection
            pong = await self.client.ping()
            if pong:
                self.enabled = True
                info = await self.client.info()
                redis_version = info.get("redis_version", "unknown")
                logger.info(f"✅ Redis connected successfully (v{redis_version})")
                logger.info(f"   Host: {Config.REDIS_HOST}:{Config.REDIS_PORT}")
                logger.info(f"   DB: {Config.REDIS_DB}")
                return True
        
        except Exception as e:
            logger.warning(f"⚠️  Redis connection failed: {e}")
            logger.info(f"   Fallback: In-memory cache will be used")
            logger.info(f"   To use Redis, ensure it's running: docker run -d -p 6379:6379 redis")
            self.enabled = False
            return False
    
    async def health_check(self) -> dict:
        """
        Check Redis health status.
        
        Returns:
            Dict with status information
        """
        if not self.enabled or not self.client:
            return {
                "redis_enabled": False,
                "cache_backend": Config.CACHE_BACKEND,
                "status": "fallback (in-memory)"
            }
        
        try:
            pong = await self.client.ping()
            info = await self.client.info()
            
            return {
                "redis_enabled": True,
                "connection": "healthy",
                "version": info.get("redis_version", "unknown"),
                "used_memory_mb": info.get("used_memory", 0) / 1024 / 1024,
                "connected_clients": info.get("connected_clients", 0),
                "commands_processed": info.get("total_commands_processed", 0)
            }
        except Exception as e:
            return {
                "redis_enabled": True,
                "connection": "unhealthy",
                "error": str(e)
            }
    
    async def close(self):
        """Close Redis connection."""
        if self.client:
            await self.client.close()
            logger.info("🔌 Redis connection closed")


# Global Redis manager instance
redis_manager = RedisManager()
