from nicegui import ui

from beaverhabits.frontend.layout import layout
from beaverhabits.frontend.components import grid
from beaverhabits.app.db import User
from beaverhabits.services.i18n import (
    t,
    get_available_languages,
    get_language_display_names,
    get_current_language,
    set_user_language,
    init_user_language
)
from beaverhabits.logging import logger


async def settings_page_ui(user: User):
    """Settings page UI."""
    # Initialize user language before any UI
    init_user_language()
    
    async with layout(user=user):
        with ui.column().classes("w-full max-w-2xl mx-auto gap-6"):
            # Page title
            ui.label(t("navigation.settings")).classes("text-3xl font-bold")
            
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
                                    ui.notify(t("settings.language_changed", language=language_name), color="positive")
                                    # Reload the page to apply the new language
                                    ui.navigate.reload()
                                else:
                                    ui.notify(t("settings.language_change_failed", language=language_name), color="negative")
                            
                            ui.button(
                                f"{'✓ ' if is_current else '   '}{lang_name}",
                                on_click=handle_language_change
                            ).classes(button_classes).props("flat")
                else:
                    ui.label(t("settings.only_one_language")).classes("text-sm text-gray-500")
            
            # Future settings sections can be added here
            # with ui.card().classes("w-full"):
            #     ui.label("Other Settings").classes("text-xl font-semibold mb-4")
            #     ui.label("More settings will be added here in the future.").classes("text-gray-600")