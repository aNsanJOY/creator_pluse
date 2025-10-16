# Email Delivery Guide

## Overview

Phase 8 implements a complete email delivery system for CreatorPulse newsletters with Gmail SMTP integration, rate limiting, delivery tracking, and compliance features.

## Features

### 1. Email Sending
- **Gmail SMTP Integration**: Secure email delivery via Gmail
- **HTML & Plain Text**: Dual-format emails for maximum compatibility
- **Batch Sending**: Send to multiple recipients with progress tracking
- **Background Processing**: Non-blocking email delivery

### 2. Rate Limiting
- **Daily Limits**: 
  - Regular Gmail: 500 emails/day (with 50 buffer = 450 usable)
  - Google Workspace: 2000 emails/day (with 50 buffer = 1950 usable)
- **Per-User Tracking**: Individual rate limits per user
- **Automatic Enforcement**: Prevents exceeding Gmail quotas

### 3. Delivery Tracking
- **Status Tracking**: queued → sending → sent/failed
- **Error Logging**: Detailed error messages for failed deliveries
- **Retry Counting**: Track retry attempts for failed sends
- **Delivery Timestamps**: Record when emails were sent

### 4. Unsubscribe Management
- **One-Click Unsubscribe**: Email links for easy unsubscription
- **Unsubscribe Page**: Branded confirmation page
- **Automatic Filtering**: Skip unsubscribed recipients
- **Compliance**: CAN-SPAM and GDPR compliant

### 5. Recipient Management
- **Recipient Lists**: Manage subscriber lists per user
- **Status Tracking**: active, unsubscribed, bounced
- **Metadata Storage**: Custom fields for segmentation

## API Endpoints

### Email Sending

#### POST /api/email/send
Send newsletter to recipients with rate limiting and tracking.

**Request:**
```json
{
  "draft_id": "uuid",
  "subject": "Newsletter Title",
  "recipient_emails": ["user1@example.com", "user2@example.com"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Email queued for delivery to 2 recipient(s)",
  "rate_limit": {
    "can_send": true,
    "current_count": 10,
    "daily_limit": 500,
    "remaining": 440,
    "requested": 2
  }
}
```

### Rate Limiting

#### GET /api/email/rate-limit
Check current rate limit status.

**Response:**
```json
{
  "success": true,
  "rate_limit": {
    "can_send": true,
    "current_count": 10,
    "daily_limit": 500,
    "remaining": 440,
    "requested": 1
  }
}
```

### Delivery Tracking

#### GET /api/email/delivery-logs
Get email delivery logs with filtering.

**Query Parameters:**
- `limit`: Number of logs to return (default: 50)
- `status_filter`: Filter by status (queued, sending, sent, failed, bounced)

**Response:**
```json
{
  "success": true,
  "logs": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "draft_id": "uuid",
      "recipient_email": "user@example.com",
      "subject": "Newsletter Title",
      "status": "sent",
      "error_message": null,
      "retry_count": 0,
      "sent_at": "2024-01-15T10:30:00Z",
      "created_at": "2024-01-15T10:29:55Z"
    }
  ],
  "total": 1
}
```

#### GET /api/email/stats
Get email delivery statistics.

**Query Parameters:**
- `days`: Number of days to include (default: 30)

**Response:**
```json
{
  "success": true,
  "stats": {
    "period_days": 30,
    "total_sent": 150,
    "total_failed": 5,
    "total_queued": 2,
    "total_attempts": 157,
    "success_rate": 95.54
  },
  "rate_limit": {
    "can_send": true,
    "current_count": 10,
    "daily_limit": 500,
    "remaining": 440,
    "requested": 1
  }
}
```

### Recipient Management

#### GET /api/email/recipients
List all recipients for the current user.

**Query Parameters:**
- `limit`: Number of recipients to return (default: 100)
- `status_filter`: Filter by status (active, unsubscribed, bounced)

#### POST /api/email/recipients
Add a new recipient.

**Request:**
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "metadata": {
    "source": "website_signup",
    "tags": ["premium"]
  }
}
```

#### DELETE /api/email/recipients/{recipient_id}
Remove a recipient from the list.

### Unsubscribe

#### GET /api/email/unsubscribe
Unsubscribe page (accessed from email link).

**Query Parameters:**
- `email`: Email address to unsubscribe
- `token`: Optional security token

**Returns:** HTML page with confirmation

#### POST /api/email/unsubscribe
API endpoint for unsubscribing.

**Request:**
```json
{
  "email": "user@example.com",
  "reason": "Too many emails"
}
```

#### GET /api/email/check-unsubscribed/{email}
Check if an email is unsubscribed.

## Database Schema

### email_delivery_log
Tracks all email delivery attempts.

```sql
- id: UUID (primary key)
- user_id: UUID (foreign key to users)
- draft_id: UUID (optional)
- recipient_email: VARCHAR(255)
- subject: VARCHAR(500)
- status: VARCHAR(50) (queued, sending, sent, failed, bounced)
- error_message: TEXT
- retry_count: INTEGER
- sent_at: TIMESTAMP
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

### unsubscribes
Stores unsubscribe requests.

```sql
- id: UUID (primary key)
- email: VARCHAR(255) (unique)
- user_id: UUID (optional, foreign key to users)
- reason: TEXT
- unsubscribed_at: TIMESTAMP
- created_at: TIMESTAMP
```

### email_rate_limits
Tracks daily email counts for rate limiting.

