"""
Main route configuration for BeaverHabits application.

This file serves as the central registration point for all routes,
importing from feature-based modules for better organization.
"""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from nicegui import app, ui

from beaverhabits import const
from beaverhabits.configs import settings
from beaverhabits.logging import logger
from beaverhabits.services.i18n import t

# Define which pages don't require authentication
UNRESTRICTED_PAGE_ROUTES = (
    "/login",
    "/register", 
    "/gui/verify-email",
    "/gui/verify",
    "/gui/forgot-password",
    "/gui/reset-password"
)


def init_gui_routes(fastapi_app: FastAPI):
    """
    Initialize all GUI routes and middleware for the application.
    
    This function sets up:
    - Authentication middleware
    - Exception handling
    - Static file serving
    - NiceGUI integration
    
    Args:
        fastapi_app: The FastAPI application instance
    """
    
    def handle_exception(exception: Exception):
        """Global exception handler for the GUI."""
        if isinstance(exception, HTTPException):
            if exception.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                ui.notify(t("general.error_occurred", error=exception), type="negative")

    @app.middleware("http")
    async def AuthMiddleware(request: Request, call_next):
        """
        Authentication middleware that adds Bearer token to requests.
        
        This middleware:
        - Adds authentication token from storage to request headers
        - Redirects to login page for 401 responses
        - Preserves the original path for redirect after login
        """
        auth_token = app.storage.user.get("auth_token")
        if auth_token:
            # Remove original authorization header
            request.scope["headers"] = [
                e for e in request.scope["headers"] if e[0] != b"authorization"
            ]
            # Add new authorization header
            request.scope["headers"].append(
                (b"authorization", f"Bearer {auth_token}".encode())
            )

        response = await call_next(request)
        if response.status_code == 401:
            root_path = request.scope["root_path"]
            app.storage.user["referrer_path"] = request.url.path.removeprefix(root_path)
            # Import here to avoid circular dependency
            from beaverhabits.routes.auth import login_page
            return RedirectResponse(request.url_for(login_page.__name__))

        return response

    # Add static files
    app.add_static_files("/statics", "statics")
    
    # Add exception handler
    app.on_exception(handle_exception)
    
    # Run NiceGUI with FastAPI
    ui.run_with(
        fastapi_app,
        title=const.PAGE_TITLE,
        storage_secret=settings.NICEGUI_STORAGE_SECRET,
        favicon="statics/images/favicon.ico",
        dark=True,
    )


# Helper function to get current list ID (used by habit routes)
def get_current_list_id() -> int | str | None:
    """
    Get current list ID from storage.
    
    Returns:
        The current list ID or None if not set
    """
    try:
        stored_id = app.storage.user.get("current_list")
        logger.info(f"Using list ID from storage: {stored_id!r}")
        return stored_id
    except Exception as e:
        logger.error(f"Error getting list ID from storage: {str(e)}")
        return None