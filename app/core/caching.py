"""
Caching strategies and Redis integration.
"""
import json
import pickle
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
import redis
from functools import wraps

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheBackend:
    """Abstract cache backend."""
    
    def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        raise NotImplementedError
    
    def delete(self, key: str) -> bool:
        raise NotImplementedError
    
    def exists(self, key: str) -> bool:
        raise NotImplementedError
    
    def clear_pattern(self, pattern: str) -> int:
        raise NotImplementedError


class RedisCache(CacheBackend):
    """Redis cache backend."""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self._client = None
    
    @property
    def client(self):
        """Get Redis client with lazy initialization."""
        if self._client is None:
            try:
                self._client = redis.from_url(
                    self.redis_url,
                    decode_responses=False,  # We'll handle encoding ourselves
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                # Test connection
                self._client.ping()
                logger.info("Redis connection established")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {str(e)}")
                self._client = None
                raise
        
        return self._client
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        try:
            data = self.client.get(key)
            if data is None:
                return None
            
            # Try to deserialize
            try:
                return pickle.loads(data)
            except:
                # Fallback to JSON
                return json.loads(data.decode('utf-8'))
                
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in Redis cache."""
        try:
            # Try to serialize with pickle first (more efficient)
            try:
                data = pickle.dumps(value)
            except:
                # Fallback to JSON
                data = json.dumps(value, default=str).encode('utf-8')
            
            return self.client.setex(key, ttl, data)
            
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from Redis cache."""
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in Redis cache."""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Error checking cache key {key}: {str(e)}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Error clearing cache pattern {pattern}: {str(e)}")
            return 0
    
    def increment(self, key: str, amount: int = 1, ttl: int = None) -> int:
        """Increment counter in Redis."""
        try:
            pipe = self.client.pipeline()
            pipe.incr(key, amount)
            if ttl:
                pipe.expire(key, ttl)
            results = pipe.execute()
            return results[0]
        except Exception as e:
            logger.error(f"Error incrementing cache key {key}: {str(e)}")
            return 0


class MemoryCache(CacheBackend):
    """In-memory cache backend (fallback)."""
    
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.timestamps = {}
        self.max_size = max_size
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache."""
        return self.cache.get(key)
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in memory cache."""
        # Simple eviction if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
            self.delete(oldest_key)
        
        self.cache[key] = value
        self.timestamps[key] = datetime.now() + timedelta(seconds=ttl)
        return True
    
    def delete(self, key: str) -> bool:
        """Delete key from memory cache."""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)
        return True
    
    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        if key not in self.cache:
            return False
        
        if datetime.now() > self.timestamps[key]:
            self.delete(key)
            return False
        
        return True
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern (simple implementation)."""
        import fnmatch
        keys_to_delete = [
            key for key in self.cache.keys()
            if fnmatch.fnmatch(key, pattern)
        ]
        
        for key in keys_to_delete:
            self.delete(key)
        
        return len(keys_to_delete)


class CacheManager:
    """Main cache manager with multiple backends."""
    
    def __init__(self):
        self.backends = {}
        self._setup_backends()
    
    def _setup_backends(self):
        """Setup cache backends."""
        try:
            # Try Redis first
            self.backends['redis'] = RedisCache()
            self.primary_backend = 'redis'
            logger.info("Using Redis as primary cache backend")
        except Exception as e:
            logger.warning(f"Redis not available, falling back to memory cache: {str(e)}")
            self.backends['memory'] = MemoryCache()
            self.primary_backend = 'memory'
    
    @property
    def cache(self) -> CacheBackend:
        """Get primary cache backend."""
        return self.backends[self.primary_backend]
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return self.cache.get(key)
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache."""
        return self.cache.set(key, value, ttl)
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        return self.cache.delete(key)
    
    def clear_user_cache(self, user_id: int) -> int:
        """Clear all cache entries for a user."""
        pattern = f"user:{user_id}:*"
        return self.cache.clear_pattern(pattern)
    
    def clear_receipt_cache(self, user_id: int = None) -> int:
        """Clear receipt-related cache entries."""
        if user_id:
            pattern = f"receipts:user:{user_id}:*"
        else:
            pattern = "receipts:*"
        return self.cache.clear_pattern(pattern)


# Global cache manager
cache = CacheManager()


def cached(key_prefix: str, ttl: int = 300, user_specific: bool = True):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key
            cache_key_parts = [key_prefix]
            
            # Add user ID if user_specific
            if user_specific and args and hasattr(args[0], 'id'):
                cache_key_parts.append(f"user:{args[0].id}")
            
            # Add function arguments to key
            arg_str = "_".join(str(arg) for arg in args[1:] if arg is not None)
            kwarg_str = "_".join(f"{k}:{v}" for k, v in sorted(kwargs.items()) if v is not None)
            
            if arg_str:
                cache_key_parts.append(arg_str)
            if kwarg_str:
                cache_key_parts.append(kwarg_str)
            
            cache_key = ":".join(cache_key_parts)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator


def cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate cache key from prefix and arguments."""
    key_parts = [prefix]
    
    # Add positional arguments
    for arg in args:
        if arg is not None:
            key_parts.append(str(arg))
    
    # Add keyword arguments
    for key, value in sorted(kwargs.items()):
        if value is not None:
            key_parts.append(f"{key}:{value}")
    
    return ":".join(key_parts)


# Predefined cache TTLs
CACHE_TTL = {
    'user_profile': 300,      # 5 minutes
    'categories': 1800,       # 30 minutes
    'analytics': 600,         # 10 minutes
    'receipts_list': 60,      # 1 minute
    'transactions_list': 60,  # 1 minute
    'spending_summary': 300,  # 5 minutes
    'bank_accounts': 300,     # 5 minutes
}
