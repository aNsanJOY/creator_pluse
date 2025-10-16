"""
Email Models
Pydantic models for email delivery, tracking, and recipient management
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class EmailStatus(str, Enum):
    """Email delivery status"""
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"


class RecipientStatus(str, Enum):
    """Recipient subscription status"""
    ACTIVE = "active"
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED = "bounced"


class EmailDeliveryLog(BaseModel):
    """Email delivery log entry"""
    id: str
    user_id: str
    draft_id: Optional[str] = None
    recipient_email: EmailStr
    subject: str
    status: EmailStatus
    error_message: Optional[str] = None
    retry_count: int = 0
    sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class Recipient(BaseModel):
    """Recipient model"""
    id: str
    user_id: str
    email: EmailStr
    name: Optional[str] = None
    status: RecipientStatus
    metadata: Dict[str, Any] = Field(default_factory=dict)
    subscribed_at: datetime
    created_at: datetime
    updated_at: datetime


class Unsubscribe(BaseModel):
    """Unsubscribe record"""
    id: str
    email: EmailStr
    user_id: Optional[str] = None
    reason: Optional[str] = None
    unsubscribed_at: datetime
    created_at: datetime


class RateLimit(BaseModel):
    """Rate limit tracking"""
    id: str
    user_id: str
    date: str
    email_count: int
    last_email_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class RateLimitStatus(BaseModel):
    """Rate limit status response"""
    can_send: bool
    current_count: int
    daily_limit: int
    remaining: int
    requested: int


class EmailStats(BaseModel):
    """Email delivery statistics"""
    period_days: int
    total_sent: int
    total_failed: int
    total_queued: int
    total_attempts: int
    success_rate: float


class SendEmailResponse(BaseModel):
    """Response for email send request"""
    success: bool
    message: str
    sent_count: Optional[int] = None
    failed_count: Optional[int] = None
    failed_recipients: Optional[List[str]] = None
    unsubscribed_recipients: Optional[List[str]] = None
    rate_limit: Optional[RateLimitStatus] = None
    error: Optional[str] = None
