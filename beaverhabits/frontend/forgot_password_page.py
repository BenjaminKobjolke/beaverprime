from nicegui import ui
import httpx
from fastapi import HTTPException

from beaverhabits.frontend.layout import custom_header
from beaverhabits.configs import settings
from beaverhabits.logging import logger


async def forgot_password_page_ui():
    """Forgot password page UI."""
    custom_header()
    
    with ui.column().classes("w-full max-w-md mx-auto mt-16 gap-6"):
        with ui.card().classes("w-full p-8"):
            ui.icon("lock_reset", color="primary", size="3rem").classes("mx-auto")
            ui.label("Reset Your Password").classes("text-2xl font-bold text-center mt-4")
            ui.label("Enter your email address and we'll send you a link to reset your password.").classes("text-center text-gray-600 mt-2 mb-6")
            
            # Email input
            email_input = ui.input("Email Address", placeholder="Enter your email address").props("outlined dense").classes("w-full")
            email_input.on("keydown.enter", lambda: send_reset_email())
            
            # Submit button
            submit_btn = ui.button("Send Reset Link", on_click=lambda: send_reset_email()).props("flat").classes("w-full bg-blue-500 text-white py-3 rounded-lg mt-4")
            
            # Success/error messages
            message_container = ui.row().classes("w-full mt-4")
            
            async def send_reset_email():
                """Send password reset email."""
                if not email_input.value or not email_input.value.strip():
                    ui.notify("Please enter your email address", color="negative")
                    return
                
                email = email_input.value.strip()
                submit_btn.props("loading")
                
                try:
                    # Call the FastAPI-Users forgot password endpoint
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            f"{settings.ROOT_URL}/auth/forgot-password",
                            json={"email": email}
                        )
                        
                        if response.status_code == 202:
                            # Success - email sent
                            with message_container:
                                message_container.clear()
                                with ui.card().classes("w-full p-4 bg-gray-800 border-gray-600"):
                                    ui.icon("check_circle", color="positive")
                                    ui.label("Reset Link Sent!").classes("font-semibold text-green-400")
                                    ui.label(f"If an account with {email} exists, we've sent password reset instructions to that email address.").classes("text-gray-300 mt-1")
                                    ui.label("Please check your inbox and follow the instructions in the email.").classes("text-gray-300 mt-2")
                            
                            # Disable form after successful submission
                            email_input.props("readonly")
                            submit_btn.props("disable")
                            
                        else:
                            # Handle error response
                            error_detail = response.json().get("detail", "An error occurred")
                            ui.notify(f"Error: {error_detail}", color="negative")
                            
                except Exception as e:
                    logger.error(f"Error sending password reset email: {str(e)}")
                    ui.notify("An error occurred while sending the reset email. Please try again.", color="negative")
                    
                finally:
                    submit_btn.props(remove="loading")
            
            # Back to login link
            with ui.row().classes("w-full justify-center mt-6"):
                ui.link("← Back to Login", target="/login").classes("text-blue-500 hover:underline")


async def password_reset_success_page_ui():
    """Show success message after password reset email is sent.""" 
    custom_header()
    
    with ui.column().classes("w-full max-w-md mx-auto mt-16 gap-6"):
        with ui.card().classes("w-full p-8"):
            ui.icon("mark_email_read", color="positive", size="3rem").classes("mx-auto")
            ui.label("Check Your Email").classes("text-2xl font-bold text-center mt-4")
            ui.label("We've sent password reset instructions to your email address.").classes("text-center text-gray-600 mt-2")
            
            with ui.column().classes("w-full gap-3 mt-6"):
                ui.label("Next steps:").classes("font-semibold")
                ui.label("1. Check your email inbox (and spam folder)")
                ui.label("2. Click the reset link in the email")
                ui.label("3. Enter your new password")
                ui.label("4. Log in with your new password")
            
            ui.label("The reset link will expire in 1 hour for security.").classes("text-center text-gray-500 text-sm mt-6")
            
            with ui.row().classes("w-full justify-center mt-6 gap-4"):
                ui.button("Back to Login", on_click=lambda: ui.navigate.to("/login")).props("flat outline").classes("px-6 py-3 rounded-lg")
                ui.button("Resend Email", on_click=lambda: ui.navigate.to("/gui/forgot-password")).props("flat").classes("bg-blue-500 text-white px-6 py-3 rounded-lg")