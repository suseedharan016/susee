"""
Notification Service for JobMatch
Handles Email and SMS notifications for rural job seekers
"""
import os
from typing import Optional
from flask_mail import Mail, Message
from twilio.rest import Client


# Email configuration
mail = None


def init_mail(app):
    """Initialize Flask-Mail with app config"""
    global mail
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@jobmatch.com')
    mail = Mail(app)
    return mail


# Twilio configuration
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')


def get_twilio_client() -> Optional[Client]:
    """Get Twilio client if credentials are configured"""
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
        return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    return None


def send_email(to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
    """
    Send email notification
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Plain text email body
        html_body: Optional HTML email body
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    try:
        if not mail:
            print("Email not configured. Would send email:")
            print(f"To: {to_email}\nSubject: {subject}\nBody: {body}")
            return False
            
        msg = Message(subject=subject, recipients=[to_email])
        msg.body = body
        if html_body:
            msg.html = html_body
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False


def send_sms(to_phone: str, message: str) -> bool:
    """
    Send SMS notification via Twilio
    
    Args:
        to_phone: Recipient phone number (E.164 format, e.g., +919876543210)
        message: SMS message text (max 160 chars recommended)
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    try:
        client = get_twilio_client()
        if not client or not TWILIO_PHONE_NUMBER:
            print("SMS not configured. Would send SMS:")
            print(f"To: {to_phone}\nMessage: {message}")
            return False
        
        # Clean up phone number - remove spaces, dashes, parentheses
        to_phone = to_phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        # Ensure phone number is in E.164 format
        if not to_phone.startswith('+'):
            # Assume Indian number if no country code
            to_phone = f"+91{to_phone.lstrip('0')}"
            
        # Validate phone number format (minimum 10 digits after country code)
        phone_digits = ''.join(filter(str.isdigit, to_phone))
        if len(phone_digits) < 10:
            print(f"Invalid phone number (too short): {to_phone}")
            return False
            
        sms_response = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone
        )
        print(f"SMS sent successfully: {sms_response.sid}")
        return True
    except Exception as e:
        print(f"Failed to send SMS: {str(e)}")
        return False


def format_sms_for_rural(title: str, message: str, max_length: int = 160) -> str:
    """
    Format SMS message for rural users with limited data
    Keep it concise and in simple language
    
    Args:
        title: Notification title
        message: Full message
        max_length: Maximum SMS length
        
    Returns:
        str: Formatted SMS message
    """
    # Try to fit both title and message
    combined = f"{title}: {message}"
    if len(combined) <= max_length:
        return combined
    
    # If too long, truncate message and add ellipsis
    available = max_length - len(title) - 5  # 5 chars for ": ..."
    if available > 0:
        return f"{title}: {message[:available]}..."
    
    # If title alone is too long, truncate it
    return title[:max_length-3] + "..."


# Notification templates
def get_match_notification(job_title: str, match_score: float, distance_km: float) -> dict:
    """Generate notification content for new job match"""
    return {
        "title": "New Job Match Found!",
        "message": f"You have a {match_score:.0f}% match with '{job_title}' ({distance_km:.1f} km away). Login to apply now!",
        "email_html": f"""
        <h2>🎉 New Job Match!</h2>
        <p>Great news! We found a job that matches your profile:</p>
        <ul>
            <li><strong>Job:</strong> {job_title}</li>
            <li><strong>Match Score:</strong> {match_score:.0f}%</li>
            <li><strong>Distance:</strong> {distance_km:.1f} km from you</li>
        </ul>
        <p>Login to your JobMatch account to view details and apply.</p>
        <p>Don't wait - good opportunities go fast!</p>
        """
    }


def get_application_update_notification(job_title: str, status: str) -> dict:
    """Generate notification content for application status update"""
    status_messages = {
        "applied": "Your application has been submitted",
        "reviewed": "Your application is under review",
        "shortlisted": "Congratulations! You've been shortlisted",
        "interview": "Interview scheduled - check your email for details",
        "accepted": "🎉 Congratulations! Your application was accepted",
        "rejected": "Application not selected this time"
    }
    
    message = status_messages.get(status, f"Application status: {status}")
    
    return {
        "title": f"Application Update: {job_title}",
        "message": message,
        "email_html": f"""
        <h2>Application Status Update</h2>
        <p><strong>Job:</strong> {job_title}</p>
        <p><strong>Status:</strong> {message}</p>
        <p>Login to your JobMatch account for more details.</p>
        """
    }


def get_interview_notification(job_title: str, interview_date: str, interview_time: str, location: str) -> dict:
    """Generate notification content for interview invite"""
    return {
        "title": "Interview Invitation",
        "message": f"Interview for '{job_title}' on {interview_date} at {interview_time}. Location: {location}",
        "email_html": f"""
        <h2>📅 Interview Invitation</h2>
        <p>You have been invited for an interview!</p>
        <ul>
            <li><strong>Job:</strong> {job_title}</li>
            <li><strong>Date:</strong> {interview_date}</li>
            <li><strong>Time:</strong> {interview_time}</li>
            <li><strong>Location:</strong> {location}</li>
        </ul>
        <p>Please arrive 10 minutes early. Bring a copy of your ID and any required documents.</p>
        <p>Good luck!</p>
        """
    }


def get_deadline_notification(job_title: str, deadline: str) -> dict:
    """Generate notification content for application deadline"""
    return {
        "title": "Application Deadline Reminder",
        "message": f"Reminder: Application for '{job_title}' closes on {deadline}. Apply now!",
        "email_html": f"""
        <h2>⏰ Application Deadline Reminder</h2>
        <p>Don't miss out! The application deadline is approaching:</p>
        <ul>
            <li><strong>Job:</strong> {job_title}</li>
            <li><strong>Deadline:</strong> {deadline}</li>
        </ul>
        <p>Login now to complete your application.</p>
        """
    }


def get_new_job_notification(job_title: str, wage: int, location: str) -> dict:
    """Generate notification content for new job posting"""
    return {
        "title": "New Job Posted!",
        "message": f"New job: {job_title} at ₹{wage}/day in {location}. Check it out!",
        "email_html": f"""
        <h2>New Job Opportunity</h2>
        <p>A new job matching your interests has been posted:</p>
        <ul>
            <li><strong>Job:</strong> {job_title}</li>
            <li><strong>Wage:</strong> ₹{wage}/day</li>
            <li><strong>Location:</strong> {location}</li>
        </ul>
        <p>Login to view full details and apply.</p>
        """
    }
