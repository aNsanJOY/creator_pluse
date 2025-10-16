"""
Pydantic models for Feedback
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class FeedbackType(str, Enum):
    """Feedback type enumeration"""
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"


class FeedbackBase(BaseModel):
    """Base feedback model"""
    feedback_type: FeedbackType = Field(..., description="Type of feedback")
    section_id: Optional[str] = Field(None, description="Section ID if feedback is for a specific section")
    comment: Optional[str] = Field(None, max_length=1000, description="Optional text comment")


class FeedbackCreate(FeedbackBase):
    """Model for creating feedback"""
    newsletter_id: str = Field(..., description="Newsletter/Draft ID")


class FeedbackUpdate(BaseModel):
    """Model for updating feedback"""
    feedback_type: Optional[FeedbackType] = Field(None, description="Type of feedback")
    comment: Optional[str] = Field(None, max_length=1000, description="Optional text comment")


class FeedbackResponse(FeedbackBase):
    """Model for feedback response"""
    id: str
    user_id: str
    newsletter_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class FeedbackListResponse(BaseModel):
    """Response model for listing feedback"""
    feedback: list[FeedbackResponse]
    total: int


class FeedbackStats(BaseModel):
    """Feedback statistics for a user"""
    total_feedback: int
    thumbs_up_count: int
    thumbs_down_count: int
    positive_rate: float
    recent_feedback: list[FeedbackResponse]