```sql
- id: UUID (primary key)
- user_id: UUID (foreign key to users)
- date: DATE
- email_count: INTEGER
- last_email_at: TIMESTAMP
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
- UNIQUE(user_id, date)
```

### recipients
Manages subscriber lists.

```sql
- id: UUID (primary key)
- user_id: UUID (foreign key to users)
- email: VARCHAR(255)
- name: VARCHAR(255)
- status: VARCHAR(50) (active, unsubscribed, bounced)
- metadata: JSONB
- subscribed_at: TIMESTAMP
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
- UNIQUE(user_id, email)
```

## Email Templates

### HTML Template
- Responsive design (max-width: 600px)
- Clean, modern styling
- Proper section formatting
- Unsubscribe link in footer
- Compliance text

### Plain Text Template
- Formatted for readability
- Section separators
- Unsubscribe link
- Compliance text

## Gmail Setup

### Prerequisites
1. Gmail account or Google Workspace account
2. 2-Factor Authentication enabled
3. App Password generated

### Configuration Steps

1. **Enable 2FA on Gmail:**
   - Go to Google Account Settings
   - Security → 2-Step Verification
   - Enable 2FA

2. **Generate App Password:**
   - Google Account → Security → App Passwords
   - Select "Mail" and "Other (Custom name)"
   - Copy the 16-character password

3. **Configure Environment Variables:**
   ```env
   GMAIL_EMAIL=your_email@gmail.com
   GMAIL_APP_PASSWORD=your_16_character_app_password
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   ```

## Rate Limiting Details

### Gmail Limits
- **Regular Gmail**: 500 emails/day
- **Google Workspace**: 2000 emails/day
- **Per-minute limit**: ~20 emails/minute (enforced by Gmail)

### Implementation
- Buffer of 50 emails kept for safety
- Per-user daily tracking
- Automatic reset at midnight (user's timezone)
- 100ms delay between emails to avoid rate limiting

### Handling Limit Exceeded
When limit is reached:
1. API returns 429 status code
2. Error message includes remaining count
3. Emails are not queued
4. User must wait until next day

## Error Handling

### Common Errors

1. **Authentication Failed**
   - Check Gmail credentials
   - Verify App Password is correct
   - Ensure 2FA is enabled

2. **Rate Limit Exceeded**
   - Wait until next day
   - Consider upgrading to Google Workspace
   - Use multiple Gmail accounts

3. **SMTP Connection Failed**
   - Check network connectivity
   - Verify SMTP host and port
   - Check firewall settings

4. **Recipient Rejected**
   - Invalid email address
   - Recipient's server blocked email
   - Email marked as spam

### Retry Logic
- Failed emails are logged with error message
- Retry count is tracked
- Maximum 3 retry attempts (configurable)
- Exponential backoff between retries

## Compliance

### CAN-SPAM Act
- ✅ Clear unsubscribe link in every email
- ✅ Physical address in footer (add to template)
- ✅ Accurate subject lines
- ✅ Honor unsubscribe requests immediately

### GDPR
- ✅ Explicit consent required for subscription
- ✅ Easy unsubscribe mechanism
- ✅ Data retention policies
- ✅ Right to be forgotten (delete recipient data)

## Best Practices

### Sending
1. **Warm Up New Accounts**: Start with small volumes
2. **Monitor Deliverability**: Track bounce and spam rates
3. **Clean Lists**: Remove bounced emails regularly
4. **Personalization**: Use recipient names when available
5. **Test Emails**: Send test emails before bulk sending

### Content
1. **Avoid Spam Triggers**: Don't use all caps, excessive punctuation
2. **Balance Text/Images**: Include plain text version
3. **Clear CTAs**: Make links and buttons obvious
4. **Mobile Responsive**: Test on mobile devices
5. **Unsubscribe Visible**: Make it easy to find

### Monitoring
1. **Track Metrics**: Open rates, click rates, bounces
2. **Review Logs**: Check delivery logs regularly
3. **Handle Bounces**: Remove hard bounces immediately
4. **Respond to Complaints**: Address spam complaints quickly
5. **Update Lists**: Keep recipient lists current

## Troubleshooting

### Emails Not Sending
1. Check Gmail credentials in `.env`
2. Verify App Password (not regular password)
3. Check rate limit status
4. Review delivery logs for errors
5. Test SMTP connection manually

### High Failure Rate
1. Validate email addresses before sending
2. Check for spam content in emails
3. Verify sender reputation
4. Review bounce reasons in logs
5. Consider using email validation service

### Rate Limit Issues
1. Monitor daily email count
2. Spread sends throughout the day
3. Upgrade to Google Workspace if needed
4. Use multiple sender accounts
5. Implement queuing system for large batches

## Future Enhancements

### Planned Features
- [ ] Email templates library
- [ ] A/B testing support
- [ ] Advanced analytics (open/click tracking)
- [ ] Bounce handling automation
- [ ] Email validation service integration
- [ ] Multiple sender account support
- [ ] Scheduled sending
- [ ] Segmentation and targeting
- [ ] Email preview testing
- [ ] Spam score checking

### Scalability
For high-volume sending:
1. Consider dedicated email service (SendGrid, Mailgun, AWS SES)
2. Implement proper queuing (Celery, RabbitMQ)
3. Add email warming strategy
4. Use dedicated IP addresses
5. Implement feedback loops

## Support

For issues or questions:
1. Check delivery logs: `GET /api/email/delivery-logs`
2. Review rate limit: `GET /api/email/rate-limit`
3. Check email stats: `GET /api/email/stats`
4. Review documentation
5. Contact support team
