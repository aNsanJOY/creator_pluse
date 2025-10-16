# Adding New Source Types to CreatorPulse

This guide explains how to add support for new content sources (e.g., Substack, Medium, LinkedIn, Podcasts, etc.) to CreatorPulse.

## Overview

CreatorPulse uses a plugin-based architecture for source connectors. This allows you to easily add new source types without modifying the core application code.

## Architecture

### Components

1. **BaseSourceConnector** - Abstract base class that all connectors must inherit from
2. **SourceRegistry** - Registry that manages all available source connectors
3. **Source Connectors** - Implementations for specific source types (Twitter, RSS, etc.)

### Database Schema

The `sources` table is designed to be flexible:
- `source_type` (VARCHAR) - Can be any string (twitter, youtube, rss, substack, medium, etc.)
- `credentials` (JSONB) - Flexible storage for source-specific credentials
- `config` (JSONB) - Additional configuration per source type

## Step-by-Step Guide

### 1. Create a New Connector Class

Create a new file in `backend/app/services/sources/` (e.g., `substack_connector.py`):

```python
from typing import List, Optional, Dict, Any
from datetime import datetime
from .base import BaseSourceConnector, SourceContent, SourceRegistry


class SubstackConnector(BaseSourceConnector):
    """Connector for Substack newsletters"""
    
    def get_source_type(self) -> str:
        """Return the source type identifier"""
        return "substack"
    
    def get_required_credentials(self) -> List[str]:
        """Return list of required credential fields"""
        # Substack RSS feeds are public, so no credentials needed
        return []
    
    def get_required_config(self) -> List[str]:
        """Return list of required configuration fields"""
        return ["publication_url"]  # e.g., https://example.substack.com
    
    async def validate_connection(self) -> bool:
        """Validate that the Substack publication exists"""
        try:
            publication_url = self.config.get("publication_url")
            if not publication_url:
                return False
            
            # Substack RSS feed is at /feed
            rss_url = f"{publication_url.rstrip('/')}/feed"
            
            # Try to fetch the feed
            import feedparser
            feed = feedparser.parse(rss_url)
            return feed.bozo == 0
        except Exception:
            return False
    
    async def fetch_content(self, since: Optional[datetime] = None) -> List[SourceContent]:
        """Fetch posts from Substack publication"""
        publication_url = self.config.get("publication_url")
        if not publication_url:
            return []
        
        rss_url = f"{publication_url.rstrip('/')}/feed"
        
        import feedparser
        feed = feedparser.parse(rss_url)
        contents = []
        
        for entry in feed.entries:
            # Parse published date
            published_at = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_at = datetime(*entry.published_parsed[:6])
            
            # Skip if older than 'since' timestamp
            if since and published_at and published_at < since:
                continue
            
            # Extract content
            content_text = entry.get('summary', '')
            if hasattr(entry, 'content'):
                content_text = entry.content[0].value
            
            source_content = SourceContent(
                title=entry.get('title', ''),
                content=content_text,
                url=entry.get('link'),
                published_at=published_at,
                metadata={
                    'author': entry.get('author', ''),
                    'publication': feed.feed.get('title', ''),
                    'source_type': 'substack'
                }
            )
            contents.append(source_content)
        
        return contents


# Register the connector
SourceRegistry.register('substack', SubstackConnector)
```

### 2. Register the Connector

The connector is automatically registered when you import it. Add it to `backend/app/services/sources/__init__.py`:

```python
# Import all connectors to register them
from .rss_connector import RSSConnector
from .substack_connector import SubstackConnector
# Add more imports as you create new connectors
```

### 3. Update Frontend (Optional)

Add the new source type to the frontend TypeScript types in `frontend/src/services/sources.service.ts`:

```typescript
export type SourceType = 
  | 'twitter' 
  | 'youtube' 
  | 'rss' 
  | 'substack'  // Add your new type here
  | 'medium' 
  | 'linkedin' 
  | 'custom'
  | string
```

### 4. Create UI Components (Optional)

Create a source connection card for your new source type in the frontend:

```tsx
// frontend/src/components/sources/SubstackSourceCard.tsx
export function SubstackSourceCard() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Substack</CardTitle>
      </CardHeader>
      <CardContent>
        <Input 
          label="Publication URL" 
          placeholder="https://example.substack.com"
        />
        <Button onClick={handleConnect}>Connect Substack</Button>
      </CardContent>
    </Card>
  )
}
```

## Examples of Source Types to Add

### 1. Medium
- **Type**: `medium`
- **Config**: `username` or `publication_url`
- **Method**: RSS feed (`https://medium.com/feed/@username`)

### 2. LinkedIn
- **Type**: `linkedin`
- **Credentials**: OAuth tokens
- **Method**: LinkedIn API

