"""
Content API Routes
Endpoints for content summarization and management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from typing import List, Dict, Any
from datetime import datetime

from app.core.database import get_supabase
from app.api.dependencies import get_current_active_user
from app.services.content_summarizer import content_summarizer
from app.models.summary import (
    SummarizeContentRequest,
    SummarizeBatchRequest,
    SummarizeRecentRequest,
    SummaryListResponse,
    SummarizationResult,
    BatchSummarizationResponse
)

router = APIRouter()


@router.post("/summarize")
async def summarize_content(
    request: SummarizeContentRequest,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Generate a summary for a specific content item
    
    Uses Groq LLM to create a structured summary with title, key points,
    and summary text. Summaries are cached in the database.
    """
    try:
        user_id = current_user["id"]
        
        summary = await content_summarizer.summarize_content(
            content_id=request.content_id,
            user_id=user_id,
            summary_type=request.summary_type.value,
            force_regenerate=request.force_regenerate
        )
        
        return {
            "success": True,
            "summary": summary,
            "message": "Summary generated successfully"
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}"
        )


@router.post("/summarize/batch", response_model=BatchSummarizationResponse)
async def summarize_batch(
    request: SummarizeBatchRequest,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Generate summaries for multiple content items
    
    Processes multiple content items in batch. Returns results for all items,
    including any that failed to summarize.
    """
    try:
        user_id = current_user["id"]
        start_time = datetime.now()
        
        summaries = await content_summarizer.summarize_batch(
            content_ids=request.content_ids,
            user_id=user_id,
            summary_type=request.summary_type.value
        )
        
        # Process results
        results = []
        successful = 0
        failed = 0
        
        for summary in summaries:
            if "error" in summary:
                results.append(SummarizationResult(
                    content_id=summary["content_id"],
                    status="failed",
                    error=summary["error"]
                ))
                failed += 1
            else:
                results.append(SummarizationResult(
                    content_id=summary["content_id"],
                    status="success",
                    summary=summary
                ))
                successful += 1
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        return BatchSummarizationResponse(
            results=results,
            total_requested=len(request.content_ids),
            successful=successful,
            failed=failed,
            processing_time=f"{processing_time:.2f}s"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process batch summarization: {str(e)}"
        )


@router.post("/summarize/recent", response_model=BatchSummarizationResponse)
async def summarize_recent(
    request: SummarizeRecentRequest,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Summarize recent unsummarized content
    
    Automatically finds and summarizes recent content that doesn't have
    summaries yet. Useful for batch processing new content.
    """
    try:
        user_id = current_user["id"]
        start_time = datetime.now()
        
        summaries = await content_summarizer.summarize_recent_content(
            user_id=user_id,
            days_back=request.days_back,
            limit=request.limit,
            summary_type=request.summary_type.value
        )
        
        # Process results
        results = []
        successful = 0
        failed = 0
        
        for summary in summaries:
            if "error" in summary:
                results.append(SummarizationResult(
                    content_id=summary.get("content_id", "unknown"),
                    status="failed",
                    error=summary["error"]
                ))
                failed += 1
            else:
                results.append(SummarizationResult(
                    content_id=summary["content_id"],
                    status="success",
                    summary=summary
                ))
                successful += 1
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        return BatchSummarizationResponse(
            results=results,
            total_requested=len(summaries),
            successful=successful,
            failed=failed,
            processing_time=f"{processing_time:.2f}s"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to summarize recent content: {str(e)}"
        )


@router.get("/summaries")
async def list_summaries(
    content_ids: str = None,  # Comma-separated list
    limit: int = 50,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get summaries for specific content items or recent summaries
    
    If content_ids provided, returns summaries for those items.
    Otherwise, returns recent summaries for the user.
    """
    try:
        user_id = current_user["id"]
        
        if content_ids:
            # Parse comma-separated content IDs
            id_list = [id.strip() for id in content_ids.split(",")]
            
            summaries_dict = await content_summarizer.get_summaries_for_content(
                content_ids=id_list,
                user_id=user_id
            )
            
            summaries = list(summaries_dict.values())
            message = f"Found {len(summaries)} summaries for {len(id_list)} content items"
        else:
            # Get recent summaries
            result = supabase.table("content_summaries").select("*").eq(
                "user_id", user_id
            ).order("created_at", desc=True).limit(limit).execute()
            
            summaries = []
            for s in result.data or []:
                summaries.append({
                    "id": s["id"],
                    "content_id": s["content_id"],
                    "title": s["title"],
                    "key_points": s.get("key_points", []),
                    "summary": s["summary_text"],
                    "metadata": s.get("metadata", {}),
                    "created_at": s["created_at"]
                })
            
            message = f"Found {len(summaries)} recent summaries"
        
        return SummaryListResponse(
            summaries=summaries,
            total=len(summaries),
            message=message
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch summaries: {str(e)}"
        )


@router.get("/summaries/{summary_id}")
async def get_summary(
    summary_id: str,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get a specific summary by ID
    """
    try:
        user_id = current_user["id"]
        
        result = supabase.table("content_summaries").select("*").eq(
            "id", summary_id
        ).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Summary not found"
            )
        
        summary = result.data[0]
        
        return {
            "id": summary["id"],
            "content_id": summary["content_id"],
            "title": summary["title"],
            "key_points": summary.get("key_points", []),
            "summary": summary["summary_text"],
            "summary_type": summary.get("summary_type", "standard"),
            "metadata": summary.get("metadata", {}),
            "model_used": summary.get("model_used"),
            "created_at": summary["created_at"],
            "updated_at": summary.get("updated_at")
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch summary: {str(e)}"
        )


@router.delete("/summaries/{summary_id}")
async def delete_summary(
    summary_id: str,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Delete a summary
    
    Useful for removing outdated or incorrect summaries.
    The content can be re-summarized later if needed.
    """
    try:
        user_id = current_user["id"]
        
        # Verify summary belongs to user
        result = supabase.table("content_summaries").select("id").eq(
            "id", summary_id
        ).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Summary not found"
            )
        
        # Delete summary
        supabase.table("content_summaries").delete().eq("id", summary_id).execute()
        
        return {
            "success": True,
            "message": "Summary deleted successfully",
            "summary_id": summary_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete summary: {str(e)}"
        )


@router.get("/content/{content_id}")
async def get_content_with_summary(
    content_id: str,
    include_summary: bool = True,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get content item with optional summary
    
    Returns the full content item and its summary (if available).
    """
    try:
        user_id = current_user["id"]
        
        # Fetch content
        content_result = supabase.table("source_content_cache").select(
            "*, sources!inner(user_id, name, source_type)"
        ).eq("id", content_id).execute()
        
        if not content_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        
        content = content_result.data[0]
        
        # Check authorization
        if content["sources"]["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        response = {
            "id": content["id"],
            "source_id": content["source_id"],
            "source_name": content["sources"]["name"],
            "source_type": content["sources"]["source_type"],
            "content_type": content["content_type"],
            "title": content.get("title"),
            "content": content.get("content"),
            "url": content.get("url"),
            "metadata": content.get("metadata", {}),
            "published_at": content.get("published_at"),
            "created_at": content["created_at"]
        }
        
        # Include summary if requested
        if include_summary:
            summaries = await content_summarizer.get_summaries_for_content(
                content_ids=[content_id],
                user_id=user_id
            )
            response["summary"] = summaries.get(content_id)
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch content: {str(e)}"
        )
