"""
Cache service for BeaverHabits application.

Provides in-memory caching for frequently calculated values
to improve performance of expensive operations.
"""

import asyncio
from datetime import date, datetime, timedelta
from typing import Dict, Optional, Any, Tuple
from uuid import UUID

from beaverhabits.logging import logger


class CacheService:
    """In-memory cache service for performance optimization."""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default TTL
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        self._default_ttl = default_ttl
        self._lock = asyncio.Lock()
    
    def _is_expired(self, timestamp: datetime, ttl: int) -> bool:
        """Check if a cache entry is expired."""
        return datetime.now() > timestamp + timedelta(seconds=ttl)
    
    def _generate_key(self, prefix: str, *args) -> str:
        """Generate a cache key from prefix and arguments."""
        key_parts = [str(arg) for arg in args]
        return f"{prefix}:{':'.join(key_parts)}"
    
    async def get(self, key: str, ttl: Optional[int] = None) -> Optional[Any]:
        """Get a value from cache."""
        if ttl is None:
            ttl = self._default_ttl
        
        async with self._lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                if not self._is_expired(timestamp, ttl):
                    return value
                else:
                    # Clean up expired entry
                    del self._cache[key]
        
        return None
    
    async def set(self, key: str, value: Any) -> None:
        """Set a value in cache."""
        async with self._lock:
            self._cache[key] = (value, datetime.now())
    
    async def delete(self, key: str) -> None:
        """Delete a value from cache."""
        async with self._lock:
            self._cache.pop(key, None)
    
    async def clear_user_cache(self, user_id: UUID) -> None:
        """Clear all cache entries for a specific user."""
        user_prefix = str(user_id)
        async with self._lock:
            keys_to_delete = [
                key for key in self._cache.keys() 
                if key.split(':')[1] == user_prefix if ':' in key
            ]
            for key in keys_to_delete:
                del self._cache[key]
        
        if keys_to_delete:
            logger.info(f"[Cache] Cleared {len(keys_to_delete)} entries for user {user_id}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        async with self._lock:
            total_entries = len(self._cache)
            expired_count = 0
            
            now = datetime.now()
            for _, timestamp in self._cache.values():
                if self._is_expired(timestamp, self._default_ttl):
                    expired_count += 1
            
            return {
                "total_entries": total_entries,
                "expired_entries": expired_count,
                "active_entries": total_entries - expired_count
            }
    
    async def cleanup_expired(self) -> int:
        """Remove expired entries from cache."""
        async with self._lock:
            expired_keys = []
            now = datetime.now()
            
            for key, (_, timestamp) in self._cache.items():
                if self._is_expired(timestamp, self._default_ttl):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.info(f"[Cache] Cleaned up {len(expired_keys)} expired entries")
            
            return len(expired_keys)


class HabitCalculationCache(CacheService):
    """Specialized cache for habit calculations."""
    
    def __init__(self):
        super().__init__(default_ttl=600)  # 10 minutes for calculations
    
    async def get_consecutive_weeks(self, habit_id: int, user_id: UUID, today: date) -> Optional[int]:
        """Get cached consecutive weeks count."""
        key = self._generate_key("consecutive_weeks", user_id, habit_id, today)
        return await self.get(key)
    
    async def set_consecutive_weeks(self, habit_id: int, user_id: UUID, today: date, count: int) -> None:
        """Cache consecutive weeks count."""
        key = self._generate_key("consecutive_weeks", user_id, habit_id, today)
        await self.set(key, count)
    
    async def get_week_completion(self, habit_id: int, user_id: UUID, week_start: date) -> Optional[Tuple[int, int]]:
        """Get cached week completion (ticks, goal)."""
        key = self._generate_key("week_completion", user_id, habit_id, week_start)
        return await self.get(key)
    
    async def set_week_completion(self, habit_id: int, user_id: UUID, week_start: date, ticks: int, goal: int) -> None:
        """Cache week completion."""
        key = self._generate_key("week_completion", user_id, habit_id, week_start)
        await self.set(key, (ticks, goal))
    
    async def get_habit_stats(self, habit_id: int, user_id: UUID) -> Optional[Dict[str, int]]:
        """Get cached habit statistics."""
        key = self._generate_key("habit_stats", user_id, habit_id)
        return await self.get(key)
    
    async def set_habit_stats(self, habit_id: int, user_id: UUID, stats: Dict[str, int]) -> None:
        """Cache habit statistics."""
        key = self._generate_key("habit_stats", user_id, habit_id)
        await self.set(key, stats)
    
    async def invalidate_habit_cache(self, habit_id: int, user_id: UUID) -> None:
        """Invalidate all cache entries for a specific habit."""
        # Get all keys that match this habit
        habit_pattern = f"{user_id}:{habit_id}"
        async with self._lock:
            keys_to_delete = [
                key for key in self._cache.keys()
                if habit_pattern in key
            ]
            for key in keys_to_delete:
                del self._cache[key]
        
        if keys_to_delete:
            logger.info(f"[Cache] Invalidated {len(keys_to_delete)} entries for habit {habit_id}")


# Global cache instances
habit_calculation_cache = HabitCalculationCache()
general_cache = CacheService()


# Background task to clean up expired cache entries
async def cache_cleanup_task():
    """Background task to periodically clean up expired cache entries."""
    while True:
        try:
            await asyncio.sleep(300)  # Run every 5 minutes
            await habit_calculation_cache.cleanup_expired()
            await general_cache.cleanup_expired()
        except Exception as e:
            logger.error(f"[Cache] Cleanup task error: {e}")


# Start the cleanup task when the module is imported
_cleanup_task = None

def start_cache_cleanup():
    """Start the cache cleanup background task."""
    global _cleanup_task
    if _cleanup_task is None:
        _cleanup_task = asyncio.create_task(cache_cleanup_task())

def stop_cache_cleanup():
    """Stop the cache cleanup background task."""
    global _cleanup_task
    if _cleanup_task:
        _cleanup_task.cancel()
        _cleanup_task = None