# RSS Integration Guide

This guide explains how to use the RSS feed integration in CreatorPulse.

## Overview

The RSS integration allows users to connect any RSS or Atom feed to CreatorPulse. The system automatically fetches and caches content from the feed, which can then be used for newsletter generation.

## Features

- ✅ Support for RSS 2.0, RSS 1.0, and Atom formats
- ✅ Automatic feed validation
- ✅ Delta crawling (fetch only new content)
- ✅ Background content fetching
- ✅ Metadata extraction (author, tags, dates)
- ✅ Error handling for malformed feeds

## API Endpoints

### 1. Add RSS Feed

**Endpoint:** `POST /api/sources/rss`

**Description:** Add a new RSS feed source.

**Request Body:**
```json
{
  "feed_url": "https://example.com/feed.xml",
  "name": "Optional Custom Name"
}
```

**Response:**
```json
{
  "source_id": "uuid",
  "name": "RSS - Feed Title",
  "feed_url": "https://example.com/feed.xml",
  "status": "active",
  "feed_title": "Example Feed",
  "feed_description": "Feed description",
  "entry_count": 25
}
```

**Example (curl):**
```bash
curl -X POST "http://localhost:8000/api/sources/rss" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "feed_url": "https://feeds.feedburner.com/TechCrunch/",
    "name": "TechCrunch"
  }'
```

### 2. Preview RSS Feed

**Endpoint:** `GET /api/sources/rss/{source_id}/preview`

**Description:** Preview the latest entries from an RSS feed without storing them.

**Response:**
```json
{
  "feed_title": "Example Feed",
  "feed_url": "https://example.com/feed.xml",
  "entry_count": 25,
  "entries": [
    {
      "title": "Article Title",
      "link": "https://example.com/article",
      "published_at": "2024-01-01T12:00:00",
      "summary": "Article summary..."
    }
  ]
}
```

### 3. Get RSS Stats

**Endpoint:** `GET /api/sources/rss/{source_id}/stats`

**Description:** Get statistics about an RSS feed source.

**Response:**
```json
{
  "source_id": "uuid",
  "name": "RSS - Feed Title",
  "feed_url": "https://example.com/feed.xml",
  "feed_title": "Example Feed",
  "feed_type": "rss20",
  "status": "active",
  "last_crawled_at": "2024-01-01T12:00:00",
  "cached_entries": 50,
  "current_entries": 25,
  "feed_updated": "2024-01-01T11:00:00"
}
```

### 4. Refresh RSS Feed

**Endpoint:** `POST /api/sources/rss/{source_id}/refresh`

**Description:** Manually trigger a refresh/crawl for an RSS feed.

**Response:**
```json
{
  "message": "RSS feed refresh started",
  "source_id": "uuid",
  "source_name": "RSS - Feed Title"
}
```

### 5. Disconnect RSS Feed

**Endpoint:** `DELETE /api/sources/rss/{source_id}`

**Description:** Remove an RSS feed source.

**Response:**
```json
{
  "message": "RSS feed disconnected successfully"
}
```

## Supported Feed Formats

### RSS 2.0
The most common RSS format. Example:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Example Feed</title>
    <link>https://example.com</link>
    <description>Feed description</description>
    <item>
      <title>Article Title</title>
      <link>https://example.com/article</link>
      <description>Article content</description>
      <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
      <author>author@example.com</author>
      <category>Technology</category>
    </item>
  </channel>
</rss>
```

### Atom
Modern feed format. Example:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Example Feed</title>
  <link href="https://example.com"/>
  <updated>2024-01-01T12:00:00Z</updated>
  <entry>
    <title>Article Title</title>
    <link href="https://example.com/article"/>
    <id>https://example.com/article</id>
    <updated>2024-01-01T12:00:00Z</updated>
    <summary>Article summary</summary>
    <content type="html">Article content</content>
    <author>
      <name>Author Name</name>
    </author>
  </entry>
</feed>
```

### RSS 1.0 (RDF)
Less common but still supported:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns="http://purl.org/rss/1.0/">
  <channel>
    <title>Example Feed</title>
    <link>https://example.com</link>
  </channel>
  <item>
    <title>Article Title</title>
    <link>https://example.com/article</link>
    <description>Article content</description>
  </item>
