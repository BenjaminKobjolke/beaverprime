import datetime
import json
from typing import List as TypeList, Optional

from nicegui import app, ui

from beaverhabits.logging import logger
from beaverhabits.app.auth import user_create
from beaverhabits.app.db import User
from beaverhabits.configs import settings
from beaverhabits.repositories import SQLAlchemyUnitOfWork
from beaverhabits.sql.models import Habit, HabitList
from beaverhabits.utils import generate_short_hash


async def get_user_habit(user: User, habit_id: str) -> Optional[Habit]:
    """Get a specific habit for a user."""
    from beaverhabits.services.habit_service import HabitService
    
    async with SQLAlchemyUnitOfWork() as uow:
        habit_service = HabitService(uow)
        try:
            habit_id_int = int(habit_id)
            return await habit_service.get_habit_by_id(habit_id_int, user)
        except ValueError:
            return None


async def add_list(user: User, name: str) -> HabitList:
    """Add a new list for a user."""
    from beaverhabits.services.list_service import ListService
    
    async with SQLAlchemyUnitOfWork() as uow:
        list_service = ListService(uow)
        return await list_service.create_list(user, name)


async def update_list(user: User, list_id: int, name: str) -> None:
    """Update a list's name."""
    from beaverhabits.services.list_service import ListService
    
    async with SQLAlchemyUnitOfWork() as uow:
        list_service = ListService(uow)
        await list_service.update_list(list_id, user, name=name)


async def delete_list(user: User, list_id: int) -> None:
    """Delete a list and unassign its habits."""
    from beaverhabits.services.list_service import ListService
    
    async with SQLAlchemyUnitOfWork() as uow:
        list_service = ListService(uow)
        await list_service.delete_list(list_id, user)


async def is_gui_authenticated() -> bool:
    """Check if user is authenticated with a valid token."""
    token = app.storage.user.get("auth_token")
    if not token:
        return False
    
    from beaverhabits.services.auth_service import AuthService
    async with SQLAlchemyUnitOfWork() as uow:
        auth_service = AuthService(uow)
        return await auth_service.validate_token(token)


async def validate_max_user_count() -> None:
    """Validate max user count."""
    from beaverhabits.services.auth_service import AuthService
    
    async with SQLAlchemyUnitOfWork() as uow:
        auth_service = AuthService(uow)
        user_count = await auth_service.get_user_count()
        if user_count >= settings.MAX_USER_COUNT > 0:
            raise ValueError("Maximum number of users reached")


async def register_user(email: str, password: str = "") -> User:
    """Register a new user."""
    try:
        logger.info(f"Attempting to register user with email: {email}")
        user = await user_create(email=email, password=password)
        if not user:
            logger.error(f"Registration failed for email: {email} - User creation returned None")
            raise ValueError("Failed to register user - Creation failed")
        logger.info(f"Successfully registered user with email: {email}")
        return user
    except Exception as e:
        logger.exception(f"Registration failed for email: {email}")
        raise ValueError(f"Failed to register user: {str(e)}")


async def login_user(user: User) -> None:
    """Login a user."""
    # Fallback to direct token creation for existing authenticated user
    from beaverhabits.app.auth import user_create_token
    token = await user_create_token(user)
    if not token:
        raise ValueError("Failed to login user")
    app.storage.user.update({"auth_token": token})


async def export_user_habits(habits: TypeList[Habit], user: User, filename: str) -> None:
    """Export user habits."""
    from beaverhabits.services.habit_service import HabitService
    from beaverhabits.services.list_service import ListService
    
    async with SQLAlchemyUnitOfWork() as uow:
        habit_service = HabitService(uow)
        list_service = ListService(uow)
        
        # Convert habits to JSON-friendly format
        data = {
            "habits": [],
            "lists": []
        }
        
        # Add habits with their records
        for habit in habits:
            # Get all records for this habit
            records = await habit_service.get_habit_checks(habit.id, user)
            habit_data = {
                "id": habit.id,
                "name": habit.name,
                "order": habit.order,
                "weekly_goal": habit.weekly_goal,
                "list_id": habit.list_id,
                "records": [
                    {
                        "day": record.day.isoformat(),
                        "done": record.done,
                        "text": record.text
                    }
                    for record in records
                ]
            }
            data["habits"].append(habit_data)
        
        # Add lists
        lists = await list_service.get_user_lists(user)
        data["lists"] = [
            {
                "id": habit_list.id,
                "name": habit_list.name,
                "order": habit_list.order
            }
            for habit_list in lists
        ]
        
        # Create JSON content and trigger download
        json_content = json.dumps(data, indent=2)
        ui.download(bytes(json_content, encoding='utf-8'), f"{filename}.json")
