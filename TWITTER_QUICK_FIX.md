# X (Twitter) `Unauthorized` Error - Quick Fix

## 🚨 Getting `tweepy.Unauthorized` error? Follow these steps:

### 1️⃣ Check Your `.env` File (backend/.env)

Make sure you have ALL 4 credentials:

```env
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_SECRET=your_access_secret_here
```

**⚠️ Common mistakes:**
- Missing any credential
- Extra spaces or quotes
- Wrong variable names

---

### 2️⃣ Get Credentials from X Developer Portal

1. Go to: https://developer.x.com/en/portal/dashboard
2. Select your app (or create one)
3. Click "Keys and tokens" tab
4. Copy these values:
   - **API Key** → `TWITTER_API_KEY`
   - **API Key Secret** → `TWITTER_API_SECRET`
   - **Access Token** → `TWITTER_ACCESS_TOKEN`
   - **Access Token Secret** → `TWITTER_ACCESS_SECRET`

**💡 Tip:** Click "Regenerate" if you don't see the values

---

### 3️⃣ Upgrade to Basic or Pro Tier (CRITICAL!)

**Most common cause of 401 errors:**

1. Go to: https://developer.x.com/en/portal/products
2. Choose "Basic" ($200/month) or "Pro" tier
3. Subscribe to the tier (payment required)
4. Access is immediate after payment

**Why?** The "Free" tier only allows 500 posts/month read (insufficient for timeline endpoints). You need "Basic" ($200/month as of Oct 2024) or "Pro" tier.

**Pricing (October 2024):**
- Free: 500 posts/month read, 50 posts/month write
- Basic: $200/month (was $100, increased Oct 2024)
- Pro: Higher limits for professional use
- Enterprise: Custom pricing

**Note:** X (formerly Twitter) has migrated to developer.x.com. Old developer.twitter.com URLs redirect automatically.

---

### 4️⃣ Restart Backend

```bash
# Stop backend (Ctrl+C)
cd backend
python app/main.py
```

**⚠️ MUST restart after changing `.env`**

---

### 5️⃣ Test It

Look for this in logs when backend starts:

```
✅ Good:
Initializing Twitter client with OAuth 1.0a credentials
Twitter connection validated for user: @your_username

❌ Bad:
Twitter authentication failed (401 Unauthorized)
```

---

## Still Not Working?

### Quick Checks:

- [ ] All 4 credentials in `.env`
- [ ] No typos or spaces
- [ ] Elevated access approved
- [ ] Backend restarted
- [ ] App has "Read" permissions in X Developer Portal

### Need More Help?

See detailed guide: `docs/TWITTER_TROUBLESHOOTING.md`

---

## Test Script

Create `test_twitter.py` in backend folder:

```python
import tweepy
import os
from dotenv import load_dotenv

load_dotenv()

try:
    client = tweepy.Client(
        consumer_key=os.getenv('TWITTER_API_KEY'),
        consumer_secret=os.getenv('TWITTER_API_SECRET'),
        access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
        access_token_secret=os.getenv('TWITTER_ACCESS_SECRET')
    )
    
    me = client.get_me()
    print(f"✅ SUCCESS! Authenticated as: @{me.data.username}")
    
except tweepy.Unauthorized:
    print("❌ FAILED: Invalid credentials or insufficient access level")
    print("1. Check .env file")
    print("2. Upgrade to Basic or Pro tier")
    print("3. Regenerate tokens")
except Exception as e:
    print(f"❌ ERROR: {e}")
```

Run: `python test_twitter.py`

---

## Quick Links

- **X Developer Portal:** https://developer.x.com/en/portal/dashboard
- **API Products & Tiers:** https://developer.x.com/en/products/twitter-api
- **API Status:** https://api.twitterstat.us/

**Note:** Old developer.twitter.com URLs redirect to developer.x.com automatically.

---

**TL;DR:** Add 4 credentials to `.env`, upgrade to Basic/Pro tier, restart backend. That fixes 95% of cases.
