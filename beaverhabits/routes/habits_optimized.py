"""
Performance-optimized habit routes for BeaverHabits application.

This module demonstrates how to use the performance optimization features
including bulk queries, caching, and monitoring.
"""

import datetime
from typing import Optional

from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from nicegui import app, ui

from beaverhabits import views
from beaverhabits.app.db import User
from beaverhabits.app.dependencies import current_active_user
from beaverhabits.configs import settings
from beaverhabits.frontend.components.index.habit.utils_optimized import (
    get_habits_with_performance_data,
    preload_habit_data_for_week,
    get_user_dashboard_summary
)
from beaverhabits.frontend.index_page import index_page_ui
from beaverhabits.logging import logger
from beaverhabits.repositories import CachedSQLAlchemyUnitOfWork
from beaverhabits.services import PerformanceService
from beaverhabits.services.monitoring_service import performance_monitor
from beaverhabits.services.i18n import t
from beaverhabits.utils import (
    get_display_days,
    get_user_today_date,
    is_navigating,
    reset_week_offset,
    set_navigating,
)
from .config import get_current_list_id


@ui.page("/gui-optimized")
async def optimized_index_page(
    request: Request,
    user: User = Depends(current_active_user),
) -> None:
    """
    Performance-optimized version of the main habit tracking page.
    
    This version demonstrates the performance improvements:
    - Uses bulk queries to reduce database round trips
    - Implements caching for calculated values  
    - Includes performance monitoring
    - Pre-loads all data needed for UI rendering
    """
    
    # Track endpoint performance
    async with performance_monitor.track_endpoint("/gui-optimized", "GET", user.id) as endpoint_info:
        try:
            # Reset to current week only if not navigating
            if not is_navigating():
                reset_week_offset()
            else:
                set_navigating(False)  # Clear navigation flag
            
            days = await get_display_days()
            today = await get_user_today_date()
            
            # Extract list parameter directly from request
            list_param = request.query_params.get("list")
            logger.info(f"Optimized Index page - List parameter from request: {list_param!r}")
            
            # Store list ID for persistence if it's a valid integer
            if list_param and list_param.isdigit():
                list_id = int(list_param)
                app.storage.user.update({"current_list": list_id})
            
            # Determine list filter
            current_list_id = None
            if list_param and list_param.lower() == "none":
                current_list_id = "None"
            elif list_param and list_param.isdigit():
                current_list_id = int(list_param)
            
            # Use cached UoW for better performance
            async with CachedSQLAlchemyUnitOfWork() as uow:
                
                # Track the bulk query performance
                async with performance_monitor.track_query("get_habits_with_performance_data", user.id) as query_info:
                    # Get all habits with performance data in one optimized query
                    habits_data = await get_habits_with_performance_data(
                        user, list_id=current_list_id, today=today
                    )
                    query_info['record_count'] = len(habits_data)
                    query_info['cache_hit'] = len(habits_data) > 0 and hasattr(uow, 'get_cache_stats')
                
                # Get cache statistics for monitoring
                if hasattr(uow, 'get_cache_stats'):
                    cache_stats = uow.get_cache_stats()
                    endpoint_info['cache_hits'] = cache_stats.get('total_entries', 0)
                
                endpoint_info['query_count'] = 1  # Single bulk query instead of N+1
            
            # Convert habits_data back to the format expected by the existing UI
            habits = [data['habit'] for data in habits_data]
            
            # Add performance metrics to the UI data for debugging (optional)
            if settings.DEBUG:
                performance_summary = await performance_monitor.get_performance_summary(hours=1)
                logger.info(f"[Optimized] Performance summary: {performance_summary}")
            
            # Pass the current list ID to the UI (existing interface)
            await index_page_ui(days, habits, user, current_list_id)
            
            logger.info(f"Optimized Index page - Loaded {len(habits)} habits with performance data")
            
        except Exception as e:
            endpoint_info['status_code'] = 500
            logger.error(f"[Optimized] Error in index page: {e}")
            raise


