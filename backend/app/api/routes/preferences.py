"""
Preferences API Routes
Endpoints for user preferences and settings
"""

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import time

from app.core.database import get_supabase
from app.api.dependencies import get_current_active_user

router = APIRouter()


class PreferencesUpdate(BaseModel):
    """User preferences update model"""
    draft_schedule_time: Optional[str] = Field(None, description="Time for daily draft generation (HH:MM format)")
    newsletter_frequency: Optional[str] = Field(None, description="Frequency: daily, weekly, custom")
    content_preferences: Optional[Dict[str, Any]] = Field(None, description="Content filtering preferences")
    tone_preferences: Optional[Dict[str, Any]] = Field(None, description="Tone and style preferences")
    notification_preferences: Optional[Dict[str, Any]] = Field(None, description="Notification settings")
    email_preferences: Optional[Dict[str, Any]] = Field(None, description="Email delivery preferences")


@router.get("")
async def get_preferences(
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get user preferences
    
    Returns all user preferences and settings.
    """
    try:
        user_id = current_user["id"]
        
        # Get user with preferences
        result = supabase.table("users").select("preferences").eq(
            "id", user_id
        ).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = result.data[0]
        preferences = user.get("preferences", {})
        
        # Set defaults if not configured
        default_preferences = {
            "draft_schedule_time": "08:00",
            "newsletter_frequency": "daily",
            "content_preferences": {
                "topics_to_include": [],
                "topics_to_exclude": [],
                "min_content_age_hours": 0,
                "max_content_age_days": 7,
                "preferred_sources": []
            },
            "tone_preferences": {
                "formality": "balanced",  # casual, balanced, formal
                "enthusiasm": "moderate",  # low, moderate, high
                "use_emojis": False,
                "length_preference": "medium"  # short, medium, long
            },
            "notification_preferences": {
                "email_on_draft_ready": True,
                "email_on_publish_success": True,
                "email_on_errors": True,
                "weekly_summary": True
            },
            "email_preferences": {
                "default_subject_template": "{title}",
                "include_preview_text": True,
                "track_opens": False,
                "track_clicks": False
            }
        }
        
        # Merge with defaults
        merged_preferences = {**default_preferences, **preferences}
        
        return {
            "success": True,
            "preferences": merged_preferences
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch preferences: {str(e)}"
        )


@router.put("")
async def update_preferences(
    updates: PreferencesUpdate,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Update user preferences
    
    Updates specific preference fields. Only provided fields are updated.
    """
    try:
        user_id = current_user["id"]
        
        # Get current preferences
        result = supabase.table("users").select("preferences").eq(
            "id", user_id
        ).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        current_preferences = result.data[0].get("preferences", {})
        
        # Build update dictionary
        update_dict = {}
        
        if updates.draft_schedule_time is not None:
            # Validate time format
            try:
                time.fromisoformat(updates.draft_schedule_time)
                update_dict["draft_schedule_time"] = updates.draft_schedule_time
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid time format. Use HH:MM format (e.g., 08:00)"
                )
        
        if updates.newsletter_frequency is not None:
            if updates.newsletter_frequency not in ["daily", "weekly", "custom"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid frequency. Must be: daily, weekly, or custom"
                )
            update_dict["newsletter_frequency"] = updates.newsletter_frequency
        
        if updates.content_preferences is not None:
            current_content = current_preferences.get("content_preferences", {})
            update_dict["content_preferences"] = {**current_content, **updates.content_preferences}
        
        if updates.tone_preferences is not None:
            current_tone = current_preferences.get("tone_preferences", {})
            update_dict["tone_preferences"] = {**current_tone, **updates.tone_preferences}
        
        if updates.notification_preferences is not None:
            current_notif = current_preferences.get("notification_preferences", {})
            update_dict["notification_preferences"] = {**current_notif, **updates.notification_preferences}
        
        if updates.email_preferences is not None:
            current_email = current_preferences.get("email_preferences", {})
            update_dict["email_preferences"] = {**current_email, **updates.email_preferences}
        
        # Merge with current preferences
        new_preferences = {**current_preferences, **update_dict}
        
        # Update in database
        supabase.table("users").update({
            "preferences": new_preferences
        }).eq("id", user_id).execute()
        
        return {
            "success": True,
            "message": "Preferences updated successfully",
            "preferences": new_preferences
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update preferences: {str(e)}"
        )


@router.post("/reset")
async def reset_preferences(
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Reset preferences to defaults
    
    Resets all user preferences to default values.
    """
    try:
        user_id = current_user["id"]
        
        default_preferences = {
            "draft_schedule_time": "08:00",
            "newsletter_frequency": "daily",
            "content_preferences": {
                "topics_to_include": [],
                "topics_to_exclude": [],
                "min_content_age_hours": 0,
                "max_content_age_days": 7,
                "preferred_sources": []
            },
            "tone_preferences": {
                "formality": "balanced",
                "enthusiasm": "moderate",
                "use_emojis": False,
                "length_preference": "medium"
            },
            "notification_preferences": {
                "email_on_draft_ready": True,
                "email_on_publish_success": True,
                "email_on_errors": True,
                "weekly_summary": True
            },
            "email_preferences": {
                "default_subject_template": "{title}",
                "include_preview_text": True,
                "track_opens": False,
                "track_clicks": False
            }
        }
        
        # Update in database
        supabase.table("users").update({
            "preferences": default_preferences
        }).eq("id", user_id).execute()
        
        return {
            "success": True,
            "message": "Preferences reset to defaults",
            "preferences": default_preferences
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset preferences: {str(e)}"
        )
