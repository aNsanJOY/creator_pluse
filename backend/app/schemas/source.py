from pydantic import BaseModel, HttpUrl, field_validator
from typing import Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum


# Common source types (extensible - not exhaustive)
class SourceType(str, Enum):
    TWITTER = "twitter"
    YOUTUBE = "youtube"
    RSS = "rss"
    SUBSTACK = "substack"
    MEDIUM = "medium"
    LINKEDIN = "linkedin"
    PODCAST = "podcast"
    NEWSLETTER = "newsletter"
    CUSTOM = "custom"  # For user-defined source types


class SourceStatus(str, Enum):
    ACTIVE = "active"
    ERROR = "error"
    PENDING = "pending"


class SourceBase(BaseModel):
    source_type: str  # Changed from SourceType enum to str for flexibility
    name: str
    url: Optional[HttpUrl] = None
    config: Optional[Dict[str, Any]] = None  # Additional configuration per source

    @field_validator('source_type')
    @classmethod
    def validate_source_type(cls, v: str) -> str:
        """Validate source type - allows any string but recommends known types"""
        # Convert to lowercase for consistency
        return v.lower()


class SourceCreate(SourceBase):
    credentials: Optional[Dict[str, Any]] = None


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[SourceStatus] = None
    credentials: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None


class SourceResponse(SourceBase):
    id: str
    user_id: str
    status: SourceStatus
    last_crawled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
