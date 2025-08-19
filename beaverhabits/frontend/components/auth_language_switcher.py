from nicegui import ui
from beaverhabits.services.i18n import (
    get_available_languages, 
    get_language_display_names, 
    get_current_language, 
    set_user_language
)
from beaverhabits.logging import logger

def auth_language_switcher() -> None:
    """Language switcher for authentication pages (login, register, etc.)."""
    try:
        # Get available languages and their display names
        available_languages = get_available_languages()
        if len(available_languages) <= 1:
            # Don't show language switcher if only one language is available
            return
            
        language_names = get_language_display_names()
        current_language_code = get_current_language()
        
        # Create code-to-name mapping for available languages only
        code_to_name = {
            code: language_names.get(code, code.upper()) 
            for code in available_languages
        }
        
        # Create options list (display names)
        options = list(code_to_name.values())
        
        # Get current display name
        current_name = code_to_name.get(current_language_code, "English")
        
        logger.debug(f"Auth language switcher - available: {available_languages}, current: {current_language_code}")
        
        def handle_language_change(e):
            """Handle language selection change."""
            selected_name = e.value
            # Find the language code for the selected display name
            selected_code = next((code for code, name in code_to_name.items() if name == selected_name), None)
            
            if selected_code:
                logger.info(f"Auth language switcher - switching to: {selected_code} ({selected_name})")
                success = set_user_language(selected_code)
                if success:
                    # Reload the page to apply the new language
                    ui.navigate.reload()
                else:
                    ui.notify(f"Failed to switch to {selected_name}", color="negative")
            else:
                logger.error(f"Auth language switcher - could not find code for: {selected_name}")
        
        # Create a compact language switcher in top-right corner style
        with ui.row().classes("items-center gap-1"):
            ui.select(
                options=options,
                value=current_name,
                on_change=handle_language_change
            ).props('outlined dense').classes('w-24 text-sm').style('font-size: 12px')
            
    except Exception as e:
        logger.error(f"Auth language switcher - error creating component: {e}")
        # Fallback - show nothing if there's an error
        pass