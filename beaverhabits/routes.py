from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from nicegui import app, ui, context, Client

from beaverhabits.frontend.import_page import import_ui_page
from beaverhabits.frontend.layout import custom_header, redirect
from beaverhabits.frontend.order_page import order_page_ui
from beaverhabits.logging import logger

from . import const, views
from .app.auth import (
    user_authenticate,
    user_create_token,
)
from .app.crud import get_user_count, get_user_habits, get_user_lists
from .app.db import User
from .app.dependencies import current_active_user, current_active_user_optional
from .app.users import UserManager, get_user_manager # Added UserManager, get_user_manager
from .configs import settings
from .frontend.add_page import add_page_ui
from .frontend.edit_page import edit_page_ui
from .frontend.cal_heatmap_page import heatmap_page
from .frontend.habit_page import habit_page_ui
from .frontend.index_page import index_page_ui
from .frontend.lists_page import lists_page_ui
from .frontend.change_password_page import change_password_ui
from .frontend.settings_page import settings_page_ui
from .frontend.verify_email_page import verify_email_page_ui
from .frontend.forgot_password_page import forgot_password_page_ui, password_reset_success_page_ui
from .frontend.reset_password_page import reset_password_page_ui
from .utils import get_display_days, get_user_today_date, reset_week_offset, is_navigating, set_navigating
from .services.i18n import t

UNRESTRICTED_PAGE_ROUTES = ("/login", "/register", "/gui/verify-email", "/gui/verify", "/gui/forgot-password", "/gui/reset-password")


def get_current_list_id() -> int | str | None:
    """Get current list ID from storage."""
    try:
        stored_id = app.storage.user.get("current_list")
        logger.info(f"Using list ID from storage: {stored_id!r}")
        return stored_id
    except Exception as e:
        logger.error(f"Error getting list ID from storage: {str(e)}")
        return None


@ui.page("/")
async def root_redirect() -> None:
    """Redirects the root path '/' to '/gui'."""
    logger.info("Redirecting from / to /gui")
    ui.navigate.to('/gui')


@ui.page("/gui/lists")
async def lists_page(user: User = Depends(current_active_user)) -> None:
    lists = await get_user_lists(user)
    await lists_page_ui(lists, user)


@ui.page("/gui")
async def index_page(
    request: Request,
    user: User = Depends(current_active_user),
) -> None:
    # Reset to current week only if not navigating
    if not is_navigating():
        reset_week_offset()
    else:
        set_navigating(False)  # Clear navigation flag
    days = await get_display_days()
    
    # Extract list parameter directly from request
    list_param = request.query_params.get("list")
    logger.info(f"Index page - List parameter from request: {list_param!r}")
    
    # Store list ID for persistence if it's a valid integer
    if list_param and list_param.isdigit():
        list_id = int(list_param)
        app.storage.user.update({"current_list": list_id})
    
    # Handle different list parameter types (case-insensitive)
    current_list_id = None
    if list_param and list_param.lower() == "none":
        # For "None" (no list), get all habits and filter to show only those with no list
        habits = await get_user_habits(user)
        habits = [h for h in habits if h.list_id is None]
        current_list_id = "None"
        logger.info(f"Index page - Showing {len(habits)} habits with no list")
    elif list_param and list_param.isdigit():
        # For specific list ID, filter at database level
        list_id = int(list_param)
        habits = await get_user_habits(user, list_id)
        current_list_id = list_id
        logger.info(f"Index page - Showing {len(habits)} habits from list {list_id}")
    else:
        # Default case (no filter) or invalid list parameter
        habits = await get_user_habits(user)
        logger.info(f"Index page - Showing all {len(habits)} habits")
    
    # Pass the current list ID to the UI
    await index_page_ui(days, habits, user, current_list_id)


@ui.page("/gui/add")
async def add_page(user: User = Depends(current_active_user)) -> None:
    await add_page_ui(user)

@ui.page("/gui/edit")
async def edit_page(user: User = Depends(current_active_user)) -> None:
    # Get all habits for editing
    habits = await get_user_habits(user)
    await edit_page_ui(habits, user)


