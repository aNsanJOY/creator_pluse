"""
User Preferences API Routes
Handles user preference management using the users.preferences JSONB field
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from pydantic import BaseModel
from app.api.dependencies import get_current_user
from app.core.database import get_supabase

router = APIRouter()


# Pydantic models for preferences
class TonePreferences(BaseModel):
    formality: Optional[str] = "balanced"  # casual, balanced, formal
    enthusiasm: Optional[str] = "moderate"  # low, moderate, high
    length_preference: Optional[str] = "medium"  # short, medium, long
    use_emojis: Optional[bool] = True


class NotificationPreferences(BaseModel):
    email_on_draft_ready: Optional[bool] = True
    email_on_publish_success: Optional[bool] = True
    email_on_errors: Optional[bool] = True
    weekly_summary: Optional[bool] = False


class EmailPreferences(BaseModel):
    default_subject_template: Optional[str] = "{title} - Weekly Newsletter"
    include_preview_text: Optional[bool] = True
    track_opens: Optional[bool] = False
    track_clicks: Optional[bool] = False


class UserPreferences(BaseModel):
    draft_schedule_time: Optional[str] = "09:00"
    newsletter_frequency: Optional[str] = "weekly"  # daily, weekly, custom
    use_voice_profile: Optional[bool] = False
    tone_preferences: Optional[TonePreferences] = TonePreferences()
    notification_preferences: Optional[NotificationPreferences] = NotificationPreferences()
    email_preferences: Optional[EmailPreferences] = EmailPreferences()


class PreferencesUpdate(BaseModel):
    draft_schedule_time: Optional[str] = None
    newsletter_frequency: Optional[str] = None
    use_voice_profile: Optional[bool] = None
    tone_preferences: Optional[dict] = None
    notification_preferences: Optional[dict] = None
    email_preferences: Optional[dict] = None


# Default preferences
DEFAULT_PREFERENCES = {
    "draft_schedule_time": "09:00",
    "newsletter_frequency": "weekly",
    "use_voice_profile": False,
    "tone_preferences": {
        "formality": "balanced",
        "enthusiasm": "moderate",
        "length_preference": "medium",
        "use_emojis": True
    },
    "notification_preferences": {
        "email_on_draft_ready": True,
        "email_on_publish_success": True,
        "email_on_errors": True,
        "weekly_summary": False
    },
    "email_preferences": {
        "default_subject_template": "{title} - Weekly Newsletter",
        "include_preview_text": True,
        "track_opens": False,
        "track_clicks": False
    }
}


def deep_merge(base: dict, updates: dict) -> dict:
    """Deep merge two dictionaries"""
    result = base.copy()
    for key, value in updates.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


@router.get("/preferences")
async def get_preferences(current_user: dict = Depends(get_current_user)):
    """
    Get user preferences
    Returns the user's preferences from the users.preferences JSONB field
    """
    try:
        supabase = get_supabase()
        
        # Query user preferences from users table
        response = supabase.table("users").select("preferences").eq("id", current_user["id"]).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get stored preferences or use defaults
        stored_prefs = response.data[0].get("preferences") or {}
        
        # Merge with defaults to ensure all fields exist
        preferences = deep_merge(DEFAULT_PREFERENCES, stored_prefs)
        
        return preferences
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch preferences: {str(e)}")


@router.patch("/preferences")
async def update_preferences(
    updates: PreferencesUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update user preferences
    Partially updates the user's preferences in the users.preferences JSONB field
    """
    try:
        supabase = get_supabase()
        
        # Get current preferences from users table
        response = supabase.table("users").select("preferences").eq("id", current_user["id"]).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get current preferences or start with defaults
        current_prefs = response.data[0].get("preferences")
        
        # Ensure current_prefs is a dict (handle case where it might be stored as string or None)
        if not isinstance(current_prefs, dict):
            current_prefs = DEFAULT_PREFERENCES.copy()
        else:
            # Make a copy to avoid modifying the original
            import copy
            current_prefs = copy.deepcopy(current_prefs)
        
        # Prepare updates dictionary (only include non-None values)
        update_dict = {}
        if updates.draft_schedule_time is not None:
            update_dict["draft_schedule_time"] = updates.draft_schedule_time
        if updates.newsletter_frequency is not None:
            update_dict["newsletter_frequency"] = updates.newsletter_frequency
        if updates.use_voice_profile is not None:
            update_dict["use_voice_profile"] = updates.use_voice_profile
        if updates.tone_preferences is not None:
            update_dict["tone_preferences"] = updates.tone_preferences
        if updates.notification_preferences is not None:
            update_dict["notification_preferences"] = updates.notification_preferences
        if updates.email_preferences is not None:
            update_dict["email_preferences"] = updates.email_preferences
        
        # Merge updates with current preferences
        updated_prefs = deep_merge(current_prefs, update_dict)
        
        # Update in users table
        update_response = supabase.table("users").update({
            "preferences": updated_prefs,
            "updated_at": "now()"
        }).eq("id", current_user["id"]).execute()
        
        if not update_response.data or len(update_response.data) == 0:
            raise HTTPException(status_code=500, detail="Failed to update preferences")
        
        return update_response.data[0]["preferences"]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update preferences: {str(e)}")


@router.post("/preferences/reset")
async def reset_preferences(current_user: dict = Depends(get_current_user)):
    """
    Reset user preferences to defaults
    Resets all preferences to their default values
    """
    try:
        supabase = get_supabase()
        
        # Reset to default preferences in users table
        response = supabase.table("users").update({
            "preferences": DEFAULT_PREFERENCES,
            "updated_at": "now()"
        }).eq("id", current_user["id"]).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        return response.data[0]["preferences"]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset preferences: {str(e)}")
