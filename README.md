# SARBot — AI-powered financial crime investigation copilot

SARBot is an autonomous AI agent that investigates suspicious activity alerts, gathers evidence, drafts regulatory-grade SAR (Suspicious Activity Report) narratives, and calculates risk scores — turning a multi-hour manual AML investigation into a task that completes in seconds.

Built for [hackathon name] using Claude's agentic tool-use API.

## What it does

Given a case ID, customer ID, and alert type, SARBot's agent autonomously:

1. **Retrieves KYC data** — nationality, PEP status, occupation, risk tier, prior alerts
2. **Pulls transaction history** — amounts, counterparties, jurisdictions
3. **Matches typologies** — searches a FATF/FCA-aligned typology reference (structuring, layering, TBML, bulk cash)
4. **Drafts a SAR narrative** — regulatory-grade prose citing the evidence gathered
5. **Calculates a risk score** — 0–100, with a clear recommendation (SUBMIT SAR / ESCALATE / MONITOR / DISMISS)

Every tool call is logged with input, output, and duration, giving investigators a transparent, auditable evidence trail — critical for regulatory scrutiny.

## Why this matters

AML analysts spend hours per case manually gathering evidence and drafting SAR narratives. This creates investigation backlogs, inconsistent SAR quality across analysts, and audit risk when reasoning lives only in someone's notes. SARBot compresses the evidence-gathering and drafting step from hours to seconds while keeping every step traceable — the analyst still reviews and approves before anything is filed.

## Architecture

```
React frontend  --->  FastAPI backend  --->  Claude (Anthropic) tool-use agent
                            |
                            v
                       5 tools (mock data, swappable for real systems)
```

- **Agent loop** (`agent.py` / `api/index.py`): Claude Messages API with native tool-use. Calls tools in sequence, observes results, decides next step, until it returns a final structured JSON result.
- **Tools** (`tools.py`): five deterministic Python functions — `get_customer_kyc`, `get_transaction_history`, `search_typology_database`, `draft_sar_narrative`, `calculate_risk_score`. Currently backed by realistic mock data; designed to be swapped for real KYC/transaction/case-management systems.
- **Backend** (`main.py`): FastAPI routes for investigation, case retrieval, sample-case seeding, and case upload (JSON/CSV).
- **Frontend** (`frontend/`): React dashboard — case list, agent trace timeline, editable SAR draft, risk score panel.

## Tech stack

- **AI:** Claude (Anthropic) — agentic tool-use
- **Backend:** FastAPI, Pydantic
- **Frontend:** React
- **Deployment:** Vercel (serverless Python functions + static frontend)

## Project structure

```
sarbot/
  main.py              FastAPI app and routes
  agent.py             Agent loop (Claude tool-use)
  tools.py             5 mock tools + typology data
  models.py             Pydantic request/response schemas
  data/
    sample_cases.json   3 demo cases
  .env                  ANTHROPIC_API_KEY (not committed)

frontend/
  src/
    App.jsx
    components/
      CaseList.jsx
      CaseHeader.jsx
      AgentTrace.jsx
      SARNarrative.jsx
      RiskScore.jsx
    styles.css

api/                    Vercel serverless entry point (consolidated app)
vercel.json             Vercel routing config
```

## Running locally

**Backend:**
```bash
cd sarbot
pip install -r requirements.txt
# Add ANTHROPIC_API_KEY to sarbot/.env
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev -- --port 3000
```

Open `http://127.0.0.1:3000`.

## Demo flow

1. Open the dashboard and select a flagged case (e.g. "Meridian Trading Ltd — structuring across UAE/NL/Cyprus")
2. The agent investigates autonomously — watch the **Agent Trace** tab for live tool calls
3. Review the **SAR Draft** tab — an editable, citation-grounded narrative
4. Review the **Decision** tab — risk score, red flags, and recommendation
5. Approve or edit before submission

## Sample cases

| Case ID | Customer | Pattern |
|---|---|---|
| CASE-2024-8841 | Meridian Trading Ltd | High-risk structuring across UAE/NL/Cyprus |
| CASE-2024-8839 | K. Osei-Mensah | Cash deposits below reporting threshold |
| CASE-2024-8835 | BlueWave Capital LP | Lower-risk wire transfer pattern |

## Deployment

See [`DEPLOY.md`](./DEPLOY.md) for Vercel deployment instructions, or deploy directly from GitHub:

1. Push this repo to GitHub
2. Go to vercel.com → Add New Project → import this repo
3. Add `ANTHROPIC_API_KEY` under Environment Variables
4. Click Deploy

Every future push to `main` auto-redeploys.

## Status

Working prototype with mock data tools and a fully functional agent loop. Tools are designed to be swapped for real KYC/transaction/case-management systems in production. The agent never files a SAR autonomously — a human analyst always reviews and approves before submission.

## License

[Add your license here]
