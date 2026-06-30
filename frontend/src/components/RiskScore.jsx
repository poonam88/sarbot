import React from "react";

function getScoreClass(score) {
  if (score >= 75) {
    return "score high";
  }
  if (score >= 50) {
    return "score medium";
  }
  return "score low";
}

function RiskScore({ result, expanded = false }) {
  return (
    <div className="card risk-card">
      <div className="card-header">
        <h2>Risk Score</h2>
        <span className={getScoreClass(result.risk_score)}>{result.risk_score}</span>
      </div>

      <div className="score-bar" aria-hidden="true">
        <span style={{ width: `${result.risk_score}%` }} />
      </div>

      <span className="recommendation-badge">{result.recommendation}</span>

      <h3>Red Flags</h3>
      {result.red_flags.length ? (
        <ul className="red-flags">
          {result.red_flags.map((flag) => (
            <li key={flag}>{flag}</li>
          ))}
        </ul>
      ) : (
        <p className="muted">No red flags returned yet.</p>
      )}

      {expanded && (
        <div className="decision-box">
          <h3>Decision</h3>
          <p>{result.recommendation}</p>
        </div>
      )}
    </div>
  );
}

export default RiskScore;
