import React from "react";
import { useNavigate } from "react-router-dom";

const RoleSelect = ({ t }) => {
  const navigate = useNavigate();

  return (
    <div className="page">
      <h1>{t("roleSelect")}</h1>
      <div className="grid">
        <button className="card" onClick={() => navigate("/seeker")}>
          <h2>{t("seeker")}</h2>
            <p>{t("roleSeekerDesc")}</p>
        </button>
        <button className="card" onClick={() => navigate("/provider")}>
          <h2>{t("provider")}</h2>
            <p>{t("roleProviderDesc")}</p>
        </button>
      </div>
    </div>
  );
};

export default RoleSelect;
