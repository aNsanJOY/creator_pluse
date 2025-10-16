# Newsletter Upload Feature

## Overview
The newsletter upload feature allows users to upload sample newsletters for voice training. This helps the AI learn the user's writing style and tone to generate personalized newsletter drafts.

## Supported Formats
- **Plain Text (.txt)**: Direct text content
- **Markdown (.md)**: Markdown formatted content (converted to plain text)
- **HTML (.html)**: HTML formatted content (converted to plain text)

## API Endpoints

### 1. Upload Newsletter Sample (JSON)
**Endpoint:** `POST /api/newsletters/upload`

**Description:** Upload a newsletter sample via direct text input or file content.

**Request Body:**
```json
{
  "title": "My Newsletter Title",
  "content": "Direct text content...",
  "file_content": "Content from file...",
  "file_format": "txt|md|html"
}
```

**Notes:**
- Either `content` or `file_content` must be provided
- `file_format` is optional when using `content`
- Content must be at least 10 characters long

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "title": "My Newsletter Title",
  "content": "Processed content...",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 2. Upload Newsletter File
**Endpoint:** `POST /api/newsletters/upload-file`

**Description:** Upload a newsletter sample file (.txt, .md, or .html).

**Request:** Multipart form data
- `file`: The file to upload (required)
- `title`: Optional title (defaults to filename)

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "title": "newsletter.txt",
  "content": "File content...",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 3. Get Newsletter Samples
**Endpoint:** `GET /api/newsletters/samples`

**Description:** Retrieve all newsletter samples for the authenticated user.

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "title": "Sample 1",
    "content": "Content...",
    "created_at": "2024-01-01T00:00:00Z"
  },
  {
    "id": "uuid",
    "user_id": "uuid",
    "title": "Sample 2",
    "content": "Content...",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

### 4. Delete Newsletter Sample
**Endpoint:** `DELETE /api/newsletters/samples/{sample_id}`

**Description:** Delete a specific newsletter sample.

**Response:** `204 No Content`

## Content Processing

### Markdown Processing
Markdown content is converted to HTML first, then to plain text while preserving structure and links.

Example:
```markdown
# My Newsletter
This is **bold** text with a [link](https://example.com).
```

### HTML Processing
HTML content is converted to plain text while preserving structure and extracting links.

Example:
```html
<h1>My Newsletter</h1>
<p>This is <strong>bold</strong> text with a <a href="https://example.com">link</a>.</p>
```

## Database Schema

The `newsletter_samples` table stores uploaded samples:

```sql
CREATE TABLE newsletter_samples (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500),
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Security

- All endpoints require authentication
- Users can only access their own newsletter samples
- Row Level Security (RLS) policies enforce user isolation
- File uploads are validated for format and encoding (UTF-8)

## Usage Examples

### Example 1: Upload via JSON
```bash
curl -X POST "http://localhost:8000/api/newsletters/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Weekly Tech Update",
    "content": "This week in tech: AI advances, new frameworks, and more..."
  }'
```

### Example 2: Upload Markdown File
```bash
curl -X POST "http://localhost:8000/api/newsletters/upload-file" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@newsletter.md" \
  -F "title=My Newsletter"
```

### Example 3: Get All Samples
```bash
curl -X GET "http://localhost:8000/api/newsletters/samples" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Example 4: Delete Sample
```bash
curl -X DELETE "http://localhost:8000/api/newsletters/samples/SAMPLE_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Error Handling

### Common Errors

**400 Bad Request**
- Content too short (< 10 characters)
- Invalid file format
- Missing content
- Invalid UTF-8 encoding

**401 Unauthorized**
- Missing or invalid authentication token

**404 Not Found**
- Newsletter sample not found
- Sample belongs to different user

**500 Internal Server Error**
- Database connection issues
- Unexpected server errors

## Best Practices

1. **Upload Multiple Samples**: Upload 3-5 sample newsletters for better voice training
2. **Diverse Content**: Include different types of newsletters (announcements, updates, tutorials)
3. **Consistent Style**: Ensure samples represent your desired writing style
4. **Clean Content**: Remove unnecessary formatting or metadata before uploading
5. **Regular Updates**: Update samples as your writing style evolves

## Next Steps

After uploading newsletter samples, the system will:
1. Analyze writing style using AI (Phase 4.3)
2. Extract tone, voice, and structural patterns
3. Store voice profile for personalized draft generation
4. Use the profile to generate drafts matching your style

## Dependencies

- `html2text==2024.2.26`: HTML to text conversion
- `markdown==3.5.2`: Markdown processing
- `fastapi`: API framework
- `supabase`: Database client
