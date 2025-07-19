"""
Redis cache management for sessions and caching
Reference: https://redis.io/docs/connect/clients/python/
"""

import redis.asyncio as redis
from typing import Optional, Any
import json
from app.shared.config import settings


class CacheManager:
    """
    Redis cache manager for application caching needs.
    
    Single Responsibility: Cache operations management
    """
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._redis: Optional[redis.Redis] = None
    
    async def connect(self):
        """Establish Redis connection."""
        self._redis = redis.from_url(self.redis_url, decode_responses=True)
    
    async def disconnect(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
    
    async def set(self, key: str, value: Any, expire: int = 3600):
        """
        Set a value in cache with expiration.
        
        Single Responsibility: Cache value storage
        """
        if not self._redis:
            await self.connect()
        
        serialized_value = json.dumps(value) if not isinstance(value, str) else value
        await self._redis.set(key, serialized_value, ex=expire)
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        
        Single Responsibility: Cache value retrieval
        """
        if not self._redis:
            await self.connect()
        
        value = await self._redis.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    async def delete(self, key: str):
        """
        Delete a value from cache.
        
        Single Responsibility: Cache value removal
        """
        if not self._redis:
            await self.connect()
        
        await self._redis.delete(key)


# Global cache manager instance
cache_manager = CacheManager(settings.redis_url)
