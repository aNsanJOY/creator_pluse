"""
Twitter OAuth and integration endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from supabase import Client
from typing import Optional
import tweepy
import os
from urllib.parse import urlencode

from app.core.database import get_supabase
from app.api.dependencies import get_current_active_user
from app.models.source import SourceType, SourceStatus
from pydantic import BaseModel


router = APIRouter()


class TwitterOAuthInitResponse(BaseModel):
    """Response for OAuth initialization"""
    authorization_url: str
    oauth_token: str


class TwitterOAuthCallbackRequest(BaseModel):
    """Request body for OAuth callback"""
    oauth_token: str
    oauth_verifier: str


class TwitterSourceResponse(BaseModel):
    """Response after successful Twitter connection"""
    source_id: str
    username: str
    status: str


# Store OAuth tokens temporarily (in production, use Redis or database)
# Key: oauth_token, Value: {oauth_token_secret, user_id}
oauth_temp_storage = {}


@router.post("/oauth/init", response_model=TwitterOAuthInitResponse)
async def twitter_oauth_init(
    current_user: dict = Depends(get_current_active_user)
):
    """
    Initialize Twitter OAuth 1.0a flow.
    Returns authorization URL for user to approve app.
    """
    try:
        # Get Twitter API credentials from environment
        api_key = os.getenv("TWITTER_API_KEY")
        api_secret = os.getenv("TWITTER_API_SECRET")
        callback_url = os.getenv("BACKEND_URL", "http://localhost:8000") + "/api/twitter/oauth/callback"
        
        if not api_key or not api_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Twitter API credentials not configured"
            )
        
        # Create OAuth handler
        auth = tweepy.OAuth1UserHandler(
            consumer_key=api_key,
            consumer_secret=api_secret,
            callback=callback_url
        )
        
        # Get authorization URL
        authorization_url = auth.get_authorization_url()
        
        # Store request token temporarily
        oauth_token = auth.request_token['oauth_token']
        oauth_token_secret = auth.request_token['oauth_token_secret']
        
        # Store in temporary storage with user_id
        oauth_temp_storage[oauth_token] = {
            'oauth_token_secret': oauth_token_secret,
            'user_id': current_user['id']
        }
        
        return TwitterOAuthInitResponse(
            authorization_url=authorization_url,
            oauth_token=oauth_token
        )
    
    except tweepy.TweepyException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Twitter OAuth initialization failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize Twitter OAuth: {str(e)}"
        )


@router.post("/oauth/callback", response_model=TwitterSourceResponse)
async def twitter_oauth_callback(
    callback_data: TwitterOAuthCallbackRequest,
    supabase: Client = Depends(get_supabase),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Handle Twitter OAuth callback.
    Exchanges OAuth verifier for access tokens and creates source.
    """
    try:
        oauth_token = callback_data.oauth_token
        oauth_verifier = callback_data.oauth_verifier
        
        # Retrieve stored token secret
        if oauth_token not in oauth_temp_storage:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OAuth token"
            )
        
        stored_data = oauth_temp_storage[oauth_token]
        oauth_token_secret = stored_data['oauth_token_secret']
        
        # Verify user
        if stored_data['user_id'] != current_user['id']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="OAuth token does not belong to current user"
            )
        
        # Get Twitter API credentials
        api_key = os.getenv("TWITTER_API_KEY")
        api_secret = os.getenv("TWITTER_API_SECRET")
        
        # Exchange for access token
        auth = tweepy.OAuth1UserHandler(
            consumer_key=api_key,
            consumer_secret=api_secret
        )
        auth.request_token = {
            'oauth_token': oauth_token,
            'oauth_token_secret': oauth_token_secret
        }
        
        # Get access token
        access_token, access_token_secret = auth.get_access_token(oauth_verifier)
        
        # Get user info
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth)
        twitter_user = api.verify_credentials()
        
        username = twitter_user.screen_name
        twitter_user_id = str(twitter_user.id)
        
        # Check if source already exists
        existing = supabase.table("sources").select("*").eq(
            "user_id", current_user['id']
        ).eq("source_type", "twitter").eq("url", f"https://twitter.com/{username}").execute()
        
        if existing.data:
            # Update existing source
            source_id = existing.data[0]['id']
            supabase.table("sources").update({
                "credentials": {
                    "api_key": api_key,
                    "api_secret": api_secret,
                    "access_token": access_token,
                    "access_token_secret": access_token_secret,
                    "twitter_user_id": twitter_user_id
                },
                "status": SourceStatus.ACTIVE.value,
                "error_message": None
            }).eq("id", source_id).execute()
        else:
            # Create new source
            new_source = {
                "user_id": current_user['id'],
                "source_type": SourceType.TWITTER.value,
                "name": f"Twitter - @{username}",
                "url": f"https://twitter.com/{username}",
                "credentials": {
                    "api_key": api_key,
                    "api_secret": api_secret,
                    "access_token": access_token,
                    "access_token_secret": access_token_secret,
                    "twitter_user_id": twitter_user_id
                },
                "config": {
                    "username": username,
                    "fetch_type": "timeline",
                    "max_results": 100
                },
                "status": SourceStatus.ACTIVE.value
            }
            
            result = supabase.table("sources").insert(new_source).execute()
            source_id = result.data[0]['id']
        
        # Clean up temporary storage
        del oauth_temp_storage[oauth_token]
        
        return TwitterSourceResponse(
            source_id=source_id,
            username=username,
            status=SourceStatus.ACTIVE.value
        )
    
    except tweepy.TweepyException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Twitter OAuth failed: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete Twitter OAuth: {str(e)}"
        )


@router.get("/oauth/callback")
async def twitter_oauth_callback_get(
    oauth_token: str,
    oauth_verifier: str,
    request: Request
):
    """
    Handle Twitter OAuth callback (GET request from Twitter).
    Redirects to frontend with tokens.
    """
    try:
        # Redirect to frontend with tokens
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        params = urlencode({
            'oauth_token': oauth_token,
            'oauth_verifier': oauth_verifier
        })
        redirect_url = f"{frontend_url}/sources/twitter/callback?{params}"
        
        return RedirectResponse(url=redirect_url)
    
    except Exception as e:
        # Redirect to error page
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        error_url = f"{frontend_url}/sources/twitter/error?error={str(e)}"
        return RedirectResponse(url=error_url)


@router.delete("/{source_id}")
async def disconnect_twitter(
    source_id: str,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Disconnect Twitter source.
    """
    try:
        # Verify source exists and belongs to user
        result = supabase.table("sources").select("*").eq(
            "id", source_id
        ).eq("user_id", current_user['id']).eq("source_type", "twitter").execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Twitter source not found"
            )
        
        # Delete source
        supabase.table("sources").delete().eq("id", source_id).execute()
        
        return {"message": "Twitter source disconnected successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect Twitter source: {str(e)}"
        )
