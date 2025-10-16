# CreatorPulse - Quick Start Guide

Get CreatorPulse running in 10 minutes!

## Prerequisites

- Python 3.9+
- Node.js 18+
- Supabase account
- Groq API key
- Gmail account

## 1. Clone & Setup (2 min)

```bash
cd creator_pluse

# Backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
cp .env.example .env

# Frontend
cd ../frontend
npm install
cp .env.example .env
```

## 2. Configure Services (5 min)

### Supabase
1. Create project at [supabase.com](https://supabase.com)
2. Copy URL and keys to `backend/.env`
3. Run `backend/database_schema.sql` in SQL Editor

### Groq
1. Get API key from [console.groq.com](https://console.groq.com)
2. Add to `backend/.env`

### Gmail
1. Enable 2FA on Gmail
2. Generate App Password
3. Add to `backend/.env`

## 3. Update .env Files (1 min)

**backend/.env:**
```env
SUPABASE_URL=your_url_here
SUPABASE_KEY=your_key_here
SUPABASE_SERVICE_KEY=your_service_key_here
JWT_SECRET_KEY=any_random_32_char_string
GROQ_API_KEY=your_groq_key_here
GMAIL_EMAIL=your_email@gmail.com
GMAIL_APP_PASSWORD=your_16_char_password
```

**frontend/.env:**
```env
VITE_API_URL=http://localhost:8000
```

## 4. Run the App (2 min)

**Terminal 1 - Backend:**
```bash
cd backend
venv\Scripts\activate  # Windows
uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## 5. Verify (30 sec)

- Backend: http://localhost:8000/docs
- Frontend: http://localhost:5173

## Next Steps

- Read [GETTING_STARTED.md](docs/GETTING_STARTED.md) for details
- Check [plan.md](plan.md) for roadmap
- Start Phase 2 implementation!

## Common Issues

**Backend won't start?**
- Check Python version: `python --version`
- Verify .env file exists and has all values
- Ensure venv is activated

**Frontend errors?**
- Run `npm install` again
- Check Node version: `node --version`
- Clear browser cache

**Database errors?**
- Verify Supabase credentials
- Ensure database_schema.sql was executed
- Check Supabase project is active

## Get Help

- 📖 Full docs in `docs/` folder
- 🐛 Check error messages in terminal
- 🔍 Review setup guides for each service

**Happy coding! 🚀**
