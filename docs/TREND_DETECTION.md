# Trend Detection System

## Overview

The Trend Detection system analyzes content from all connected sources to identify trending topics and themes using Groq LLM. It employs an ensemble scoring algorithm that combines multiple signals to rank trends by relevance.

## Features

- **AI-Powered Topic Extraction**: Uses Groq LLM to identify topics and themes from content
- **Ensemble Scoring**: Combines frequency, recency, engagement, and relevance signals
- **Manual Override**: Allows users to manually promote or demote trends
- **Configurable Detection**: Adjustable time windows, score thresholds, and result limits
- **Persistent Storage**: Stores detected trends in database for historical analysis

## How It Works

### 1. Content Collection

The system fetches recent content from all active sources for a user:
- Default lookback period: 7 days
- Maximum content analyzed: 100 items
- Sources: RSS feeds, Twitter, YouTube, etc.

### 2. Topic Extraction

Using Groq LLM, the system:
- Analyzes content titles and snippets
- Identifies 10-15 main topics/themes
- Categorizes topics (technology, business, science, etc.)
- Assigns initial relevance scores

### 3. Ensemble Scoring

Each trend receives a composite score based on:

| Signal | Weight | Description |
|--------|--------|-------------|
| **Frequency** | 30% | How many content items mention this topic |
| **Recency** | 30% | How recent the content is (exponential decay) |
| **Engagement** | 20% | Metadata signals (likes, shares, etc.) |
| **Relevance** | 20% | LLM-assigned relevance score |

**Formula:**
```
ensemble_score = 0.3 × frequency + 0.3 × recency + 0.2 × engagement + 0.2 × relevance
```

### 4. Filtering & Ranking

- Trends below minimum score threshold are filtered out
- Remaining trends are sorted by score (highest first)
- Results are limited to requested maximum

## API Endpoints

### POST /api/trends/detect

Detect trending topics from user's content sources.

**Request Body:**
```json
{
  "days_back": 7,
  "min_score": 0.5,
  "max_trends": 10
}
```

**Response:**
```json
{
  "trends": [
    {
      "topic": "Artificial Intelligence Advances",
      "description": "Recent breakthroughs in AI and machine learning",
      "score": 0.85,
      "signals": {
        "frequency": 0.8,
        "recency": 0.9,
        "engagement": 0.5,
        "relevance": 0.9
      },
      "metadata": {
        "keywords": ["AI", "machine learning", "NLP"],
        "category": "technology",
        "content_count": 5,
        "content_ids": ["id1", "id2", "id3"]
      },
      "manual_override": false
    }
  ],
  "total_content_analyzed": 42,
  "detection_time": "3.45s",
  "message": null
}
```

### GET /api/trends/list

Get previously detected trends.

**Query Parameters:**
- `days_back` (default: 7): Days to look back
- `limit` (default: 20): Maximum trends to return

**Response:**
```json
{
  "trends": [...],
  "total": 15,
  "days_back": 7
}
```

### GET /api/trends/{trend_id}

Get a specific trend by ID.

**Response:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "topic": "Topic Name",
  "score": 0.85,
  "sources": {
    "description": "...",
    "signals": {...},
    "metadata": {...}
  },
  "detected_at": "2024-01-15T10:30:00Z",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### PUT /api/trends/{trend_id}/override

Update manual override flag for a trend.

**Request Body:**
```json
{
  "manual_override": true,
  "override_score": 0.95
}
```

**Response:**
```json
{
  "success": true,
  "message": "Trend override updated successfully (manually promoted)",
  "trend_id": "uuid"
}
```

### DELETE /api/trends/{trend_id}

Delete a trend (useful for removing false positives).

**Response:**
```json
{
  "success": true,
  "message": "Trend deleted successfully",
  "trend_id": "uuid"
}
```

## Usage Examples

### Python Client

```python
import requests

# Detect trends
response = requests.post(
    "http://localhost:8000/api/trends/detect",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "days_back": 7,
        "min_score": 0.6,
        "max_trends": 15
    }
)

trends = response.json()["trends"]
for trend in trends:
    print(f"{trend['topic']}: {trend['score']}")
```

### JavaScript/TypeScript

```typescript
const detectTrends = async () => {
  const response = await fetch('/api/trends/detect', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      days_back: 7,
      min_score: 0.5,
      max_trends: 10
    })
  });
  
  const data = await response.json();
  return data.trends;
};
```

## Configuration

### Adjusting Detection Parameters

**For more trends:**
- Increase `max_trends`
- Lower `min_score` threshold
- Increase `days_back` window

**For higher quality trends:**
- Increase `min_score` threshold
- Decrease `days_back` (focus on recent content)
- Reduce `max_trends` (top trends only)

### Scoring Weights

To adjust scoring weights, modify `_score_trends()` in `trend_detector.py`:

```python
ensemble_score = (
    0.3 * frequency_score +    # Adjust these weights
    0.3 * recency_score +      # to change scoring
    0.2 * engagement_score +   # behavior
    0.2 * relevance_score
)
```

## Database Schema

Trends are stored in the `trends` table:

```sql
CREATE TABLE trends (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    topic VARCHAR(500) NOT NULL,
    score FLOAT NOT NULL,
    sources JSONB,  -- Contains description, signals, metadata
    detected_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE
);
```

## Performance Considerations

### API Latency

- Topic extraction: ~5-15 seconds (depends on Groq API)
- Scoring: <1 second
- Total detection time: ~5-20 seconds

### Rate Limits

- Groq API: Check current limits in your plan
- Recommendation: Cache trends and run detection periodically (e.g., daily)

### Optimization Tips

1. **Limit content analyzed**: Default is 100 items, adjust if needed
2. **Use shorter lookback windows**: 3-7 days is usually sufficient
3. **Cache results**: Store trends and refresh periodically
4. **Batch processing**: Run detection for all users in background jobs

## Testing

### Unit Tests

```bash
cd backend
pytest tests/test_trend_detection.py -v
```

### Integration Tests (requires Groq API)

```bash
pytest tests/test_trend_detection.py -v -m integration
```

### Manual Testing

```bash
# Start the server
cd backend
python -m app.main

# Test detection endpoint
curl -X POST http://localhost:8000/api/trends/detect \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"days_back": 7, "min_score": 0.5, "max_trends": 10}'
```

## Troubleshooting

### No trends detected

**Possible causes:**
- No recent content in sources
- `min_score` threshold too high
- `days_back` window too short

**Solutions:**
- Check if sources have been crawled recently
- Lower `min_score` to 0.3-0.4
- Increase `days_back` to 14-30 days

### Low-quality trends (false positives)

**Solutions:**
- Increase `min_score` threshold
- Adjust scoring weights to emphasize frequency/recency
- Use manual override to demote irrelevant trends
- Delete false positive trends

### Slow detection

**Causes:**
- Large amount of content to analyze
- Groq API latency

**Solutions:**
- Reduce content limit in `_get_recent_content()`
- Use shorter lookback window
- Run detection as background job
- Cache results

## Future Enhancements

- [ ] Multi-language support
- [ ] Topic clustering and deduplication
- [ ] User feedback integration (learn from manual overrides)
- [ ] Trend momentum tracking (rising vs. declining)
- [ ] Category-specific trend detection
- [ ] Real-time trend updates via WebSocket
- [ ] Trend visualization and analytics

## Related Documentation

- [API Credentials Guide](./API_CREDENTIALS_GUIDE.md)
- [Scheduled Crawling](./SCHEDULED_CRAWLING.md)
- [Voice Analysis](./VOICE_ANALYSIS.md)
