from datetime import datetime

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Seeker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    mobile_number = db.Column(db.String(20), nullable=True)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    pwd_status = db.Column(db.Boolean, default=False)
    skills = db.Column(db.Text, nullable=False)
    expected_wage = db.Column(db.Integer, nullable=False)
    max_distance_km = db.Column(db.Float, default=50.0)
    work_hours = db.Column(db.String(50), nullable=False)
    duration_pref = db.Column(db.String(30), nullable=False)
    education_level = db.Column(db.String(60), nullable=False)
    need_accommodation = db.Column(db.Boolean, default=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Provider(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(160), nullable=False)
    contact_info = db.Column(db.String(160), nullable=False)
    location_text = db.Column(db.String(200), nullable=False)
    verified = db.Column(db.Boolean, default=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey("provider.id"), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    required_skills = db.Column(db.Text, nullable=False)
    wage = db.Column(db.Integer, nullable=False)
    work_hours = db.Column(db.String(50), nullable=False)
    duration = db.Column(db.String(30), nullable=False)
    required_education = db.Column(db.String(60), nullable=False)
    age_pref = db.Column(db.String(20), nullable=True)
    gender_friendly = db.Column(db.Boolean, default=True)
    pwd_accessible = db.Column(db.Boolean, default=False)
    accommodation_available = db.Column(db.Boolean, default=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seeker_id = db.Column(db.Integer, db.ForeignKey("seeker.id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=False)
    match_score = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(30), default="applied")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("application.id"), nullable=False)
    seeker_feedback = db.Column(db.Text, nullable=True)
    provider_feedback = db.Column(db.Text, nullable=True)
    payment_confirmed = db.Column(db.Boolean, default=False)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SearchLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seeker_id = db.Column(db.Integer, db.ForeignKey("seeker.id"), nullable=False)
    duration_ms = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(160), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False)
    seeker_id = db.Column(db.Integer, db.ForeignKey("seeker.id"), nullable=True)
    provider_id = db.Column(db.Integer, db.ForeignKey("provider.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # match, application_update, interview, deadline
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    related_job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=True)
    related_application_id = db.Column(db.Integer, db.ForeignKey("application.id"), nullable=True)
    priority = db.Column(db.String(20), default="normal")  # low, normal, high, urgent
    is_read = db.Column(db.Boolean, default=False)
    sent_email = db.Column(db.Boolean, default=False)
    sent_sms = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class NotificationPreference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True)
    email_enabled = db.Column(db.Boolean, default=True)
    sms_enabled = db.Column(db.Boolean, default=True)
    app_enabled = db.Column(db.Boolean, default=True)
    notify_on_match = db.Column(db.Boolean, default=True)
    notify_on_application_update = db.Column(db.Boolean, default=True)
    notify_on_interview = db.Column(db.Boolean, default=True)
    notify_on_deadline = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
