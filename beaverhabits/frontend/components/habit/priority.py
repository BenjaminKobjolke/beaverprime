from nicegui import ui

class HabitPriority(ui.label):
    def __init__(self, initial_priority: int = 0) -> None:
        super().__init__(f"Priority: {initial_priority}")
        self.classes("text-xs text-gray-500 priority-label")
        
    async def _update_priority(self, priority: int) -> None:
        """Update the priority label."""
        self.text = f"Priority: {priority}"
