import React from "react";
import { useNavigate } from "react-router-dom";

const Login = ({ t }) => {
  const navigate = useNavigate();

  return (
    <div className="page login-page">
      <section className="hero">
        <div className="hero-copy">
          <div className="pill">{t("sampleNetwork")}</div>
          <h1>{t("loginHeadline")}</h1>
          <p>{t("loginSubhead")}</p>
          <div className="stat-row">
            <div className="stat">
              <span>{t("statPlacements")}</span>
              <strong>12.4k</strong>
            </div>
            <div className="stat">
              <span>{t("statWomen")}</span>
              <strong>64%</strong>
            </div>
            <div className="stat">
              <span>{t("statAvgMatch")}</span>
              <strong>82%</strong>
            </div>
          </div>
          <div className="hero-actions">
            <button className="primary" onClick={() => navigate("/seeker")}>
              {t("actionSeeker")}
            </button>
            <button className="secondary" onClick={() => navigate("/provider")}>
              {t("actionProvider")}
            </button>
          </div>
        </div>
        <div className="hero-card">
          <div className="signin-header">
            <div>
              <h2>{t("loginTitle")}</h2>
              <p>{t("loginHelper")}</p>
            </div>
            <div className="badge-soft">{t("secureBadge")}</div>
          </div>
          <label className="input-group">
            <span>{t("loginId")}</span>
            <input type="text" placeholder={t("loginIdPlaceholder")} />
          </label>
          <label className="input-group">
            <span>{t("loginPass")}</span>
            <input type="password" placeholder={t("loginPassPlaceholder")} />
          </label>
          <div className="signin-actions">
            <button className="primary" onClick={() => navigate("/roles")}>
              {t("continue")}
            </button>
            <button className="ghost" onClick={() => navigate("/roles")}>
              {t("guest")}
            </button>
          </div>
          <div className="signin-footer">
            <span>{t("helpText")}</span>
            <button className="link" type="button">
              {t("helpLink")}
            </button>
          </div>
        </div>
      </section>

      <section className="info-grid">
        <div className="card">
          <h3>{t("quickStepsTitle")}</h3>
          <ol className="step-list">
            <li>{t("stepOne")}</li>
            <li>{t("stepTwo")}</li>
            <li>{t("stepThree")}</li>
          </ol>
        </div>
        <div className="card">
          <h3>{t("trustTitle")}</h3>
          <ul className="detail-list">
            <li>{t("trustLineOne")}</li>
            <li>{t("trustLineTwo")}</li>
            <li>{t("trustLineThree")}</li>
          </ul>
        </div>
      </section>

      <section className="sample-work">
        <div className="section-header">
          <h2>{t("sampleTitle")}</h2>
          <p>{t("sampleSub")}</p>
        </div>
        <div className="sample-grid">
          <div className="sample-card">
            <div className="sample-meta">
              <span className="tag">{t("sampleBadge")}</span>
              <span className="tag">12 km</span>
            </div>
            <h3>{t("sampleJobFarm")}</h3>
            <p>{t("sampleWageLabel")}: 650</p>
            <p>{t("sampleSkillsLabel")}: irrigation, sorting</p>
          </div>
          <div className="sample-card">
            <div className="sample-meta">
              <span className="tag">{t("sampleBadge")}</span>
              <span className="tag">7 km</span>
            </div>
            <h3>{t("sampleJobTextile")}</h3>
            <p>{t("sampleWageLabel")}: 720</p>
            <p>{t("sampleSkillsLabel")}: packing, machine care</p>
          </div>
          <div className="sample-card">
            <div className="sample-meta">
              <span className="tag">{t("sampleBadge")}</span>
              <span className="tag">18 km</span>
            </div>
            <h3>{t("sampleJobKitchen")}</h3>
            <p>{t("sampleWageLabel")}: 600</p>
            <p>{t("sampleSkillsLabel")}: prep, hygiene</p>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Login;
