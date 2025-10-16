"""
Substack Connector - Fetches newsletter posts from Substack publications
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import feedparser
import aiohttp
from bs4 import BeautifulSoup
from .base import BaseSourceConnector, SourceContent, SourceRegistry


class SubstackConnector(BaseSourceConnector):
    """
    Connector for Substack newsletters.
    
    Substack provides RSS feeds for all publications at:
    https://{publication}.substack.com/feed
    
    Configuration:
    - publication_url: Full URL to the Substack publication (e.g., https://example.substack.com)
    
    Optional:
    - include_free_only: Only fetch free posts (default: True)
    - fetch_full_content: Fetch full article content via scraping (default: False)
    """
    
    def get_source_type(self) -> str:
        return "substack"
    
    def get_required_credentials(self) -> List[str]:
        # Substack RSS feeds are public, no credentials needed
        return []
    
    def get_required_config(self) -> List[str]:
        return ["publication_url"]
    
    async def validate_connection(self) -> bool:
        """Validate Substack publication URL is accessible"""
        try:
            publication_url = self.config.get("publication_url", "").rstrip("/")
            if not publication_url:
                return False
            
            # Construct RSS feed URL
            feed_url = f"{publication_url}/feed"
            
            # Try to parse the feed
            feed = feedparser.parse(feed_url)
            return feed.bozo == 0 and len(feed.entries) > 0
        except Exception:
            return False
    
    async def fetch_content(self, since: Optional[datetime] = None) -> List[SourceContent]:
        """
        Fetch posts from Substack publication.
        """
        publication_url = self.config.get("publication_url", "").rstrip("/")
        if not publication_url:
            return []
        
        feed_url = f"{publication_url}/feed"
        feed = feedparser.parse(feed_url)
        
        if feed.bozo and not feed.entries:
            return []
        
        contents = []
        include_free_only = self.config.get("include_free_only", True)
        fetch_full_content = self.config.get("fetch_full_content", False)
        
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
            
            # Check if post is free or paid
            is_free = True
            if 'paywall' in content_text.lower() or 'subscribers only' in content_text.lower():
                is_free = False
            
            # Skip paid posts if configured
            if include_free_only and not is_free:
                continue
            
            # Optionally fetch full content
            if fetch_full_content and entry.get('link'):
                full_content = await self._fetch_full_article(entry.get('link'))
                if full_content:
                    content_text = full_content
            
            # Extract author
            author = entry.get('author', '')
            
            # Extract tags
            tags = []
            if hasattr(entry, 'tags') and entry.tags:
                tags = [tag.get('term', '') for tag in entry.tags if tag.get('term')]
            
            # Build metadata
            metadata = {
                'author': author,
                'tags': tags,
                'publication': feed.feed.get('title', ''),
                'is_free': is_free,
                'source': 'substack',
                'publication_url': publication_url
            }
            
            # Add subtitle if available
            if hasattr(entry, 'subtitle'):
                metadata['subtitle'] = entry.subtitle
            
            source_content = SourceContent(
                title=entry.get('title', 'Untitled'),
                content=content_text,
                url=entry.get('link', ''),
                published_at=published_at,
                metadata=metadata
            )
            contents.append(source_content)
        
        return contents
    
    async def _fetch_full_article(self, url: str) -> Optional[str]:
        """
        Fetch full article content from Substack post URL.
        Uses web scraping to extract the article body.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        return None
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find article content (Substack uses specific class names)
                    article = soup.find('div', class_='available-content')
                    if not article:
                        article = soup.find('article')
                    
                    if article:
                        # Remove script and style tags
                        for tag in article.find_all(['script', 'style']):
                            tag.decompose()
                        
                        return article.get_text(separator='\n', strip=True)
                    
                    return None
        except Exception as e:
            # Log error but don't fail the entire fetch
            return None


# Register the connector
SourceRegistry.register('substack', SubstackConnector)
