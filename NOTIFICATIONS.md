# Notification System Documentation

## Overview

The JobMatch notification system provides multi-channel alerts for job seekers and providers through:
- **In-app notifications** - Real-time notifications within the application
- **Email notifications** - Detailed email alerts with HTML formatting
- **SMS notifications** - Concise text messages for low-data rural users

## Features

### Notification Types

1. **Job Match Notifications** (`match`)
   - Sent to job seekers when high-quality job matches (>70%) are found
   - Includes match percentage and distance information

2. **Application Updates** (`application_update`)
   - Sent when application status changes (reviewed, shortlisted, interview, accepted, rejected)
   - Notifies providers when new applications are received

3. **Interview Invitations** (`interview`)
   - Sent when candidates are invited for interviews
   - Includes date, time, and location details

4. **Deadline Reminders** (`deadline`)
   - Reminds users about approaching application deadlines

### Multi-Channel Delivery

- **In-App**: Always delivered, stored in database, accessible via UI
- **Email**: Sends HTML-formatted emails with full details
- **SMS**: Sends concise text messages (160 chars max) optimized for rural users with limited data

## Backend Setup

### 1. Install Dependencies

```bash
pip install Flask-Mail twilio
```

Or install from requirements.txt:
```bash
pip install -r backend/requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the backend directory:

```bash
# Email Configuration (Gmail example)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@jobmatch.com

# Twilio SMS Configuration
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=+1234567890
```

#### Email Setup (Gmail)

1. Go to Google Account settings
2. Enable 2-factor authentication
3. Generate an App Password: https://myaccount.google.com/apppasswords
4. Use the generated password as `MAIL_PASSWORD`

#### SMS Setup (Twilio)

1. Sign up for Twilio: https://www.twilio.com/try-twilio
2. Get a phone number from Twilio console
3. Copy your Account SID and Auth Token
4. Add credentials to `.env` file

**Note**: Twilio free tier includes trial credits. For production, you'll need a paid plan.

### 3. Database Migration

The notification tables will be created automatically when you run the app:

```bash
python backend/app.py
```

This creates two new tables:
- `notification` - Stores all notifications
- `notification_preference` - Stores user notification preferences

## API Endpoints

### Get Notifications
```http
GET /notifications?unread_only=false&limit=50
Authorization: Bearer <token>
```

Response:
```json
{
  "notifications": [
    {
      "notification_id": 1,
      "notification_type": "match",
      "title": "New Job Match Found!",
      "message": "You have a 85% match with 'Paddy Field Worker'...",
      "priority": "normal",
      "is_read": false,
      "sent_email": true,
      "sent_sms": true,
      "created_at": "2026-02-19T10:30:00"
    }
  ],
  "unread_count": 5
}
```

### Mark Notification as Read
```http
PATCH /notifications/<notification_id>/read
Authorization: Bearer <token>
```

### Mark All Notifications as Read
```http
PATCH /notifications/read-all
Authorization: Bearer <token>
```

### Delete Notification
```http
DELETE /notifications/<notification_id>
Authorization: Bearer <token>
```

### Get Notification Preferences
```http
GET /notification-preferences
Authorization: Bearer <token>
```

Response:
```json
{
  "email_enabled": true,
  "sms_enabled": true,
  "app_enabled": true,
  "notify_on_match": true,
  "notify_on_application_update": true,
  "notify_on_interview": true,
  "notify_on_deadline": true
}
```

### Update Notification Preferences
```http
PATCH /notification-preferences
Authorization: Bearer <token>
Content-Type: application/json

{
  "email_enabled": false,
  "sms_enabled": true,
  "notify_on_match": true
}
```

### Test Notification (Development)
```http
POST /test-notification
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Test Notification",
  "message": "This is a test message"
}
```

## Frontend Integration

### NotificationBell Component

The notification bell appears in the navbar when a user is logged in:

```jsx
import NotificationBell from "./components/NotificationBell";

// In your Navbar component
{isLoggedIn && <NotificationBell t={t} />}
```

Features:
- Shows unread count badge
- Dropdown with recent notifications
- Click to mark as read
- Delete individual notifications
- Auto-refreshes every 30 seconds
- Priority indicators (urgent, high, normal, low)

### Styling

The NotificationBell component includes responsive CSS that adapts to mobile devices.

## Workflow Integration

### When Application is Created

Provider receives notification:
- In-app notification
- Email with applicant details
- SMS (if enabled)

### When Application Status Changes

Job seeker receives notification:
- Status update notification
- Priority: HIGH for "interview" and "accepted" status
- Priority: NORMAL for other statuses

### When High Matches are Found

Call `/match_jobs/<seeker_id>?notify=true` to send notifications for top matches (>70% score).

## SMS Optimization for Rural Users

SMS messages are automatically optimized:
- Maximum 160 characters per message
- Concise, actionable content
- Phone numbers auto-formatted to E.164 (+91 for India)
- Critical information prioritized

Example SMS:
```
New Job Match Found!: You have a 85% match with 'Paddy Field Worker' (12.3 km away). Login to apply now!
```

## Testing

### Test Email Configuration

```bash
# Send a test email
curl -X POST http://localhost:5000/test-notification \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Email","message":"Testing email notifications"}'
```

### Test SMS Configuration

Register a job seeker with a valid mobile number and update an application status to trigger SMS.

### Development Mode

Without email/SMS configuration, notifications will:
- Always create in-app notifications
- Print would-be email/SMS to console
- Mark `sent_email` and `sent_sms` as false

## Best Practices

1. **Rate Limiting**: Consider adding rate limiting to prevent notification spam
2. **Batch Notifications**: Group similar notifications to avoid overwhelming users
3. **User Preferences**: Always respect user notification preferences
4. **Priority Levels**: Use appropriate priority levels:
   - `urgent`: Critical actions (interview today, deadline in hours)
   - `high`: Important updates (interview scheduled, accepted)
   - `normal`: Regular updates (new match, status change)
   - `low`: Minor updates (profile views, tips)

4. **SMS Costs**: Monitor SMS usage for cost control (Twilio charges per message)
5. **Error Handling**: Log failed notifications for retry/debugging

## Troubleshooting

### Email Not Sending

1. Check environment variables are loaded
2. Verify SMTP credentials
3. Check firewall/network restrictions on port 587
4. For Gmail, ensure "Less secure app access" or use App Password

### SMS Not Sending

1. Verify Twilio credentials
2. Check phone number format (E.164: +919876543210)
3. Ensure sender number is verified in Twilio
4. Check Twilio account balance

### Notifications Not Appearing in UI

1. Check JWT token is valid
2. Verify user is logged in
3. Check browser console for errors
4. Verify API endpoints are accessible

## Security Considerations

1. **Environment Variables**: Never commit credentials to version control
2. **Token Security**: Use HTTPS in production
3. **Rate Limiting**: Implement to prevent abuse
4. **Data Privacy**: Ensure compliance with local data protection laws
5. **SMS Security**: Validate phone numbers before storing

## Production Deployment

1. Use environment variables for all credentials
2. Enable HTTPS for secure token transmission
3. Set up proper logging and monitoring
4. Configure production email service (SendGrid, AWS SES, etc.)
5. Monitor SMS costs and set billing alerts
6. Implement notification archiving/cleanup for old notifications
7. Set up error alerting for failed notifications

## Future Enhancements

- Push notifications for mobile apps
- WhatsApp integration (via Twilio)
- Notification scheduling
- Digest emails (daily/weekly summaries)
- Rich media notifications (images, documents)
- WebSocket support for real-time updates
- Notification analytics and engagement tracking
