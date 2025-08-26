"""
Repository interfaces for the BeaverHabits application.

These abstract base classes define the contracts for data access operations,
enabling dependency inversion and making the system more testable and flexible.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional
from uuid import UUID

from beaverhabits.sql.models import Habit, HabitList, CheckedRecord, User


class IHabitRepository(ABC):
    """Interface for habit data access operations."""
    
    @abstractmethod
    async def get_by_id(self, habit_id: int) -> Optional[Habit]:
        """Get a habit by its ID."""
        pass
    
    @abstractmethod
    async def get_user_habits(self, user: User, list_id: Optional[int] = None) -> List[Habit]:
        """Get all habits for a user, optionally filtered by list ID."""
        pass
    
    @abstractmethod
    async def create(self, user: User, name: str, weekly_goal: int = 1, 
                    priority: int = 0, list_id: Optional[int] = None) -> Habit:
        """Create a new habit."""
        pass
    
    @abstractmethod
    async def update(self, habit_id: int, user_id: UUID, **kwargs) -> Optional[Habit]:
        """Update a habit."""
        pass
    
    @abstractmethod
    async def delete(self, habit_id: int, user_id: UUID) -> bool:
        """Delete a habit."""
        pass
    
    @abstractmethod
    async def get_checks(self, habit: Habit, start_date: date, end_date: date) -> List[CheckedRecord]:
        """Get habit completion records for a date range."""
        pass
    
    @abstractmethod
    async def add_check(self, habit: Habit, check_date: date, note: Optional[str] = None) -> CheckedRecord:
        """Add a completion record for a habit."""
        pass
    
    @abstractmethod
    async def remove_check(self, habit: Habit, check_date: date) -> bool:
        """Remove a completion record for a habit."""
        pass
    
    @abstractmethod
    async def delete_all_user_habits(self, user: User) -> None:
        """Delete all habits for a user."""
        pass


class IListRepository(ABC):
    """Interface for habit list data access operations."""
    
    @abstractmethod
    async def get_by_id(self, list_id: int) -> Optional[HabitList]:
        """Get a list by its ID."""
        pass
    
    @abstractmethod
    async def get_user_lists(self, user: User) -> List[HabitList]:
        """Get all lists for a user."""
        pass
    
    @abstractmethod
    async def create(self, user: User, name: str, order: int = 0) -> HabitList:
        """Create a new list."""
        pass
    
    @abstractmethod
    async def update(self, list_id: int, user_id: UUID, name: Optional[str] = None, 
                    order: Optional[int] = None, deleted: bool = False,
                    enable_letter_filter: Optional[bool] = None) -> Optional[HabitList]:
        """Update a list."""
        pass
    
    @abstractmethod
    async def delete(self, list_id: int, user_id: UUID) -> bool:
        """Delete a list."""
        pass
    
    @abstractmethod
    async def delete_all_user_lists(self, user: User) -> None:
        """Delete all lists for a user."""
        pass


class IUserRepository(ABC):
    """Interface for user data access operations."""
    
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get a user by ID."""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        pass
    
    @abstractmethod
    async def get_count(self) -> int:
        """Get total user count."""
        pass
    
    @abstractmethod
    async def create(self, email: str, hashed_password: str, **kwargs) -> User:
        """Create a new user."""
        pass
    
    @abstractmethod
    async def update(self, user_id: UUID, **kwargs) -> Optional[User]:
        """Update a user."""
        pass


class IUnitOfWork(ABC):
    """Interface for managing database transactions and repositories."""
    
    habits: IHabitRepository
    lists: IListRepository
    users: IUserRepository
    
    @abstractmethod
    async def __aenter__(self):
        """Enter the async context manager."""
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context manager."""
        pass
    
    @abstractmethod
    async def commit(self):
        """Commit the current transaction."""
        pass
    
    @abstractmethod
    async def rollback(self):
        """Rollback the current transaction."""
        pass