"""
Pydantic models for Content Summaries
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SummaryType(str, Enum):
    """Summary type enumeration"""
    BRIEF = "brief"
    STANDARD = "standard"
    DETAILED = "detailed"


class SummarySentiment(str, Enum):
    """Sentiment enumeration"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


class SummaryMetadata(BaseModel):
    """Summary metadata"""
    topics: List[str] = Field(default_factory=list, description="Related topics")
    sentiment: SummarySentiment = Field(default=SummarySentiment.NEUTRAL, description="Content sentiment")
    relevance_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Relevance score (0-1)")
    word_count: int = Field(default=0, description="Summary word count")
    source_url: Optional[str] = Field(None, description="Original content URL")
    source_title: Optional[str] = Field(None, description="Original content title")


class SummaryBase(BaseModel):
    """Base summary model"""
    title: str = Field(..., min_length=1, max_length=500, description="Summary title")
    key_points: List[str] = Field(default_factory=list, description="Key points/highlights")
    summary: str = Field(..., min_length=1, description="Summary text")


class SummaryCreate(SummaryBase):
    """Model for creating a summary"""
    content_id: str = Field(..., description="Content ID to summarize")
    summary_type: SummaryType = Field(default=SummaryType.STANDARD, description="Type of summary")
    force_regenerate: bool = Field(default=False, description="Force regeneration if exists")


class SummaryResponse(SummaryBase):
    """Model for summary response"""
    id: str
    content_id: str
    metadata: SummaryMetadata
    created_at: datetime
    
    class Config:
        from_attributes = True


class SummarizeContentRequest(BaseModel):
    """Request model for summarizing a single content item"""
    content_id: str = Field(..., description="Content ID to summarize")
    summary_type: SummaryType = Field(default=SummaryType.STANDARD, description="Type of summary")
    force_regenerate: bool = Field(default=False, description="Force regeneration")


class SummarizeBatchRequest(BaseModel):
    """Request model for batch summarization"""
    content_ids: List[str] = Field(..., min_items=1, max_items=50, description="Content IDs to summarize")
    summary_type: SummaryType = Field(default=SummaryType.STANDARD, description="Type of summary")


class SummarizeRecentRequest(BaseModel):
    """Request model for summarizing recent content"""
    days_back: int = Field(default=7, ge=1, le=30, description="Days to look back")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum items to summarize")
    summary_type: SummaryType = Field(default=SummaryType.STANDARD, description="Type of summary")


class SummaryListResponse(BaseModel):
    """Response model for listing summaries"""
    summaries: List[Dict[str, Any]]
    total: int
    message: Optional[str] = None


class SummarizationResult(BaseModel):
    """Result of a summarization operation"""
    content_id: str
    status: str  # "success" or "failed"
    summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BatchSummarizationResponse(BaseModel):
    """Response model for batch summarization"""
    results: List[SummarizationResult]
    total_requested: int
    successful: int
    failed: int
    processing_time: str
