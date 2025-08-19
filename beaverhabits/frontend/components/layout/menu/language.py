from beaverhabits.frontend.components import compat_menu
from beaverhabits.frontend.components.layout.utils.navigation import redirect
from beaverhabits.services.i18n import t


def settings_menu_item() -> None:
    """Create a settings menu item that navigates to settings page."""
    compat_menu(t("navigation.settings"), lambda: redirect("settings"))