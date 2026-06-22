# models/database/cache.py
"""
Query caching system for frequently accessed data.
"""

import hashlib
import json
from datetime import datetime, timedelta
from collections import OrderedDict
from loguru import logger

class QueryCache:
    """LRU cache for database queries."""
    
    def __init__(self, max_size=100, ttl_seconds=300):
        self.max_size = max_size
        self.ttl = timedelta(seconds=ttl_seconds)
        self._cache = OrderedDict()
        self._hits = 0
        self._misses = 0
    
    def get(self, key):
        """Get cached result."""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if datetime.now() - timestamp < self.ttl:
                self._cache.move_to_end(key)
                self._hits += 1
                return data
            else:
                del self._cache[key]
        self._misses += 1
        return None
    
    def set(self, key, value):
        """Cache a result."""
        if len(self._cache) >= self.max_size:
            # Remove oldest
            self._cache.popitem(last=False)
        self._cache[key] = (value, datetime.now())
    
    def clear(self):
        """Clear all cache."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
    
    def get_stats(self):
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': f"{hit_rate:.1f}%"
        }


# Global cache instance
_query_cache = QueryCache(max_size=100, ttl_seconds=300)


def cache_key(prefix, *args, **kwargs):
    """Generate cache key from query parameters."""
    key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
    return hashlib.md5(key_data.encode()).hexdigest()


def cached_query(ttl_seconds=300):
    """Decorator for caching query results."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = cache_key(func.__name__, *args, **kwargs)
            
            # Try to get from cache
            result = _query_cache.get(key)
            if result is not None:
                return result
            
            # Execute query
            result = func(*args, **kwargs)
            
            # Cache result
            if result is not None:
                _query_cache.set(key, result)
            
            return result
        return wrapper
    return decorator