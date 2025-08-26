"""
Habit management routes for BeaverHabits application.

Handles habit CRUD operations, habit tracking, and habit-related UI pages.
"""

import datetime
from typing import Optional

from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from nicegui import app, ui

from beaverhabits import views
from beaverhabits.app.crud import get_user_habits
from beaverhabits.app.db import User
from beaverhabits.app.dependencies import current_active_user
from beaverhabits.configs import settings
from beaverhabits.frontend.add_page import add_page_ui
from beaverhabits.frontend.cal_heatmap_page import heatmap_page
from beaverhabits.frontend.edit_page import edit_page_ui
from beaverhabits.frontend.habit_page import habit_page_ui
from beaverhabits.frontend.import_page import import_ui_page
from beaverhabits.frontend.index_page import index_page_ui
from beaverhabits.frontend.order_page import order_page_ui
from beaverhabits.logging import logger
from beaverhabits.services.i18n import t
from beaverhabits.utils import (
    get_display_days,
    get_user_today_date,
    is_navigating,
    reset_week_offset,
    set_navigating,
)
from .config import get_current_list_id


@ui.page("/")
async def root_redirect() -> None:
    """Redirects the root path '/' to '/gui'."""
    logger.info("Redirecting from / to /gui")
    ui.navigate.to('/gui')


@ui.page("/gui")
async def index_page(
    request: Request,
    user: User = Depends(current_active_user),
) -> None:
    """Main habit tracking page."""
    # Reset to current week only if not navigating
    if not is_navigating():
        reset_week_offset()
    else:
        set_navigating(False)  # Clear navigation flag
    days = await get_display_days()
    
    # Extract list parameter directly from request
    list_param = request.query_params.get("list")
    logger.info(f"Index page - List parameter from request: {list_param!r}")
    
    # Store list ID for persistence if it's a valid integer
    if list_param and list_param.isdigit():
        list_id = int(list_param)
        app.storage.user.update({"current_list": list_id})
    
    # Handle different list parameter types (case-insensitive)
    current_list_id = None
    if list_param and list_param.lower() == "none":
        # For "None" (no list), get all habits and filter to show only those with no list
        habits = await get_user_habits(user)
        habits = [h for h in habits if h.list_id is None]
        current_list_id = "None"
        logger.info(f"Index page - Showing {len(habits)} habits with no list")
    elif list_param and list_param.isdigit():
        # For specific list ID, filter at database level
        list_id = int(list_param)
        habits = await get_user_habits(user, list_id)
        current_list_id = list_id
        logger.info(f"Index page - Showing {len(habits)} habits from list {list_id}")
    else:
        # Default case (no filter) or invalid list parameter
        habits = await get_user_habits(user)
        logger.info(f"Index page - Showing all {len(habits)} habits")
    
    # Pass the current list ID to the UI
    await index_page_ui(days, habits, user, current_list_id)


@ui.page("/gui/add")
async def add_page(user: User = Depends(current_active_user)) -> None:
    """Add new habit page."""
    await add_page_ui(user)


@ui.page("/gui/edit")
async def edit_page(user: User = Depends(current_active_user)) -> None:
    """Edit habits page."""
    # Get all habits for editing
    habits = await get_user_habits(user)
    await edit_page_ui(habits, user)


@ui.page("/gui/order")
async def order_page(
    request: Request,
    user: User = Depends(current_active_user)
) -> None:
    """Reorder habits page."""
    # Extract list parameter directly from request
    list_param = request.query_params.get("list")
    logger.info(f"Order page - List parameter from request: {list_param!r}")
    
    # Store list ID for persistence if it's a valid integer
    if list_param and list_param.isdigit():
        list_id = int(list_param)
        app.storage.user.update({"current_list": list_id})
    
    # Handle different list parameter types (case-insensitive)
    current_list_id = None
    if list_param and list_param.lower() == "none":
        # For "None" (no list), get all habits and filter to show only those with no list
        habits = await get_user_habits(user)
        habits = [h for h in habits if h.list_id is None]
        current_list_id = "None"
        logger.info(f"Order page - Showing {len(habits)} habits with no list")
    elif list_param and list_param.isdigit():
        # For specific list ID, filter at database level
        list_id = int(list_param)
        habits = await get_user_habits(user, list_id)
        current_list_id = list_id
        logger.info(f"Order page - Showing {len(habits)} habits from list {list_id}")
    else:
        # Default case (no filter) or invalid list parameter
        habits = await get_user_habits(user)
        logger.info(f"Order page - Showing all {len(habits)} habits")
    
    # Pass the current list ID to the UI
    await order_page_ui(habits, user, current_list_id)


@ui.page("/gui/habits/{habit_id}")
async def habit_page(
    habit_id: str,
    user: User = Depends(current_active_user)
) -> Optional[RedirectResponse]:
    """Individual habit details page."""
    today = await get_user_today_date()
    habit = await views.get_user_habit(user, habit_id)
    if habit is None:
        ui.notify(t("habits.habit_not_found", habit_id=habit_id), color="negative")
        return RedirectResponse("/gui")
    await habit_page_ui(today, habit, user)


@ui.page("/gui/habits/{habit_id}/streak")
@ui.page("/gui/habits/{habit_id}/heatmap")
async def gui_habit_page_heatmap(
    habit_id: str,
    user: User = Depends(current_active_user)
) -> Optional[RedirectResponse]:
    """Habit heatmap/streak visualization page."""
    habit = await views.get_user_habit(user, habit_id)
    if habit is None:
        ui.notify(t("habits.habit_not_found", habit_id=habit_id), color="negative")
        return RedirectResponse("/gui")
    today = await get_user_today_date()
    await heatmap_page(today, habit, user)


@ui.page("/gui/export")
async def gui_export(user: User = Depends(current_active_user)) -> None:
    """Export habits data."""
    habits = await get_user_habits(user)
    if not habits:
        ui.notify(t("export.no_habits"), color="negative")
        return
    await views.export_user_habits(habits, user, user.email)


@ui.page("/gui/import")
async def gui_import(user: User = Depends(current_active_user)) -> None:
    """Import habits data page."""
    await import_ui_page(user)


# List of habit routes for registration
habit_routes = [
    root_redirect,
    index_page,
    add_page,
    edit_page,
    order_page,
    habit_page,
    gui_habit_page_heatmap,
    gui_export,
    gui_import,
]