"""
Pydantic models for Newsletter Drafts
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DraftStatus(str, Enum):
    """Draft status enumeration"""
    GENERATING = "generating"
    READY = "ready"
    EDITING = "editing"
    PUBLISHED = "published"
    FAILED = "failed"


class DraftSection(BaseModel):
    """Individual section within a draft"""
    id: str = Field(..., description="Section ID")
    type: str = Field(..., description="Section type (intro, topic, conclusion)")
    title: Optional[str] = Field(None, description="Section title")
    content: str = Field(..., description="Section content")
    source_ids: List[str] = Field(default_factory=list, description="Related content IDs")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DraftBase(BaseModel):
    """Base draft model"""
    title: str = Field(..., min_length=1, max_length=500, description="Draft title")
    sections: List[DraftSection] = Field(default_factory=list, description="Draft sections")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Draft metadata")


class DraftCreate(BaseModel):
    """Model for creating a draft"""
    user_id: str = Field(..., description="User ID")
    topic_count: int = Field(default=5, ge=3, le=10, description="Number of topics to include")
    days_back: int = Field(default=7, ge=1, le=30, description="Days to look back for content")
    force_regenerate: bool = Field(default=False, description="Force regeneration")


class DraftUpdate(BaseModel):
    """Model for updating a draft"""
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="Draft title")
    sections: Optional[List[DraftSection]] = Field(None, description="Draft sections")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Draft metadata")


class DraftResponse(DraftBase):
    """Model for draft response"""
    id: str
    user_id: str
    status: DraftStatus
    generated_at: datetime
    published_at: Optional[datetime] = None
    email_sent: bool = False
    
    class Config:
        from_attributes = True


class GenerateDraftRequest(BaseModel):
    """Request model for generating a draft"""
    topic_count: int = Field(default=5, ge=3, le=10, description="Number of topics to include")
    days_back: int = Field(default=7, ge=1, le=30, description="Days to look back for content")
    use_voice_profile: bool = Field(default=True, description="Use user's voice profile")
    force_regenerate: bool = Field(default=False, description="Force regeneration")


class RegenerateDraftRequest(BaseModel):
    """Request model for regenerating a draft"""
    topic_count: Optional[int] = Field(None, ge=3, le=10, description="Number of topics")
    use_voice_profile: bool = Field(default=True, description="Use user's voice profile")


class PublishDraftRequest(BaseModel):
    """Request model for publishing a draft"""
    send_email: bool = Field(default=True, description="Send email to subscribers")
    recipient_emails: Optional[List[str]] = Field(None, description="Recipient email addresses")
    subject: Optional[str] = Field(None, description="Email subject (overrides draft title)")


class DraftListResponse(BaseModel):
    """Response model for listing drafts"""
    drafts: List[DraftResponse]
    total: int
    message: Optional[str] = None


class DraftGenerationResult(BaseModel):
    """Result of draft generation"""
    draft_id: str
    status: DraftStatus
    message: str
    draft: Optional[DraftResponse] = None
    error: Optional[str] = None
