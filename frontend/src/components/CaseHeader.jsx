import React from "react";

function CaseHeader({ caseItem, loading }) {
  return (
    <section className="case-header">
      <div>
        <p className="eyebrow">{caseItem.case_id}</p>
        <h2>{caseItem.customer_name}</h2>
        <p className="muted">{caseItem.date}</p>
      </div>
      <span className={loading ? "status-badge running" : "status-badge"}>
        {loading ? "Running" : caseItem.status}
      </span>
    </section>
  );
}

export default CaseHeader;
