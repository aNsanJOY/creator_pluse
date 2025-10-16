# CreatorPulse Implementation Plan

## Overview
This plan breaks down the CreatorPulse MVP development into actionable phases with trackable checkboxes. The goal is to deliver a working product within 3 months that allows creators to review and send newsletters in under 20 minutes.

**Tech Stack:**
- **Frontend:** React with shadcn/ui components, TailwindCSS, and Lucide icons
- **Backend:** FastAPI (Python) - handles all business logic and database operations
- **Database:** Supabase (PostgreSQL)
- **Authentication:** Supabase Auth (accessed via FastAPI)
- **Email:** Gmail SMTP (using your Gmail account)
- **AI/LLM:** Groq

**Architecture:**
- React frontend communicates with FastAPI backend via REST API
- All database operations are performed through FastAPI (no direct DB calls from React)
- FastAPI handles authentication, source crawling, LLM interactions, and email delivery
- Background tasks for scheduled crawling and draft generation (APScheduler/Celery)

**Note:** All SQL schema files and database migrations are stored in `backend/database_migrations/`

---

## Phase 1: Project Setup & Infrastructure (Week 1-2)

### 1.1 Development Environment
- [✅] Initialize Git repository with proper .gitignore
- [✅] Set up project structure (frontend/backend separation)
- [✅] Configure development environment variables
- [✅] Set up code linting and formatting (ESLint, Prettier)
- [✅] Create README with setup instructions

### 1.2 Backend Infrastructure (FastAPI)
- [✅] Initialize FastAPI project structure
- [✅] Set up virtual environment and dependencies (requirements.txt)
- [✅] Configure CORS for React frontend
- [✅] Set up environment variables (.env)
- [✅] Create API router structure
- [✅] Set up Supabase Python client
- [✅] Configure Supabase authentication (email-based)
- [✅] Design and create database schema:
  - [✅] Users table
  - [✅] Sources table (Twitter, YouTube, RSS)
  - [✅] Newsletters table (drafts and sent)
  - [✅] Feedback table (thumbs up/down)
  - [✅] Source content cache table
- [✅] Create database models (SQLAlchemy/Pydantic)
- [✅] Set up database migrations (Alembic)

### 1.3 Frontend Infrastructure
- [✅] Initialize React project (Vite/Next.js)
- [✅] Install and configure TailwindCSS
- [✅] Set up shadcn/ui components
- [✅] Install Lucide icons
- [✅] Configure routing (React Router/Next.js routing)
- [✅] Set up Axios/Fetch API client for FastAPI backend
- [✅] Create API service layer for backend communication
- [✅] Set up authentication token management (localStorage/cookies)

### 1.4 External Services Setup
- [✅] Set up Gmail SMTP for email delivery
- [✅] Enable 2-factor authentication on Gmail account
- [✅] Generate Gmail App Password for SMTP access
- [✅] Configure SMTP settings in FastAPI (.env file)
- [✅] Set up Groq API access and configure API key
- [✅] Configure Twitter API access
- [✅] Configure YouTube API access
- [✅] Set up RSS feed parser (feedparser library)

---

## Phase 2: Authentication & User Management (Week 2-3)

### 2.1 Authentication Flow (FastAPI Backend)
- [✅] Create FastAPI endpoints for auth:
  - [✅] POST /api/auth/signup (register user)
  - [✅] POST /api/auth/login (authenticate user)
  - [✅] POST /api/auth/logout
  - [✅] POST /api/auth/reset-password
- [✅] Implement JWT token generation and validation
- [✅] Create authentication middleware for protected routes
- [✅] Set up Supabase Auth integration in FastAPI

### 2.2 Authentication UI (React Frontend)
- [✅] Create signup page without email verification
- [✅] Create login page
- [✅] Implement password reset flow
- [✅] Add protected route middleware (check JWT)
- [✅] Create user session management (context/state)
- [✅] Add logout functionality

### 2.3 User Profile
- [✅] Create FastAPI endpoints:
  - [✅] GET /api/user/profile
  - [✅] PUT /api/user/profile (update profile)
  - [✅] DELETE /api/user/account
- [✅] Create user profile page (React)
- [✅] Implement account deletion option with confirmation dialog

---

## Phase 3: Source Connection System (Week 3-4)