### 3. Podcast
- **Type**: `podcast`
- **Config**: `rss_feed_url`
- **Method**: Parse podcast RSS feed

### 4. Newsletter (Generic)
- **Type**: `newsletter`
- **Config**: `rss_feed_url` or `email_forward_address`
- **Method**: RSS or email parsing

### 5. GitHub
- **Type**: `github`
- **Config**: `username` or `repo_url`
- **Method**: GitHub API (releases, commits, etc.)

### 6. Hacker News
- **Type**: `hackernews`
- **Config**: `username` or `topic`
- **Method**: Hacker News API

### 7. Reddit
- **Type**: `reddit`
- **Config**: `subreddit` or `username`
- **Method**: Reddit API

## Advanced Features

### OAuth Authentication

For sources requiring OAuth (Twitter, LinkedIn, etc.):

```python
class LinkedInConnector(BaseSourceConnector):
    def get_required_credentials(self) -> List[str]:
        return ["access_token", "refresh_token"]
    
    async def validate_connection(self) -> bool:
        # Validate OAuth token
        headers = {"Authorization": f"Bearer {self.credentials['access_token']}"}
        # Make API call to validate token
        pass
    
    async def refresh_token(self):
        # Implement token refresh logic
        pass
```

### Rate Limiting

Handle rate limits gracefully:

```python
async def fetch_content(self, since: Optional[datetime] = None) -> List[SourceContent]:
    try:
        # Fetch content
        pass
    except RateLimitError as e:
        await self.handle_rate_limit(retry_after=e.retry_after)
        # Retry or schedule for later
```

### Webhooks

For push-based sources:

```python
class WebhookConnector(BaseSourceConnector):
    def get_webhook_url(self) -> str:
        """Return webhook URL for this source"""
        return f"{BACKEND_URL}/api/webhooks/{self.source_id}"
    
    async def handle_webhook(self, payload: Dict[str, Any]) -> SourceContent:
        """Process incoming webhook payload"""
        return self.transform_content(payload)
```

## Testing Your Connector

Create tests in `backend/tests/test_sources/`:

```python
import pytest
from app.services.sources.substack_connector import SubstackConnector

@pytest.mark.asyncio
async def test_substack_connector():
    connector = SubstackConnector(
        source_id="test-123",
        config={"publication_url": "https://example.substack.com"}
    )
    
    # Test validation
    is_valid = await connector.validate_connection()
    assert is_valid
    
    # Test fetching content
    contents = await connector.fetch_content()
    assert len(contents) > 0
    assert contents[0].title
    assert contents[0].content
```

## Best Practices

1. **Error Handling**: Always handle API errors gracefully
2. **Rate Limiting**: Respect API rate limits and implement backoff
3. **Caching**: Cache responses when possible to reduce API calls
4. **Delta Crawls**: Use the `since` parameter to fetch only new content
5. **Metadata**: Store useful metadata for trend detection
6. **Validation**: Validate configuration and credentials before crawling
7. **Logging**: Log errors and important events for debugging
8. **Documentation**: Document required config and credentials

## Configuration Examples

### RSS-based Source (Simple)
```json
{
  "source_type": "substack",
  "name": "My Favorite Newsletter",
  "config": {
    "publication_url": "https://example.substack.com"
  }
}
```

### API-based Source (Complex)
```json
{
  "source_type": "linkedin",
  "name": "My LinkedIn Feed",
  "config": {
    "username": "johndoe",
    "fetch_comments": true,
    "max_posts": 50
  },
  "credentials": {
    "access_token": "...",
    "refresh_token": "...",
    "expires_at": "2024-12-31T23:59:59Z"
  }
}
```

## Troubleshooting

### Connector Not Found
- Ensure the connector is imported in `__init__.py`
- Check that `SourceRegistry.register()` is called
- Verify the source_type string matches

### Connection Validation Fails
- Check API credentials are correct
- Verify network connectivity
- Check API endpoint URLs
- Review API documentation for changes

### No Content Fetched
- Verify the source has recent content
- Check the `since` parameter isn't too restrictive
- Review API response format
- Check for rate limiting

## Resources

- **BaseSourceConnector**: `backend/app/services/sources/base.py`
- **RSS Example**: `backend/app/services/sources/rss_connector.py`
- **Database Schema**: `backend/database_schema.sql`
- **API Schemas**: `backend/app/schemas/source.py`

## Contributing

When adding a new source type:
1. Create the connector class
2. Write tests
3. Update documentation
4. Submit a pull request
5. Include example configuration

---

**Need Help?**
- Check existing connectors for examples
- Review the BaseSourceConnector documentation
- Ask in the developer Discord/Slack
