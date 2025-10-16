# Voice Training System - Quick Start Guide

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
# Backend
cd backend
pip install groq==0.4.1

# Frontend (already has dependencies)
cd frontend
npm install
```

### 2. Configure Groq API
Add to `backend/.env`:
```env
GROQ_API_KEY=your_groq_api_key_here
```

Get your API key from: https://console.groq.com

### 3. Start Services
```bash
# Terminal 1 - Backend
cd backend
uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 4. Access Voice Training
Navigate to: http://localhost:5173/voice-training

---

## 📝 User Flow

### Step 1: Upload Samples
1. Go to `/voice-training`
2. Choose "Paste Text" or "Upload File"
3. Add title (optional)
4. Paste content or select file (.txt, .md, .html)
5. Click "Upload Sample"
6. Repeat 3-5 times for best results

### Step 2: Analyze Voice
1. Wait until you have 3+ samples
2. Click "Analyze My Voice"
3. Wait for analysis (10-30 seconds)
4. View results and summary

### Step 3: Use Your Voice
Your voice profile is automatically used in future newsletter draft generation!

---

## 🔧 API Quick Reference

### Upload Text Sample
```bash
curl -X POST "http://localhost:8000/api/newsletters/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test", "content": "Your newsletter content here..."}'
```

### Upload File Sample
```bash
curl -X POST "http://localhost:8000/api/newsletters/upload-file" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@newsletter.md"
```

### Analyze Voice
```bash
curl -X POST "http://localhost:8000/api/voice/analyze" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Profile
```bash
curl -X GET "http://localhost:8000/api/voice/profile" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🧪 Testing

### Run Backend Tests
```bash
cd backend
pytest tests/test_voice_analysis.py -v
pytest tests/test_newsletter_upload.py -v
```

### Manual Test Flow
1. Login to app
2. Navigate to `/voice-training`
3. Upload 3 sample newsletters
4. Click "Analyze My Voice"
5. Check database: `users.voice_profile` should be populated
6. Verify profile in response

---

## 🎯 Key Features

### ✅ Smart Defaults
- No samples? Uses professional default profile
- API error? Falls back to default
- Always functional, never blocks workflow

### ✅ Comprehensive Analysis
- Tone & style detection
- Writing patterns (questions, lists, humor)
- Formatting preferences
- Unique characteristics
- Sample phrases

### ✅ User-Friendly
- Dual upload modes (text/file)
- Progress tracking
- Clear error messages
- Tips and guidance

---

## 🐛 Common Issues

### "Analysis failed"
**Cause:** Groq API key missing/invalid
**Fix:** Check `.env` file, verify API key

### "No samples found"
**Cause:** Samples not uploaded or user mismatch
**Fix:** Upload samples first, check authentication

### "Using default profile"
**Cause:** No samples or API error
**Fix:** This is expected behavior - upload samples and re-analyze

---

## 📊 Voice Profile Structure

```json
{
  "tone": "friendly and enthusiastic",
  "style": "conversational",
  "vocabulary_level": "intermediate",
  "personality_traits": ["enthusiastic", "friendly"],
  "writing_patterns": {
    "uses_questions": true,
    "uses_lists": true
  },
  "source": "analyzed",
  "samples_count": 5
}
```

---

## 📚 Documentation

- **Full Guide**: [docs/VOICE_TRAINING.md](./docs/VOICE_TRAINING.md)
- **Implementation**: [PHASE_4.2_4.3_SUMMARY.md](./PHASE_4.2_4.3_SUMMARY.md)
- **Newsletter Upload**: [docs/NEWSLETTER_UPLOAD.md](./docs/NEWSLETTER_UPLOAD.md)

---

## 🎨 UI Components

### Pages
- `frontend/src/pages/NewsletterSamples.tsx` - Main voice training page

### Services
- `frontend/src/services/newsletters.service.ts` - API client

### Backend
- `backend/app/services/voice_analyzer.py` - Voice analysis logic
- `backend/app/api/routes/voice.py` - Voice API endpoints
- `backend/app/api/routes/newsletters.py` - Sample upload endpoints

---

## ✨ Next Steps

After voice training is complete:
1. **Phase 5**: Content aggregation and trend detection
2. **Phase 6**: Use voice profile for personalized draft generation
3. **Future**: Manual profile editing, multiple profiles, A/B testing

---

## 💡 Tips

### For Best Results
- Upload 3-5 diverse newsletter samples
- Include complete newsletters (intro + body + conclusion)
- Use your authentic writing style
- Re-analyze after adding new samples

### For Developers
- Monitor Groq API usage and costs
- Log analysis results for debugging
- Handle all error cases gracefully
- Test with various sample counts (0, 1, 3, 5+)

---

## 🔐 Security

- ✅ Authentication required for all endpoints
- ✅ Row-level security (RLS) enforced
- ✅ User isolation (can't access others' samples)
- ✅ Voice profiles stored securely in database
- ✅ API keys in environment variables

---

## 📞 Support

- **API Docs**: http://localhost:8000/docs
- **Issues**: Check logs in terminal
- **Database**: Verify in Supabase dashboard
- **Tests**: Run pytest for validation

---

**Status**: ✅ Ready to use!

**Last Updated**: October 15, 2025
