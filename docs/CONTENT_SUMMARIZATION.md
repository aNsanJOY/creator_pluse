## Content Summarization System

## Overview

The Content Summarization system uses Groq LLM to generate structured, newsletter-friendly summaries of content from all connected sources. Summaries include titles, key points, and concise text optimized for newsletter readers.

## Features

- **AI-Powered Summarization**: Uses Groq LLM for intelligent content summarization
- **Multiple Summary Types**: Brief, standard, and detailed summaries
- **Structured Output**: Title, key points, summary text, topics, and sentiment
- **Batch Processing**: Summarize multiple items efficiently
- **Smart Caching**: Summaries are stored and reused to save API calls
- **Auto-Discovery**: Automatically find and summarize new content

## Summary Types

### Brief
- **Length**: 2-3 sentences
- **Key Points**: 3-5 highlights
- **Use Case**: Quick overviews, social media posts

### Standard (Default)
- **Length**: 3-5 sentences
- **Key Points**: 5-7 highlights
- **Use Case**: Newsletter sections, content curation

### Detailed
- **Length**: 5-8 sentences
- **Key Points**: 7-10 highlights
- **Use Case**: In-depth analysis, comprehensive coverage

## API Endpoints

### POST /api/content/summarize

Generate a summary for a single content item.

**Request Body:**
```json
{
  "content_id": "uuid",
  "summary_type": "standard",
  "force_regenerate": false
}
```

**Response:**
```json
{
  "success": true,
  "summary": {
    "id": "uuid",
    "content_id": "uuid",
    "title": "Clear, Engaging Title",
    "key_points": [
      "First key point or highlight",
      "Second key point",
      "Third key point"
    ],
    "summary": "Concise summary paragraph that captures the main ideas...",
    "metadata": {
      "topics": ["AI", "technology", "innovation"],
      "sentiment": "positive",
      "relevance_score": 0.85,
      "word_count": 42,
      "source_url": "https://example.com/article",
      "source_title": "Original Article Title"
    },
    "created_at": "2024-01-15T10:30:00Z"
  },
  "message": "Summary generated successfully"
}
```

### POST /api/content/summarize/batch

Generate summaries for multiple content items.

**Request Body:**
```json
{
  "content_ids": ["uuid1", "uuid2", "uuid3"],
  "summary_type": "standard"
}
```

**Response:**
```json
{
  "results": [
    {
      "content_id": "uuid1",
      "status": "success",
      "summary": {...}
    },
    {
      "content_id": "uuid2",
      "status": "failed",
      "error": "Content not found"
    }
  ],
  "total_requested": 3,
  "successful": 2,
  "failed": 1,
  "processing_time": "8.45s"
}
```

### POST /api/content/summarize/recent

Automatically summarize recent unsummarized content.

**Request Body:**
```json
{
  "days_back": 7,
  "limit": 20,
  "summary_type": "standard"
}
```

**Response:**
```json
{
  "results": [...],
  "total_requested": 15,
  "successful": 14,
  "failed": 1,
  "processing_time": "42.3s"
}
```

### GET /api/content/summaries

List summaries for specific content or recent summaries.

**Query Parameters:**
- `content_ids` (optional): Comma-separated list of content IDs
- `limit` (default: 50): Maximum summaries to return

**Response:**
```json
{
  "summaries": [...],
  "total": 25,
  "message": "Found 25 recent summaries"
}
```

### GET /api/content/summaries/{summary_id}

Get a specific summary by ID.

**Response:**
```json
{
  "id": "uuid",
  "content_id": "uuid",
  "title": "Summary Title",
  "key_points": [...],
  "summary": "Summary text...",
  "summary_type": "standard",
  "metadata": {...},
  "model_used": "openai/gpt-oss-20b",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### DELETE /api/content/summaries/{summary_id}

Delete a summary (can be regenerated later).

**Response:**
```json
{
  "success": true,
  "message": "Summary deleted successfully",
  "summary_id": "uuid"
}
```

### GET /api/content/content/{content_id}

Get content item with optional summary.

**Query Parameters:**
- `include_summary` (default: true): Include summary if available

**Response:**
```json
{
  "id": "uuid",
  "source_id": "uuid",
  "source_name": "TechCrunch",
  "source_type": "rss",
  "content_type": "rss_article",
  "title": "Original Article Title",
  "content": "Full article content...",
  "url": "https://example.com/article",
  "metadata": {...},
  "published_at": "2024-01-15T08:00:00Z",
  "created_at": "2024-01-15T09:00:00Z",
  "summary": {
    "id": "uuid",
    "title": "Summary Title",
    "key_points": [...],
    "summary": "Summary text...",
    "metadata": {...}
  }
}
```

## Usage Examples

### Python Client

```python
import requests

# Summarize a single content item
response = requests.post(
    "http://localhost:8000/api/content/summarize",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "content_id": "content-uuid",
        "summary_type": "standard"
    }
)

summary = response.json()["summary"]
print(f"Title: {summary['title']}")
print(f"Summary: {summary['summary']}")
print(f"Key Points: {summary['key_points']}")

# Batch summarize recent content
response = requests.post(
    "http://localhost:8000/api/content/summarize/recent",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "days_back": 7,
        "limit": 20,
        "summary_type": "brief"
    }
)

