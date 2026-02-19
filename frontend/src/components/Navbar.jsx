import React from "react";
import { NavLink } from "react-router-dom";
import NotificationBell from "./NotificationBell";
import logo from "../assets/logo.png";

const Navbar = ({ language, onToggle, title, t }) => {
  const isLoggedIn = !!localStorage.getItem("token");
  
  return (
    <header className="navbar">
      <div className="brand">
        <img src={logo} alt="EquiGram Logo" className="brand-logo" />
        {title}
      </div>
      <nav className="nav-links" aria-label="Primary">
        <NavLink className="nav-link" to="/">
          {t("navHome")}
        </NavLink>
        <NavLink className="nav-link" to="/roles">
          {t("navRoles")}
        </NavLink>
        <NavLink className="nav-link" to="/seeker">
          {t("navSeeker")}
        </NavLink>
        <NavLink className="nav-link" to="/provider">
          {t("navProvider")}
        </NavLink>
        <NavLink className="nav-link" to="/search">
          {t("navSearch")}
        </NavLink>
        <NavLink className="nav-link" to="/jobs">
          {t("navJobs")}
        </NavLink>
        <NavLink className="nav-link" to="/matches">
          {t("navMatches")}
        </NavLink>
        <NavLink className="nav-link" to="/admin">
          {t("navAdmin")}
        </NavLink>
      </nav>
      <div className="navbar-actions">
        {isLoggedIn && <NotificationBell t={t} />}
        <button className="lang-toggle" onClick={onToggle}>
          EN | தமிழ் | हिंदी
        </button>
      </div>
    </header>
  );
};

export default Navbar;
