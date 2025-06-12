"""
Email service for sending notifications and system emails.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmailService:
    """Service for sending emails."""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_tls = settings.SMTP_TLS
        self.from_email = settings.EMAILS_FROM_EMAIL
        self.from_name = settings.EMAILS_FROM_NAME
    
    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send email to recipients."""
        if not self.smtp_host or not self.from_email:
            logger.warning("Email service not configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>" if self.from_name else self.from_email
            msg['To'] = ', '.join(to_emails)
            
            # Add text content
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_tls:
                    server.starttls()
                
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {', '.join(to_emails)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def send_password_reset_email(self, email: str, reset_token: str) -> bool:
        """Send password reset email."""
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        subject = "Reset Your Password - Spendlot"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Reset Your Password</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">Reset Your Password</h2>
                
                <p>You requested a password reset for your Spendlot account.</p>
                
                <p>Click the button below to reset your password:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background-color: #3498db; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Reset Password
                    </a>
                </div>
                
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #7f8c8d;">{reset_url}</p>
                
                <p><strong>This link will expire in 1 hour.</strong></p>
                
                <p>If you didn't request this password reset, please ignore this email.</p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="color: #7f8c8d; font-size: 12px;">
                    This email was sent by Spendlot Receipt Tracker.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Reset Your Password - Spendlot
        
        You requested a password reset for your Spendlot account.
        
        Click this link to reset your password:
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request this password reset, please ignore this email.
        """
        
        return self.send_email([email], subject, html_content, text_content)
    
    def send_welcome_email(self, email: str, full_name: str) -> bool:
        """Send welcome email to new users."""
        subject = "Welcome to Spendlot!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome to Spendlot</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">Welcome to Spendlot! 🎉</h2>
                
                <p>Hi {full_name or 'there'},</p>
                
                <p>Welcome to Spendlot, your smart receipt tracking companion!</p>
                
                <p>Here's what you can do with Spendlot:</p>
                <ul>
                    <li>📸 Upload receipt photos for automatic OCR processing</li>
                    <li>📧 Connect Gmail to automatically import receipt emails</li>
                    <li>🏦 Link bank accounts for transaction tracking</li>
                    <li>📊 Get insights into your spending patterns</li>
                    <li>🏷️ Automatic categorization of expenses</li>
                </ul>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{settings.FRONTEND_URL}/dashboard" 
                       style="background-color: #27ae60; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Get Started
                    </a>
                </div>
                
                <p>If you have any questions, feel free to reach out to our support team.</p>
                
                <p>Happy tracking!</p>
                <p>The Spendlot Team</p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="color: #7f8c8d; font-size: 12px;">
                    This email was sent by Spendlot Receipt Tracker.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to Spendlot!
        
        Hi {full_name or 'there'},
        
        Welcome to Spendlot, your smart receipt tracking companion!
        
        Here's what you can do with Spendlot:
        - Upload receipt photos for automatic OCR processing
        - Connect Gmail to automatically import receipt emails
        - Link bank accounts for transaction tracking
        - Get insights into your spending patterns
        - Automatic categorization of expenses
        
        Visit {settings.FRONTEND_URL}/dashboard to get started.
        
        If you have any questions, feel free to reach out to our support team.
        
        Happy tracking!
        The Spendlot Team
        """
        
        return self.send_email([email], subject, html_content, text_content)
    
    def send_receipt_processed_notification(
        self, 
        email: str, 
        receipt_id: int, 
        merchant_name: str, 
        amount: float
    ) -> bool:
        """Send notification when receipt is processed."""
        subject = f"Receipt Processed: {merchant_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Receipt Processed</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">Receipt Processed Successfully ✅</h2>
                
                <p>Your receipt has been processed and added to your account:</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Merchant:</strong> {merchant_name}</p>
                    <p><strong>Amount:</strong> ${amount:.2f}</p>
                    <p><strong>Receipt ID:</strong> #{receipt_id}</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{settings.FRONTEND_URL}/receipts/{receipt_id}" 
                       style="background-color: #3498db; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        View Receipt
                    </a>
                </div>
                
                <p>You can view and edit this receipt in your dashboard.</p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="color: #7f8c8d; font-size: 12px;">
                    This email was sent by Spendlot Receipt Tracker.
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email([email], subject, html_content)
