import React from "react";

const getBadgeClass = (percent) => {
  if (percent >= 80) return "badge badge-high";
  if (percent >= 60) return "badge badge-mid";
  return "badge badge-low";
};

const JobCard = ({ job, seekerLocation, t }) => {
  const label = (key, fallback) => (t ? t(key) : fallback);
  const formatTravelTime = (minutes) => {
    if (minutes == null) return "";
    if (minutes < 60) return `${minutes} ${label("labelMin", "min")}`;
    const hours = Math.floor(minutes / 60);
    const remaining = minutes % 60;
    if (remaining === 0) return `${hours} ${label("labelHr", "hr")}`;
    return `${hours} ${label("labelHr", "hr")} ${remaining} ${label("labelMin", "min")}`;
  };
  const hasCoords = job.latitude != null && job.longitude != null;
  const hasSeekerCoords = seekerLocation?.latitude != null && seekerLocation?.longitude != null;
  
  // Build Google Maps embed URL
  let embedUrl = "";
  let mapsLink = "";
  
  if (hasCoords && hasSeekerCoords) {
    // Show both locations with directions
    embedUrl = `https://www.google.com/maps/embed/v1/directions?key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8&origin=${seekerLocation.latitude},${seekerLocation.longitude}&destination=${job.latitude},${job.longitude}&mode=driving`;
    mapsLink = `https://www.google.com/maps/dir/?api=1&origin=${seekerLocation.latitude},${seekerLocation.longitude}&destination=${job.latitude},${job.longitude}`;
  } else if (hasCoords) {
    // Show only job location
    embedUrl = `https://www.google.com/maps/embed/v1/place?key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8&q=${job.latitude},${job.longitude}&zoom=14`;
    mapsLink = `https://www.google.com/maps/search/?api=1&query=${job.latitude},${job.longitude}`;
  }
  return (
    <div className="card job-card">
      <div className="card-header">
        <h3>{job.title}</h3>
        {job.match_percent !== undefined && (
          <span className={getBadgeClass(job.match_percent)}>
            {job.match_percent}%
          </span>
        )}
      </div>
      <div className="card-body">
        <p>{label("jobWage", "Wage")}: {job.wage}</p>
        {job.duration && <p>{label("jobDuration", "Duration")}: {job.duration}</p>}
        {job.work_hours && <p>{label("jobWorkHours", "Work hours")}: {job.work_hours}</p>}
        {job.distance_km !== undefined && (
          <p>{label("jobDistance", "Distance")}: {job.distance_km} km</p>
        )}
        {job.estimated_days !== undefined && job.estimated_hours !== undefined && (
          <p>
            {label("jobEstimatedTime", "Estimated time")}: {job.estimated_days} {label("labelDays", "days")} / {job.estimated_hours} {label("labelHours", "hours")}
          </p>
        )}
        {job.travel_time_min !== undefined && (
          <p>{label("jobEstimatedTime", "Estimated time")}: {formatTravelTime(job.travel_time_min)}</p>
        )}
        {hasCoords && embedUrl && (
          <div className="job-map-container">
            <iframe
              className="job-map-preview"
              src={embedUrl}
              allowFullScreen
              loading="lazy"
              referrerPolicy="no-referrer-when-downgrade"
              title={`Map for ${job.title}`}
            />
            {hasSeekerCoords && (
              <p className="map-info">{label("mapShowingRoute", "Showing route from your location to job")}</p>
            )}
            <a
              className="job-map-link"
              href={mapsLink}
              target="_blank"
              rel="noreferrer"
            >
              {label("jobMapLink", "Open in Google Maps")}
            </a>
          </div>
        )}
        {job.details && (
          <ul className="detail-list">
            <li>
              {label("jobSkillMatch", "Skill match")}: {
                job.match_percent !== undefined ? job.match_percent : 0
              }%
            </li>
            <li>
              {label("jobPwdFriendly", "PwD friendly")}: {job.details.pwd_friendly ? label("yesLabel", "Yes") : label("noLabel", "No")}
            </li>
            <li>
              {label("jobAccommodation", "Accommodation")}: {job.details.accommodation_available ? label("yesLabel", "Yes") : label("noLabel", "No")}
            </li>
          </ul>
        )}
      </div>
    </div>
  );
};

export default JobCard;
