"""
Route modules for BeaverHabits application.

This package contains feature-based route modules to organize
the application's endpoints in a maintainable way.
"""

# Import route collections from submodules
from .auth import auth_routes
from .habits import habit_routes
from .lists import list_routes
from .settings import settings_routes
from .misc import misc_routes

# Import main routing functions from the config module
from .config import init_gui_routes, get_current_list_id, UNRESTRICTED_PAGE_ROUTES

__all__ = [
    'auth_routes',
    'habit_routes', 
    'list_routes',
    'settings_routes',
    'misc_routes',
    'init_gui_routes',
    'get_current_list_id',
    'UNRESTRICTED_PAGE_ROUTES',
]