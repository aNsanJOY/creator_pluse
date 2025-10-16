"""
Pydantic models for Trends
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class TrendSignals(BaseModel):
    """Trend scoring signals"""
    frequency: float = Field(..., ge=0.0, le=1.0, description="Frequency score (0-1)")
    recency: float = Field(..., ge=0.0, le=1.0, description="Recency score (0-1)")
    engagement: float = Field(..., ge=0.0, le=1.0, description="Engagement score (0-1)")
    relevance: float = Field(..., ge=0.0, le=1.0, description="Relevance score (0-1)")


class TrendMetadata(BaseModel):
    """Trend metadata"""
    keywords: List[str] = Field(default_factory=list, description="Related keywords")
    category: str = Field(default="general", description="Topic category")
    content_count: int = Field(default=0, description="Number of content items")
    content_ids: List[str] = Field(default_factory=list, description="Related content IDs")


class TrendBase(BaseModel):
    """Base trend model"""
    topic: str = Field(..., min_length=1, max_length=500, description="Trend topic name")
    description: Optional[str] = Field(None, description="Trend description")
    score: float = Field(..., ge=0.0, le=1.0, description="Overall trend score (0-1)")


class TrendCreate(TrendBase):
    """Model for creating a trend"""
    signals: TrendSignals
    metadata: TrendMetadata
    manual_override: bool = Field(default=False, description="Manual override flag")


class TrendResponse(TrendBase):
    """Model for trend response"""
    id: str
    user_id: str
    signals: TrendSignals
    metadata: TrendMetadata
    manual_override: bool
    detected_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class TrendDetectionRequest(BaseModel):
    """Request model for trend detection"""
    days_back: int = Field(default=7, ge=1, le=30, description="Days to look back")
    min_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum score threshold")
    max_trends: int = Field(default=10, ge=1, le=50, description="Maximum trends to return")


class TrendDetectionResponse(BaseModel):
    """Response model for trend detection"""
    trends: List[Dict[str, Any]]
    total_content_analyzed: int
    detection_time: str
    message: Optional[str] = None


class TrendListResponse(BaseModel):
    """Response model for listing trends"""
    trends: List[Dict[str, Any]]
    total: int
    days_back: int


class TrendUpdateRequest(BaseModel):
    """Request model for updating trend"""
    manual_override: bool = Field(..., description="Manual override flag")
    override_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Manual score override")


class TrendUpdateResponse(BaseModel):
    """Response model for trend update"""
    success: bool
    message: str
    trend_id: str
