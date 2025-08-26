from nicegui import ui, events
import uuid
import json
from datetime import datetime

from beaverhabits.frontend.layout import layout
from beaverhabits.frontend.components import grid
from beaverhabits.app.db import User
from beaverhabits.app.users import change_user_password, UserManager
from beaverhabits.app.crud import (
    get_user_habits, get_user_lists, create_list, create_habit, toggle_habit_check, update_habit, update_list,
    delete_all_user_habits, delete_all_user_lists
)
from beaverhabits import views
from beaverhabits.services.i18n import (
    t,
    get_available_languages,
    get_language_display_names,
    get_current_language,
    set_user_language,
    init_user_language
)
from beaverhabits.services.display_settings_service import (
    get_display_settings,
    save_display_settings,
    get_font_size_css,
    init_display_settings
)
from beaverhabits.logging import logger
from beaverhabits.configs import settings
from fastapi_users.exceptions import InvalidPasswordException


async def settings_page_ui(user: User, user_manager: UserManager):
    """Settings page UI."""
    # Initialize user language and display settings before any UI
    init_user_language()
    init_display_settings()
    
    # Add font size CSS to the page
    ui.add_head_html(f'<style id="font-size-styles">{get_font_size_css()}</style>')
    
    async with layout(user=user):
        with ui.column().classes("w-full max-w-2xl mx-auto gap-6"):
            # Language Settings Section
            with ui.card().classes("w-full p-6"):
                ui.label(t("settings.language_section")).classes("text-xl font-semibold mb-4")
                
                # Get language data
                available_languages = get_available_languages()
                language_names = get_language_display_names()
                current_language_code = get_current_language()
                
                # Language selection
                if len(available_languages) > 1:
                    ui.label(t("settings.select_language")).classes("text-sm text-gray-600 mb-2")
                    
                    with ui.column().classes("w-full gap-2"):
                        for lang_code in available_languages:
                            lang_name = language_names.get(lang_code, lang_code.upper())
                            is_current = lang_code == current_language_code
                            
                            # Create button for each language
                            button_classes = "w-full justify-start px-4 py-2 rounded-lg"
                            if is_current:
                                button_classes += " bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200"
                            else:
                                button_classes += " hover:bg-gray-100 dark:hover:bg-gray-800"
                            
                            async def handle_language_change(language_code=lang_code, language_name=lang_name):
                                """Handle language selection."""
                                logger.info(f"Settings page - switching to: {language_code} ({language_name})")
                                success = set_user_language(language_code)
                                if success:
                                    # Reload the page to apply the new language
                                    # Note: We don't show notification here to avoid translation issues during language switch
                                    ui.navigate.reload()
                                else:
                                    ui.notify(f"Failed to change language to {language_name}", color="negative")
                            
                            ui.button(
                                f"{'✓ ' if is_current else '   '}{lang_name}",
                                on_click=handle_language_change
                            ).classes(button_classes).props("flat")
                else:
                    ui.label(t("settings.only_one_language")).classes("text-sm text-gray-500")
            
            # Change Password Section
            with ui.card().classes("w-full p-6"):
                ui.label(t("navigation.change_password")).classes("text-xl font-semibold mb-4")
                
                # Password change form
                with ui.column().classes("w-full gap-4"):
                    old_password_input = ui.input(
                        label=t("auth.old_password"), 
                        password=True, 
                        password_toggle_button=True
                    ).props("outlined").classes("w-full")
                    
                    new_password_input = ui.input(
                        label=t("auth.new_password"), 
                        password=True, 
                        password_toggle_button=True
                    ).props("outlined").classes("w-full")
                    
                    confirm_password_input = ui.input(
                        label=t("auth.confirm_new_password"), 
                        password=True, 
                        password_toggle_button=True
                    ).props("outlined").classes("w-full")
                    
                    async def handle_password_change():
                        """Handle password change."""
                        old_pw = old_password_input.value
                        new_pw = new_password_input.value
                        confirm_pw = confirm_password_input.value

                        if not old_pw or not new_pw or not confirm_pw:
                            ui.notify(t("auth.all_fields_required"), color="negative")
                            return

                        if new_pw != confirm_pw:
                            ui.notify(t("auth.passwords_no_match"), color="negative")
                            return

                        try:
                            success = await change_user_password(
                                user_manager=user_manager, 
                                user_id=user.id, 
                                old_password=old_pw, 
                                new_password=new_pw
                            )

                            if success:
                                ui.notify(t("auth.password_changed_successfully"), color="positive")
                                old_password_input.set_value("")
                                new_password_input.set_value("")
                                confirm_password_input.set_value("")
                            else:
                                ui.notify(t("auth.password_change_failed"), color="negative")

                        except InvalidPasswordException:
                            ui.notify(t("auth.incorrect_old_password"), color="negative")
                        except Exception as e:
                            detail = getattr(e, 'detail', str(e))
                            ui.notify(t("auth.error_occurred", detail=detail), color="negative")
                    
                    ui.button(
                        t("auth.change_password_button"), 
                        on_click=handle_password_change
                    ).classes("bg-blue-500 text-white px-6 py-2 rounded-lg")
            
            # Display Settings Section
            with ui.card().classes("w-full p-6"):
                ui.label(t("settings.display_section")).classes("text-xl font-semibold mb-4")
                
                # Get current settings
                current_settings = get_display_settings()
                print(f"[SETTINGS] Current display settings: {current_settings}")
                
                with ui.column().classes("w-full gap-4"):
                    # Consecutive weeks toggle
                    consecutive_weeks_checkbox = ui.checkbox(
                        t("settings.show_consecutive_weeks"), 
                        value=current_settings["show_consecutive_weeks"]
                    ).classes("mb-2")
                    ui.label(t("settings.consecutive_weeks_description")).classes("text-sm text-gray-600 ml-6")
                    
                    ui.separator().classes("my-4")
                    
                    # Font size controls
                    ui.label(t("settings.font_size_label")).classes("text-lg font-medium")
                    ui.label(t("settings.font_size_description")).classes("text-sm text-gray-600 mb-4")
                    
                    with ui.column().classes("w-full gap-3"):
                        # Font size slider
                        font_size_slider = ui.slider(
                            min=1.0, 
                            max=3.0, 
                            step=0.1, 
                            value=current_settings["font_size"]
                        ).props("label-always")
                        
                        # Font size labels row
                        with ui.row().classes("w-full justify-between text-xs text-gray-500"):
                            ui.label(t("settings.font_size_small"))
                            ui.label(t("settings.font_size_normal"))
                            ui.label(t("settings.font_size_large"))
                        
                        ui.separator().classes("my-4")
                        
                        # Save button and status
                        with ui.row().classes("w-full justify-between items-center"):
                            save_button = ui.button(
                                "Save Display Settings", 
                                color="primary"
                            ).classes("px-6 py-2")
                            
                            status_label = ui.label("").classes("text-sm text-gray-600")
                        
                        def check_for_changes(current_font_size=None, current_checkbox=None):
                            """Check if settings have changed and update button state."""
                            try:
                                # Use provided values or get from components
                                if current_font_size is None:
                                    current_font_size = font_size_slider.value
                                if current_checkbox is None:
                                    current_checkbox = consecutive_weeks_checkbox.value
                                
                                print(f"[SETTINGS] Checking for changes...")
                                print(f"[SETTINGS] Current font size: {current_font_size}")
                                print(f"[SETTINGS] Original font size: {current_settings['font_size']}")
                                print(f"[SETTINGS] Current checkbox: {current_checkbox}")
                                print(f"[SETTINGS] Original checkbox: {current_settings['show_consecutive_weeks']}")
                                
                                font_size_changed = current_font_size != current_settings["font_size"]
                                checkbox_changed = current_checkbox != current_settings["show_consecutive_weeks"]
                                
                                print(f"[SETTINGS] Font size changed: {font_size_changed}")
                                print(f"[SETTINGS] Checkbox changed: {checkbox_changed}")
                                
                                has_changes = font_size_changed or checkbox_changed
                                print(f"[SETTINGS] Has changes: {has_changes}")
                                
                                if has_changes:
                                    print(f"[SETTINGS] Enabling save button")
                                    save_button.props("color=primary")
                                    save_button.text = "Save Changes"
                                    save_button.enable()
                                    status_label.text = "Changes not saved"
                                    status_label.classes("text-sm text-orange-600")
                                else:
                                    print(f"[SETTINGS] Disabling save button")
                                    save_button.props("color=grey")
                                    save_button.text = "No Changes"
                                    save_button.disable()
                                    status_label.text = "All changes saved"
                                    status_label.classes("text-sm text-green-600")
                            except Exception as e:
                                print(f"[SETTINGS] Error checking changes: {e}")
                                import traceback
                                traceback.print_exc()
                        
                        async def handle_save_settings():
                            """Save display settings."""
                            try:
                                new_settings = {
                                    "font_size": font_size_slider.value,
                                    "show_consecutive_weeks": consecutive_weeks_checkbox.value
                                }
                                
                                print(f"[SETTINGS] Attempting to save: {new_settings}")
                                
                                success = save_display_settings(new_settings)
                                
                                if success:
                                    # Update CSS immediately
                                    new_css = get_font_size_css()
                                    ui.run_javascript(f'''
                                        let styleTag = document.getElementById('font-size-styles');
                                        if (styleTag) {{
                                            styleTag.textContent = `{new_css}`;
                                        }}
                                    ''')
                                    
                                    # Update current_settings to new values
                                    nonlocal current_settings
                                    current_settings = new_settings.copy()
                                    
                                    # Update UI state
                                    save_button.props("color=green")
                                    save_button.text = "Saved ✓"
                                    save_button.disable()
                                    status_label.text = "Settings saved successfully"
                                    status_label.classes("text-sm text-green-600")
                                    
                                    ui.notify("Display settings saved successfully!", color="positive")
                                    logger.info(f"Display settings saved: {new_settings}")
                                else:
                                    ui.notify("Failed to save display settings", color="negative")
                                    logger.error(f"Failed to save display settings: {new_settings}")
                                    
                            except Exception as e:
                                print(f"[SETTINGS] Error saving settings: {e}")
                                ui.notify("Error saving settings", color="negative")
                                logger.error(f"Error saving display settings: {e}")
                        
                        # Set up event handlers with debugging
                        def on_font_size_change(e):
                            try:
                                print(f"[SETTINGS] Font size slider event received!")
                                print(f"[SETTINGS] Event type: {type(e)}")
                                print(f"[SETTINGS] Event attributes: {dir(e)}")
                                print(f"[SETTINGS] Event args: {e.args if hasattr(e, 'args') else 'No args'}")
                                
                                # Try different ways to get the value
                                slider_value = None
                                if hasattr(e, 'value'):
                                    slider_value = e.value
                                elif hasattr(e, 'args') and e.args:
                                    slider_value = e.args.get('value') if isinstance(e.args, dict) else None
                                else:
                                    # Fallback to component value
                                    slider_value = font_size_slider.value
                                
                                print(f"[SETTINGS] Font size slider value: {slider_value}")
                                check_for_changes(current_font_size=slider_value)
                            except Exception as ex:
                                print(f"[SETTINGS] Error in font size change handler: {ex}")
                                import traceback
                                traceback.print_exc()
                        
                        def on_checkbox_change(e):
                            try:
                                print(f"[SETTINGS] Checkbox event received!")
                                print(f"[SETTINGS] Event type: {type(e)}")
                                print(f"[SETTINGS] Event attributes: {dir(e)}")
                                print(f"[SETTINGS] Event args: {e.args if hasattr(e, 'args') else 'No args'}")
                                
                                # Try different ways to get the value
                                checkbox_value = None
                                if hasattr(e, 'value'):
                                    checkbox_value = e.value
                                elif hasattr(e, 'args') and e.args:
                                    checkbox_value = e.args.get('value') if isinstance(e.args, dict) else None
                                else:
                                    # Fallback to component value
                                    checkbox_value = consecutive_weeks_checkbox.value
                                
                                print(f"[SETTINGS] Checkbox value: {checkbox_value}")
                                check_for_changes(current_checkbox=checkbox_value)
                            except Exception as ex:
                                print(f"[SETTINGS] Error in checkbox change handler: {ex}")
                                import traceback
                                traceback.print_exc()
                        
                        print(f"[SETTINGS] Setting up event handlers with correct syntax")
                        # Use correct NiceGUI event syntax
                        # Try both 'change' and 'input' for slider to ensure it works
                        font_size_slider.on("change", on_font_size_change)
                        font_size_slider.on("input", on_font_size_change)  # Fallback for continuous updates
                        
                        # For checkbox, try multiple event types
                        consecutive_weeks_checkbox.on("change", on_checkbox_change)
                        consecutive_weeks_checkbox.on("click", lambda e: print(f"[SETTINGS] Checkbox clicked!"))
                        consecutive_weeks_checkbox.on("input", on_checkbox_change)  # Alternative event type
                        
                        save_button.on_click(handle_save_settings)
                        
                        # Fallback: periodic check for changes in case events don't work
                        def periodic_check():
                            print(f"[SETTINGS] Periodic check triggered")
                            check_for_changes()
                        
                        # Set up a timer that checks every 500ms as fallback
                        ui.timer(0.5, periodic_check)
                        
                        # Initial state check
                        print(f"[SETTINGS] Doing initial state check")
                        check_for_changes()
            
            # Data Management Section
            with ui.card().classes("w-full p-6"):
                ui.label("Data Management").classes("text-xl font-semibold mb-4")
                
                # Export section
                with ui.column().classes("w-full gap-4"):
                    ui.label("Export Data").classes("text-lg font-medium")
                    ui.label("Export all your habits and their completion history as a JSON file.").classes("text-sm text-gray-600")
                    
                    async def handle_export():
                        """Handle data export."""
                        try:
                            habits = await get_user_habits(user)
                            if not habits:
                                ui.notify("No habits to export", color="negative")
                                return
                            await views.export_user_habits(habits, user, user.email)
                            ui.notify("Data exported successfully", color="positive")
                        except Exception as e:
                            logger.error(f"Export failed: {e}")
                            ui.notify(f"Export failed: {str(e)}", color="negative")
                    
                    ui.button(
                        "Export Data", 
                        on_click=handle_export
                    ).classes("bg-green-500 text-white px-6 py-2 rounded-lg")
                    
                    ui.separator().classes("my-4")
                    
                    # Import section
                    ui.label("Import Data").classes("text-lg font-medium")
                    ui.label("Import habits from a JSON file.").classes("text-sm text-gray-600")
                    
                    # Clear data option
                    clear_existing_checkbox = ui.checkbox(
                        "Clear existing habits and lists before import (otherwise habits and lists with same names will be merged, and habits and lists with different names will be added)"
                    ).classes("mb-2")
                    
                    async def handle_import(e: events.UploadEventArguments):
                        """Handle data import."""
                        try:
                            text = e.content.read().decode("utf-8")
                            if not e.name.endswith(".json"):
                                ui.notify("Please upload a JSON file", color="negative")
                                return
                            
                            # Parse JSON data
                            data = json.loads(text)
                            if not data.get("habits"):
                                ui.notify("No habits found in file", color="negative")
                                return
                            
                            habits_data = data["habits"]
                            
                            # Check if user wants to clear existing data
                            clear_existing = clear_existing_checkbox.value
                            deleted_habits_count = 0
                            deleted_lists_count = 0
                            
                            if clear_existing:
                                # Clear existing habits and lists using bulk delete functions
                                deleted_habits_count = await delete_all_user_habits(user)
                                deleted_lists_count = await delete_all_user_lists(user)
                                
                                # All habits are now "new" since we cleared existing ones
                                new_habits = habits_data
                                merge_habits = []
                            else:
                                # Get existing habits for merging
                                existing_habits = await get_user_habits(user)
                                existing_names = {h.name for h in existing_habits}

                                # Separate new and existing habits
                                new_habits = [h for h in habits_data if h["name"] not in existing_names]
                                merge_habits = [h for h in habits_data if h["name"] in existing_names]
                            
                            # Import lists if they exist in the data
                            imported_lists = {}
                            if data.get("lists"):
                                for list_data in data["lists"]:
                                    imported_list = await create_list(user, list_data["name"])
                                    imported_lists[list_data["id"]] = imported_list.id
                            
                            # Get or create a default list for habits without a list
                            lists = await get_user_lists(user)
                            if not lists:
                                default_list = await create_list(user, "Default")
                                default_list_id = default_list.id
                            else:
                                default_list_id = lists[0].id

                            # Import new habits
                            for habit_data in new_habits:
                                # Determine which list to use
                                original_list_id = habit_data.get("list_id")
                                if original_list_id and original_list_id in imported_lists:
                                    target_list_id = imported_lists[original_list_id]
                                elif original_list_id is None:
                                    target_list_id = None  # No list
                                else:
                                    target_list_id = default_list_id  # Fallback to default
                                
                                habit = await create_habit(user, habit_data["name"], target_list_id)
                                if habit:
                                    # Import records
                                    for record in habit_data.get("records", []):
                                        day = datetime.strptime(record["day"], "%Y-%m-%d").date()
                                        if record.get("done"):
                                            await toggle_habit_check(habit.id, user.id, day)

                            # Merge existing habits
                            if not clear_existing:  # Only merge if we didn't clear existing data
                                for habit_data in merge_habits:
                                    habit = next((h for h in existing_habits if h.name == habit_data["name"]), None)
                                    if habit:
                                        # Import records
                                        for record in habit_data.get("records", []):
                                            day = datetime.strptime(record["day"], "%Y-%m-%d").date()
                                            if record.get("done"):
                                                await toggle_habit_check(habit.id, user.id, day)
                            
                            # Update success message
                            total_habits = len(new_habits) + (len(merge_habits) if not clear_existing else 0)
                            total_lists = len(data.get("lists", []))
                            
                            if clear_existing:
                                ui.notify(
                                    f"Import completed! Cleared {deleted_habits_count} existing habits and {deleted_lists_count} existing lists, imported {total_habits} habits and {total_lists} lists",
                                    color="positive"
                                )
                            else:
                                ui.notify(
                                    f"Import completed! Added {len(new_habits)} new habits, merged {len(merge_habits)} existing habits, and imported {total_lists} lists",
                                    color="positive"
                                )
                            
                        except json.JSONDecodeError:
                            ui.notify("Invalid JSON file", color="negative")
                        except Exception as e:
                            logger.error(f"Import failed: {e}")
                            ui.notify(f"Import failed: {str(e)}", color="negative")
                    
                    ui.upload(
                        on_upload=handle_import,
                        multiple=False,
                        auto_upload=True
                    ).classes("w-full").props('accept=".json"')