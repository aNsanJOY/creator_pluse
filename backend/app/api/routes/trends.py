"""
Trends API Routes
Endpoints for trend detection and management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from typing import List, Dict, Any
from datetime import datetime

from app.core.database import get_supabase
from app.api.dependencies import get_current_active_user
from app.services.trend_detector import trend_detector
from app.models.trend import (
    TrendDetectionRequest,
    TrendDetectionResponse,
    TrendListResponse,
    TrendUpdateRequest,
    TrendUpdateResponse
)

router = APIRouter()


@router.post("/detect", response_model=TrendDetectionResponse)
async def detect_trends(
    request: TrendDetectionRequest,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Detect trending topics from user's content sources
    
    This endpoint analyzes recent content from all user's sources and uses
    Groq LLM to identify trending topics with ensemble scoring.
    """
    try:
        user_id = current_user["id"]
        
        start_time = datetime.now()
        
        # Detect trends
        trends = await trend_detector.detect_trends(
            user_id=user_id,
            days_back=request.days_back,
            min_score=request.min_score,
            max_trends=request.max_trends
        )
        
        # Get content count for reporting
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=request.days_back)
        
        # Get user's sources
        sources_result = supabase.table("sources").select("id").eq(
            "user_id", user_id
        ).eq("status", "active").execute()
        
        content_count = 0
        if sources_result.data:
            source_ids = [s["id"] for s in sources_result.data]
            content_result = supabase.table("source_content_cache").select(
                "id", count="exact"
            ).in_("source_id", source_ids).gte(
                "created_at", cutoff_date.isoformat()
            ).execute()
            content_count = content_result.count if hasattr(content_result, 'count') else len(content_result.data or [])
        
        end_time = datetime.now()
        detection_time = (end_time - start_time).total_seconds()
        
        message = None
        if not trends:
            message = "No trends detected. Try adjusting the parameters or adding more content sources."
        elif len(trends) < request.max_trends:
            message = f"Found {len(trends)} trends (fewer than requested). Consider lowering min_score or increasing days_back."
        
        return TrendDetectionResponse(
            trends=trends,
            total_content_analyzed=content_count,
            detection_time=f"{detection_time:.2f}s",
            message=message
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect trends: {str(e)}"
        )


@router.get("/list", response_model=TrendListResponse)
async def list_trends(
    days_back: int = 7,
    limit: int = 20,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get previously detected trends for the user
    
    Returns trends detected within the specified time period,
    sorted by score (highest first).
    """
    try:
        user_id = current_user["id"]
        
        trends = await trend_detector.get_user_trends(
            user_id=user_id,
            days_back=days_back,
            limit=limit
        )
        
        return TrendListResponse(
            trends=trends,
            total=len(trends),
            days_back=days_back
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch trends: {str(e)}"
        )


@router.get("/{trend_id}")
async def get_trend(
    trend_id: str,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get a specific trend by ID
    """
    try:
        user_id = current_user["id"]
        
        # Fetch trend
        result = supabase.table("trends").select("*").eq("id", trend_id).eq(
            "user_id", user_id
        ).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trend not found"
            )
        
        return result.data[0]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch trend: {str(e)}"
        )


@router.put("/{trend_id}/override", response_model=TrendUpdateResponse)
async def update_trend_override(
    trend_id: str,
    request: TrendUpdateRequest,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Update manual override flag for a trend
    
    Allows users to manually promote or demote trends by setting
    the manual_override flag and optionally adjusting the score.
    """
    try:
        user_id = current_user["id"]
        
        # Verify trend belongs to user
        result = supabase.table("trends").select("id").eq("id", trend_id).eq(
            "user_id", user_id
        ).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trend not found"
            )
        
        # Update trend
        success = await trend_detector.update_trend_override(
            trend_id=trend_id,
            manual_override=request.manual_override,
            override_score=request.override_score
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update trend"
            )
        
        message = "Trend override updated successfully"
        if request.manual_override:
            message += " (manually promoted)"
        else:
            message += " (automatic scoring restored)"
        
        return TrendUpdateResponse(
            success=True,
            message=message,
            trend_id=trend_id
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update trend: {str(e)}"
        )


@router.delete("/{trend_id}")
async def delete_trend(
    trend_id: str,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Delete a trend
    
    Removes a trend from the database. Useful for removing
    false positives or irrelevant trends.
    """
    try:
        user_id = current_user["id"]
        
        # Verify trend belongs to user
        result = supabase.table("trends").select("id").eq("id", trend_id).eq(
            "user_id", user_id
        ).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trend not found"
            )
        
        # Delete trend
        supabase.table("trends").delete().eq("id", trend_id).execute()
        
        return {
            "success": True,
            "message": "Trend deleted successfully",
            "trend_id": trend_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete trend: {str(e)}"
        )


@router.post("/batch-detect")
async def batch_detect_trends_for_all_users(
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Batch detect trends for all users (admin only)
    
    This endpoint is intended for scheduled jobs to detect trends
    for all active users. In production, this should be restricted
    to admin users or run as a background task.
    """
    try:
        # TODO: Add admin check
        # For now, only allow for the current user
        user_id = current_user["id"]
        
        trends = await trend_detector.detect_trends(
            user_id=user_id,
            days_back=7,
            min_score=0.5,
            max_trends=10
        )
        
        return {
            "success": True,
            "message": f"Detected {len(trends)} trends",
            "trends_count": len(trends)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to batch detect trends: {str(e)}"
        )
