# X (Twitter) API Troubleshooting Guide

## Common Error: `tweepy.Unauthorized` (401)

The `tweepy.Unauthorized` error indicates authentication failure with the X API (formerly Twitter). This guide will help you resolve it.

**Note:** X is the new name for Twitter. The platform has migrated to developer.x.com (old developer.twitter.com URLs redirect automatically).

---

## Quick Diagnosis Checklist

- [ ] X API credentials are set in `.env` file
- [ ] All 4 credentials are present (API Key, API Secret, Access Token, Access Token Secret)
- [ ] Credentials are valid and not expired
- [ ] X app has Basic/Pro access (not just Free tier)
- [ ] App permissions include "Read" access
- [ ] No typos or extra spaces in credential values
- [ ] Backend was restarted after updating `.env`

---

## Step-by-Step Resolution

### Step 1: Verify Your `.env` File

Open `backend/.env` and ensure these variables are set:

```env
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_SECRET=your_access_secret_here
```

**Common mistakes:**
- Missing any of the 4 credentials
- Extra spaces before/after values
- Using quotes around values (remove them)
- Copy-paste errors

### Step 2: Get/Regenerate X API Credentials

1. **Go to X Developer Portal**
   - Visit: https://developer.x.com/en/portal/dashboard
   - Sign in with your X (Twitter) account

2. **Select Your App**
   - Click on your app name
   - If you don't have an app, create one first

3. **Navigate to "Keys and tokens" Tab**

4. **Get API Key & Secret**
   - Under "Consumer Keys"
   - Click "Regenerate" if needed
   - Copy both values to `.env`:
     ```env
     TWITTER_API_KEY=<API Key>
     TWITTER_API_SECRET=<API Key Secret>
     ```

5. **Generate Access Token & Secret**
   - Under "Authentication Tokens"
   - Click "Generate" or "Regenerate"
   - Copy both values to `.env`:
     ```env
     TWITTER_ACCESS_TOKEN=<Access Token>
     TWITTER_ACCESS_SECRET=<Access Token Secret>
     ```

### Step 3: Check API Access Level

**Most Important:** X has different API access tiers. The Free tier has significant limitations.

1. **Check Your Current Access Level**
   - In Developer Portal, look for "Access Level" or "Product" badge
   - You'll see: "Free", "Basic", "Pro", or "Enterprise"

2. **Upgrade to Basic or Pro Access (Required for most features)**
   - Go to: https://developer.x.com/en/portal/products
   - Choose "Basic" ($200/month) or "Pro" tier
   - Subscribe and pay (access is immediate after payment)
   - Note: This is a paid subscription, not a free application process

3. **Why Basic/Pro Access is Needed**
   - **Free tier:** Only 500 posts/month read, 50 posts/month write (insufficient for timeline endpoints)
   - **Basic tier:** $200/month (increased from $100 in Oct 2024), required for user timeline, mentions, likes
   - **Pro tier:** Professional access with higher limits and advanced features
   - **Enterprise:** Custom pricing and limits
   - Many endpoints used by CreatorPulse require at least Basic tier

4. **Important Pricing Update (October 2024)**
   - X doubled the Basic tier price from $100 to $200/month
   - Annual subscriptions available at discounted rates
   - Free tier now has stricter limits (500 posts/month read)

### Step 4: Verify App Permissions

1. **In X Developer Portal → Your App → Settings**

2. **Check "App permissions"**
   - Should be at least "Read"
   - If it says "Read and Write" or "Read, Write, and Direct Messages", that's fine too

3. **If permissions are wrong:**
   - Click "Edit"
   - Select "Read" or "Read and Write"
   - Save changes
   - **Important:** Regenerate your Access Token & Secret after changing permissions

### Step 5: Restart Backend

After updating `.env`, you MUST restart the backend:

```bash
# Stop the backend (Ctrl+C if running)

# Restart it
cd backend
python app/main.py
```

### Step 6: Test the Connection

```bash
# Test with curl
curl -X POST http://localhost:8000/api/sources \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "twitter",
    "name": "Test Twitter Source",
    "config": {
      "username": "twitter",
      "fetch_type": "timeline",
      "max_results": 10
    }
  }'
```

---

## Error Messages & Solutions

### Error: "Invalid or expired token"

**Cause:** Access tokens have been revoked or expired

**Solution:**
1. Go to Developer Portal → Keys and tokens
2. Click "Regenerate" under Authentication Tokens
3. Update `.env` with new tokens
4. Restart backend

### Error: "Could not authenticate you"

**Cause:** API Key or Secret is incorrect

**Solution:**
1. Regenerate API Key & Secret in Developer Portal
2. Update `.env`
3. Restart backend

### Error: "403 Forbidden"

**Cause:** Insufficient API access level or permissions

**Solution:**
1. Apply for Elevated access (see Step 3 above)
2. Check app permissions (see Step 4 above)
3. Ensure the Twitter user you're fetching is public (not protected)

### Error: "User not found"

**Cause:** Username is incorrect or account is suspended

