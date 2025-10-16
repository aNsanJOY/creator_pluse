"""
Dashboard API Routes
Endpoints for dashboard statistics and overview
"""

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from app.core.database import get_supabase
from app.api.dependencies import get_current_active_user

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get dashboard overview statistics
    
    Returns counts and summaries for:
    - Connected sources
    - Recent drafts
    - Sent newsletters
    - Content items
    - Trends detected
    """
    try:
        user_id = current_user["id"]
        
        # Get sources count
        sources_result = supabase.table("sources").select("id, status, source_type").eq(
            "user_id", user_id
        ).execute()
        
        sources = sources_result.data or []
        sources_count = len(sources)
        active_sources = sum(1 for s in sources if s.get("status") == "active")
        
        # Count by source type
        sources_by_type = {}
        for source in sources:
            source_type = source.get("source_type", "unknown")
            sources_by_type[source_type] = sources_by_type.get(source_type, 0) + 1
        
        # Get drafts count
        drafts_result = supabase.table("newsletter_drafts").select(
            "id, status, generated_at, email_sent"
        ).eq("user_id", user_id).execute()
        
        drafts = drafts_result.data or []
        total_drafts = len(drafts)
        published_drafts = sum(1 for d in drafts if d.get("status") == "published")
        pending_drafts = sum(1 for d in drafts if d.get("status") in ["ready", "editing"])
        emails_sent = sum(1 for d in drafts if d.get("email_sent"))
        
        # Get content items count
        if sources:
            source_ids = [s["id"] for s in sources]
            content_result = supabase.table("source_content_cache").select(
                "id", count="exact"
            ).in_("source_id", source_ids).execute()
            content_count = content_result.count if hasattr(content_result, 'count') else len(content_result.data or [])
        else:
            content_count = 0
        
        # Get trends count
        trends_result = supabase.table("trends").select("id", count="exact").eq(
            "user_id", user_id
        ).execute()
        trends_count = trends_result.count if hasattr(trends_result, 'count') else len(trends_result.data or [])
        
        # Get voice samples count
        samples_result = supabase.table("newsletter_samples").select("id", count="exact").eq(
            "user_id", user_id
        ).execute()
        samples_count = samples_result.count if hasattr(samples_result, 'count') else len(samples_result.data or [])
        
        # Get email stats (last 30 days)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        email_logs_result = supabase.table("email_delivery_log").select("status").eq(
            "user_id", user_id
        ).gte("created_at", thirty_days_ago).execute()
        
        email_logs = email_logs_result.data or []
        emails_sent_30d = sum(1 for log in email_logs if log.get("status") == "sent")
        emails_failed_30d = sum(1 for log in email_logs if log.get("status") == "failed")
        
        # Get rate limit info
        from app.services.email_service import email_service
        rate_limit = await email_service.check_rate_limit(user_id)
        
        return {
            "success": True,
            "stats": {
                "sources": {
                    "total": sources_count,
                    "active": active_sources,
                    "by_type": sources_by_type
                },
                "drafts": {
                    "total": total_drafts,
                    "published": published_drafts,
                    "pending": pending_drafts,
                    "emails_sent": emails_sent
                },
                "content": {
                    "total_items": content_count,
                    "trends_detected": trends_count
                },
                "voice": {
                    "samples_uploaded": samples_count,
                    "profile_trained": samples_count > 0
                },
                "email": {
                    "sent_30d": emails_sent_30d,
                    "failed_30d": emails_failed_30d,
                    "rate_limit": rate_limit
                }
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard stats: {str(e)}"
        )


@router.get("/recent-drafts")
async def get_recent_drafts(
    limit: int = 5,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get recent newsletter drafts
    
    Returns the most recent drafts with basic information.
    """
    try:
        user_id = current_user["id"]
        
        result = supabase.table("newsletter_drafts").select(
            "id, title, status, generated_at, published_at, email_sent, metadata"
        ).eq("user_id", user_id).order(
            "generated_at", desc=True
        ).limit(limit).execute()
        
        drafts = result.data or []
        
        return {
            "success": True,
            "drafts": drafts,
            "total": len(drafts)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch recent drafts: {str(e)}"
        )


@router.get("/recent-newsletters")
async def get_recent_newsletters(
    limit: int = 5,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get recent sent newsletters
    
    Returns the most recent published newsletters.
    """
    try:
        user_id = current_user["id"]
        
        result = supabase.table("newsletter_drafts").select(
            "id, title, status, published_at, email_sent, email_sent_at, metadata"
        ).eq("user_id", user_id).eq(
            "status", "published"
        ).order(
            "published_at", desc=True
        ).limit(limit).execute()
        
        newsletters = result.data or []
        
        return {
            "success": True,
            "newsletters": newsletters,
            "total": len(newsletters)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch recent newsletters: {str(e)}"
        )


@router.get("/activity")
async def get_recent_activity(
    days: int = 7,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get recent activity timeline
    
    Returns recent events like drafts generated, newsletters sent, sources added.
    """
    try:
        user_id = current_user["id"]
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        activity = []
        
        # Get recent drafts
        drafts_result = supabase.table("newsletter_drafts").select(
            "id, title, status, generated_at, published_at"
        ).eq("user_id", user_id).gte(
            "generated_at", since_date
        ).order("generated_at", desc=True).limit(10).execute()
        
        for draft in drafts_result.data or []:
            activity.append({
                "type": "draft_generated",
                "title": f"Draft generated: {draft['title']}",
                "timestamp": draft["generated_at"],
                "data": draft
            })
            
            if draft.get("published_at"):
                activity.append({
                    "type": "newsletter_published",
                    "title": f"Newsletter published: {draft['title']}",
                    "timestamp": draft["published_at"],
                    "data": draft
                })
        
        # Get recent sources
        sources_result = supabase.table("sources").select(
            "id, name, source_type, created_at"
        ).eq("user_id", user_id).gte(
            "created_at", since_date
        ).order("created_at", desc=True).limit(10).execute()
        
        for source in sources_result.data or []:
            activity.append({
                "type": "source_added",
                "title": f"Source connected: {source['name']}",
                "timestamp": source["created_at"],
                "data": source
            })
        
        # Get recent voice samples
        samples_result = supabase.table("newsletter_samples").select(
            "id, title, created_at"
        ).eq("user_id", user_id).gte(
            "created_at", since_date
        ).order("created_at", desc=True).limit(10).execute()
        
        for sample in samples_result.data or []:
            activity.append({
                "type": "voice_sample_uploaded",
                "title": f"Voice sample uploaded: {sample.get('title', 'Untitled')}",
                "timestamp": sample["created_at"],
                "data": sample
            })
        
        # Sort by timestamp
        activity.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "success": True,
            "activity": activity[:20],  # Return top 20 most recent
            "total": len(activity)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch recent activity: {str(e)}"
        )
