import React, { useState } from "react";
import { Routes, Route } from "react-router-dom";
import { translations } from "./translations";
import Navbar from "./components/Navbar";
import Login from "./pages/Login";
import RoleSelect from "./pages/RoleSelect";
import SeekerDashboard from "./pages/SeekerDashboard";
import ProviderDashboard from "./pages/ProviderDashboard";
import JobMatches from "./pages/JobMatches";
import AdminDashboard from "./pages/AdminDashboard";
import AllJobs from "./pages/AllJobs";
import JobSearch from "./pages/JobSearch";
import NotFound from "./pages/NotFound";

const App = () => {
  const [language, setLanguage] = useState("en");
  const t = (key) => translations[language][key] || key;

  const handleToggle = () => {
    const order = ["en", "ta", "hi"];
    setLanguage((prev) => order[(order.indexOf(prev) + 1) % order.length]);
  };

  return (
    <div className="app">
      <Navbar language={language} onToggle={handleToggle} title={t("appTitle")} t={t} />
      <main>
        <Routes>
          <Route path="/" element={<Login t={t} />} />
          <Route path="/roles" element={<RoleSelect t={t} />} />
          <Route path="/seeker" element={<SeekerDashboard t={t} />} />
          <Route path="/provider" element={<ProviderDashboard t={t} />} />
          <Route path="/matches" element={<JobMatches t={t} />} />
          <Route path="/jobs" element={<AllJobs t={t} />} />
          <Route path="/search" element={<JobSearch t={t} />} />
          <Route path="/admin" element={<AdminDashboard t={t} />} />
          <Route path="*" element={<NotFound t={t} />} />
        </Routes>
      </main>
    </div>
  );
};

export default App;
