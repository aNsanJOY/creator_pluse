"""
Draft API Routes
Endpoints for newsletter draft generation, management, and publishing
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from supabase import Client
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import asyncio

from app.core.database import get_supabase
from app.api.dependencies import get_current_active_user
from app.services.draft_generator import draft_generator
from app.models.draft import (
    GenerateDraftRequest,
    RegenerateDraftRequest,
    PublishDraftRequest,
    DraftResponse,
    DraftUpdate,
    DraftListResponse,
    DraftGenerationResult,
    DraftStatus
)

router = APIRouter()


@router.get("/debug/content-status")
async def get_content_status(
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Debug endpoint to check content availability for draft generation
    """
    try:
        user_id = current_user["id"]
        
        # Get sources
        sources_result = supabase.table("sources").select("id, name, source_type, status").eq(
            "user_id", user_id
        ).execute()
        
        sources = sources_result.data if sources_result.data else []
        source_ids = [s["id"] for s in sources]
        
        # Get content count
        content_count = 0
        if source_ids:
            content_result = supabase.table("source_content_cache").select(
                "id", count="exact"
            ).in_("source_id", source_ids).execute()
            content_count = content_result.count if hasattr(content_result, 'count') else len(content_result.data or [])
        
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
        
        return {
            "sources": {
                "total": len(sources),
                "active": sum(1 for s in sources if s["status"] == "active"),
                "by_type": {s["source_type"]: sum(1 for x in sources if x["source_type"] == s["source_type"]) for s in sources}
            },
            "content_items": content_count,
            "trends_detected": trends_count,
            "voice_samples": samples_count,
            "can_generate_draft": content_count > 0,
            "recommendations": []
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get content status: {str(e)}"
        )


