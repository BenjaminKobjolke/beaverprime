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


@ui.refreshable
async def edit_ui(habits: list[Habit], lists: list[HabitList], user: User):
    # Filter out deleted habits
    active_habits = [h for h in habits if not h.deleted]
    active_habits.sort(key=lambda h: h.order)

    for item in active_habits:
        with ui.card().classes("w-full p-4 mx-0 habit-edit-card") as card:
            # Add habit ID and name to the card for scrolling and filtering
            card.props(f'data-habit-id="{item.id}" data-habit-name="{item.name}"')
            
            with ui.column().classes("w-full gap-4"):
                # First line: Name (full width)
                name_input = MultiPartNameInput(initial_value=item.name, habit=item)

                # Second line: Weekly Goal
                with ui.row().classes("items-center gap-2"):
                    weekly_goal = WeeklyGoalInput(item, None)
                    ui.label(t("habits.times_per_week"))

                # Third line: List Selection (full width)
                no_list_label = t("habits.no_list")
                list_options = [{"label": no_list_label, "value": None}] + [
                    {"label": list.name, "value": list.id} for list in lists if not list.deleted
                ]
                name_to_id = {no_list_label: None}
                name_to_id.update({opt["label"]: opt["value"] for opt in list_options[1:]})
                options = list(name_to_id.keys())
                current_name = next(
                    (name for name, id in name_to_id.items() if id == item.list_id),
                    no_list_label
                )
                list_select = ui.select(
                    options=options,
                    value=current_name,
                    on_change=lambda e, h=item: (setattr(h, 'list_id', name_to_id[e.value]))
                ).props('dense outlined options-dense').classes("w-full")
                list_select.bind_value_from(lambda: next(
                    (name for name, id in name_to_id.items() if id == item.list_id),
                    no_list_label
                ))

                # Fourth line: Save button on left, Star and Delete on right
                with ui.row().classes("w-full justify-between items-center"):
                    # Left side - Save button
                    save = HabitSaveButton(item, weekly_goal, name_input, edit_ui.refresh)
                    
                    # Right side - Star and Delete buttons
                    with ui.row().classes("gap-2 items-center"):
                        star = HabitStarCheckbox(item, edit_ui.refresh)
                        delete = HabitDeleteButton(item, edit_ui.refresh)


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