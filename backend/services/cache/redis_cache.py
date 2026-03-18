"""Redis caching layer for market data."""

import logging
import json
import redis.asyncio as redis
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis-based cache for market data with TTL support."""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.host = host
        self.port = port
        self.db = db
        self.client: Optional[redis.Redis] = None
        self.enabled = True
    
    async def connect(self):
        """Connect to Redis."""
        try:
            self.client = await redis.from_url(
                f"redis://{self.host}:{self.port}/{self.db}",
                encoding="utf8",
                decode_responses=True
            )
            # Test connection
            await self.client.ping()
            logger.info(f"✅ Redis cache connected ({self.host}:{self.port})")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}. Falling back to in-memory cache.")
            self.enabled = False
            self.client = None
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache."""
        if not self.enabled or not self.client:
            return None
        
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.warning(f"⚠️ Redis get error for {key}: {e}")
        
        return None
    
    async def set(self, key: str, value: Dict[str, Any], ttl_seconds: int = 60):
        """Set value in cache with TTL."""
        if not self.enabled or not self.client:
            return False
        
        try:
            json_value = json.dumps(value, default=str)
            await self.client.setex(key, ttl_seconds, json_value)
            return True
        except Exception as e:
            logger.warning(f"⚠️ Redis set error for {key}: {e}")
            return False
    
    async def get_many(self, keys: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get multiple values from cache."""
        if not self.enabled or not self.client:
            return {k: None for k in keys}
        
        try:
            values = await self.client.mget(keys)
            result = {}
            
            for key, value in zip(keys, values):
                if value:
                    result[key] = json.loads(value)
                else:
                    result[key] = None
            
            return result
        except Exception as e:
            logger.warning(f"⚠️ Redis mget error: {e}")
            return {k: None for k in keys}
    
    async def set_many(self, data: Dict[str, Dict[str, Any]], ttl_seconds: int = 60):
        """Set multiple values in cache."""
        if not self.enabled or not self.client:
            return False
        
        try:
            pipe = self.client.pipeline()
            
            for key, value in data.items():
                json_value = json.dumps(value, default=str)
                await pipe.setex(key, ttl_seconds, json_value)
            
            await pipe.execute()
            return True
        except Exception as e:
            logger.warning(f"⚠️ Redis mset error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not self.enabled or not self.client:
            return False
        
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"⚠️ Redis delete error: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        if not self.enabled or not self.client:
            return 0
        
        try:
            keys = await self.client.keys(pattern)
            if keys:
                return await self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"⚠️ Redis delete pattern error: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.enabled or not self.client:
            return False
        
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.warning(f"⚠️ Redis exists error: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """Get remaining TTL for key in seconds."""
        if not self.enabled or not self.client:
            return -1
        
        try:
            return await self.client.ttl(key)
        except Exception as e:
            logger.warning(f"⚠️ Redis ttl error: {e}")
            return -1
    
    async def clear(self) -> bool:
        """Clear entire cache database."""
        if not self.enabled or not self.client:
            return False
        
        try:
            await self.client.flushdb()
            logger.info("🗑️ Redis cache cleared")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Redis clear error: {e}")
            return False
    
    async def close(self):
        """Close Redis connection."""
        if self.client:
            await self.client.close()
            logger.info("🔌 Redis cache closed")
    
    def get_cache_key(self, prefix: str, symbol: str, interval: str = None) -> str:
        """Generate cache key for data."""
        if interval:
            return f"{prefix}:{symbol}:{interval}"
        return f"{prefix}:{symbol}"
