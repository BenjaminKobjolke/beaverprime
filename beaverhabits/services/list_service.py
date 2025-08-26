"""
List service layer for BeaverHabits application.

This service encapsulates business logic for habit list operations,
using the repository pattern for data access.
"""

from typing import List, Optional
from uuid import UUID

from beaverhabits.logging import logger
from beaverhabits.repositories.interfaces import IUnitOfWork
from beaverhabits.sql.models import HabitList, User


class ListService:
    """Service for habit list-related business operations."""
    
    def __init__(self, uow: IUnitOfWork):
        self._uow = uow
    
    async def get_list_by_id(self, list_id: int, user: User) -> Optional[HabitList]:
        """
        Get a list by ID, ensuring it belongs to the user.
        
        Args:
            list_id: The list ID
            user: The user requesting the list
            
        Returns:
            The list if found and belongs to user, None otherwise
        """
        habit_list = await self._uow.lists.get_by_id(list_id)
        if habit_list and habit_list.user_id == user.id:
            return habit_list
        return None
    
    async def get_user_lists(self, user: User) -> List[HabitList]:
        """
        Get all lists for a user.
        
        Args:
            user: The user
            
        Returns:
            List of habit lists
        """
        return await self._uow.lists.get_user_lists(user)
    
    async def create_list(self, user: User, name: str, order: int = 0) -> HabitList:
        """
        Create a new habit list with business validation.
        
        Args:
            user: The user creating the list
            name: The list name
            order: Display order (default 0)
            
        Returns:
            The created list
            
        Raises:
            ValueError: If validation fails
        """
        # Validate input
        if not name or not name.strip():
            raise ValueError("List name cannot be empty")
        
        # Check for duplicate names (business rule)
        existing_lists = await self.get_user_lists(user)
        existing_names = {lst.name.lower() for lst in existing_lists}
        
        if name.strip().lower() in existing_names:
            raise ValueError("A list with this name already exists")
        
        habit_list = await self._uow.lists.create(
            user=user,
            name=name.strip(),
            order=order
        )
        
        await self._uow.commit()
        logger.info(f"[ListService] Created list '{name}' for user {user.id}")
        return habit_list
    
    async def update_list(self, list_id: int, user: User, **updates) -> Optional[HabitList]:
        """
        Update a list with business validation.
        
        Args:
            list_id: The list ID
            user: The user updating the list
            **updates: Fields to update
            
        Returns:
            The updated list if successful, None if not found
            
        Raises:
            ValueError: If validation fails
        """
        # Validate name if provided
        if 'name' in updates and updates['name'] is not None:
            if not updates['name'] or not updates['name'].strip():
                raise ValueError("List name cannot be empty")
            
            # Check for duplicate names (excluding current list)
            existing_lists = await self.get_user_lists(user)
            existing_names = {
                lst.name.lower() for lst in existing_lists 
                if lst.id != list_id
            }
            
            if updates['name'].strip().lower() in existing_names:
                raise ValueError("A list with this name already exists")
            
            updates['name'] = updates['name'].strip()
        
        habit_list = await self._uow.lists.update(list_id, user.id, **updates)
        if habit_list:
            await self._uow.commit()
            logger.info(f"[ListService] Updated list {list_id} for user {user.id}")
        
        return habit_list
    
    async def delete_list(self, list_id: int, user: User) -> bool:
        """
        Delete a list (mark as deleted) and all its habits.
        
        Args:
            list_id: The list ID
            user: The user deleting the list
            
        Returns:
            True if deleted successfully, False if not found
        """
        success = await self._uow.lists.delete(list_id, user.id)
        if success:
            await self._uow.commit()
            logger.info(f"[ListService] Deleted list {list_id} and its habits for user {user.id}")
        
        return success
    
    async def reorder_lists(self, user: User, list_orders: dict[int, int]) -> None:
        """
        Reorder multiple lists.
        
        Args:
            user: The user
            list_orders: Dictionary mapping list_id to new order
        """
        for list_id, new_order in list_orders.items():
            await self._uow.lists.update(list_id, user.id, order=new_order)
        
        await self._uow.commit()
        logger.info(f"[ListService] Reordered {len(list_orders)} lists for user {user.id}")
    
    async def get_list_stats(self, list_id: int, user: User) -> dict:
        """
        Get statistics for a list.
        
        Args:
            list_id: The list ID
            user: The user
            
        Returns:
            Dictionary with list statistics
        """
        habit_list = await self.get_list_by_id(list_id, user)
        if not habit_list:
            return {"total_habits": 0, "active_habits": 0}
        
        # Get habits in this list
        habits = await self._uow.habits.get_user_habits(user, list_id)
        active_habits = [h for h in habits if not h.deleted]
        
        return {
            "total_habits": len(habits),
            "active_habits": len(active_habits),
            "list_name": habit_list.name,
            "enable_letter_filter": habit_list.enable_letter_filter
        }
    
    async def delete_all_user_lists(self, user: User) -> None:
        """
        Delete all lists for a user.
        
        Args:
            user: The user
        """
        await self._uow.lists.delete_all_user_lists(user)
        await self._uow.commit()
        logger.info(f"[ListService] Deleted all lists for user {user.id}")
    
    async def toggle_letter_filter(self, list_id: int, user: User, enable: bool) -> Optional[HabitList]:
        """
        Toggle letter filter for a list.
        
        Args:
            list_id: The list ID
            user: The user
            enable: Whether to enable letter filter
            
        Returns:
            The updated list if successful, None if not found
        """
        return await self.update_list(list_id, user, enable_letter_filter=enable)