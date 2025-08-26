"""
SQLAlchemy implementations of repository interfaces.

These classes provide concrete implementations of the repository interfaces
using SQLAlchemy for data persistence operations.
"""

import contextlib
from datetime import date, timedelta
from typing import List, Optional, Dict
from uuid import UUID

from sqlalchemy import select, update, and_, or_
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from beaverhabits.logging import logger
from beaverhabits.sql.models import Habit, HabitList, CheckedRecord, User
from beaverhabits.app.db import get_async_session
from .interfaces import IHabitRepository, IListRepository, IUserRepository, IUnitOfWork


class SQLAlchemyHabitRepository(IHabitRepository):
    """SQLAlchemy implementation of habit repository."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def get_by_id(self, habit_id: int) -> Optional[Habit]:
        """Get a habit by its ID."""
        stmt = select(Habit).where(Habit.id == habit_id, Habit.deleted == False)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_habits(self, user: User, list_id: Optional[int] = None) -> List[Habit]:
        """Get all habits for a user, optionally filtered by list ID."""
        stmt = select(Habit).options(
            joinedload(Habit.checked_records)
        ).where(
            Habit.user_id == user.id,
            Habit.deleted == False
        )
        
        if list_id:
            stmt = stmt.join(HabitList).where(
                Habit.list_id == list_id,
                HabitList.deleted == False
            )
        
        stmt = stmt.order_by(Habit.order)
        result = await self._session.execute(stmt)
        return list(result.unique().scalars())
    
    async def create(self, user: User, name: str, weekly_goal: int = 1, 
                    priority: int = 0, list_id: Optional[int] = None) -> Habit:
        """Create a new habit."""
        # Verify list belongs to user if list_id is provided
        if list_id is not None:
            stmt = select(HabitList).where(
                HabitList.id == list_id, 
                HabitList.user_id == user.id,
                HabitList.deleted == False
            )
            result = await self._session.execute(stmt)
            habit_list = result.scalar_one_or_none()
            
            if not habit_list:
                raise ValueError(f"List {list_id} not found for user {user.id}")
        
        habit = Habit(
            name=name, 
            weekly_goal=weekly_goal,
            order=priority, 
            list_id=list_id, 
            user_id=user.id
        )
        self._session.add(habit)
        await self._session.flush()  # Get the ID without committing
        await self._session.refresh(habit)
        logger.info(f"[Repository] Created habit {habit.id} for user {user.id}")
        return habit
    
    async def update(self, habit_id: int, user_id: UUID, **kwargs) -> Optional[Habit]:
        """Update a habit."""
        stmt = select(Habit).where(Habit.id == habit_id, Habit.user_id == user_id)
        result = await self._session.execute(stmt)
        habit = result.scalar_one_or_none()
        
        if not habit:
            return None
        
        # Handle list_id validation if provided
        if 'list_id' in kwargs and kwargs['list_id'] is not None:
            list_stmt = select(HabitList).where(
                HabitList.id == kwargs['list_id'], 
                HabitList.user_id == user_id,
                HabitList.deleted == False
            )
            list_result = await self._session.execute(list_stmt)
            if not list_result.scalar_one_or_none():
                raise ValueError(f"List {kwargs['list_id']} not found for user {user_id}")
        
        # Update allowed fields
        allowed_fields = ['name', 'order', 'list_id', 'weekly_goal', 'deleted', 'star']
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(habit, field, value)
        
        await self._session.flush()
        await self._session.refresh(habit)
        logger.info(f"[Repository] Updated habit {habit_id}")
        return habit
    
    async def delete(self, habit_id: int, user_id: UUID) -> bool:
        """Delete a habit (mark as deleted)."""
        return await self.update(habit_id, user_id, deleted=True) is not None
    
    async def get_checks(self, habit: Habit, start_date: date, end_date: date) -> List[CheckedRecord]:
        """Get habit completion records for a date range."""
        stmt = select(CheckedRecord).where(
            CheckedRecord.habit_id == habit.id,
            CheckedRecord.day >= start_date,
            CheckedRecord.day <= end_date
        )
        result = await self._session.execute(stmt)
        return list(result.scalars())
    
    async def add_check(self, habit: Habit, check_date: date, note: Optional[str] = None) -> CheckedRecord:
        """Add a completion record for a habit."""
        # Check if record already exists
        stmt = select(CheckedRecord).where(
            CheckedRecord.habit_id == habit.id,
            CheckedRecord.day == check_date
        )
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.done = True
            if note is not None:
                existing.text = note
            record = existing
        else:
            record = CheckedRecord(
                habit_id=habit.id, 
                day=check_date, 
                done=True, 
                text=note
            )
            self._session.add(record)
        
        await self._session.flush()
        await self._session.refresh(record)
        logger.info(f"[Repository] Added check for habit {habit.id} on {check_date}")
        return record
    
    async def remove_check(self, habit: Habit, check_date: date) -> bool:
        """Remove a completion record for a habit."""
        stmt = select(CheckedRecord).where(
            CheckedRecord.habit_id == habit.id,
            CheckedRecord.day == check_date
        )
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        
        if record:
            await self._session.delete(record)
            await self._session.flush()
            logger.info(f"[Repository] Removed check for habit {habit.id} on {check_date}")
            return True
        return False
    
    async def delete_all_user_habits(self, user: User) -> None:
        """Delete all habits for a user."""
        stmt = update(Habit).where(
            Habit.user_id == user.id,
            Habit.deleted == False
        ).values(deleted=True)
        
        result = await self._session.execute(stmt)
        await self._session.flush()
        count = result.rowcount
        logger.info(f"[Repository] Marked {count} habits as deleted for user {user.id}")
    
    async def get_bulk_checks(self, habits: List[Habit], start_date: date, end_date: date) -> Dict[int, List[CheckedRecord]]:
        """Get completion records for multiple habits in a single query."""
        if not habits:
            return {}
        
        habit_ids = [habit.id for habit in habits]
        stmt = select(CheckedRecord).where(
            and_(
                CheckedRecord.habit_id.in_(habit_ids),
                CheckedRecord.day >= start_date,
                CheckedRecord.day <= end_date
            )
        ).order_by(CheckedRecord.habit_id, CheckedRecord.day)
        
        result = await self._session.execute(stmt)
        records = result.scalars().all()
        
        # Group records by habit_id
        bulk_checks = {}
        for record in records:
            if record.habit_id not in bulk_checks:
                bulk_checks[record.habit_id] = []
            bulk_checks[record.habit_id].append(record)
        
        # Ensure all habit IDs have an entry (even if empty)
        for habit_id in habit_ids:
            if habit_id not in bulk_checks:
                bulk_checks[habit_id] = []
        
        logger.info(f"[Repository] Bulk loaded checks for {len(habit_ids)} habits, {len(records)} total records")
        return bulk_checks
    
    async def get_user_habits_with_recent_checks(self, user: User, days: int = 30, list_id: Optional[int] = None) -> List[Habit]:
        """Get user habits with their recent completion records pre-loaded."""
        # Calculate date range for recent checks
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Build base query with optimized eager loading
        stmt = select(Habit).options(
            # Load only recent checked records to reduce memory usage
            selectinload(Habit.checked_records).where(
                and_(
                    CheckedRecord.day >= start_date,
                    CheckedRecord.day <= end_date
                )
            )
        ).where(
            Habit.user_id == user.id,
            Habit.deleted == False
        )
        
        # Add list filtering if specified
        if list_id is not None:
            stmt = stmt.where(Habit.list_id == list_id)
        
        stmt = stmt.order_by(Habit.order)
        result = await self._session.execute(stmt)
        habits = list(result.unique().scalars())
        
        logger.info(f"[Repository] Loaded {len(habits)} habits with {days} days of recent checks")
        return habits


class SQLAlchemyListRepository(IListRepository):
    """SQLAlchemy implementation of list repository."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def get_by_id(self, list_id: int) -> Optional[HabitList]:
        """Get a list by its ID."""
        stmt = select(HabitList).where(HabitList.id == list_id, HabitList.deleted == False)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_lists(self, user: User) -> List[HabitList]:
        """Get all lists for a user."""
        stmt = select(HabitList).where(
            HabitList.user_id == user.id,
            HabitList.deleted == False
        ).order_by(HabitList.order)
        result = await self._session.execute(stmt)
        return list(result.scalars())
    
    async def create(self, user: User, name: str, order: int = 0) -> HabitList:
        """Create a new list."""
        habit_list = HabitList(name=name, order=order, user_id=user.id)
        self._session.add(habit_list)
        await self._session.flush()
        await self._session.refresh(habit_list)
        logger.info(f"[Repository] Created list {habit_list.id} for user {user.id}")
        return habit_list
    
    async def update(self, list_id: int, user_id: UUID, name: Optional[str] = None, 
                    order: Optional[int] = None, deleted: bool = False,
                    enable_letter_filter: Optional[bool] = None) -> Optional[HabitList]:
        """Update a list."""
        stmt = select(HabitList).where(HabitList.id == list_id, HabitList.user_id == user_id)
        result = await self._session.execute(stmt)
        habit_list = result.scalar_one_or_none()
        
        if not habit_list:
            return None
        
        if name is not None:
            habit_list.name = name
        if order is not None:
            habit_list.order = order
        if enable_letter_filter is not None:
            habit_list.enable_letter_filter = enable_letter_filter
        
        if deleted:
            # Mark list as deleted and also mark all habits in this list as deleted
            habit_list.deleted = True
            
            habit_stmt = select(Habit).where(
                Habit.list_id == list_id,
                Habit.user_id == user_id
            )
            habit_result = await self._session.execute(habit_stmt)
            habits = habit_result.scalars()
            for habit in habits:
                habit.deleted = True
        
        await self._session.flush()
        await self._session.refresh(habit_list)
        logger.info(f"[Repository] Updated list {list_id}")
        return habit_list
    
    async def delete(self, list_id: int, user_id: UUID) -> bool:
        """Delete a list (mark as deleted)."""
        return await self.update(list_id, user_id, deleted=True) is not None
    
    async def delete_all_user_lists(self, user: User) -> None:
        """Delete all lists for a user."""
        stmt = update(HabitList).where(
            HabitList.user_id == user.id,
            HabitList.deleted == False
        ).values(deleted=True)
        
        result = await self._session.execute(stmt)
        await self._session.flush()
        count = result.rowcount
        logger.info(f"[Repository] Marked {count} lists as deleted for user {user.id}")


