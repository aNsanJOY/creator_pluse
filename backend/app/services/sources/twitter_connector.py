"""
X (formerly Twitter) API connector for CreatorPulse.
Handles OAuth authentication, content fetching, and rate limiting.
"""

import tweepy
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from app.services.sources.base import BaseSourceConnector, SourceContent
from app.core.config import settings


class TwitterConnector(BaseSourceConnector):
    """
    X (formerly Twitter) connector using Tweepy library.
    Supports OAuth 1.0a and OAuth 2.0 authentication.
    
    X API Tier Requirements (as of October 2024):
    - Free tier: 500 posts/month read, 50 posts/month write
    - Basic tier: $200/month, higher limits, more endpoints
    - Pro tier: Professional access with advanced features
    - Enterprise: Custom pricing and limits
    
    Note: Most endpoints used here require at least Basic tier access.
    """
    
    def __init__(self, source_id: str, config: Dict[str, Any], credentials: Optional[Dict[str, Any]] = None):
        super().__init__(source_id, config, credentials)
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """
        Initialize Tweepy client with user-provided credentials only.
        No fallback to global settings.
        """
        try:
            # Get API keys from user credentials only
            api_key = self.credentials.get('api_key') if self.credentials else None
            api_secret = self.credentials.get('api_secret') if self.credentials else None
            access_token = self.credentials.get('access_token') if self.credentials else None
            access_token_secret = self.credentials.get('access_token_secret') if self.credentials else None
            bearer_token = self.credentials.get('bearer_token') if self.credentials else None
            
            # OAuth 1.0a User Context (for user timeline, likes, etc.)
            if all([api_key, api_secret, access_token, access_token_secret]):
                print("Initializing X (Twitter) client with OAuth 1.0a credentials")
                auth = tweepy.OAuth1UserHandler(
                    consumer_key=api_key,
                    consumer_secret=api_secret,
                    access_token=access_token,
                    access_token_secret=access_token_secret
                )
                self.api = tweepy.API(auth, wait_on_rate_limit=True)
                
                # Also create v2 client for better features
                self.client = tweepy.Client(
                    consumer_key=api_key,
                    consumer_secret=api_secret,
                    access_token=access_token,
                    access_token_secret=access_token_secret,
                    wait_on_rate_limit=True
                )
                self.auth_type = "oauth1"
            # OAuth 2.0 Bearer Token (read-only access)
            elif bearer_token:
                print("Initializing X (Twitter) client with Bearer Token (OAuth 2.0)")
                self.client = tweepy.Client(
                    bearer_token=bearer_token,
                    wait_on_rate_limit=True
                )
                self.api = None
                self.auth_type = "bearer"
            else:
                print("Error: No X (Twitter) API credentials provided. Please provide credentials when adding the source.")
                self.client = None
                self.api = None
                self.auth_type = None
        except Exception as e:
            print(f"Error initializing X (Twitter) client: {e}")
            self.client = None
            self.api = None
            self.auth_type = None
    
    def get_source_type(self) -> str:
        return "twitter"
    
    def get_required_credentials(self) -> List[str]:
        """
        X (Twitter) requires user-provided credentials:
        - OAuth 1.0a: api_key, api_secret, access_token, access_token_secret
        - OAuth 2.0: bearer_token (alternative)
        """
        # At minimum, bearer_token OR all OAuth 1.0a credentials required
        return ["api_key", "api_secret", "access_token", "access_token_secret"]
    
    def get_required_config(self) -> List[str]:
        """
        Required config:
        - username: X (Twitter) username to monitor (without @)
        - fetch_type: 'timeline' (user posts), 'mentions', 'likes', or 'list'
        - max_results: Maximum posts to fetch per request (default: 10, max: 100)
        """
        return ["username", "fetch_type"]
    
    async def validate_connection(self) -> bool:
        """Validate X (Twitter) API connection"""
        if not self.client:
            print("X (Twitter) client not initialized")
            return False
        
        try:
            # For OAuth 1.0a, try to get authenticated user info
            if self.auth_type == "oauth1":
                me = self.client.get_me()
                if me.data:
                    print(f"X (Twitter) connection validated for user: {me.data.username}")
                    return True
                else:
                    print("X (Twitter) connection validation failed: No user data returned")
                    return False
            # For Bearer Token, try a simple API call
            elif self.auth_type == "bearer":
                # Try to get a public user to validate the token
                test_user = self.client.get_user(username="twitter")
                if test_user.data:
                    print("X (Twitter) connection validated with Bearer Token")
                    return True
                else:
                    print("X (Twitter) connection validation failed: Bearer token invalid")
                    return False
            else:
                print("X (Twitter) connection validation failed: Unknown auth type")
                return False
        except tweepy.Unauthorized as e:
            print(f"X (Twitter) authentication failed (401 Unauthorized): {e}")
            print("\nPossible causes:")
            print("1. Invalid API credentials (check TWITTER_API_KEY, TWITTER_API_SECRET, etc. in .env)")
            print("2. Expired or revoked access tokens")
            print("3. App doesn't have required permissions in X Developer Portal")
            print("4. API access level is insufficient (need Basic or Pro tier for most endpoints)")
            print("\nPlease verify your credentials at: https://developer.x.com/")
            return False
        except tweepy.Forbidden as e:
            print(f"X (Twitter) access forbidden (403): {e}")
            print("Your app may not have the required access level or permissions.")
            print("Check your X Developer Portal settings at: https://developer.x.com/")
            return False
        except Exception as e:
            print(f"X (Twitter) connection validation failed: {e}")
            return False
    
    async def fetch_content(self, since: Optional[datetime] = None) -> List[SourceContent]:
        """
        Fetch posts from X (Twitter).
        
        Args:
            since: Only fetch posts after this timestamp (delta crawl)
        
        Returns:
            List of SourceContent objects containing posts
        """
        if not self.client:
            raise ValueError("X (Twitter) client not initialized")
        
        username = self.config.get("username")
        fetch_type = self.config.get("fetch_type", "timeline")
        max_results = min(self.config.get("max_results", 10), 100)  # Default 10, max 100 (API limit)
        
        if not username:
            raise ValueError("Username is required in config")
        
        contents = []
        
        try:
            # Get user ID from username
            user = self.client.get_user(username=username)
            if not user.data:
                raise ValueError(f"User {username} not found")
            
            user_id = user.data.id
            
            # Prepare query parameters
            tweet_fields = ["created_at", "public_metrics", "entities", "referenced_tweets"]
            expansions = ["author_id", "referenced_tweets.id"]
            
            # Calculate start_time for delta crawl
            start_time = None
            if since:
                # Twitter API requires RFC 3339 format
                start_time = since.isoformat() + "Z"
            else:
                # Default to last 7 days if no since parameter
                start_time = (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z"
            
            # Fetch tweets based on type
            # Note: These endpoints require at least Basic tier ($200/month as of Oct 2024)
            tweets = None
            if fetch_type == "timeline":
                # Get user's tweets (posts)
                # Endpoint: GET /2/users/:id/tweets
                # Tier requirement: Basic or higher
                tweets = self.client.get_users_tweets(
                    id=user_id,
                    max_results=min(max_results, 100),  # API limit is 100
                    tweet_fields=tweet_fields,
                    expansions=expansions,
                    start_time=start_time,
                    exclude=["retweets", "replies"]  # Only original posts
                )
            elif fetch_type == "mentions":
                # Get mentions of the user
                # Endpoint: GET /2/users/:id/mentions
                # Tier requirement: Basic or higher
                tweets = self.client.get_users_mentions(
                    id=user_id,
                    max_results=min(max_results, 100),
                    tweet_fields=tweet_fields,
                    start_time=start_time
                )
            elif fetch_type == "likes":
                # Get user's liked tweets
                # Endpoint: GET /2/users/:id/liked_tweets
                # Tier requirement: Basic or higher
                tweets = self.client.get_liked_tweets(
                    id=user_id,
                    max_results=min(max_results, 100),
                    tweet_fields=tweet_fields,
                    expansions=expansions
                )
            else:
                raise ValueError(f"Unsupported fetch_type: {fetch_type}")
            
            # Process tweets
            if tweets and tweets.data:
                for tweet in tweets.data:
                    content = self._transform_tweet(tweet, username)
                    contents.append(content)
            
            return contents
        
        except tweepy.TooManyRequests as e:
            # Handle rate limiting
            print(f"X (Twitter) rate limit reached: {e}")
            await self.handle_rate_limit(retry_after=900)  # 15 minutes
            return []
        except tweepy.Unauthorized as e:
            error_msg = (
                f"X (Twitter) authentication failed (401 Unauthorized): {e}\n\n"
                "Possible causes:\n"
                "1. Invalid API credentials - Check your .env file:\n"
                "   - TWITTER_API_KEY\n"
                "   - TWITTER_API_SECRET\n"
                "   - TWITTER_ACCESS_TOKEN\n"
                "   - TWITTER_ACCESS_SECRET\n\n"
                "2. Expired or revoked access tokens - Regenerate tokens in X Developer Portal\n\n"
                "3. Insufficient API access level - You may need Basic or Pro tier:\n"
                "   - Free tier: Limited to 500 posts/month read (insufficient for most use cases)\n"
                "   - Basic tier: $200/month (as of Oct 2024), required for user timeline endpoints\n"
                "   - Go to https://developer.x.com/en/portal/products\n"
                "   - Upgrade to Basic or Pro tier for your app\n\n"
                "4. App permissions issue - Ensure your app has read permissions\n\n"
                "5. Incorrect authentication method - Some endpoints require OAuth 1.0a User Context\n\n"
                "Please verify your credentials at: https://developer.x.com/"
            )
            print(error_msg)
            raise ValueError("X (Twitter) authentication failed. Please check your API credentials and access level.")
        except tweepy.Forbidden as e:
            error_msg = (
                f"X (Twitter) access forbidden (403): {e}\n\n"
                "This usually means:\n"
                "1. Your app doesn't have the required access level (need Basic or Pro tier)\n"
                "2. The endpoint requires specific permissions your app doesn't have\n"
                "3. You're trying to access protected/private content\n\n"
                "To fix:\n"
                "- Upgrade to Basic or Pro tier: https://developer.x.com/en/portal/products\n"
                "- Check app permissions in X Developer Portal\n"
                "- Ensure the user account you're accessing is public"
            )
            print(error_msg)
            raise ValueError("X (Twitter) access forbidden. You may need Elevated API access.")
        except tweepy.NotFound as e:
            print(f"X (Twitter) user not found: {e}")
            raise ValueError(f"X (Twitter) user '{username}' not found. Please check the username.")
        except Exception as e:
            print(f"Error fetching X (Twitter) content: {e}")
            raise
    
    def _transform_tweet(self, tweet, username: str) -> SourceContent:
        """Transform a post into a SourceContent object"""
        tweet_id = tweet.id
        tweet_url = f"https://twitter.com/{username}/status/{tweet_id}"
        
        # Extract metrics
        metrics = tweet.public_metrics if hasattr(tweet, 'public_metrics') else {}
        
        # Build metadata
        metadata = {
            "tweet_id": str(tweet_id),
            "author": username,
            "engagement": {
                "likes": metrics.get("like_count", 0),
                "retweets": metrics.get("retweet_count", 0),
                "replies": metrics.get("reply_count", 0),
                "quotes": metrics.get("quote_count", 0)
            }
        }
        
        # Extract hashtags and mentions if available
        if hasattr(tweet, 'entities'):
            entities = tweet.entities
            if entities:
                if 'hashtags' in entities:
                    metadata["hashtags"] = [tag['tag'] for tag in entities['hashtags']]
                if 'mentions' in entities:
                    metadata["mentions"] = [mention['username'] for mention in entities['mentions']]
                if 'urls' in entities:
                    metadata["urls"] = [url['expanded_url'] for url in entities['urls']]
        
        # Create content
        return SourceContent(
            title=f"Post by @{username}",
            content=tweet.text,
            url=tweet_url,
            published_at=tweet.created_at if hasattr(tweet, 'created_at') else datetime.utcnow(),
            metadata=metadata
        )
    
    async def handle_rate_limit(self, retry_after: Optional[int] = None):
        """
        Handle X (Twitter) rate limiting.
        X has different rate limits for different endpoints.
        """
        wait_time = retry_after or 900  # Default 15 minutes
        print(f"Rate limit hit. Waiting {wait_time} seconds...")
        await asyncio.sleep(wait_time)


# Register the connector
from app.services.sources.base import SourceRegistry
SourceRegistry.register("twitter", TwitterConnector)
