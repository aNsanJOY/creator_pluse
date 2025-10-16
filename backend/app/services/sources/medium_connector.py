"""
Medium Connector - Fetches articles from Medium publications and users
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import feedparser
import aiohttp
from .base import BaseSourceConnector, SourceContent, SourceRegistry


class MediumConnector(BaseSourceConnector):
    """
    Connector for Medium articles.
    
    Medium provides RSS feeds for:
    - User profiles: https://medium.com/feed/@{username}
    - Publications: https://medium.com/feed/{publication}
    - Tags: https://medium.com/feed/tag/{tag}
    
    Configuration:
    - feed_type: Type of feed ('user', 'publication', or 'tag')
    - identifier: Username, publication name, or tag name
    
    Example configs:
    - User: {"feed_type": "user", "identifier": "username"}
    - Publication: {"feed_type": "publication", "identifier": "publication-name"}
    - Tag: {"feed_type": "tag", "identifier": "artificial-intelligence"}
    """
    
    def get_source_type(self) -> str:
        return "medium"
    
    def get_required_credentials(self) -> List[str]:
        # Medium RSS feeds are public
        return []
    
    def get_required_config(self) -> List[str]:
        return ["feed_type", "identifier"]
    
    def _build_feed_url(self) -> Optional[str]:
        """Build Medium RSS feed URL based on configuration"""
        feed_type = self.config.get("feed_type", "").lower()
        identifier = self.config.get("identifier", "").strip()
        
        if not identifier:
            return None
        
        if feed_type == "user":
            # User feed format: https://medium.com/feed/@username
            if not identifier.startswith("@"):
                identifier = f"@{identifier}"
            return f"https://medium.com/feed/{identifier}"
        elif feed_type == "publication":
            # Publication feed format: https://medium.com/feed/publication-name
            return f"https://medium.com/feed/{identifier}"
        elif feed_type == "tag":
            # Tag feed format: https://medium.com/feed/tag/tag-name
            return f"https://medium.com/feed/tag/{identifier}"
        else:
            return None
    
    async def validate_connection(self) -> bool:
        """Validate Medium feed URL is accessible"""
        try:
            feed_url = self._build_feed_url()
            if not feed_url:
                return False
            
            feed = feedparser.parse(feed_url)
            return feed.bozo == 0 and len(feed.entries) > 0
        except Exception:
            return False
    
    async def fetch_content(self, since: Optional[datetime] = None) -> List[SourceContent]:
        """
        Fetch articles from Medium feed.
        """
        feed_url = self._build_feed_url()
        if not feed_url:
            return []
        
        feed = feedparser.parse(feed_url)
        
        if feed.bozo and not feed.entries:
            return []
        
        contents = []
        
        for entry in feed.entries:
            # Parse published date
            published_at = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    published_at = datetime(*entry.published_parsed[:6])
                except (TypeError, ValueError):
                    pass
            
            # Skip if older than 'since' timestamp
            if since and published_at and published_at < since:
                continue
            
            # Extract content
            content_text = ""
            if hasattr(entry, 'content') and entry.content:
                if isinstance(entry.content, list) and len(entry.content) > 0:
                    content_text = entry.content[0].get('value', '')
            elif hasattr(entry, 'summary'):
                content_text = entry.summary
            
            # Extract author
            author = entry.get('author', '')
            
            # Extract tags/categories
            tags = []
            if hasattr(entry, 'tags') and entry.tags:
                tags = [tag.get('term', '') for tag in entry.tags if tag.get('term')]
            
            # Extract reading time (Medium-specific)
            reading_time = None
            if hasattr(entry, 'content') and entry.content:
                # Medium sometimes includes reading time in content
                content_str = str(entry.content)
                if 'min read' in content_str:
                    try:
                        # Extract number before "min read"
                        import re
                        match = re.search(r'(\d+)\s*min read', content_str)
                        if match:
                            reading_time = int(match.group(1))
                    except:
                        pass
            
            # Build metadata
            metadata = {
                'author': author,
                'tags': tags,
                'feed_type': self.config.get('feed_type'),
                'identifier': self.config.get('identifier'),
                'source': 'medium'
            }
            
            if reading_time:
                metadata['reading_time_minutes'] = reading_time
            
            # Add GUID if available
            if hasattr(entry, 'id'):
                metadata['medium_id'] = entry.id
            
            # Extract thumbnail if available
            if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                metadata['thumbnail_url'] = entry.media_thumbnail[0].get('url', '')
            
            source_content = SourceContent(
                title=entry.get('title', 'Untitled'),
                content=content_text,
                url=entry.get('link', ''),
                published_at=published_at,
                metadata=metadata
            )
            contents.append(source_content)
        
        return contents


# Register the connector
SourceRegistry.register('medium', MediumConnector)
