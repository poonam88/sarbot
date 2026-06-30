import React from "react";

function CaseList({ cases, selectedCaseId, onSelect, onUpload, uploading }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>Cases</h2>
        <span>{cases.length}</span>
      </div>

      <label className={uploading ? "upload-button disabled" : "upload-button"}>
        {uploading ? "Uploading..." : "Upload JSON/CSV"}
        <input
          accept=".json,.csv,application/json,text/csv"
          disabled={uploading}
          onChange={(event) => {
            onUpload(event.target.files?.[0]);
            event.target.value = "";
          }}
          type="file"
        />
      </label>

      <div className="case-list">
        {cases.map((caseItem) => (
          <button
            key={caseItem.case_id}
            className={
              selectedCaseId === caseItem.case_id ? "case-item selected" : "case-item"
            }
            onClick={() => onSelect(caseItem)}
            type="button"
          >
            <span className="case-id">{caseItem.case_id}</span>
            <strong>{caseItem.customer_name}</strong>
            <span className="case-summary">{caseItem.summary}</span>
            <span className="case-alert">{caseItem.alert_type}</span>
          </button>
        ))}
      </div>
    </aside>
  );
}

export default CaseList;
