from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class FeedbackType(str, Enum):
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"


class FeedbackBase(BaseModel):
    feedback_type: FeedbackType
    section_id: Optional[str] = None
    comment: Optional[str] = None


class FeedbackCreate(FeedbackBase):
    newsletter_id: str


class FeedbackResponse(FeedbackBase):
    id: str
    user_id: str
    newsletter_id: str
    created_at: datetime

    class Config:
        from_attributes = True
