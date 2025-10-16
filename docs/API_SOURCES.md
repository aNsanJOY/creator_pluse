# Source Management API Reference

## Overview
The Source Management API allows users to connect and manage various content sources (Twitter, YouTube, RSS feeds, etc.) for their newsletter curation.

## Base URL
```
http://localhost:8000/api/sources
```

## Authentication
All endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### 1. List All Sources
Get all sources for the authenticated user.

**Endpoint:** `GET /api/sources`

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "source_type": "rss",
    "name": "TechCrunch",
    "url": "https://techcrunch.com/feed/",
    "config": {"polling_frequency": "daily"},
    "status": "active",
    "last_crawled_at": "2025-10-13T12:00:00Z",
    "error_message": null,
    "created_at": "2025-10-13T10:00:00Z",
    "updated_at": "2025-10-13T10:00:00Z"
  }
]
```

---

### 2. Create Source
Add a new content source.

**Endpoint:** `POST /api/sources`

**Request Body:**
```json
{
  "source_type": "rss",
  "name": "TechCrunch",
  "url": "https://techcrunch.com/feed/",
  "config": {
    "polling_frequency": "daily"
  },
  "credentials": null
}
```

**Supported Source Types:**
- `twitter` - Twitter/X accounts
- `youtube` - YouTube channels
- `rss` - RSS/Atom feeds
- `substack` - Substack newsletters
- `medium` - Medium publications
- `linkedin` - LinkedIn profiles
- `podcast` - Podcast feeds
- `newsletter` - Newsletter archives
- `custom` - Custom sources

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "source_type": "rss",
  "name": "TechCrunch",
  "url": "https://techcrunch.com/feed/",
  "config": {"polling_frequency": "daily"},
  "status": "active",
  "last_crawled_at": null,
  "error_message": null,
  "created_at": "2025-10-13T10:00:00Z",
  "updated_at": "2025-10-13T10:00:00Z"
}
```

**Validation Errors:** `400 Bad Request`
```json
{
  "detail": "Invalid RSS feed format"
}
```

---

### 3. Get Source by ID
Retrieve a specific source.

**Endpoint:** `GET /api/sources/{source_id}`

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "source_type": "rss",
  "name": "TechCrunch",
  "url": "https://techcrunch.com/feed/",
  "config": {"polling_frequency": "daily"},
  "status": "active",
  "last_crawled_at": "2025-10-13T12:00:00Z",
  "error_message": null,
  "created_at": "2025-10-13T10:00:00Z",
  "updated_at": "2025-10-13T10:00:00Z"
}
```

**Error:** `404 Not Found`
```json
{
  "detail": "Source not found"
}
```

---

### 4. Update Source
Update source details (partial updates supported).

**Endpoint:** `PUT /api/sources/{source_id}`

**Request Body:**
```json
{
  "name": "TechCrunch (Updated)",
  "config": {
    "polling_frequency": "hourly"
  }
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "source_type": "rss",
  "name": "TechCrunch (Updated)",
  "url": "https://techcrunch.com/feed/",
  "config": {"polling_frequency": "hourly"},
  "status": "active",
  "last_crawled_at": "2025-10-13T12:00:00Z",
  "error_message": null,
  "created_at": "2025-10-13T10:00:00Z",
  "updated_at": "2025-10-13T12:30:00Z"
}
```

---

### 5. Delete Source
Remove a source and all associated content.

**Endpoint:** `DELETE /api/sources/{source_id}`

**Response:** `204 No Content`

**Error:** `404 Not Found`
```json
{
  "detail": "Source not found"
}
```

---

### 6. Check Source Status
Get health status and crawl information for a source.

**Endpoint:** `GET /api/sources/{source_id}/status`

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "status": "active",
  "last_crawled_at": "2025-10-13T12:00:00Z",
  "error_message": null,
  "is_healthy": true
}
```

**Status Values:**
- `active` - Source is working normally
- `error` - Source has encountered an error
- `pending` - Source is being set up

---

## Source Type Examples

### RSS Feed
```json
{
  "source_type": "rss",
  "name": "TechCrunch",
  "url": "https://techcrunch.com/feed/",
  "config": {
    "polling_frequency": "daily"
  }
}
```

### YouTube Channel
```json
{
  "source_type": "youtube",
  "name": "Fireship",
  "url": "https://www.youtube.com/@Fireship",
  "config": {
    "include_shorts": false
  }
}
```

### Twitter Account
```json
{
  "source_type": "twitter",
  "name": "Naval",
  "url": "https://twitter.com/naval",
  "config": {
    "include_retweets": false
  }
}
```

### Substack Newsletter
```json
{
  "source_type": "substack",
  "name": "Stratechery",
  "url": "https://stratechery.com",
  "config": {}
}
```

---

## Validation Rules

### Twitter
- Handle must be 1-15 characters
- Alphanumeric and underscore only
- Can provide full URL or just handle

### YouTube
- Must be a valid YouTube channel URL
- Supports formats: `/channel/`, `/c/`, `/@username`, `/user/`

### RSS
- Must be a valid, parseable RSS/Atom feed
- Feed must have at least one entry
- Validates by actually fetching and parsing the feed

### URL-based Sources (Substack, Medium, LinkedIn)
- Must be a valid URL format
- Must contain the expected domain

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid Twitter handle format"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 404 Not Found
```json
{
  "detail": "Source not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to create source: <error details>"
}
```

---

## Testing with cURL

### Create an RSS Source
```bash
curl -X POST http://localhost:8000/api/sources \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "rss",
    "name": "TechCrunch",
    "url": "https://techcrunch.com/feed/"
  }'
```

### List All Sources
```bash
curl -X GET http://localhost:8000/api/sources \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Delete a Source
```bash
curl -X DELETE http://localhost:8000/api/sources/{source_id} \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Notes

- **Credentials Storage**: OAuth tokens and API keys are stored securely in the `credentials` JSONB field
- **Config Field**: Use the `config` field for source-specific settings (polling frequency, filters, etc.)
- **Cascading Deletes**: Deleting a source will also delete all associated content from the `source_content` table
- **User Isolation**: Users can only access their own sources (enforced by RLS policies)
- **Extensibility**: New source types can be added without database schema changes

---

## Interactive Documentation

For interactive API testing, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