@ui.page("/gui/order")
async def order_page(
    request: Request,
    user: User = Depends(current_active_user)
) -> None:
    # Extract list parameter directly from request
    list_param = request.query_params.get("list")
    logger.info(f"Order page - List parameter from request: {list_param!r}")
    
    # Store list ID for persistence if it's a valid integer
    if list_param and list_param.isdigit():
        list_id = int(list_param)
        app.storage.user.update({"current_list": list_id})
    
    # Handle different list parameter types (case-insensitive)
    current_list_id = None
    if list_param and list_param.lower() == "none":
        # For "None" (no list), get all habits and filter to show only those with no list
        habits = await get_user_habits(user)
        habits = [h for h in habits if h.list_id is None]
        current_list_id = "None"
        logger.info(f"Order page - Showing {len(habits)} habits with no list")
    elif list_param and list_param.isdigit():
        # For specific list ID, filter at database level
        list_id = int(list_param)
        habits = await get_user_habits(user, list_id)
        current_list_id = list_id
        logger.info(f"Order page - Showing {len(habits)} habits from list {list_id}")
    else:
        # Default case (no filter) or invalid list parameter
        habits = await get_user_habits(user)
        logger.info(f"Order page - Showing all {len(habits)} habits")
    
    # Pass the current list ID to the UI
    await order_page_ui(habits, user, current_list_id)


@ui.page("/gui/habits/{habit_id}")
async def habit_page(habit_id: str, user: User = Depends(current_active_user)) -> Optional[RedirectResponse]:
    today = await get_user_today_date()
    habit = await views.get_user_habit(user, habit_id)
    if habit is None:
        ui.notify(t("habits.habit_not_found", habit_id=habit_id), color="negative")
        return RedirectResponse("/gui")
    await habit_page_ui(today, habit, user)


@ui.page("/gui/habits/{habit_id}/streak")
@ui.page("/gui/habits/{habit_id}/heatmap")
async def gui_habit_page_heatmap(
    habit_id: str, user: User = Depends(current_active_user)
) -> Optional[RedirectResponse]:
    habit = await views.get_user_habit(user, habit_id)
    if habit is None:
        ui.notify(t("habits.habit_not_found", habit_id=habit_id), color="negative")
        return RedirectResponse("/gui")
    today = await get_user_today_date()
    await heatmap_page(today, habit, user)


@ui.page("/gui/export")
async def gui_export(user: User = Depends(current_active_user)) -> None:
    habits = await get_user_habits(user)
    if not habits:
        ui.notify(t("export.no_habits"), color="negative")
        return
    await views.export_user_habits(habits, user, user.email)


@ui.page("/gui/import")
async def gui_import(user: User = Depends(current_active_user)) -> None:
    await import_ui_page(user)


@ui.page("/gui/settings", title="Settings")
async def show_settings_page(user: User = Depends(current_active_user), user_manager: UserManager = Depends(get_user_manager)):
    """Settings page."""
    await settings_page_ui(user=user, user_manager=user_manager)


@ui.page("/gui/change-password", title="Change Password")
async def show_change_password_page(user: User = Depends(current_active_user), user_manager: UserManager = Depends(get_user_manager)): # Added user_manager dependency
    # Assuming custom_header() is a function that sets up common page layout/header
    # If it's not defined or used elsewhere, this line can be omitted or replaced
    # with specific layout components if needed.
    # For now, let's assume it exists as per the plan.
    # If custom_header() is not available, the subtask should proceed without it,
    # and we can adjust later if layout is missing.
    try:
        custom_header() # Removed await
    except NameError:
        # If custom_header is not defined, we can skip it for now.
        # Or add a simple ui.header if that's the pattern.
        # For this subtask, let's assume it might not be present and proceed.
        pass # Or ui.header().classes('justify-between items-center') etc.

    # Pass the user object to the UI function if it needs user context,
    # e.g., for displaying user information or using user_id directly.
    # The change_password_ui function was defined to accept an optional user_id.
    # We pass user_manager and user.id here.
    await change_password_ui(user_manager=user_manager, user_id=user.id)


@ui.page("/gui/verify-email", title="Verify Email")
async def verify_email_page(request: Request, user: Optional[User] = Depends(current_active_user_optional)):
    """Email verification status page."""
    # Check for verification status from query parameters
    status = request.query_params.get("status", "pending")
    
    await verify_email_page_ui(user=user, verification_status=status)


@ui.page("/gui/forgot-password", title="Forgot Password")
async def forgot_password_page():
    """Forgot password request page."""
    await forgot_password_page_ui()


