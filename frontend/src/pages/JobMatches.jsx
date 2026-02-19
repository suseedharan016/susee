import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import JobCard from "../components/JobCard";

const JobMatches = ({ t }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const matches = location.state?.matches || [];
  const seekerLocation = location.state?.seekerLocation;

  return (
    <div className="page">
      <h1>{t("matches")}</h1>
      <div className="stack">
        {matches.length === 0 && <p>{t("noMatches")}</p>}
        {matches.map((job) => (
          <JobCard key={job.job_id} job={job} seekerLocation={seekerLocation} t={t} />
        ))}
      </div>
      <button className="secondary" onClick={() => navigate("/seeker")}>
        {t("back")}
      </button>
    </div>
  );
};

export default JobMatches;
