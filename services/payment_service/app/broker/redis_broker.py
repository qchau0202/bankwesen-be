"""
Redis Pub/Sub Message Broker for Payment Service

This module provides Redis-based publish/subscribe functionality for
asynchronous communication between services.
"""
import json
import logging
from typing import Dict, Any, Optional
import redis.asyncio as redis
from app.core.config import settings

logger = logging.getLogger(__name__)

# Redis client
redis_client: Optional[redis.Redis] = None


async def connect_to_redis():
    """Connect to Redis for pub/sub messaging."""
    global redis_client
    try:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        await redis_client.ping()
        logger.info(f"Connected to Redis at {settings.REDIS_URL}")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        redis_client = None


async def close_redis_connection():
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Closed Redis connection")


def get_redis_client() -> Optional[redis.Redis]:
    """Get Redis client instance."""
    return redis_client


async def publish_event(channel: str, event_type: str, data: Dict[str, Any]) -> bool:
    """
    Publish an event to a Redis channel.
    
    Args:
        channel: Redis channel name (e.g., "payment.events")
        event_type: Type of event (e.g., "payment.completed", "payment.created")
        data: Event data
        
    Returns:
        True if published successfully, False otherwise
    """
    if not redis_client:
        logger.warning("Redis client not initialized, skipping event publish")
        return False
    
    try:
        message = {
            "event_type": event_type,
            "data": data
        }
        
        await redis_client.publish(channel, json.dumps(message))
        logger.info(f"Published event '{event_type}' to channel '{channel}'")
        return True
    except Exception as e:
        logger.error(f"Failed to publish event to {channel}: {e}")
        return False


async def subscribe_to_channel(channel: str, callback):
    """
    Subscribe to a Redis channel and process messages.
    
    Args:
        channel: Redis channel name
        callback: Async function to handle received messages
    """
    if not redis_client:
        logger.error("Redis client not initialized")
        return
    
    try:
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(channel)
        logger.info(f"Subscribed to channel '{channel}'")
        
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    await callback(data)
                except Exception as e:
                    logger.error(f"Error processing message from {channel}: {e}")
    except Exception as e:
        logger.error(f"Error subscribing to {channel}: {e}")
