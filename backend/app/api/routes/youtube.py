"""
YouTube OAuth and integration endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from supabase import Client
from typing import Optional
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from urllib.parse import urlencode
import json

from app.core.database import get_supabase
from app.api.dependencies import get_current_active_user
from app.models.source import SourceType, SourceStatus
from pydantic import BaseModel


router = APIRouter()


class YouTubeOAuthInitResponse(BaseModel):
    """Response for OAuth initialization"""
    authorization_url: str
    state: str


class YouTubeOAuthCallbackRequest(BaseModel):
    """Request body for OAuth callback"""
    code: str
    state: str


class YouTubeSourceResponse(BaseModel):
    """Response after successful YouTube connection"""
    source_id: str
    channel_title: str
    channel_id: str
    status: str


# Store OAuth states temporarily (in production, use Redis or database)
# Key: state, Value: {user_id}
oauth_state_storage = {}


# YouTube OAuth scopes
YOUTUBE_SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]


def get_oauth_flow(redirect_uri: str) -> Flow:
    """Create OAuth flow for YouTube"""
    client_config = {
        "web": {
            "client_id": os.getenv("YOUTUBE_CLIENT_ID"),
            "client_secret": os.getenv("YOUTUBE_CLIENT_SECRET"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=YOUTUBE_SCOPES,
        redirect_uri=redirect_uri
    )
    
    return flow


@router.post("/oauth/init", response_model=YouTubeOAuthInitResponse)
async def youtube_oauth_init(
    current_user: dict = Depends(get_current_active_user)
):
    """
    Initialize YouTube OAuth 2.0 flow.
    Returns authorization URL for user to approve app.
    """
    try:
        # Get YouTube API credentials from environment
        client_id = os.getenv("YOUTUBE_CLIENT_ID")
        client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
        redirect_uri = os.getenv("BACKEND_URL", "http://localhost:8000") + "/api/youtube/oauth/callback"
        
        if not client_id or not client_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="YouTube API credentials not configured"
            )
        
        # Create OAuth flow
        flow = get_oauth_flow(redirect_uri)
        
        # Generate authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent to get refresh token
        )
        
        # Store state with user_id
        oauth_state_storage[state] = {
            'user_id': current_user['id']
        }
        
        return YouTubeOAuthInitResponse(
            authorization_url=authorization_url,
            state=state
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize YouTube OAuth: {str(e)}"
        )


@router.post("/oauth/callback", response_model=YouTubeSourceResponse)
async def youtube_oauth_callback(
    callback_data: YouTubeOAuthCallbackRequest,
    supabase: Client = Depends(get_supabase),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Handle YouTube OAuth callback.
    Exchanges authorization code for access tokens and creates source.
    """
    try:
        code = callback_data.code
        state = callback_data.state
        
        # Retrieve stored state
        if state not in oauth_state_storage:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OAuth state"
            )
        
        stored_data = oauth_state_storage[state]
        
        # Verify user
        if stored_data['user_id'] != current_user['id']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="OAuth state does not belong to current user"
            )
        
        # Exchange code for tokens
        redirect_uri = os.getenv("BACKEND_URL", "http://localhost:8000") + "/api/youtube/oauth/callback"
        flow = get_oauth_flow(redirect_uri)
        
        flow.fetch_token(code=code)
        
        credentials = flow.credentials
        
        # Get channel info
        youtube = build('youtube', 'v3', credentials=credentials, cache_discovery=False)
        
        channels_response = youtube.channels().list(
            part='snippet,contentDetails,statistics',
            mine=True
        ).execute()
        
        if not channels_response.get('items'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No YouTube channel found for this account"
            )
        
        channel = channels_response['items'][0]
        channel_id = channel['id']
        channel_title = channel['snippet']['title']
        channel_url = f"https://www.youtube.com/channel/{channel_id}"
        
        # Check if source already exists
        existing = supabase.table("sources").select("*").eq(
            "user_id", current_user['id']
        ).eq("source_type", "youtube").eq("url", channel_url).execute()
        
        # Prepare credentials
        credentials_dict = {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
            "api_key": os.getenv("YOUTUBE_API_KEY")  # Store API key for quota management
        }
        
        if existing.data:
            # Update existing source
            source_id = existing.data[0]['id']
            supabase.table("sources").update({
                "credentials": credentials_dict,
                "status": SourceStatus.ACTIVE.value,
                "error_message": None,
                "config": {
                    "channel_id": channel_id,
                    "channel_title": channel_title,
                    "fetch_type": "uploads",
                    "max_results": 50
                }
            }).eq("id", source_id).execute()
        else:
            # Create new source
            new_source = {
                "user_id": current_user['id'],
                "source_type": SourceType.YOUTUBE.value,
                "name": f"YouTube - {channel_title}",
                "url": channel_url,
                "credentials": credentials_dict,
                "config": {
                    "channel_id": channel_id,
                    "channel_title": channel_title,
                    "fetch_type": "uploads",
                    "max_results": 50
                },
                "status": SourceStatus.ACTIVE.value
            }
            
            result = supabase.table("sources").insert(new_source).execute()
            source_id = result.data[0]['id']
        
        # Clean up temporary storage
        del oauth_state_storage[state]
        
        return YouTubeSourceResponse(
            source_id=source_id,
            channel_title=channel_title,
            channel_id=channel_id,
            status=SourceStatus.ACTIVE.value
        )
    
    except HttpError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"YouTube API error: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete YouTube OAuth: {str(e)}"
        )


