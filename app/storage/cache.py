"""Caching utilities for improving application performance."""
from __future__ import annotations

import functools
import hashlib
import threading
import time
from collections import OrderedDict
from datetime import datetime
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

T = TypeVar("T")


class CacheEntry:
    """A single cache entry with expiration tracking."""
    
    __slots__ = ("value", "expires_at", "created_at", "hits")
    
    def __init__(self, value: Any, ttl_seconds: float) -> None:
        """Create a cache entry.
        
        Args:
            value: The cached value
            ttl_seconds: Time-to-live in seconds (0 = never expires)
        """
        self.value = value
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl_seconds if ttl_seconds > 0 else float("inf")
        self.hits = 0
    
    def is_expired(self) -> bool:
        """Check if this entry has expired."""
        return time.time() > self.expires_at
    
    def time_remaining(self) -> float:
        """Get seconds until expiration (0 if expired)."""
        remaining = self.expires_at - time.time()
        return max(0, remaining)


class Cache:
    """Thread-safe in-memory cache with TTL support.
    
    Features:
    - Configurable time-to-live (TTL) for entries
    - Automatic cleanup of expired entries
    - Thread-safe operations
    - Optional maximum size limit
    - Statistics tracking
    
    Example:
        cache = Cache(ttl_seconds=300, max_size=1000)
        cache.set("key", "value")
        value = cache.get("key")  # Returns "value" if not expired
    """
    
    def __init__(
        self,
        ttl_seconds: float = 300,
        max_size: int = 0,
        cleanup_interval: float = 60
    ) -> None:
        """Initialize the cache.
        
        Args:
            ttl_seconds: Default TTL for entries (0 = never expires)
            max_size: Maximum number of entries (0 = unlimited)
            cleanup_interval: Seconds between automatic cleanup runs
        """
        self._data: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self.default_ttl = ttl_seconds
        self.max_size = max_size
        self._cleanup_interval = cleanup_interval
        self._last_cleanup = time.time()
        
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    def _maybe_cleanup(self) -> None:
        """Run cleanup if enough time has passed."""
        now = time.time()
        if now - self._last_cleanup > self._cleanup_interval:
            self._cleanup()
            self._last_cleanup = now
    
    def _cleanup(self) -> int:
        """Remove all expired entries. Returns count of removed entries."""
        removed = 0
        expired_keys = [k for k, v in self._data.items() if v.is_expired()]
        for key in expired_keys:
            del self._data[key]
            removed += 1
            self._evictions += 1
        return removed
    
    def _enforce_max_size(self) -> None:
        """Evict oldest entries if cache exceeds max_size."""
        if self.max_size <= 0:
            return
        
        while len(self._data) > self.max_size:
            oldest_key = min(
                self._data.keys(),
                key=lambda k: self._data[k].created_at
            )
            del self._data[oldest_key]
            self._evictions += 1
    
    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[float] = None
    ) -> None:
        """Store a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Optional custom TTL (uses default if not specified)
        """
        with self._lock:
            self._maybe_cleanup()
            ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
            self._data[key] = CacheEntry(value, ttl)
            self._enforce_max_size()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from the cache.
        
        Args:
            key: Cache key
            default: Value to return if key not found or expired
            
        Returns:
            Cached value or default
        """
        with self._lock:
            self._maybe_cleanup()
            entry = self._data.get(key)
            
            if entry is None:
                self._misses += 1
                return default
            
            if entry.is_expired():
                del self._data[key]
                self._misses += 1
                self._evictions += 1
                return default
            
            entry.hits += 1
            self._hits += 1
            return entry.value
    
    def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl_seconds: Optional[float] = None
    ) -> Any:
        """Get a value from cache, or compute and cache it if missing.
        
        Args:
            key: Cache key
            factory: Function to compute value if not cached
            ttl_seconds: Optional custom TTL
            
        Returns:
            Cached or newly computed value
        """
        value = self.get(key)
        if value is not None:
            return value
        
        value = factory()
        self.set(key, value, ttl_seconds)
        return value
    
    def delete(self, key: str) -> bool:
        """Remove a key from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was present and removed
        """
        with self._lock:
            if key in self._data:
                del self._data[key]
                return True
            return False
    
    def clear(self) -> int:
        """Remove all entries from the cache.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            count = len(self._data)
            self._data.clear()
            return count
    
    def has(self, key: str) -> bool:
        """Check if a key exists and is not expired.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists and is valid
        """
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return False
            if entry.is_expired():
                del self._data[key]
                return False
            return True
    
    def keys(self) -> List[str]:
        """Get all non-expired keys in the cache."""
        with self._lock:
            self._cleanup()
            return list(self._data.keys())
    
    def size(self) -> int:
        """Get the number of entries in the cache."""
        with self._lock:
            return len(self._data)
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "size": len(self._data),
                "max_size": self.max_size,
                "default_ttl": self.default_ttl,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate_percent": round(hit_rate, 2),
                "evictions": self._evictions,
            }
    
    def get_info(self, key: str) -> Optional[Dict[str, Any]]:
        """Get detailed info about a cached entry.
        
        Args:
            key: Cache key
            
        Returns:
            Entry info or None if not found
        """
        with self._lock:
            entry = self._data.get(key)
            if entry is None or entry.is_expired():
                return None
            
            return {
                "key": key,
                "created_at": datetime.fromtimestamp(entry.created_at),
                "expires_at": datetime.fromtimestamp(entry.expires_at) if entry.expires_at != float("inf") else None,
                "time_remaining_seconds": entry.time_remaining(),
                "hits": entry.hits,
            }


