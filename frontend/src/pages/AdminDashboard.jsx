import React, { useEffect, useState } from "react";
import axios from "axios";

const AdminDashboard = ({ t }) => {
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    const loadMetrics = async () => {
      const response = await axios.get("http://localhost:5000/admin_metrics");
      setMetrics(response.data);
    };
    loadMetrics();
  }, []);

  if (!metrics) {
    return <div className="page">{t("adminLoading")}</div>;
  }

  return (
    <div className="page">
      <h1>{t("adminTitle")}</h1>
      <div className="grid">
        <div className="card">
          <h3>{t("adminTotalPlacements")}</h3>
          <p>{metrics.total_placements}</p>
        </div>
        <div className="card">
          <h3>{t("adminWomenPlaced")}</h3>
          <p>{metrics.percent_women_placed}%</p>
        </div>
        <div className="card">
          <h3>{t("adminPwdPlaced")}</h3>
          <p>{metrics.percent_pwd_placed}%</p>
        </div>
        <div className="card">
          <h3>{t("adminAvgSearch")}</h3>
          <p>{metrics.average_search_time_ms} ms</p>
        </div>
        <div className="card">
          <h3>{t("adminAvgMatch")}</h3>
          <p>{metrics.average_match_score}%</p>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
