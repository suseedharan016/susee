# Inclusive AI Job Matching Platform – Tamil Nadu Rural Employment Network

## Project Goal
Increase verified rural job placements across Tamil Nadu by improving matching precision, reducing search time, and ensuring inclusion of women and PwD within a 50 km employment radius.

## Tech Stack
- Frontend: React, React Router, Axios, clean CSS
- Backend: Flask, Flask SQLAlchemy, Flask CORS
- Database: SQLite

## API Routes
- POST /register_seeker
- POST /create_provider
- POST /post_job
- GET /match_jobs/<seeker_id>
- GET /all_jobs
- GET /filter_jobs
- POST /apply_job
- POST /submit_feedback
- GET /admin_metrics

## Local Development

### Backend
1. Create a virtual environment and install dependencies:
   - `pip install -r backend/requirements.txt`
2. Run the server:
   - `python backend/app.py`

### Frontend
1. Install dependencies:
   - `npm install` (from the frontend directory)
2. Start the dev server:
   - `npm run dev`

## Notes
- Update the API base URL in frontend pages if the backend host changes.
- Matching uses a weighted scoring model with Haversine distance.

Last deployment trigger: 2026-02-19
