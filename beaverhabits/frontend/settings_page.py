from nicegui import ui
import uuid

from beaverhabits.frontend.layout import layout
from beaverhabits.frontend.components import grid
from beaverhabits.app.db import User
from beaverhabits.app.users import change_user_password, UserManager
from beaverhabits.services.i18n import (
    t,
    get_available_languages,
    get_language_display_names,
    get_current_language,
    set_user_language,
    init_user_language
)
from beaverhabits.logging import logger
from fastapi_users.exceptions import InvalidPasswordException


async def settings_page_ui(user: User, user_manager: UserManager):
    """Settings page UI."""
    # Initialize user language before any UI
    init_user_language()
    
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