@ui.page("/gui/reset-password", title="Reset Password")
async def reset_password_page(request: Request):
    """Password reset page."""
    await reset_password_page_ui(request)


@ui.page("/gui/verify", title="Email Verification")
async def gui_verify_email(request: Request):
    """GUI verification handler that processes the verification token."""
    import httpx
    
    # Get token from query parameters
    token = request.query_params.get("token")
    
    if not token:
        # No token provided - redirect to error page
        ui.navigate.to("/gui/verify-email?status=error")
        return
    
    try:
        # Call the FastAPI-Users verify endpoint internally
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.ROOT_URL}/auth/verify",
                json={"token": token}
            )
            
            if response.status_code == 200:
                # Verification successful
                ui.navigate.to("/gui/verify-email?status=success")
            else:
                # Verification failed (expired, invalid token, etc.)
                logger.warning(f"Email verification failed with status {response.status_code}: {response.text}")
                ui.navigate.to("/gui/verify-email?status=error")
                
    except Exception as e:
        logger.error(f"Error during email verification: {str(e)}")
        ui.navigate.to("/gui/verify-email?status=error")


@ui.page("/login")
async def login_page() -> Optional[RedirectResponse]:
    from beaverhabits.services.i18n import init_user_language
    from beaverhabits.frontend.components import auth_language_switcher
    
    # Initialize user language before any UI
    init_user_language()
    
    custom_header()
    if await views.is_gui_authenticated():
        return RedirectResponse("/gui")
    
    # Add language switcher in top-right corner
    with ui.row().classes("fixed top-4 right-4 z-50"):
        auth_language_switcher()

    # Pre-fill email if remembered
    remembered_email = app.storage.user.get("remembered_email")
    remembered_flag = app.storage.user.get("remember_me", False)

    with ui.column().classes("w-full max-w-md mx-auto mt-16 gap-6"):
        with ui.card().classes("w-full p-8"):
            ui.label(t("auth.login_title")).classes("text-2xl font-bold text-center mb-6")
            
            email = ui.input(t("auth.email"), value=remembered_email or "").props("outlined dense").classes("w-full")
            password = ui.input(t("auth.password"), password=True, password_toggle_button=True).props("outlined dense").classes("w-full")
            remember_me = ui.checkbox(t("auth.remember_me"), value=remembered_flag).classes("mt-2")
            
            loading = {"state": False}  # Use dict to allow mutation in closure
            
            async def try_login():
                if loading["state"]:  # Prevent double submission
                    return
                loading["state"] = True
                login_btn.disable()
                login_btn.text = "Logging in..."
                login_btn.props("loading")
                await ui.run_javascript('setTimeout(() => {}, 10)')  # Force UI update
                
                try:
                    user = await user_authenticate(email=email.value, password=password.value)
                    token = user and await user_create_token(user)
                    if token is not None:
                        # Check if email verification is required and user is not verified
                        if settings.REQUIRE_VERIFICATION and user and not user.is_verified:
                            ui.notify(t("auth.verify_email_before_login"), color="warning", timeout=8000)
                            ui.navigate.to("/gui/verify-email")
                            loading["state"] = False
                            login_btn.enable()
                            login_btn.text = t("auth.continue")
                            login_btn.props(remove="loading")
                            return
                        
                        app.storage.user.update({"auth_token": token})
                        if remember_me.value:
                            app.storage.user.update({"remembered_email": email.value, "remember_me": True})
                        else:
                            app.storage.user.update({"remembered_email": None, "remember_me": False})
                        ui.navigate.to("/gui")
                    else:
                        ui.notify(t("auth.invalid_credentials"), color="negative")
                        loading["state"] = False
                        login_btn.enable()
                        login_btn.text = t("auth.continue")
                        login_btn.props(remove="loading")
                except Exception as e:
                    ui.notify(t("auth.invalid_credentials"), color="negative")
                    loading["state"] = False
                    login_btn.enable()
                    login_btn.text = t("auth.continue")
                    login_btn.props(remove="loading")
            
            email.on("keydown.enter", lambda: ui.timer(0.01, try_login, once=True))
            password.on("keydown.enter", lambda: ui.timer(0.01, try_login, once=True))
            
            login_btn = ui.button(t("auth.continue"), on_click=lambda: ui.timer(0.01, try_login, once=True)).props("flat").classes("w-full bg-blue-500 text-white py-3 rounded-lg mt-4")

            # Forgot password link
            with ui.row().classes("w-full justify-center mt-4"):
                ui.link(t("auth.forgot_password"), target="/gui/forgot-password").classes("text-blue-500 hover:underline")

            if not await get_user_count() >= settings.MAX_USER_COUNT > 0:
                ui.separator().classes("mt-6")
                with ui.row().classes("w-full justify-center gap-1 mt-4"):
                    ui.label(t("auth.new_here"))
                    ui.link(t("auth.create_account"), target="/register").classes("text-blue-500 hover:underline")


