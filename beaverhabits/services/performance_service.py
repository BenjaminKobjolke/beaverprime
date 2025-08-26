"""
Performance-optimized service for BeaverHabits application.

This service provides high-performance implementations of frequently used
operations, utilizing bulk queries and caching to minimize database load.
"""

from datetime import date, timedelta
from typing import List, Dict, Optional, Tuple
from uuid import UUID

from beaverhabits.logging import logger
from beaverhabits.repositories.interfaces import IUnitOfWork
from beaverhabits.services.cache_service import habit_calculation_cache
from beaverhabits.sql.models import Habit, CheckedRecord, User


class PerformanceService:
    """High-performance service for bulk operations and calculations."""
    
    def __init__(self, uow: IUnitOfWork):
        self._uow = uow
    
    async def get_habits_with_calculations(self, user: User, list_id: Optional[int] = None, 
                                         today: Optional[date] = None) -> List[Dict]:
        """
        Get habits with pre-calculated performance metrics in a single optimized query.
        
        Returns list of dicts with habit data and calculated metrics:
        - habit: Habit object
        - week_ticks: Current week completion count
        - total_ticks: Total completion count
        - consecutive_weeks: Consecutive weeks meeting goal
        - last_week_complete: Whether last week's goal was met
        """
        if today is None:
            today = date.today()
        
        # Use optimized query to get habits with recent checks pre-loaded
        habits = await self._uow.habits.get_user_habits_with_recent_checks(
            user, days=90, list_id=list_id  # 90 days should cover most calculations
        )
        
        if not habits:
            return []
        
        # Get additional older records if needed for consecutive weeks calculation
        start_date = today - timedelta(days=365)  # Full year for complete streaks
        end_date = today + timedelta(days=1)  # Include today
        
        # Bulk load all required checks
        bulk_checks = await self._uow.habits.get_bulk_checks(habits, start_date, end_date)
        
        result = []
        
        for habit in habits:
            habit_checks = bulk_checks.get(habit.id, [])
            
            # Calculate all metrics at once
            metrics = await self._calculate_habit_metrics(
                habit, habit_checks, today
            )
            
            result.append({
                'habit': habit,
                **metrics
            })
        
        logger.info(f"[Performance] Calculated metrics for {len(habits)} habits with {sum(len(checks) for checks in bulk_checks.values())} total checks")
        return result
    
    async def _calculate_habit_metrics(self, habit: Habit, checks: List[CheckedRecord], 
                                     today: date) -> Dict[str, int]:
        """Calculate all habit metrics from pre-loaded checks."""
        # Try to get from cache first
        cached_stats = await habit_calculation_cache.get_habit_stats(habit.id, habit.user_id)
        if cached_stats and cached_stats.get('calculated_date') == today:
            return cached_stats
        
        # Convert checks to a set of completed dates for faster lookup
        completed_dates = {
            check.day for check in checks 
            if check.done and check.day <= today
        }
        
        # Calculate current week ticks
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        week_ticks = sum(1 for day in completed_dates 
                        if week_start <= day <= week_end)
        
        # Calculate total ticks
        total_ticks = len(completed_dates)
        
        # Calculate consecutive weeks
        consecutive_weeks = self._calculate_consecutive_weeks_optimized(
            habit, completed_dates, today
        )
        
        # Calculate last week completion
        last_week_start = week_start - timedelta(days=7)
        last_week_end = last_week_start + timedelta(days=6)
        
        # Check if habit existed last week
        if habit.created_at.date() <= last_week_end:
            last_week_ticks = sum(1 for day in completed_dates 
                                if last_week_start <= day <= last_week_end)
            last_week_complete = last_week_ticks >= (habit.weekly_goal or 0)
        else:
            last_week_complete = True  # New habits don't show as incomplete
        
        metrics = {
            'week_ticks': week_ticks,
            'total_ticks': total_ticks,
            'consecutive_weeks': consecutive_weeks,
            'last_week_complete': last_week_complete,
            'calculated_date': today
        }
        
        # Cache the results
        await habit_calculation_cache.set_habit_stats(habit.id, habit.user_id, metrics)
        
        return metrics
    
    def _calculate_consecutive_weeks_optimized(self, habit: Habit, 
                                             completed_dates: set, today: date) -> int:
        """Optimized consecutive weeks calculation using set lookup."""
        if not habit.weekly_goal or habit.weekly_goal == 0:
            return 0
        
        # Start from current week if complete, otherwise last week
        current_week_start = today - timedelta(days=today.weekday())
        current_week_end = current_week_start + timedelta(days=6)
        
        current_week_ticks = sum(1 for day in completed_dates 
                               if current_week_start <= day <= current_week_end)
        current_week_complete = current_week_ticks >= habit.weekly_goal
        
        # Start checking from last week
        consecutive_weeks = 0
        week_start = current_week_start - timedelta(days=7)
        
        # Check weeks backwards until we find an incomplete week
        while True:
            week_end = week_start + timedelta(days=6)
            
            # Don't count weeks before habit was created
            if week_end < habit.created_at.date():
                break
            
            # Count ticks for this week
            week_ticks = sum(1 for day in completed_dates 
                           if week_start <= day <= week_end)
            
            if week_ticks >= habit.weekly_goal:
                consecutive_weeks += 1
                week_start -= timedelta(days=7)  # Move to previous week
            else:
                break  # First incomplete week found
        
        # Add current week if it's complete and we have consecutive weeks
        if current_week_complete and consecutive_weeks > 0:
            consecutive_weeks += 1
        
        return consecutive_weeks
    
    async def bulk_update_habit_checks(self, updates: List[Dict]) -> int:
        """
        Bulk update multiple habit checks efficiently.
        
        Args:
            updates: List of dicts with keys: habit_id, user_id, date, done, note
        
        Returns:
            Number of records updated
        """
        if not updates:
            return 0
        
        updated_count = 0
        affected_habits = set()
        
        for update_data in updates:
            habit_id = update_data['habit_id']
            user_id = update_data['user_id']
            check_date = update_data['date']
            done = update_data['done']
            note = update_data.get('note')
            
            # Get habit for validation
            habit = await self._uow.habits.get_by_id(habit_id)
            if not habit or habit.user_id != user_id:
                continue
            
            if done:
                await self._uow.habits.add_check(habit, check_date, note)
            else:
                await self._uow.habits.remove_check(habit, check_date)
            
            updated_count += 1
            affected_habits.add((habit_id, user_id))
        
        # Commit all changes at once
        await self._uow.commit()
        
        # Invalidate cache for affected habits
        for habit_id, user_id in affected_habits:
            await habit_calculation_cache.invalidate_habit_cache(habit_id, user_id)
        
        logger.info(f"[Performance] Bulk updated {updated_count} habit checks for {len(affected_habits)} habits")
        return updated_count
    
    async def get_user_performance_summary(self, user: User, days: int = 30) -> Dict[str, any]:
        """
        Get a performance summary for a user over the specified period.
        
        Returns summary with completion rates, streaks, and trends.
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get habits with recent data
        habits = await self._uow.habits.get_user_habits_with_recent_checks(
            user, days=days
        )
        
        if not habits:
            return {
                'total_habits': 0,
                'completion_rate': 0.0,
                'total_completions': 0,
                'average_streak': 0.0,
                'habits_meeting_goals': 0,
                'most_consistent_habit': None
            }
        
        # Calculate summary metrics
        total_completions = 0
        total_possible = 0
        streaks = []
        habits_meeting_weekly_goals = 0
        
        # Get bulk checks for all habits
        bulk_checks = await self._uow.habits.get_bulk_checks(habits, start_date, end_date)
        
        for habit in habits:
            habit_checks = bulk_checks.get(habit.id, [])
            completed_days = {check.day for check in habit_checks if check.done}
            
            # Count completions in period
            period_completions = len(completed_days)
            total_completions += period_completions
            
            # Calculate possible completions based on habit creation date
            habit_start = max(habit.created_at.date(), start_date)
            possible_days = (end_date - habit_start).days + 1
            total_possible += possible_days
            
            # Calculate weekly goal achievement
            weeks_in_period = (days // 7) + 1
            weekly_completions = []
            
            for week_offset in range(weeks_in_period):
                week_start = end_date - timedelta(days=end_date.weekday()) - timedelta(weeks=week_offset)
                week_end = week_start + timedelta(days=6)
                
                if week_end < habit_start:
                    continue
                
                week_ticks = sum(1 for day in completed_days 
                               if week_start <= day <= week_end)
                weekly_completions.append(week_ticks)
            
            # Check if habit consistently meets weekly goals
            if habit.weekly_goal and weekly_completions:
                weeks_meeting_goal = sum(1 for ticks in weekly_completions 
                                       if ticks >= habit.weekly_goal)
                if weeks_meeting_goal >= len(weekly_completions) * 0.8:  # 80% of weeks
                    habits_meeting_weekly_goals += 1
            
            # Calculate current streak
            current_streak = self._calculate_current_streak(completed_days, end_date)
            streaks.append(current_streak)
        
        completion_rate = (total_completions / total_possible * 100) if total_possible > 0 else 0
        average_streak = sum(streaks) / len(streaks) if streaks else 0
        
        # Find most consistent habit (highest completion rate)
        most_consistent = None
        if habits:
            habit_rates = []
            for habit in habits:
                habit_checks = bulk_checks.get(habit.id, [])
                completed_days = len({check.day for check in habit_checks if check.done})
                habit_start = max(habit.created_at.date(), start_date)
                possible_days = (end_date - habit_start).days + 1
                rate = completed_days / possible_days if possible_days > 0 else 0
                habit_rates.append((habit.name, rate))
            
            most_consistent = max(habit_rates, key=lambda x: x[1])[0] if habit_rates else None
        
        summary = {
            'total_habits': len(habits),
            'completion_rate': round(completion_rate, 1),
            'total_completions': total_completions,
            'average_streak': round(average_streak, 1),
            'habits_meeting_goals': habits_meeting_weekly_goals,
            'most_consistent_habit': most_consistent,
            'period_days': days
        }
        
        logger.info(f"[Performance] Generated summary for {len(habits)} habits over {days} days")
        return summary
    
    def _calculate_current_streak(self, completed_dates: set, end_date: date) -> int:
        """Calculate current consecutive day streak."""
        if not completed_dates:
            return 0
        
        streak = 0
        current_date = end_date
        
        # Count backwards from today
        while current_date in completed_dates:
            streak += 1
            current_date -= timedelta(days=1)
        
        return streak