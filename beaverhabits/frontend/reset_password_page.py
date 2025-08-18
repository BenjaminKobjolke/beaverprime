from nicegui import ui
from fastapi import Request
import httpx

from beaverhabits.frontend.layout import custom_header
from beaverhabits.configs import settings
from beaverhabits.logging import logger


async def reset_password_page_ui(request: Request):
    """Password reset page UI."""
    custom_header()
    
    # Get token from query parameters
    token = request.query_params.get("token")
    
    if not token:
        # No token provided - show error
        with ui.column().classes("w-full max-w-md mx-auto mt-16 gap-6"):
            with ui.card().classes("w-full p-8"):
                ui.icon("error", color="negative", size="3rem").classes("mx-auto")
                ui.label("Invalid Reset Link").classes("text-2xl font-bold text-center mt-4")
                ui.label("This password reset link is invalid or malformed.").classes("text-center text-gray-600 mt-2")
                
                with ui.row().classes("w-full justify-center mt-6"):
                    ui.button("Request New Reset Link", on_click=lambda: ui.navigate.to("/gui/forgot-password")).props("flat").classes("bg-blue-500 text-white px-6 py-3 rounded-lg")
        return
    
    with ui.column().classes("w-full max-w-md mx-auto mt-16 gap-6"):
        with ui.card().classes("w-full p-8"):
            ui.icon("lock_reset", color="primary", size="3rem").classes("mx-auto")
            ui.label("Reset Your Password").classes("text-2xl font-bold text-center mt-4")
            ui.label("Enter your new password below.").classes("text-center text-gray-600 mt-2 mb-6")
            
            # Password inputs
            password_input = ui.input("New Password", password=True, password_toggle_button=True).props("outlined dense").classes("w-full")
            confirm_password_input = ui.input("Confirm New Password", password=True, password_toggle_button=True).props("outlined dense").classes("w-full mt-4")
            
            # Password strength indicator
            strength_indicator = ui.row().classes("w-full mt-2")
            
            # Submit button
            submit_btn = ui.button("Reset Password", on_click=lambda: reset_password()).props("flat").classes("w-full bg-blue-500 text-white py-3 rounded-lg mt-6")
            
            # Message container
            message_container = ui.row().classes("w-full mt-4")
            
            def update_password_strength():
                """Update password strength indicator."""
                password = password_input.value or ""
                strength_indicator.clear()
                
                if len(password) < 6:
                    with strength_indicator:
                        ui.label("Password must be at least 6 characters").classes("text-red-500 text-sm")
                elif len(password) < 8:
                    with strength_indicator:
                        ui.label("Password strength: Weak").classes("text-orange-500 text-sm")
                else:
                    # Check for complexity
                    has_upper = any(c.isupper() for c in password)
                    has_lower = any(c.islower() for c in password)
                    has_digit = any(c.isdigit() for c in password)
                    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
                    
                    score = sum([has_upper, has_lower, has_digit, has_special])
                    
                    if score >= 3:
                        with strength_indicator:
                            ui.label("Password strength: Strong").classes("text-green-500 text-sm")
                    elif score >= 2:
                        with strength_indicator:
                            ui.label("Password strength: Good").classes("text-blue-500 text-sm")
                    else:
                        with strength_indicator:
                            ui.label("Password strength: Fair").classes("text-yellow-500 text-sm")
            
            password_input.on("input", lambda: update_password_strength())
            password_input.on("keydown.enter", lambda: reset_password())
            confirm_password_input.on("keydown.enter", lambda: reset_password())
            
            async def reset_password():
                """Handle password reset."""
                password = password_input.value
                confirm_password = confirm_password_input.value
                
                # Validation
                if not password or not confirm_password:
                    ui.notify("Please fill in both password fields", color="negative")
                    return
                
                if len(password) < 6:
                    ui.notify("Password must be at least 6 characters long", color="negative")
                    return
                
                if password != confirm_password:
                    ui.notify("Passwords do not match", color="negative")
                    return
                
                submit_btn.props("loading")
                
                try:
                    # Call the FastAPI-Users reset password endpoint
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            f"{settings.ROOT_URL}/auth/reset-password",
                            json={
                                "token": token,
                                "password": password
                            }
                        )
                        
                        if response.status_code == 200:
                            # Success
                            message_container.clear()
                            with message_container:
                                with ui.card().classes("w-full p-4 bg-gray-800 border-gray-600"):
                                    ui.icon("check_circle", color="positive")
                                    ui.label("Password Reset Successfully!").classes("font-semibold text-green-400")
                                    ui.label("Your password has been updated. You can now log in with your new password.").classes("text-gray-300 mt-1")
                            
                            # Disable form
                            password_input.props("readonly")
                            confirm_password_input.props("readonly")
                            submit_btn.props("disable")
                            
                            # Redirect to login after delay
                            ui.timer(3.0, lambda: ui.navigate.to("/login"), once=True)
                            
                        else:
                            # Handle error response
                            error_data = response.json()
                            if response.status_code == 400:
                                error_detail = error_data.get("detail", "Invalid or expired reset token")
                                ui.notify(f"Reset failed: {error_detail}", color="negative")
                                
                                if "expired" in error_detail.lower() or "invalid" in error_detail.lower():
                                    message_container.clear()
                                    with message_container:
                                        with ui.card().classes("w-full p-4 bg-gray-800 border-gray-600"):
                                            ui.icon("error", color="negative")
                                            ui.label("Reset Link Expired").classes("font-semibold text-red-400")
                                            ui.label("This password reset link has expired or is invalid. Please request a new one.").classes("text-gray-300 mt-1")
                                            ui.button("Request New Reset Link", 
                                                    on_click=lambda: ui.navigate.to("/gui/forgot-password")
                                                    ).props("flat").classes("bg-blue-500 text-white px-4 py-2 rounded mt-3")
                            else:
                                ui.notify("An error occurred while resetting your password", color="negative")
                                
                except Exception as e:
                    logger.error(f"Error resetting password: {str(e)}")
                    ui.notify("An error occurred while resetting your password. Please try again.", color="negative")
                    
                finally:
                    submit_btn.props(remove="loading")
            
            # Back to login link
            with ui.row().classes("w-full justify-center mt-6"):
                ui.link("← Back to Login", target="/login").classes("text-blue-500 hover:underline")