"""
Habit service layer for BeaverHabits application.

This service encapsulates business logic for habit operations,
using the repository pattern for data access.
"""

from datetime import date
from typing import List, Optional
from uuid import UUID

from beaverhabits.logging import logger
from beaverhabits.repositories.interfaces import IUnitOfWork
from beaverhabits.sql.models import Habit, CheckedRecord, User


class HabitService:
    """Service for habit-related business operations."""
    
    def __init__(self, uow: IUnitOfWork):
        self._uow = uow
    
    async def get_habit_by_id(self, habit_id: int, user: User) -> Optional[Habit]:
        """
        Get a habit by ID, ensuring it belongs to the user.
        
        Args:
            habit_id: The habit ID
            user: The user requesting the habit
            
        Returns:
            The habit if found and belongs to user, None otherwise
        """
        habit = await self._uow.habits.get_by_id(habit_id)
        if habit and habit.user_id == user.id:
            return habit
        return None
    
    async def get_user_habits(self, user: User, list_id: Optional[int] = None) -> List[Habit]:
        """
        Get all habits for a user, optionally filtered by list.
        
        Args:
            user: The user
            list_id: Optional list ID to filter by
            
        Returns:
            List of habits
        """
        return await self._uow.habits.get_user_habits(user, list_id)
    
    async def create_habit(self, user: User, name: str, weekly_goal: int = 1, 
                          priority: int = 0, list_id: Optional[int] = None) -> Habit:
        """
        Create a new habit with business validation.
        
        Args:
            user: The user creating the habit
            name: The habit name
            weekly_goal: Weekly goal (default 1)
            priority: Priority/order (default 0)
            list_id: Optional list to assign to
            
        Returns:
            The created habit
            
        Raises:
            ValueError: If validation fails
        """
        # Validate input
        if not name or not name.strip():
            raise ValueError("Habit name cannot be empty")
        
        if weekly_goal < 1:
            raise ValueError("Weekly goal must be at least 1")
        
        # Validate list exists if provided
        if list_id is not None:
            habit_list = await self._uow.lists.get_by_id(list_id)
            if not habit_list or habit_list.user_id != user.id:
                raise ValueError(f"List {list_id} not found or does not belong to user")
        
        habit = await self._uow.habits.create(
            user=user,
            name=name.strip(),
            weekly_goal=weekly_goal,
            priority=priority,
            list_id=list_id
        )
        
        await self._uow.commit()
        logger.info(f"[HabitService] Created habit '{name}' for user {user.id}")
        return habit
    
    async def update_habit(self, habit_id: int, user: User, **updates) -> Optional[Habit]:
        """
        Update a habit with business validation.
        
        Args:
            habit_id: The habit ID
            user: The user updating the habit
            **updates: Fields to update
            
        Returns:
            The updated habit if successful, None if not found
            
        Raises:
            ValueError: If validation fails
        """
        # Validate name if provided
        if 'name' in updates and updates['name'] is not None:
            if not updates['name'] or not updates['name'].strip():
                raise ValueError("Habit name cannot be empty")
            updates['name'] = updates['name'].strip()
        
        # Validate weekly_goal if provided
        if 'weekly_goal' in updates and updates['weekly_goal'] is not None:
            if updates['weekly_goal'] < 1:
                raise ValueError("Weekly goal must be at least 1")
        
        # Validate list_id if provided
        if 'list_id' in updates and updates['list_id'] is not None:
            habit_list = await self._uow.lists.get_by_id(updates['list_id'])
            if not habit_list or habit_list.user_id != user.id:
                raise ValueError(f"List {updates['list_id']} not found or does not belong to user")
        
        habit = await self._uow.habits.update(habit_id, user.id, **updates)
        if habit:
            await self._uow.commit()
            logger.info(f"[HabitService] Updated habit {habit_id} for user {user.id}")
        
        return habit
    
    async def delete_habit(self, habit_id: int, user: User) -> bool:
        """
        Delete a habit (mark as deleted).
        
        Args:
            habit_id: The habit ID
            user: The user deleting the habit
            
        Returns:
            True if deleted successfully, False if not found
        """
        success = await self._uow.habits.delete(habit_id, user.id)
        if success:
            await self._uow.commit()
            logger.info(f"[HabitService] Deleted habit {habit_id} for user {user.id}")
        
        return success
    
    async def toggle_habit_check(self, habit_id: int, user: User, check_date: date, 
                                value: Optional[bool] = None, note: Optional[str] = None) -> Optional[CheckedRecord]:
        """
        Toggle a habit check for a specific date.
        
        Args:
            habit_id: The habit ID
            user: The user
            check_date: The date to check/uncheck
            value: True for checked, False for skipped, None to remove
            note: Optional note
            
        Returns:
            The check record if created/updated, None if removed
        """
        # Verify habit belongs to user
        habit = await self.get_habit_by_id(habit_id, user)
        if not habit:
            raise ValueError("Habit not found or does not belong to user")
        
        if value is None:
            # Remove check
            success = await self._uow.habits.remove_check(habit, check_date)
            if success:
                await self._uow.commit()
                logger.info(f"[HabitService] Removed check for habit {habit_id} on {check_date}")
            return None
        else:
            # Add/update check
            record = await self._uow.habits.add_check(habit, check_date, note)
            # Update the done status if different
            if record.done != value:
                record.done = value
            
            await self._uow.commit()
            logger.info(f"[HabitService] Set check for habit {habit_id} on {check_date} to {value}")
            return record
    
    async def get_habit_checks(self, habit_id: int, user: User, 
                              start_date: Optional[date] = None, 
                              end_date: Optional[date] = None) -> List[CheckedRecord]:
        """
        Get habit completion records for a date range.
        
        Args:
            habit_id: The habit ID
            user: The user
            start_date: Start date (optional)
            end_date: End date (optional)
            
        Returns:
            List of check records
        """
        habit = await self.get_habit_by_id(habit_id, user)
        if not habit:
            return []
        
        # Use reasonable defaults if dates not provided
        if start_date is None:
            from datetime import timedelta
            start_date = date.today() - timedelta(days=365)  # Last year
        
        if end_date is None:
            end_date = date.today()
        
        return await self._uow.habits.get_checks(habit, start_date, end_date)
    
    async def delete_all_user_habits(self, user: User) -> None:
        """
        Delete all habits for a user.
        
        Args:
            user: The user
        """
        await self._uow.habits.delete_all_user_habits(user)
        await self._uow.commit()
        logger.info(f"[HabitService] Deleted all habits for user {user.id}")
    
    async def get_habit_streak_stats(self, habit_id: int, user: User) -> dict:
        """
        Calculate streak statistics for a habit.
        
        Args:
            habit_id: The habit ID
            user: The user
            
        Returns:
            Dictionary with streak stats
        """
        from datetime import timedelta
        
        habit = await self.get_habit_by_id(habit_id, user)
        if not habit:
            return {"current_streak": 0, "longest_streak": 0, "total_completions": 0}
        
        # Get checks for the last year
        end_date = date.today()
        start_date = end_date - timedelta(days=365)
        
        checks = await self.get_habit_checks(habit_id, user, start_date, end_date)
        
        # Convert to set of completed dates for easy lookup
        completed_dates = {check.day for check in checks if check.done}
        
        # Calculate current streak
        current_streak = 0
        check_date = end_date
        while check_date in completed_dates:
            current_streak += 1
            check_date -= timedelta(days=1)
        
        # Calculate longest streak
        longest_streak = 0
        temp_streak = 0
        check_date = start_date
        
        while check_date <= end_date:
            if check_date in completed_dates:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 0
            check_date += timedelta(days=1)
        
        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "total_completions": len(completed_dates)
        }