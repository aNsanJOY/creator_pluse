"""
RSS Feed integration endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from supabase import Client
from typing import Optional
from pydantic import BaseModel, HttpUrl
import feedparser

from app.core.database import get_supabase
from app.api.dependencies import get_current_active_user
from app.models.source import SourceType, SourceStatus
from app.utils.validators import SourceValidator
from app.services.crawler import crawl_source_task


router = APIRouter()


class RSSFeedAddRequest(BaseModel):
    """Request body for adding RSS feed"""
    feed_url: HttpUrl
    name: Optional[str] = None


class RSSSourceResponse(BaseModel):
    """Response after successful RSS feed connection"""
    source_id: str
    name: str
    feed_url: str
    status: str
    feed_title: Optional[str] = None
    feed_description: Optional[str] = None
    entry_count: int


@router.post("", response_model=RSSSourceResponse, status_code=status.HTTP_201_CREATED)
async def add_rss_feed(
    feed_data: RSSFeedAddRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Add a new RSS feed source.
    Validates the feed URL and creates a source entry.
    """
    try:
        feed_url = str(feed_data.feed_url)
        
        # Validate RSS feed
        is_valid, error_message = SourceValidator.validate_rss_feed(feed_url)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # Parse feed to get metadata
        feed = feedparser.parse(feed_url)
        
        # Extract feed information
        feed_title = feed.feed.get('title', 'Untitled Feed')
        feed_description = feed.feed.get('description', '')
        entry_count = len(feed.entries)
        
        # Use provided name or default to feed title
        source_name = feed_data.name if feed_data.name else f"RSS - {feed_title}"
        
        # Check if source already exists for this user
        existing = supabase.table("sources").select("*").eq(
            "user_id", current_user['id']
        ).eq("source_type", "rss").eq("url", feed_url).execute()
        
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This RSS feed is already connected"
            )
        
        # Create new source
        new_source = {
            "user_id": current_user['id'],
            "source_type": SourceType.RSS.value,
            "name": source_name,
            "url": feed_url,
            "credentials": {},  # RSS feeds don't require credentials
            "config": {
                "feed_url": feed_url,
                "feed_title": feed_title,
                "feed_description": feed_description,
                "feed_type": feed.version if hasattr(feed, 'version') else 'unknown'
            },
            "status": SourceStatus.ACTIVE.value
        }
        
        result = supabase.table("sources").insert(new_source).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create RSS source"
            )
        
        source_id = result.data[0]['id']
        
        # Trigger initial crawl in background
        background_tasks.add_task(crawl_source_task, source_id)
        
        return RSSSourceResponse(
            source_id=source_id,
            name=source_name,
            feed_url=feed_url,
            status=SourceStatus.ACTIVE.value,
            feed_title=feed_title,
            feed_description=feed_description,
            entry_count=entry_count
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add RSS feed: {str(e)}"
        )


@router.get("/{source_id}/preview")
async def preview_rss_feed(
    source_id: str,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Preview RSS feed entries without storing them.
    Returns the latest entries from the feed.
    """
    try:
        # Verify source exists and belongs to user
        result = supabase.table("sources").select("*").eq(
            "id", source_id
        ).eq("user_id", current_user['id']).eq("source_type", "rss").execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RSS source not found"
            )
        
        source = result.data[0]
        feed_url = source['url']
        
        # Parse feed
        feed = feedparser.parse(feed_url)
        
        if feed.bozo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to parse RSS feed"
            )
        
        # Format entries for preview
        entries = []
        for entry in feed.entries[:10]:  # Limit to 10 most recent
            published_at = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                from datetime import datetime
                published_at = datetime(*entry.published_parsed[:6]).isoformat()
            
            entries.append({
                "title": entry.get('title', 'Untitled'),
                "link": entry.get('link', ''),
                "published_at": published_at,
                "summary": entry.get('summary', '')[:200] + '...' if entry.get('summary') else ''
            })
        
        return {
            "feed_title": feed.feed.get('title', ''),
            "feed_url": feed_url,
            "entry_count": len(feed.entries),
            "entries": entries
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview RSS feed: {str(e)}"
        )


@router.delete("/{source_id}")
async def disconnect_rss_feed(
    source_id: str,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Disconnect RSS feed source.
    """
    try:
        # Verify source exists and belongs to user
        result = supabase.table("sources").select("*").eq(
            "id", source_id
        ).eq("user_id", current_user['id']).eq("source_type", "rss").execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RSS source not found"
            )
        
        # Delete source (cascade will delete associated content)
        supabase.table("sources").delete().eq("id", source_id).execute()
        
        return {"message": "RSS feed disconnected successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect RSS feed: {str(e)}"
        )


@router.post("/{source_id}/refresh")
async def refresh_rss_feed(
    source_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Manually trigger a refresh/crawl for an RSS feed.
    """
    try:
        # Verify source exists and belongs to user
        result = supabase.table("sources").select("*").eq(
            "id", source_id
        ).eq("user_id", current_user['id']).eq("source_type", "rss").execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RSS source not found"
            )
        
        source = result.data[0]
        
        # Check if source is active
        if source["status"] != SourceStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot refresh RSS feed with status: {source['status']}"
            )
        
        # Trigger background crawl
        background_tasks.add_task(crawl_source_task, source_id)
        
        return {
            "message": "RSS feed refresh started",
            "source_id": source_id,
            "source_name": source["name"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh RSS feed: {str(e)}"
        )


@router.get("/{source_id}/stats")
async def get_rss_stats(
    source_id: str,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get RSS feed statistics and cached content count.
    """
    try:
        # Verify source exists and belongs to user
        result = supabase.table("sources").select("*").eq(
            "id", source_id
        ).eq("user_id", current_user['id']).eq("source_type", "rss").execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RSS source not found"
            )
        
        source = result.data[0]
        
        # Get cached content count
        content_result = supabase.table("source_content_cache").select(
            "id", count="exact"
        ).eq("source_id", source_id).execute()
        
        cached_count = content_result.count if content_result.count else 0
        
        # Parse feed for current stats
        feed_url = source['url']
        feed = feedparser.parse(feed_url)
        
        return {
            "source_id": source_id,
            "name": source['name'],
            "feed_url": feed_url,
            "feed_title": feed.feed.get('title', ''),
            "feed_type": source['config'].get('feed_type', 'unknown'),
            "status": source['status'],
            "last_crawled_at": source.get('last_crawled_at'),
            "cached_entries": cached_count,
            "current_entries": len(feed.entries),
            "feed_updated": feed.feed.get('updated', None)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get RSS stats: {str(e)}"
        )
