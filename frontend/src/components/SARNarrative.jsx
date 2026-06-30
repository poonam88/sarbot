import React, { useEffect, useState } from "react";

function SARNarrative({ narrative }) {
  const [draft, setDraft] = useState(narrative);
  const [approved, setApproved] = useState(false);

  useEffect(() => {
    setDraft(narrative);
    setApproved(false);
  }, [narrative]);

  return (
    <div className="card sar-card">
      <div className="card-header">
        <h2>SAR Draft</h2>
        {approved && <span className="approved-badge">Approved</span>}
      </div>

      <textarea
        aria-label="SAR narrative draft"
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
      />

      <div className="action-row">
        <button className="secondary-button" type="button">
          Edit
        </button>
        <button
          className="primary-button"
          onClick={() => setApproved(true)}
          type="button"
        >
          Approve
        </button>
      </div>
    </div>
  );
}

export default SARNarrative;
