# Source Connectors

This directory contains source connector implementations for CreatorPulse.

## Available Connectors

### Built-in Connectors
- **RSS** (`rss_connector.py`) - Generic RSS feed parser
- **Twitter** (`twitter_connector.py`) - Twitter/X API integration
- **YouTube** (`youtube_connector.py`) - YouTube Data API integration
- **Substack** (`substack_connector.py`) - Substack newsletter aggregation
- **Medium** (`medium_connector.py`) - Medium publication feeds
- **LinkedIn** (`linkedin_connector.py`) - LinkedIn posts and articles

### Planned Connectors
- **Podcast** - Podcast RSS feeds with audio transcription
- **Newsletter** - Generic newsletter aggregation
- **GitHub** - GitHub repository activity
- **Reddit** - Reddit posts and comments
- **Hacker News** - Hacker News stories and comments

## Architecture

All connectors inherit from `BaseSourceConnector` which provides:
- Standard interface for all source types
- Content fetching and validation
- Rate limiting handling
- Credential management

## Adding a New Connector

See [ADDING_NEW_SOURCES.md](../../../docs/ADDING_NEW_SOURCES.md) for detailed instructions.

Quick steps:
1. Create new file: `{source_type}_connector.py`
2. Inherit from `BaseSourceConnector`
3. Implement required methods
4. Register with `SourceRegistry.register()`
5. Import in `__init__.py`

## Example Usage

```python
from app.services.sources.base import SourceRegistry
from app.services.sources.rss_connector import RSSConnector

# Get connector class
ConnectorClass = SourceRegistry.get_connector('rss')

# Create instance
connector = ConnectorClass(
    source_id="123",
    config={"feed_url": "https://example.com/feed"},
    credentials={}
)

# Validate connection
is_valid = await connector.validate_connection()

# Fetch content
contents = await connector.fetch_content()
```

## Registry

The `SourceRegistry` maintains a mapping of source types to connector classes:

```python
# Check if source type is supported
SourceRegistry.is_supported('rss')  # True

# Get all supported types
SourceRegistry.get_all_source_types()  # ['rss', 'twitter', ...]

# Get connector class
ConnectorClass = SourceRegistry.get_connector('rss')
```

## Testing

Each connector should have corresponding tests in `backend/tests/test_sources/`.

Example:
```python
@pytest.mark.asyncio
async def test_rss_connector():
    connector = RSSConnector(
        source_id="test",
        config={"feed_url": "https://example.com/feed"}
    )
    assert await connector.validate_connection()
    contents = await connector.fetch_content()
    assert len(contents) > 0
```

## Best Practices

1. **Error Handling**: Catch and log all exceptions
2. **Rate Limiting**: Respect API limits
3. **Delta Crawls**: Support `since` parameter for incremental fetching
4. **Validation**: Validate config and credentials before use
5. **Metadata**: Include rich metadata for trend detection
6. **Documentation**: Document required config fields

## Source Type Naming

Use lowercase, descriptive names:
- ✅ `twitter`, `youtube`, `rss`, `substack`
- ❌ `Twitter`, `YOUTUBE`, `rss-feed`

## Configuration Schema

Each connector defines its own config schema:

```python
def get_required_config(self) -> List[str]:
    return ["feed_url", "polling_interval"]

def get_required_credentials(self) -> List[str]:
    return ["api_key", "api_secret"]
```

## Content Format

All connectors return `SourceContent` objects:

```python
SourceContent(
    title="Article Title",
    content="Full article content...",
    url="https://example.com/article",
    published_at=datetime.now(),
    metadata={
        "author": "John Doe",
        "tags": ["tech", "ai"],
        "engagement": {"likes": 100, "shares": 50}
    }
)
```

## Webhook Support

The system now supports webhooks for push-based sources. See the [Webhooks API](../../api/routes/webhooks.py) for implementation details.

Webhook endpoint: `POST /api/webhooks/generic/{source_id}`

Supported webhook parsers:
- `generic` - Standard format
- `substack` - Substack webhook format
- `medium` - Medium webhook format (via third-party services)

## Future Enhancements

- [x] Webhook support for push-based sources
- [ ] Automatic credential refresh (OAuth)
- [ ] Parallel fetching for multiple sources
- [ ] Content deduplication
- [ ] Source health monitoring
- [ ] Automatic retry with exponential backoff
- [ ] Source-specific rate limit tracking
- [ ] Content quality scoring
