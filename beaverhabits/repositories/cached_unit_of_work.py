"""
Cached Unit of Work implementation for BeaverHabits.

Provides query result caching within the Unit of Work context to avoid
duplicate database queries within the same request/transaction.
"""

import contextlib
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from beaverhabits.app.db import get_async_session
from beaverhabits.logging import logger
from beaverhabits.repositories.interfaces import IUnitOfWork, IHabitRepository, IListRepository, IUserRepository
from beaverhabits.repositories.sqlalchemy_repositories import (
    SQLAlchemyHabitRepository, SQLAlchemyListRepository, SQLAlchemyUserRepository
)


class CachedHabitRepository(SQLAlchemyHabitRepository):
    """Habit repository with query result caching."""
    
    def __init__(self, session: AsyncSession, cache: Dict[str, Any]):
        super().__init__(session)
        self._cache = cache
    
    def _cache_key(self, operation: str, *args) -> str:
        """Generate cache key for operation and arguments."""
        return f"habit_{operation}:{':'.join(str(arg) for arg in args)}"
    
    async def get_by_id(self, habit_id: int):
        """Get habit by ID with caching."""
        cache_key = self._cache_key("get_by_id", habit_id)
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = await super().get_by_id(habit_id)
        self._cache[cache_key] = result
        return result
    
    async def get_user_habits(self, user, list_id=None):
        """Get user habits with caching."""
        cache_key = self._cache_key("get_user_habits", user.id, list_id)
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = await super().get_user_habits(user, list_id)
        self._cache[cache_key] = result
        return result
    
    async def get_user_habits_with_recent_checks(self, user, days=30, list_id=None):
        """Get user habits with recent checks, with caching."""
        cache_key = self._cache_key("get_user_habits_with_recent_checks", user.id, days, list_id)
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = await super().get_user_habits_with_recent_checks(user, days, list_id)
        self._cache[cache_key] = result
        return result
    
    async def get_bulk_checks(self, habits, start_date, end_date):
        """Get bulk checks with caching."""
        habit_ids = tuple(sorted(habit.id for habit in habits))
        cache_key = self._cache_key("get_bulk_checks", habit_ids, start_date, end_date)
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = await super().get_bulk_checks(habits, start_date, end_date)
        self._cache[cache_key] = result
        return result
    
    async def update(self, habit_id, user_id, **kwargs):
        """Update habit and invalidate related cache entries."""
        result = await super().update(habit_id, user_id, **kwargs)
        
        if result:
            # Invalidate cache entries related to this habit
            keys_to_remove = [
                key for key in self._cache.keys()
                if f"habit_" in key and (str(habit_id) in key or str(user_id) in key)
            ]
            
            for key in keys_to_remove:
                del self._cache[key]
            
            logger.debug(f"[Cache] Invalidated {len(keys_to_remove)} cache entries after habit update")
        
        return result
    
    async def create(self, user, name, weekly_goal=1, priority=0, list_id=None):
        """Create habit and invalidate related cache entries."""
        result = await super().create(user, name, weekly_goal, priority, list_id)
        
        if result:
            # Invalidate user habit queries
            keys_to_remove = [
                key for key in self._cache.keys()
                if f"get_user_habits" in key and str(user.id) in key
            ]
            
            for key in keys_to_remove:
                del self._cache[key]
        
        return result