@router.post("/generate", response_model=DraftGenerationResult)
async def generate_draft(
    request: GenerateDraftRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Generate a new newsletter draft
    
    Creates a draft based on trending topics and content summaries.
    Uses the user's voice profile if available and requested.
    
    Returns immediately with status='generating' and the generation
    happens in the background. Poll the draft status to check completion.
    """
    try:
        user_id = current_user["id"]
        
        # Check if user already has a recent draft (within last hour)
        if not request.force_regenerate:
            one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
            
            recent_result = supabase.table("newsletter_drafts").select("id, status").eq(
                "user_id", user_id
            ).gte("generated_at", one_hour_ago).execute()
            
            if recent_result.data:
                existing_draft = recent_result.data[0]
                # Only return existing if it's ready, not if it's still generating
                if existing_draft.get("status") == "ready":
                    return DraftGenerationResult(
                        draft_id=existing_draft["id"],
                        status=DraftStatus.READY,
                        message="A recent draft already exists. Use force_regenerate=true to create a new one.",
                        error="recent_draft_exists"
                    )
        
        # Create a placeholder draft with 'generating' status
        import uuid
        draft_id = str(uuid.uuid4())
        
        placeholder_draft = {
            "id": draft_id,
            "user_id": user_id,
            "title": "Generating...",
            "sections": [],
            "status": "generating",
            "metadata": {
                "topic_count": request.topic_count,
                "days_back": request.days_back,
                "use_voice_profile": request.use_voice_profile
            }
        }
        
        supabase.table("newsletter_drafts").insert(placeholder_draft).execute()
        
        # Generate draft in background
        async def generate_in_background():
            try:
                # Generate draft content without storing it
                from app.services.trend_detector import trend_detector
                from app.services.content_summarizer import content_summarizer
                from app.services.feedback_analyzer import feedback_analyzer
                
                # Initialize draft generator
                draft_generator.initialize()
                
                # Get trending topics
                trends = await trend_detector.detect_trends(
                    user_id=user_id,
                    days_back=request.days_back,
                    min_score=0.2,
                    max_trends=request.topic_count
                )
                
                if not trends:
                    trends = await trend_detector.detect_trends(
                        user_id=user_id,
                        days_back=request.days_back,
                        min_score=0.1,
                        max_trends=request.topic_count
                    )
                
                # Handle no trends case
                if not trends:
                    fallback_draft = await draft_generator._create_fallback_draft(user_id, request.days_back, store=False)
                    # Update placeholder with fallback
                    supabase.table("newsletter_drafts").update({
                        "title": fallback_draft["title"],
                        "sections": fallback_draft["sections"],
                        "status": "ready",
                        "metadata": fallback_draft["metadata"],
                        "generated_at": fallback_draft["generated_at"]
                    }).eq("id", draft_id).execute()
                    return
                
                # Get summaries
                trend_summaries = await draft_generator._get_trend_summaries(trends, user_id)
                
                # Get voice profile
                voice_profile = None
                if request.use_voice_profile:
                    voice_profile = await draft_generator._get_voice_profile(user_id)
                
                # Get feedback insights
                feedback_insights = await feedback_analyzer.get_feedback_insights(
                    user_id=user_id,
                    days_back=30
                )
                
                # Generate draft content
                draft_content = await draft_generator._generate_draft_content(
                    trends=trends,
                    summaries=trend_summaries,
                    voice_profile=voice_profile,
                    feedback_insights=feedback_insights,
                    user_id=user_id
                )
                
                # Update the placeholder with actual draft (don't create new one)
                supabase.table("newsletter_drafts").update({
                    "title": draft_content.get("title", ""),
                    "sections": draft_content.get("sections", []),
                    "status": "ready",
                    "metadata": {
                        **draft_content.get("metadata", {}),
                        "trends_used": [t["topic"] for t in trends],
                        "model_used": draft_content.get("model_used", draft_generator.model),
                        "voice_profile_used": draft_content.get("voice_profile_used", False)
                    },
                    "generated_at": datetime.now().isoformat()
                }).eq("id", draft_id).execute()
                
                # Log successful generation
                supabase.table("draft_generation_logs").insert({
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "success_count": 1,
                    "error_count": 0,
                    "total_count": 1
                }).execute()
                
            except Exception as e:
                # Mark as failed
                supabase.table("newsletter_drafts").update({
                    "status": "failed",
                    "metadata": {"error": str(e)}
                }).eq("id", draft_id).execute()
                
                # Log failed generation
                supabase.table("draft_generation_logs").insert({
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "success_count": 0,
                    "error_count": 1,
                    "total_count": 1
                }).execute()
        
        # Add to background tasks - wrap async function
        def run_async_generate():
            asyncio.run(generate_in_background())
        
        background_tasks.add_task(run_async_generate)
        
        return DraftGenerationResult(
            draft_id=draft_id,
            status=DraftStatus.GENERATING,
            message="Draft generation started. Poll the draft status to check completion."
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        return DraftGenerationResult(
            draft_id="",
            status=DraftStatus.FAILED,
            message="Failed to start draft generation",
            error=str(e)
        )


@router.get("", response_model=DraftListResponse)
async def list_drafts(
    limit: int = 20,
    status_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    List all drafts for the current user
    
    Returns drafts ordered by generation date (newest first).
    Can filter by status (ready, editing, published, failed).
    """
    try:
        user_id = current_user["id"]
        
        query = supabase.table("newsletter_drafts").select("*").eq("user_id", user_id)
        
        if status_filter:
            query = query.eq("status", status_filter)
        
        result = query.order("generated_at", desc=True).limit(limit).execute()
        
        drafts = []
        for draft in result.data or []:
            drafts.append(DraftResponse(
                id=draft["id"],
                user_id=draft["user_id"],
                title=draft["title"],
                sections=draft.get("sections", []),
                status=DraftStatus(draft.get("status", "ready")),
                metadata=draft.get("metadata", {}),
                generated_at=draft["generated_at"],
                published_at=draft.get("published_at"),
                email_sent=draft.get("email_sent", False)
            ))
        
        return DraftListResponse(
            drafts=drafts,
            total=len(drafts),
            message=f"Found {len(drafts)} draft(s)"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch drafts: {str(e)}"
        )


@router.get("/{draft_id}", response_model=DraftResponse)
async def get_draft(
    draft_id: str,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get a specific draft by ID
    
    Returns the complete draft with all sections and metadata.
    """
    try:
        user_id = current_user["id"]
        
        result = supabase.table("newsletter_drafts").select("*").eq(
            "id", draft_id
        ).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft not found"
            )
        
        draft = result.data[0]
        
        return DraftResponse(
            id=draft["id"],
            user_id=draft["user_id"],
            title=draft["title"],
            sections=draft.get("sections", []),
            status=DraftStatus(draft.get("status", "ready")),
            metadata=draft.get("metadata", {}),
            generated_at=draft["generated_at"],
            published_at=draft.get("published_at"),
            email_sent=draft.get("email_sent", False)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch draft: {str(e)}"
        )


@router.put("/{draft_id}", response_model=DraftResponse)
async def update_draft(
    draft_id: str,
    update_data: DraftUpdate,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Update a draft
    
    Allows editing the title, sections, and metadata.
    Sets status to 'editing' if not already published.
    """
    try:
        user_id = current_user["id"]
        
        # Verify draft exists and belongs to user
        result = supabase.table("newsletter_drafts").select("*").eq(
            "id", draft_id
        ).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft not found"
            )
        
        current_draft = result.data[0]
        
        # Don't allow editing published drafts
        if current_draft.get("status") == "published":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot edit published draft"
            )
        
        # Build update dictionary
        update_dict = {}
        if update_data.title is not None:
            update_dict["title"] = update_data.title
        if update_data.sections is not None:
            update_dict["sections"] = [s.dict() for s in update_data.sections]
        if update_data.metadata is not None:
            update_dict["metadata"] = update_data.metadata
        
        # Set status to editing
        update_dict["status"] = "editing"
        update_dict["updated_at"] = datetime.now().isoformat()
        
        # Update draft
        updated_result = supabase.table("newsletter_drafts").update(
            update_dict
        ).eq("id", draft_id).execute()
        
        if not updated_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update draft"
            )
        
        updated_draft = updated_result.data[0]
        
        return DraftResponse(
            id=updated_draft["id"],
            user_id=updated_draft["user_id"],
            title=updated_draft["title"],
            sections=updated_draft.get("sections", []),
            status=DraftStatus(updated_draft.get("status", "editing")),
            metadata=updated_draft.get("metadata", {}),
            generated_at=updated_draft["generated_at"],
            published_at=updated_draft.get("published_at"),
            email_sent=updated_draft.get("email_sent", False)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update draft: {str(e)}"
        )


