import React, { useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";
import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import JobCard from "../components/JobCard";

const DEFAULT_CENTER = { lat: 20.5937, lng: 78.9629 };

const haversineKm = (lat1, lon1, lat2, lon2) => {
  const toRad = (value) => (value * Math.PI) / 180;
  const radius = 6371;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) *
      Math.cos(toRad(lat2)) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return radius * c;
};

const JobSearch = ({ t }) => {
  const [filters, setFilters] = useState({
    q: "",
    min_wage: "",
    max_distance: "",
    duration: "",
    gender_friendly: "",
    pwd_accessible: "",
  });
  const [results, setResults] = useState([]);
  const [showResults, setShowResults] = useState(false);
  const [userLocation, setUserLocation] = useState(null);
  const [geoError, setGeoError] = useState("");
  const [isLocating, setIsLocating] = useState(false);
  const [isTracking, setIsTracking] = useState(false);
  const [travelMode, setTravelMode] = useState("scooter");
  const watchIdRef = useRef(null);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFilters((prev) => ({ ...prev, [name]: value }));
  };

  const handleUseLocation = () => {
    if (!navigator.geolocation) {
      setGeoError(t("geoNotSupported"));
      return;
    }
    setIsLocating(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setUserLocation({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        });
        setGeoError("");
        setIsLocating(false);
      },
      () => {
        setGeoError(t("geoAccessDenied"));
        setIsLocating(false);
      },
      { enableHighAccuracy: true, maximumAge: 0, timeout: 10000 }
    );
  };

  const handleStartTracking = () => {
    if (!navigator.geolocation) {
      setGeoError(t("geoNotSupported"));
      return;
    }
    if (watchIdRef.current != null) {
      return;
    }
    setIsTracking(true);
    watchIdRef.current = navigator.geolocation.watchPosition(
      (position) => {
        setUserLocation({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        });
        setGeoError("");
      },
      () => {
        setGeoError(t("geoTrackDenied"));
        setIsTracking(false);
      },
      { enableHighAccuracy: true, maximumAge: 0, timeout: 10000 }
    );
  };

  const handleStopTracking = () => {
    if (watchIdRef.current != null && navigator.geolocation) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }
    setIsTracking(false);
  };

  useEffect(() => () => handleStopTracking(), []);

  const handleSearch = async () => {
    const params = {};
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== "") params[key] = value;
    });
    if (userLocation) {
      params.lat = userLocation.lat;
      params.lon = userLocation.lng;
    }
    const response = await axios.get("http://localhost:5000/filter_jobs", { params });
    setResults(response.data.jobs);
    setShowResults(true);
  };

  const handleCloseResults = () => {
    setShowResults(false);
  };

  const mapCenter = useMemo(() => {
    if (userLocation) return userLocation;
    const firstJob = results.find((job) => job.latitude != null && job.longitude != null);
    if (firstJob) return { lat: firstJob.latitude, lng: firstJob.longitude };
    return DEFAULT_CENTER;
  }, [results, userLocation]);

  const travelSpeedKmh = useMemo(() => {
    if (travelMode === "walk") return 5;
    if (travelMode === "bike") return 15;
    if (travelMode === "car") return 40;
    return 25;
  }, [travelMode]);

  const resultsWithDistance = useMemo(() =>
    results.map((job) => {
      if (!userLocation || job.latitude == null || job.longitude == null) return job;
      const distance = job.distance_km != null
        ? job.distance_km
        : haversineKm(userLocation.lat, userLocation.lng, job.latitude, job.longitude);
      const distanceRounded = Math.round(distance * 100) / 100;
      const travelTimeHours = distanceRounded / travelSpeedKmh;
      const travelTimeMin = Math.round(travelTimeHours * 60);
      return {
        ...job,
        distance_km: distanceRounded,
        travel_time_min: travelTimeMin,
        travel_mode: travelMode,
      };
    }),
  [results, travelMode, travelSpeedKmh, userLocation]);

  return (
    <div className="page">
      <h1>{t("filterTitle")}</h1>
      <div className="card form">
        <label>
          {t("filterKeyword")}
          <input
            name="q"
            value={filters.q}
            onChange={handleChange}
            placeholder={t("filterKeywordPlaceholder")}
          />
        </label>
        <label>
          {t("filterMinWage")}
          <input name="min_wage" value={filters.min_wage} onChange={handleChange} />
        </label>
        <label>
          {t("filterMaxDistance")}
          <input
            name="max_distance"
            value={filters.max_distance}
            onChange={handleChange}
          />
        </label>
        <label>
          {t("filterDuration")}
          <input name="duration" value={filters.duration} onChange={handleChange} />
        </label>
        <label>
          {t("filterGenderFriendly")}
          <input name="gender_friendly" value={filters.gender_friendly} onChange={handleChange} />
        </label>
        <label>
          {t("filterPwdAccessible")}
          <input name="pwd_accessible" value={filters.pwd_accessible} onChange={handleChange} />
        </label>
        <label>
          {t("filterTravelMode")}
          <select name="travel_mode" value={travelMode} onChange={(event) => setTravelMode(event.target.value)}>
            <option value="walk">{t("travelWalk")}</option>
            <option value="bike">{t("travelBike")}</option>
            <option value="scooter">{t("travelScooter")}</option>
            <option value="car">{t("travelCar")}</option>
          </select>
        </label>
        <div className="map-actions">
          <button className="secondary" onClick={handleUseLocation} disabled={isLocating}>
            {isLocating ? t("filterLocating") : t("filterUseLocation")}
          </button>
          <button
            className="secondary"
            onClick={isTracking ? handleStopTracking : handleStartTracking}
          >
            {isTracking ? t("filterStopTracking") : t("filterStartTracking")}
          </button>
          <button className="primary" onClick={handleSearch}>{t("filterSearch")}</button>
        </div>
        {userLocation && (
          <p className="helper">{t("filterLocationLabel")}: {userLocation.lat.toFixed(6)}, {userLocation.lng.toFixed(6)}</p>
        )}
        {geoError && <p className="helper error">{geoError}</p>}
      </div>
      <div className="card map-card">
        <div className="map-header">
          <h2>{t("mapViewTitle")}</h2>
          <p>{t("mapViewSub")}</p>
        </div>
        <div className="map-shell">
          <MapContainer className="map-canvas" center={mapCenter} zoom={userLocation ? 12 : 5}>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {userLocation && (
              <Marker position={userLocation}>
                <Popup>{t("mapYouAreHere")}</Popup>
              </Marker>
            )}
            {resultsWithDistance.map((job) =>
              job.latitude != null && job.longitude != null ? (
                <Marker key={job.job_id} position={{ lat: job.latitude, lng: job.longitude }}>
                  <Popup>
                    <strong>{job.title}</strong>
                    {job.distance_km != null && (
                      <div>{t("popupDistance")}: {job.distance_km} km</div>
                    )}
                    {job.travel_time_min != null && (
                      <div>{t("popupEta")}: {job.travel_time_min} min</div>
                    )}
                  </Popup>
                </Marker>
              ) : null
            )}
          </MapContainer>
        </div>
      </div>
      <div className="stack">
        {resultsWithDistance.map((job) => (
          <JobCard key={job.job_id} job={job} t={t} />
        ))}
      </div>
      {showResults && (
        <div className="modal-overlay" role="dialog" aria-modal="true">
          <div className="modal-card">
            <div className="modal-header">
              <h3>{t("modalTitle")}</h3>
              <button className="ghost" onClick={handleCloseResults}>{t("modalClose")}</button>
            </div>
            {resultsWithDistance.length === 0 ? (
              <p className="helper">{t("modalNoResults")}</p>
            ) : (
              <div className="modal-list">
                {resultsWithDistance.map((job) => (
                  <div className="modal-item" key={job.job_id}>
                    <strong>{job.title}</strong>
                    <span>{t("jobWage")}: {job.wage}</span>
                    {job.distance_km != null && <span>{t("jobDistance")}: {job.distance_km} km</span>}
                    {job.travel_time_min != null && <span>{t("popupEta")}: {job.travel_time_min} min</span>}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default JobSearch;
