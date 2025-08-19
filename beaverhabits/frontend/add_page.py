from nicegui import ui

from beaverhabits.frontend import components
from beaverhabits.frontend.components import (
    HabitAddButton,
    HabitDeleteButton,
    HabitNameInput,
    HabitSaveButton,
    HabitStarCheckbox,
    WeeklyGoalInput,
    MultiPartNameInput,
)
from beaverhabits.frontend.layout import layout
from beaverhabits.sql.models import Habit, HabitList
from beaverhabits.app.crud import get_user_lists, get_user_habits, create_habit, update_habit
from beaverhabits.app.db import User
from beaverhabits.services.i18n import t




async def add_page_ui(user: User):
    async with layout(user=user):
        with ui.column().classes("w-full gap-4 pb-64 px-4"):
            # Add new habit form
            with ui.card().classes("w-full p-4"):
                with ui.column().classes("w-full gap-4"):
                    ui.label(t("habits.add_new_habit")).classes("text-lg font-semibold")
                    
                    # Multi-part name input
                    ui.label(t("habits.habit_name")).classes("text-sm font-medium")
                    name_input = MultiPartNameInput()

                    # Weekly goal input
                    with ui.row().classes("items-center gap-2"):
                        goal_input = ui.number(
                            value=0,
                            min=0,
                            max=7,
                            label=t("habits.weekly_goal")
                        ).props("dense hide-bottom-space")
                        ui.label(t("habits.times_per_week"))

                    # List selection
                    lists = await get_user_lists(user)
                    no_list_label = t("habits.no_list")
                    list_options = [{"label": no_list_label, "value": None}] + [
                        {"label": list.name, "value": list.id} for list in lists if not list.deleted
                    ]
                    name_to_id = {no_list_label: None}
                    name_to_id.update({opt["label"]: opt["value"] for opt in list_options[1:]})
                    options = list(name_to_id.keys())
                    list_select = ui.select(
                        options=options,
                        value=no_list_label,
                        label=t("habits.list")
                    ).props('outlined dense options-dense').classes("w-full")

                    # Add button
                    with ui.row().classes("justify-end"):
                        ui.button(t("habits.add_habit"), on_click=lambda: add_habit(
                            user,
                            name_input.get_value(),
                            name_to_id[list_select.value],
                            int(goal_input.value)
                        )).props("flat")

            async def add_habit(user, name, list_id, weekly_goal):
                if not name or not name.strip():
                    ui.notify(t("habits.please_enter_habit_name"), color="negative")
                    return
                
                try:
                    habit = await create_habit(user, name, list_id)
                    if habit:
                        await update_habit(habit.id, habit.user_id, weekly_goal=weekly_goal)
                        ui.notify(t("habits.successfully_added_habit", name=name), color="positive", timeout=3000)
                        # Clear the form by reloading the page after a short delay
                        ui.timer(1.5, lambda: ui.navigate.reload(), once=True)
                    else:
                        ui.notify(t("habits.failed_to_create_habit"), color="negative")
                except Exception as e:
                    ui.notify(t("habits.error_creating_habit", error=str(e)), color="negative")
