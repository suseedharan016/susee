import React from "react";

const NotFound = ({ t }) => {
  return (
    <div className="page">
      <h1>{t("notFoundTitle")}</h1>
      <p>{t("notFoundHint")}</p>
    </div>
  );
};

export default NotFound;
