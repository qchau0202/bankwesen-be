import redis.asyncio as redis
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class RedisClient:
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
    
    async def connect(self, redis_url: str):
        try:
            self.redis = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test the connection
            await self.redis.ping()
            logger.info("Successfully connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis")
    
    async def set(self, key: str, value: str, expiration: int):
        if not self.redis:
            raise Exception("Redis client not connected")
        await self.redis.setex(key, expiration, value)
    
    async def get(self, key: str) -> Optional[str]:
        if not self.redis:
            raise Exception("Redis client not connected")
        return await self.redis.get(key)
    
    async def delete(self, key: str):
        if not self.redis:
            raise Exception("Redis client not connected")
        await self.redis.delete(key)
    
    async def exists(self, key: str) -> bool:
        if not self.redis:
            raise Exception("Redis client not connected")
        return await self.redis.exists(key) > 0
    
    async def ttl(self, key: str) -> int:
        if not self.redis:
            raise Exception("Redis client not connected")
        return await self.redis.ttl(key)
    
    async def incr(self, key: str) -> int:
        if not self.redis:
            raise Exception("Redis client not connected")
        return await self.redis.incr(key)
    
    async def expire(self, key: str, expiration: int):
        if not self.redis:
            raise Exception("Redis client not connected")
        await self.redis.expire(key, expiration)

# Global Redis client instance
redis_client = RedisClient()

async def get_redis() -> RedisClient:
    return redis_client
