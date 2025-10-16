# Newsletter Upload Feature - Quick Start

## Installation

1. **Install new dependencies:**
   ```bash
   pip install html2text==2024.2.26 markdown==3.5.2
   ```
   
   Or install all dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify database schema:**
   The `newsletter_samples` table should already exist. If not, run the schema:
   ```bash
   # Connect to your Supabase database and run database_schema.sql
   ```

## Running the Server

```bash
cd backend
uvicorn app.main:app --reload
```

The server will start at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Quick Test

### 1. Get Authentication Token
First, login or signup to get an authentication token:

```bash
# Signup
curl -X POST "http://localhost:8000/api/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "full_name": "Test User"
  }'

# Login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123"
  }'
```

Save the `access_token` from the response.

### 2. Upload a Newsletter Sample

**Option A: Upload text directly**
```bash
curl -X POST "http://localhost:8000/api/newsletters/upload" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Newsletter",
    "content": "Welcome to my newsletter! This week I want to share some exciting updates about AI and technology. The field is moving incredibly fast, and there are so many interesting developments to discuss."
  }'
```

**Option B: Upload a markdown file**
Create a file `sample.md`:
```markdown
# Weekly Tech Update

Hello readers!

This week in tech:
- **AI Advances**: New models released
- **Web Development**: Latest frameworks
- **Cloud Computing**: Best practices

Check out my [blog](https://example.com) for more!
```

Upload it:
```bash
curl -X POST "http://localhost:8000/api/newsletters/upload-file" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@sample.md" \
  -F "title=Weekly Tech Update"
```

### 3. List Your Samples

```bash
curl -X GET "http://localhost:8000/api/newsletters/samples" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Delete a Sample

```bash
curl -X DELETE "http://localhost:8000/api/newsletters/samples/SAMPLE_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Testing

Run the test suite:

```bash
# Run all newsletter upload tests
pytest tests/test_newsletter_upload.py -v

# Run with coverage
pytest tests/test_newsletter_upload.py --cov=app.api.routes.newsletters -v

# Run all tests
pytest tests/ -v
```

## Supported File Formats

| Format | Extension | Processing |
|--------|-----------|------------|
| Plain Text | `.txt` | Direct storage |
| Markdown | `.md` | Converted to plain text (structure preserved) |
| HTML | `.html` | Converted to plain text (links preserved) |

## Common Issues

### Issue: "Failed to upload newsletter sample"
**Solution:** Check that:
- You're authenticated (valid token)
- Content is at least 10 characters
- File is UTF-8 encoded
- File extension is .txt, .md, or .html

### Issue: "Newsletter sample not found"
**Solution:** 
- Verify the sample ID is correct
- Ensure the sample belongs to your user account

### Issue: Import errors for html2text or markdown
**Solution:**
```bash
pip install html2text markdown
```

## Example Files

### example_newsletter.txt
```
Weekly Newsletter - January 2024

Hi everyone,

This week I want to share three key insights:

1. The importance of consistency in content creation
2. How to engage with your audience authentically
3. Tips for growing your newsletter organically

Thanks for reading!
```

### example_newsletter.md
```markdown
# Weekly Newsletter

## January 2024 Edition

Hi everyone! 👋

This week's highlights:

- **Consistency** is key in content creation
- **Authenticity** builds trust with your audience
- **Organic growth** beats paid promotion

Read more on my [blog](https://example.com).

Cheers!
```

### example_newsletter.html
```html
<!DOCTYPE html>
<html>
<head>
    <title>Weekly Newsletter</title>
</head>
<body>
    <h1>Weekly Newsletter</h1>
    <h2>January 2024 Edition</h2>
    
    <p>Hi everyone!</p>
    
    <p>This week's highlights:</p>
    <ul>
        <li><strong>Consistency</strong> is key</li>
        <li><strong>Authenticity</strong> builds trust</li>
        <li><strong>Organic growth</strong> wins</li>
    </ul>
    
    <p>Read more on my <a href="https://example.com">blog</a>.</p>
</body>
</html>
```

## Next Steps

After uploading samples:
1. **Phase 4.2:** Frontend UI will be created for easier uploads
2. **Phase 4.3:** Voice analysis will extract your writing style
3. **Phase 6:** AI will use your style to generate personalized drafts

## Need Help?

- Check the full documentation: `docs/NEWSLETTER_UPLOAD.md`
- Review the implementation: `backend/app/api/routes/newsletters.py`
- Run tests to see examples: `tests/test_newsletter_upload.py`
- Visit API docs: http://localhost:8000/docs
