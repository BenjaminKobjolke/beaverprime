from nicegui import ui
from fastapi import Request
import httpx

from beaverhabits.frontend.layout import layout
from beaverhabits.frontend.components.layout.utils.navigation import redirect
from beaverhabits.app.db import User
from beaverhabits.configs import settings
from beaverhabits.logging import logger


async def verify_email_page_ui(user: User = None, verification_status: str = "pending"):
    async with layout(user=user, with_menu=False):
        with ui.column().classes("w-full max-w-md mx-auto mt-16 gap-6"):
            with ui.card().classes("w-full p-8"):
                # Different content based on verification status
                if verification_status == "success":
                    ui.icon("check_circle", color="positive", size="4rem").classes("mx-auto")
                    ui.label("Email Verified Successfully!").classes("text-2xl font-bold text-center mt-4")
                    ui.label("Your email address has been verified. You can now use all features of Beaver Habits.").classes("text-center text-gray-600 mt-2")
                    
                    with ui.row().classes("w-full justify-center mt-6"):
                        ui.button("Continue to App", on_click=lambda: redirect("")).props("flat").classes("bg-green-500 text-white px-8 py-3 rounded-lg")
                
                elif verification_status == "error":
                    ui.icon("error", color="negative", size="4rem").classes("mx-auto")
                    ui.label("Verification Failed").classes("text-2xl font-bold text-center mt-4")
                    ui.label("The verification link is invalid or has expired. Please request a new verification email.").classes("text-center text-gray-600 mt-2")
                    
                    with ui.row().classes("w-full justify-center mt-6 gap-4"):
                        ui.button("Request New Email", on_click=lambda: show_resend_form()).props("flat").classes("bg-blue-500 text-white px-6 py-3 rounded-lg")
                        ui.button("Back to Login", on_click=lambda: ui.navigate.to("/login")).props("flat outline").classes("px-6 py-3 rounded-lg")
                
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
                        ui.button("Request New Email", on_click=lambda: show_resend_form()).props("flat").classes("bg-blue-500 text-white px-6 py-3 rounded-lg")
                        ui.button("Back to Login", on_click=lambda: ui.navigate.to("/login")).props("flat outline").classes("px-6 py-3 rounded-lg")

        # Function to show resend email form
        async def show_resend_form():
            """Show a form to resend verification email."""
            with ui.dialog() as dialog, ui.card().classes("w-96 p-6"):
                ui.label("Resend Verification Email").classes("text-xl font-semibold mb-4")
                ui.label("Enter your email address to receive a new verification link.").classes("text-gray-600 mb-4")
                
                email_input = ui.input("Email Address", placeholder="Enter your email address").props("outlined dense").classes("w-full")
                
                with ui.row().classes("w-full justify-end gap-2 mt-4"):
                    ui.button("Cancel", on_click=dialog.close).props("flat outline")
                    
                    async def send_verification():
                        if not email_input.value or not email_input.value.strip():
                            ui.notify("Please enter your email address", color="negative")
                            return
                            
                        try:
                            async with httpx.AsyncClient() as client:
                                response = await client.post(
                                    f"{settings.ROOT_URL}/auth/request-verify-token",
                                    json={"email": email_input.value.strip()}
                                )
                                
                                if response.status_code == 202:
                                    ui.notify("Verification email sent! Please check your inbox.", color="positive", timeout=5000)
                                    dialog.close()
                                else:
                                    error_detail = response.json().get("detail", "An error occurred")
                                    ui.notify(f"Error: {error_detail}", color="negative")
                                    
                        except Exception as e:
                            logger.error(f"Error requesting verification: {str(e)}")
                            ui.notify("An error occurred while sending verification email. Please try again.", color="negative")
                    
                    ui.button("Send Email", on_click=send_verification).props("flat").classes("bg-blue-500 text-white")
            
            dialog.open()


