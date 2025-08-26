"""
Performance-optimized habit utilities for BeaverHabits application.

This module provides optimized versions of commonly used habit utility functions
that leverage bulk queries and caching for better performance.
"""

import datetime
from typing import List, Dict, Optional

from beaverhabits.logging import logger
from beaverhabits.repositories import SQLAlchemyUnitOfWork
from beaverhabits.services.performance_service import PerformanceService
from beaverhabits.sql.models import Habit, User


async def get_habits_with_performance_data(user: User, list_id: Optional[int] = None, 
                                         today: Optional[datetime.date] = None) -> List[Dict]:
    """
    Get habits with all performance calculations done efficiently.
    
    This replaces multiple individual database calls with bulk operations
    and returns pre-calculated metrics for UI rendering.
    
    Returns:
        List of dicts with habit data and performance metrics:
        - habit: Habit object
        - week_ticks: Current week completion count  
        - total_ticks: Total completion count
        - consecutive_weeks: Consecutive weeks meeting goal
        - last_week_complete: Whether last week's goal was met
        - completion_rate: Overall completion percentage
    """
    if today is None:
        today = datetime.date.today()
    
    async with SQLAlchemyUnitOfWork() as uow:
        performance_service = PerformanceService(uow)
        
        # Get all habits with calculated metrics in one optimized operation
        habits_data = await performance_service.get_habits_with_calculations(
            user, list_id=list_id, today=today
        )
        
        # Add additional UI-specific calculations
        for habit_data in habits_data:
            habit = habit_data['habit']
            
            # Calculate completion rate for display
            if habit_data['total_ticks'] > 0:
                # Estimate based on days since creation
                days_since_creation = (today - habit.created_at.date()).days + 1
                completion_rate = (habit_data['total_ticks'] / days_since_creation) * 100
                habit_data['completion_rate'] = min(100, round(completion_rate, 1))
            else:
                habit_data['completion_rate'] = 0.0
            
            # Add display helpers
            habit_data['display_name'] = habit.name
            habit_data['is_starred'] = habit.star
            habit_data['weekly_goal'] = habit.weekly_goal or 1
            
            # Goal achievement status for current week
            habit_data['week_goal_met'] = (
                habit_data['week_ticks'] >= (habit.weekly_goal or 1)
            )
    
    logger.info(f"[Utils] Retrieved {len(habits_data)} habits with optimized performance data")
    return habits_data


async def bulk_update_habit_completions(updates: List[Dict[str, any]]) -> bool:
    """
    Update multiple habit completions efficiently in a single transaction.
    
    Args:
        updates: List of update dicts with keys:
            - habit_id: int
            - user_id: UUID
            - date: datetime.date
            - done: bool
            - note: Optional[str]
    
    Returns:
        True if all updates succeeded, False otherwise
    """
    try:
        async with SQLAlchemyUnitOfWork() as uow:
            performance_service = PerformanceService(uow)
            updated_count = await performance_service.bulk_update_habit_checks(updates)
            
            logger.info(f"[Utils] Bulk updated {updated_count} habit completions")
            return updated_count > 0
            
    except Exception as e:
        logger.error(f"[Utils] Bulk update failed: {e}")
        return False


async def get_user_dashboard_summary(user: User, days: int = 30) -> Dict[str, any]:
    """
    Get an optimized dashboard summary for a user.
    
    Provides key metrics and insights efficiently calculated from bulk data.
    
    Returns:
        Dict with summary metrics for dashboard display
    """
    async with SQLAlchemyUnitOfWork() as uow:
        performance_service = PerformanceService(uow)
        summary = await performance_service.get_user_performance_summary(user, days)
        
        # Add UI-friendly formatting
        summary['completion_rate_display'] = f"{summary['completion_rate']}%"
        summary['period_display'] = f"Last {days} days"
        
        # Add motivational messages based on performance
        if summary['completion_rate'] >= 80:
            summary['performance_message'] = "Excellent consistency! Keep it up! 🎉"
            summary['performance_level'] = "excellent"
        elif summary['completion_rate'] >= 60:
            summary['performance_message'] = "Great progress! You're doing well! 👍"
            summary['performance_level'] = "good"
        elif summary['completion_rate'] >= 40:
            summary['performance_message'] = "Good start! Keep building momentum! 💪"
            summary['performance_level'] = "fair"
        else:
            summary['performance_message'] = "Every day is a new opportunity! 🌟"
            summary['performance_level'] = "needs_improvement"
    
    logger.info(f"[Utils] Generated dashboard summary: {summary['completion_rate']}% over {days} days")
    return summary


