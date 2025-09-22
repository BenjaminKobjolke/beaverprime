"""
Back button component for navigation.
"""

from nicegui import ui
from beaverhabits.frontend import icons


def back_button():
    """Create a back button that navigates to the previous page using browser history."""

    # JavaScript function to go back in browser history
    back_script = """
    function goBack() {
        if (window.history.length > 1) {
            window.history.back();
        } else {
            // Fallback to home page if no history
            window.location.href = '/gui';
        }
    }
    """

    # Add the script to the page
    ui.add_head_html(f'<script>{back_script}</script>')

    # Create the back button
    button = ui.button(icon=icons.ARROW_BACK)
    button.props('flat round')
    button.classes('text-primary')
    button.on('click', lambda: ui.run_javascript('goBack()'))

    return button