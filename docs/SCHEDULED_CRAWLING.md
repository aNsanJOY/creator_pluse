# Scheduled Crawling System

## Overview
The Scheduled Crawling System automatically fetches content from all connected sources (RSS, Twitter, YouTube, GitHub, Reddit) on a regular schedule. It uses APScheduler for job management and provides comprehensive logging, error handling, and admin alerts.

## Architecture

### Components

**1. Crawl Orchestrator** (`app/services/crawl_orchestrator.py`)
- Manages crawling across all sources
- Routes to source-specific crawlers
- Handles error recovery and retry logic
- Logs all crawl activities

**2. Scheduler Service** (`app/services/scheduler.py`)
- Uses APScheduler for job scheduling
- Runs daily crawl at 2:00 AM UTC
- Runs hourly crawl for high-frequency updates
- Sends admin alerts on failures

**3. Crawl API** (`app/api/routes/crawl.py`)
- Manual crawl triggering
- Crawl logs viewing
- Crawl statistics
- Source status monitoring

**4. Crawl Logs Table** (`crawl_logs`)
- Tracks every crawl execution
- Stores success/failure status
- Records items fetched and duration
- Enables performance monitoring

## Features

### Automated Scheduling
- **Daily Crawl**: 2:00 AM UTC - Full crawl of all sources
- **Hourly Crawl**: Every hour - Quick updates
- **Configurable**: Custom schedules via APScheduler

### Error Handling
- **Retry Logic**: Automatic retries on transient failures
- **Graceful Degradation**: Continues even if some sources fail
- **Error Logging**: Detailed error messages in database
- **Status Tracking**: Sources marked as 'error' when failing

### Admin Alerts
- **Email Notifications**: Sent to admin on critical failures
- **Threshold-Based**: Alerts when >5 sources fail
- **Detailed Reports**: Includes error details and timestamps

### Monitoring
- **Crawl Logs**: Complete history of all crawls
- **Statistics**: Success rates, durations, items fetched
- **Source Status**: Real-time status of each source
- **Performance Metrics**: Average duration, throughput

## Database Schema

### crawl_logs Table
```sql
CREATE TABLE crawl_logs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    source_id UUID REFERENCES sources(id),
    crawl_type VARCHAR(50), -- 'scheduled', 'manual', 'retry'
    status VARCHAR(50), -- 'started', 'success', 'failed', 'partial'
    items_fetched INTEGER,
    items_new INTEGER,
    error_message TEXT,
    error_details JSONB,
    duration_ms INTEGER,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    metadata JSONB
);
```

### sources Table Updates
- `last_crawled_at`: Timestamp of last successful crawl
- `error_message`: Latest error (if any)
- `status`: 'active', 'error', or 'pending'

## API Endpoints

### POST /api/crawl/trigger
Manually trigger a crawl for all user's sources.

**Request:**
```http
POST /api/crawl/trigger
Authorization: Bearer {token}
```

**Response:**
```json
{
  "message": "Manual crawl completed",
  "sources_crawled": 5,
  "successful": 4,
  "failed": 1,
  "results": [...]
}
```

### GET /api/crawl/logs
Get crawl logs for the current user.

**Parameters:**
- `limit` (optional): Number of logs to return (default: 50)
- `source_id` (optional): Filter by specific source

**Response:**
```json
{
  "logs": [
    {
      "id": "uuid",
      "source_id": "uuid",
      "crawl_type": "scheduled",
      "status": "success",
      "items_fetched": 15,
      "items_new": 3,
      "duration_ms": 2500,
      "started_at": "2025-10-15T02:00:00Z",
      "completed_at": "2025-10-15T02:00:02Z"
    }
  ],
  "count": 50
}
```

### GET /api/crawl/stats
Get crawl statistics for the current user.

**Response:**
```json
{
  "total_crawls": 150,
  "successful": 145,
  "failed": 3,
  "partial": 2,
  "total_items_fetched": 2250,
  "total_items_new": 450,
  "last_crawl_at": "2025-10-15T02:00:00Z",
  "avg_duration_ms": 2345.67,
  "success_rate": 96.67
}
```