@router.post("/{draft_id}/regenerate", response_model=DraftGenerationResult)
async def regenerate_draft(
    draft_id: str,
    request: RegenerateDraftRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Regenerate a draft
    
    Creates a new draft with fresh content, replacing the old one.
    Useful if the user wants different topics or updated content.
    
    Returns immediately with status='generating' and the regeneration
    happens in the background. Poll the new draft status to check completion.
    """
    try:
        user_id = current_user["id"]
        
        # Verify the old draft exists
        old_draft_result = supabase.table("newsletter_drafts").select("*").eq(
            "id", draft_id
        ).eq("user_id", user_id).execute()
        
        if not old_draft_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft not found"
            )
        
        # Create a placeholder for the new draft
        import uuid
        new_draft_id = str(uuid.uuid4())
        
        placeholder_draft = {
            "id": new_draft_id,
            "user_id": user_id,
            "title": "Regenerating...",
            "sections": [],
            "status": "generating",
            "metadata": {
                "regenerated_from": draft_id,
                "topic_count": request.topic_count,
                "use_voice_profile": request.use_voice_profile
            }
        }
        
        supabase.table("newsletter_drafts").insert(placeholder_draft).execute()
        
        # Regenerate in background
        async def regenerate_in_background():
            try:
                # Get old draft metadata
                old_metadata = old_draft_result.data[0].get("metadata", {})
                was_fallback = old_metadata.get("fallback", False)
                days_back = 14 if was_fallback else 10
                
                # Use topic count from request or old draft
                topic_count = request.topic_count
                if topic_count is None:
                    old_sections = old_draft_result.data[0].get("sections", [])
                    topic_count = len([s for s in old_sections if s.get("type") == "topic"])
                    topic_count = max(3, min(10, topic_count))
                
                # Generate new draft content (same logic as generate)
                from app.services.trend_detector import trend_detector
                from app.services.content_summarizer import content_summarizer
                from app.services.feedback_analyzer import feedback_analyzer
                
                draft_generator.initialize()
                
                trends = await trend_detector.detect_trends(
                    user_id=user_id,
                    days_back=days_back,
                    min_score=0.2,
                    max_trends=topic_count
                )
                
                if not trends:
                    trends = await trend_detector.detect_trends(
                        user_id=user_id,
                        days_back=days_back,
                        min_score=0.1,
                        max_trends=topic_count
                    )
                
                if not trends:
                    fallback_draft = await draft_generator._create_fallback_draft(user_id, days_back, store=False)
                    # Update placeholder
                    supabase.table("newsletter_drafts").update({
                        "title": fallback_draft["title"],
                        "sections": fallback_draft["sections"],
                        "status": "ready",
                        "metadata": {**fallback_draft["metadata"], "regenerated_from": draft_id},
                        "generated_at": fallback_draft["generated_at"]
                    }).eq("id", new_draft_id).execute()
                    # Delete old draft
                    supabase.table("newsletter_drafts").delete().eq("id", draft_id).execute()
                    return
                
                trend_summaries = await draft_generator._get_trend_summaries(trends, user_id)
                
                voice_profile = None
                if request.use_voice_profile:
                    voice_profile = await draft_generator._get_voice_profile(user_id)
                
                feedback_insights = await feedback_analyzer.get_feedback_insights(
                    user_id=user_id,
                    days_back=30
                )
                
                draft_content = await draft_generator._generate_draft_content(
                    trends=trends,
                    summaries=trend_summaries,
                    voice_profile=voice_profile,
                    feedback_insights=feedback_insights,
                    user_id=user_id
                )
                
                # Update placeholder with new content
                supabase.table("newsletter_drafts").update({
                    "title": draft_content.get("title", ""),
                    "sections": draft_content.get("sections", []),
                    "status": "ready",
                    "metadata": {
                        **draft_content.get("metadata", {}),
                        "trends_used": [t["topic"] for t in trends],
                        "model_used": draft_content.get("model_used", draft_generator.model),
                        "voice_profile_used": draft_content.get("voice_profile_used", False),
                        "regenerated_from": draft_id
                    },
                    "generated_at": datetime.now().isoformat()
                }).eq("id", new_draft_id).execute()
                
                # Delete old draft
                supabase.table("newsletter_drafts").delete().eq("id", draft_id).execute()
                
                # Log successful regeneration
                supabase.table("draft_generation_logs").insert({
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "success_count": 1,
                    "error_count": 0,
                    "total_count": 1
                }).execute()
                
            except Exception as e:
                # Mark as failed
                supabase.table("newsletter_drafts").update({
                    "status": "failed",
                    "title": "Regeneration Failed",
                    "metadata": {"error": str(e), "regenerated_from": draft_id}
                }).eq("id", new_draft_id).execute()
                
                # Log failed regeneration
                supabase.table("draft_generation_logs").insert({
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "success_count": 0,
                    "error_count": 1,
                    "total_count": 1
                }).execute()
        
        # Add to background tasks - wrap async function
        def run_async_regenerate():
            asyncio.run(regenerate_in_background())
        
        background_tasks.add_task(run_async_regenerate)
        
        return DraftGenerationResult(
            draft_id=new_draft_id,
            status=DraftStatus.GENERATING,
            message="Draft regeneration started. Poll the draft status to check completion."
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        return DraftGenerationResult(
            draft_id="",
            status=DraftStatus.FAILED,
            message="Failed to start draft regeneration",
            error=str(e)
        )


@router.post("/{draft_id}/publish")
async def publish_draft(
    draft_id: str,
    request: PublishDraftRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Publish a draft
    
    Marks the draft as published and optionally sends it via email.
    Email sending happens in the background.
    """
    try:
        user_id = current_user["id"]
        
        # Get draft
        result = supabase.table("newsletter_drafts").select("*").eq(
            "id", draft_id
        ).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft not found"
            )
        
        draft = result.data[0]
        
        # Update draft status
        update_data = {
            "status": "published",
            "published_at": datetime.now().isoformat()
        }
        
        supabase.table("newsletter_drafts").update(update_data).eq(
            "id", draft_id
        ).execute()
        
        # Send email if requested
        if request.send_email:
            # Import email service
            from app.services.email_service import email_service
            
            subject = request.subject or draft["title"]
            recipients = request.recipient_emails or []
            
            # If no recipients specified, get from user profile
            if not recipients:
                user_result = supabase.table("users").select("email").eq(
                    "id", user_id
                ).execute()
                if user_result.data:
                    recipients = [user_result.data[0]["email"]]
            
            # Send email in background
            background_tasks.add_task(
                email_service.send_newsletter,
                draft_id=draft_id,
                subject=subject,
                recipients=recipients,
                user_id=user_id
            )
            
            message = "Draft published and email queued for delivery"
        else:
            message = "Draft published successfully"
        
        return {
            "success": True,
            "message": message,
            "draft_id": draft_id,
            "published_at": update_data["published_at"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish draft: {str(e)}"
        )


@router.delete("/{draft_id}")
async def delete_draft(
    draft_id: str,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Delete a draft
    
    Permanently removes the draft from the database.
    Published drafts can still be deleted for cleanup.
    """
    try:
        user_id = current_user["id"]
        
        # Verify draft belongs to user
        result = supabase.table("newsletter_drafts").select("id").eq(
            "id", draft_id
        ).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft not found"
            )
        
        # Delete draft
        supabase.table("newsletter_drafts").delete().eq("id", draft_id).execute()
        
        return {
            "success": True,
            "message": "Draft deleted successfully",
            "draft_id": draft_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete draft: {str(e)}"
        )
