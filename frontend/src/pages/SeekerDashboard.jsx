import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const SeekerDashboard = ({ t }) => {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "",
    mobile_number: "",
    address: "",
    age: "",
    gender: "female",
    pwd_status: false,
    skills: "",
    expected_wage: "",
    max_distance_km: 50,
    work_hours: "day",
    duration_pref: "daily",
    education_level: "secondary",
    need_accommodation: false,
  });
  const [location, setLocation] = useState(null);
  const [locationMessage, setLocationMessage] = useState("");
  const [seekerId, setSeekerId] = useState(null);
  const [showSuccess, setShowSuccess] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = async () => {
    const requiredFields = [
      "name",
      "mobile_number",
      "age",
      "skills",
      "expected_wage",
      "max_distance_km",
      "work_hours",
      "duration_pref",
      "education_level",
    ];
    const missing = requiredFields.some((field) => {
      const value = form[field];
      return value === null || value === undefined || String(value).trim() === "";
    });
    if (missing) {
      setSubmitError(t("formRequiredError"));
      return;
    }
    let submitLocation = location;
    if (!submitLocation && form.address.trim()) {
      submitLocation = await handleGeocode();
    }
    if (!submitLocation) {
      setLocationMessage(t("locationNotSet"));
      return;
    }
    setSubmitError("");
    setIsSubmitting(true);
    try {
      const response = await axios.post("http://localhost:5000/register_seeker", {
        ...form,
        age: Number(form.age),
        expected_wage: Number(form.expected_wage),
        max_distance_km: Number(form.max_distance_km),
        latitude: submitLocation.lat,
        longitude: submitLocation.lng,
      });
      setSeekerId(response.data.seeker_id);
      setShowSuccess(true);
    } catch (error) {
      setSubmitError(error.response?.data?.error || t("submitFailed"));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUseGps = () => {
    if (!navigator.geolocation) {
      setLocationMessage(t("locationError"));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        });
        setLocationMessage(t("locationSet"));
      },
      () => setLocationMessage(t("locationError")),
      { enableHighAccuracy: true, maximumAge: 0, timeout: 10000 }
    );
  };

  const handleGeocode = async () => {
    if (!form.address.trim()) {
      setLocationMessage(t("locationNeedAddress"));
      return null;
    }
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
        form.address
      )}`
    );
    const results = await response.json();
    if (!results.length) {
      setLocationMessage(t("locationNotFound"));
      return null;
    }
    const first = results[0];
    const coords = { lat: Number(first.lat), lng: Number(first.lon) };
    setLocation(coords);
    setLocationMessage(t("locationSet"));
    return coords;
  };

  const handleMatch = async () => {
    if (!seekerId) return;
    const response = await axios.get(`http://localhost:5000/match_jobs/${seekerId}`);
    navigate("/matches", { 
      state: { 
        matches: response.data.matches,
        seekerLocation: response.data.seeker_location
      } 
    });
  };

  const handleCloseSuccess = () => {
    setShowSuccess(false);
  };

  return (
    <div className="page">
      <h1>{t("dashboard")}</h1>
      <div className="card form">
        <h2>{t("createProfile")}</h2>
        <label>
          {t("formName")}
          <input name="name" value={form.name} onChange={handleChange} />
        </label>
        <label>
          {t("formMobile")}
          <input name="mobile_number" value={form.mobile_number} onChange={handleChange} />
        </label>
        <label>
          {t("formAddress")}
          <input
            name="address"
            value={form.address}
            onChange={handleChange}
            placeholder={t("addressPlaceholder")}
          />
        </label>
        <div className="map-actions">
          <button className="secondary" onClick={handleUseGps}>
            {t("formUseGps")}
          </button>
          <button className="secondary" onClick={handleGeocode}>
            {t("formFindAddress")}
          </button>
        </div>
        <p className="helper">
          {t("formLocationStatus")}: {location ? `${location.lat.toFixed(5)}, ${location.lng.toFixed(5)}` : t("locationNotSet")}
        </p>
        {locationMessage && <p className="helper">{locationMessage}</p>}
        <label>
          {t("formAge")}
          <input name="age" value={form.age} onChange={handleChange} />
        </label>
        <label>
          {t("formGender")}
          <select name="gender" value={form.gender} onChange={handleChange}>
            <option value="female">{t("genderFemale")}</option>
            <option value="male">{t("genderMale")}</option>
            <option value="other">{t("genderOther")}</option>
          </select>
        </label>
        <label className="inline">
          <input
            type="checkbox"
            name="pwd_status"
            checked={form.pwd_status}
            onChange={handleChange}
          />
          {t("formPwdStatus")}
        </label>
        <label>
          {t("formSkills")}
          <input name="skills" value={form.skills} onChange={handleChange} />
        </label>
        <label>
          {t("formExpectedWage")}
          <input name="expected_wage" value={form.expected_wage} onChange={handleChange} />
        </label>
        <label>
          {t("formMaxDistance")}
          <input
            name="max_distance_km"
            value={form.max_distance_km}
            onChange={handleChange}
          />
        </label>
        <label>
          {t("formWorkHours")}
          <input name="work_hours" value={form.work_hours} onChange={handleChange} />
        </label>
        <label>
          {t("formDurationPref")}
          <input name="duration_pref" value={form.duration_pref} onChange={handleChange} />
        </label>
        <label>
          {t("formEducation")}
          <input name="education_level" value={form.education_level} onChange={handleChange} />
        </label>
        <label className="inline">
          <input
            type="checkbox"
            name="need_accommodation"
            checked={form.need_accommodation}
            onChange={handleChange}
          />
          {t("formNeedAccommodation")}
        </label>
        <button className="primary" onClick={handleSubmit}>
          {isSubmitting ? t("filterLocating") : t("submit")}
        </button>
        {submitError && <p className="helper error">{submitError}</p>}
      </div>
      <div className="actions">
        <button className="secondary" onClick={handleMatch}>
          {t("matchNow")}
        </button>
        <button className="secondary" onClick={() => navigate("/search")}>
          {t("filterJobs")}
        </button>
        <button className="secondary" onClick={() => navigate("/jobs")}>
          {t("viewAll")}
        </button>
      </div>
      {showSuccess && (
        <div className="modal-overlay" role="dialog" aria-modal="true">
          <div className="modal-card">
            <div className="modal-header">
              <h3>{t("seekerRegistered")}</h3>
              <button className="ghost" onClick={handleCloseSuccess}>{t("close")}</button>
            </div>
            <p className="helper">{t("seekerStored")}</p>
            <div className="map-actions">
              <button className="primary" onClick={handleMatch}>{t("viewMatchesNow")}</button>
              <button className="secondary" onClick={handleCloseSuccess}>{t("close")}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SeekerDashboard;
