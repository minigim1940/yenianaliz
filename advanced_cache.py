"""
Phase 8.G: Performance Optimization - Advanced Caching Strategy
Multi-layer caching, cache warming, invalidation strategies
"""

import time
import hashlib
import json
import pickle
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta
from collections import OrderedDict
from pathlib import Path
import sqlite3

class CacheLayer:
    """Base cache layer interface"""
    
    def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError
    
    def set(self, key: str, value: Any, ttl: int = 300):
        raise NotImplementedError
    
    def delete(self, key: str):
        raise NotImplementedError
    
    def clear(self):
        raise NotImplementedError


class MemoryCache(CacheLayer):
    """In-memory LRU cache with TTL"""
    
    def __init__(self, max_size: int = 1000):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.stats = {"hits": 0, "misses": 0, "evictions": 0}
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            entry = self.cache[key]
            # Check expiration
            if entry['expires_at'] > datetime.now():
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.stats['hits'] += 1
                return entry['value']
            else:
                # Expired
                del self.cache[key]
        
        self.stats['misses'] += 1
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        # Check size limit
        if len(self.cache) >= self.max_size and key not in self.cache:
            # Evict oldest
            self.cache.popitem(last=False)
            self.stats['evictions'] += 1
        
        self.cache[key] = {
            'value': value,
            'expires_at': datetime.now() + timedelta(seconds=ttl),
            'created_at': datetime.now()
        }
        self.cache.move_to_end(key)
    
    def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        self.cache.clear()
    
    def get_stats(self) -> Dict:
        total = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total * 100) if total > 0 else 0
        
        return {
            "type": "memory",
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.stats['hits'],
            "misses": self.stats['misses'],
            "evictions": self.stats['evictions'],
            "hit_rate": round(hit_rate, 2)
        }


