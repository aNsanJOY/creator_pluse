# Extensible Source System

CreatorPulse uses a plugin-based architecture for source connectors, making it easy to add new content sources without modifying core code.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Adding a New Source Type](#adding-a-new-source-type)
- [Available Connectors](#available-connectors)
- [Webhook Support](#webhook-support)
- [Best Practices](#best-practices)
- [Testing](#testing)

## Architecture Overview

### Components

1. **BaseSourceConnector**: Abstract base class that all connectors inherit from
2. **SourceRegistry**: Central registry that manages all available source types
3. **SourceContent**: Standard data model for content from any source
4. **CrawlerService**: Orchestrates content fetching from all sources

### How It Works

```
User adds source → Source stored in DB → Crawler fetches content → Content stored in cache
                                ↓
                        SourceRegistry.get_connector(type)
                                ↓
                        Specific connector (RSS, Twitter, etc.)
```

## Adding a New Source Type

### Step 1: Create Connector File

Create a new file in `backend/app/services/sources/` named `{source_type}_connector.py`:

```python
"""
MySource Connector - Description of what this connector does
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from .base import BaseSourceConnector, SourceContent, SourceRegistry


class MySourceConnector(BaseSourceConnector):
    """
    Connector for MySource.
    
    Configuration:
    - config_field_1: Description
    - config_field_2: Description
    
    Credentials:
    - api_key: API key for authentication
    """
    
    def get_source_type(self) -> str:
        """Return the source type identifier"""
        return "mysource"
    
    def get_required_credentials(self) -> List[str]:
        """List required credential fields"""
        return ["api_key"]
    
    def get_required_config(self) -> List[str]:
        """List required configuration fields"""
        return ["config_field_1"]
    
    async def validate_connection(self) -> bool:
        """
        Validate that the source connection is working.
        Test API credentials, check feed accessibility, etc.
        """
        try:
            # Test connection logic here
            api_key = self.credentials.get("api_key")
            if not api_key:
                return False
            
            # Make test API call
            # Return True if successful, False otherwise
            return True
        except Exception:
            return False
    
    async def fetch_content(self, since: Optional[datetime] = None) -> List[SourceContent]:
        """
        Fetch content from the source.
        
        Args:
            since: Only fetch content published after this timestamp (delta crawl)
        
        Returns:
            List of SourceContent objects
        """
        contents = []
        
        # Fetch data from your source
        # Parse and transform into SourceContent objects
        
        for item in fetched_items:
            # Skip items older than 'since' if provided
            if since and item.published_at and item.published_at < since:
                continue
            
            content = SourceContent(
                title=item.title,
                content=item.content,
                url=item.url,
                published_at=item.published_at,
                metadata={
                    "author": item.author,
                    "tags": item.tags,
                    "source": "mysource"
                }
            )
            contents.append(content)
        
        return contents


# Register the connector
SourceRegistry.register('mysource', MySourceConnector)
```

### Step 2: Register in __init__.py

Add your connector to `backend/app/services/sources/__init__.py`:

```python
# Import your connector
try:
    from app.services.sources.mysource_connector import MySourceConnector
    _mysource_available = True
except (ImportError, ModuleNotFoundError) as e:
    print(f"Warning: MySource connector not available: {e}")
    MySourceConnector = None
    _mysource_available = False

# Add to __all__ exports
if _mysource_available:
    __all__.append("MySourceConnector")
```

### Step 3: Update Source Type Enum (Optional)

If you want to add your source type to the enum, update `backend/app/models/source.py`:

```python
class SourceType(str, Enum):
    # ... existing types
    MYSOURCE = "mysource"
```

**Note**: This is optional since the system accepts any string as a source type.

### Step 4: Test Your Connector

Create tests in `backend/tests/test_sources/test_mysource_connector.py`:

```python
import pytest
from app.services.sources.mysource_connector import MySourceConnector

@pytest.mark.asyncio
async def test_mysource_validation():
    connector = MySourceConnector(
        source_id="test",
        config={"config_field_1": "value"},
        credentials={"api_key": "test_key"}
    )
    
    # Test validation
    is_valid = await connector.validate_connection()
    assert is_valid

@pytest.mark.asyncio
async def test_mysource_fetch():
    connector = MySourceConnector(
        source_id="test",
        config={"config_field_1": "value"},
        credentials={"api_key": "test_key"}
    )
    
    # Test content fetching
    contents = await connector.fetch_content()
    assert len(contents) > 0
    assert contents[0].title is not None
```

## Available Connectors

### Built-in Connectors

#### RSS Feed
- **Type**: `rss`
- **Config**: `feed_url`
- **Credentials**: None
- **Use Case**: Any RSS/Atom feed

#### Twitter/X
- **Type**: `twitter`
- **Config**: `username` or `list_id`
- **Credentials**: `access_token`, `access_token_secret`
- **Use Case**: Twitter timelines, lists

#### YouTube
- **Type**: `youtube`
- **Config**: `channel_id` or `playlist_id`
- **Credentials**: `api_key`
- **Use Case**: YouTube channels, playlists

#### Substack
- **Type**: `substack`
- **Config**: `publication_url`
- **Credentials**: None
- **Use Case**: Substack newsletters

#### Medium
- **Type**: `medium`
- **Config**: `feed_type` (user/publication/tag), `identifier`
- **Credentials**: None
- **Use Case**: Medium articles

#### LinkedIn
- **Type**: `linkedin`
- **Config**: `profile_type` (personal/company), `profile_id`
- **Credentials**: `access_token`
- **Use Case**: LinkedIn posts

## Webhook Support

For sources that support push notifications, you can use webhooks instead of polling.

### Setting Up Webhooks

1. **Configure Source with Webhook Settings**:

```json
{
  "webhook_enabled": true,
  "webhook_secret": "your-secret-key",
  "webhook_parser": "substack",
  "signature_header": "X-Webhook-Signature",
  "signature_algorithm": "sha256"
}
```

2. **Get Webhook URL**:

```bash
GET /api/webhooks/{source_id}/info
```

3. **Configure External Service**:

Point the external service's webhook to:
```
POST https://your-domain.com/api/webhooks/generic/{source_id}
```

### Webhook Parsers

Available parsers:
- `generic`: Standard format (title, content, url, published_at, metadata)
- `substack`: Substack webhook format
- `medium`: Medium webhook format (via third-party services)

### Creating Custom Webhook Parser

Add your parser to `backend/app/api/routes/webhooks.py`:

```python
def parse_mysource_webhook(payload: dict) -> SourceContent:
    """Parse MySource webhook payload"""
    return SourceContent(
        title=payload.get("title"),
        content=payload.get("body"),
        url=payload.get("link"),
        published_at=datetime.fromisoformat(payload["date"]),
        metadata={"source": "mysource"}
    )

# Update parse_webhook_payload function
def parse_webhook_payload(payload: dict, parser_type: str):
    if parser_type == "mysource":
        return parse_mysource_webhook(payload)
    # ... other parsers
```

## Best Practices

### 1. Error Handling

Always wrap API calls in try-except blocks:

```python
async def fetch_content(self, since: Optional[datetime] = None):
    try:
        # API call
        response = await self._make_api_call()
        return self._parse_response(response)
    except Exception as e:
        logger.error(f"Error fetching content: {e}")
        return []
```

### 2. Rate Limiting

Respect API rate limits:

```python
async def handle_rate_limit(self, retry_after: Optional[int] = None):
    import asyncio
    wait_time = retry_after or 60
    await asyncio.sleep(wait_time)
```

### 3. Delta Crawls

Always support the `since` parameter for incremental fetching:

```python
async def fetch_content(self, since: Optional[datetime] = None):
    # Only fetch content newer than 'since'
    if since and item.published_at < since:
        continue
```

### 4. Rich Metadata

Include rich metadata for better trend detection:

```python
metadata = {
    "author": "John Doe",
    "tags": ["tech", "ai"],
    "engagement": {
        "likes": 100,
        "shares": 50,
        "comments": 25
    },
    "source": "mysource"
}
```

### 5. Content Deduplication

Check for existing content before storing:

```python
# The crawler service handles this automatically
# by checking URL uniqueness
```

### 6. Logging

Use proper logging for debugging:

```python
import logging
logger = logging.getLogger(__name__)

logger.info(f"Fetching content from {source_type}")
logger.error(f"Error: {e}")
logger.debug(f"Parsed {len(contents)} items")
```

## Testing

### Unit Tests

Test each method independently:

```python
@pytest.mark.asyncio
async def test_validate_connection():
    connector = MySourceConnector(...)
    assert await connector.validate_connection()

@pytest.mark.asyncio
async def test_fetch_content():
    connector = MySourceConnector(...)
    contents = await connector.fetch_content()
    assert len(contents) > 0

@pytest.mark.asyncio
async def test_delta_crawl():
    connector = MySourceConnector(...)
    since = datetime.now() - timedelta(days=1)
    contents = await connector.fetch_content(since=since)
    # Verify all contents are newer than 'since'
```

### Integration Tests

Test with the crawler service:

```python
@pytest.mark.asyncio
async def test_crawler_integration():
    from app.services.crawler import CrawlerService
    
    crawler = CrawlerService(supabase)
    result = await crawler.crawl_source(source_id)
    
    assert result["success"]
    assert result["items_fetched"] > 0
```

### Manual Testing

1. Add source via API:
```bash
POST /api/sources
{
  "source_type": "mysource",
  "name": "My Test Source",
  "config": {"config_field_1": "value"},
  "credentials": {"api_key": "test_key"}
}
```

2. Trigger crawl:
```bash
POST /api/sources/{source_id}/crawl
```

3. Check results:
```bash
GET /api/sources/{source_id}/status
```

## Examples

### Example 1: Simple RSS-like Source

```python
class SimpleFeedConnector(BaseSourceConnector):
    def get_source_type(self) -> str:
        return "simplefeed"
    
    def get_required_credentials(self) -> List[str]:
        return []
    
    def get_required_config(self) -> List[str]:
        return ["feed_url"]
    
    async def validate_connection(self) -> bool:
        feed_url = self.config.get("feed_url")
        return bool(feed_url)
    
    async def fetch_content(self, since: Optional[datetime] = None):
        # Use feedparser for RSS-like feeds
        import feedparser
        feed = feedparser.parse(self.config["feed_url"])
        
        contents = []
        for entry in feed.entries:
            contents.append(SourceContent(
                title=entry.title,
                content=entry.summary,
                url=entry.link,
                published_at=datetime(*entry.published_parsed[:6]),
                metadata={"author": entry.get("author", "")}
            ))
        return contents

SourceRegistry.register('simplefeed', SimpleFeedConnector)
```

### Example 2: API-based Source

```python
class APISourceConnector(BaseSourceConnector):
    API_BASE = "https://api.example.com/v1"
    
    def get_source_type(self) -> str:
        return "apisource"
    
    def get_required_credentials(self) -> List[str]:
        return ["api_key"]
    
    def get_required_config(self) -> List[str]:
        return ["user_id"]
    
    async def validate_connection(self) -> bool:
        headers = {"Authorization": f"Bearer {self.credentials['api_key']}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.API_BASE}/me", headers=headers) as resp:
                return resp.status == 200
    
    async def fetch_content(self, since: Optional[datetime] = None):
        headers = {"Authorization": f"Bearer {self.credentials['api_key']}"}
        params = {"user_id": self.config["user_id"], "limit": 50}
        
        if since:
            params["since"] = since.isoformat()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.API_BASE}/posts",
                headers=headers,
                params=params
            ) as resp:
                data = await resp.json()
                
                contents = []
                for item in data["posts"]:
                    contents.append(SourceContent(
                        title=item["title"],
                        content=item["body"],
                        url=item["url"],
                        published_at=datetime.fromisoformat(item["created_at"]),
                        metadata={"author": item["author"]}
                    ))
                return contents

SourceRegistry.register('apisource', APISourceConnector)
```

## Troubleshooting

### Connector Not Registered

**Problem**: `Unsupported source type: mysource`

**Solution**: 
1. Check that you called `SourceRegistry.register()` at the end of your connector file
2. Verify the connector is imported in `__init__.py`
3. Restart the FastAPI server

### Validation Fails

**Problem**: Source status shows `ERROR` after creation

**Solution**:
1. Check `validate_connection()` implementation
2. Verify credentials are correct
3. Check API endpoint accessibility
4. Review logs for specific error messages

### No Content Fetched

**Problem**: Crawl succeeds but `items_fetched: 0`

**Solution**:
1. Check if `fetch_content()` returns empty list
2. Verify the `since` parameter isn't filtering all content
3. Check API response format
4. Add debug logging to see what's being fetched

### Import Errors

**Problem**: `ModuleNotFoundError` when importing connector

**Solution**:
1. Add dependencies to `requirements.txt`
2. Use conditional imports in `__init__.py`
3. Install missing packages: `pip install -r requirements.txt`

## Additional Resources

- [ADDING_NEW_SOURCES.md](./ADDING_NEW_SOURCES.md) - Quick reference guide
- [API_SOURCES.md](./API_SOURCES.md) - API integration examples
- [Source Connectors README](../backend/app/services/sources/README.md) - Technical details
- [BaseSourceConnector API](../backend/app/services/sources/base.py) - Base class documentation

## Contributing

When contributing a new connector:

1. Follow the naming convention: `{source_type}_connector.py`
2. Include comprehensive docstrings
3. Add unit tests
4. Update this documentation
5. Add example configuration to README
6. Test with real data before submitting PR
