"""
Email Service for Newsletter Delivery
Handles sending newsletters via Gmail SMTP with tracking, rate limiting, and compliance
"""

import logging
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from supabase import Client
import uuid

from app.core.config import settings
from app.core.database import get_supabase

logger = logging.getLogger(__name__)

# Gmail sending limits
GMAIL_DAILY_LIMIT = 500  # For regular Gmail accounts
GMAIL_WORKSPACE_DAILY_LIMIT = 2000  # For Google Workspace accounts
RATE_LIMIT_BUFFER = 50  # Keep some buffer for safety


class EmailService:
    """Handles email delivery for newsletters with tracking and rate limiting"""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.GMAIL_EMAIL
        self.smtp_password = settings.GMAIL_APP_PASSWORD
        self.from_email = settings.GMAIL_EMAIL
        self.supabase: Optional[Client] = None
        self.daily_limit = GMAIL_DAILY_LIMIT
    
    def initialize(self):
        """Initialize database connection"""
        if not self.supabase:
            self.supabase = get_supabase()
    
    async def check_rate_limit(self, user_id: str, recipient_count: int = 1) -> Dict[str, Any]:
        """
        Check if user has reached their daily email sending limit
        
        Args:
            user_id: User ID
            recipient_count: Number of recipients to send to
        
        Returns:
            Dictionary with rate limit status
        """
        self.initialize()
        
        today = date.today()
        
        # Get or create rate limit record for today
        result = self.supabase.table("email_rate_limits").select("*").eq(
            "user_id", user_id
        ).eq("date", today.isoformat()).execute()
        
        if result.data:
            rate_limit = result.data[0]
            current_count = rate_limit["email_count"]
        else:
            current_count = 0
        
        remaining = self.daily_limit - RATE_LIMIT_BUFFER - current_count
        can_send = remaining >= recipient_count
        
        return {
            "can_send": can_send,
            "current_count": current_count,
            "daily_limit": self.daily_limit,
            "remaining": max(0, remaining),
            "requested": recipient_count
        }
    
    async def increment_rate_limit(self, user_id: str, count: int = 1):
        """
        Increment the email count for rate limiting
        
        Args:
            user_id: User ID
            count: Number of emails sent
        """
        self.initialize()
        
        today = date.today()
        
        # Try to update existing record
        result = self.supabase.table("email_rate_limits").select("*").eq(
            "user_id", user_id
        ).eq("date", today.isoformat()).execute()
        
        if result.data:
            # Update existing record
            new_count = result.data[0]["email_count"] + count
            self.supabase.table("email_rate_limits").update({
                "email_count": new_count,
                "last_email_at": datetime.now().isoformat()
            }).eq("user_id", user_id).eq("date", today.isoformat()).execute()
        else:
            # Create new record
            self.supabase.table("email_rate_limits").insert({
                "user_id": user_id,
                "date": today.isoformat(),
                "email_count": count,
                "last_email_at": datetime.now().isoformat()
            }).execute()
    
    async def check_unsubscribed(self, email: str) -> bool:
        """
        Check if an email address has unsubscribed
        
        Args:
            email: Email address to check
        
        Returns:
            True if unsubscribed, False otherwise
        """
        self.initialize()
        
        result = self.supabase.table("unsubscribes").select("email").eq(
            "email", email.lower()
        ).execute()
        
        return len(result.data) > 0 if result.data else False
    
    async def log_email_delivery(
        self,
        user_id: str,
        recipient_email: str,
        subject: str,
        status: str,
        draft_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> str:
        """
        Log email delivery attempt
        
        Args:
            user_id: User ID
            recipient_email: Recipient email
            subject: Email subject
            status: Delivery status (queued, sending, sent, failed, bounced)
            draft_id: Optional draft ID
            error_message: Optional error message
        
        Returns:
            Log entry ID
        """
        self.initialize()
        
        log_data = {
            "user_id": user_id,
            "recipient_email": recipient_email,
            "subject": subject,
            "status": status,
            "draft_id": draft_id,
            "error_message": error_message,
            "retry_count": 0
        }
        
        if status == "sent":
            log_data["sent_at"] = datetime.now().isoformat()
        
        result = self.supabase.table("email_delivery_log").insert(log_data).execute()
        
        return result.data[0]["id"] if result.data else None
    
    async def update_email_log(
        self,
        log_id: str,
        status: str,
        error_message: Optional[str] = None,
        increment_retry: bool = False
    ):
        """
        Update email delivery log
        
        Args:
            log_id: Log entry ID
            status: New status
            error_message: Optional error message
            increment_retry: Whether to increment retry count
        """
        self.initialize()
        
        update_data = {"status": status}
        
        if error_message:
            update_data["error_message"] = error_message
        
        if status == "sent":
            update_data["sent_at"] = datetime.now().isoformat()
        
        if increment_retry:
            # Get current retry count
            result = self.supabase.table("email_delivery_log").select("retry_count").eq(
                "id", log_id
            ).execute()
            if result.data:
                current_retry = result.data[0].get("retry_count", 0)
                update_data["retry_count"] = current_retry + 1
        
        self.supabase.table("email_delivery_log").update(update_data).eq(
            "id", log_id
        ).execute()
    
    async def send_newsletter(
        self,
        draft_id: str,
        subject: str,
        recipients: List[str],
        user_id: str,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Send newsletter email with rate limiting and tracking
        
        Args:
            draft_id: Draft ID to send
            subject: Email subject
            recipients: List of recipient email addresses
            user_id: User ID
            max_retries: Maximum retry attempts for failed sends
        
        Returns:
            Result dictionary with success status
        """
        self.initialize()
        
        logger.info(f"Sending newsletter {draft_id} to {len(recipients)} recipient(s)")
        
        try:
            # Check rate limit
            rate_limit = await self.check_rate_limit(user_id, len(recipients))
            if not rate_limit["can_send"]:
                return {
                    "success": False,
                    "error": "rate_limit_exceeded",
                    "message": f"Daily email limit reached. {rate_limit['remaining']} emails remaining today.",
                    "rate_limit": rate_limit
                }
            
            # Get draft content
            result = self.supabase.table("newsletter_drafts").select("*").eq(
                "id", draft_id
            ).eq("user_id", user_id).execute()
            
            if not result.data:
                raise ValueError(f"Draft {draft_id} not found")
            
            draft = result.data[0]
            
            # Convert draft to HTML with unsubscribe link
            html_content = self._draft_to_html(draft, user_id)
            text_content = self._draft_to_text(draft, user_id)
            
            # Filter out unsubscribed recipients
            valid_recipients = []
            unsubscribed_recipients = []
            
            for recipient in recipients:
                if await self.check_unsubscribed(recipient):
                    unsubscribed_recipients.append(recipient)
                    logger.info(f"Skipping unsubscribed recipient: {recipient}")
                else:
                    valid_recipients.append(recipient)
            
            # Send emails
            success_count = 0
            failed_recipients = []
            
            for recipient in valid_recipients:
                log_id = None
                try:
                    # Log email attempt
                    log_id = await self.log_email_delivery(
                        user_id=user_id,
                        recipient_email=recipient,
                        subject=subject,
                        status="sending",
                        draft_id=draft_id
                    )
                    
                    # Send email
                    self._send_email(
                        to_email=recipient,
                        subject=subject,
                        html_content=html_content,
                        text_content=text_content
                    )
                    
                    # Update log to sent
                    if log_id:
                        await self.update_email_log(log_id, "sent")
                    
                    success_count += 1
                    
                    # Small delay to avoid rate limiting
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Failed to send to {recipient}: {str(e)}")
                    failed_recipients.append(recipient)
                    
                    # Update log to failed
                    if log_id:
                        await self.update_email_log(
                            log_id,
                            "failed",
                            error_message=str(e),
                            increment_retry=True
                        )
            
            # Update rate limit counter
            if success_count > 0:
                await self.increment_rate_limit(user_id, success_count)
            
            # Update draft
            self.supabase.table("newsletter_drafts").update({
                "email_sent": True,
                "email_sent_at": datetime.now().isoformat(),
                "metadata": {
                    **draft.get("metadata", {}),
                    "email_stats": {
                        "sent_count": success_count,
                        "failed_count": len(failed_recipients),
                        "recipients": recipients
                    }
                }
            }).eq("id", draft_id).execute()
            
            logger.info(f"Newsletter sent: {success_count} success, {len(failed_recipients)} failed")
            
            return {
                "success": True,
                "sent_count": success_count,
                "failed_count": len(failed_recipients),
                "failed_recipients": failed_recipients,
                "message": f"Newsletter sent to {success_count} recipient(s)"
            }
            
        except Exception as e:
            logger.error(f"Error sending newsletter: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to send newsletter"
            }
    
    async def send_draft_notification(
        self,
        draft_id: str,
        user_email: str,
        user_id: str
    ) -> bool:
        """
        Send draft notification email to user
        
        Args:
            draft_id: Draft ID
            user_email: User's email address
            user_id: User ID
        
        Returns:
            Success status
        """
        self.initialize()
        
        try:
            # Get draft
            result = self.supabase.table("newsletter_drafts").select("*").eq(
                "id", draft_id
            ).eq("user_id", user_id).execute()
            
            if not result.data:
                return False
            
            draft = result.data[0]
            
            # Create notification email
            subject = f"Your Newsletter Draft is Ready: {draft['title']}"
            
            review_url = f"{settings.FRONTEND_URL}/drafts/{draft_id}"
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2>Your Newsletter Draft is Ready!</h2>
                <p>We've generated a new newsletter draft for you based on your latest content sources.</p>
                
                <h3>{draft['title']}</h3>
                
                <p><strong>Topics included:</strong> {draft.get('metadata', {}).get('topic_count', 0)}</p>
                <p><strong>Estimated read time:</strong> {draft.get('metadata', {}).get('estimated_read_time', 'N/A')}</p>
                
                <p style="margin: 30px 0;">
                    <a href="{review_url}" style="background-color: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Review & Edit Draft
                    </a>
                </p>
                
                <p style="color: #666; font-size: 14px;">
                    You can review, edit, and send your newsletter from the CreatorPulse dashboard.
                </p>
            </body>
            </html>
            """
            
            text_content = f"""
Your Newsletter Draft is Ready!

We've generated a new newsletter draft for you based on your latest content sources.

{draft['title']}

Topics included: {draft.get('metadata', {}).get('topic_count', 0)}
Estimated read time: {draft.get('metadata', {}).get('estimated_read_time', 'N/A')}

Review your draft: {review_url}

You can review, edit, and send your newsletter from the CreatorPulse dashboard.
            """
            
            self._send_email(
                to_email=user_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            logger.info(f"Draft notification sent to {user_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending draft notification: {str(e)}")
            return False
    
    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str
    ):
        """
        Send email via SMTP
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Attach parts
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {to_email}")
            
        except Exception as e:
            logger.error(f"SMTP error sending to {to_email}: {str(e)}")
            raise
    
    def _draft_to_html(self, draft: Dict[str, Any], user_id: Optional[str] = None) -> str:
        """Convert draft to HTML email format with unsubscribe link"""
        
        sections_html = ""
        for section in draft.get("sections", []):
            section_type = section.get("type", "topic")
            title = section.get("title")
            content = section.get("content", "")
            
            # Convert markdown-style formatting to HTML
            content_html = content.replace("\n\n", "</p><p>")
            content_html = content_html.replace("**", "<strong>").replace("**", "</strong>")
            content_html = content_html.replace("*", "<em>").replace("*", "</em>")
            
            if section_type == "intro":
                sections_html += f"""
                <div style="margin-bottom: 30px;">
                    <p>{content_html}</p>
                </div>
                """
            elif section_type == "topic":
                sections_html += f"""
                <div style="margin-bottom: 30px; border-left: 4px solid #4F46E5; padding-left: 20px;">
                    <h3 style="color: #1F2937; margin-bottom: 10px;">{title or 'Topic'}</h3>
                    <p>{content_html}</p>
                </div>
                """
            elif section_type == "conclusion":
                sections_html += f"""
                <div style="margin-top: 40px; padding-top: 20px; border-top: 2px solid #E5E7EB;">
                    <p>{content_html}</p>
                </div>
                """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #F9FAFB; padding: 30px; border-radius: 8px;">
                <h1 style="color: #1F2937; margin-bottom: 20px;">{draft.get('title', 'Newsletter')}</h1>
                
                {sections_html}
                
                <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #E5E7EB; text-align: center; color: #6B7280; font-size: 14px;">
                    <p>Sent with CreatorPulse</p>
                    <p>
                        <a href="{settings.BACKEND_URL}/api/email/unsubscribe?email={{email}}&token={{token}}" 
                           style="color: #4F46E5; text-decoration: none;">Unsubscribe</a>
                    </p>
                    <p style="font-size: 12px; margin-top: 10px;">
                        You're receiving this because you subscribed to this newsletter.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _draft_to_text(self, draft: Dict[str, Any], user_id: Optional[str] = None) -> str:
        """Convert draft to plain text email format with unsubscribe link"""
        
        text_parts = [
            f"{draft.get('title', 'Newsletter')}",
            "=" * len(draft.get('title', 'Newsletter')),
            ""
        ]
        
        for section in draft.get("sections", []):
            section_type = section.get("type", "topic")
            title = section.get("title")
            content = section.get("content", "")
            
            if section_type == "intro":
                text_parts.append(content)
                text_parts.append("")
            elif section_type == "topic":
                text_parts.append(f"\n{title or 'Topic'}")
                text_parts.append("-" * len(title or 'Topic'))
                text_parts.append(content)
                text_parts.append("")
            elif section_type == "conclusion":
                text_parts.append("\n" + "-" * 40)
                text_parts.append(content)
                text_parts.append("")
        
        text_parts.extend([
            "\n" + "=" * 40,
            "Sent with CreatorPulse",
            f"Unsubscribe: {settings.BACKEND_URL}/api/email/unsubscribe?email={{{{email}}}}&token={{{{token}}}}",
            "You're receiving this because you subscribed to this newsletter."
        ])
        
        return "\n".join(text_parts)


# Singleton instance
email_service = EmailService()
