import datetime
from typing import Callable, Optional
from nicegui import ui, events

from beaverhabits.configs import settings
from beaverhabits.frontend import icons
from beaverhabits.logging import logger
from beaverhabits.sql.models import Habit
from beaverhabits.app.crud import update_habit, get_habit_checks
from .checkbox import habit_tick
from beaverhabits.services.i18n import t

TODAY = "today"
DAY_MASK = "%Y-%m-%d"
MONTH_MASK = "%Y/%m"
CALENDAR_EVENT_MASK = "%Y/%m/%d"

class WeeklyGoalInput(ui.number):
    def __init__(self, habit: Habit, refresh: Callable) -> None:
        super().__init__(value=habit.weekly_goal or 0, min=0, max=7)
        self.habit = habit
        self.props("dense hide-bottom-space")

    def _validate(self, value: str) -> Optional[str]:
        if value is None or value < 0 or value > 7:
            return t("habits.weekly_goal_range")

    def get_value(self) -> int:
        return self.value

class HabitNameInput(ui.input):
    def __init__(self, habit: Habit, refresh: Callable) -> None:
        super().__init__(value=habit.name)
        self.habit = habit
        self.validation = self._validate
        self.props("dense hide-bottom-space")

    def _validate(self, value: str) -> Optional[str]:
        if not value:
            return t("habits.name_required")
        if len(value) > 130:
            return t("habits.name_too_long")

    def get_value(self) -> str:
        return self.value

class MultiPartNameInput(ui.column):
    def __init__(self, initial_value: str = "", habit: Optional[Habit] = None, refresh: Optional[Callable] = None) -> None:
        super().__init__()
        self.habit = habit
        self.refresh = refresh
        self.input_fields = []
        self.field_rows = []  # Track the UI rows containing each field
        self.classes("w-full gap-2")
        
        # Parse initial value (split by ||)
        if initial_value and initial_value.strip():
            parts = [part.strip() for part in initial_value.split('||') if part.strip()]
        else:
            parts = [""]  # Start with one empty field
        
        # Create input fields for each part
        for i, part in enumerate(parts):
            self._add_input_field(part, i == 0)  # First field cannot be deleted
    
    def _add_input_field(self, value: str = "", is_first: bool = False):
        """Add a new input field with add/remove buttons."""
        row = ui.row().classes("w-full items-center gap-2")
        with row:
            # Input field
            input_field = ui.input(
                value=value,
                placeholder=t("habits.habit_part_placeholder", part=len(self.input_fields) + 1) if len(self.input_fields) > 0 else t("habits.habit_name_placeholder"),
                validation=self._validate_field
            ).props("dense hide-bottom-space").classes("flex-grow")
            
            # Capture the index BEFORE adding to the list (this will be the index of this field)
            field_index = len(self.input_fields)
            
            # Add the input field and row to our tracking lists now
            self.input_fields.append(input_field)
            self.field_rows.append(row)
            
            # Add button (always present)
            ui.button(
                "+",
                on_click=lambda: self._add_new_field()
            ).props("flat fab-mini").classes("text-green-600")
            
            # Remove button (only if not the first field or if there are multiple fields)
            if not is_first or len(self.input_fields) > 1:  # Now check against updated length
                ui.button(
                    "-",
                    on_click=lambda idx=field_index: self._remove_field_direct(idx)
                ).props("flat fab-mini").classes("text-red-600")
            else:
                # Add invisible button to keep alignment (same size as the - button)
                ui.button("-").props("flat fab-mini").classes("invisible")
    
    def _add_new_field(self):
        """Add a new empty input field."""
        self._add_input_field()
    
    def _remove_field_direct(self, index: int):
        """Remove an input field by index without rebuilding."""
        if len(self.input_fields) <= 1:
            return  # Don't remove if it's the only field
        
        if 0 <= index < len(self.input_fields):
            # Remove the row from the UI
            row_to_remove = self.field_rows[index]
            row_to_remove.delete()
            
            # Remove from our tracking lists
            self.input_fields.pop(index)
            self.field_rows.pop(index)
    
    def _remove_field(self, index: int):
        """Remove an input field by index."""
        if len(self.input_fields) <= 1:
            return  # Don't remove if it's the only field
        
        # Remove the field from our tracking
        if 0 <= index < len(self.input_fields):
            # Get all current values (including empty ones) before modification
            current_values = [field.value for field in self.input_fields]
            
            # Remove the field at the specified index
            current_values.pop(index)
            
            # Clear the entire container and rebuild
            self.clear()
            self.input_fields.clear()
            
            # If no values left, add one empty field
            if not current_values:
                current_values = [""]
            
            # Recreate all fields
            for i, value in enumerate(current_values):
                self._add_input_field(value, i == 0)
            
            # Force a UI update
            self.update()
    
    def _validate_field(self, value: str) -> Optional[str]:
        """Validate individual field."""
        if value and len(value) > 130:
            return t("habits.name_too_long")
        return None
    
    def get_parts(self) -> list[str]:
        """Get all non-empty parts."""
        return [field.value.strip() for field in self.input_fields if field.value.strip()]
    
    def get_value(self) -> str:
        """Get the combined value with || separator."""
        parts = self.get_parts()
        if not parts:
            return ""
        return " || ".join(parts)
    
    def validate(self) -> Optional[str]:
        """Validate the entire input (at least one non-empty part)."""
        parts = self.get_parts()
        if not parts:
            return t("habits.at_least_one_part_required")
        return None

class HabitDateInput(ui.date):
    def __init__(
        self,
        today: datetime.date,
        habit: Habit,
    ) -> None:
        self.today = today
        self.habit = habit
        super().__init__(self._tick_days, on_change=self._async_task)

        self.props("multiple minimal flat today-btn")
        self.props(f"default-year-month={self.today.strftime(MONTH_MASK)}")
        self.props(f"first-day-of-week='{(settings.FIRST_DAY_OF_WEEK + 1) % 7}'")

        self.classes("shadow-none")

        self.bind_value_from(self, "_tick_days")
        # Get events (days with notes)
        events = [
            r.day.strftime(CALENDAR_EVENT_MASK)
            for r in habit.checked_records
            if hasattr(r, 'text') and r.text
        ]
        self.props(f'events="{events}" event-color="teal"')

    @property
    def _tick_days(self) -> list[str]:
        # Get completed days from eagerly loaded checked_records
        ticked_days = [r.day.strftime(DAY_MASK) for r in self.habit.checked_records if r.done]
        return [*ticked_days, TODAY]

    async def _async_task(self, e: events.ValueChangeEventArguments):
        # Get current completed days
        records = await get_habit_checks(self.habit.id, self.habit.user_id)
        old_values = {r.day for r in records if r.done}
        value = await e.value
        new_values = set()
        for x in value:
            if x and x != TODAY:
                try:
                    date = datetime.datetime.strptime(x, DAY_MASK).date()
                    new_values.add(date)
                except ValueError:
                    logger.warning(f"Invalid date format: {x}")

        if diff := new_values - old_values:
            day, value = diff.pop(), True
        elif diff := old_values - new_values:
            day, value = diff.pop(), False
        else:
            return


        self.props(f"default-year-month={day.strftime(MONTH_MASK)}")
        await habit_tick(self.habit, day, bool(value))
        self.value = self._tick_days