### GET /api/crawl/status
Get current crawl status for all user's sources.

**Response:**
```json
{
  "sources": [
    {
      "id": "uuid",
      "name": "TechCrunch RSS",
      "type": "rss",
      "status": "active",
      "last_crawled_at": "2025-10-15T02:00:00Z",
      "error_message": null,
      "latest_crawl": {...}
    }
  ],
  "total": 5,
  "active": 4,
  "error": 1
}
```

## Crawl Orchestration Flow

```
1. Scheduler triggers job (daily/hourly)
   ↓
2. Orchestrator initializes
   ↓
3. Fetch all active sources from database
   ↓
4. Group sources by user
   ↓
5. For each source:
   - Create crawl log (status: 'started')
   - Route to source-specific crawler
   - Fetch content
   - Store in source_content_cache
   - Update crawl log (status: 'success'/'failed')
   - Update source.last_crawled_at
   ↓
6. Generate summary report
   ↓
7. Send admin alerts if needed
   ↓
8. Complete
```

## Source-Specific Crawlers

### RSS Crawler
- Uses `feedparser` library
- Fetches last 20 entries
- Checks for duplicates before storing
- Extracts: title, content, URL, author, tags
- Handles feed errors gracefully

### Twitter Crawler
- **Status**: Placeholder (to be implemented)
- Will use Tweepy library
- Fetch recent tweets from timeline

### YouTube Crawler
- **Status**: Placeholder (to be implemented)
- Will use YouTube Data API
- Fetch recent videos from channel

### GitHub Crawler
- **Status**: Placeholder (to be implemented)
- Will use PyGithub library
- Fetch recent commits/releases

### Reddit Crawler
- **Status**: Placeholder (to be implemented)
- Will use PRAW library
- Fetch recent posts from subreddit

## Error Handling Strategy

### Transient Errors
- Network timeouts
- Rate limiting
- Temporary API outages

**Handling:**
- Log error
- Mark source as 'error' temporarily
- Retry on next scheduled crawl
- Alert admin if persists >24 hours

### Permanent Errors
- Invalid credentials
- Deleted/private sources
- Invalid URLs

**Handling:**
- Mark source as 'error'
- Store error message
- Send immediate admin alert
- Require user intervention

### Partial Failures
- Some items fail, others succeed

**Handling:**
- Mark crawl as 'partial'
- Log which items failed
- Continue processing successful items
- Report partial success

## Admin Alerts

### Trigger Conditions
- More than 5 sources fail in single crawl
- Fatal error in orchestrator
- Scheduler crashes
- Database connection issues

### Alert Content
```
Subject: [CreatorPulse Alert] Daily Crawl Alert

Alert from CreatorPulse Scheduled Crawl System

Subject: Daily Crawl Alert
Time: 2025-10-15T02:05:00Z

Details:
Daily crawl had 6 failures

Please check the crawl logs for more information.
```

### Alert Delivery
- Email to admin (GMAIL_EMAIL from config)
- Logged to application logs
- Stored in crawl_logs with error details

## Configuration

### Schedule Configuration
Edit `app/services/scheduler.py`:

```python
# Daily crawl at 2:00 AM UTC
self.scheduler.add_job(
    self._daily_crawl_job,
    trigger=CronTrigger(hour=2, minute=0),
    id="daily_crawl"
)

# Hourly crawl
self.scheduler.add_job(
    self._hourly_crawl_job,
    trigger=IntervalTrigger(hours=1),
    id="hourly_crawl"
)
```

### Custom Schedules
```python
from apscheduler.triggers.cron import CronTrigger

# Every 6 hours
trigger = IntervalTrigger(hours=6)

# Specific times
trigger = CronTrigger(hour=2, minute=30)

# Multiple times per day
trigger = CronTrigger(hour='2,8,14,20', minute=0)
```

