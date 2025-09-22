import calendar
import datetime
from contextlib import contextmanager

from nicegui import ui

from beaverhabits.frontend.components import (
    CalendarHeatmap,
    HabitDateInput,
    habit_heat_map,
    habit_history,
    habit_notes,
    link,
)
from beaverhabits.frontend.css import (
    CALENDAR_CSS,
    CHECK_BOX_CSS,
    EXPANSION_CSS,
    HIDE_TIMELINE_TITLE,
)
from beaverhabits.frontend.layout import layout, redirect
from beaverhabits.frontend.components.habit.habit_edit_form import habit_edit_form
from beaverhabits.sql.models import Habit, CheckedRecord
from beaverhabits.app.crud import get_habit_checks, get_user_lists
from beaverhabits.app.db import User
from beaverhabits.services.i18n import t

WEEKS_TO_DISPLAY = 15


def card_title(title: str, target: str):
    return link(title, target).classes("text-base flex justify-center")


@contextmanager
def grid(classes: str = ""):
    with ui.element("div").classes(f"grid grid-cols-1 gap-2 h-fit {classes}") as grid:
        yield grid


@contextmanager
def card(link: str | None = None, padding: float = 3):
    with ui.card().classes("gap-0 no-shadow items-center") as card:
        card.classes(f"p-{padding}")
        card.classes("w-full break-inside-avoid h-fit")
        if link:
            card.classes("cursor-pointer")
            card.on("click", lambda: redirect(link))

        yield card


@ui.refreshable
async def habit_page(today: datetime.date, habit: Habit, user: User):
    # Get all checked records for this habit
    records = await get_habit_checks(habit.id, habit.user_id)

    # Get notes and sort them by date
    notes = [r for r in records if r.text]
    notes.sort(key=lambda x: x.day, reverse=True)

    # Get completed days
    completed_days = [r.day for r in records if r.done]

    # Get lists for edit form
    lists = await get_user_lists(user)

    # https://tailwindcss.com/docs/responsive-design#container-size-reference
    masony = "md:grid-cols-2" if notes else ""

    # Add container with padding and max-width for better mobile experience
    with ui.element('div').classes('w-full px-4 mx-auto max-w-2xl'):
        with grid(masony):
            habit_calendar = CalendarHeatmap.build(today, WEEKS_TO_DISPLAY, calendar.MONDAY)
            target = f"habits/{habit.id}/heatmap"

            with grid():
                # Edit Settings Section (collapsible, folded by default)
                await habit_edit_form(
                    habit,
                    lists,
                    user,
                    habit_page.refresh,
                    show_card=False,
                    collapsible=True,
                    collapsed_by_default=True
                )

                # Habit Details Section (show note and URL if they exist)
                if habit.note or habit.url:
                    with card():
                        card_title(t("habits.details"), "#")
                        ui.space().classes("h-2")

                        if habit.note:
                            with ui.column().classes("w-full gap-1"):
                                ui.label(t("habits.note_label")).classes("text-sm font-semibold")
                                ui.label(habit.note).classes("text-sm whitespace-pre-wrap")

                        if habit.url:
                            with ui.column().classes("w-full gap-1 mt-2"):
                                ui.label(t("habits.url_label")).classes("text-sm font-semibold")
                                ui.link(habit.url, habit.url, new_tab=True).classes("text-sm text-blue-600 underline")

                with card():
                    HabitDateInput(today, habit)

                with card():
                    card_title("Last 3 Months", target)
                    ui.space().classes("h-1")
                    with ui.element('div').classes('overflow-x-auto w-full'):
                        await habit_heat_map(habit, habit_calendar)

                with card():
                    card_title("History", target)
                    await habit_history(habit, today)

            if notes:
                with grid():
                    with card(padding=2):
                        card_title("Notes", "#").tooltip(
                            "Press and hold to add notes/descriptions"
                        )
                        habit_notes(notes)

            with card(target, padding=0.5):
                ui.icon("more_horiz", size="1.5em")


async def habit_page_ui(today: datetime.date, habit: Habit, user: User | None = None):
    ui.add_css(CHECK_BOX_CSS)
    ui.add_css(CALENDAR_CSS)
    ui.add_css(EXPANSION_CSS)
    ui.add_css(HIDE_TIMELINE_TITLE)

    async with layout(title=habit.name, user=user):
        await habit_page(today, habit, user)
