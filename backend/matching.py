import math


WEIGHTS = {
    "skills": 0.30,
    "distance": 0.20,
    "wage": 0.15,
    "duration": 0.10,
    "work_hours": 0.10,
    "pwd": 0.10,
    "accommodation": 0.05,
}


def haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


def _normalize_list(raw_text):
    return [item.strip().lower() for item in raw_text.split(",") if item.strip()]


def skill_match_percent(seeker_skills, job_skills):
    """Calculate skill match percentage with support for partial matches and word stems."""
    seeker_set = set(_normalize_list(seeker_skills))
    job_set = set(_normalize_list(job_skills))
    if not seeker_set or not job_set:
        return 0.0
    
    # First check for exact matches
    exact_overlap = seeker_set.intersection(job_set)
    matched_job_skills = set(exact_overlap)
    
    # Then check for partial matches using common prefixes (minimum 4 chars)
    for job_skill in job_set:
        if job_skill not in matched_job_skills:
            for seeker_skill in seeker_set:
                # Check if either skill is a substring of the other
                if (job_skill in seeker_skill or seeker_skill in job_skill):
                    matched_job_skills.add(job_skill)
                    break
                # Check for common prefix of at least 4 characters
                elif (len(job_skill) >= 4 and len(seeker_skill) >= 4 and 
                      job_skill[:4] == seeker_skill[:4]):
                    matched_job_skills.add(job_skill)
                    break
    
    return (len(matched_job_skills) / len(job_set)) * 100.0


def distance_score(distance_km, max_distance_km):
    if distance_km > max_distance_km:
        return 0.0
    return max(0.0, 1.0 - (distance_km / max_distance_km))


def wage_score(expected_wage, job_wage):
    if expected_wage <= 0:
        return 0.0
    return min(1.0, job_wage / expected_wage)


def match_score(seeker, job, distance_km):
    skills_pct = skill_match_percent(seeker.skills, job.required_skills)
    duration_match = 1.0 if seeker.duration_pref == job.duration else 0.0
    work_hours_match = 1.0 if seeker.work_hours == job.work_hours else 0.0
    pwd_match = 1.0 if (not seeker.pwd_status or job.pwd_accessible) else 0.0
    accommodation_match = 1.0 if (not seeker.need_accommodation or job.accommodation_available) else 0.0

    weighted = (
        WEIGHTS["skills"] * (skills_pct / 100.0)
        + WEIGHTS["distance"] * distance_score(distance_km, seeker.max_distance_km)
        + WEIGHTS["wage"] * wage_score(seeker.expected_wage, job.wage)
        + WEIGHTS["duration"] * duration_match
        + WEIGHTS["work_hours"] * work_hours_match
        + WEIGHTS["pwd"] * pwd_match
        + WEIGHTS["accommodation"] * accommodation_match
    )
    return max(0.0, min(1.0, weighted)), {
        "skill_match": round(skills_pct, 1),
        "distance_km": round(distance_km, 1),
        "wage_compatible": job.wage >= seeker.expected_wage,
        "duration_match": duration_match == 1.0,
        "work_hours_match": work_hours_match == 1.0,
        "pwd_friendly": job.pwd_accessible,
        "accommodation_available": job.accommodation_available,
    }
