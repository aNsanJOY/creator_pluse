"""
YouTube API connector for CreatorPulse.
Handles OAuth authentication, content fetching, and rate limiting.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.services.sources.base import BaseSourceConnector, SourceContent
from app.core.config import settings


class YouTubeConnector(BaseSourceConnector):
    """
    YouTube connector using Google API Client.
    Supports OAuth 2.0 authentication and fetches videos, comments, and analytics.
    """
    
    def __init__(self, source_id: str, config: Dict[str, Any], credentials: Optional[Dict[str, Any]] = None):
        super().__init__(source_id, config, credentials)
        self.youtube = None
        self._initialize_client()
    
    def _initialize_client(self):
        """
        Initialize YouTube API client with user-provided credentials only.
        No fallback to global settings.
        """
        try:
            # Get API key from user credentials only
            api_key = None
            if self.credentials and 'api_key' in self.credentials:
                api_key = self.credentials.get('api_key')
            
            if not api_key:
                print("Error: No YouTube API key provided. Please provide an API key when adding the source.")
                return
            
            # Build YouTube service with API key
            self.youtube = build(
                'youtube',
                'v3',
                developerKey=api_key,
                cache_discovery=False
            )
        except Exception as e:
            print(f"Error initializing YouTube client: {e}")
            self.youtube = None
    
    def get_source_type(self) -> str:
        return "youtube"
    
    def get_required_credentials(self) -> List[str]:
        """
        YouTube requires user-provided credentials:
        - api_key: YouTube Data API key (required)
        """
        return ["api_key"]
    
    def get_required_config(self) -> List[str]:
        """
        Required config:
        - channel_id: YouTube channel ID or handle (e.g., @username) to monitor
        - fetch_type: 'uploads' (channel videos), 'liked', 'subscriptions', or 'playlist'
        - max_results: Maximum videos to fetch per request (default: 10, max: 50)
        """
        return ["channel_id", "fetch_type"]
    
    async def validate_connection(self) -> bool:
        """Validate YouTube API connection"""
        if not self.youtube:
            print(f"YouTube client not initialized. Config: {self.config}, Credentials: {bool(self.credentials)}")
            return False
        
        try:
            # Try to get channel info
            channel_id = self.config.get("channel_id")
            if not channel_id:
                print(f"No channel_id found in config. Config keys: {list(self.config.keys())}, Config: {self.config}")
                return False
            
            print(f"Validating YouTube connection for channel_id: {channel_id}")
            
            # If channel_id starts with @, it's a handle - need to convert to channel ID
            if channel_id.startswith('@'):
                print(f"Detected YouTube handle, searching for channel...")
                search_request = self.youtube.search().list(
                    part="snippet",
                    q=channel_id,
                    type="channel",
                    maxResults=1
                )
                search_response = search_request.execute()
                
                if not search_response.get('items'):
                    print(f"No channel found for handle: {channel_id}")
                    return False
                
                # Get the actual channel ID from search results
                actual_channel_id = search_response['items'][0]['snippet']['channelId']
                print(f"Converted handle {channel_id} to channel ID: {actual_channel_id}")
                
                # Update config with the actual channel ID
                self.config['channel_id'] = actual_channel_id
                channel_id = actual_channel_id
            
            request = self.youtube.channels().list(
                part="snippet,contentDetails,statistics",
                id=channel_id
            )
            response = request.execute()
            
            has_items = len(response.get('items', [])) > 0
            if not has_items:
                print(f"No channel found for channel_id: {channel_id}")
            else:
                print(f"YouTube connection validated successfully for channel_id: {channel_id}")
            
            return has_items
        except HttpError as e:
            print(f"YouTube connection validation failed (HttpError): {e}")
            return False
        except Exception as e:
            print(f"YouTube connection validation error (Exception): {type(e).__name__}: {e}")
            return False
    
    async def fetch_content(self, since: Optional[datetime] = None) -> List[SourceContent]:
        """
        Fetch videos from YouTube.
        
        Args:
            since: Only fetch videos published after this timestamp (delta crawl)
        
        Returns:
            List of SourceContent objects containing video metadata
        """
        if not self.youtube:
            raise ValueError("YouTube client not initialized")
        
        channel_id = self.config.get("channel_id")
        fetch_type = self.config.get("fetch_type", "uploads")
        max_results = min(self.config.get("max_results", 10), 50)  # Default 10, max 50 (API limit)
        
        if not channel_id:
            raise ValueError("channel_id is required in config")
        
        contents = []
        
        try:
            # Calculate published_after for delta crawl
            published_after = None
            if since:
                # YouTube API requires RFC 3339 format
                published_after = since.isoformat() + "Z"
            else:
                # Default to last 30 days if no since parameter
                published_after = (datetime.utcnow() - timedelta(days=30)).isoformat() + "Z"
            
            # Fetch videos based on type
            if fetch_type == "uploads":
                # Get channel's uploads playlist
                channel_response = self.youtube.channels().list(
                    part="contentDetails",
                    id=channel_id
                ).execute()
                
                if not channel_response.get('items'):
                    raise ValueError(f"Channel {channel_id} not found")
                
                uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
                
                # Get videos from uploads playlist
                playlist_response = self.youtube.playlistItems().list(
                    part="snippet,contentDetails",
                    playlistId=uploads_playlist_id,
                    maxResults=min(max_results, 50),  # API limit is 50
                    # Note: playlistItems doesn't support publishedAfter, so we filter manually
                ).execute()
                
                video_ids = [item['contentDetails']['videoId'] for item in playlist_response.get('items', [])]
                
            elif fetch_type == "search":
                # Search for videos in the channel
                search_response = self.youtube.search().list(
                    part="id,snippet",
                    channelId=channel_id,
                    maxResults=min(max_results, 50),
                    order="date",
                    type="video",
                    publishedAfter=published_after
                ).execute()
                
                video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
                
            elif fetch_type == "liked":
                # Get liked videos (requires OAuth with appropriate scope)
                # Note: This requires the channel to be authenticated
                print("Warning: 'liked' fetch type requires OAuth authentication and is not supported with API key only")
                print("Falling back to 'uploads' fetch type for this channel")
                # Fallback to uploads
                channel_response = self.youtube.channels().list(
                    part="contentDetails",
                    id=channel_id
                ).execute()
                
                if not channel_response.get('items'):
                    raise ValueError(f"Channel {channel_id} not found")
                
                uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
                
                playlist_response = self.youtube.playlistItems().list(
                    part="snippet,contentDetails",
                    playlistId=uploads_playlist_id,
                    maxResults=min(max_results, 50)
                ).execute()
                
                video_ids = [item['contentDetails']['videoId'] for item in playlist_response.get('items', [])]
                    
            elif fetch_type == "subscriptions":
                # Get videos from subscribed channels (requires OAuth)
                print("Warning: 'subscriptions' fetch type requires OAuth authentication and is not supported with API key only")
                print("Falling back to 'uploads' fetch type for this channel")
                # Fallback to uploads
                channel_response = self.youtube.channels().list(
                    part="contentDetails",
                    id=channel_id
                ).execute()
                
                if not channel_response.get('items'):
                    raise ValueError(f"Channel {channel_id} not found")
                
                uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
                
                playlist_response = self.youtube.playlistItems().list(
                    part="snippet,contentDetails",
                    playlistId=uploads_playlist_id,
                    maxResults=min(max_results, 50)
                ).execute()
                
                video_ids = [item['contentDetails']['videoId'] for item in playlist_response.get('items', [])]
                    
            elif fetch_type == "playlist":
                # Get videos from a specific playlist
                playlist_id = self.config.get("playlist_id")
                if not playlist_id:
                    raise ValueError("playlist_id is required for fetch_type='playlist'")
                
                playlist_response = self.youtube.playlistItems().list(
                    part="snippet,contentDetails",
                    playlistId=playlist_id,
                    maxResults=min(max_results, 50)
                ).execute()
                
                video_ids = [item['contentDetails']['videoId'] for item in playlist_response.get('items', [])]
            else:
                raise ValueError(f"Unsupported fetch_type: {fetch_type}")
            
            # Get detailed video information
            if video_ids:
                videos_response = self.youtube.videos().list(
                    part="snippet,contentDetails,statistics",
                    id=','.join(video_ids)
                ).execute()
                
                for video in videos_response.get('items', []):
                    # Filter by published date if using playlist method
                    if since and fetch_type in ["uploads", "playlist"]:
                        published_at = datetime.fromisoformat(video['snippet']['publishedAt'].replace('Z', '+00:00'))
                        if published_at <= since:
                            continue
                    
                    content = self._transform_video(video)
                    contents.append(content)
            
            return contents
        
        except HttpError as e:
            if e.resp.status == 403:
                # Quota exceeded or permission denied
                print(f"YouTube API quota exceeded or permission denied: {e}")
                await self.handle_rate_limit(retry_after=3600)  # 1 hour
                return []
            elif e.resp.status == 401:
                print(f"YouTube authentication failed: {e}")
                raise ValueError("YouTube authentication failed. Please reconnect your account.")
            else:
                print(f"YouTube API error: {e}")
                raise
        except Exception as e:
            print(f"Error fetching YouTube content: {e}")
            raise
    
    def _transform_video(self, video: Dict[str, Any]) -> SourceContent:
        """Transform a YouTube video into a SourceContent object"""
        video_id = video['id']
        snippet = video['snippet']
        statistics = video.get('statistics', {})
        content_details = video.get('contentDetails', {})
        
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Build metadata
        metadata = {
            "video_id": video_id,
            "channel_id": snippet.get('channelId'),
            "channel_title": snippet.get('channelTitle'),
            "duration": content_details.get('duration'),
            "engagement": {
                "views": int(statistics.get('viewCount', 0)),
                "likes": int(statistics.get('likeCount', 0)),
                "comments": int(statistics.get('commentCount', 0))
            },
            "tags": snippet.get('tags', []),
            "category_id": snippet.get('categoryId'),
            "thumbnail": snippet.get('thumbnails', {}).get('high', {}).get('url')
        }
        
        # Parse published date
        published_at = datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00'))
        
        # Create content
        return SourceContent(
            title=snippet.get('title', ''),
            content=snippet.get('description', ''),
            url=video_url,
            published_at=published_at,
            metadata=metadata
        )
    
    async def handle_rate_limit(self, retry_after: Optional[int] = None):
        """
        Handle YouTube API rate limiting.
        YouTube has quota limits that reset daily.
        """
        wait_time = retry_after or 3600  # Default 1 hour
        print(f"YouTube API quota limit hit. Waiting {wait_time} seconds...")
        await asyncio.sleep(wait_time)


# Register the connector
from app.services.sources.base import SourceRegistry
SourceRegistry.register("youtube", YouTubeConnector)
