# CreatorPulse

A daily feed curator and newsletter drafting assistant for independent creators. CreatorPulse aggregates trusted sources, detects trending topics, and generates voice-matched newsletter drafts that can be reviewed and sent in under 20 minutes.

## 🚀 Features

- **Source Aggregation**: Connect Twitter, YouTube, and RSS feeds
- **Trend Detection**: AI-powered detection of trending topics
- **Voice Matching**: Learns your writing style from past newsletters
- **Draft Generation**: Auto-generates newsletter drafts daily at 8:00 AM
- **Quick Review**: Review and send newsletters in under 20 minutes
- **Feedback Loop**: Thumbs up/down to refine future drafts

## 🛠️ Tech Stack

### Frontend
- React with Vite
- TailwindCSS for styling
- shadcn/ui components
- Lucide icons
- React Router for navigation

### Backend
- FastAPI (Python)
- Supabase (PostgreSQL database)
- Supabase Auth for authentication
- APScheduler for background tasks

### External Services
- **AI/LLM**: Groq
- **Email**: Gmail SMTP
- **APIs**: Twitter API, YouTube API, RSS feeds

## 📋 Prerequisites

- Python 3.9+
- Node.js 18+
- Supabase account
- Groq API key
- Gmail account with App Password
- Twitter API credentials (optional)
- YouTube API credentials (optional)

## 🔧 Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
- Windows: `venv\Scripts\activate`
- macOS/Linux: `source venv/bin/activate`

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Create a `.env` file in the backend directory with the following variables:
```env
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key

# JWT
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# Groq
GROQ_API_KEY=your_groq_api_key

# Gmail SMTP
GMAIL_EMAIL=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587

# Twitter API (optional)
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_SECRET=your_twitter_access_secret

# YouTube API (optional)
YOUTUBE_API_KEY=your_youtube_api_key

# Application
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000
```

6. Run database migrations:
```bash
alembic upgrade head
```

7. Start the development server:
```bash
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file in the frontend directory:
```env
VITE_API_URL=http://localhost:8000
```

4. Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## 📚 Project Structure

```
creator_pluse/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   └── dependencies.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── database.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── lib/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── package.json
│   └── .env
├── .gitignore
├── README.md
├── prd.md
└── plan.md
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 📖 Documentation

### API Documentation
Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Feature Guides
- [Trend Detection](./docs/TREND_DETECTION.md) - AI-powered trending topic detection
- [Scheduled Crawling](./docs/SCHEDULED_CRAWLING.md) - Automated content aggregation
- [API Credentials Guide](./docs/API_CREDENTIALS_GUIDE.md) - Setting up external APIs
- [Adding New Sources](./docs/ADDING_NEW_SOURCES.md) - Extensibility guide

## 🔐 Gmail SMTP Setup

1. Enable 2-factor authentication on your Gmail account
2. Go to Google Account Settings → Security → 2-Step Verification
3. Scroll to "App passwords" and generate a new password
4. Use this password in the `GMAIL_APP_PASSWORD` environment variable

## 📊 Success Metrics

- Average review time per draft: ≤ 20 minutes
- Draft acceptance rate: ≥ 70%
- Median open/CTR uplift: ≥ 2× baseline
- System uptime: ≥ 99.5%

## 🗺️ Roadmap

See [plan.md](./plan.md) for the detailed implementation plan.

## 📄 License

MIT License

## 🤝 Contributing

Contributions are welcome! Please read the contributing guidelines before submitting PRs.

## 📧 Support

For support, email support@creatorpulse.com or join our Discord community.