@ui.page("/gui-dashboard")
async def performance_dashboard_page(
    user: User = Depends(current_active_user),
) -> None:
    """
    Performance dashboard showing user metrics and system performance.
    
    This demonstrates advanced performance features like dashboard summaries
    and performance monitoring.
    """
    
    async with performance_monitor.track_endpoint("/gui-dashboard", "GET", user.id) as endpoint_info:
        try:
            # Get user performance summary
            async with performance_monitor.track_query("get_user_dashboard_summary", user.id) as query_info:
                dashboard_data = await get_user_dashboard_summary(user, days=30)
                query_info['record_count'] = dashboard_data.get('total_habits', 0)
            
            # Get system performance metrics
            system_performance = await performance_monitor.get_performance_summary(hours=24)
            user_performance = await performance_monitor.get_user_performance(user.id, hours=24)
            
            endpoint_info['query_count'] = 1
            
            # Simple dashboard UI
            with ui.column().classes("w-full max-w-4xl mx-auto p-4"):
                ui.label("Performance Dashboard").classes("text-2xl font-bold mb-4")
                
                # User metrics section
                with ui.card().classes("w-full mb-4"):
                    ui.label("Your Habit Performance").classes("text-lg font-semibold")
                    
                    with ui.row().classes("w-full"):
                        with ui.column():
                            ui.label(f"Total Habits: {dashboard_data['total_habits']}")
                            ui.label(f"Completion Rate: {dashboard_data['completion_rate_display']}")
                            ui.label(f"Total Completions: {dashboard_data['total_completions']}")
                        
                        with ui.column():
                            ui.label(f"Average Streak: {dashboard_data['average_streak']} days")
                            ui.label(f"Goals Met: {dashboard_data['habits_meeting_goals']} habits")
                            ui.label(f"Most Consistent: {dashboard_data.get('most_consistent_habit', 'N/A')}")
                    
                    ui.label(dashboard_data['performance_message']).classes("mt-2 text-sm italic")
                
                # System performance section (for debugging/admin)
                if settings.DEBUG:
                    with ui.card().classes("w-full mb-4"):
                        ui.label("System Performance (24h)").classes("text-lg font-semibold")
                        
                        query_stats = system_performance['query_stats']
                        ui.label(f"Total Queries: {query_stats['total_queries']}")
                        ui.label(f"Avg Query Time: {query_stats['avg_duration_ms']}ms")
                        ui.label(f"Cache Hit Rate: {query_stats['cache_hit_rate_percent']}%")
                        
                        if query_stats['top_slow_queries']:
                            ui.label("Slow Queries:").classes("font-semibold mt-2")
                            for slow_query in query_stats['top_slow_queries'][:3]:
                                ui.label(f"• {slow_query['query_type']}: {slow_query['max_duration_ms']}ms ({slow_query['count']}x)")
                
                # User-specific performance
                if user_performance.get('query_count', 0) > 0:
                    with ui.card().classes("w-full"):
                        ui.label("Your Usage (24h)").classes("text-lg font-semibold")
                        ui.label(f"Queries: {user_performance['query_count']}")
                        ui.label(f"Avg Response: {user_performance['avg_endpoint_time_ms']}ms")
                        ui.label(f"Cache Hits: {user_performance['cache_hits']}")
            
            logger.info(f"[Dashboard] Loaded performance data for user {user.id}")
            
        except Exception as e:
            endpoint_info['status_code'] = 500
            logger.error(f"[Dashboard] Error loading dashboard: {e}")
            ui.notify("Error loading dashboard", type="negative")


@ui.page("/gui-week-optimized")
async def optimized_week_view(
    request: Request,
    user: User = Depends(current_active_user),
) -> None:
    """
    Optimized week view that preloads all data needed for the entire week.
    
    This demonstrates bulk data loading for complex UI views.
    """
    
    async with performance_monitor.track_endpoint("/gui-week-optimized", "GET", user.id) as endpoint_info:
        try:
            # Get week offset from query params
            week_offset = int(request.query_params.get("offset", "0"))
            today = datetime.date.today()
            week_start = today - datetime.timedelta(days=today.weekday()) - datetime.timedelta(weeks=week_offset)
            
            list_param = request.query_params.get("list")
            current_list_id = None
            if list_param and list_param.lower() == "none":
                current_list_id = "None"
            elif list_param and list_param.isdigit():
                current_list_id = int(list_param)
            
            # Preload all week data in one optimized operation
            async with performance_monitor.track_query("preload_habit_data_for_week", user.id) as query_info:
                week_data = await preload_habit_data_for_week(
                    user, week_start, list_id=current_list_id
                )
                query_info['record_count'] = week_data['habits_count']
            
            endpoint_info['query_count'] = 1
            
            # Render optimized week view
            with ui.column().classes("w-full max-w-6xl mx-auto"):
                ui.label(f"Week of {week_start.strftime('%B %d, %Y')}").classes("text-xl font-bold mb-4")
                
                # Week navigation
                with ui.row().classes("mb-4"):
                    ui.button("← Previous Week", 
                             on_click=lambda: ui.navigate.to(f"/gui-week-optimized?offset={week_offset + 1}"))
                    ui.button("This Week", 
                             on_click=lambda: ui.navigate.to("/gui-week-optimized"))
                    ui.button("Next Week →", 
                             on_click=lambda: ui.navigate.to(f"/gui-week-optimized?offset={week_offset - 1}"))
                
                # Week summary
                completion_rate = (
                    (week_data['actual_completions'] / week_data['total_possible_completions'] * 100)
                    if week_data['total_possible_completions'] > 0 else 0
                )
                
                with ui.card().classes("w-full mb-4"):
                    ui.label(f"Week Summary: {completion_rate:.1f}% complete")
                    ui.label(f"{week_data['actual_completions']} of {week_data['total_possible_completions']} possible completions")
                
                # Week grid (simplified for demo)
                with ui.row().classes("w-full"):
                    for day_offset in range(7):
                        day_date = week_start + datetime.timedelta(days=day_offset)
                        day_data = week_data['week_data'][day_date]
                        
                        with ui.column().classes("flex-1"):
                            ui.label(day_date.strftime("%a %m/%d")).classes("font-semibold")
                            
                            completed_today = sum(
                                1 for habit_data in day_data['habits']
                                if habit_data['day_completion'] is True
                            )
                            
                            ui.label(f"{completed_today}/{len(day_data['habits'])}")
            
            logger.info(f"[Week] Loaded optimized week view for {week_data['habits_count']} habits")
            
        except Exception as e:
            endpoint_info['status_code'] = 500
            logger.error(f"[Week] Error in optimized week view: {e}")
            ui.notify("Error loading week view", type="negative")


# Export optimized route handlers
optimized_habit_routes = [
    optimized_index_page,
    performance_dashboard_page, 
    optimized_week_view,
]