### 3.1 Source Management Backend (FastAPI)
- [✅] Create FastAPI endpoints:
  - [✅] GET /api/sources (list all user sources)
  - [✅] POST /api/sources (add new source)
  - [✅] DELETE /api/sources/{id} (remove source)
  - [✅] GET /api/sources/{id}/status (check source status)
- [✅] Implement source validation logic
- [✅] Store source credentials securely in database

### 3.2 Source Management UI (React)
- [✅] Create sources dashboard page
- [✅] Design source connection cards (Twitter, YouTube, RSS)
- [✅] Add source connection modal/form
- [✅] Display connected sources list
- [✅] Add source removal functionality
- [✅] Show source status (active/error)

### 3.3 Twitter Integration (FastAPI Backend)
- [✅] Create FastAPI endpoint: POST /api/sources/twitter/oauth
- [✅] Implement Twitter OAuth flow
- [✅] Store Twitter access tokens securely in database
- [✅] Create Twitter content crawler (background task)
- [✅] Implement rate limit handling
- [✅] Add delta crawl logic (fetch only new content)
- [✅] Store crawled tweets in cache table

### 3.4 YouTube Integration (FastAPI Backend)
- [✅] Create FastAPI endpoint: POST /api/sources/youtube/oauth
- [✅] Implement YouTube OAuth flow
- [✅] Store YouTube access tokens securely in database
- [✅] Create YouTube content crawler (background task)
- [✅] Implement rate limit handling
- [✅] Add delta crawl logic (fetch only new videos)
- [✅] Store video metadata and transcripts in cache

### 3.5 RSS Integration (FastAPI Backend)
- [✅] Create FastAPI endpoint: POST /api/sources/rss
- [✅] Create RSS feed parser using feedparser
- [✅] Add RSS feed validation
- [✅] Implement RSS content crawler (background task)
- [✅] Store RSS items in cache table
- [✅] Handle various RSS formats (RSS 2.0, Atom)

### 3.6 Extensible Source System (FastAPI Backend)
- [✅] Design plugin-based architecture for new source types
- [✅] Create abstract base class for source connectors
- [✅] Implement source type registry system
- [✅] Add support for custom source types (Substack, Medium, LinkedIn, etc.)
- [✅] Create generic webhook endpoint for push-based sources
- [✅] Document how to add new source types
- [✅] Add source type configuration in database (flexible JSONB fields)

---

## Phase 4: Voice Training System (Week 4-5)

### 4.1 Newsletter Upload Backend (FastAPI)
- [✅] Create FastAPI endpoints:
  - [✅] POST /api/newsletters/upload (upload file or text)
  - [✅] GET /api/newsletters/samples (list uploaded samples)
  - [✅] DELETE /api/newsletters/samples/{id}
- [✅] Support multiple file formats (txt, md, html)
- [✅] Store uploaded newsletters in database

### 4.2 Newsletter Upload UI (React)
- [✅] Create newsletter upload page
- [✅] Support file upload and paste text directly
- [✅] Display uploaded newsletters list
- [✅] Add delete uploaded newsletter functionality

### 4.3 Voice Analysis (FastAPI Backend with Groq)
- [✅] Create FastAPI endpoint: POST /api/voice/analyze
- [✅] Create prompt for extracting writing style
- [✅] Implement Groq LLM-based style analysis
- [✅] Store style profile per user in database
- [✅] Create fallback tone for insufficient data
- [ ] Test style matching accuracy (≥70% target)

---

## Phase 5: Content Aggregation & Trend Detection (Week 5-6)

### 5.1 Scheduled Crawling (FastAPI Backend)
- [✅] Set up cron job/scheduled task for daily crawls (APScheduler or Celery)
- [✅] Implement crawl orchestration (Twitter → YouTube → RSS)
- [✅] Add error handling and retry logic
- [✅] Log crawl status and errors to database
- [✅] Send admin alerts on critical failures
- [✅] Create manual crawl trigger endpoint: POST /api/crawl/trigger
- [✅] Create crawl logs endpoint: GET /api/crawl/logs
- [✅] Create crawl stats endpoint: GET /api/crawl/stats
- [✅] Create crawl status endpoint: GET /api/crawl/status
- [✅] Create source reactivation endpoint: POST /api/crawl/reactivate/{source_id}
- [✅] Create bulk reactivation endpoint: POST /api/crawl/reactivate-all

