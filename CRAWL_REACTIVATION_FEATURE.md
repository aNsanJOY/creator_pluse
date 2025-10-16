# Source Reactivation Feature

## Overview
Added endpoints to reactivate failed/error sources from the React frontend, allowing users to easily recover from temporary failures.

## New Endpoints

### 1. Reactivate Single Source
**Endpoint**: `POST /api/crawl/reactivate/{source_id}`

**Description**: Reactivates a single failed source by changing its status from 'error' to 'active' and clearing the error message.

**Request**:
```bash
POST /api/crawl/reactivate/cea79559-7cd5-4d7f-99af-5023d1b1e4b0
Authorization: Bearer <token>
```

**Response**:
```json
{
  "message": "Source 'AI_Latest' reactivated successfully",
  "source_id": "cea79559-7cd5-4d7f-99af-5023d1b1e4b0",
  "previous_status": "error",
  "new_status": "active"
}
```

**Use Case**: User clicks "Retry" or "Reactivate" button on a failed source card in the UI.

---

### 2. Reactivate All Failed Sources
**Endpoint**: `POST /api/crawl/reactivate-all`

**Description**: Bulk reactivates all sources with 'error' status for the current user.

**Request**:
```bash
POST /api/crawl/reactivate-all
Authorization: Bearer <token>
```

**Response**:
```json
{
  "message": "Reactivated 4 source(s)",
  "reactivated_count": 4,
  "sources": [
    {
      "id": "cea79559-7cd5-4d7f-99af-5023d1b1e4b0",
      "name": "AI_Latest",
      "type": "rss"
    },
    {
      "id": "d20bbc25-5785-4f08-8b6e-13db1fe084f1",
      "name": "TechCrunch",
      "type": "rss"
    },
    ...
  ]
}
```

**Use Case**: User clicks "Reactivate All Failed Sources" button in the sources dashboard.

---

## Frontend Integration

### Source Card Component
Add a reactivation button to source cards when status is 'error':

```tsx
// In SourceCard.tsx or similar component
import { RefreshCw } from 'lucide-react'
import apiClient from '../services/api'

const handleReactivate = async (sourceId: string) => {
  try {
    const response = await apiClient.post(`/api/crawl/reactivate/${sourceId}`)
    // Show success message
    toast.success(response.data.message)
    // Refresh sources list
    fetchSources()
  } catch (error) {
    toast.error('Failed to reactivate source')
  }
}

// In the card render:
{source.status === 'error' && (
  <Button
    variant="outline"
    size="sm"
    onClick={() => handleReactivate(source.id)}
  >
    <RefreshCw className="h-4 w-4 mr-2" />
    Reactivate
  </Button>
)}
```

### Bulk Reactivation Button
Add to the sources page header:

```tsx
const handleReactivateAll = async () => {
  try {
    const response = await apiClient.post('/api/crawl/reactivate-all')
    toast.success(response.data.message)
    fetchSources()
  } catch (error) {
    toast.error('Failed to reactivate sources')
  }
}

// In the page header:
{errorSourcesCount > 0 && (
  <Button
    variant="secondary"
    onClick={handleReactivateAll}
  >
    <RefreshCw className="h-4 w-4 mr-2" />
    Reactivate All Failed ({errorSourcesCount})
  </Button>
)}
```

---

## Database Changes

### Source Status Values
The `sources` table has the following status values:
- `active` - Source is working normally
- `error` - Source has failed (can be reactivated)
- `pending` - Source is being set up

### What Reactivation Does
1. Changes `status` from `error` to `active`
2. Clears `error_message` field
3. Allows the source to be crawled again in the next scheduled run

---

## Error Handling

### Source Not Found (404)
```json
{
  "detail": "Source not found"
}
```

### Unauthorized (401)
```json
{
  "detail": "Not authenticated"
}
```

### Server Error (500)
```json
{
  "detail": "Failed to reactivate source: <error details>"
}
```

---

## Testing

### Test Single Reactivation
```bash
# 1. Get a source with error status
GET /api/sources

# 2. Reactivate it
POST /api/crawl/reactivate/{source_id}

# 3. Verify status changed
GET /api/sources/{source_id}
# Should show status: "active", error_message: null
```

### Test Bulk Reactivation
```bash
# 1. Get all error sources
GET /api/sources?status=error

# 2. Reactivate all
POST /api/crawl/reactivate-all

# 3. Verify all changed
GET /api/sources?status=error
# Should return empty or fewer sources
```

---

## Benefits

✅ **User-Friendly**: Easy recovery from temporary failures  
✅ **Bulk Operations**: Reactivate multiple sources at once  
✅ **Clear Feedback**: Detailed response messages  
✅ **Safe**: Only affects user's own sources  
✅ **Audit Trail**: Maintains crawl logs history  

---

## Related Endpoints

- `GET /api/crawl/status` - Get current status of all sources
- `GET /api/crawl/logs` - View crawl history
- `POST /api/crawl/trigger` - Manually trigger crawl
- `GET /api/sources` - List all sources

---

## Files Modified

1. **`backend/app/api/routes/crawl.py`**
   - Added `reactivate_source()` endpoint
   - Added `reactivate_all_failed_sources()` endpoint

2. **`plan.md`**
   - Updated Phase 5.1 with new endpoints

3. **`backend/app/services/crawl_orchestrator.py`**
   - Fixed RSS crawler import error
   - Made RSS parsing more lenient

---

**Status**: ✅ Backend implementation complete  
**Next Step**: Implement frontend UI components for reactivation
