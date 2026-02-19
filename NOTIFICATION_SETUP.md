# Notification System - Quick Setup Guide

## 🚀 Quick Start

### 1. Install New Dependencies

```bash
cd backend
pip install Flask-Mail==0.9.1 twilio==9.0.4
```

### 2. Configure Environment (Optional but Recommended)

Copy the example environment file:
```bash
cp backend/.env.example backend/.env
```

Edit `.env` and add your credentials (see below for setup instructions).

### 3. Restart Backend

The new database tables will be created automatically:
```bash
python backend/app.py
```

You'll see notifications working in the app immediately! 

## ✉️ Email Setup (Optional)

### Using Gmail (Easiest):

1. Enable 2-factor authentication on your Google account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Add to `.env`:
```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-16-char-app-password
MAIL_DEFAULT_SENDER=noreply@jobmatch.com
```

### Alternative Email Providers:

**SendGrid**:
```bash
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USERNAME=apikey
MAIL_PASSWORD=your-sendgrid-api-key
```

**AWS SES**, **Mailgun**, etc. - check their SMTP settings

## 📱 SMS Setup (Optional - Twilio)

**Free Trial**: Twilio offers $15 trial credit (enough for ~500 SMS in India)

1. Sign up: https://www.twilio.com/try-twilio
2. Verify your phone number
3. Get a Twilio phone number from the console
4. Copy your credentials to `.env`:
```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890
```

**Note**: Without configuration, SMS will print to console (development mode)

## 🧪 Testing

### Test In-App Notifications:

1. Register two users (seeker and provider)
2. Provider posts a job
3. Seeker applies → Provider gets notification
4. Provider updates status → Seeker gets notification
5. Check notifications in the bell icon 🔔

### Test Email/SMS:

Use the test endpoint:
```bash
curl -X POST http://localhost:5000/test-notification \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","message":"Testing notifications"}'
```

## 📊 Features Available

✅ **In-App Notifications** - Always working (no setup needed)
✅ **Email Notifications** - Works after email config
✅ **SMS Notifications** - Works after Twilio config
✅ **Multi-language Support** - English, Tamil, Hindi
✅ **User Preferences** - Users can enable/disable channels
✅ **Priority Levels** - Urgent, High, Normal, Low
✅ **Real-time Updates** - Bell icon updates every 30 seconds

## 🎯 When Notifications are Sent

| Event | Recipient | Type | Priority |
|-------|-----------|------|----------|
| Application submitted | Provider | application_update | Normal |
| Status changed to "interview" | Seeker | application_update | High |
| Status changed to "accepted" | Seeker | application_update | High |
| Status changed (other) | Seeker | application_update | Normal |
| High match found (>70%) | Seeker | match | Normal |

## ⚙️ User Preferences

Users can control notifications at:
- API: `GET/PATCH /notification-preferences`
- Frontend: Will be in user settings (coming soon)

Default settings:
- Email: ✅ Enabled
- SMS: ✅ Enabled  
- In-App: ✅ Enabled
- All notification types: ✅ Enabled

## 🔧 Troubleshooting

**Notifications not showing up?**
- Check JWT token is valid
- Verify user is logged in
- Check browser console for errors

**Email not sending?**
- Verify SMTP credentials in `.env`
- Check spam/junk folder
- Look for error messages in terminal

**SMS not sending?**
- Verify Twilio credentials
- Check phone number format (+91XXXXXXXXXX for India)
- Verify Twilio account balance

**Development Mode:**
Without email/SMS configured, notifications will:
- ✅ Still create in-app notifications
- 📝 Print would-be email/SMS to terminal
- ⚠️ Mark sent_email/sent_sms as false

## 📚 Full Documentation

See [NOTIFICATIONS.md](./NOTIFICATIONS.md) for:
- Complete API documentation
- Advanced configuration
- Production deployment guide
- Security best practices
- Cost optimization tips

## 💰 Cost Estimates (Production)

**Email** (using SendGrid free tier):
- Free: 100 emails/day forever
- Paid: $15/month for 50,000 emails

**SMS** (using Twilio):
- India: ~₹0.50 per SMS
- Free trial: $15 credit (≈ 500 SMS)
- 1000 users × 5 notifications/month = 5000 SMS ≈ ₹2,500/month

**Recommendation**: Start with email only, add SMS for critical notifications

## 🎉 That's It!

The notification system is now fully integrated and working! Users will see the notification bell (🔔) in the navbar when logged in.

For questions or issues, check the full documentation in NOTIFICATIONS.md
