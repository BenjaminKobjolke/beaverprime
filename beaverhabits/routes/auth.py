"""
Authentication routes for BeaverHabits application.

Handles login, registration, password reset, and email verification routes.
"""

from typing import Optional

from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from nicegui import app, ui

from beaverhabits import views
from beaverhabits.app.auth import user_authenticate, user_create_token
from beaverhabits.app.db import User
from beaverhabits.app.crud import get_user_count
from beaverhabits.app.dependencies import current_active_user, current_active_user_optional
from beaverhabits.app.users import UserManager, get_user_manager
from beaverhabits.configs import settings
from beaverhabits.frontend.change_password_page import change_password_ui
from beaverhabits.frontend.forgot_password_page import forgot_password_page_ui
from beaverhabits.frontend.layout import custom_header
from beaverhabits.frontend.reset_password_page import reset_password_page_ui
from beaverhabits.frontend.verify_email_page import verify_email_page_ui
from beaverhabits.logging import logger
from beaverhabits.services.i18n import t


@ui.page("/login")
async def login_page() -> Optional[RedirectResponse]:
    """Login page route."""
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
    """Registration page route."""
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


@ui.page("/gui/change-password", title="Change Password")
async def show_change_password_page(
    user: User = Depends(current_active_user), 
    user_manager: UserManager = Depends(get_user_manager)
):
    """Change password page route."""
    try:
        custom_header()
    except NameError:
        pass

    await change_password_ui(user_manager=user_manager, user_id=user.id)


@ui.page("/gui/verify-email", title="Verify Email")
async def verify_email_page(
    request: Request, 
    user: Optional[User] = Depends(current_active_user_optional)
):
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


# List of auth routes for registration
auth_routes = [
    login_page,
    register_page,
    show_change_password_page,
    verify_email_page,
    forgot_password_page,
    reset_password_page,
    gui_verify_email,
]