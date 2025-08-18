import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import asyncio

from beaverhabits.configs import settings
from beaverhabits.logging import logger


class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_use_tls = settings.SMTP_USE_TLS
        self.from_email = settings.FROM_EMAIL
        self.from_name = settings.FROM_NAME

    async def send_email(self, to_email: str, subject: str, html_body: str, text_body: Optional[str] = None):
        """Send an email asynchronously."""
        try:
            # Run the blocking SMTP operation in a thread pool
            await asyncio.get_event_loop().run_in_executor(
                None, self._send_email_sync, to_email, subject, html_body, text_body
            )
            logger.info(f"Email sent successfully to {to_email}")
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            raise

    def _send_email_sync(self, to_email: str, subject: str, html_body: str, text_body: Optional[str] = None):
        """Synchronous email sending implementation."""
        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP credentials not configured - email not sent")
            if settings.is_dev():
                logger.info(f"DEV MODE - Would send email to {to_email}:")
                logger.info(f"Subject: {subject}")
                logger.info(f"Body: {html_body}")
            return

        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{self.from_name} <{self.from_email}>"
        msg['To'] = to_email

        # Add text part if provided
        if text_body:
            text_part = MIMEText(text_body, 'plain')
            msg.attach(text_part)

        # Add HTML part
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)

        # Create secure context and send
        context = ssl.create_default_context()
        
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            if self.smtp_use_tls:
                server.starttls(context=context)
            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.from_email, to_email, msg.as_string())

    async def send_verification_email(self, to_email: str, token: str):
        """Send email verification message."""
        verification_url = f"{settings.ROOT_URL}/gui/verify?token={token}"
        
        html_body = f"""
        <html>
        <body>
            <h2>Welcome to {self.from_name}!</h2>
            <p>Thank you for registering with {self.from_name}. To complete your registration and start tracking your habits, please verify your email address by clicking the link below:</p>
            
            <p><a href="{verification_url}" style="background-color: #4CAF50; color: white; padding: 14px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">Verify Email Address</a></p>
            
            <p>Or copy and paste this link into your browser:</p>
            <p><code>{verification_url}</code></p>
            
            <p>This verification link will expire in 24 hours for security purposes.</p>
            
            <p>If you didn't create an account with {self.from_name}, you can safely ignore this email.</p>
            
            <p>Happy habit tracking!</p>
            <p>The {self.from_name} Team</p>
        </body>
        </html>
        """
        
        text_body = f"""
        Welcome to {self.from_name}!
        
        Thank you for registering with {self.from_name}. To complete your registration and start tracking your habits, please verify your email address by visiting this link:
        
        {verification_url}
        
        This verification link will expire in 24 hours for security purposes.
        
        If you didn't create an account with {self.from_name}, you can safely ignore this email.
        
        Happy habit tracking!
        The {self.from_name} Team
        """
        
        await self.send_email(to_email, settings.VERIFICATION_SUBJECT, html_body, text_body)

    async def send_password_reset_email(self, to_email: str, token: str):
        """Send password reset email."""
        reset_url = f"{settings.ROOT_URL}/gui/reset-password?token={token}"
        
        html_body = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>We received a request to reset your password for your {self.from_name} account.</p>
            
            <p>Click the link below to reset your password:</p>
            
            <p><a href="{reset_url}" style="background-color: #2196F3; color: white; padding: 14px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">Reset Password</a></p>
            
            <p>Or copy and paste this link into your browser:</p>
            <p><code>{reset_url}</code></p>
            
            <p>This password reset link will expire in 1 hour for security purposes.</p>
            
            <p><strong>If you didn't request a password reset, you can safely ignore this email.</strong> Your password will remain unchanged.</p>
            
            <p>For security reasons, this request was logged with your IP address and timestamp.</p>
            
            <p>The {self.from_name} Team</p>
        </body>
        </html>
        """
        
        text_body = f"""
        Password Reset Request
        
        We received a request to reset your password for your {self.from_name} account.
        
        Visit this link to reset your password:
        {reset_url}
        
        This password reset link will expire in 1 hour for security purposes.
        
        If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.
        
        The {self.from_name} Team
        """
        
        await self.send_email(to_email, settings.RESET_SUBJECT, html_body, text_body)


# Global email service instance
email_service = EmailService()