class SQLAlchemyUserRepository(IUserRepository):
    """SQLAlchemy implementation of user repository."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get a user by ID."""
        stmt = select(User).where(User.id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_count(self) -> int:
        """Get total user count."""
        stmt = select(User)
        result = await self._session.execute(stmt)
        return len(result.all())
    
    async def create(self, email: str, hashed_password: str, **kwargs) -> User:
        """Create a new user."""
        user = User(email=email, hashed_password=hashed_password, **kwargs)
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        logger.info(f"[Repository] Created user {user.id}")
        return user
    
    async def update(self, user_id: UUID, **kwargs) -> Optional[User]:
        """Update a user."""
        stmt = select(User).where(User.id == user_id)
        result = await self._session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        for field, value in kwargs.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        await self._session.flush()
        await self._session.refresh(user)
        logger.info(f"[Repository] Updated user {user_id}")
        return user


class SQLAlchemyUnitOfWork(IUnitOfWork):
    """SQLAlchemy implementation of Unit of Work pattern."""
    
    def __init__(self):
        self._session: Optional[AsyncSession] = None
        self._session_context_manager = None
        self.habits: Optional[IHabitRepository] = None
        self.lists: Optional[IListRepository] = None
        self.users: Optional[IUserRepository] = None
    
    async def __aenter__(self):
        """Enter the async context manager."""
        # Create a new context manager instance
        self._session_context_manager = contextlib.asynccontextmanager(get_async_session)()
        self._session = await self._session_context_manager.__aenter__()
        
        # Initialize repositories with the session
        self.habits = SQLAlchemyHabitRepository(self._session)
        self.lists = SQLAlchemyListRepository(self._session)
        self.users = SQLAlchemyUserRepository(self._session)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context manager."""
        if self._session_context_manager:
            await self._session_context_manager.__aexit__(exc_type, exc_val, exc_tb)
        
        # Clean up repository references
        self.habits = None
        self.lists = None
        self.users = None
        self._session = None
        self._session_context_manager = None
    
    async def commit(self):
        """Commit the current transaction."""
        if self._session:
            await self._session.commit()
    
    async def rollback(self):
        """Rollback the current transaction."""
        if self._session:
            await self._session.rollback()