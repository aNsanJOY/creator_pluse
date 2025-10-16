# External Services Setup Guide

This guide walks you through setting up all the external services required for CreatorPulse.

## Table of Contents
1. [Supabase Setup](#supabase-setup)
2. [Groq API Setup](#groq-api-setup)
3. [Gmail SMTP Setup](#gmail-smtp-setup)
4. [Twitter API Setup (Optional)](#twitter-api-setup-optional)
5. [YouTube API Setup (Optional)](#youtube-api-setup-optional)

---

## Supabase Setup

Supabase provides the PostgreSQL database and authentication for CreatorPulse.

### Steps:

1. **Create a Supabase Account**
   - Go to [https://supabase.com](https://supabase.com)
   - Sign up for a free account

2. **Create a New Project**
   - Click "New Project"
   - Choose your organization
   - Enter project name: `creatorpulse`
   - Set a strong database password (save this!)
   - Select a region close to your users
   - Click "Create new project"

3. **Get Your Credentials**
   - Once the project is ready, go to Settings → API
   - Copy the following:
     - `Project URL` → `SUPABASE_URL`
     - `anon public` key → `SUPABASE_KEY`
     - `service_role` key → `SUPABASE_SERVICE_KEY` (keep this secret!)

4. **Set Up Database Schema**
   - Go to SQL Editor in the Supabase dashboard
   - Click "New Query"
   - Copy the contents of `backend/database_schema.sql`
   - Paste and execute the SQL

5. **Configure Authentication**
   - Go to Authentication → Settings
   - Enable Email provider
   - Disable email confirmation for MVP (optional)
   - Set Site URL to your frontend URL (e.g., `http://localhost:5173`)

---

## Groq API Setup

Groq provides fast LLM inference for content generation and analysis.

### Steps:

1. **Create a Groq Account**
   - Go to [https://console.groq.com](https://console.groq.com)
   - Sign up for an account

2. **Generate API Key**
   - Navigate to API Keys section
   - Click "Create API Key"
   - Give it a name: `CreatorPulse`
   - Copy the API key → `GROQ_API_KEY`
   - **Important:** Save this key immediately, you won't see it again!

3. **Check Rate Limits**
   - Free tier: 30 requests/minute
   - Upgrade if needed for production use

---

## Gmail SMTP Setup

Gmail SMTP is used to send newsletter emails to users.

### Steps:

1. **Enable 2-Factor Authentication**
   - Go to your Google Account settings
   - Navigate to Security
   - Enable 2-Step Verification if not already enabled

2. **Generate App Password**
   - Go to Google Account → Security
   - Under "2-Step Verification", find "App passwords"
   - Click "App passwords"
   - Select app: "Mail"
   - Select device: "Other (Custom name)"
   - Enter: "CreatorPulse"
   - Click "Generate"
   - Copy the 16-character password → `GMAIL_APP_PASSWORD`

3. **Configure Environment Variables**
   ```env
   GMAIL_EMAIL=your_email@gmail.com
   GMAIL_APP_PASSWORD=your_16_character_app_password
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   ```

4. **Important Notes**
   - Gmail has sending limits:
     - Regular Gmail: 500 emails/day
     - Google Workspace: 2,000 emails/day
   - For production, consider using a dedicated email service (SendGrid, AWS SES, Resend)

---

## Twitter API Setup (Optional)

Required for aggregating content from Twitter accounts.

### Steps:

1. **Apply for Twitter Developer Account**
   - Go to [https://developer.twitter.com](https://developer.twitter.com)
   - Sign in with your Twitter account
   - Apply for a developer account
   - Fill out the application form (explain CreatorPulse use case)
   - Wait for approval (usually 1-2 days)

2. **Create a Project and App**
   - Once approved, go to Developer Portal
   - Create a new Project: "CreatorPulse"
   - Create a new App within the project
   - Set app permissions to "Read"

3. **Generate API Keys**
   - Go to your app's "Keys and tokens" tab
   - Generate the following:
     - API Key → `TWITTER_API_KEY`
     - API Secret Key → `TWITTER_API_SECRET`
     - Access Token → `TWITTER_ACCESS_TOKEN`
     - Access Token Secret → `TWITTER_ACCESS_SECRET`

4. **Enable OAuth 1.0a**
   - Go to App Settings → User authentication settings
   - Enable OAuth 1.0a
   - Set callback URL (for future OAuth flow)

5. **Check Rate Limits**
   - Free tier: 500,000 tweets/month
   - Monitor usage in the developer portal

---

## YouTube API Setup (Optional)

Required for aggregating content from YouTube channels.

### Steps:

1. **Create Google Cloud Project**
   - Go to [https://console.cloud.google.com](https://console.cloud.google.com)
   - Create a new project: "CreatorPulse"

2. **Enable YouTube Data API v3**
   - In the project, go to "APIs & Services" → "Library"
   - Search for "YouTube Data API v3"
   - Click on it and press "Enable"

3. **Create API Credentials**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "API Key"
   - Copy the API key → `YOUTUBE_API_KEY`
   - (Optional) Restrict the key to YouTube Data API v3 only

4. **Set Up OAuth 2.0 (for future use)**
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: "Web application"
   - Add authorized redirect URIs
   - Save client ID and secret for OAuth flow

5. **Check Quotas**
   - Free tier: 10,000 units/day
   - Most read operations cost 1 unit
   - Monitor usage in the Google Cloud Console

---

## Environment Variables Summary

After completing all setups, your `.env` file should look like this:

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key

# JWT
JWT_SECRET_KEY=your_random_secret_key_min_32_chars
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# Groq
GROQ_API_KEY=your_groq_api_key

# Gmail SMTP
GMAIL_EMAIL=your_email@gmail.com
GMAIL_APP_PASSWORD=your_16_character_app_password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587

# Twitter API (Optional)
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_SECRET=your_twitter_access_secret

# YouTube API (Optional)
YOUTUBE_API_KEY=your_youtube_api_key

# Application
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000
ENVIRONMENT=development
```

---

## Security Best Practices

1. **Never commit `.env` files to version control**
   - Always use `.env.example` as a template
   - Add `.env` to `.gitignore`

2. **Use different keys for development and production**
   - Create separate Supabase projects
   - Use different API keys

3. **Rotate keys regularly**
   - Especially after team member changes
   - If keys are accidentally exposed

4. **Restrict API key permissions**
   - Use read-only keys where possible
   - Restrict by IP address in production

5. **Monitor API usage**
   - Set up alerts for unusual activity
   - Track costs and rate limits

---

## Troubleshooting

### Supabase Connection Issues
- Check if your IP is allowed (Supabase → Settings → Database → Connection pooling)
- Verify the project URL and keys are correct
- Ensure RLS policies are properly configured

### Gmail SMTP Errors
- Verify 2FA is enabled
- Regenerate app password if needed
- Check for "Less secure app access" warnings
- Ensure SMTP port 587 is not blocked by firewall

### Twitter API Rate Limits
- Implement caching to reduce API calls
- Use delta crawls (only fetch new content)
- Consider upgrading to paid tier for production

### YouTube API Quota Exceeded
- Optimize queries to use fewer units
- Implement caching
- Request quota increase from Google

---

## Cost Estimates (Monthly)

- **Supabase Free Tier**: $0 (up to 500MB database, 2GB bandwidth)
- **Groq Free Tier**: $0 (with rate limits)
- **Gmail SMTP**: $0 (with sending limits)
- **Twitter API Free Tier**: $0 (500K tweets/month)
- **YouTube API Free Tier**: $0 (10K units/day)

**Total MVP Cost**: $0/month (using free tiers)

For production, consider:
- Supabase Pro: $25/month
- Dedicated email service: $10-50/month
- Twitter API Pro: $100/month (if needed)

---

## Next Steps

After setting up all services:

1. Copy `.env.example` to `.env` in the backend directory
2. Fill in all the credentials you obtained
3. Run the database schema SQL in Supabase
4. Test the backend API connection
5. Start building Phase 2 features!

---

**Need Help?**
- Supabase: [https://supabase.com/docs](https://supabase.com/docs)
- Groq: [https://console.groq.com/docs](https://console.groq.com/docs)
- Twitter API: [https://developer.twitter.com/en/docs](https://developer.twitter.com/en/docs)
- YouTube API: [https://developers.google.com/youtube/v3](https://developers.google.com/youtube/v3)