class CachedListRepository(SQLAlchemyListRepository):
    """List repository with query result caching."""
    
    def __init__(self, session: AsyncSession, cache: Dict[str, Any]):
        super().__init__(session)
        self._cache = cache
    
    def _cache_key(self, operation: str, *args) -> str:
        """Generate cache key for operation and arguments."""
        return f"list_{operation}:{':'.join(str(arg) for arg in args)}"
    
    async def get_by_id(self, list_id: int):
        """Get list by ID with caching."""
        cache_key = self._cache_key("get_by_id", list_id)
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = await super().get_by_id(list_id)
        self._cache[cache_key] = result
        return result
    
    async def get_user_lists(self, user):
        """Get user lists with caching."""
        cache_key = self._cache_key("get_user_lists", user.id)
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = await super().get_user_lists(user)
        self._cache[cache_key] = result
        return result
    
    async def update(self, list_id, user_id, **kwargs):
        """Update list and invalidate related cache entries."""
        result = await super().update(list_id, user_id, **kwargs)
        
        if result:
            # Invalidate cache entries related to this list
            keys_to_remove = [
                key for key in self._cache.keys()
                if f"list_" in key and (str(list_id) in key or str(user_id) in key)
            ]
            
            for key in keys_to_remove:
                del self._cache[key]
        
        return result


class CachedUserRepository(SQLAlchemyUserRepository):
    """User repository with query result caching."""
    
    def __init__(self, session: AsyncSession, cache: Dict[str, Any]):
        super().__init__(session)
        self._cache = cache
    
    def _cache_key(self, operation: str, *args) -> str:
        """Generate cache key for operation and arguments."""
        return f"user_{operation}:{':'.join(str(arg) for arg in args)}"
    
    async def get_by_id(self, user_id):
        """Get user by ID with caching."""
        cache_key = self._cache_key("get_by_id", user_id)
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = await super().get_by_id(user_id)
        self._cache[cache_key] = result
        return result
    
    async def get_by_email(self, email):
        """Get user by email with caching."""
        cache_key = self._cache_key("get_by_email", email)
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = await super().get_by_email(email)
        self._cache[cache_key] = result
        return result


class CachedSQLAlchemyUnitOfWork(IUnitOfWork):
    """SQLAlchemy Unit of Work with query result caching."""
    
    def __init__(self):
        self._session: Optional[AsyncSession] = None
        self._session_context_manager = None
        self._cache: Dict[str, Any] = {}
        self.habits: Optional[IHabitRepository] = None
        self.lists: Optional[IListRepository] = None
        self.users: Optional[IUserRepository] = None
    
    async def __aenter__(self):
        """Enter the async context manager."""
        # Create a new context manager instance
        self._session_context_manager = contextlib.asynccontextmanager(get_async_session)()
        self._session = await self._session_context_manager.__aenter__()
        
        # Initialize cached repositories with the session and shared cache
        self.habits = CachedHabitRepository(self._session, self._cache)
        self.lists = CachedListRepository(self._session, self._cache)
        self.users = CachedUserRepository(self._session, self._cache)
        
        logger.debug("[CachedUoW] Started cached unit of work session")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context manager."""
        cache_size = len(self._cache)
        
        if self._session_context_manager:
            await self._session_context_manager.__aexit__(exc_type, exc_val, exc_tb)
        
        # Clean up repository references and cache
        self.habits = None
        self.lists = None
        self.users = None
        self._session = None
        self._session_context_manager = None
        self._cache.clear()
        
        if cache_size > 0:
            logger.debug(f"[CachedUoW] Completed session with {cache_size} cached queries")
    
    async def commit(self):
        """Commit the current transaction."""
        if self._session:
            await self._session.commit()
            # Clear cache after commit since data may have changed
            cache_size = len(self._cache)
            self._cache.clear()
            logger.debug(f"[CachedUoW] Committed transaction, cleared {cache_size} cache entries")
    
    async def rollback(self):
        """Rollback the current transaction."""
        if self._session:
            await self._session.rollback()
            # Clear cache after rollback
            cache_size = len(self._cache)
            self._cache.clear()
            logger.debug(f"[CachedUoW] Rolled back transaction, cleared {cache_size} cache entries")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get statistics about the current cache."""
        return {
            'total_entries': len(self._cache),
            'habit_queries': len([k for k in self._cache.keys() if k.startswith('habit_')]),
            'list_queries': len([k for k in self._cache.keys() if k.startswith('list_')]),
            'user_queries': len([k for k in self._cache.keys() if k.startswith('user_')])
        }