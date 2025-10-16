"""
Feedback API endpoints for collecting user feedback on newsletter drafts
"""

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from typing import Optional

from app.core.database import get_supabase
from app.api.dependencies import get_current_active_user
from app.models.feedback import (
    FeedbackCreate,
    FeedbackUpdate,
    FeedbackResponse,
    FeedbackListResponse,
    FeedbackStats
)


router = APIRouter()


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    feedback_data: FeedbackCreate,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Submit feedback for a newsletter draft or specific section.
    """
    try:
        user_id = current_user["id"]
        
        # Verify the draft exists and belongs to the user
        draft_result = supabase.table("newsletter_drafts").select("id").eq(
            "id", feedback_data.newsletter_id
        ).eq("user_id", user_id).execute()
        
        if not draft_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft not found"
            )
        
        # Create feedback entry
        new_feedback = {
            "user_id": user_id,
            "newsletter_id": feedback_data.newsletter_id,
            "feedback_type": feedback_data.feedback_type.value,
            "section_id": feedback_data.section_id,
            "comment": feedback_data.comment
        }
        
        result = supabase.table("feedback").insert(new_feedback).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to submit feedback"
            )
        
        return FeedbackResponse(**result.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


@router.get("/user/{user_id}", response_model=FeedbackListResponse)
async def get_user_feedback(
    user_id: str,
    newsletter_id: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get feedback history for a user.
    Optionally filter by newsletter_id.
    """
    try:
        # Verify the requesting user is the same as the user_id
        if current_user["id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own feedback"
            )
        
        # Build query
        query = supabase.table("feedback").select("*").eq("user_id", user_id)
        
        if newsletter_id:
            query = query.eq("newsletter_id", newsletter_id)
        
        query = query.order("created_at", desc=True).limit(limit)
        
        result = query.execute()
        
        feedback_list = [FeedbackResponse(**item) for item in result.data] if result.data else []
        
        return FeedbackListResponse(
            feedback=feedback_list,
            total=len(feedback_list)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch feedback: {str(e)}"
        )


@router.get("/newsletter/{newsletter_id}", response_model=FeedbackListResponse)
async def get_newsletter_feedback(
    newsletter_id: str,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get all feedback for a specific newsletter.
    """
    try:
        user_id = current_user["id"]
        
        # Verify the draft belongs to the user
        draft_result = supabase.table("newsletter_drafts").select("id").eq(
            "id", newsletter_id
        ).eq("user_id", user_id).execute()
        
        if not draft_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft not found"
            )
        
        # Get feedback for this newsletter
        result = supabase.table("feedback").select("*").eq(
            "newsletter_id", newsletter_id
        ).order("created_at", desc=True).execute()
        
        feedback_list = [FeedbackResponse(**item) for item in result.data] if result.data else []
        
        return FeedbackListResponse(
            feedback=feedback_list,
            total=len(feedback_list)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch newsletter feedback: {str(e)}"
        )


@router.get("/stats", response_model=FeedbackStats)
async def get_feedback_stats(
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get feedback statistics for the current user.
    """
    try:
        user_id = current_user["id"]
        
        # Get all feedback for the user
        result = supabase.table("feedback").select("*").eq(
            "user_id", user_id
        ).order("created_at", desc=True).execute()
        
        feedback_data = result.data if result.data else []
        total_feedback = len(feedback_data)
        
        thumbs_up_count = sum(1 for f in feedback_data if f["feedback_type"] == "thumbs_up")
        thumbs_down_count = sum(1 for f in feedback_data if f["feedback_type"] == "thumbs_down")
        
        positive_rate = (thumbs_up_count / total_feedback * 100) if total_feedback > 0 else 0.0
        
        # Get recent feedback (last 10)
        recent_feedback = [FeedbackResponse(**item) for item in feedback_data[:10]]
        
        return FeedbackStats(
            total_feedback=total_feedback,
            thumbs_up_count=thumbs_up_count,
            thumbs_down_count=thumbs_down_count,
            positive_rate=round(positive_rate, 2),
            recent_feedback=recent_feedback
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch feedback stats: {str(e)}"
        )


@router.put("/{feedback_id}", response_model=FeedbackResponse)
async def update_feedback(
    feedback_id: str,
    feedback_data: FeedbackUpdate,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Update existing feedback.
    """
    try:
        user_id = current_user["id"]
        
        # Verify feedback exists and belongs to user
        existing = supabase.table("feedback").select("*").eq(
            "id", feedback_id
        ).eq("user_id", user_id).execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback not found"
            )
        
        # Prepare update data
        update_data = {}
        if feedback_data.feedback_type is not None:
            update_data["feedback_type"] = feedback_data.feedback_type.value
        if feedback_data.comment is not None:
            update_data["comment"] = feedback_data.comment
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        # Update feedback
        result = supabase.table("feedback").update(update_data).eq(
            "id", feedback_id
        ).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update feedback"
            )
        
        return FeedbackResponse(**result.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update feedback: {str(e)}"
        )


@router.delete("/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feedback(
    feedback_id: str,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Delete feedback.
    """
    try:
        user_id = current_user["id"]
        
        # Verify feedback exists and belongs to user
        existing = supabase.table("feedback").select("*").eq(
            "id", feedback_id
        ).eq("user_id", user_id).execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback not found"
            )
        
        # Delete feedback
        supabase.table("feedback").delete().eq("id", feedback_id).execute()
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete feedback: {str(e)}"
        )
