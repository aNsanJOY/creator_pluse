from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class SourceType(str, Enum):
    """Supported source types"""
    TWITTER = "twitter"
    YOUTUBE = "youtube"
    RSS = "rss"
    SUBSTACK = "substack"
    MEDIUM = "medium"
    GITHUB = "github"
    REDDIT = "reddit"
    LINKEDIN = "linkedin"
    PODCAST = "podcast"
    NEWSLETTER = "newsletter"
    CUSTOM = "custom"


class SourceStatus(str, Enum):
    """Source status"""
    ACTIVE = "active"
    ERROR = "error"
    PENDING = "pending"


class SourceBase(BaseModel):
    """Base source model"""
    source_type: SourceType
    name: str = Field(..., min_length=1, max_length=255)
    url: Optional[str] = None
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SourceCreate(SourceBase):
    """Model for creating a new source"""
    credentials: Optional[Dict[str, Any]] = None


class SourceUpdate(BaseModel):
    """Model for updating a source"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    credentials: Optional[Dict[str, Any]] = None
    status: Optional[SourceStatus] = None


class SourceResponse(SourceBase):
    """Model for source response"""
    id: str
    user_id: str
    status: SourceStatus
    last_crawled_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SourceStatusResponse(BaseModel):
    """Model for source status check response"""
    id: str
    status: SourceStatus
    last_crawled_at: Optional[datetime] = None
    error_message: Optional[str] = None
    is_healthy: bool
