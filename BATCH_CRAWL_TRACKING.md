# Batch Crawl Tracking Implementation

## Overview
Implemented a comprehensive batch crawl tracking system that records when all sources for a user are crawled together, separate from individual source crawl tracking.

## Changes Made

### 1. Database Migration (`004_user_crawl_schedule.sql`)

Created new table `user_crawl_schedule` with the following fields:

- **id**: UUID primary key
- **user_id**: Foreign key to users table (unique)
- **last_batch_crawl_at**: Timestamp of last completed batch crawl
- **next_scheduled_crawl_at**: Timestamp of next scheduled batch crawl
- **crawl_frequency_hours**: How often to crawl (default: 24 hours)
- **is_crawling**: Boolean flag indicating if batch crawl is in progress
- **last_crawl_duration_seconds**: Duration of last batch crawl
- **sources_crawled_count**: Number of sources successfully crawled in last batch
- **sources_failed_count**: Number of sources that failed in last batch
- **created_at**: Record creation timestamp
- **updated_at**: Record update timestamp (auto-updated via trigger)

**Features:**
- Unique constraint on user_id (one schedule per user)
- Indexes on user_id and next_scheduled_crawl_at for performance
- Auto-update trigger for updated_at timestamp
- Default records created for existing users

### 2. Crawl Orchestrator Updates (`crawl_orchestrator.py`)

**New Methods:**

#### `_start_batch_crawl(user_id)`
- Marks batch crawl as started for a user
- Sets `is_crawling = True`
- Creates schedule record if it doesn't exist

#### `_complete_batch_crawl(user_id, sources_crawled, sources_failed, duration_seconds)`
- Marks batch crawl as completed
- Records completion timestamp
- Calculates and sets next scheduled crawl time (based on frequency)
- Sets `is_crawling = False`
- Records statistics (sources crawled/failed, duration)

**Modified Method:**

#### `crawl_all_sources()`
- Now calls `_start_batch_crawl()` before crawling user's sources
- Tracks per-user success/failure counts
- Calls `_complete_batch_crawl()` after completing all sources for a user
- Records batch-level metrics

### 3. API Endpoint Updates (`routes/crawl.py`)

#### `GET /api/crawl/status`

**Enhanced Response:**
```json
{
  "sources": [...],  // Individual source details
  "total": 5,
  "active": 4,
  "error": 1,
  "last_batch_crawl_at": "2025-10-16T08:30:00Z",
  "next_scheduled_crawl_at": "2025-10-17T08:30:00Z",
  "is_crawling": false,
  "last_crawl_duration_seconds": 45,
  "sources_crawled_count": 4,
  "sources_failed_count": 1
}
```

**New Fields:**
- `last_batch_crawl_at`: When all sources were last crawled together
- `next_scheduled_crawl_at`: When next batch crawl is scheduled
- `is_crawling`: Whether a batch crawl is currently in progress
- `last_crawl_duration_seconds`: How long the last batch crawl took
- `sources_crawled_count`: Success count from last batch
- `sources_failed_count`: Failure count from last batch

**Behavior:**
- Auto-creates schedule record if it doesn't exist for the user
- Returns batch schedule data along with individual source details

### 4. Frontend Dashboard Updates (`Dashboard.tsx`)

**Updated Interface:**
```typescript
interface CrawlStatus {
  sources: Array<{...}>;
  total: number;
  active: number;
  error: number;
  last_batch_crawl_at: string | null;
  next_scheduled_crawl_at: string | null;
  is_crawling: boolean;
  last_crawl_duration_seconds: number | null;
  sources_crawled_count: number;
  sources_failed_count: number;
}
```

**Updated Helper Functions:**
- `getLastCrawledTime()`: Returns `last_batch_crawl_at` from schedule
- `getNextScheduledTime()`: Returns `next_scheduled_crawl_at` from schedule

**UI Enhancements:**

1. **Crawl Button:**
   - Disabled when `is_crawling` is true
   - Shows "Crawling..." state with spinner
   - Shows "Crawl All Now" when idle

2. **Status Display:**
   - "All Sources Last Crawled" - shows batch crawl time
   - "Next All Sources Crawl" - shows next scheduled time
   - Progress indicator when batch crawl is active

