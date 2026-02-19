import React, { useState } from "react";
import axios from "axios";

const ProviderDashboard = ({ t }) => {
  const [providerId, setProviderId] = useState(null);
  const [providerForm, setProviderForm] = useState({
    business_name: "",
    contact_info: "",
    location_text: "",
    verified: false,
  });
  const [jobForm, setJobForm] = useState({
    title: "",
    job_address: "",
    required_skills: "",
    wage: "",
    work_hours: "day",
    duration: "daily",
    required_education: "secondary",
    age_pref: "",
    gender_friendly: true,
    pwd_accessible: false,
    accommodation_available: false,
  });
  const [providerLocation, setProviderLocation] = useState(null);
  const [jobLocation, setJobLocation] = useState(null);
  const [locationMessage, setLocationMessage] = useState("");
  const [submitError, setSubmitError] = useState("");
  const [isSubmittingProvider, setIsSubmittingProvider] = useState(false);
  const [isSubmittingJob, setIsSubmittingJob] = useState(false);

  const handleProviderChange = (event) => {
    const { name, value, type, checked } = event.target;
    setProviderForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleJobChange = (event) => {
    const { name, value, type, checked } = event.target;
    setJobForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const submitProvider = async () => {
    if (!providerLocation) {
      setLocationMessage(t("locationNotSet"));
      return;
    }
    setSubmitError("");
    setIsSubmittingProvider(true);
    try {
      const response = await axios.post("http://localhost:5000/create_provider", {
        ...providerForm,
        latitude: providerLocation.lat,
        longitude: providerLocation.lng,
      });
      setProviderId(response.data.provider_id);
    } catch (error) {
      setSubmitError(error.response?.data?.error || t("submitFailed"));
    } finally {
      setIsSubmittingProvider(false);
    }
  };

  const submitJob = async () => {
    if (!providerId) return;
    if (!jobLocation) {
      setLocationMessage(t("locationNotSet"));
      return;
    }
    setSubmitError("");
    setIsSubmittingJob(true);
    try {
      await axios.post("http://localhost:5000/post_job", {
        ...jobForm,
        provider_id: providerId,
        wage: Number(jobForm.wage),
        latitude: jobLocation.lat,
        longitude: jobLocation.lng,
      });
    } catch (error) {
      setSubmitError(error.response?.data?.error || t("submitFailed"));
    } finally {
      setIsSubmittingJob(false);
    }
  };

  const handleUseGps = (setter) => {
    if (!navigator.geolocation) {
      setLocationMessage(t("locationError"));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setter({ lat: position.coords.latitude, lng: position.coords.longitude });
        setLocationMessage(t("locationSet"));
      },
      () => setLocationMessage(t("locationError")),
      { enableHighAccuracy: true, maximumAge: 0, timeout: 10000 }
    );
  };

  const handleGeocode = async (address, setter) => {
    if (!address.trim()) {
      setLocationMessage(t("locationNeedAddress"));
      return;
    }
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}`
    );
    const results = await response.json();
    if (!results.length) {
      setLocationMessage(t("locationNotFound"));
      return;
    }
    const first = results[0];
    setter({ lat: Number(first.lat), lng: Number(first.lon) });
    setLocationMessage(t("locationSet"));
  };

  return (
    <div className="page">
      <h1>{t("dashboard")}</h1>
      <div className="card form">
        <h2>{t("formProviderProfile")}</h2>
        <label>
          {t("formBusinessName")}
          <input name="business_name" value={providerForm.business_name} onChange={handleProviderChange} />
        </label>
        <label>
          {t("formContactInfo")}
          <input name="contact_info" value={providerForm.contact_info} onChange={handleProviderChange} />
        </label>
        <label>
          {t("providerAddress")}
          <input name="location_text" value={providerForm.location_text} onChange={handleProviderChange} />
        </label>
        <div className="map-actions">
          <button className="secondary" onClick={() => handleUseGps(setProviderLocation)}>
            {t("formUseGps")}
          </button>
          <button
            className="secondary"
            onClick={() => handleGeocode(providerForm.location_text, setProviderLocation)}
          >
            {t("formFindAddress")}
          </button>
        </div>
        <p className="helper">
          {t("formLocationStatus")}: {providerLocation
            ? `${providerLocation.lat.toFixed(5)}, ${providerLocation.lng.toFixed(5)}`
            : t("locationNotSet")}
        </p>
        <label className="inline">
          <input
            type="checkbox"
            name="verified"
            checked={providerForm.verified}
            onChange={handleProviderChange}
          />
          {t("formVerified")}
        </label>
        {locationMessage && <p className="helper">{locationMessage}</p>}
        {submitError && <p className="helper error">{submitError}</p>}
        <button className="primary" onClick={submitProvider}>
          {isSubmittingProvider ? t("filterLocating") : t("submit")}
        </button>
      </div>

      <div className="card form">
        <h2>{t("postJob")}</h2>
        <label>
          {t("formJobTitle")}
          <input name="title" value={jobForm.title} onChange={handleJobChange} />
        </label>
        <label>
          {t("jobAddress")}
          <input name="job_address" value={jobForm.job_address} onChange={handleJobChange} />
        </label>
        <div className="map-actions">
          <button className="secondary" onClick={() => handleUseGps(setJobLocation)}>
            {t("formUseGps")}
          </button>
          <button
            className="secondary"
            onClick={() => handleGeocode(jobForm.job_address, setJobLocation)}
          >
            {t("formFindAddress")}
          </button>
          <button
            className="secondary"
            onClick={() => providerLocation && setJobLocation(providerLocation)}
          >
            {t("formUseProviderLocation")}
          </button>
        </div>
        <p className="helper">
          {t("formLocationStatus")}: {jobLocation
            ? `${jobLocation.lat.toFixed(5)}, ${jobLocation.lng.toFixed(5)}`
            : t("locationNotSet")}
        </p>
        <label>
          {t("formRequiredSkills")}
          <input name="required_skills" value={jobForm.required_skills} onChange={handleJobChange} />
        </label>
        <label>
          {t("formWage")}
          <input name="wage" value={jobForm.wage} onChange={handleJobChange} />
        </label>
        <label>
          {t("formWorkingHours")}
          <input name="work_hours" value={jobForm.work_hours} onChange={handleJobChange} />
        </label>
        <label>
          {t("formDuration")}
          <input name="duration" value={jobForm.duration} onChange={handleJobChange} />
        </label>
        <label>
          {t("formRequiredEducation")}
          <input
            name="required_education"
            value={jobForm.required_education}
            onChange={handleJobChange}
          />
        </label>
        <label>
          {t("formAgePref")}
          <input name="age_pref" value={jobForm.age_pref} onChange={handleJobChange} />
        </label>
        <label className="inline">
          <input
            type="checkbox"
            name="gender_friendly"
            checked={jobForm.gender_friendly}
            onChange={handleJobChange}
          />
          {t("formGenderFriendly")}
        </label>
        <label className="inline">
          <input
            type="checkbox"
            name="pwd_accessible"
            checked={jobForm.pwd_accessible}
            onChange={handleJobChange}
          />
          {t("formPwdAccessible")}
        </label>
        <label className="inline">
          <input
            type="checkbox"
            name="accommodation_available"
            checked={jobForm.accommodation_available}
            onChange={handleJobChange}
          />
          {t("formAccommodation")}
        </label>
        {locationMessage && <p className="helper">{locationMessage}</p>}
        {submitError && <p className="helper error">{submitError}</p>}
        <button className="primary" onClick={submitJob}>
          {isSubmittingJob ? t("filterLocating") : t("submit")}
        </button>
      </div>
    </div>
  );
};

export default ProviderDashboard;