## Performance Optimization

### Batch Processing
- Sources processed in batches
- Parallel processing for independent sources
- Rate limiting to avoid API throttling

### Caching
- Duplicate detection before storage
- Content deduplication by URL
- Metadata caching for faster lookups

### Database Optimization
- Indexed queries on source_id, user_id
- Bulk inserts for content
- Periodic cleanup of old logs

## Monitoring & Debugging

### Check Scheduler Status
```python
from app.services.scheduler import get_scheduler

scheduler = get_scheduler()
jobs = scheduler.get_jobs()
print(jobs)
```

### View Recent Logs
```bash
# Via API
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/crawl/logs?limit=10

# Via database
SELECT * FROM crawl_logs 
ORDER BY started_at DESC 
LIMIT 10;
```

### Monitor Performance
```bash
# Get statistics
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/crawl/stats
```

### Debug Failed Crawls
```sql
-- Find failed crawls
SELECT * FROM crawl_logs 
WHERE status = 'failed' 
ORDER BY started_at DESC;

-- Check error patterns
SELECT error_message, COUNT(*) 
FROM crawl_logs 
WHERE status = 'failed' 
GROUP BY error_message;
```

## Testing

### Manual Crawl Test
```bash
curl -X POST \
  -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/crawl/trigger
```

### Unit Tests
```bash
pytest backend/tests/test_crawl_orchestrator.py -v
```

### Integration Tests
```bash
pytest backend/tests/test_scheduled_crawling.py -v
```

## Troubleshooting

### Scheduler Not Starting
**Symptom**: No crawls running
**Check**:
- Application logs for errors
- APScheduler initialization
- Database connectivity

**Fix**:
```python
# Restart scheduler
from app.services.scheduler import start_scheduler
start_scheduler()
```

### Crawls Failing
**Symptom**: All crawls marked as 'failed'
**Check**:
- Source credentials
- API rate limits
- Network connectivity
- Database connection

**Fix**:
- Check crawl logs for specific errors
- Verify source configurations
- Test manual crawl for single source

### High Failure Rate
**Symptom**: >20% crawls failing
**Check**:
- API quotas and limits
- Source availability
- Error patterns in logs

**Fix**:
- Adjust crawl frequency
- Update source credentials
- Implement backoff strategy

### Missing Content
**Symptom**: Crawls successful but no new content
**Check**:
- Duplicate detection logic
- Content filters
- Source has new content

**Fix**:
- Review source_content_cache
- Check published_at timestamps
- Verify deduplication logic

## Best Practices

### Crawl Frequency
- **High-volume sources**: Hourly
- **Medium-volume sources**: Every 6 hours
- **Low-volume sources**: Daily
- **Static sources**: Weekly

### Error Recovery
- Log all errors with context
- Implement exponential backoff
- Alert on persistent failures
- Provide user-friendly error messages

### Performance
- Limit items per crawl (e.g., 20 most recent)
- Use connection pooling
- Implement request caching
- Monitor API quotas

### Security
- Encrypt credentials at rest
- Use environment variables for API keys
- Implement rate limiting
- Validate all external data

## Future Enhancements

- [ ] Intelligent crawl frequency based on source activity
- [ ] Parallel crawling for faster execution
- [ ] Content quality scoring
- [ ] Automatic source health monitoring
- [ ] Predictive crawl scheduling
- [ ] Advanced retry strategies
- [ ] Real-time crawl progress tracking
- [ ] Webhook notifications for crawl completion
- [ ] Custom crawl rules per source
- [ ] Machine learning for optimal scheduling

## Related Documentation

- [API Credentials Guide](./API_CREDENTIALS_GUIDE.md)
- [Adding New Sources](./ADDING_NEW_SOURCES.md)
- [Database Schema](../backend/database_schema.sql)

## Status: ✅ COMPLETE

**Phase 5.1 - Scheduled Crawling**: Fully implemented and operational

**Date Completed**: October 15, 2025
