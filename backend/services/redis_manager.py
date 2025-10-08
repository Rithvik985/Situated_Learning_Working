# redis_manager.py
import os
import logging
import redis.asyncio as aioredis
from typing import Optional

logger = logging.getLogger(__name__)

class RedisManager:
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        password: Optional[str] = None,
        db: Optional[int] = None,
        decode_responses: bool = True,
    ):
        # read from env if not provided
        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = int(port or os.getenv("REDIS_PORT", 6379))
        self.password = password or os.getenv("REDIS_PASSWORD", None)
        self.db = int(db or os.getenv("REDIS_DB", 0))
        self.decode_responses = decode_responses

        self._redis: Optional[aioredis.Redis] = None

    async def init(self):
        """Create the async Redis client and verify connectivity."""
        if self._redis:
            return

        self._redis = aioredis.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            decode_responses=self.decode_responses,
            # optional: set a short socket timeout if you want
            socket_timeout=5,
        )
        try:
            await self._redis.ping()
            logger.info("Connected to Redis %s:%s db=%s", self.host, self.port, self.db)
        except Exception as e:
            logger.exception("Failed to connect to Redis: %s", e)
            # re-raise so the app startup can fail if desired
            raise

    async def get(self, key: str):
        if not self._redis:
            raise RuntimeError("Redis client not initialized. Call init() first.")
        return await self._redis.get(key)

    async def setex(self, key: str, ttl_seconds: int, value):
        """Set key with expiry in seconds"""
        if not self._redis:
            raise RuntimeError("Redis client not initialized. Call init() first.")
        return await self._redis.setex(key, ttl_seconds, value)

    async def delete(self, key: str):
        if not self._redis:
            raise RuntimeError("Redis client not initialized. Call init() first.")
        return await self._redis.delete(key)

    async def close(self):
        if self._redis:
            try:
                await self._redis.close()
                # disconnect underlying connections
                await self._redis.connection_pool.disconnect()
                logger.info("Closed Redis connection.")
            except Exception:
                logger.exception("Error while closing Redis connection.")
            finally:
                self._redis = None