### 5.2 Trend Detection Algorithm (FastAPI Backend)
- [✅] Create FastAPI endpoint: POST /api/trends/detect
- [✅] Implement topic extraction from content using Groq
- [✅] Create trend scoring algorithm (frequency, recency, engagement)
- [✅] Implement ensemble detection (multiple signals)
- [✅] Add manual override flag for trends
- [✅] Store detected trends in database
- [ ] Test for false positive rate

### 5.3 Content Summarization (FastAPI Backend with Groq)
- [✅] Create FastAPI endpoint: POST /api/content/summarize
- [✅] Create prompt for summarizing source content
- [✅] Implement Groq LLM-based summarization
- [✅] Generate structured summaries (title, key points, link)
- [✅] Store summaries linked to source content in database

---

## Phase 6: Newsletter Draft Generation (Week 6-7)

### 6.1 Draft Generation Engine (FastAPI Backend with Groq)
- [✅] Create FastAPI endpoint: POST /api/drafts/generate
- [✅] Design newsletter structure (intro, links, summaries, commentary)
- [✅] Create main draft generation prompt for Groq
- [✅] Implement style adaptation from user voice profile
- [✅] Generate draft with top 5-7 trending topics
- [✅] Add fallback to plain summaries on errors
- [✅] Store generated drafts in database

### 6.2 Scheduled Draft Delivery (FastAPI Backend)
- [✅] Set up scheduled task for 8:00 AM local time (APScheduler)
- [✅] Create background job to generate draft for each active user
- [✅] Create FastAPI endpoint: POST /api/drafts/send-email
- [✅] Send draft via email with review link
- [✅] Track draft delivery status in database
- [✅] Handle timezone conversions correctly

### 6.3 Draft Review Backend (FastAPI)
- [✅] Create FastAPI endpoints:
  - [✅] GET /api/drafts/{id} (fetch draft)
  - [✅] PUT /api/drafts/{id} (update draft)
  - [✅] POST /api/drafts/{id}/publish (send newsletter)
  - [✅] POST /api/drafts/{id}/regenerate

### 6.4 Draft Review Interface (React)
- [✅] Create draft review page (web app)
- [✅] Display draft with formatting preview
- [✅] Add inline editing capability
- [✅] Show source links for each section
- [✅] Add "Send Now" button
- [✅] Add "Save Draft" button
- [✅] Add "Regenerate" option

---

## Phase 7: Feedback Loop (Week 7-8)

### 7.1 Feedback Collection Backend (FastAPI)
- [✅] Create FastAPI endpoints:
  - [✅] POST /api/feedback (submit feedback)
  - [✅] GET /api/feedback/user/{user_id} (get user feedback history)
  - [✅] GET /api/feedback/newsletter/{newsletter_id} (get newsletter feedback)
  - [✅] GET /api/feedback/stats (get user feedback statistics)
  - [✅] PUT /api/feedback/{feedback_id} (update feedback)
  - [✅] DELETE /api/feedback/{feedback_id} (delete feedback)
- [✅] Store feedback in database (linked to draft and section)
- [✅] Track feedback over time per user

### 7.2 Feedback Collection UI (React)
- [✅] Add thumbs up/down buttons to each draft section
- [✅] Add optional text feedback field
- [✅] Send feedback to backend API
- [✅] Create FeedbackButtons component with thumbs up/down
- [✅] Create FeedbackStats component for dashboard
- [✅] Integrate feedback UI into DraftReview page

### 7.3 Feedback Integration (FastAPI Backend with Groq)
- [✅] Create prompt adjustment based on feedback
- [✅] Implement feedback-driven style refinement using Groq
- [✅] Create FeedbackAnalyzer service for analyzing feedback patterns
- [✅] Integrate feedback insights into draft generation
- [ ] Update user voice profile based on feedback patterns
- [ ] Test improved draft quality after feedback
- [ ] Monitor draft acceptance rate (≥70% target)

---

## Phase 8: Newsletter Publishing (Week 8-9)

