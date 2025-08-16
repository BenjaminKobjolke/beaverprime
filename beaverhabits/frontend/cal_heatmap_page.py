import datetime

from nicegui import ui

from beaverhabits.configs import settings
from beaverhabits.frontend.components import (
    CalendarHeatmap,
    habit_heat_map,
)
from beaverhabits.frontend.layout import layout
from beaverhabits.frontend.css import CHECK_BOX_CSS
from beaverhabits.sql.models import Habit
from beaverhabits.app.crud import get_habit_checks
from beaverhabits.app.db import User

WEEKS_TO_DISPLAY = 53


async def heatmap_page(today: datetime.date, habit: Habit, user: User | None = None):
    ui.add_css(CHECK_BOX_CSS)

    async with layout(title=habit.name, user=user):
        # Get all completed records
        records = await get_habit_checks(habit.id, habit.user_id)
        completed_days = [r.day for r in records if r.done]
        start_date = min(completed_days) if completed_days else today

        with ui.column():
            # Show heatmap for each year from today back to the first record
            current_year = today.year
            start_year = start_date.year if completed_days else today.year
            
            for year in range(current_year, start_year - 1, -1):
                year_date = today.replace(year=year)
                with ui.card().classes("p-3 gap-0 no-shadow items-center"):
                    ui.label(str(year)).classes("text-base")

                    habit_calendar = CalendarHeatmap.build(
                        year_date, WEEKS_TO_DISPLAY, settings.FIRST_DAY_OF_WEEK
                    )
                    await habit_heat_map(habit, habit_calendar)
