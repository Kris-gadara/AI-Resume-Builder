"""
Redis Caching Layer
====================
Cache expensive Gemini API calls and resume generations.
"""

import os
import json
import hashlib
import logging
from typing import Optional, Any
from functools import wraps

logger = logging.getLogger(__name__)

# Redis connection
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

redis_client = None

try:
    import redis
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
        socket_connect_timeout=2
    )
    redis_client.ping()
    logger.info("Redis cache connected successfully")
except ImportError:
    logger.warning("Redis library not installed, caching disabled. Install with: pip install redis")
except Exception as e:
    logger.warning(f"Redis unavailable, caching disabled: {e}")
    redis_client = None


def _make_cache_key(prefix: str, data: dict) -> str:
    """Generate a deterministic cache key from data."""
    serialized = json.dumps(data, sort_keys=True)
    hash_value = hashlib.md5(serialized.encode()).hexdigest()
    return f"{prefix}:{hash_value}"


def cached(prefix: str, ttl: int = 3600):
    """
    Decorator to cache function results in Redis.
    
    Args:
        prefix: Cache key prefix (e.g., 'summary', 'skills')
        ttl: Time-to-live in seconds (default 1 hour)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if redis_client is None:
                return func(*args, **kwargs)
            
            # Build cache key from function arguments
            # Convert args to dict for hashing
            cache_data = {
                'func': func.__name__,
                'args': str(args),
                'kwargs': {k: str(v) for k, v in kwargs.items()}
            }
            cache_key = _make_cache_key(prefix, cache_data)
            
            # Try to get from cache
            try:
                cached_value = redis_client.get(cache_key)
                if cached_value:
                    from .monitoring import record_cache_hit
                    record_cache_hit(prefix)
                    logger.info(f"Cache HIT for {prefix}")
                    return cached_value
            except Exception as e:
                logger.warning(f"Cache read error: {e}")
            
            # Cache miss - call function
            from .monitoring import record_cache_miss
            record_cache_miss(prefix)
            logger.info(f"Cache MISS for {prefix}")
            result = func(*args, **kwargs)
            
            # Store in cache (only cache strings)
            if isinstance(result, str):
                try:
                    redis_client.setex(cache_key, ttl, result)
                except Exception as e:
                    logger.warning(f"Cache write error: {e}")
            
            return result
        return wrapper
    return decorator


def clear_cache(pattern: str = "*"):
    """Clear cache entries matching pattern."""
    if redis_client is None:
        logger.warning("Redis not available, cannot clear cache")
        return
    
    count = 0
    try:
        for key in redis_client.scan_iter(match=pattern):
            redis_client.delete(key)
            count += 1
        logger.info(f"Cleared {count} cache entries matching '{pattern}'")
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")


def get_cache_stats() -> dict:
    """Get cache statistics."""
    if redis_client is None:
        return {
            'available': False,
            'message': 'Redis not available'
        }
    
    try:
        info = redis_client.info('stats')
        return {
            'available': True,
            'total_keys': redis_client.dbsize(),
            'hits': info.get('keyspace_hits', 0),
            'misses': info.get('keyspace_misses', 0),
        }
    except Exception as e:
        return {
            'available': False,
            'error': str(e)
        }
