from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from typing import Dict, Any

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
    Analyze user's writing voice from uploaded newsletter samples.
    Creates or updates the user's voice profile.
    If no samples are available, uses a default professional tone.
    """
    try:
        user_id = current_user["id"]
        
        # Fetch user's newsletter samples
        result = supabase.table("newsletter_samples").select("*").eq("user_id", user_id).execute()
        
        samples = []
        if result.data:
            samples = [
                {
                    "title": sample.get("title"),
                    "content": sample["content"]
                }
                for sample in result.data
            ]
        
        # Analyze voice using Groq (pass user_id for usage tracking)
        voice_profile = await voice_analyzer.analyze_voice(samples, user_id=user_id)
        
        # Generate human-readable summary
        summary = voice_analyzer.generate_style_summary(voice_profile)
        
        # Update user's voice profile in database
        update_result = supabase.table("users").update({
            "voice_profile": voice_profile
        }).eq("id", user_id).execute()
        
        if not update_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update voice profile"
            )
        
        # Prepare response message
        if voice_profile.get("source") == "default":
            message = "No newsletter samples found. Using default professional voice profile. Upload 3-5 newsletter samples for personalized analysis."
        elif voice_profile.get("source") == "default_error":
            message = f"Voice analysis encountered an error. Using default profile. Error: {voice_profile.get('error', 'Unknown error')}"
        elif voice_profile.get("warning"):
            message = f"Voice analysis complete! {voice_profile['warning']} {summary}"
        else:
            message = f"Voice analysis complete! {summary}"
        
        return {
            "message": message,
            "voice_profile": voice_profile,
            "samples_analyzed": len(samples),
            "summary": summary
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
    Get the current user's voice profile.
    """
    try:
        user_id = current_user["id"]
        
        # Fetch user's voice profile
        result = supabase.table("users").select("voice_profile").eq("id", user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        voice_profile = result.data[0].get("voice_profile")
        
        if not voice_profile:
            return {
                "message": "No voice profile found. Run voice analysis first.",
                "voice_profile": None,
                "has_profile": False
            }
        
        # Generate summary
        summary = voice_analyzer.generate_style_summary(voice_profile)
        
        return {
            "message": "Voice profile retrieved successfully",
            "voice_profile": voice_profile,
            "summary": summary,
            "has_profile": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve voice profile: {str(e)}"
        )


@router.delete("/profile")
async def delete_voice_profile(
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Delete the current user's voice profile.
    """
    try:
        user_id = current_user["id"]
        
        # Clear voice profile
        result = supabase.table("users").update({
            "voice_profile": None
        }).eq("id", user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete voice profile"
            )
        
        return {
            "message": "Voice profile deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete voice profile: {str(e)}"
        )
