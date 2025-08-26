"""
List management routes for BeaverHabits application.

Handles habit list creation, editing, and organization.
"""

from fastapi import Depends
from nicegui import ui

from beaverhabits.app.crud import get_user_lists
from beaverhabits.app.db import User
from beaverhabits.app.dependencies import current_active_user
from beaverhabits.frontend.lists_page import lists_page_ui


@ui.page("/gui/lists")
async def lists_page(user: User = Depends(current_active_user)) -> None:
    """Habit lists management page."""
    lists = await get_user_lists(user)
    await lists_page_ui(lists, user)


# List of list routes for registration
list_routes = [
    lists_page,
]