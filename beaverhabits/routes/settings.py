"""
Settings routes for BeaverHabits application.

Handles user settings, preferences, and data management.
"""

from fastapi import Depends
from nicegui import ui

from beaverhabits.app.db import User
from beaverhabits.app.dependencies import current_active_user
from beaverhabits.app.users import UserManager, get_user_manager
from beaverhabits.frontend.settings_page import settings_page_ui


@ui.page("/gui/settings", title="Settings")
async def show_settings_page(
    user: User = Depends(current_active_user),
    user_manager: UserManager = Depends(get_user_manager)
):
    """Settings page."""
    await settings_page_ui(user=user, user_manager=user_manager)


# List of settings routes for registration
settings_routes = [
    show_settings_page,
]