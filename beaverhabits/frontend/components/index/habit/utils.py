import datetime
from typing import List

from beaverhabits.sql.models import Habit
from beaverhabits.app.crud import get_habit_checks
from beaverhabits.logging import logger

# not used
async def get_habit_priority(habit: Habit, days: List[datetime.date]) -> int:
    """Calculate habit priority based on completion status."""
    records = await get_habit_checks(habit.id, habit.user_id)
    week_ticks = sum(1 for record in records if record.day in days and record.done)
    return 1 if week_ticks >= (habit.weekly_goal or 0) else 0

async def get_week_ticks(habit: Habit, today: datetime.date) -> tuple[int, int]:
    """Get the number of ticks for the current week."""
    records = await get_habit_checks(habit.id, habit.user_id)
    week_start = today - datetime.timedelta(days=today.weekday())
    week_end = week_start + datetime.timedelta(days=6)
    week_ticks = sum(1 for record in records 
                    if week_start <= record.day <= week_end and record.done)
    total_ticks = sum(1 for record in records if record.done)
    return week_ticks, total_ticks

def should_check_last_week(habit: Habit, today: datetime.date) -> bool:
    """Determine if habit should be checked for last week's completion."""
    # Get the start of last week
    last_week_start = today - datetime.timedelta(days=today.weekday() + 7)
    
    # If habit was created after last week started, don't check last week
    if habit.created_at.date() > last_week_start:
        return False
        
    return True

async def get_last_week_completion(habit: Habit, today: datetime.date) -> bool:
    """Check if the habit was completed last week."""
    # First check if we should even look at last week
    if not should_check_last_week(habit, today):
        return True  # Return True to avoid showing red for new habits
        
    records = await get_habit_checks(habit.id, habit.user_id)
    last_week_start = today - datetime.timedelta(days=today.weekday() + 7)
    last_week_end = last_week_start + datetime.timedelta(days=6)
    last_week_ticks = sum(1 for record in records 
                         if last_week_start <= record.day <= last_week_end and record.done)
    return last_week_ticks >= (habit.weekly_goal or 0)

def filter_habits_by_list(habits: List[Habit], current_list_id: str | int | None) -> List[Habit]:
    """Filter habits based on list selection."""
    # Log the filtering criteria
    logger.info(f"Filtering habits with list_id={current_list_id!r} (type: {type(current_list_id)})")
    
    active_habits = []
    no_list_count = 0
    with_list_count = 0
    
    for h in habits:
        if h.deleted:
            continue
        
        # Show habit if:
        # - "None" is selected and habit has no list
        if current_list_id == "None":
            if h.list_id is None:
                active_habits.append(h)
                no_list_count += 1
        # - A specific list is selected and habit belongs to that list
        elif isinstance(current_list_id, int):
            if h.list_id == current_list_id:
                active_habits.append(h)
                with_list_count += 1
        # - No specific list is selected (show all habits)
        else:
            active_habits.append(h)
    
    active_habits.sort(key=lambda h: h.order)
    
    # Log summary instead of individual habits
    if current_list_id == "None":
        logger.info(f"Showing {no_list_count} habits with no list")
    elif isinstance(current_list_id, int):
        logger.info(f"Showing {with_list_count} habits from list {current_list_id}")
    else:
        logger.info(f"Showing all {len(active_habits)} habits")
    
    return active_habits

async def get_consecutive_weeks_count(habit: Habit, today: datetime.date) -> int:
    """Calculate consecutive weeks where weekly goal was met."""
    if not habit.weekly_goal or habit.weekly_goal == 0:
        return 0
        
    records = await get_habit_checks(habit.id, habit.user_id)
    consecutive_weeks = 0
    
    # Check if current week already meets the goal
    current_week_start = today - datetime.timedelta(days=today.weekday())
    current_week_end = current_week_start + datetime.timedelta(days=6)
    current_week_ticks = sum(1 for record in records 
                           if current_week_start <= record.day <= current_week_end and record.done)
    current_week_complete = current_week_ticks >= habit.weekly_goal
    
    # Start from last week (skip current incomplete week) and go backwards
    week_start = current_week_start - datetime.timedelta(days=7)  # Start from last week
    
    while True:
        week_end = week_start + datetime.timedelta(days=6)
        
        # Don't count weeks that start before habit was created
        # This allows the week of creation to count
        if week_start < habit.created_at.date() and week_end < habit.created_at.date():
            break
        
        # Count completions for this week
        week_ticks = sum(1 for record in records 
                        if week_start <= record.day <= week_end and record.done)
        
        # If this week meets the goal, increment counter
        if week_ticks >= habit.weekly_goal:
            consecutive_weeks += 1
        else:
            # First week that doesn't meet goal - stop counting
            break
            
        # Move to previous week
        week_start -= datetime.timedelta(days=7)
    
    # Bonus: Add current week if it already meets the goal
    if current_week_complete and consecutive_weeks > 0:
        consecutive_weeks += 1
    elif current_week_complete and consecutive_weeks == 0:
        consecutive_weeks = 1
    return consecutive_weeks
