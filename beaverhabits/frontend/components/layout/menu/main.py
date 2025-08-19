from nicegui import ui, context

from beaverhabits.app.auth import user_logout
from beaverhabits.frontend.components import compat_menu
from beaverhabits.frontend.components.layout.utils.navigation import redirect, open_tab
from beaverhabits.services.i18n import t
from .language import settings_menu_item

def menu_component() -> None:
    """Dropdown menu for the top-right corner of the page."""
    with ui.menu():
        show_import = True
        show_export = True

        path = context.client.page.path
        compat_menu(t("navigation.add_habits"), lambda: redirect("add"))
        compat_menu(t("navigation.edit_habits"), lambda: redirect("edit"))
        if "edit" in path:
            compat_menu(t("navigation.reorder"), lambda: redirect("order"))
        ui.separator()

        compat_menu(t("navigation.configure_lists"), lambda: redirect("lists"))
        ui.separator()

        if show_export:
            compat_menu(t("navigation.export"), lambda: open_tab("export"))
            # ui.separator() # Keep separator logic clean, maybe group user settings
        if show_import:
            compat_menu(t("navigation.import"), lambda: redirect("import"))

        # Adding Settings link here
        ui.separator() # Separator before user-specific actions
        
        # Settings menu item (navigates to settings page)
        settings_menu_item()
        ui.separator()

        compat_menu(t("navigation.logout"), lambda: user_logout() and ui.navigate.to("/login"))