results = response.json()
print(f"Summarized {results['successful']} items in {results['processing_time']}")
```

### JavaScript/TypeScript

```typescript
const summarizeContent = async (contentId: string) => {
  const response = await fetch('/api/content/summarize', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      content_id: contentId,
      summary_type: 'standard',
      force_regenerate: false
    })
  });
  
  const data = await response.json();
  return data.summary;
};

// Get content with summary
const getContentWithSummary = async (contentId: string) => {
  const response = await fetch(
    `/api/content/content/${contentId}?include_summary=true`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  
  return await response.json();
};
```

## Database Schema

Summaries are stored in the `content_summaries` table:

```sql
CREATE TABLE content_summaries (
    id UUID PRIMARY KEY,
    content_id UUID REFERENCES source_content_cache(id),
    user_id UUID REFERENCES users(id),
    summary_type VARCHAR(50) DEFAULT 'standard',
    title TEXT,
    key_points JSONB,
    summary_text TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    model_used VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

## Workflow Integration

### Typical Workflow

1. **Content Crawling**: Sources are crawled and stored in `source_content_cache`
2. **Auto-Summarization**: New content is automatically summarized
3. **Trend Detection**: Summaries are used for trend analysis
4. **Draft Generation**: Summaries are included in newsletter drafts

### Automated Summarization

Set up a scheduled job to summarize new content:

```python
from app.services.content_summarizer import content_summarizer

async def daily_summarization_job():
    """Run daily to summarize new content"""
    users = get_active_users()
    
    for user in users:
        summaries = await content_summarizer.summarize_recent_content(
            user_id=user.id,
            days_back=1,  # Yesterday's content
            limit=50,
            summary_type="standard"
        )
        
        print(f"Summarized {len(summaries)} items for user {user.id}")
```

## Performance Considerations

### API Latency

- **Single Summary**: ~3-8 seconds (Groq API dependent)
- **Batch (10 items)**: ~30-80 seconds
- **Batch (50 items)**: ~2-4 minutes

### Optimization Tips

1. **Use Caching**: Summaries are automatically cached
2. **Batch Processing**: Use `/summarize/batch` or `/summarize/recent`
3. **Background Jobs**: Run summarization asynchronously
4. **Smart Limits**: Limit to 20-50 items per batch
5. **Check Existing**: Set `force_regenerate: false` to use cached summaries

### Rate Limits

- Groq API: Check your plan limits
- Recommendation: Batch process during off-peak hours
- Consider implementing queue system for large volumes

## Prompt Engineering

The summarization prompt is optimized for newsletter content:

```python
def _create_summary_prompt(content, summary_type):
    return f"""Summarize the following content for a newsletter reader.

TITLE: {title}
CONTENT: {text}

{length_instruction}

Focus on:
- What is the main idea or news?
- Why does it matter?
- What are the key takeaways?
- Keep it engaging and newsletter-friendly

Provide summary in JSON format with:
- title: Clear, engaging title
- key_points: Array of highlights
- summary: Concise paragraph
- topics: Related topics
- sentiment: positive/neutral/negative/mixed
- relevance_score: 0.0-1.0
"""
```

### Customizing Prompts

To adjust summarization style, edit `_create_summary_prompt()` in `content_summarizer.py`:

- Change tone/style instructions
- Adjust length requirements
- Add domain-specific guidance
- Modify output format

## Testing

### Unit Tests

```bash
cd backend
pytest tests/test_content_summarization.py -v
```

### Manual Testing

```bash
# Start server
python -m app.main

# Test summarization
curl -X POST http://localhost:8000/api/content/summarize \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": "content-uuid",
    "summary_type": "standard"
  }'
```

## Troubleshooting

### Summary Generation Fails

**Possible causes:**
- Content not found or inaccessible
- Groq API error or rate limit
- Content too short or malformed

**Solutions:**
- Verify content exists and user has access
- Check Groq API key and quota
- Ensure content has meaningful text

### Poor Summary Quality

**Solutions:**
- Try different summary types (brief/standard/detailed)
- Check if source content is complete
- Adjust prompt instructions
- Use `force_regenerate: true` to retry

### Slow Performance

**Solutions:**
- Use batch endpoints instead of individual calls
- Run summarization as background job
- Reduce batch size
- Check Groq API latency

## Best Practices

1. **Cache Aggressively**: Don't regenerate unless necessary
2. **Batch When Possible**: More efficient than individual calls
3. **Background Processing**: Don't block user requests
4. **Error Handling**: Gracefully handle API failures
5. **Monitor Costs**: Track Groq API usage
6. **Quality Checks**: Periodically review summary quality

## Future Enhancements

- [ ] Multi-language summarization
- [ ] Custom summary templates per user
- [ ] Summary quality scoring
- [ ] A/B testing different prompts
- [ ] Image/video content summarization
- [ ] Automatic summary updates when content changes
- [ ] Summary comparison and merging

## Related Documentation

- [Trend Detection](./TREND_DETECTION.md)
- [Scheduled Crawling](./SCHEDULED_CRAWLING.md)
- [Voice Analysis](./VOICE_ANALYSIS.md)
- [API Credentials Guide](./API_CREDENTIALS_GUIDE.md)
