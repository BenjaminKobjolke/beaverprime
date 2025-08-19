import datetime
from nicegui import ui

from beaverhabits.utils import get_week_offset, set_week_offset, set_navigating
from beaverhabits.frontend.components.utils.date import format_week_range

@ui.refreshable
async def week_navigation(days: list[datetime.date]):
    """Week navigation component."""
    offset = get_week_offset()
    state = ui.state(dict(can_go_forward=offset < 0))
    
    # Mobile: vertical layout (date on top, arrows below), Desktop: horizontal layout
    # Use a container that has consistent height alignment
    with ui.column().classes("items-center justify-center gap-0 sm:hidden"):
        # Mobile: date on top, arrows below
        ui.label(format_week_range(days)).classes("text-xs text-center whitespace-nowrap")
        with ui.row().classes("gap-2"):
            ui.button(
                "←",
                on_click=lambda: change_week(offset - 1)
            ).props('flat dense').classes("min-w-6 h-6")
            ui.button(
                "→",
                on_click=lambda: change_week(offset + 1)
            ).props('flat dense').bind_enabled_from(state, 'can_go_forward').classes("min-w-6 h-6")
    
    # Desktop: horizontal layout  
    with ui.row().classes("items-center justify-center gap-4 hidden sm:flex"):
        ui.button(
            "←",
            on_click=lambda: change_week(offset - 1)
        ).props('flat')
        ui.label(format_week_range(days)).classes("text-lg text-center px-2")
        ui.button(
            "→",
            on_click=lambda: change_week(offset + 1)
        ).props('flat').bind_enabled_from(state, 'can_go_forward')

async def change_week(new_offset: int) -> None:
    """Change the current week offset and reload the page."""
    set_week_offset(new_offset)
    set_navigating(True)  # Mark that we're navigating
    # Navigate to the same page to get fresh data
    ui.navigate.reload()