</rdf:RDF>
```

## Content Extraction

The RSS connector extracts the following information from each feed entry:

### Required Fields
- **Title:** Entry title (defaults to "Untitled" if missing)
- **URL:** Link to the full article
- **Content:** Full content or summary text

### Optional Fields
- **Published Date:** Publication timestamp (tries multiple date fields)
- **Author:** Entry author (tries multiple author fields)
- **Tags/Categories:** Associated tags or categories
- **Entry ID:** Unique identifier for the entry

### Metadata
Additional metadata stored with each entry:
- Feed title
- Feed type (RSS 2.0, Atom, etc.)
- Entry ID
- Update timestamp
- Media content indicator

## Delta Crawling

The RSS connector supports delta crawling, which means it only fetches new content since the last crawl:

1. **First Crawl:** Fetches all entries from the feed
2. **Subsequent Crawls:** Only fetches entries newer than the last crawl timestamp
3. **Duplicate Detection:** Prevents storing duplicate entries based on URL

This approach:
- Reduces bandwidth usage
- Improves crawl performance
- Prevents duplicate content in the cache

## Error Handling

The RSS integration handles various error scenarios:

### Invalid Feed URL
- Returns validation error during feed addition
- Provides clear error message

### Malformed XML
- Attempts to parse even if feed has minor errors
- Returns empty list if feed is completely invalid

### Network Errors
- Marks source as "error" status
- Stores error message for debugging
- Retries on next scheduled crawl

### Missing Fields
- Uses sensible defaults for missing fields
- Continues processing even if some fields are missing

## Background Crawling

RSS feeds are crawled automatically in the background:

1. **Initial Crawl:** Triggered immediately when feed is added
2. **Scheduled Crawls:** Run daily for all active RSS sources
3. **Manual Refresh:** Can be triggered via API endpoint

The crawler:
- Processes sources sequentially with delays to avoid rate limiting
- Updates source status after each crawl
- Stores new content in the cache table
- Handles errors gracefully without affecting other sources

## Best Practices

### Choosing Feeds
- Use feeds that update regularly (daily or weekly)
- Verify feed URL before adding
- Prefer feeds with full content over summary-only feeds

### Feed Management
- Remove inactive or broken feeds
- Monitor feed stats to ensure content is being fetched
- Use preview endpoint to verify feed content before adding

### Performance
- Avoid adding too many feeds from the same domain
- Use manual refresh sparingly (scheduled crawls are sufficient)
- Monitor cached entry count to ensure storage doesn't grow unbounded

## Common RSS Feed Sources

Popular platforms that provide RSS feeds:

- **Blogs:** WordPress, Medium, Substack (all have RSS)
- **News Sites:** Most news sites provide RSS feeds
- **Podcasts:** Podcast feeds are RSS-based
- **YouTube Channels:** `https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID`
- **Reddit:** `https://www.reddit.com/r/SUBREDDIT/.rss`
- **GitHub:** `https://github.com/USER.atom`

## Troubleshooting

### Feed Not Validating
- Check if the URL is accessible in a browser
- Verify the URL returns XML content
- Try the feed URL in an RSS reader to confirm it's valid

### No Content Being Fetched
- Check source status via `/api/sources/{source_id}/status`
- Review error message if status is "error"
- Verify feed has recent entries (some feeds may be inactive)

### Duplicate Content
- The system automatically prevents duplicates based on URL
- If duplicates appear, check if the feed is using different URLs for the same content

### Missing Content Fields
- Some feeds only provide summaries, not full content
- Check feed format - Atom feeds typically have more complete content
- Consider using the feed's website URL instead if content is insufficient

## Integration with Frontend

Example React code to add an RSS feed:

```typescript
import { useState } from 'react';
import { apiClient } from '@/lib/api';

function AddRSSFeed() {
  const [feedUrl, setFeedUrl] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await apiClient.post('/api/sources/rss', {
        feed_url: feedUrl
      });
      
      console.log('RSS feed added:', response.data);
      // Handle success (e.g., show notification, redirect)
    } catch (error) {
      console.error('Failed to add RSS feed:', error);
      // Handle error (e.g., show error message)
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="url"
        value={feedUrl}
        onChange={(e) => setFeedUrl(e.target.value)}
        placeholder="https://example.com/feed.xml"
        required
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Adding...' : 'Add RSS Feed'}
      </button>
    </form>
  );
}
```

## Next Steps

After setting up RSS integration:

1. **Test with Popular Feeds:** Add feeds from TechCrunch, GitHub, or other popular sources
2. **Monitor Crawl Performance:** Check logs to ensure feeds are being crawled successfully
3. **Integrate with Newsletter Generation:** Use cached RSS content in newsletter drafts
4. **Add Frontend UI:** Create user-friendly interface for managing RSS feeds

## Related Documentation

- [Adding New Sources](./ADDING_NEW_SOURCES.md)
- [API Sources Overview](./API_SOURCES.md)
- [External Services Setup](./EXTERNAL_SERVICES_SETUP.md)
