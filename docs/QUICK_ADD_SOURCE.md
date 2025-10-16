# Quick Guide: Adding a New Source Type

This is a condensed guide for quickly adding a new source connector to CreatorPulse.

## 5-Minute Setup

### 1. Create Connector File

Create `backend/app/services/sources/{source_name}_connector.py`:

```python
from typing import List, Optional
from datetime import datetime
from .base import BaseSourceConnector, SourceContent, SourceRegistry

class MySourceConnector(BaseSourceConnector):
    def get_source_type(self) -> str:
        return "mysource"
    
    def get_required_credentials(self) -> List[str]:
        return ["api_key"]  # or [] if no credentials needed
    
    def get_required_config(self) -> List[str]:
        return ["feed_url"]  # required config fields
    
    async def validate_connection(self) -> bool:
        # Test if connection works
        return True
    
    async def fetch_content(self, since: Optional[datetime] = None) -> List[SourceContent]:
        # Fetch and return content
        contents = []
        # ... your fetching logic ...
        return contents

# Register the connector
SourceRegistry.register('mysource', MySourceConnector)
```

### 2. Register in __init__.py

Add to `backend/app/services/sources/__init__.py`:

```python
try:
    from app.services.sources.mysource_connector import MySourceConnector
    _mysource_available = True
except (ImportError, ModuleNotFoundError) as e:
    print(f"Warning: MySource connector not available: {e}")
    MySourceConnector = None
    _mysource_available = False

# In __all__ section:
if _mysource_available:
    __all__.append("MySourceConnector")
```

### 3. Test It

```bash
# Add source via API
curl -X POST http://localhost:8000/api/sources \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "mysource",
    "name": "My Test Source",
    "config": {"feed_url": "https://example.com/feed"},
    "credentials": {"api_key": "your_key"}
  }'

# Trigger crawl
curl -X POST http://localhost:8000/api/sources/{source_id}/crawl \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Common Patterns

### RSS-like Feed

```python
import feedparser

async def fetch_content(self, since: Optional[datetime] = None):
    feed = feedparser.parse(self.config["feed_url"])
    contents = []
    
    for entry in feed.entries:
        published_at = datetime(*entry.published_parsed[:6])
        
        if since and published_at < since:
            continue
        
        contents.append(SourceContent(
            title=entry.title,
            content=entry.summary,
            url=entry.link,
            published_at=published_at,
            metadata={"author": entry.get("author", "")}
        ))
    
    return contents
```

### REST API

```python
import aiohttp

async def fetch_content(self, since: Optional[datetime] = None):
    headers = {"Authorization": f"Bearer {self.credentials['api_key']}"}
    params = {"limit": 50}
    
    if since:
        params["since"] = since.isoformat()
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.example.com/posts",
            headers=headers,
            params=params
        ) as resp:
            data = await resp.json()
            
            contents = []
            for item in data["items"]:
                contents.append(SourceContent(
                    title=item["title"],
                    content=item["body"],
                    url=item["url"],
                    published_at=datetime.fromisoformat(item["date"]),
                    metadata={"author": item["author"]}
                ))
            
            return contents
```

### Web Scraping

```python
import aiohttp
from bs4 import BeautifulSoup

async def fetch_content(self, since: Optional[datetime] = None):
    url = self.config["page_url"]
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            contents = []
            for article in soup.find_all('article'):
                title = article.find('h2').text
                content = article.find('div', class_='content').text
                link = article.find('a')['href']
                
                contents.append(SourceContent(
                    title=title,
                    content=content,
                    url=link,
                    published_at=datetime.now(),
                    metadata={"source": "webscrape"}
                ))
            
            return contents
```

## Webhook Support

To enable webhooks for your source:

### 1. Add Webhook Parser

In `backend/app/api/routes/webhooks.py`:

```python
def parse_mysource_webhook(payload: dict) -> SourceContent:
    return SourceContent(
        title=payload["title"],
        content=payload["content"],
        url=payload["url"],
        published_at=datetime.fromisoformat(payload["published_at"]),
        metadata={"source": "mysource"}
    )

# Update parse_webhook_payload:
def parse_webhook_payload(payload: dict, parser_type: str):
    if parser_type == "mysource":
        return parse_mysource_webhook(payload)
    # ... existing parsers
```

### 2. Configure Source

```json
{
  "source_type": "mysource",
  "name": "My Webhook Source",
  "config": {
    "webhook_enabled": true,
    "webhook_secret": "your-secret-key",
    "webhook_parser": "mysource",
    "signature_header": "X-Webhook-Signature",
    "signature_algorithm": "sha256"
  }
}
```

### 3. Get Webhook URL

```bash
GET /api/webhooks/{source_id}/info
```

## Checklist

- [ ] Created connector file
- [ ] Implemented all required methods
- [ ] Registered in `__init__.py`
- [ ] Added to `SourceType` enum (optional)
- [ ] Tested validation
- [ ] Tested content fetching
- [ ] Tested delta crawl (with `since` parameter)
- [ ] Added error handling
- [ ] Added logging
- [ ] Documented config/credentials requirements
- [ ] Created unit tests (optional but recommended)

## Troubleshooting

**Connector not found**: Restart FastAPI server after adding connector

**Validation fails**: Check credentials and API endpoint accessibility

**No content fetched**: Add debug logging to see what's being returned

**Import errors**: Install missing dependencies in `requirements.txt`

## Full Documentation

For complete details, see [EXTENSIBLE_SOURCES.md](./EXTENSIBLE_SOURCES.md)
