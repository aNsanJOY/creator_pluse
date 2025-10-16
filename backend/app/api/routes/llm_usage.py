"""
LLM API Usage Tracking Routes
Endpoints for viewing LLM usage statistics and rate limits
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client

from app.core.database import get_supabase
from app.api.dependencies import get_current_active_user
from app.services.llm_usage_tracker import llm_usage_tracker

router = APIRouter()


@router.get("/stats")
async def get_llm_usage_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get LLM API usage statistics for the current user
    
    Query Parameters:
    - days: Number of days to look back (1-365, default 30)
    
    Returns:
    - total_calls: Total number of LLM API calls
    - total_tokens: Total tokens used
    - total_prompt_tokens: Total input tokens
    - total_completion_tokens: Total output tokens
    - by_model: Breakdown by LLM model
    - by_day: Daily breakdown
    """
    try:
        user_id = current_user["id"]
        
        stats = await llm_usage_tracker.get_usage_stats(
            user_id=user_id,
            days=days
        )
        
        return {
            "success": True,
            "stats": stats
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch LLM usage stats: {str(e)}"
        )


@router.get("/rate-limits")
async def get_llm_rate_limits(
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get current LLM rate limits for the user
    
    Returns rate limit information including:
    - current_count: Current usage in the time window
    - limit_value: Maximum allowed calls
    - remaining: Calls remaining
    - reset_at: When the counter resets
    """
    try:
        user_id = current_user["id"]
        
        # Get all rate limits for user
        result = supabase.table("llm_rate_limits").select("*").eq("user_id", user_id).execute()
        
        if not result.data:
            # Create default rate limits
            await llm_usage_tracker.check_rate_limit(user_id, "minute")
            await llm_usage_tracker.check_rate_limit(user_id, "day")
            result = supabase.table("llm_rate_limits").select("*").eq("user_id", user_id).execute()
        
        # Format rate limits
        rate_limits = []
        for limit in result.data if result.data else []:
            remaining = max(0, limit["limit_value"] - limit["current_count"])
            rate_limits.append({
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
            detail=f"Failed to fetch LLM rate limits: {str(e)}"
        )


@router.get("/rate-limit/{limit_type}")
async def get_llm_rate_limit(
    limit_type: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Check LLM rate limit for a specific time window
    
    Path Parameters:
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
        
        limit_info = await llm_usage_tracker.check_rate_limit(
            user_id=user_id,
            limit_type=limit_type
        )
        
        return {
            "success": True,
            **limit_info
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check LLM rate limit: {str(e)}"
        )


@router.get("/logs")
async def get_llm_usage_logs(
    limit: int = Query(50, ge=1, le=500, description="Number of logs to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get detailed LLM API usage logs
    
    Query Parameters:
    - limit: Number of logs to return (1-500, default 50)
    - offset: Offset for pagination
    
    Returns paginated list of LLM API call logs
    """
    try:
        user_id = current_user["id"]
        
        # Get total count
        count_result = supabase.table("llm_usage_logs").select("*").eq("user_id", user_id).execute()
        total_count = len(count_result.data) if count_result.data else 0
        
        # Get paginated results
        result = supabase.table("llm_usage_logs").select("*").eq(
            "user_id", user_id
        ).order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        
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
            detail=f"Failed to fetch LLM usage logs: {str(e)}"
        )


@router.get("/summary")
async def get_llm_usage_summary(
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get a quick summary of LLM API usage
    
    Returns:
    - Today's usage
    - This month's usage
    - Rate limit status (per minute and per day)
    """
    try:
        user_id = current_user["id"]
        
        # Get today's stats
        today_stats = await llm_usage_tracker.get_usage_stats(
            user_id=user_id,
            days=1
        )
        
        # Get this month's stats
        month_stats = await llm_usage_tracker.get_usage_stats(
            user_id=user_id,
            days=30
        )
        
        # Get rate limits
        minute_limit = await llm_usage_tracker.check_rate_limit(
            user_id=user_id,
            limit_type="minute"
        )
        
        day_limit = await llm_usage_tracker.check_rate_limit(
            user_id=user_id,
            limit_type="day"
        )
        
        return {
            "success": True,
            "summary": {
                "today": {
                    "calls": today_stats["total_calls"],
                    "tokens": today_stats["total_tokens"],
                    "prompt_tokens": today_stats["total_prompt_tokens"],
                    "completion_tokens": today_stats["total_completion_tokens"]
                },
                "this_month": {
                    "calls": month_stats["total_calls"],
                    "tokens": month_stats["total_tokens"],
                    "prompt_tokens": month_stats["total_prompt_tokens"],
                    "completion_tokens": month_stats["total_completion_tokens"]
                },
                "rate_limits": {
                    "per_minute": minute_limit,
                    "per_day": day_limit
                }
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch LLM usage summary: {str(e)}"
        )
