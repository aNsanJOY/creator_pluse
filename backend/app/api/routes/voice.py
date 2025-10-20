from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from typing import Dict, Any
import json

from app.core.database import get_supabase
from app.api.dependencies import get_current_active_user
from app.services.voice_analyzer import voice_analyzer

router = APIRouter()


@router.post("/analyze")
async def analyze_voice(
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Analyze user's newsletter samples to create a voice profile.
    Requires at least 1 sample, but 3-5 samples recommended for best results.
    """
    try:
        user_id = current_user["id"]
        
        # Fetch all newsletter samples for the user
        samples_result = supabase.table("newsletter_samples").select("*").eq("user_id", user_id).execute()
        
        if not samples_result.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No newsletter samples found. Please upload at least one sample before analyzing."
            )
        
        # Prepare samples for analysis
        samples = [
            {
                "title": sample.get("title", "Untitled"),
                "content": sample["content"]
            }
            for sample in samples_result.data
        ]
        
        # Analyze voice using the voice analyzer service
        voice_profile = await voice_analyzer.analyze_voice(samples, user_id=user_id)
        
        # Generate human-readable summary
        summary = voice_analyzer.generate_style_summary(voice_profile)
        
        # Update user's voice profile in the database
        update_result = supabase.table("users").update({
            "voice_profile": voice_profile
        }).eq("id", user_id).execute()
        
        if not update_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save voice profile"
            )
        
        # Auto-enable use_voice_profile in preferences if analysis was successful
        if voice_profile.get("source") == "analyzed":
            # Get current preferences
            user_data = supabase.table("users").select("preferences").eq("id", user_id).single().execute()
            current_preferences = user_data.data.get("preferences", {}) if user_data.data else {}
            
            # Update preferences to enable voice profile
            updated_preferences = {**current_preferences, "use_voice_profile": True}
            
            supabase.table("users").update({
                "preferences": updated_preferences
            }).eq("id", user_id).execute()
        
        return {
            "voice_profile": voice_profile,
            "summary": summary,
            "message": f"Voice analysis completed successfully! Analyzed {len(samples)} sample(s).",
            "samples_analyzed": len(samples)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze voice: {str(e)}"
        )


@router.get("/profile")
async def get_voice_profile(
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get the user's voice profile.
    Returns the analyzed voice profile if available, or a default profile.
    """
    try:
        user_id = current_user["id"]
        
        # Fetch user's voice profile
        user_result = supabase.table("users").select("voice_profile").eq("id", user_id).single().execute()
        
        if not user_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        voice_profile = user_result.data.get("voice_profile")
        
        # Check if voice profile exists
        if voice_profile:
            # Generate summary
            summary = voice_analyzer.generate_style_summary(voice_profile)
            
            return {
                "voice_profile": voice_profile,
                "summary": summary,
                "has_profile": True,
                "message": "Voice profile loaded successfully"
            }
        
        # No voice profile exists - return default
        from app.services.voice_analyzer import DEFAULT_VOICE_PROFILE
        
        default_profile = {
            **DEFAULT_VOICE_PROFILE,
            "source": "default",
            "message": "No voice profile found. Upload newsletter samples and analyze to create one."
        }
        
        return {
            "voice_profile": default_profile,
            "summary": "No voice profile available yet. Upload 3-5 newsletter samples to get started.",
            "has_profile": False,
            "message": "Using default voice profile. Upload samples to create a personalized profile."
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch voice profile: {str(e)}"
        )