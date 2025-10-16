"""
RSS Feed Connector - Example implementation of BaseSourceConnector
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import feedparser
import asyncio
from .base import BaseSourceConnector, SourceContent


class RSSConnector(BaseSourceConnector):
    """Connector for RSS feeds"""
    
    def get_source_type(self) -> str:
        return "rss"
    
    def get_required_credentials(self) -> List[str]:
        # RSS feeds typically don't require credentials
        return []
    
    def get_required_config(self) -> List[str]:
        return ["feed_url"]
    
    async def validate_connection(self) -> bool:
        """Validate RSS feed URL is accessible"""
        try:
            feed_url = self.config.get("feed_url")
            if not feed_url:
                print("RSS: No feed_url provided in config")
                return False
            
            print(f"RSS: Validating feed URL: {feed_url}")
            
            # Run feedparser in executor to avoid blocking
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, feed_url)
            
            # Check if feed has entries (be lenient with bozo flag)
            if hasattr(feed, 'entries') and len(feed.entries) > 0:
                print(f"RSS: Feed validated successfully ({len(feed.entries)} entries found)")
                return True
            elif hasattr(feed, 'feed') and hasattr(feed.feed, 'title'):
                print(f"RSS: Feed validated (title: {feed.feed.title})")
                return True
            else:
                print(f"RSS: Feed validation failed - no entries or feed info found")
                if feed.bozo:
                    print(f"RSS: Feed parsing warning: {feed.bozo_exception}")
                return False
                
        except Exception as e:
            print(f"RSS: Validation error: {e}")
            return False
    
    async def fetch_content(self, since: Optional[datetime] = None) -> List[SourceContent]:
        """
        Fetch entries from RSS feed.
        Supports RSS 2.0, RSS 1.0, and Atom formats.
        """
        feed_url = self.config.get("feed_url")
        if not feed_url:
            return []
        
        # Run feedparser in executor to avoid blocking
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, feed_url)
        
        # Check for parsing errors
        if feed.bozo:
            # Log warning but continue if we have entries
            if not feed.entries:
                return []
        
        contents = []
        
        for entry in feed.entries:
            # Parse published date - try multiple fields for different formats
            published_at = None
            
            # Try published_parsed (RSS 2.0, Atom)
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                except (TypeError, ValueError):
                    pass
            
            # Try updated_parsed (Atom)
            if not published_at and hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                try:
                    published_at = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                except (TypeError, ValueError):
                    pass
            
            # Try created_parsed (some feeds)
            if not published_at and hasattr(entry, 'created_parsed') and entry.created_parsed:
                try:
                    published_at = datetime(*entry.created_parsed[:6], tzinfo=timezone.utc)
                except (TypeError, ValueError):
                    pass
            
            # Skip if older than 'since' timestamp
            if since and published_at and published_at < since:
                continue
            
            # Extract content - try multiple fields for different formats
            content_text = ""
            
            # Try content field (Atom, some RSS feeds)
            if hasattr(entry, 'content') and entry.content:
                if isinstance(entry.content, list) and len(entry.content) > 0:
                    content_text = entry.content[0].get('value', '')
                else:
                    content_text = str(entry.content)
            
            # Try summary field (RSS 2.0, Atom)
            if not content_text and hasattr(entry, 'summary'):
                content_text = entry.summary
            
            # Try description field (RSS 2.0)
            if not content_text and hasattr(entry, 'description'):
                content_text = entry.description
            
            # Extract author - try multiple fields
            author = ""
            if hasattr(entry, 'author'):
                author = entry.author
            elif hasattr(entry, 'author_detail') and entry.author_detail:
                author = entry.author_detail.get('name', '')
            elif hasattr(entry, 'dc_creator'):
                author = entry.dc_creator
            
            # Extract tags/categories
            tags = []
            if hasattr(entry, 'tags') and entry.tags:
                tags = [tag.get('term', '') for tag in entry.tags if tag.get('term')]
            elif hasattr(entry, 'categories') and entry.categories:
                tags = list(entry.categories)
            
            # Build metadata
            metadata = {
                'author': author,
                'tags': tags,
                'feed_title': feed.feed.get('title', ''),
                'feed_type': getattr(feed, 'version', 'unknown'),
            }
            
            # Add optional fields if available
            if hasattr(entry, 'id'):
                metadata['entry_id'] = entry.id
            if hasattr(entry, 'updated'):
                metadata['updated'] = entry.updated
            if hasattr(entry, 'media_content'):
                metadata['has_media'] = True
            
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
from .base import SourceRegistry
SourceRegistry.register('rss', RSSConnector)
