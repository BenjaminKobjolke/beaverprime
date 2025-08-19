from nicegui import ui
from fastapi import Request
import httpx

from beaverhabits.frontend.layout import layout
from beaverhabits.frontend.components.layout.utils.navigation import redirect
from beaverhabits.app.db import User
from beaverhabits.configs import settings
from beaverhabits.logging import logger
from beaverhabits.services.i18n import t


async def verify_email_page_ui(user: User = None, verification_status: str = "pending"):
    from beaverhabits.services.i18n import init_user_language
    from beaverhabits.frontend.components import auth_language_switcher
    
    # Initialize user language before any UI
    init_user_language()
    
    # Add language switcher in top-right corner for guest users
    if not user:
        with ui.row().classes("fixed top-4 right-4 z-50"):
            auth_language_switcher()
    
    async with layout(user=user, with_menu=False):
        with ui.column().classes("w-full max-w-md mx-auto mt-16 gap-6"):
            with ui.card().classes("w-full p-8"):
                # Different content based on verification status
                if verification_status == "success":
                    ui.icon("check_circle", color="positive", size="4rem").classes("mx-auto")
                    ui.label(t("verification.success_title")).classes("text-2xl font-bold text-center mt-4")
                    ui.label(t("verification.success_message")).classes("text-center text-gray-600 mt-2")
                    
                    with ui.row().classes("w-full justify-center mt-6"):
                        ui.button(t("verification.continue_to_app"), on_click=lambda: redirect("")).props("flat").classes("bg-green-500 text-white px-8 py-3 rounded-lg")
                
                elif verification_status == "error":
                    ui.icon("error", color="negative", size="4rem").classes("mx-auto")
                    ui.label("Verification Failed").classes("text-2xl font-bold text-center mt-4")
                    ui.label("The verification link is invalid or has expired. Please request a new verification email.").classes("text-center text-gray-600 mt-2")
                    
                    with ui.row().classes("w-full justify-center mt-6 gap-4"):
                        ui.button(t("verification.request_new_email"), on_click=lambda: show_resend_form()).props("flat").classes("bg-blue-500 text-white px-6 py-3 rounded-lg")
                        ui.button(t("verification.back_to_login"), on_click=lambda: ui.navigate.to("/login")).props("flat outline").classes("px-6 py-3 rounded-lg")
                
                else:  # pending or default
                    ui.icon("email", color="primary", size="4rem").classes("mx-auto")
                    ui.label("Check Your Email").classes("text-2xl font-bold text-center mt-4")
                    
                    if user:
                        ui.label(f"We've sent a verification email to:").classes("text-center text-gray-600 mt-2")
                        ui.label(user.email).classes("text-center font-mono bg-gray-800 text-gray-300 rounded px-3 py-1 mt-2")
                    else:
                        ui.label("We've sent you a verification email.").classes("text-center text-gray-600 mt-2")
                    
                    ui.label("Please check your inbox and click the verification link to activate your account.").classes("text-center text-gray-600 mt-4")
                    
                    with ui.expansion("Didn't receive the email?", icon="help_outline").classes("mt-6 w-full"):
                        with ui.column().classes("gap-3 mt-2"):
                            ui.label("• Check your spam/junk folder")
                            ui.label("• Make sure you entered the correct email address") 
                            ui.label("• Wait a few minutes for the email to arrive")
                            ui.label("• Request a new verification email below")
                    
                    with ui.row().classes("w-full justify-center mt-6 gap-4"):
                        ui.button(t("verification.request_new_email"), on_click=lambda: show_resend_form()).props("flat").classes("bg-blue-500 text-white px-6 py-3 rounded-lg")
                        ui.button(t("verification.back_to_login"), on_click=lambda: ui.navigate.to("/login")).props("flat outline").classes("px-6 py-3 rounded-lg")

        # Function to show resend email form
        async def show_resend_form():
            """Show a form to resend verification email."""
            with ui.dialog() as dialog, ui.card().classes("w-96 p-6"):
                ui.label(t("verification.resend_title")).classes("text-xl font-semibold mb-4")
                ui.label(t("verification.resend_instruction")).classes("text-gray-600 mb-4")
                
                email_input = ui.input(t("verification.email_label"), placeholder=t("verification.email_placeholder")).props("outlined dense").classes("w-full")
                
                with ui.row().classes("w-full justify-end gap-2 mt-4"):
                    ui.button(t("verification.cancel"), on_click=dialog.close).props("flat outline")
                    
                    async def send_verification():
                        if not email_input.value or not email_input.value.strip():
                            ui.notify(t("verification.enter_email_error"), color="negative")
                            return
                            
                        try:
                            async with httpx.AsyncClient() as client:
                                response = await client.post(
                                    f"{settings.ROOT_URL}/auth/request-verify-token",
                                    json={"email": email_input.value.strip()}
                                )
                                
                                if response.status_code == 202:
                                    ui.notify(t("verification.email_sent_success"), color="positive", timeout=5000)
                                    dialog.close()
                                else:
                                    error_detail = response.json().get("detail", t("verification.generic_error"))
                                    ui.notify(t("verification.error_with_detail", error=error_detail), color="negative")
                                    
                        except Exception as e:
                            logger.error(f"Error requesting verification: {str(e)}")
                            ui.notify(t("verification.send_error"), color="negative")
                    
                    ui.button(t("verification.send_email"), on_click=send_verification).props("flat").classes("bg-blue-500 text-white")
            
            dialog.open()