@router.get("/oauth/callback")
async def youtube_oauth_callback_get(
    code: str,
    state: str,
    request: Request
):
    """
    Handle YouTube OAuth callback (GET request from Google).
    Redirects to frontend with authorization code.
    """
    try:
        # Redirect to frontend with code and state
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        params = urlencode({
            'code': code,
            'state': state
        })
        redirect_url = f"{frontend_url}/sources/youtube/callback?{params}"
        
        return RedirectResponse(url=redirect_url)
    
    except Exception as e:
        # Redirect to error page
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        error_url = f"{frontend_url}/sources/youtube/error?error={str(e)}"
        return RedirectResponse(url=error_url)


@router.delete("/{source_id}")
async def disconnect_youtube(
    source_id: str,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Disconnect YouTube source.
    """
    try:
        # Verify source exists and belongs to user
        result = supabase.table("sources").select("*").eq(
            "id", source_id
        ).eq("user_id", current_user['id']).eq("source_type", "youtube").execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="YouTube source not found"
            )
        
        # Delete source
        supabase.table("sources").delete().eq("id", source_id).execute()
        
        return {"message": "YouTube source disconnected successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect YouTube source: {str(e)}"
        )


@router.get("/{source_id}/stats")
async def get_youtube_stats(
    source_id: str,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get YouTube channel statistics.
    """
    try:
        # Verify source exists and belongs to user
        result = supabase.table("sources").select("*").eq(
            "id", source_id
        ).eq("user_id", current_user['id']).eq("source_type", "youtube").execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="YouTube source not found"
            )
        
        source = result.data[0]
        credentials_dict = source['credentials']
        channel_id = source['config']['channel_id']
        
        # Build YouTube client
        from google.oauth2.credentials import Credentials
        credentials = Credentials(
            token=credentials_dict['access_token'],
            refresh_token=credentials_dict.get('refresh_token'),
            token_uri=credentials_dict['token_uri'],
            client_id=credentials_dict['client_id'],
            client_secret=credentials_dict['client_secret'],
            scopes=credentials_dict['scopes']
        )
        
        youtube = build('youtube', 'v3', credentials=credentials, cache_discovery=False)
        
        # Get channel statistics
        channels_response = youtube.channels().list(
            part='statistics,snippet',
            id=channel_id
        ).execute()
        
        if not channels_response.get('items'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found"
            )
        
        channel = channels_response['items'][0]
        stats = channel['statistics']
        
        return {
            "channel_id": channel_id,
            "channel_title": channel['snippet']['title'],
            "subscriber_count": int(stats.get('subscriberCount', 0)),
            "video_count": int(stats.get('videoCount', 0)),
            "view_count": int(stats.get('viewCount', 0))
        }
    
    except HttpError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"YouTube API error: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get YouTube stats: {str(e)}"
        )
