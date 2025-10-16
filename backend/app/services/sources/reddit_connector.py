"""
Reddit API connector for CreatorPulse.
Fetches posts from subreddits using Async PRAW (Python Reddit API Wrapper).
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from app.services.sources.base import BaseSourceConnector, SourceContent
from app.core.config import settings

try:
    import asyncpraw
    from asyncpraw.exceptions import AsyncPRAWException, RedditAPIException
    ASYNCPRAW_AVAILABLE = True
except ImportError:
    ASYNCPRAW_AVAILABLE = False
    print("Warning: Async PRAW not installed. Install with: pip install asyncpraw")


class RedditConnector(BaseSourceConnector):
    """
    Reddit connector using PRAW library.
    
    Reddit API is free with rate limits:
    - 60 requests per minute
    - Requires Reddit app credentials (free to create)
    
    Supported fetch types:
    - hot: Hot posts from subreddit
    - new: New posts from subreddit
    - top: Top posts (requires time_filter)
    - rising: Rising posts
    """
    
    def __init__(self, source_id: str, config: Dict[str, Any], credentials: Optional[Dict[str, Any]] = None):
        super().__init__(source_id, config, credentials)
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Reddit client with user-provided credentials only."""
        if not ASYNCPRAW_AVAILABLE:
            print("Async PRAW library not available")
            return
        
        try:
            # Get user-specific credentials only
            client_id = None
            client_secret = None
            user_agent = "CreatorPulse/1.0"
            
            if self.credentials:
                client_id = self.credentials.get("reddit_client_id")
                client_secret = self.credentials.get("reddit_client_secret")
                user_agent = self.credentials.get("reddit_user_agent", user_agent)
            
            if client_id and client_secret:
                print("Initializing Async Reddit client with app credentials")
                self.client = asyncpraw.Reddit(
                    client_id=client_id,
                    client_secret=client_secret,
                    user_agent=user_agent
                )
            else:
                print("Error: No Reddit API credentials provided. Please provide credentials when adding the source.")
                print("Create a Reddit app at: https://www.reddit.com/prefs/apps")
                self.client = None
                
        except Exception as e:
            print(f"Error initializing Reddit client: {e}")
            self.client = None
    
    def get_source_type(self) -> str:
        """Return source type identifier."""
        return "reddit"
    
    def get_required_credentials(self) -> List[str]:
        """
        Reddit requires user-provided credentials:
        - reddit_client_id: Reddit app client ID (required)
        - reddit_client_secret: Reddit app client secret (required)
        - reddit_user_agent: User agent string (optional)
        """
        return ["reddit_client_id", "reddit_client_secret"]
    
    def get_required_config(self) -> List[str]:
        """
        Required config:
        - subreddit: Subreddit name (without r/, e.g., 'Angular2')
        - fetch_type: 'hot', 'new', 'top', or 'rising'
        - max_results: Maximum posts to fetch (default: 10, max: 100)
        - time_filter: For 'top' type: 'hour', 'day', 'week', 'month', 'year', 'all'
        """
        return ["subreddit", "fetch_type"]
    
    async def validate_connection(self) -> bool:
        """Validate Reddit API connection."""
        if not self.client:
            print("Reddit client not initialized")
            return False
        
        try:
            # Validate the subreddit exists
            subreddit_name = self.config.get("subreddit")
            if subreddit_name:
                subreddit = await self.client.subreddit(subreddit_name)
                # Access a property to trigger API call
                display_name = await subreddit.display_name()
                print(f"Subreddit r/{display_name} validated")
            else:
                print("Reddit connection validated")
            
            return True
            
        except AsyncPRAWException as e:
            print(f"Reddit connection validation failed: {e}")
            return False
        except Exception as e:
            print(f"Reddit connection validation failed: {e}")
            return False
    
    async def fetch_content(self, since: Optional[datetime] = None) -> List[SourceContent]:
        """
        Fetch posts from Reddit subreddit.
        
        Args:
            since: Only fetch posts after this timestamp (delta crawl)
        
        Returns:
            List of SourceContent objects containing posts
        """
        if not self.client:
            raise ValueError("Reddit client not initialized")
        
        subreddit_name = self.config.get("subreddit")
        fetch_type = self.config.get("fetch_type", "hot")
        max_results = min(self.config.get("max_results", 10), 100)
        time_filter = self.config.get("time_filter", "week")  # For 'top' type
        
        if not subreddit_name:
            raise ValueError("Subreddit is required in config")
        
        contents = []
        
        try:
            subreddit = await self.client.subreddit(subreddit_name)
            
            # Calculate since timestamp for delta crawl (timezone-aware)
            if since:
                since_timestamp = since.timestamp()
            else:
                since_timestamp = (datetime.now(timezone.utc) - timedelta(days=7)).timestamp()
            
            # Fetch posts based on type
            posts = None
            if fetch_type == "hot":
                posts = subreddit.hot(limit=max_results * 2)  # Fetch extra to filter by date
            elif fetch_type == "new":
                posts = subreddit.new(limit=max_results * 2)
            elif fetch_type == "top":
                posts = subreddit.top(time_filter=time_filter, limit=max_results * 2)
            elif fetch_type == "rising":
                posts = subreddit.rising(limit=max_results * 2)
            else:
                raise ValueError(f"Unsupported fetch_type: {fetch_type}. Use 'hot', 'new', 'top', or 'rising'")
            
            # Process posts
            count = 0
            checked = 0
            async for post in posts:
                checked += 1
                if checked > 1000:  # Safety limit
                    break
                
                if count >= max_results:
                    break
                
                # Filter by date (delta crawl)
                post_time = datetime.fromtimestamp(post.created_utc, tz=timezone.utc)
                if post_time.timestamp() < since_timestamp:
                    continue
                
                # Skip removed or deleted posts
                if post.removed_by_category or post.author is None:
                    continue
                
                content = await self._transform_post(post, subreddit_name)
                contents.append(content)
                count += 1
            
            return contents
            
        except RedditAPIException as e:
            error_msg = f"Reddit API error: {e}"
            print(error_msg)
            raise ValueError(error_msg)
        except AsyncPRAWException as e:
            error_msg = f"Reddit error: {e}"
            print(error_msg)
            if "401" in str(e):
                raise ValueError("Reddit authentication failed. Please check your credentials.")
            elif "404" in str(e):
                raise ValueError(f"Subreddit r/{subreddit_name} not found.")
            elif "403" in str(e):
                raise ValueError(f"Access to r/{subreddit_name} is forbidden. It may be private or banned.")
            raise ValueError(error_msg)
        except Exception as e:
            print(f"Error fetching Reddit content: {e}")
            raise
    
    async def _transform_post(self, post, subreddit_name: str) -> SourceContent:
        """Transform a Reddit post into a SourceContent object."""
        
        # Get post content
        content_text = post.selftext if post.selftext else post.title
        
        # Handle different post types
        post_type = "text"
        if post.is_self:
            post_type = "text"
        elif post.url:
            if any(domain in post.url for domain in ['i.redd.it', 'imgur.com', 'i.imgur.com']):
                post_type = "image"
            elif any(domain in post.url for domain in ['v.redd.it', 'youtube.com', 'youtu.be']):
                post_type = "video"
            else:
                post_type = "link"
        
        # Build metadata
        metadata = {
            "post_id": post.id,
            "subreddit": subreddit_name,
            "author": str(post.author) if post.author else "[deleted]",
            "post_type": post_type,
            "score": post.score,
            "upvote_ratio": post.upvote_ratio,
            "num_comments": post.num_comments,
            "awards": post.total_awards_received,
            "is_original_content": post.is_original_content,
            "is_self": post.is_self,
            "permalink": f"https://reddit.com{post.permalink}",
            "flair": post.link_flair_text if post.link_flair_text else None,
            "nsfw": post.over_18,
            "spoiler": post.spoiler,
            "stickied": post.stickied,
            "locked": post.locked
        }
        
        # Add URL if it's a link post
        if not post.is_self and post.url:
            metadata["external_url"] = post.url
        
        return SourceContent(
            title=f"r/{subreddit_name}: {post.title}",
            content=content_text,
            url=f"https://reddit.com{post.permalink}",
            published_at=datetime.fromtimestamp(post.created_utc, tz=timezone.utc),
            metadata=metadata
        )
    
    async def handle_rate_limit(self, retry_after: Optional[int] = None):
        """
        Handle Reddit rate limiting.
        Reddit allows 60 requests per minute.
        """
        import asyncio
        wait_time = retry_after or 60  # Default to 1 minute
        print(f"Rate limit exceeded. Waiting {wait_time} seconds...")
        await asyncio.sleep(wait_time)
    
    async def close(self):
        """Close the Reddit client connection."""
        if self.client:
            await self.client.close()


# Register the connector
from app.services.sources.base import SourceRegistry
SourceRegistry.register("reddit", RedditConnector)
