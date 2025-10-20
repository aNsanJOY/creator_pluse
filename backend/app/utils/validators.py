import re
from typing import Dict, Any
from urllib.parse import urlparse
import feedparser
from app.models.source import SourceType


class SourceValidator:
    """Validates source configurations and credentials"""

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate if URL is properly formatted"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    @staticmethod
    def validate_twitter_handle(handle: str) -> bool:
        """Validate Twitter handle format"""
        # Twitter handles: 1-15 characters, alphanumeric and underscore
        pattern = r'^@?[A-Za-z0-9_]{1,15}$'
        return bool(re.match(pattern, handle))

    @staticmethod
    def validate_youtube_channel(url: str) -> bool:
        """Validate YouTube channel URL"""
        youtube_patterns = [
            r'(www\.)?youtube\.com/channel/',
            r'(www\.)?youtube\.com/c/',
            r'(www\.)?youtube\.com/@',
            r'(www\.)?youtube\.com/user/',
        ]
        return any(re.search(pattern, url) for pattern in youtube_patterns)

    @staticmethod
    def validate_rss_feed(url: str) -> tuple[bool, str]:
        """
        Validate RSS feed URL by attempting to parse it
        Returns: (is_valid, error_message)
        """
        try:
            if not SourceValidator.validate_url(url):
                return False, "Invalid URL format"
            
            feed = feedparser.parse(url)
            
            # Check if feed was parsed successfully
            # Only reject if there's a critical parsing error
            if feed.bozo and hasattr(feed, 'bozo_exception'):
                # Some feeds have minor issues but are still usable
                # Only fail on critical errors
                exception_type = type(feed.bozo_exception).__name__
                if exception_type in ['URLError', 'HTTPError', 'SAXParseException']:
                    error_msg = str(feed.bozo_exception)
                    return False, f"Cannot access or parse feed: {error_msg}"
            
            # Check if feed has the basic structure
            if not hasattr(feed, 'feed'):
                return False, "Invalid RSS feed structure"
            
            # Allow feeds with no entries (they might be new or temporarily empty)
            # Just check that the feed object exists
            if not hasattr(feed, 'entries'):
                return False, "RSS feed has invalid structure"
            
            return True, ""
        except Exception as e:
            return False, f"Error validating RSS feed: {str(e)}"

    @staticmethod
    def validate_source(source_type: SourceType, url: str = None, credentials: Dict[str, Any] = None) -> tuple[bool, str]:
        """
        Validate source based on type
        Returns: (is_valid, error_message)
        """
        if source_type == SourceType.TWITTER:
            # Validate credentials first
            if not credentials:
                return False, "X (Twitter) requires credentials. Provide either: (1) Bearer Token, or (2) All OAuth 1.0a credentials (api_key, api_secret, access_token, access_token_secret)"
            
            bearer_token = credentials.get('bearer_token')
            api_key = credentials.get('api_key')
            api_secret = credentials.get('api_secret')
            access_token = credentials.get('access_token')
            access_token_secret = credentials.get('access_token_secret')
            
            # Check if bearer_token is provided
            has_bearer = bool(bearer_token)
            
            # Check if all OAuth 1.0a credentials are provided
            has_oauth1 = all([api_key, api_secret, access_token, access_token_secret])
            
            if not has_bearer and not has_oauth1:
                # Check if partial OAuth 1.0a credentials are provided
                oauth1_fields = [api_key, api_secret, access_token, access_token_secret]
                oauth1_field_names = ['api_key', 'api_secret', 'access_token', 'access_token_secret']
                provided_oauth1 = [name for name, value in zip(oauth1_field_names, oauth1_fields) if value]
                
                if provided_oauth1:
                    missing = [name for name, value in zip(oauth1_field_names, oauth1_fields) if not value]
                    return False, f"Incomplete OAuth 1.0a credentials. Missing: {', '.join(missing)}. Either provide all OAuth 1.0a credentials or use Bearer Token instead."
                else:
                    return False, "X (Twitter) requires credentials. Provide either: (1) Bearer Token, or (2) All OAuth 1.0a credentials (api_key, api_secret, access_token, access_token_secret)"
            
            # Validate URL/handle if provided
            if not url:
                return False, "Twitter handle or URL is required"
            
            # Extract handle from URL if provided
            if 'twitter.com' in url or 'x.com' in url:
                parts = url.rstrip('/').split('/')
                handle = parts[-1] if parts else ""
            else:
                handle = url
            
            if not SourceValidator.validate_twitter_handle(handle):
                return False, "Invalid Twitter handle format"
            
            return True, ""

        elif source_type == SourceType.YOUTUBE:
            if not url:
                return False, "YouTube channel URL is required"
            
            if not SourceValidator.validate_url(url):
                return False, "Invalid URL format"
            
            if not SourceValidator.validate_youtube_channel(url):
                return False, "Invalid YouTube channel URL"
            
            return True, ""

        elif source_type == SourceType.RSS:
            if not url:
                return False, "RSS feed URL is required"
            
            return SourceValidator.validate_rss_feed(url)

        elif source_type in [SourceType.SUBSTACK, SourceType.MEDIUM, SourceType.LINKEDIN]:
            if not url:
                return False, f"{source_type.value.capitalize()} URL is required"
            
            if not SourceValidator.validate_url(url):
                return False, "Invalid URL format"
            
            # Basic domain validation
            domain_map = {
                SourceType.SUBSTACK: 'substack.com',
                SourceType.MEDIUM: 'medium.com',
                SourceType.LINKEDIN: 'linkedin.com'
            }
            
            expected_domain = domain_map.get(source_type)
            if expected_domain and expected_domain not in url:
                return False, f"URL must be from {expected_domain}"
            
            return True, ""

        elif source_type == SourceType.GITHUB:
            # GitHub sources don't require URL, they use config.repository
            # Validation will be done by the GitHub crawler based on config
            return True, ""
        
        elif source_type == SourceType.REDDIT:
            # Reddit sources don't require URL, they use config.subreddit
            # Validation will be done by the Reddit crawler based on config
            return True, ""

        elif source_type == SourceType.CUSTOM:
            if not url:
                return False, "URL is required for custom sources"
            
            if not SourceValidator.validate_url(url):
                return False, "Invalid URL format"
            
            return True, ""

        else:
            # For other types, just validate URL if provided
            if url and not SourceValidator.validate_url(url):
                return False, "Invalid URL format"
            
            return True, ""
