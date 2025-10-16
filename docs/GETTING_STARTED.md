# Getting Started with CreatorPulse

This guide will help you set up and run CreatorPulse locally for development.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** 18+ ([Download](https://nodejs.org/))
- **Python** 3.9+ ([Download](https://www.python.org/))
- **Git** ([Download](https://git-scm.com/))
- A code editor (VS Code recommended)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd creator_pluse
```

### 2. Set Up External Services

Follow the [External Services Setup Guide](./EXTERNAL_SERVICES_SETUP.md) to configure:
- Supabase (Database & Auth)
- Groq API (LLM)
- Gmail SMTP (Email delivery)
- Twitter API (Optional)
- YouTube API (Optional)

### 3. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables template
cp .env.example .env

# Edit .env and add your credentials
# Use your favorite text editor to fill in the values
```

### 4. Database Setup

1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Open `backend/database_schema.sql`
4. Copy the entire content
5. Paste into Supabase SQL Editor
6. Click "Run" to execute

### 5. Start Backend Server

```bash
# Make sure you're in the backend directory with venv activated
uvicorn app.main:app --reload --port 8000
```

The backend API will be available at:
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 6. Frontend Setup

Open a new terminal window:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Copy environment variables template
cp .env.example .env

# Edit .env if needed (default should work)
```

### 7. Start Frontend Server

```bash
# Make sure you're in the frontend directory
npm run dev
```

The frontend will be available at: http://localhost:5173

## Verify Installation

### Backend Health Check

Visit http://localhost:8000/health in your browser. You should see:

```json
{
  "status": "healthy",
  "environment": "development"
}
```

### Frontend

Visit http://localhost:5173 in your browser. You should see the CreatorPulse home page.

## Project Structure

```
creator_pluse/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Config, security, database
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── main.py         # FastAPI app
│   ├── tests/              # Backend tests
│   ├── database_schema.sql # Database schema
│   ├── requirements.txt    # Python dependencies
│   └── .env               # Environment variables (create this)
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── contexts/      # React contexts
│   │   ├── pages/         # Page components
│   │   ├── services/      # API services
│   │   ├── App.tsx        # Main app
│   │   └── main.tsx       # Entry point
│   ├── package.json       # Node dependencies
│   └── .env              # Environment variables (create this)
├── docs/                  # Documentation
├── README.md             # Project overview
├── plan.md              # Implementation plan
└── prd.md              # Product requirements
```

## Development Workflow

### Running Tests

**Backend:**
```bash
cd backend
pytest
```

**Frontend:**
```bash
cd frontend
npm test
```

### Code Linting

**Backend:**
```bash
cd backend
# Install flake8 if not already installed
pip install flake8
flake8 app/
```

**Frontend:**
```bash
cd frontend
npm run lint
```

### Building for Production

**Backend:**
```bash
# No build step needed for FastAPI
# Just ensure all dependencies are installed
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm run build
# Output will be in the dist/ directory
```

## Common Issues & Solutions

### Issue: Backend won't start

**Solution:**
- Check if port 8000 is already in use
- Verify all environment variables in `.env` are set
- Ensure virtual environment is activated
- Check Python version: `python --version` (should be 3.9+)

### Issue: Frontend shows connection errors

**Solution:**
- Verify backend is running on port 8000
- Check `VITE_API_URL` in frontend `.env`
- Clear browser cache and reload
- Check browser console for specific errors

### Issue: Database connection fails

**Solution:**
- Verify Supabase credentials in backend `.env`
- Check if database schema has been executed
- Ensure Supabase project is active (not paused)
- Check network connectivity

### Issue: "Module not found" errors

**Solution:**
- Backend: Ensure virtual environment is activated and dependencies installed
- Frontend: Run `npm install` again
- Delete `node_modules` and run `npm install` fresh

### Issue: CORS errors in browser

**Solution:**
- Check `FRONTEND_URL` in backend `.env` matches your frontend URL
- Verify CORS middleware is configured in `backend/app/main.py`
- Clear browser cache

## Next Steps

Now that you have CreatorPulse running locally:

1. **Explore the API**: Visit http://localhost:8000/docs to see all available endpoints
2. **Review the Plan**: Check `plan.md` for the full implementation roadmap
3. **Start Phase 2**: Begin implementing authentication features
4. **Join Development**: Check the contributing guidelines (coming soon)

## Getting Help

- **Documentation**: Check the `docs/` directory
- **API Reference**: http://localhost:8000/docs
- **Issues**: Create an issue on GitHub
- **Questions**: Reach out to the team

## Environment Variables Reference

### Backend (.env)

```env
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key
JWT_SECRET_KEY=your_random_secret_key
GROQ_API_KEY=your_groq_api_key
GMAIL_EMAIL=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password

# Optional
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_SECRET=your_twitter_access_secret
YOUTUBE_API_KEY=your_youtube_api_key

# Defaults (usually don't need to change)
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000
ENVIRONMENT=development
```

### Frontend (.env)

```env
VITE_API_URL=http://localhost:8000
```

## Tips for Development

1. **Use the Swagger UI**: The interactive API docs at `/docs` are great for testing endpoints
2. **Hot Reload**: Both backend and frontend support hot reload - changes appear automatically
3. **Browser DevTools**: Use React DevTools and Network tab for debugging
4. **Database Inspection**: Use Supabase dashboard to view and query data directly
5. **Logging**: Check terminal output for both backend and frontend for errors

## Production Deployment

For production deployment instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md) (coming soon).

---

**Happy Coding! 🚀**