### 8.1 Email Delivery (FastAPI Backend with Gmail SMTP)
- [✅] Create FastAPI endpoint: POST /api/email/send
- [✅] Install email library (smtplib or python-email-validator)
- [✅] Configure Gmail SMTP connection (smtp.gmail.com:587)
- [✅] Implement email sending with TLS/SSL
- [✅] Create email template with proper formatting (HTML/plain text)
- [✅] Implement batch sending for multiple recipients
- [✅] Handle email delivery errors gracefully (connection, authentication, quota)
- [✅] Track email delivery status (sent, failed) in database
- [✅] Implement retry logic for failed sends

### 8.2 Deliverability Optimization (Gmail SMTP)
- [✅] Be aware of Gmail sending limits (500 emails/day for regular accounts, 2000/day for Google Workspace)
- [✅] Implement rate limiting to stay within Gmail quotas
- [✅] Implement unsubscribe mechanism
- [✅] Add email footer with compliance info
- [✅] Monitor for "suspicious activity" warnings from Gmail
- [✅] Consider using multiple Gmail accounts or upgrading to Google Workspace for higher limits
---

## Phase 9: Dashboard (Optional - Week 9-10)

### 9.1 Dashboard Backend (FastAPI)
- [✅] Create FastAPI endpoints:
  - [✅] GET /api/dashboard/stats (overview statistics)
  - [✅] GET /api/dashboard/recent-drafts
  - [✅] GET /api/dashboard/recent-newsletters
  - [✅] GET /api/dashboard/activity (recent activity timeline)

### 9.2 Dashboard UI (React)
- [✅] Create main dashboard page
- [✅] Display recent drafts and sent newsletters
- [✅] Display connected sources summary
- [✅] Add quick actions (connect source, view draft)
- [✅] Show real-time statistics (sources, drafts, content, emails)
- [✅] Display voice training status

### 9.3 Preferences Backend (FastAPI)
- [✅] Create FastAPI endpoints:
  - [✅] GET /api/preferences
  - [✅] PUT /api/preferences (update user preferences)
  - [✅] POST /api/preferences/reset (reset to defaults)
- [✅] Store preferences in database

### 9.4 Preferences UI (React)
- [✅] Create preferences page
- [✅] Add draft schedule customization
- [✅] Configure newsletter frequency
- [✅] Set content preferences (topics to include/exclude)
- [✅] Adjust tone/style preferences
- [✅] Configure notification preferences
- [✅] Set email delivery preferences

### 9.5 Billing (Future)
- [ ] Design pricing tiers
- [ ] Create FastAPI endpoints for Stripe integration
- [ ] Integrate payment processor (Stripe)
- [ ] Create billing page (React)
- [ ] Implement usage tracking
- [ ] Add subscription management

---

## Phase 10: Testing & Quality Assurance (Week 10-11)

### 10.1 Unit Testing (FastAPI Backend)
- [ ] Set up pytest for FastAPI testing
- [ ] Write tests for authentication endpoints
- [ ] Write tests for source crawlers
- [ ] Write tests for trend detection algorithms
- [ ] Write tests for draft generation with Groq
- [ ] Write tests for feedback processing
- [ ] Achieve ≥80% code coverage for backend

### 10.2 Integration Testing
- [ ] Test end-to-end user journey (React → FastAPI → Database)
- [ ] Test source connection flows (OAuth callbacks)
- [ ] Test draft generation and delivery pipeline
- [ ] Test email sending and tracking
- [ ] Test feedback loop (UI → API → Groq refinement)
- [ ] Test React component integration

### 10.3 Performance Testing
- [ ] Test Groq API latency (P50 < 10s, P95 < 30s)
- [ ] Test FastAPI concurrent request handling
- [ ] Test database query performance (Supabase)
- [ ] Optimize slow queries with indexes
- [ ] Test email delivery at scale
- [ ] Load test API endpoints

### 10.4 Offline Testing (Groq LLM)
- [ ] Create golden set of sample drafts
- [ ] Evaluate tone accuracy with Groq (≥70% match target)
- [ ] Test style adaptation with various inputs
- [ ] Validate trend detection accuracy
- [ ] Test prompt variations for quality

---

## Phase 11: Security & Compliance (Week 11-12)

### 11.1 Security Hardening (FastAPI)
- [ ] Implement API rate limiting (slowapi or custom middleware)
- [ ] Add input validation with Pydantic models
- [ ] Add request sanitization
- [ ] Encrypt sensitive data at rest (database encryption)
- [ ] Use secure token storage for OAuth tokens
- [ ] Implement CSRF protection for state-changing endpoints
- [ ] Configure CORS properly for React frontend
- [ ] Add security headers (CSP, X-Frame-Options, etc.)
- [ ] Implement JWT token expiration and refresh
- [ ] Conduct security audit