**Solution:**
1. Verify the username on Twitter.com
2. Remove the "@" symbol (use "elonmusk" not "@elonmusk")
3. Check if the account is suspended or deleted

---

## Testing Your Credentials

### Method 1: Python Script

Create a test file `test_twitter.py`:

```python
import tweepy
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv('TWITTER_API_KEY')
api_secret = os.getenv('TWITTER_API_SECRET')
access_token = os.getenv('TWITTER_ACCESS_TOKEN')
access_secret = os.getenv('TWITTER_ACCESS_SECRET')

print("Testing Twitter credentials...")
print(f"API Key: {api_key[:10]}... (hidden)")
print(f"API Secret: {api_secret[:10]}... (hidden)")
print(f"Access Token: {access_token[:10]}... (hidden)")
print(f"Access Secret: {access_secret[:10]}... (hidden)")

try:
    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret
    )
    
    # Test authentication
    me = client.get_me()
    print(f"\n✅ Success! Authenticated as: @{me.data.username}")
    
    # Test fetching tweets
    user = client.get_user(username="twitter")
    tweets = client.get_users_tweets(user.data.id, max_results=5)
    print(f"✅ Successfully fetched {len(tweets.data)} tweets")
    
except tweepy.Unauthorized as e:
    print(f"\n❌ Authentication failed: {e}")
    print("\nCheck your credentials and API access level.")
except Exception as e:
    print(f"\n❌ Error: {e}")
```

Run it:
```bash
cd backend
python test_twitter.py
```

### Method 2: Check Logs

When you start the backend, look for these log messages:

```
✅ Good:
Initializing Twitter client with OAuth 1.0a credentials
Twitter connection validated for user: @your_username

❌ Bad:
Warning: No Twitter API credentials available
Twitter authentication failed (401 Unauthorized)
```

---

## Alternative: Use Bearer Token (OAuth 2.0)

If you only need read-only access and don't want to deal with 4 credentials:

1. **Get Bearer Token**
   - Developer Portal → Your App → Keys and tokens
   - Under "Bearer Token", click "Generate" or "Regenerate"

2. **Update `.env`**
   ```env
   # Option 1: OAuth 1.0a (4 credentials)
   TWITTER_API_KEY=...
   TWITTER_API_SECRET=...
   TWITTER_ACCESS_TOKEN=...
   TWITTER_ACCESS_SECRET=...
   
   # Option 2: Bearer Token (simpler, but limited)
   # TWITTER_BEARER_TOKEN=your_bearer_token_here
   ```

3. **Update `twitter_connector.py`**
   - Add Bearer Token support to settings (if not already present)
   - The connector already supports bearer tokens

**Note:** Bearer tokens have more limitations than OAuth 1.0a.

---

## Still Not Working?

### Check Twitter API Status
- Visit: https://api.twitterstat.us/
- Ensure Twitter API is operational

### Verify Rate Limits
- You might be hitting rate limits
- Wait 15 minutes and try again

### Check Tweepy Version
```bash
pip show tweepy
# Should be version 4.x or higher
```

### Enable Debug Logging

Add to `twitter_connector.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Contact Support

If all else fails:
1. Check X Developer Community: https://twittercommunity.com/
2. Review X API documentation: https://developer.x.com/en/docs
3. Check if your account has any restrictions

---

## Best Practices

1. **Never commit `.env` to git**
   - Already in `.gitignore`
   - Use `.env.example` as template

2. **Rotate credentials regularly**
   - Regenerate every 90 days
   - Revoke old credentials

3. **Use separate credentials for dev/prod**
   - Create separate X apps
   - Different credentials for each environment

4. **Monitor API usage**
   - Check Developer Portal dashboard
   - Watch for rate limit warnings

5. **Keep credentials secure**
   - Don't share in screenshots
   - Don't paste in public channels
   - Use environment variables only

---

## Summary

The `tweepy.Unauthorized` error is usually caused by:

1. **Missing credentials** → Add all 4 to `.env`
2. **Invalid credentials** → Regenerate in X Developer Portal
3. **Insufficient access level** → Upgrade to Basic ($200/month) or Pro tier (paid subscription required)
4. **Wrong permissions** → Enable Read access
5. **Not restarted** → Restart backend after `.env` changes

**Important:** As of October 2024, X API Basic tier costs $200/month (doubled from $100). The Free tier (500 posts/month) is insufficient for most use cases.

Follow the steps above in order, and you should be able to resolve the issue.

---

## Quick Reference

| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Check credentials, regenerate tokens |
| 403 Forbidden | Upgrade to Basic ($200/month) or Pro tier |
| User not found | Verify username (no @ symbol) |
| Rate limit | Wait 15 minutes |
| Connection failed | Check internet, X API status |
| Free tier limits | Upgrade to Basic tier (required for timeline endpoints) |

**X Developer Portal:** https://developer.x.com/en/portal/dashboard
**API Products & Tiers:** https://developer.x.com/en/products/twitter-api
**API Status:** https://api.twitterstat.us/
