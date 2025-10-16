-- Newsletter drafts table
CREATE TABLE newsletter_drafts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  sections JSONB NOT NULL,
  status TEXT NOT NULL DEFAULT 'ready',
  metadata JSONB DEFAULT '{}',
  generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  published_at TIMESTAMP WITH TIME ZONE,
  email_sent BOOLEAN DEFAULT FALSE,
  email_sent_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_newsletter_drafts_user_id ON newsletter_drafts(user_id);
CREATE INDEX idx_newsletter_drafts_status ON newsletter_drafts(status);

-- User preferences table (if not exists)
CREATE TABLE user_preferences (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
  preferences JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Draft generation logs (optional, for monitoring)
CREATE TABLE draft_generation_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  success_count INTEGER DEFAULT 0,
  error_count INTEGER DEFAULT 0,
  total_count INTEGER DEFAULT 0
);
