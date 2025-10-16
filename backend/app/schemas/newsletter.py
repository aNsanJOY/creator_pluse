from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class NewsletterStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    SCHEDULED = "scheduled"


class NewsletterBase(BaseModel):
    title: str
    content: str


class NewsletterCreate(NewsletterBase):
    pass


class NewsletterUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[NewsletterStatus] = None


class NewsletterResponse(NewsletterBase):
    id: str
    user_id: str
    status: NewsletterStatus
    sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NewsletterSampleBase(BaseModel):
    content: str
    title: Optional[str] = None


class NewsletterSampleCreate(NewsletterSampleBase):
    pass


class NewsletterSampleResponse(NewsletterSampleBase):
    id: str
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True