3. **Statistics Panel:**
   - Total sources count
   - Active sources count
   - Error sources count (if any)
   - Last crawl duration (if available)

## Data Flow

### Batch Crawl Lifecycle

1. **Trigger** (Manual or Scheduled)
   ```
   POST /api/crawl/trigger
   ```

2. **Start Batch**
   ```
   crawl_orchestrator._start_batch_crawl(user_id)
   → Sets is_crawling = True
   ```

3. **Crawl Sources**
   ```
   For each source:
     - Crawl content
     - Update individual source.last_crawled_at
     - Track success/failure
   ```

4. **Complete Batch**
   ```
   crawl_orchestrator._complete_batch_crawl(user_id, ...)
   → Sets last_batch_crawl_at = NOW
   → Sets next_scheduled_crawl_at = NOW + frequency_hours
   → Sets is_crawling = False
   → Records statistics
   ```

5. **Frontend Refresh**
   ```
   GET /api/crawl/status
   → Returns updated batch schedule
   → Dashboard displays new times
   ```

## Benefits

### 1. **Clear Batch Tracking**
- Know exactly when ALL sources were last crawled together
- Separate from individual source crawl times

### 2. **Accurate Scheduling**
- Next crawl time calculated from actual batch completion
- Frequency configurable per user (default 24 hours)

### 3. **Progress Visibility**
- `is_crawling` flag shows when batch is in progress
- Prevents duplicate batch crawls
- UI shows real-time status

### 4. **Performance Metrics**
- Track batch crawl duration
- Monitor success/failure rates
- Identify performance issues

### 5. **Better UX**
- Users see when their content was last refreshed
- Know when next refresh will happen
- Clear feedback during crawl operations

## Migration Instructions

### 1. Run Database Migration
```bash
psql -h your-supabase-host -U postgres -d postgres \
  -f backend/database_migrations/004_user_crawl_schedule.sql
```

### 2. Restart Backend
```bash
cd backend
python -m uvicorn app.main:app --reload
```

### 3. Restart Frontend
```bash
cd frontend
npm run dev
```

### 4. Verify
- Navigate to dashboard
- Check "Content Crawl Status" card
- Trigger a manual crawl
- Verify times update correctly

## Testing Checklist

- [ ] Database migration runs successfully
- [ ] Schedule records created for existing users
- [ ] Manual crawl trigger updates batch schedule
- [ ] `is_crawling` flag toggles correctly
- [ ] Next crawl time calculated correctly (24h after completion)
- [ ] Dashboard displays batch crawl times
- [ ] Button disabled during crawl
- [ ] Statistics display correctly
- [ ] Individual source times still tracked separately
- [ ] Multiple users have separate schedules

## Future Enhancements

1. **Configurable Frequency**
   - Allow users to set custom crawl frequency
   - UI for adjusting schedule

2. **Crawl History**
   - Track historical batch crawls
   - Show crawl trends over time

3. **Smart Scheduling**
   - Adjust frequency based on content update patterns
   - Skip crawls if no new content expected

4. **Notifications**
   - Email when batch crawl completes
   - Alert on crawl failures

5. **Batch Crawl Logs**
   - Detailed logs for each batch crawl
   - Per-batch success/failure breakdown

## Troubleshooting

### Issue: Times not updating
**Solution:** Check that crawl orchestrator is calling `_start_batch_crawl()` and `_complete_batch_crawl()`

### Issue: `is_crawling` stuck as true
**Solution:** Manually reset in database:
```sql
UPDATE user_crawl_schedule 
SET is_crawling = false 
WHERE user_id = 'your-user-id';
```

### Issue: Schedule record not created
**Solution:** Endpoint auto-creates on first access, or manually:
```sql
INSERT INTO user_crawl_schedule (user_id, crawl_frequency_hours)
VALUES ('your-user-id', 24);
```

## Summary

The batch crawl tracking system provides:
- ✅ Separate tracking for batch vs individual crawls
- ✅ Accurate "last crawled" and "next scheduled" times
- ✅ Real-time crawl progress indication
- ✅ Performance metrics and statistics
- ✅ Better user experience with clear status display

This implementation ensures users always know when their content was last refreshed and when the next refresh will occur.
