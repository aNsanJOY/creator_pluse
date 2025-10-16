"""
API Usage Tracking Routes
Endpoints for viewing API usage statistics and rate limits
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client
from typing import Optional

from app.core.database import get_supabase
from app.api.dependencies import get_current_active_user
from app.services.api_usage_tracker import api_usage_tracker

router = APIRouter()


@router.get("/stats")
async def get_usage_stats(
    service: Optional[str] = Query(None, description="Filter by service name"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get API usage statistics for the current user
    
    Query Parameters:
    - service: Filter by service name (groq, twitter, youtube, etc.)
    - days: Number of days to look back (1-365, default 30)
    
    Returns:
    - total_calls: Total number of API calls
    - total_tokens: Total tokens used (for LLM services)
    - by_service: Breakdown by service
    - by_day: Daily breakdown
    """
    try:
        user_id = current_user["id"]
        
        stats = await api_usage_tracker.get_usage_stats(
            user_id=user_id,
            service_name=service,
            days=days
        )
        
        return {
            "success": True,
            "stats": stats
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch usage stats: {str(e)}"
        )


@router.get("/rate-limits")
async def get_rate_limits(
    service: Optional[str] = Query(None, description="Filter by service name"),
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get current rate limits for all services or a specific service
    
    Returns rate limit information including:
    - current_count: Current usage in the time window
    - limit_value: Maximum allowed calls
    - remaining: Calls remaining
    - reset_at: When the counter resets
    """
    try:
        user_id = current_user["id"]
        
        # Build query
        query = supabase.table("api_rate_limits").select("*").eq("user_id", user_id)
        
        if service:
            query = query.eq("service_name", service)
        
        result = query.execute()
        
        if not result.data:
            return {
                "success": True,
                "rate_limits": []
            }
        
        # Format rate limits
        rate_limits = []
        for limit in result.data:
            remaining = max(0, limit["limit_value"] - limit["current_count"])
            rate_limits.append({
                "service_name": limit["service_name"],
                "limit_type": limit["limit_type"],
                "current_count": limit["current_count"],
                "limit_value": limit["limit_value"],
                "remaining": remaining,
                "reset_at": limit["reset_at"],
                "percentage_used": round((limit["current_count"] / limit["limit_value"]) * 100, 2) if limit["limit_value"] > 0 else 0
            })
        
        return {
            "success": True,
            "rate_limits": rate_limits
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch rate limits: {str(e)}"
        )


@router.get("/rate-limits/{service}")
async def get_service_rate_limit(
    service: str,
    limit_type: str = Query("minute", description="minute, hour, day, or month"),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Check rate limit for a specific service and time window
    
    Path Parameters:
    - service: Service name (groq, twitter, youtube, etc.)
    
    Query Parameters:
    - limit_type: Time window (minute, hour, day, month)
    
    Returns:
    - can_call: Whether the user can make another call
    - current_count: Current usage
    - limit_value: Maximum allowed
    - remaining: Calls remaining
    - reset_at: When counter resets
    """
    try:
        user_id = current_user["id"]
        
        limit_info = await api_usage_tracker.check_rate_limit(
            user_id=user_id,
            service_name=service,
            limit_type=limit_type
        )
        
        return {
            "success": True,
            **limit_info
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check rate limit: {str(e)}"
        )


@router.get("/logs")
async def get_usage_logs(
    service: Optional[str] = Query(None, description="Filter by service name"),
    limit: int = Query(50, ge=1, le=500, description="Number of logs to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get detailed API usage logs
    
    Query Parameters:
    - service: Filter by service name
    - limit: Number of logs to return (1-500, default 50)
    - offset: Offset for pagination
    
    Returns paginated list of API call logs
    """
    try:
        user_id = current_user["id"]
        
        # Build query
        query = supabase.table("api_usage_logs").select("*").eq("user_id", user_id)
        
        if service:
            query = query.eq("service_name", service)
        
        # Get total count
        count_result = query.execute()
        total_count = len(count_result.data) if count_result.data else 0
        
        # Get paginated results
        result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        
        return {
            "success": True,
            "logs": result.data if result.data else [],
            "total": total_count,
            "limit": limit,
            "offset": offset
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch usage logs: {str(e)}"
        )


@router.get("/summary")
async def get_usage_summary(
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get a quick summary of API usage across all services
    
    Returns:
    - Today's usage
    - This month's usage
    - Rate limit status for key services
    """
    try:
        user_id = current_user["id"]
        
        # Get today's stats
        today_stats = await api_usage_tracker.get_usage_stats(
            user_id=user_id,
            days=1
        )
        
        # Get this month's stats
        month_stats = await api_usage_tracker.get_usage_stats(
            user_id=user_id,
            days=30
        )
        
        # Get Groq rate limits
        groq_minute_limit = await api_usage_tracker.check_rate_limit(
            user_id=user_id,
            service_name="groq",
            limit_type="minute"
        )
        
        groq_day_limit = await api_usage_tracker.check_rate_limit(
            user_id=user_id,
            service_name="groq",
            limit_type="day"
        )
        
        return {
            "success": True,
            "summary": {
                "today": {
                    "calls": today_stats["total_calls"],
                    "tokens": today_stats["total_tokens"]
                },
                "this_month": {
                    "calls": month_stats["total_calls"],
                    "tokens": month_stats["total_tokens"]
                },
                "groq_limits": {
                    "per_minute": groq_minute_limit,
                    "per_day": groq_day_limit
                }
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch usage summary: {str(e)}"
        )
