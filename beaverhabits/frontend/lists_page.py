from nicegui import ui

from beaverhabits import views
from beaverhabits.frontend.components import grid
from beaverhabits.frontend.layout import layout
from beaverhabits.sql.models import HabitList
from beaverhabits.app.crud import create_list, update_list, get_user_lists
from beaverhabits.app.db import User
from beaverhabits.services.i18n import t


@ui.refreshable
async def lists_ui(lists: list[HabitList], user: User | None = None):
    """Lists UI component."""
    with ui.column().classes("w-full gap-4"):
        # Add new list form
        with ui.card().classes("w-full p-4"):
            with grid(columns=8):
                new_list_input = ui.input(t("lists.new_list")).classes("col-span-6")
                
                async def add_list():
                    if not new_list_input.value:
                        ui.notify(t("lists.name_required"), color="negative")
                        return
                    try:
                        await create_list(user, new_list_input.value)
                        new_list_input.set_value("")
                        ui.notify(t("lists.added_successfully"), color="positive")
                        ui.navigate.to("/gui/lists")  # Reload the page with fresh data
                    except Exception as e:
                        ui.notify(t("lists.add_failed", error=str(e)), color="negative")
                
                ui.button(t("lists.add_button"), on_click=add_list).classes("col-span-2")

        # Existing lists
        active_lists = [l for l in lists if not l.deleted]
        active_lists.sort(key=lambda l: l.order)
        
        for list_item in active_lists:
            with ui.card().classes("w-full p-4"):
                with grid(columns=8):
                    # List name input
                    edit_input = ui.input(value=list_item.name).classes("col-span-8")
                    
                    # Letter filter checkbox
                    with ui.row().classes("col-span-8 items-center gap-2"):
                        filter_checkbox = ui.checkbox(
                            t("lists.enable_letter_filter"),
                            value=list_item.enable_letter_filter
                        )
                        
                        async def update_letter_filter(e):
                            try:
                                await update_list(list_item.id, user.id, enable_letter_filter=e.value)
                                ui.notify(t("lists.updated_successfully"), color="positive")
                            except Exception as ex:
                                ui.notify(t("lists.update_failed", error=str(ex)), color="negative")
                        
                        filter_checkbox.on("change", update_letter_filter)
                    
                    # Buttons row
                    with ui.row().classes("col-span-8 gap-2"):
                        async def update_list_name(list_id: int, input_element: ui.input, checkbox: ui.checkbox):
                            if not input_element.value:
                                ui.notify(t("lists.name_required"), color="negative")
                                return
                            try:
                                await update_list(
                                    list_id, 
                                    user.id, 
                                    name=input_element.value,
                                    enable_letter_filter=checkbox.value
                                )
                                ui.notify(t("lists.updated_successfully"), color="positive")
                                ui.navigate.to("/gui/lists")  # Reload the page with fresh data
                            except Exception as e:
                                ui.notify(t("lists.update_failed", error=str(e)), color="negative")
                        
                        async def delete_list_item(list_id: int):
                            try:
                                await update_list(list_id, user.id, deleted=True)
                                ui.notify(t("lists.deleted_successfully"), color="positive")
                                ui.navigate.to("/gui/lists")  # Reload the page with fresh data
                            except Exception as e:
                                ui.notify(t("lists.delete_failed", error=str(e)), color="negative")
                        
                        ui.button(
                            t("lists.save_button"), 
                            on_click=lambda l=list_item, i=edit_input, c=filter_checkbox: update_list_name(l.id, i, c)
                        ).props("flat")
                        ui.button(
                            t("lists.delete_button"), 
                            on_click=lambda l=list_item: delete_list_item(l.id)
                        ).props("flat")


async def lists_page_ui(lists: list[HabitList], user: User | None = None):
    """Lists management page."""
    async with layout(t("navigation.configure_lists"), user=user):
        with ui.column().classes("w-full gap-4 pb-64 px-2 md:px-4"):
            await lists_ui(lists, user)
