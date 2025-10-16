# CreatorPulse Backend

FastAPI backend for CreatorPulse - A daily feed curator and newsletter drafting assistant.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows: `venv\Scripts\activate`
- macOS/Linux: `source venv/bin/activate`

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

5. Set up the database schema in Supabase:
- Go to your Supabase project dashboard
- Navigate to SQL Editor
- Copy and paste the contents of `database_schema.sql`
- Execute the SQL

## Running the Server

Development mode with auto-reload:
```bash
uvicorn app.main:app --reload --port 8000
```

Or use the main.py directly:
```bash
python -m app.main
```

The API will be available at:
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

Run tests with pytest:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=app --cov-report=html
```

### Testing Twitter API Credentials

If you're experiencing issues with Twitter API authentication:

```bash
python test_twitter_credentials.py
```

This will diagnose credential issues and provide specific guidance. See:
- Quick fix guide: `../TWITTER_QUICK_FIX.md`
- Detailed troubleshooting: `../docs/TWITTER_TROUBLESHOOTING.md`

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── routes/          # API route handlers
│   │   └── dependencies.py  # Shared dependencies
│   ├── core/
│   │   ├── config.py        # Configuration settings
│   │   ├── security.py      # Authentication & security
│   │   └── database.py      # Database connection
│   ├── models/              # Database models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   └── main.py              # FastAPI application
├── tests/                   # Test files
├── database_schema.sql      # Database schema
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── README.md               # This file
```

## API Endpoints

### Health Check
- `GET /` - Root endpoint
- `GET /health` - Health check

### Authentication (Phase 2)
- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/logout` - Logout user
- `POST /api/auth/reset-password` - Reset password

### Sources (Phase 3)
- `GET /api/sources` - List all user sources
- `POST /api/sources` - Add new source
- `DELETE /api/sources/{id}` - Remove source
- `GET /api/sources/{id}/status` - Check source status

### Drafts (Phase 6)
- `GET /api/drafts/{id}` - Fetch draft
- `PUT /api/drafts/{id}` - Update draft
- `POST /api/drafts/{id}/publish` - Send newsletter
- `POST /api/drafts/{id}/regenerate` - Regenerate draft

### Feedback (Phase 7)
- `POST /api/feedback` - Submit feedback
- `GET /api/feedback/user/{user_id}` - Get user feedback history

### User (Phase 2)
- `GET /api/user/profile` - Get user profile
- `DELETE /api/user/account` - Delete account

## Environment Variables

See `.env.example` for all required environment variables.

## Database Schema

The database schema is defined in `database_schema.sql`. It includes:
- Users table
- Sources table (Twitter, YouTube, RSS)
- Source content cache table
- Newsletters table (drafts and sent)
- Newsletter samples table (for voice training)
- Feedback table (thumbs up/down)
- Trends table

All tables have Row Level Security (RLS) enabled for data protection.
