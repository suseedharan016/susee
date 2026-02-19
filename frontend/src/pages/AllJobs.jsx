import React, { useEffect, useState } from "react";
import axios from "axios";
import JobCard from "../components/JobCard";

const AllJobs = ({ t }) => {
  const [jobs, setJobs] = useState([]);

  useEffect(() => {
    const loadJobs = async () => {
      const response = await axios.get("http://localhost:5000/all_jobs");
      setJobs(response.data.jobs);
    };
    loadJobs();
  }, []);

  return (
    <div className="page">
      <h1>{t("allJobsTitle")}</h1>
      <div className="stack">
        {jobs.map((job) => (
          <JobCard key={job.job_id} job={job} t={t} />
        ))}
      </div>
    </div>
  );
};

export default AllJobs;