def filter_habits_by_list_optimized(habits_data: List[Dict], current_list_id: str | int | None) -> List[Dict]:
    """
    Optimized version of habit filtering that works on pre-loaded data.
    
    This avoids additional database queries by filtering in-memory data.
    
    Args:
        habits_data: List of habit data dicts from get_habits_with_performance_data
        current_list_id: List ID to filter by ("None", int, or None for all)
    
    Returns:
        Filtered list of habit data dicts
    """
    if not habits_data:
        return []
    
    active_habits = []
    
    for habit_data in habits_data:
        habit = habit_data['habit']
        
        # Skip deleted habits (should already be filtered but double-check)
        if habit.deleted:
            continue
        
        # Apply list filtering
        if current_list_id == "None":
            if habit.list_id is None:
                active_habits.append(habit_data)
        elif isinstance(current_list_id, int):
            if habit.list_id == current_list_id:
                active_habits.append(habit_data)
        else:
            # No filter - include all
            active_habits.append(habit_data)
    
    # Sort by order (already done in query but ensure consistency)
    active_habits.sort(key=lambda x: x['habit'].order)
    
    # Log summary
    if current_list_id == "None":
        logger.info(f"[Utils] Filtered to {len(active_habits)} habits with no list")
    elif isinstance(current_list_id, int):
        logger.info(f"[Utils] Filtered to {len(active_habits)} habits from list {current_list_id}")
    else:
        logger.info(f"[Utils] Showing all {len(active_habits)} habits")
    
    return active_habits


async def preload_habit_data_for_week(user: User, week_start: datetime.date, 
                                    list_id: Optional[int] = None) -> Dict[str, any]:
    """
    Preload all habit data needed for a week view in a single optimized query.
    
    This function loads everything needed to render a full week view without
    additional database queries during UI rendering.
    
    Args:
        user: User object
        week_start: Start date of the week to load
        list_id: Optional list filter
    
    Returns:
        Dict containing all preloaded data for the week
    """
    week_end = week_start + datetime.timedelta(days=6)
    today = datetime.date.today()
    
    async with SQLAlchemyUnitOfWork() as uow:
        performance_service = PerformanceService(uow)
        
        # Get habits with extended data range to cover the week plus calculations
        habits_data = await performance_service.get_habits_with_calculations(
            user, list_id=list_id, today=today
        )
        
        # Get bulk checks for the specific week
        habits = [data['habit'] for data in habits_data]
        week_checks = await uow.habits.get_bulk_checks(habits, week_start, week_end)
        
        # Organize data by day for easy UI access
        week_data = {}
        for day_offset in range(7):
            current_day = week_start + datetime.timedelta(days=day_offset)
            week_data[current_day] = {
                'date': current_day,
                'habits': []
            }
            
            for habit_data in habits_data:
                habit = habit_data['habit']
                day_checks = [
                    check for check in week_checks.get(habit.id, [])
                    if check.day == current_day
                ]
                
                # Determine completion status for this day
                completion_status = None
                note = None
                if day_checks:
                    check = day_checks[0]  # Should only be one per day
                    completion_status = check.done
                    note = check.text
                
                week_data[current_day]['habits'].append({
                    **habit_data,  # Include all pre-calculated metrics
                    'day_completion': completion_status,
                    'day_note': note,
                    'is_today': current_day == today,
                    'is_future': current_day > today
                })
    
    result = {
        'week_start': week_start,
        'week_end': week_end,
        'week_data': week_data,
        'habits_count': len(habits_data),
        'total_possible_completions': len(habits_data) * 7,
        'actual_completions': sum(
            1 for day_data in week_data.values()
            for habit_data in day_data['habits']
            if habit_data['day_completion'] is True
        )
    }
    
    logger.info(f"[Utils] Preloaded week data: {result['habits_count']} habits, "
               f"{result['actual_completions']}/{result['total_possible_completions']} completions")
    
    return result