class LRUCache(Generic[T]):
    """Least Recently Used (LRU) cache with fixed size.
    
    When the cache is full, the least recently accessed item is evicted.
    Thread-safe implementation using OrderedDict.
    
    Example:
        cache = LRUCache[dict](max_size=100)
        cache.set("user:1", {"name": "Alice"})
        user = cache.get("user:1")
    """
    
    def __init__(self, max_size: int = 100) -> None:
        """Initialize the LRU cache.
        
        Args:
            max_size: Maximum number of entries
        """
        self._data: OrderedDict[str, T] = OrderedDict()
        self._lock = threading.RLock()
        self.max_size = max(1, max_size)
        
        self._hits = 0
        self._misses = 0
    
    def set(self, key: str, value: T) -> None:
        """Store a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            if key in self._data:
                del self._data[key]
            
            self._data[key] = value
            
            while len(self._data) > self.max_size:
                self._data.popitem(last=False)
    
    def get(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """Retrieve a value from the cache.
        
        Accessing a key moves it to the end (most recently used).
        
        Args:
            key: Cache key
            default: Value to return if key not found
            
        Returns:
            Cached value or default
        """
        with self._lock:
            if key not in self._data:
                self._misses += 1
                return default
            
            self._data.move_to_end(key)
            self._hits += 1
            return self._data[key]
    
    def delete(self, key: str) -> bool:
        """Remove a key from the cache."""
        with self._lock:
            if key in self._data:
                del self._data[key]
                return True
            return False
    
    def clear(self) -> None:
        """Remove all entries from the cache."""
        with self._lock:
            self._data.clear()
    
    def size(self) -> int:
        """Get the number of entries in the cache."""
        return len(self._data)
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        return {
            "size": len(self._data),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_percent": round(self._hits / total * 100, 2) if total > 0 else 0,
        }


def _make_cache_key(*args, **kwargs) -> str:
    """Create a cache key from function arguments."""
    key_parts = [repr(arg) for arg in args]
    key_parts.extend(f"{k}={repr(v)}" for k, v in sorted(kwargs.items()))
    key_str = ":".join(key_parts)
    
    # Hash long keys
    if len(key_str) > 200:
        return hashlib.md5(key_str.encode()).hexdigest()
    return key_str


def cached(
    ttl_seconds: float = 300,
    cache: Optional[Cache] = None,
    key_prefix: str = ""
) -> Callable:
    """Decorator to cache function results.
    
    Args:
        ttl_seconds: Time-to-live for cached results
        cache: Optional Cache instance (creates new one if not provided)
        key_prefix: Optional prefix for cache keys
        
    Example:
        @cached(ttl_seconds=60)
        def get_user(user_id: int) -> dict:
            return db.fetch_user(user_id)
    """
    _cache = cache or Cache(ttl_seconds=ttl_seconds)
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_key = f"{key_prefix}{func.__module__}.{func.__name__}"
            args_key = _make_cache_key(*args, **kwargs)
            full_key = f"{func_key}:{args_key}"
            
            result = _cache.get(full_key)
            if result is not None:
                return result
            
            result = func(*args, **kwargs)
            if result is not None:
                _cache.set(full_key, result, ttl_seconds)
            
            return result
        
        wrapper.cache = _cache
        wrapper.cache_clear = lambda: _cache.clear()
        wrapper.cache_stats = lambda: _cache.stats()
        
        return wrapper
    return decorator


def lru_cached(max_size: int = 100) -> Callable:
    """Decorator to cache function results using LRU eviction.
    
    Args:
        max_size: Maximum number of cached results
        
    Example:
        @lru_cached(max_size=50)
        def compute_expensive(x: int, y: int) -> int:
            return x ** y
    """
    _cache: LRUCache[Any] = LRUCache(max_size=max_size)
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = _make_cache_key(*args, **kwargs)
            
            result = _cache.get(cache_key)
            if result is not None:
                return result
            
            result = func(*args, **kwargs)
            if result is not None:
                _cache.set(cache_key, result)
            
            return result
        
        wrapper.cache = _cache
        wrapper.cache_clear = lambda: _cache.clear()
        wrapper.cache_stats = lambda: _cache.stats()
        
        return wrapper
    return decorator


class QueryCache:
    """Specialized cache for database query results.
    
    Provides convenient methods for caching query results with
    automatic key generation based on SQL and parameters.
    
    Example:
        query_cache = QueryCache(ttl_seconds=120)
        
        # Cache a query result
        result = query_cache.get_or_fetch(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
            fetcher=lambda: db.fetch_one(sql, params)
        )
    """
    
    def __init__(self, ttl_seconds: float = 120, max_size: int = 500) -> None:
        """Initialize the query cache.
        
        Args:
            ttl_seconds: Default TTL for cached queries
            max_size: Maximum number of cached queries
        """
        self._cache = Cache(ttl_seconds=ttl_seconds, max_size=max_size)
    
    def _make_query_key(self, sql: str, params: Optional[tuple] = None) -> str:
        """Create a cache key from SQL and parameters."""
        normalized_sql = " ".join(sql.split()).lower()
        key_str = normalized_sql
        if params:
            key_str += ":" + ":".join(repr(p) for p in params)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, sql: str, params: Optional[tuple] = None) -> Optional[Any]:
        """Get cached query result.
        
        Args:
            sql: SQL query
            params: Query parameters
            
        Returns:
            Cached result or None
        """
        key = self._make_query_key(sql, params)
        return self._cache.get(key)
    
    def set(
        self,
        sql: str,
        params: Optional[tuple],
        result: Any,
        ttl_seconds: Optional[float] = None
    ) -> None:
        """Cache a query result.
        
        Args:
            sql: SQL query
            params: Query parameters  
            result: Query result to cache
            ttl_seconds: Optional custom TTL
        """
        key = self._make_query_key(sql, params)
        self._cache.set(key, result, ttl_seconds)
    
    def get_or_fetch(
        self,
        sql: str,
        params: Optional[tuple],
        fetcher: Callable[[], Any],
        ttl_seconds: Optional[float] = None
    ) -> Any:
        """Get cached result or fetch and cache it.
        
        Args:
            sql: SQL query
            params: Query parameters
            fetcher: Function to execute query if not cached
            ttl_seconds: Optional custom TTL
            
        Returns:
            Cached or freshly fetched result
        """
        key = self._make_query_key(sql, params)
        return self._cache.get_or_set(key, fetcher, ttl_seconds)
    
    def invalidate(self, sql: str, params: Optional[tuple] = None) -> bool:
        """Remove a specific query from cache.
        
        Args:
            sql: SQL query
            params: Query parameters
            
        Returns:
            True if entry was removed
        """
        key = self._make_query_key(sql, params)
        return self._cache.delete(key)
    
    def invalidate_table(self, table_name: str) -> int:
        """Invalidate all cached queries for a table.
        
        This is a best-effort operation that clears queries
        mentioning the table name.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Number of entries cleared (approximate)
        """
        # For simplicity, we clear all cache when table changes
        # A more sophisticated approach would track table dependencies
        return self._cache.clear()
    
    def clear(self) -> int:
        """Clear all cached queries."""
        return self._cache.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self._cache.stats()


_default_cache: Optional[Cache] = None
_query_cache: Optional[QueryCache] = None


def get_default_cache() -> Cache:
    """Get the default application cache."""
    global _default_cache
    if _default_cache is None:
        _default_cache = Cache(ttl_seconds=300, max_size=1000)
    return _default_cache


def get_query_cache() -> QueryCache:
    """Get the default query cache."""
    global _query_cache
    if _query_cache is None:
        _query_cache = QueryCache(ttl_seconds=120, max_size=500)
    return _query_cache


__all__ = [
    "Cache",
    "CacheEntry",
    "LRUCache",
    "QueryCache",
    "cached",
    "lru_cached",
    "get_default_cache",
    "get_query_cache",
]
