from nicegui import ui
import httpx
from fastapi import HTTPException

from beaverhabits.frontend.layout import custom_header
from beaverhabits.configs import settings
from beaverhabits.logging import logger
from beaverhabits.services.i18n import t


async def forgot_password_page_ui():
    """Forgot password page UI."""
    from beaverhabits.services.i18n import init_user_language
    from beaverhabits.frontend.components import auth_language_switcher
    
    # Initialize user language before any UI
    init_user_language()
    
    custom_header()
    
    # Add language switcher in top-right corner
    with ui.row().classes("fixed top-4 right-4 z-50"):
        auth_language_switcher()
    
    with ui.column().classes("w-full max-w-md mx-auto mt-16 gap-6"):
        with ui.card().classes("w-full p-8"):
            ui.icon("lock_reset", color="primary", size="3rem").classes("mx-auto")
            ui.label(t("password_reset.title")).classes("text-2xl font-bold text-center mt-4")
            ui.label(t("password_reset.instruction")).classes("text-center text-gray-600 mt-2 mb-6")
            
            # Email input
            email_input = ui.input(t("password_reset.email_label"), placeholder=t("password_reset.email_placeholder")).props("outlined dense").classes("w-full")
            email_input.on("keydown.enter", lambda: send_reset_email())
            
            # Submit button
            submit_btn = ui.button(t("password_reset.send_button"), on_click=lambda: send_reset_email()).props("flat").classes("w-full bg-blue-500 text-white py-3 rounded-lg mt-4")
            
            # Success/error messages
            message_container = ui.row().classes("w-full mt-4")
            
            async def send_reset_email():
                """Send password reset email."""
                if not email_input.value or not email_input.value.strip():
                    ui.notify(t("password_reset.email_required"), color="negative")
                    return
                
                email = email_input.value.strip()
                submit_btn.disable()
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
                                    ui.label(t("password_reset.success_title")).classes("font-semibold text-green-400")
                                    ui.label(t("password_reset.success_message", email=email)).classes("text-gray-300 mt-1")
                                    ui.label(t("password_reset.check_inbox")).classes("text-gray-300 mt-2")
                            
                            # Disable form after successful submission
                            email_input.props("readonly")
                            submit_btn.props("disable")
                            
                        else:
                            # Handle error response
                            error_detail = response.json().get("detail", t("password_reset.generic_error"))
                            ui.notify(t("password_reset.error_with_detail", error=error_detail), color="negative")
                            
                except Exception as e:
                    logger.error(f"Error sending password reset email: {str(e)}")
                    ui.notify(t("password_reset.send_error"), color="negative")
                    
                finally:
                    submit_btn.enable()
                    submit_btn.props(remove="loading")
            
            # Back to login link
            with ui.row().classes("w-full justify-center mt-6"):
                ui.link(t("password_reset.back_to_login"), target="/login").classes("text-blue-500 hover:underline")


async def password_reset_success_page_ui():
    """Show success message after password reset email is sent.""" 
    custom_header()
    
    with ui.column().classes("w-full max-w-md mx-auto mt-16 gap-6"):
        with ui.card().classes("w-full p-8"):
            ui.icon("mark_email_read", color="positive", size="3rem").classes("mx-auto")
            ui.label(t("password_reset.check_email_title")).classes("text-2xl font-bold text-center mt-4")
            ui.label(t("password_reset.email_sent_message")).classes("text-center text-gray-600 mt-2")
            
            with ui.column().classes("w-full gap-3 mt-6"):
                ui.label(t("password_reset.next_steps_title")).classes("font-semibold")
                ui.label(t("password_reset.step_1"))
                ui.label(t("password_reset.step_2"))
                ui.label(t("password_reset.step_3"))
                ui.label(t("password_reset.step_4"))
            
            ui.label(t("password_reset.expiry_notice")).classes("text-center text-gray-500 text-sm mt-6")
            
            with ui.row().classes("w-full justify-center mt-6 gap-4"):
                ui.button(t("password_reset.back_to_login_button"), on_click=lambda: ui.navigate.to("/login")).props("flat outline").classes("px-6 py-3 rounded-lg")
                ui.button(t("password_reset.resend_email"), on_click=lambda: ui.navigate.to("/gui/forgot-password")).props("flat").classes("bg-blue-500 text-white px-6 py-3 rounded-lg")