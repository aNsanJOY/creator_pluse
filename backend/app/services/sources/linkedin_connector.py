"""
LinkedIn Connector - Fetches posts and articles from LinkedIn
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import aiohttp
from .base import BaseSourceConnector, SourceContent, SourceRegistry


class LinkedInConnector(BaseSourceConnector):
    """
    Connector for LinkedIn posts and articles.
    
    Note: LinkedIn's official API requires OAuth and has strict rate limits.
    This connector requires:
    - LinkedIn API credentials (Client ID, Client Secret)
    - OAuth access token with appropriate scopes
    
    Required scopes:
    - r_liteprofile (for profile info)
    - r_organization_social (for company posts)
    - w_member_social (for member posts)
    
    Configuration:
    - profile_type: 'personal' or 'company'
    - profile_id: LinkedIn profile ID or company ID (URN format)
    
    Credentials:
    - access_token: OAuth 2.0 access token
    - refresh_token: OAuth 2.0 refresh token (optional)
    
    Example:
    {
        "profile_type": "personal",
        "profile_id": "urn:li:person:ABC123"
    }
    """
    
    LINKEDIN_API_BASE = "https://api.linkedin.com/v2"
    
    def get_source_type(self) -> str:
        return "linkedin"
    
    def get_required_credentials(self) -> List[str]:
        return ["access_token"]
    
    def get_required_config(self) -> List[str]:
        return ["profile_type", "profile_id"]
    
    async def validate_connection(self) -> bool:
        """Validate LinkedIn API credentials"""
        try:
            access_token = self.credentials.get("access_token")
            if not access_token:
                return False
            
            # Test API connection by fetching profile info
            headers = {
                "Authorization": f"Bearer {access_token}",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.LINKEDIN_API_BASE}/me",
                    headers=headers,
                    timeout=10
                ) as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def fetch_content(self, since: Optional[datetime] = None) -> List[SourceContent]:
        """
        Fetch posts from LinkedIn profile or company page.
        """
        access_token = self.credentials.get("access_token")
        if not access_token:
            return []
        
        profile_type = self.config.get("profile_type", "personal")
        profile_id = self.config.get("profile_id")
        
        if not profile_id:
            return []
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        # Build API endpoint based on profile type
        if profile_type == "personal":
            endpoint = f"{self.LINKEDIN_API_BASE}/ugcPosts"
            params = {
                "q": "authors",
                "authors": f"List({profile_id})",
                "count": 50
            }
        else:  # company
            endpoint = f"{self.LINKEDIN_API_BASE}/ugcPosts"
            params = {
                "q": "authors",
                "authors": f"List({profile_id})",
                "count": 50
            }
        
        contents = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    endpoint,
                    headers=headers,
                    params=params,
                    timeout=30
                ) as response:
                    if response.status != 200:
                        return []
                    
                    data = await response.json()
                    posts = data.get("elements", [])
                    
                    for post in posts:
                        # Parse post data
                        post_content = self._parse_linkedin_post(post, since)
                        if post_content:
                            contents.append(post_content)
        
        except Exception as e:
            # Log error but return what we have
            pass
        
        return contents
    
    def _parse_linkedin_post(self, post: dict, since: Optional[datetime] = None) -> Optional[SourceContent]:
        """Parse a LinkedIn post into SourceContent format"""
        try:
            # Extract post text
            specific_content = post.get("specificContent", {})
            share_content = specific_content.get("com.linkedin.ugc.ShareContent", {})
            share_commentary = share_content.get("shareCommentary", {})
            text = share_commentary.get("text", "")
            
            # Extract created timestamp
            created_timestamp = post.get("created", {}).get("time")
            published_at = None
            if created_timestamp:
                published_at = datetime.fromtimestamp(created_timestamp / 1000)  # Convert from milliseconds
            
            # Skip if older than 'since' timestamp
            if since and published_at and published_at < since:
                return None
            
            # Extract post ID
            post_id = post.get("id", "")
            
            # Build post URL (approximate - LinkedIn URLs are complex)
            post_url = None
            if post_id:
                # Extract activity ID from URN
                activity_id = post_id.split(":")[-1] if ":" in post_id else post_id
                post_url = f"https://www.linkedin.com/feed/update/{activity_id}"
            
            # Extract media info
            media = share_content.get("media", [])
            has_media = len(media) > 0
            media_urls = []
            if has_media:
                for media_item in media:
                    media_url = media_item.get("originalUrl")
                    if media_url:
                        media_urls.append(media_url)
            
            # Extract engagement metrics
            like_count = post.get("numLikes", 0)
            comment_count = post.get("numComments", 0)
            share_count = post.get("numShares", 0)
            
            # Build metadata
            metadata = {
                "post_id": post_id,
                "profile_type": self.config.get("profile_type"),
                "profile_id": self.config.get("profile_id"),
                "has_media": has_media,
                "media_urls": media_urls,
                "engagement": {
                    "likes": like_count,
                    "comments": comment_count,
                    "shares": share_count
                },
                "source": "linkedin"
            }
            
            # Extract title (first line or truncated text)
            title = text.split('\n')[0][:100] if text else "LinkedIn Post"
            if len(text.split('\n')[0]) > 100:
                title += "..."
            
            return SourceContent(
                title=title,
                content=text,
                url=post_url,
                published_at=published_at,
                metadata=metadata
            )
        
        except Exception as e:
            return None
    
    async def handle_rate_limit(self, retry_after: Optional[int] = None):
        """
        Handle LinkedIn API rate limiting.
        LinkedIn uses a points-based throttling system.
        """
        import asyncio
        # LinkedIn recommends waiting at least 1 minute on rate limit
        wait_time = retry_after or 60
        await asyncio.sleep(wait_time)


# Register the connector
SourceRegistry.register('linkedin', LinkedInConnector)
