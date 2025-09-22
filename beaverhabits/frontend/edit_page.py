from nicegui import ui

from beaverhabits.frontend import components
from beaverhabits.frontend.components.habit.habit_edit_form import habit_edit_form
from beaverhabits.frontend.layout import layout
from beaverhabits.sql.models import Habit, HabitList
from beaverhabits.app.crud import get_user_lists, get_user_habits, create_habit, update_habit
from beaverhabits.app.db import User
from beaverhabits.services.i18n import t


@ui.refreshable
async def edit_ui(habits: list[Habit], lists: list[HabitList], user: User):
    # Filter out deleted habits
    active_habits = [h for h in habits if not h.deleted]
    active_habits.sort(key=lambda h: h.order)

    for item in active_habits:
        await habit_edit_form(
            habit=item,
            lists=lists,
            user=user,
            refresh_callback=edit_ui.refresh,
            show_card=True,
            show_filter_data=True,
            collapsible=False,  # Not collapsible on bulk edit page
            collapsed_by_default=False
        )


async def edit_page_ui(habits: list[Habit], user: User):
    async with layout(user=user):
        with ui.column().classes("w-full gap-4 pb-64 px-4"):
            # Get all lists for the user
            lists = await get_user_lists(user)
            
            # Filter input for existing habits
            if habits:  # Only show filter if there are habits
                with ui.card().classes("w-full p-4"):
                    with ui.column().classes("w-full gap-2"):
                        ui.label(t("habits.filter_habits")).classes("text-lg font-semibold")
                        with ui.row().classes("w-full items-center gap-2"):
                            filter_input = ui.input(
                                placeholder=t("habits.filter_placeholder"),
                                on_change=lambda e: ui.run_javascript(
                                    f'window.HabitEditFilter.filterHabits("{e.value}");'
                                )
                            ).props('clearable outlined dense').classes("flex-grow")
                            filter_input.props('id="habit-filter-input"')
                        ui.label("").props('id="habit-filter-count"').classes("text-sm text-gray-600")
            
            # Existing habits section
            await edit_ui(habits, lists, user)