### 11.2 Privacy & GDPR Compliance
- [ ] Create FastAPI endpoints:
  - [ ] GET /api/user/export-data (GDPR data export)
  - [ ] POST /api/user/delete-data (GDPR right to be forgotten)
- [ ] Create privacy policy page (React)
- [ ] Create terms of service page (React)
- [ ] Implement data retention policy (90 days for cache)
- [ ] Implement cookie consent banner (React)
- [ ] Add audit logging for data access in backend

---

## Phase 12: Private Beta Launch (Week 12)

### 12.1 Beta Preparation
- [ ] Create onboarding documentation
- [ ] Prepare beta user invitation emails
- [ ] Set up feedback collection mechanism
- [ ] Create support channel (email/Discord)
- [ ] Prepare monitoring dashboard

### 12.2 Beta User Recruitment
- [ ] Identify 10-20 target creators
- [ ] Send beta invitations
- [ ] Onboard beta users
- [ ] Provide setup assistance

### 12.3 Beta Monitoring
- [ ] Monitor system health and errors
- [ ] Track key metrics (draft acceptance, review time)
- [ ] Collect user feedback weekly
- [ ] Fix critical bugs within 24 hours
- [ ] Iterate on feedback

---

## Phase 13: Public MVP Launch (Week 13+)

### 13.1 Pre-Launch
- [ ] Create landing page
- [ ] Set up analytics (Google Analytics/Plausible)
- [ ] Prepare launch announcement
- [ ] Create demo video
- [ ] Write launch blog post

### 13.2 Launch
- [ ] Open public signup
- [ ] Post on Product Hunt
- [ ] Share on social media
- [ ] Reach out to creator communities
- [ ] Monitor signup and activation rates

### 13.3 Post-Launch
- [ ] Monitor system performance and errors
- [ ] Respond to user support requests
- [ ] Track KPIs (review time, acceptance rate, engagement uplift)
- [ ] Collect user testimonials
- [ ] Plan v2 features based on feedback

---

## Ongoing Tasks

### Maintenance
- [ ] Weekly system health checks
- [ ] Monthly security updates
- [ ] Regular dependency updates
- [ ] Database backup verification
- [ ] Cost monitoring and optimization

### Monitoring
- [ ] Track draft acceptance rate (target: ≥70%)
- [ ] Track average review time (target: ≤20 min)
- [ ] Track engagement uplift (target: ≥2× baseline)
- [ ] Monitor API costs (LLM, email, social APIs)
- [ ] Track user retention and churn

### Documentation
- [ ] Maintain API documentation
- [ ] Update user guides
- [ ] Document architecture decisions
- [ ] Create troubleshooting guides
- [ ] Update changelog

---

## Risk Mitigation Checklist

### API Rate Limits
- [ ] Implement caching layer
- [ ] Add delta crawl logic
- [ ] Create back-off queue system
- [ ] Monitor rate limit usage
- [ ] Set up alerts for approaching limits

### Voice Mismatch
- [ ] Implement human-in-loop feedback
- [ ] Create retrain path for style updates
- [ ] Add manual tone adjustment controls
- [ ] Test with diverse writing styles

### Trend False Positives
- [ ] Implement ensemble detection
- [ ] Add manual override flag
- [ ] Create trend quality scoring
- [ ] Allow user to mark irrelevant trends

### Email Deliverability
- [ ] Use verified sender domains
- [ ] Implement batch sending
- [ ] Monitor bounce rates
- [ ] Test across email providers
- [ ] Maintain sender reputation

---

## Success Metrics Tracking

### 90-Day Targets
- [ ] Average review time per draft ≤ 20 minutes
- [ ] Draft acceptance rate ≥ 70%
- [ ] Median open/CTR uplift ≥ 2× baseline
- [ ] 60%+ users see engagement uplift
- [ ] System uptime ≥ 99.5%

---

## Notes
- This plan assumes a 3-month MVP timeline
- Adjust timelines based on team size and resources
- Dashboard features are optional for MVP
- Focus on core workflow: connect sources → generate draft → review → send
- Prioritize user feedback over feature completeness
