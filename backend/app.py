import time

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import or_, text

from matching import haversine_km, match_score
from models import Application, Feedback, Job, Provider, SearchLog, Seeker, User, Notification, NotificationPreference, db
from notifications import (
    init_mail,
    send_email,
    send_sms,
    format_sms_for_rural,
    get_match_notification,
    get_application_update_notification,
    get_interview_notification,
    get_deadline_notification,
    get_new_job_notification,
)


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = app.config.get("JWT_SECRET_KEY", "change-this-secret")
    CORS(app)
    db.init_app(app)
    jwt = JWTManager(app)
    
    # Initialize mail for notifications
    init_mail(app)

    with app.app_context():
        db.create_all()
        try:
            columns = db.session.execute(text("PRAGMA table_info(seeker)")).fetchall()
            column_names = {column[1] for column in columns}
            if "mobile_number" not in column_names:
                db.session.execute(text("ALTER TABLE seeker ADD COLUMN mobile_number VARCHAR(20)"))
                db.session.commit()
        except Exception:
            db.session.rollback()

    def _json_error(message, status=400):
        return jsonify({"error": message}), status

    def _require_fields(payload, fields):
        missing = [field for field in fields if field not in payload]
        if missing:
            return _json_error(f"Missing fields: {', '.join(missing)}")
        return None

    def _job_to_dict(job, distance_km=None):
        return {
            "job_id": job.id,
            "provider_id": job.provider_id,
            "title": job.title,
            "required_skills": job.required_skills,
            "wage": job.wage,
            "work_hours": job.work_hours,
            "duration": job.duration,
            "required_education": job.required_education,
            "age_pref": job.age_pref,
            "gender_friendly": job.gender_friendly,
            "pwd_accessible": job.pwd_accessible,
            "accommodation_available": job.accommodation_available,
            "latitude": job.latitude,
            "longitude": job.longitude,
            "active": job.active,
            "distance_km": round(distance_km, 1) if distance_km is not None else None,
        }

    def _provider_to_dict(provider):
        return {
            "provider_id": provider.id,
            "business_name": provider.business_name,
            "contact_info": provider.contact_info,
            "location_text": provider.location_text,
            "verified": provider.verified,
            "latitude": provider.latitude,
            "longitude": provider.longitude,
        }

    def _seeker_to_dict(seeker):
        return {
            "seeker_id": seeker.id,
            "name": seeker.name,
            "mobile_number": seeker.mobile_number,
            "age": seeker.age,
            "gender": seeker.gender,
            "pwd_status": seeker.pwd_status,
            "skills": seeker.skills,
            "expected_wage": seeker.expected_wage,
            "max_distance_km": seeker.max_distance_km,
            "work_hours": seeker.work_hours,
            "duration_pref": seeker.duration_pref,
            "education_level": seeker.education_level,
            "need_accommodation": seeker.need_accommodation,
            "latitude": seeker.latitude,
            "longitude": seeker.longitude,
        }

    def _application_to_dict(application):
        return {
            "application_id": application.id,
            "seeker_id": application.seeker_id,
            "job_id": application.job_id,
            "match_score": application.match_score,
            "status": application.status,
        }

    def _sample_job_metrics(job):
        distance_km = round(5 + (job.id % 7) * 3.2, 1)
        estimated_days = 3 + (job.id % 5)
        estimated_hours = 4 + (job.id % 6)
        return distance_km, estimated_days, estimated_hours

    def _create_notification(user_id, notification_type, title, message, related_job_id=None, related_application_id=None, priority="normal"):
        """Create a notification in the database"""
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            related_job_id=related_job_id,
            related_application_id=related_application_id,
            priority=priority,
        )
        db.session.add(notification)
        db.session.flush()
        return notification

    def _send_notification(user_id, notification_type, content_dict, related_job_id=None, related_application_id=None, priority="normal"):
        """
        Send notification via multiple channels based on user preferences
        
        Args:
            user_id: User ID to send notification to
            notification_type: Type of notification (match, application_update, etc.)
            content_dict: Dict with 'title', 'message', 'email_html' keys
            related_job_id: Optional job ID
            related_application_id: Optional application ID
            priority: Notification priority (low, normal, high, urgent)
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False
            
            # Get user preferences (create default if not exists)
            pref = NotificationPreference.query.filter_by(user_id=user_id).first()
            if not pref:
                pref = NotificationPreference(user_id=user_id)
                db.session.add(pref)
                db.session.flush()
            
            # Check if user wants this type of notification
            notify_map = {
                "match": pref.notify_on_match,
                "application_update": pref.notify_on_application_update,
                "interview": pref.notify_on_interview,
                "deadline": pref.notify_on_deadline,
            }
            if not notify_map.get(notification_type, True):
                return False
            
            # Create in-app notification
            notification = _create_notification(
                user_id=user_id,
                notification_type=notification_type,
                title=content_dict["title"],
                message=content_dict["message"],
                related_job_id=related_job_id,
                related_application_id=related_application_id,
                priority=priority,
            )
            
            # Send email if enabled
            if pref.email_enabled and pref.app_enabled and user.email:
                email_sent = send_email(
                    to_email=user.email,
                    subject=content_dict["title"],
                    body=content_dict["message"],
                    html_body=content_dict.get("email_html"),
                )
                notification.sent_email = email_sent
            
            # Send SMS if enabled (for seekers)
            if pref.sms_enabled and user.seeker_id:
                seeker = Seeker.query.get(user.seeker_id)
                if seeker and seeker.mobile_number and seeker.mobile_number.strip():
                    sms_message = format_sms_for_rural(
                        content_dict["title"],
                        content_dict["message"]
                    )
                    sms_sent = send_sms(seeker.mobile_number, sms_message)
                    notification.sent_sms = sms_sent
            
            db.session.commit()
            return True
            
        except Exception as e:
            print(f"Failed to send notification: {str(e)}")
            db.session.rollback()
            return False

    def _notification_to_dict(notification):
        """Convert notification to dictionary"""
        return {
            "notification_id": notification.id,
            "notification_type": notification.notification_type,
            "title": notification.title,
            "message": notification.message,
            "related_job_id": notification.related_job_id,
            "related_application_id": notification.related_application_id,
            "priority": notification.priority,
            "is_read": notification.is_read,
            "sent_email": notification.sent_email,
            "sent_sms": notification.sent_sms,
            "created_at": notification.created_at.isoformat() if notification.created_at else None,
        }

    def _require_roles(*roles):
        def wrapper(fn):
            @jwt_required()
            def inner(*args, **kwargs):
                claims = get_jwt()
                role = claims.get("role")
                if role not in roles:
                    return _json_error("Unauthorized", 403)
                return fn(*args, **kwargs)

            inner.__name__ = fn.__name__
            return inner

        return wrapper

    @app.route("/auth/register", methods=["POST"])
    def register_user():
        payload = request.get_json(force=True)
        base_required = ["email", "password", "role"]
        missing = _require_fields(payload, base_required)
        if missing:
            return missing

        email = payload["email"].strip().lower()
        if User.query.filter_by(email=email).first():
            return _json_error("Email already registered")

        role = payload["role"].strip().lower()
        seeker = None
        provider = None

        if role == "seeker":
            seeker_fields = [
                "name",
                "mobile_number",
                "age",
                "gender",
                "skills",
                "expected_wage",
                "work_hours",
                "duration_pref",
                "education_level",
                "latitude",
                "longitude",
            ]
            missing = _require_fields(payload, seeker_fields)
            if missing:
                return missing
            seeker = Seeker(
                name=payload["name"],
                mobile_number=payload.get("mobile_number"),
                age=payload["age"],
                gender=payload["gender"],
                pwd_status=payload.get("pwd_status", False),
                skills=payload["skills"],
                expected_wage=payload["expected_wage"],
                max_distance_km=payload.get("max_distance_km", 50.0),
                work_hours=payload["work_hours"],
                duration_pref=payload["duration_pref"],
                education_level=payload["education_level"],
                need_accommodation=payload.get("need_accommodation", False),
                latitude=payload["latitude"],
                longitude=payload["longitude"],
            )
            db.session.add(seeker)
            db.session.flush()
        elif role == "provider":
            provider_fields = [
                "business_name",
                "contact_info",
                "location_text",
                "latitude",
                "longitude",
            ]
            missing = _require_fields(payload, provider_fields)
            if missing:
                return missing
            provider = Provider(
                business_name=payload["business_name"],
                contact_info=payload["contact_info"],
                location_text=payload["location_text"],
                verified=payload.get("verified", False),
                latitude=payload["latitude"],
                longitude=payload["longitude"],
            )
            db.session.add(provider)
            db.session.flush()
        elif role != "admin":
            return _json_error("Invalid role")

        user = User(
            email=email,
            password_hash=generate_password_hash(payload["password"]),
            role=role,
            seeker_id=seeker.id if seeker else None,
            provider_id=provider.id if provider else None,
        )
        db.session.add(user)
        db.session.commit()

        return (
            jsonify(
                {
                    "user_id": user.id,
                    "role": user.role,
                    "seeker_id": user.seeker_id,
                    "provider_id": user.provider_id,
                }
            ),
            201,
        )

    @app.route("/auth/login", methods=["POST"])
    def login_user():
        payload = request.get_json(force=True)
        missing = _require_fields(payload, ["email", "password"])
        if missing:
            return missing

        user = User.query.filter_by(email=payload["email"].strip().lower()).first()
        if not user or not check_password_hash(user.password_hash, payload["password"]):
            return _json_error("Invalid credentials", 401)

        token = create_access_token(
            identity=user.id,
            additional_claims={
                "role": user.role,
                "seeker_id": user.seeker_id,
                "provider_id": user.provider_id,
            },
        )
        return jsonify(
            {
                "access_token": token,
                "role": user.role,
                "seeker_id": user.seeker_id,
                "provider_id": user.provider_id,
            }
        )

    @app.route("/providers", methods=["GET"])
    @_require_roles("admin")
    def list_providers():
        providers = Provider.query.all()
        return jsonify({"providers": [_provider_to_dict(provider) for provider in providers]})

    @app.route("/providers", methods=["POST"])
    @_require_roles("admin")
    def create_provider_rest():
        payload = request.get_json(force=True)
        missing = _require_fields(
            payload,
            ["business_name", "contact_info", "location_text", "latitude", "longitude"],
        )
        if missing:
            return missing
        provider = Provider(
            business_name=payload["business_name"],
            contact_info=payload["contact_info"],
            location_text=payload["location_text"],
            verified=payload.get("verified", False),
            latitude=payload["latitude"],
            longitude=payload["longitude"],
        )
        db.session.add(provider)
        db.session.commit()
        return jsonify(_provider_to_dict(provider)), 201

    @app.route("/providers/<int:provider_id>", methods=["GET"])
    @_require_roles("admin", "provider")
    def get_provider(provider_id):
        provider = Provider.query.get_or_404(provider_id)
        claims = get_jwt()
        if claims.get("role") == "provider" and claims.get("provider_id") != provider_id:
            return _json_error("Unauthorized", 403)
        return jsonify(_provider_to_dict(provider))

    @app.route("/providers/<int:provider_id>", methods=["PATCH"])
    @_require_roles("admin", "provider")
    def update_provider(provider_id):
        provider = Provider.query.get_or_404(provider_id)
        claims = get_jwt()
        if claims.get("role") == "provider" and claims.get("provider_id") != provider_id:
            return _json_error("Unauthorized", 403)
        payload = request.get_json(force=True)
        for field in [
            "business_name",
            "contact_info",
            "location_text",
            "verified",
            "latitude",
            "longitude",
        ]:
            if field in payload:
                setattr(provider, field, payload[field])
        db.session.commit()
        return jsonify(_provider_to_dict(provider))

    @app.route("/seekers", methods=["GET"])
    @_require_roles("admin")
    def list_seekers():
        seekers = Seeker.query.all()
        return jsonify({"seekers": [_seeker_to_dict(seeker) for seeker in seekers]})

    @app.route("/seekers/<int:seeker_id>", methods=["GET"])
    @_require_roles("admin", "seeker")
    def get_seeker(seeker_id):
        seeker = Seeker.query.get_or_404(seeker_id)
        claims = get_jwt()
        if claims.get("role") == "seeker" and claims.get("seeker_id") != seeker_id:
            return _json_error("Unauthorized", 403)
        return jsonify(_seeker_to_dict(seeker))

    @app.route("/seekers/<int:seeker_id>", methods=["PATCH"])
    @_require_roles("admin", "seeker")
    def update_seeker(seeker_id):
        seeker = Seeker.query.get_or_404(seeker_id)
        claims = get_jwt()
        if claims.get("role") == "seeker" and claims.get("seeker_id") != seeker_id:
            return _json_error("Unauthorized", 403)
        payload = request.get_json(force=True)
        for field in [
            "name",
            "mobile_number",
            "age",
            "gender",
            "pwd_status",
            "skills",
            "expected_wage",
            "max_distance_km",
            "work_hours",
            "duration_pref",
            "education_level",
            "need_accommodation",
            "latitude",
            "longitude",
        ]:
            if field in payload:
                setattr(seeker, field, payload[field])
        db.session.commit()
        return jsonify(_seeker_to_dict(seeker))

    @app.route("/jobs", methods=["GET"])
    def list_jobs():
        min_wage = request.args.get("min_wage", type=int)
        max_wage = request.args.get("max_wage", type=int)
        duration = request.args.get("duration")
        gender_friendly = request.args.get("gender_friendly", type=int)
        pwd_accessible = request.args.get("pwd_accessible", type=int)
        provider_id = request.args.get("provider_id", type=int)
        active_only = request.args.get("active", default=1, type=int)

        jobs = Job.query
        if provider_id is not None:
            jobs = jobs.filter(Job.provider_id == provider_id)
        if min_wage is not None:
            jobs = jobs.filter(Job.wage >= min_wage)
        if max_wage is not None:
            jobs = jobs.filter(Job.wage <= max_wage)
        if duration:
            jobs = jobs.filter(Job.duration == duration)
        if gender_friendly is not None:
            jobs = jobs.filter(Job.gender_friendly == bool(gender_friendly))
        if pwd_accessible is not None:
            jobs = jobs.filter(Job.pwd_accessible == bool(pwd_accessible))
        if active_only:
            jobs = jobs.filter(Job.active.is_(True))

        lat = request.args.get("lat", type=float)
        lon = request.args.get("lon", type=float)
        max_distance = request.args.get("max_distance", type=float)
        results = []
        for job in jobs.all():
            distance_km = None
            if lat is not None and lon is not None:
                distance_km = haversine_km(lat, lon, job.latitude, job.longitude)
                if max_distance is not None and distance_km > max_distance:
                    continue
            results.append(_job_to_dict(job, distance_km))
        return jsonify({"jobs": results})

    @app.route("/jobs", methods=["POST"])
    @_require_roles("provider", "admin")
    def create_job():
        payload = request.get_json(force=True)
        required = [
            "title",
            "required_skills",
            "wage",
            "work_hours",
            "duration",
            "required_education",
            "latitude",
            "longitude",
        ]
        missing = _require_fields(payload, required)
        if missing:
            return missing
        claims = get_jwt()
        provider_id = payload.get("provider_id")
        if claims.get("role") == "provider":
            if not claims.get("provider_id"):
                return _json_error("Provider profile not found", 403)
            provider_id = claims.get("provider_id")
        if provider_id is None:
            return _json_error("provider_id is required")

        job = Job(
            provider_id=provider_id,
            title=payload["title"],
            required_skills=payload["required_skills"],
            wage=payload["wage"],
            work_hours=payload["work_hours"],
            duration=payload["duration"],
            required_education=payload["required_education"],
            age_pref=payload.get("age_pref"),
            gender_friendly=payload.get("gender_friendly", True),
            pwd_accessible=payload.get("pwd_accessible", False),
            accommodation_available=payload.get("accommodation_available", False),
            latitude=payload["latitude"],
            longitude=payload["longitude"],
            active=payload.get("active", True),
        )
        db.session.add(job)
        db.session.commit()
        return jsonify(_job_to_dict(job)), 201

    @app.route("/jobs/<int:job_id>", methods=["GET"])
    def get_job(job_id):
        job = Job.query.get_or_404(job_id)
        return jsonify(_job_to_dict(job))

    @app.route("/jobs/<int:job_id>", methods=["PATCH"])
    @_require_roles("provider", "admin")
    def update_job(job_id):
        job = Job.query.get_or_404(job_id)
        claims = get_jwt()
        if claims.get("role") == "provider" and claims.get("provider_id") != job.provider_id:
            return _json_error("Unauthorized", 403)
        payload = request.get_json(force=True)
        for field in [
            "title",
            "required_skills",
            "wage",
            "work_hours",
            "duration",
            "required_education",
            "age_pref",
            "gender_friendly",
            "pwd_accessible",
            "accommodation_available",
            "latitude",
            "longitude",
            "active",
        ]:
            if field in payload:
                setattr(job, field, payload[field])
        db.session.commit()
        return jsonify(_job_to_dict(job))

    @app.route("/jobs/<int:job_id>", methods=["DELETE"])
    @_require_roles("provider", "admin")
    def deactivate_job(job_id):
        job = Job.query.get_or_404(job_id)
        claims = get_jwt()
        if claims.get("role") == "provider" and claims.get("provider_id") != job.provider_id:
            return _json_error("Unauthorized", 403)
        job.active = False
        db.session.commit()
        return jsonify({"job_id": job.id, "active": job.active})

    @app.route("/applications", methods=["POST"])
    @_require_roles("seeker")
    def create_application():
        payload = request.get_json(force=True)
        missing = _require_fields(payload, ["job_id"])
        if missing:
            return missing

        claims = get_jwt()
        seeker_id = claims.get("seeker_id")
        if not seeker_id:
            return _json_error("Seeker profile not found", 403)
        job = Job.query.get_or_404(payload["job_id"])
        seeker = Seeker.query.get_or_404(seeker_id)

        distance_km = haversine_km(seeker.latitude, seeker.longitude, job.latitude, job.longitude)
        score, _ = match_score(seeker, job, distance_km)
        application = Application(
            seeker_id=seeker_id,
            job_id=job.id,
            match_score=payload.get("match_score", score),
            status="applied",
        )
        db.session.add(application)
        db.session.commit()
        
        # Send notification to provider about new application
        provider = Provider.query.get(job.provider_id)
        if provider:
            provider_user = User.query.filter_by(provider_id=provider.id).first()
            if provider_user:
                content = {
                    "title": "New Job Application",
                    "message": f"{seeker.name} applied for '{job.title}' with {score*100:.0f}% match score",
                    "email_html": f"""
                    <h2>New Application Received</h2>
                    <p>You have received a new application for your job posting:</p>
                    <ul>
                        <li><strong>Job:</strong> {job.title}</li>
                        <li><strong>Applicant:</strong> {seeker.name}</li>
                        <li><strong>Match Score:</strong> {score*100:.0f}%</li>
                        <li><strong>Contact:</strong> {seeker.mobile_number or 'N/A'}</li>
                    </ul>
                    <p>Login to review the application.</p>
                    """
                }
                _send_notification(
                    user_id=provider_user.id,
                    notification_type="application_update",
                    content_dict=content,
                    related_job_id=job.id,
                    related_application_id=application.id,
                    priority="normal"
                )
        
        return jsonify(_application_to_dict(application)), 201

    @app.route("/applications", methods=["GET"])
    @_require_roles("seeker", "provider", "admin")
    def list_applications():
        claims = get_jwt()
        seeker_id = request.args.get("seeker_id", type=int)
        provider_id = request.args.get("provider_id", type=int)

        if claims.get("role") == "seeker":
            seeker_id = claims.get("seeker_id")
        if claims.get("role") == "provider":
            provider_id = claims.get("provider_id")

        query = Application.query
        if seeker_id is not None:
            query = query.filter(Application.seeker_id == seeker_id)
        if provider_id is not None:
            provider_jobs = Job.query.filter(Job.provider_id == provider_id).with_entities(Job.id).all()
            job_ids = [job_id for (job_id,) in provider_jobs]
            if job_ids:
                query = query.filter(Application.job_id.in_(job_ids))
            else:
                return jsonify({"applications": []})

        applications = query.all()
        return jsonify({"applications": [_application_to_dict(app_item) for app_item in applications]})

    @app.route("/applications/<int:application_id>", methods=["PATCH"])
    @_require_roles("provider", "admin")
    def update_application(application_id):
        application = Application.query.get_or_404(application_id)
        claims = get_jwt()
        if claims.get("role") == "provider":
            job = Job.query.get(application.job_id)
            if not job or job.provider_id != claims.get("provider_id"):
                return _json_error("Unauthorized", 403)
        payload = request.get_json(force=True)
        old_status = application.status
        if "status" in payload:
            application.status = payload["status"]
        db.session.commit()
        
        # Send notification to seeker about status change
        if "status" in payload and old_status != application.status:
            job = Job.query.get(application.job_id)
            seeker = Seeker.query.get(application.seeker_id)
            seeker_user = User.query.filter_by(seeker_id=seeker.id).first()
            if seeker_user and job:
                content = get_application_update_notification(job.title, application.status)
                priority = "high" if application.status in ["interview", "accepted"] else "normal"
                _send_notification(
                    user_id=seeker_user.id,
                    notification_type="application_update",
                    content_dict=content,
                    related_job_id=job.id,
                    related_application_id=application.id,
                    priority=priority
                )
        
        return jsonify(_application_to_dict(application))

    @app.route("/feedback", methods=["POST"])
    @_require_roles("seeker", "provider", "admin")
    def create_feedback():
        payload = request.get_json(force=True)
        missing = _require_fields(payload, ["application_id"])
        if missing:
            return missing
        feedback = Feedback(
            application_id=payload["application_id"],
            seeker_feedback=payload.get("seeker_feedback"),
            provider_feedback=payload.get("provider_feedback"),
            payment_confirmed=payload.get("payment_confirmed", False),
            completed=payload.get("completed", False),
        )
        db.session.add(feedback)
        db.session.commit()
        return jsonify({"feedback_id": feedback.id}), 201

    @app.route("/register_seeker", methods=["POST"])
    def register_seeker():
        payload = request.get_json(force=True)
        required = [
            "name",
            "mobile_number",
            "age",
            "gender",
            "skills",
            "expected_wage",
            "work_hours",
            "duration_pref",
            "education_level",
            "latitude",
            "longitude",
        ]
        missing = _require_fields(payload, required)
        if missing:
            return missing
        seeker = Seeker(
            name=payload["name"],
            mobile_number=payload.get("mobile_number"),
            age=payload["age"],
            gender=payload["gender"],
            pwd_status=payload.get("pwd_status", False),
            skills=payload["skills"],
            expected_wage=payload["expected_wage"],
            max_distance_km=payload.get("max_distance_km", 50.0),
            work_hours=payload["work_hours"],
            duration_pref=payload["duration_pref"],
            education_level=payload["education_level"],
            need_accommodation=payload.get("need_accommodation", False),
            latitude=payload["latitude"],
            longitude=payload["longitude"],
        )
        db.session.add(seeker)
        db.session.commit()
        return jsonify({"seeker_id": seeker.id}), 201

    @app.route("/create_provider", methods=["POST"])
    def create_provider():
        payload = request.get_json(force=True)
        provider = Provider(
            business_name=payload["business_name"],
            contact_info=payload["contact_info"],
            location_text=payload["location_text"],
            verified=payload.get("verified", False),
            latitude=payload["latitude"],
            longitude=payload["longitude"],
        )
        db.session.add(provider)
        db.session.commit()
        return jsonify({"provider_id": provider.id}), 201

    @app.route("/post_job", methods=["POST"])
    def post_job():
        payload = request.get_json(force=True)
        job = Job(
            provider_id=payload["provider_id"],
            title=payload["title"],
            required_skills=payload["required_skills"],
            wage=payload["wage"],
            work_hours=payload["work_hours"],
            duration=payload["duration"],
            required_education=payload["required_education"],
            age_pref=payload.get("age_pref"),
            gender_friendly=payload.get("gender_friendly", True),
            pwd_accessible=payload.get("pwd_accessible", False),
            accommodation_available=payload.get("accommodation_available", False),
            latitude=payload["latitude"],
            longitude=payload["longitude"],
        )
        db.session.add(job)
        db.session.commit()
        return jsonify({"job_id": job.id}), 201

    @app.route("/apply_job", methods=["POST"])
    def apply_job():
        payload = request.get_json(force=True)
        application = Application(
            seeker_id=payload["seeker_id"],
            job_id=payload["job_id"],
            match_score=payload["match_score"],
        )
        db.session.add(application)
        db.session.commit()
        return jsonify({"application_id": application.id}), 201

    @app.route("/submit_feedback", methods=["POST"])
    def submit_feedback():
        payload = request.get_json(force=True)
        feedback = Feedback(
            application_id=payload["application_id"],
            seeker_feedback=payload.get("seeker_feedback"),
            provider_feedback=payload.get("provider_feedback"),
            payment_confirmed=payload.get("payment_confirmed", False),
            completed=payload.get("completed", False),
        )
        db.session.add(feedback)
        db.session.commit()
        return jsonify({"feedback_id": feedback.id}), 201

    @app.route("/match_jobs/<int:seeker_id>", methods=["GET"])
    def match_jobs(seeker_id):
        start_time = time.time()
        seeker = Seeker.query.get_or_404(seeker_id)
        jobs = Job.query.filter_by(active=True).all()
        matches = []
        
        # Optional: notify about high matches
        notify_matches = request.args.get("notify", "false").lower() == "true"

        for job in jobs:
            distance_km = haversine_km(seeker.latitude, seeker.longitude, job.latitude, job.longitude)
            score, details = match_score(seeker, job, distance_km)
            matches.append(
                {
                    "job_id": job.id,
                    "title": job.title,
                    "wage": job.wage,
                    "duration": job.duration,
                    "work_hours": job.work_hours,
                    "distance_km": details["distance_km"],
                    "match_percent": round(score * 100, 1),
                    "latitude": job.latitude,
                    "longitude": job.longitude,
                    "details": details,
                }
            )

        matches.sort(key=lambda item: item["match_percent"], reverse=True)
        
        # Send notifications for top matches if requested
        if notify_matches and matches:
            seeker_user = User.query.filter_by(seeker_id=seeker.id).first()
            top_matches = [m for m in matches[:3] if m["match_percent"] >= 70]  # Top 3 with >70% match
            
            if seeker_user and top_matches:
                for match in top_matches:
                    job = Job.query.get(match["job_id"])
                    if job:
                        content = get_match_notification(
                            job_title=job.title,
                            match_score=match["match_percent"],
                            distance_km=match["distance_km"]
                        )
                        _send_notification(
                            user_id=seeker_user.id,
                            notification_type="match",
                            content_dict=content,
                            related_job_id=job.id,
                            priority="normal"
                        )

        duration_ms = int((time.time() - start_time) * 1000)
        db.session.add(SearchLog(seeker_id=seeker.id, duration_ms=duration_ms))
        db.session.commit()

        return jsonify({
            "matches": matches,
            "seeker_location": {
                "latitude": seeker.latitude,
                "longitude": seeker.longitude
            }
        })

    @app.route("/all_jobs", methods=["GET"])
    def all_jobs():
        jobs = Job.query.filter_by(active=True).all()
        results = []
        for job in jobs:
            distance_km, estimated_days, estimated_hours = _sample_job_metrics(job)
            results.append(
                {
                    "job_id": job.id,
                    "title": job.title,
                    "wage": job.wage,
                    "duration": job.duration,
                    "work_hours": job.work_hours,
                    "required_education": job.required_education,
                    "gender_friendly": job.gender_friendly,
                    "pwd_accessible": job.pwd_accessible,
                    "latitude": job.latitude,
                    "longitude": job.longitude,
                    "distance_km": distance_km,
                    "estimated_days": estimated_days,
                    "estimated_hours": estimated_hours,
                }
            )
        return jsonify({"jobs": results})

    @app.route("/filter_jobs", methods=["GET"])
    def filter_jobs():
        min_wage = request.args.get("min_wage", type=int)
        max_distance = request.args.get("max_distance", type=float)
        duration = request.args.get("duration")
        gender_friendly = request.args.get("gender_friendly", type=int)
        pwd_accessible = request.args.get("pwd_accessible", type=int)
        query = request.args.get("q")

        jobs = Job.query.filter_by(active=True)
        if min_wage is not None:
            jobs = jobs.filter(Job.wage >= min_wage)
        if gender_friendly is not None:
            jobs = jobs.filter(Job.gender_friendly == bool(gender_friendly))
        if pwd_accessible is not None:
            jobs = jobs.filter(Job.pwd_accessible == bool(pwd_accessible))
        if query:
            like_term = f"%{query}%"
            jobs = jobs.filter(
                or_(Job.title.ilike(like_term), Job.required_skills.ilike(like_term))
            )

        results = []
        lat = request.args.get("lat", type=float)
        lon = request.args.get("lon", type=float)
        def _normalize(value):
            return "".join(char for char in value.lower() if char.isalnum())

        target_duration = _normalize(duration) if duration else None

        for job in jobs.all():
            if target_duration:
                job_duration = _normalize(job.duration or "")
                if job_duration != target_duration:
                    continue
            distance_km = None
            if max_distance is not None and lat is not None and lon is not None:
                distance_km = haversine_km(lat, lon, job.latitude, job.longitude)
                if distance_km > max_distance:
                    continue
            elif lat is not None and lon is not None:
                distance_km = haversine_km(lat, lon, job.latitude, job.longitude)
            results.append(
                {
                    "job_id": job.id,
                    "title": job.title,
                    "wage": job.wage,
                    "duration": job.duration,
                    "gender_friendly": job.gender_friendly,
                    "pwd_accessible": job.pwd_accessible,
                    "latitude": job.latitude,
                    "longitude": job.longitude,
                    "distance_km": round(distance_km, 1) if distance_km is not None else None,
                }
            )
        return jsonify({"jobs": results})

    @app.route("/admin_metrics", methods=["GET"])
    def admin_metrics():
        total_placements = Feedback.query.filter_by(completed=True, payment_confirmed=True).count()
        total_seekers = Seeker.query.count()
        women_placements = (
            Feedback.query.join(Application, Feedback.application_id == Application.id)
            .join(Seeker, Application.seeker_id == Seeker.id)
            .filter(Feedback.completed.is_(True), Feedback.payment_confirmed.is_(True))
            .filter(Seeker.gender.ilike("female"))
            .count()
        )
        pwd_placements = (
            Feedback.query.join(Application, Feedback.application_id == Application.id)
            .join(Seeker, Application.seeker_id == Seeker.id)
            .filter(Feedback.completed.is_(True), Feedback.payment_confirmed.is_(True))
            .filter(Seeker.pwd_status.is_(True))
            .count()
        )
        avg_match = db.session.query(db.func.avg(Application.match_score)).scalar() or 0
        avg_search_time = db.session.query(db.func.avg(SearchLog.duration_ms)).scalar() or 0

        return jsonify(
            {
                "total_placements": total_placements,
                "percent_women_placed": round((women_placements / total_placements) * 100, 1)
                if total_placements
                else 0,
                "percent_pwd_placed": round((pwd_placements / total_placements) * 100, 1)
                if total_placements
                else 0,
                "average_search_time_ms": int(avg_search_time),
                "average_match_score": round(avg_match, 1),
                "total_seekers": total_seekers,
            }
        )

    # ============ NOTIFICATION ENDPOINTS ============

    @app.route("/notifications", methods=["GET"])
    @jwt_required()
    def get_notifications():
        """Get notifications for the current user"""
        user_id = get_jwt_identity()
        unread_only = request.args.get("unread_only", "false").lower() == "true"
        limit = request.args.get("limit", 50, type=int)
        
        query = Notification.query.filter_by(user_id=user_id)
        if unread_only:
            query = query.filter_by(is_read=False)
        
        notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
        return jsonify({
            "notifications": [_notification_to_dict(n) for n in notifications],
            "unread_count": Notification.query.filter_by(user_id=user_id, is_read=False).count()
        })

    @app.route("/notifications/<int:notification_id>/read", methods=["PATCH"])
    @jwt_required()
    def mark_notification_read(notification_id):
        """Mark a notification as read"""
        user_id = get_jwt_identity()
        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first_or_404()
        notification.is_read = True
        db.session.commit()
        return jsonify(_notification_to_dict(notification))

    @app.route("/notifications/read-all", methods=["PATCH"])
    @jwt_required()
    def mark_all_notifications_read():
        """Mark all notifications as read for current user"""
        user_id = get_jwt_identity()
        Notification.query.filter_by(user_id=user_id, is_read=False).update({"is_read": True})
        db.session.commit()
        return jsonify({"message": "All notifications marked as read"})

    @app.route("/notifications/<int:notification_id>", methods=["DELETE"])
    @jwt_required()
    def delete_notification(notification_id):
        """Delete a notification"""
        user_id = get_jwt_identity()
        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first_or_404()
        db.session.delete(notification)
        db.session.commit()
        return jsonify({"message": "Notification deleted"})

    @app.route("/notification-preferences", methods=["GET"])
    @jwt_required()
    def get_notification_preferences():
        """Get notification preferences for current user"""
        user_id = get_jwt_identity()
        pref = NotificationPreference.query.filter_by(user_id=user_id).first()
        if not pref:
            pref = NotificationPreference(user_id=user_id)
            db.session.add(pref)
            db.session.commit()
        
        return jsonify({
            "email_enabled": pref.email_enabled,
            "sms_enabled": pref.sms_enabled,
            "app_enabled": pref.app_enabled,
            "notify_on_match": pref.notify_on_match,
            "notify_on_application_update": pref.notify_on_application_update,
            "notify_on_interview": pref.notify_on_interview,
            "notify_on_deadline": pref.notify_on_deadline,
        })

    @app.route("/notification-preferences", methods=["PATCH"])
    @jwt_required()
    def update_notification_preferences():
        """Update notification preferences"""
        user_id = get_jwt_identity()
        pref = NotificationPreference.query.filter_by(user_id=user_id).first()
        if not pref:
            pref = NotificationPreference(user_id=user_id)
            db.session.add(pref)
        
        payload = request.get_json(force=True)
        for field in [
            "email_enabled",
            "sms_enabled",
            "app_enabled",
            "notify_on_match",
            "notify_on_application_update",
            "notify_on_interview",
            "notify_on_deadline",
        ]:
            if field in payload:
                setattr(pref, field, payload[field])
        
        db.session.commit()
        return jsonify({"message": "Preferences updated"})

    @app.route("/test-notification", methods=["POST"])
    @jwt_required()
    def test_notification():
        """Test notification sending (for development)"""
        user_id = get_jwt_identity()
        payload = request.get_json(force=True)
        
        content = {
            "title": payload.get("title", "Test Notification"),
            "message": payload.get("message", "This is a test notification from JobMatch"),
            "email_html": f"<p>{payload.get('message', 'This is a test notification from JobMatch')}</p>"
        }
        
        success = _send_notification(
            user_id=user_id,
            notification_type="match",  # Default type
            content_dict=content,
            priority="normal"
        )
        
        return jsonify({"success": success, "message": "Test notification sent"})

    @app.route("/seed_rural_jobs", methods=["POST"])
    def seed_rural_jobs():
        providers_payload = [
            {
                "business_name": "Kongu Dairy Collective",
                "contact_info": "kongu.dairy@example.com",
                "location_text": "Erode District",
                "verified": True,
                "latitude": 11.3410,
                "longitude": 77.7172,
            },
            {
                "business_name": "Thanjavur Agro",
                "contact_info": "tanjore.agro@example.com",
                "location_text": "Thanjavur District",
                "verified": True,
                "latitude": 10.7870,
                "longitude": 79.1378,
            },
            {
                "business_name": "Madurai Farm Co-op",
                "contact_info": "madurai.farm@example.com",
                "location_text": "Madurai District",
                "verified": True,
                "latitude": 9.9252,
                "longitude": 78.1198,
            },
        ]

        providers = {}
        for payload in providers_payload:
            provider = Provider.query.filter_by(business_name=payload["business_name"]).first()
            if provider is None:
                provider = Provider(**payload)
                db.session.add(provider)
                db.session.flush()
            providers[payload["business_name"]] = provider

        jobs_payload = [
            {
                "provider_name": "Thanjavur Agro",
                "title": "Paddy Field Worker",
                "required_skills": "planting, weeding, harvesting",
                "wage": 520,
                "work_hours": "morning",
                "duration": "seasonal",
                "required_education": "none",
                "age_pref": "18-45",
                "gender_friendly": True,
                "pwd_accessible": False,
                "accommodation_available": True,
                "latitude": 10.7812,
                "longitude": 79.1315,
            },
            {
                "provider_name": "Kongu Dairy Collective",
                "title": "Dairy Helper",
                "required_skills": "milking, animal care, cleaning",
                "wage": 560,
                "work_hours": "morning",
                "duration": "full-time",
                "required_education": "none",
                "age_pref": "20-50",
                "gender_friendly": True,
                "pwd_accessible": False,
                "accommodation_available": False,
                "latitude": 11.3489,
                "longitude": 77.7300,
            },
            {
                "provider_name": "Madurai Farm Co-op",
                "title": "Poultry Farm Assistant",
                "required_skills": "feeding, cleaning, record keeping",
                "wage": 500,
                "work_hours": "day",
                "duration": "full-time",
                "required_education": "primary",
                "age_pref": "18-40",
                "gender_friendly": True,
                "pwd_accessible": True,
                "accommodation_available": False,
                "latitude": 9.9397,
                "longitude": 78.1340,
            },
            {
                "provider_name": "Thanjavur Agro",
                "title": "Agri Equipment Operator",
                "required_skills": "tractor driving, maintenance",
                "wage": 750,
                "work_hours": "day",
                "duration": "contract",
                "required_education": "secondary",
                "age_pref": "22-50",
                "gender_friendly": True,
                "pwd_accessible": False,
                "accommodation_available": False,
                "latitude": 10.8004,
                "longitude": 79.1082,
            },
            {
                "provider_name": "Kongu Dairy Collective",
                "title": "Warehouse Sorter",
                "required_skills": "sorting, packaging, basic inventory",
                "wage": 540,
                "work_hours": "evening",
                "duration": "full-time",
                "required_education": "primary",
                "age_pref": "18-45",
                "gender_friendly": True,
                "pwd_accessible": True,
                "accommodation_available": False,
                "latitude": 11.3261,
                "longitude": 77.7235,
            },
        ]

        titles = [job["title"] for job in jobs_payload]
        existing = Job.query.filter(Job.title.in_(titles)).all()
        if len(existing) >= len(titles):
            return jsonify({"created_jobs": [], "message": "Jobs already seeded"}), 200

        created = []
        for job_data in jobs_payload:
            provider = providers[job_data.pop("provider_name")]
            job = Job(provider_id=provider.id, **job_data)
            db.session.add(job)
            created.append(job)

        db.session.commit()
        return jsonify({"created_jobs": [job.id for job in created]}), 201

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