@ui.page("/register")
async def register_page():
    from beaverhabits.services.i18n import init_user_language
    from beaverhabits.frontend.components import auth_language_switcher
    
    # Initialize user language before any UI
    init_user_language()
    
    custom_header()
    if await views.is_gui_authenticated():
        return RedirectResponse("/gui")
    
    # Add language switcher in top-right corner
    with ui.row().classes("fixed top-4 right-4 z-50"):
        auth_language_switcher()

    await views.validate_max_user_count()
    with ui.column().classes("w-full max-w-md mx-auto mt-16 gap-6"):
        with ui.card().classes("w-full p-8"):
            ui.label(t("auth.register_title")).classes("text-2xl font-bold text-center mb-6")
            
            email = ui.input(t("auth.email")).props("outlined dense").classes("w-full")
            password = ui.input(t("auth.password"), password=True, password_toggle_button=True).props("outlined dense").classes("w-full")

            loading = {"state": False}  # Use dict to allow mutation in closure

            async def try_register():
                if loading["state"]:  # Prevent double submission
                    return
                loading["state"] = True
                register_btn.disable()
                register_btn.text = "Creating account..."
                register_btn.props("loading")
                await ui.run_javascript('setTimeout(() => {}, 10)')  # Force UI update
                
                try:
                    await views.validate_max_user_count()
                    user = await views.register_user(email=email.value, password=password.value)
                    
                    if settings.REQUIRE_VERIFICATION:
                        # Don't log user in immediately - redirect to verification page with confirmation
                        ui.notify(t("auth.registration_successful_verify"), color="positive", timeout=8000)
                        ui.navigate.to("/gui/verify-email?status=pending")
                    else:
                        # If verification not required, log user in as before
                        await views.login_user(user)
                        ui.navigate.to("/gui")
                except Exception as e:
                    ui.notify(str(e), color="negative")
                    loading["state"] = False
                    register_btn.enable()
                    register_btn.text = t("auth.register")
                    register_btn.props(remove="loading")
            
            email.on("keydown.enter", lambda: ui.timer(0.01, try_register, once=True))
            password.on("keydown.enter", lambda: ui.timer(0.01, try_register, once=True))

            register_btn = ui.button(t("auth.register"), on_click=lambda: ui.timer(0.01, try_register, once=True)).props("flat").classes("w-full bg-green-500 text-white py-3 rounded-lg mt-4")

            ui.separator().classes("mt-6")
            with ui.row().classes("w-full justify-center gap-1 mt-4"):
                ui.label(t("auth.already_have_account"))
                ui.link(t("auth.log_in"), target="/login").classes("text-blue-500 hover:underline")



def init_gui_routes(fastapi_app: FastAPI):
    def handle_exception(exception: Exception):
        if isinstance(exception, HTTPException):
            if exception.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                ui.notify(t("general.error_occurred", error=exception), type="negative")

    @app.middleware("http")
    async def AuthMiddleware(request: Request, call_next):
        auth_token = app.storage.user.get("auth_token")
        if auth_token:
            # Remove original authorization header
            request.scope["headers"] = [
                e for e in request.scope["headers"] if e[0] != b"authorization"
            ]
            # add new authorization header
            request.scope["headers"].append(
                (b"authorization", f"Bearer {auth_token}".encode())
            )

        response = await call_next(request)
        if response.status_code == 401:
            root_path = request.scope["root_path"]
            app.storage.user["referrer_path"] = request.url.path.removeprefix(root_path)
            return RedirectResponse(request.url_for(login_page.__name__))

        return response

    app.add_static_files("/statics", "statics")
    app.on_exception(handle_exception)
    ui.run_with(
        fastapi_app,
        title=const.PAGE_TITLE,
        storage_secret=settings.NICEGUI_STORAGE_SECRET,
        favicon="statics/images/favicon.ico",
        dark=True,
    )