class DiskCache(CacheLayer):
    """Persistent disk-based cache"""
    
    def __init__(self, db_path: str = "disk_cache.db"):
        self.db_path = Path(db_path)
        self.ensure_table()
        self.stats = {"hits": 0, "misses": 0}
    
    def ensure_table(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    cache_key TEXT PRIMARY KEY,
                    value BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_expires ON cache_entries(expires_at)")
            conn.commit()
    
    def get(self, key: str) -> Optional[Any]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                result = conn.execute("""
                    SELECT value FROM cache_entries
                    WHERE cache_key = ? AND expires_at > ?
                """, (key, datetime.now())).fetchone()
                
                if result:
                    self.stats['hits'] += 1
                    return pickle.loads(result[0])
                
                self.stats['misses'] += 1
                return None
        except Exception:
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        try:
            expires_at = datetime.now() + timedelta(seconds=ttl)
            pickled_value = pickle.dumps(value)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO cache_entries
                    (cache_key, value, expires_at)
                    VALUES (?, ?, ?)
                """, (key, pickled_value, expires_at))
                conn.commit()
        except Exception as e:
            print(f"Disk cache set error: {e}")
    
    def delete(self, key: str):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM cache_entries WHERE cache_key = ?", (key,))
                conn.commit()
        except Exception:
            pass
    
    def clear(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM cache_entries")
                conn.commit()
        except Exception:
            pass
    
    def cleanup_expired(self):
        """Remove expired entries"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                result = conn.execute("""
                    DELETE FROM cache_entries WHERE expires_at < ?
                """, (datetime.now(),))
                conn.commit()
                return result.rowcount
        except Exception:
            return 0
    
    def get_stats(self) -> Dict:
        try:
            with sqlite3.connect(self.db_path) as conn:
                total_entries = conn.execute("SELECT COUNT(*) FROM cache_entries").fetchone()[0]
                expired = conn.execute(
                    "SELECT COUNT(*) FROM cache_entries WHERE expires_at < ?",
                    (datetime.now(),)
                ).fetchone()[0]
                
                total = self.stats['hits'] + self.stats['misses']
                hit_rate = (self.stats['hits'] / total * 100) if total > 0 else 0
                
                return {
                    "type": "disk",
                    "total_entries": total_entries,
                    "expired_entries": expired,
                    "hits": self.stats['hits'],
                    "misses": self.stats['misses'],
                    "hit_rate": round(hit_rate, 2)
                }
        except Exception:
            return {"type": "disk", "error": "Stats unavailable"}


class MultiLayerCache:
    """Multi-layer cache with fallback strategy"""
    
    def __init__(
        self,
        memory_max_size: int = 1000,
        disk_db_path: str = "disk_cache.db"
    ):
        self.l1_cache = MemoryCache(max_size=memory_max_size)
        self.l2_cache = DiskCache(db_path=disk_db_path)
        self.warmup_functions = {}  # Functions to warm cache
        self.invalidation_patterns = {}  # Pattern-based invalidation
    
    def get(self, key: str) -> Optional[Any]:
        """Get from cache with L1 -> L2 fallback"""
        # Try L1 (memory)
        value = self.l1_cache.get(key)
        if value is not None:
            return value
        
        # Try L2 (disk)
        value = self.l2_cache.get(key)
        if value is not None:
            # Promote to L1
            self.l1_cache.set(key, value)
            return value
        
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300, persist: bool = True):
        """Set value in cache layers"""
        # Always set in L1
        self.l1_cache.set(key, value, ttl)
        
        # Optionally persist to L2
        if persist:
            self.l2_cache.set(key, value, ttl)
    
    def delete(self, key: str):
        """Delete from all layers"""
        self.l1_cache.delete(key)
        self.l2_cache.delete(key)
    
    def clear(self):
        """Clear all layers"""
        self.l1_cache.clear()
        self.l2_cache.clear()
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        # For memory cache
        keys_to_delete = [k for k in self.l1_cache.cache.keys() if pattern in k]
        for key in keys_to_delete:
            self.l1_cache.delete(key)
        
        # For disk cache - would need pattern matching in SQL
        # Simplified: clear all if pattern is '*'
        if pattern == '*':
            self.clear()
    
    def register_warmup(self, cache_key: str, func: Callable):
        """Register function to warm up cache"""
        self.warmup_functions[cache_key] = func
    
    def warmup(self, cache_key: Optional[str] = None):
        """Warm up cache by pre-loading data"""
        if cache_key:
            # Warm specific key
            if cache_key in self.warmup_functions:
                func = self.warmup_functions[cache_key]
                value = func()
                self.set(cache_key, value, persist=True)
                return 1
            return 0
        else:
            # Warm all registered keys
            count = 0
            for key, func in self.warmup_functions.items():
                try:
                    value = func()
                    self.set(key, value, persist=True)
                    count += 1
                except Exception as e:
                    print(f"Warmup error for {key}: {e}")
            return count
    
    def get_or_compute(
        self,
        key: str,
        compute_func: Callable,
        ttl: int = 300,
        persist: bool = True
    ) -> Any:
        """Get from cache or compute if not present"""
        value = self.get(key)
        if value is not None:
            return value
        
        # Compute
        value = compute_func()
        self.set(key, value, ttl, persist)
        return value
    
    def cleanup(self):
        """Cleanup expired entries"""
        return self.l2_cache.cleanup_expired()
    
    def get_stats(self) -> Dict:
        """Get combined cache statistics"""
        l1_stats = self.l1_cache.get_stats()
        l2_stats = self.l2_cache.get_stats()
        
        total_hits = l1_stats['hits'] + l2_stats['hits']
        total_misses = l1_stats['misses'] + l2_stats['misses']
        total = total_hits + total_misses
        overall_hit_rate = (total_hits / total * 100) if total > 0 else 0
        
        return {
            "l1_memory": l1_stats,
            "l2_disk": l2_stats,
            "overall": {
                "total_hits": total_hits,
                "total_misses": total_misses,
                "hit_rate": round(overall_hit_rate, 2)
            },
            "warmup_functions": len(self.warmup_functions)
        }


class CacheInvalidator:
    """Cache invalidation strategies"""
    
    @staticmethod
    def time_based(cache: MultiLayerCache, key: str, interval_seconds: int):
        """Time-based invalidation"""
        # Set with TTL
        # This is handled automatically by TTL in cache layers
        pass
    
    @staticmethod
    def event_based(cache: MultiLayerCache, event_type: str, affected_keys: List[str]):
        """Event-based invalidation"""
        for key in affected_keys:
            cache.delete(key)
    
    @staticmethod
    def tag_based(cache: MultiLayerCache, tag: str):
        """Tag-based invalidation"""
        cache.invalidate_pattern(f"*{tag}*")
    
    @staticmethod
    def dependency_based(
        cache: MultiLayerCache,
        primary_key: str,
        dependent_keys: List[str]
    ):
        """Dependency-based invalidation"""
        cache.delete(primary_key)
        for dep_key in dependent_keys:
            cache.delete(dep_key)


def cache_key_generator(*args, **kwargs) -> str:
    """Generate cache key from function arguments"""
    key_data = f"{args}:{sorted(kwargs.items())}"
    return hashlib.md5(key_data.encode()).hexdigest()


def cached(ttl: int = 300, persist: bool = True):
    """Decorator for caching function results"""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            # Get or create cache instance
            if not hasattr(wrapper, '_cache'):
                wrapper._cache = MultiLayerCache()
            
            # Generate cache key
            cache_key = f"{func.__name__}:{cache_key_generator(*args, **kwargs)}"
            
            # Try cache first
            result = wrapper._cache.get(cache_key)
            if result is not None:
                return result
            
            # Compute and cache
            result = func(*args, **kwargs)
            wrapper._cache.set(cache_key, result, ttl, persist)
            return result
        
        return wrapper
    return decorator


# Test code
if __name__ == "__main__":
    print("🚀 Testing Advanced Caching System...")
    
    cache = MultiLayerCache(memory_max_size=100)
    
    # Test basic operations
    print("\n📝 Testing basic operations...")
    cache.set("key1", {"data": "value1"}, ttl=60)
    result = cache.get("key1")
    print(f"   Get key1: {result}")
    
    # Test L1 -> L2 promotion
    print("\n🔄 Testing cache promotion...")
    cache.l1_cache.clear()  # Clear L1
    result = cache.get("key1")  # Should get from L2 and promote to L1
    print(f"   Get after L1 clear: {result}")
    print(f"   L1 size: {len(cache.l1_cache.cache)}")
    
    # Test get_or_compute
    print("\n⚙️ Testing get_or_compute...")
    def expensive_computation():
        time.sleep(0.1)
        return {"result": "computed"}
    
    start = time.time()
    result1 = cache.get_or_compute("computed_key", expensive_computation)
    time1 = time.time() - start
    
    start = time.time()
    result2 = cache.get_or_compute("computed_key", expensive_computation)
    time2 = time.time() - start
    
    print(f"   First call: {time1:.3f}s")
    print(f"   Cached call: {time2:.3f}s")
    if time2 > 0:
        print(f"   Speedup: {time1/time2:.1f}x")
    else:
        print(f"   Speedup: Very fast (cached)")
    
    # Test cache warming
    print("\n🔥 Testing cache warmup...")
    def warmup_function():
        return {"warmed": "data"}
    
    cache.register_warmup("warm_key", warmup_function)
    warmed = cache.warmup()
    print(f"   Warmed {warmed} keys")
    print(f"   Retrieved: {cache.get('warm_key')}")
    
    # Test statistics
    print("\n📊 Cache Statistics:")
    stats = cache.get_stats()
    print(f"   L1 Hit Rate: {stats['l1_memory']['hit_rate']}%")
    print(f"   L2 Hit Rate: {stats['l2_disk']['hit_rate']}%")
    print(f"   Overall Hit Rate: {stats['overall']['hit_rate']}%")
    print(f"   L1 Size: {stats['l1_memory']['size']}/{stats['l1_memory']['max_size']}")
    print(f"   L2 Entries: {stats['l2_disk'].get('total_entries', 0)}")
    
    # Test decorator
    print("\n🎨 Testing @cached decorator...")
    @cached(ttl=30)
    def slow_function(x):
        time.sleep(0.05)
        return x * 2
    
    start = time.time()
    result1 = slow_function(10)
    time1 = time.time() - start
    
    start = time.time()
    result2 = slow_function(10)
    time2 = time.time() - start
    
    print(f"   First: {time1:.3f}s, Cached: {time2:.3f}s")
    print(f"   Result: {result1}")
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    expired = cache.cleanup()
    print(f"   Removed {expired} expired entries")
    
    print("\n✅ Advanced Caching test complete!")
