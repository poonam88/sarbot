# Deploying SARBot to Vercel

This repo is pre-wired for Vercel: a serverless Python API (`api/index.py`)
and a React frontend (`frontend/`).

## 1. Add your real frontend

Your existing React app (App.jsx, components/, styles.css) goes into the
`frontend/` folder, replacing the placeholder `package.json`. Keep the
same `frontend/src/...` structure you already have.

## 2. Update API calls to relative paths

Your React code currently calls `http://127.0.0.1:8000/investigate`.
Change every API call to a relative path, since Vercel serves both
frontend and API from the same domain:

```js
// Before
fetch("http://127.0.0.1:8000/investigate", { ... })

// After
fetch("/api/investigate", { ... })
```

Apply this to all endpoints:
- `/api/investigate`
- `/api/cases/seed`
- `/api/case/{case_id}`
- `/api/health`

## 3. Push to GitHub

```bash
cd sarbot-vercel
git init
git add .
git commit -m "SARBot ready for Vercel"
git remote add origin https://github.com/YOUR_USERNAME/sarbot.git
git push -u origin main
```

## 4. Deploy from the Vercel dashboard

1. Go to vercel.com -> sign in with GitHub
2. Add New -> Project -> Import your repo
3. Before deploying, expand Environment Variables and add:
   ```
   ANTHROPIC_API_KEY = sk-ant-...
   ```
4. Click Deploy

Vercel auto-detects `vercel.json` and builds both the API and frontend.
Every future push to `main` auto-redeploys.

## 5. Verify

```bash
curl https://your-project.vercel.app/api/health
# {"status":"ok"}

curl -X POST https://your-project.vercel.app/api/investigate \
  -H "Content-Type: application/json" \
  -d '{"case_id":"CASE-2024-8841","customer_id":"CUST-MERIDIAN-001","alert_type":"structuring_pattern"}'
```

Then open the deployed URL in a browser to see the dashboard.

## Constraints to know

- **No persistent storage** — in-memory `CASE_RESULTS` resets between
  serverless invocations. Fine for a demo; add a real database (Vercel KV,
  Postgres) for anything beyond that.
- **Execution time limit** — free tier caps functions at 10 seconds (Pro:
  60s+). The agent loop has an 8-iteration cap built in to stay within this.
- **Cold starts** — first request after inactivity may take a few extra
  seconds while the function spins up.
