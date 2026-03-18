"""In-memory caching layer as fallback when Redis is unavailable."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class CacheEntry:
    """Single cache entry with TTL."""
    
    def __init__(self, value: Dict[str, Any], ttl_seconds: int):
        self.value = value
        self.created_at = datetime.utcnow()
        self.ttl_seconds = ttl_seconds
    
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        elapsed = (datetime.utcnow() - self.created_at).total_seconds()
        return elapsed > self.ttl_seconds
    
    def remaining_ttl(self) -> int:
        """Get remaining TTL in seconds."""
        elapsed = (datetime.utcnow() - self.created_at).total_seconds()
        return max(0, self.ttl_seconds - int(elapsed))


class InMemoryCache:
    """Simple in-memory cache with TTL support."""
    
    def __init__(self, max_entries: int = 10000):
        self.cache: Dict[str, CacheEntry] = {}
        self.max_entries = max_entries
        self.enabled = True
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache."""
        if not self.enabled:
            return None
        
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        # Check if expired
        if entry.is_expired():
            del self.cache[key]
            return None
        
        return entry.value
    
    async def set(self, key: str, value: Dict[str, Any], ttl_seconds: int = 60):
        """Set value in cache with TTL."""
        if not self.enabled:
            return False
        
        # Simple eviction: remove oldest entry if at capacity
        if len(self.cache) >= self.max_entries and key not in self.cache:
            oldest_key = min(
                self.cache.keys(),
                key=lambda k: self.cache[k].created_at
            )
            del self.cache[oldest_key]
        
        self.cache[key] = CacheEntry(value, ttl_seconds)
        return True
    
    async def get_many(self, keys: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get multiple values from cache."""
        result = {}
        
        for key in keys:
            result[key] = await self.get(key)
        
        return result
    
    async def set_many(self, data: Dict[str, Dict[str, Any]], ttl_seconds: int = 60):
        """Set multiple values in cache."""
        for key, value in data.items():
            await self.set(key, value, ttl_seconds)
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        import fnmatch
        
        keys_to_delete = [k for k in self.cache.keys() if fnmatch.fnmatch(k, pattern)]
        count = len(keys_to_delete)
        
        for key in keys_to_delete:
            del self.cache[key]
        
        return count
    
    async def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        if key not in self.cache:
            return False
        
        entry = self.cache[key]
        
        if entry.is_expired():
            del self.cache[key]
            return False
        
        return True
    
    async def ttl(self, key: str) -> int:
        """Get remaining TTL for key in seconds."""
        if key not in self.cache:
            return -2  # Key doesn't exist
        
        entry = self.cache[key]
        
        if entry.is_expired():
            del self.cache[key]
            return -2
        
        return entry.remaining_ttl()
    
    async def clear(self) -> bool:
        """Clear entire cache."""
        self.cache.clear()
        logger.info("🗑️ In-memory cache cleared")
        return True
    
    async def close(self):
        """Cleanup (no-op for in-memory cache)."""
        logger.info("🔌 In-memory cache closed")
    
    def get_cache_key(self, prefix: str, symbol: str, interval: str = None) -> str:
        """Generate cache key for data."""
        if interval:
            return f"{prefix}:{symbol}:{interval}"
        return f"{prefix}:{symbol}"
    
    def get_user_cache_key(self, user_id: str, prefix: str, suffix: str = None) -> str:
        """Generate user-specific cache key."""
        if suffix:
            return f"user:{user_id}:{prefix}:{suffix}"
        return f"user:{user_id}:{prefix}"
    
    async def set_user_data(
        self,
        user_id: str,
        prefix: str,
        data: Dict[str, Any],
        ttl_seconds: int = 300,
        suffix: str = None
    ) -> bool:
        """Cache user-specific data (portfolio, settings, etc)."""
        try:
            key = self.get_user_cache_key(user_id, prefix, suffix)
            
            # Check capacity
            if len(self.cache) >= self.max_entries:
                self._evict_oldest()
            
            self.cache[key] = CacheEntry(data, ttl_seconds)
            return True
        
        except Exception as e:
            logger.error(f"❌ Failed to set user cache: {e}")
            return False
    
    async def get_user_data(
        self,
        user_id: str,
        prefix: str,
        suffix: str = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieve user-specific cached data."""
        try:
            key = self.get_user_cache_key(user_id, prefix, suffix)
            
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            
            if entry.is_expired():
                del self.cache[key]
                return None
            
            return entry.value
        
        except Exception as e:
            logger.error(f"❌ Failed to get user cache: {e}")
            return None
    
    def get_user_cache_stats(self, user_id: str) -> Dict[str, Any]:
        """Get cache statistics for a specific user."""
        user_prefix = f"user:{user_id}:"
        user_entries = {k: v for k, v in self.cache.items() if k.startswith(user_prefix)}
        
        expired = sum(1 for e in user_entries.values() if e.is_expired())
        
        return {
            "user_id": user_id,
            "total_entries": len(user_entries),
            "expired_entries": expired,
            "active_entries": len(user_entries) - expired
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        expired = sum(1 for e in self.cache.values() if e.is_expired())
        
        return {
            "total_entries": len(self.cache),
            "expired_entries": expired,
            "active_entries": len(self.cache) - expired,
            "max_capacity": self.max_entries,
            "usage_percentage": (len(self.cache) / self.max_entries) * 100
        }
