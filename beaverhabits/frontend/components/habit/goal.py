from nicegui import ui

class HabitGoalLabel(ui.label):
    def __init__(self, goal: int, initial_color: str | None = None) -> None:
        super().__init__(f"{int(goal)}x")
        self.classes("text-sm habit-goal")
        
        # Set initial color if provided
        if initial_color:
            self.props(f"text-color={initial_color}")
    
    async def _update_style(self, color: str) -> None:
        """Update the visual state of the label."""
        self.props(f"text-color={color}")

class HabitConsecutiveWeeksLabel(ui.label):
    def __init__(self, consecutive_weeks: int, initial_color: str | None = None) -> None:
        super().__init__(f"{int(consecutive_weeks)}w")
        # Smaller font and muted color for secondary info
        self.classes("text-xs opacity-70 habit-weeks")
        
        # Set initial color if provided, but make it more muted
        if initial_color:
            self.props(f"text-color={initial_color}")
    
    async def _update_style(self, color: str) -> None:
        """Update the visual state of the label."""
        self.props(f"text-color={color}")
