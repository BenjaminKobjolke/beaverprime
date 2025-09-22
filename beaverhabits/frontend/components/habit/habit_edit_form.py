from typing import Callable, Optional, List
from nicegui import ui

from beaverhabits.sql.models import Habit, HabitList
from beaverhabits.app.db import User
from beaverhabits.services.i18n import t
from .inputs import MultiPartNameInput, WeeklyGoalInput, HabitNoteInput, HabitUrlInput
from .buttons import HabitSaveButton
from .checkbox import HabitStarCheckbox
from .buttons import HabitDeleteButton


@ui.refreshable
async def habit_edit_form(
    habit: Habit,
    lists: List[HabitList],
    user: User,
    refresh_callback: Optional[Callable] = None,
    show_card: bool = True,
    show_filter_data: bool = False,
    collapsible: bool = False,
    collapsed_by_default: bool = False
):
    """
    Reusable habit edit form component.

    Args:
        habit: The habit to edit
        lists: Available lists for the user
        user: The current user
        refresh_callback: Optional callback to refresh parent component
        show_card: Whether to wrap the form in a card
        show_filter_data: Whether to add data attributes for filtering
        collapsible: Whether to make the form collapsible
        collapsed_by_default: Whether to start collapsed (only if collapsible=True)
    """
    # Wrapper function for refreshing
    async def refresh():
        if refresh_callback:
            await refresh_callback()
        habit_edit_form.refresh()

    # Create the form content
    def create_form_content():
        with ui.column().classes("w-full gap-4"):
            # First line: Name (full width)
            name_input = MultiPartNameInput(initial_value=habit.name, habit=habit)

            # Second line: Weekly Goal
            with ui.row().classes("items-center gap-2"):
                weekly_goal = WeeklyGoalInput(habit, None)
                ui.label(t("habits.times_per_week"))

            # Third line: List Selection (full width)
            no_list_label = t("habits.no_list")
            list_options = [{"label": no_list_label, "value": None}] + [
                {"label": lst.name, "value": lst.id} for lst in lists if not lst.deleted
            ]
            name_to_id = {no_list_label: None}
            name_to_id.update({opt["label"]: opt["value"] for opt in list_options[1:]})
            options = list(name_to_id.keys())
            current_name = next(
                (name for name, list_id in name_to_id.items() if list_id == habit.list_id),
                no_list_label
            )
            list_select = ui.select(
                options=options,
                value=current_name,
                on_change=lambda e, h=habit: (setattr(h, 'list_id', name_to_id[e.value]))
            ).props('dense outlined options-dense').classes("w-full")
            list_select.bind_value_from(lambda: next(
                (name for name, list_id in name_to_id.items() if list_id == habit.list_id),
                no_list_label
            ))

            # Fourth line: Note field
            with ui.column().classes("w-full gap-1"):
                ui.label(t("habits.note_label")).classes("text-sm")
                note_input = HabitNoteInput(habit, refresh)

            # Fifth line: URL field
            with ui.column().classes("w-full gap-1"):
                ui.label(t("habits.url_label")).classes("text-sm")
                url_input = HabitUrlInput(habit, refresh)

            # Sixth line: Save button on left, Star and Delete on right
            with ui.row().classes("w-full justify-between items-center"):
                # Left side - Save button
                save = HabitSaveButton(habit, weekly_goal, name_input, refresh, note_input, url_input)

                # Right side - Star and Delete buttons
                with ui.row().classes("gap-2 items-center"):
                    star = HabitStarCheckbox(habit, refresh)
                    delete = HabitDeleteButton(habit, refresh)

    # Conditional wrapper based on configuration
    if collapsible:
        # Use expansion element for collapsible behavior
        expansion = ui.expansion(t("habits.edit_settings"), icon="settings")
        if collapsed_by_default:
            expansion.props("default-opened=false")
        else:
            expansion.props("default-opened=true")

        # Apply card styling to expansion if needed
        if show_card:
            expansion.classes("w-full habit-edit-card")
            if show_filter_data:
                expansion.props(f'data-habit-id="{habit.id}" data-habit-name="{habit.name}"')

        with expansion:
            create_form_content()
    else:
        # Conditional card wrapper for non-collapsible mode
        if show_card:
            card = ui.card().classes("w-full p-4 mx-0 habit-edit-card")
            if show_filter_data:
                card.props(f'data-habit-id="{habit.id}" data-habit-name="{habit.name}"')
            card.__enter__()

        try:
            create_form_content()
        finally:
            if show_card and not collapsible:
                card.__exit__(None, None, None)