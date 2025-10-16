-- Email Delivery Tracking and Unsubscribe Management
-- Migration 003: Add tables for tracking email delivery and managing unsubscribes

-- Email delivery log table
CREATE TABLE IF NOT EXISTS email_delivery_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    draft_id UUID,
    recipient_email VARCHAR(255) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('queued', 'sending', 'sent', 'failed', 'bounced')),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Unsubscribe list table
CREATE TABLE IF NOT EXISTS unsubscribes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    reason TEXT,
    unsubscribed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Email rate limiting tracking table
CREATE TABLE IF NOT EXISTS email_rate_limits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    email_count INTEGER DEFAULT 0,
    last_email_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, date)
);

-- Recipient list table (for managing subscriber lists)
CREATE TABLE IF NOT EXISTS recipients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'unsubscribed', 'bounced')),
    metadata JSONB DEFAULT '{}',
    subscribed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, email)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_email_delivery_log_user_id ON email_delivery_log(user_id);
CREATE INDEX IF NOT EXISTS idx_email_delivery_log_draft_id ON email_delivery_log(draft_id);
CREATE INDEX IF NOT EXISTS idx_email_delivery_log_status ON email_delivery_log(status);
CREATE INDEX IF NOT EXISTS idx_email_delivery_log_created_at ON email_delivery_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_unsubscribes_email ON unsubscribes(email);
CREATE INDEX IF NOT EXISTS idx_email_rate_limits_user_date ON email_rate_limits(user_id, date);
CREATE INDEX IF NOT EXISTS idx_recipients_user_id ON recipients(user_id);
CREATE INDEX IF NOT EXISTS idx_recipients_email ON recipients(email);
CREATE INDEX IF NOT EXISTS idx_recipients_status ON recipients(status);

-- Create triggers for updated_at
CREATE TRIGGER update_email_delivery_log_updated_at BEFORE UPDATE ON email_delivery_log
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_email_rate_limits_updated_at BEFORE UPDATE ON email_rate_limits
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_recipients_updated_at BEFORE UPDATE ON recipients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE email_delivery_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE unsubscribes ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_rate_limits ENABLE ROW LEVEL SECURITY;
ALTER TABLE recipients ENABLE ROW LEVEL SECURITY;

-- RLS Policies for email_delivery_log table
CREATE POLICY "Users can view their own email logs" ON email_delivery_log
    FOR SELECT USING (auth.uid() = user_id);

-- RLS Policies for unsubscribes table (public read for checking, admin write)
CREATE POLICY "Anyone can check unsubscribe status" ON unsubscribes
    FOR SELECT USING (true);

-- RLS Policies for email_rate_limits table
CREATE POLICY "Users can view their own rate limits" ON email_rate_limits
    FOR SELECT USING (auth.uid() = user_id);

-- RLS Policies for recipients table
CREATE POLICY "Users can view their own recipients" ON recipients
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own recipients" ON recipients
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own recipients" ON recipients
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own recipients" ON recipients
    FOR DELETE USING (auth.uid() = user_id);

-- Comments for documentation
COMMENT ON TABLE email_delivery_log IS 'Tracks all email delivery attempts and their status';
COMMENT ON TABLE unsubscribes IS 'Stores unsubscribe requests from recipients';
COMMENT ON TABLE email_rate_limits IS 'Tracks daily email sending counts per user for rate limiting';
COMMENT ON TABLE recipients IS 'Manages subscriber lists for each user';
