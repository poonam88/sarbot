import React, { useMemo, useState } from "react";
import AgentTrace from "./components/AgentTrace.jsx";
import CaseHeader from "./components/CaseHeader.jsx";
import CaseList from "./components/CaseList.jsx";
import RiskScore from "./components/RiskScore.jsx";
import SARNarrative from "./components/SARNarrative.jsx";

const SAMPLE_CASES = [
  {
    case_id: "CASE-2024-8841",
    customer_id: "CUST-MERIDIAN-001",
    alert_type: "structuring_pattern",
    customer_name: "Meridian Trading Ltd",
    date: "2024-12-06",
    status: "High risk",
    summary: "GBP 47,840 across UAE/NL/Cyprus with structuring indicators.",
  },
  {
    case_id: "CASE-2024-8839",
    customer_id: "CUST-OSEI-039",
    alert_type: "cash_deposits_below_threshold",
    customer_name: "K. Osei-Mensah",
    date: "2024-12-06",
    status: "Review",
    summary: "UK domestic cash deposits clustered below threshold.",
  },
  {
    case_id: "CASE-2024-8835",
    customer_id: "CUST-BLUEWAVE-035",
    alert_type: "wire_transfers",
    customer_name: "BlueWave Capital LP",
    date: "2024-12-08",
    status: "Low risk",
    summary: "Routine supported wire transfers to known counterparties.",
  },
];

const TABS = ["Overview", "Agent Trace", "SAR Draft", "Decision"];

function App() {
  const [cases, setCases] = useState(SAMPLE_CASES);
  const [selectedCase, setSelectedCase] = useState(SAMPLE_CASES[0]);
  const [activeTab, setActiveTab] = useState("Overview");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const selectedCaseResult = useMemo(() => {
    if (result) {
      return result;
    }

    return {
      sar_narrative: "Select a case to run the SARBot investigation.",
      risk_score: 0,
      recommendation: "Awaiting agent result",
      red_flags: [],
      tool_call_log: [],
      total_time_seconds: 0,
    };
  }, [result]);

  async function handleCaseSelect(caseItem) {
    setSelectedCase(caseItem);
    setActiveTab("Overview");
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch("/api/investigate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          case_id: caseItem.case_id,
          customer_id: caseItem.customer_id,
          alert_type: caseItem.alert_type,
        }),
      });

      if (!response.ok) {
        throw new Error(`Investigation failed with status ${response.status}`);
      }

      setResult(await response.json());
    } catch (err) {
      setError(err.message || "Unable to run investigation.");
    } finally {
      setLoading(false);
    }
  }

  async function handleCaseUpload(file) {
    if (!file) {
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    setUploading(true);
    setError("");

    try {
      const response = await fetch("/api/cases/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || `Upload failed with status ${response.status}`);
      }

      const payload = await response.json();
      const uploadedCases = payload.cases || [];
      setCases((currentCases) => {
        const existingIds = new Set(currentCases.map((caseItem) => caseItem.case_id));
        const newCases = uploadedCases.filter(
          (caseItem) => !existingIds.has(caseItem.case_id)
        );
        return [...newCases, ...currentCases];
      });

      if (uploadedCases[0]) {
        setSelectedCase(uploadedCases[0]);
        setResult(null);
        setActiveTab("Overview");
      }
    } catch (err) {
      setError(err.message || "Unable to upload case data.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Financial Crime Copilot</p>
          <h1>SARBot Investigation Desk</h1>
        </div>
        <span className="environment-pill">Demo</span>
      </header>

      <div className="workspace">
        <CaseList
          cases={cases}
          selectedCaseId={selectedCase.case_id}
          onSelect={handleCaseSelect}
          onUpload={handleCaseUpload}
          uploading={uploading}
        />

        <main className="main-panel">
          <CaseHeader caseItem={selectedCase} loading={loading} />

          {loading && (
            <div className="loading-card">
              <span className="spinner" />
              Agent running - fetching KYC...
            </div>
          )}

          {error && <div className="error-card">{error}</div>}

          <nav className="tabs" aria-label="Investigation tabs">
            {TABS.map((tab) => (
              <button
                key={tab}
                className={activeTab === tab ? "tab active" : "tab"}
                onClick={() => setActiveTab(tab)}
                type="button"
              >
                {tab}
              </button>
            ))}
          </nav>

          <section className="tab-panel">
            {activeTab === "Overview" && (
              <div className="overview-grid">
                <RiskScore result={selectedCaseResult} />
                <div className="card">
                  <h2>Case Summary</h2>
                  <p>{selectedCase.summary}</p>
                  <dl className="detail-list">
                    <div>
                      <dt>Customer ID</dt>
                      <dd>{selectedCase.customer_id}</dd>
                    </div>
                    <div>
                      <dt>Alert Type</dt>
                      <dd>{selectedCase.alert_type}</dd>
                    </div>
                    <div>
                      <dt>Runtime</dt>
                      <dd>{selectedCaseResult.total_time_seconds}s</dd>
                    </div>
                  </dl>
                </div>
              </div>
            )}

            {activeTab === "Agent Trace" && (
              <AgentTrace toolCalls={selectedCaseResult.tool_call_log} />
            )}

            {activeTab === "SAR Draft" && (
              <SARNarrative narrative={selectedCaseResult.sar_narrative} />
            )}

            {activeTab === "Decision" && (
              <RiskScore result={selectedCaseResult} expanded />
            )}
          </section>
        </main>
      </div>
    </div>
  );
}

export default App;
