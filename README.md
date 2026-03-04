# CRM Agent — Enterprise Customer Experience Intelligence Agent

Agentic AI system that monitors CX data (tickets, reviews, NPS), detects anomalies, investigates root cause, and produces alerts and actions.

## Tech stack

- **Backend:** FastAPI (Python 3.11)
- **LLM:** OpenAI GPT-4o
- **Agentic:** LangGraph (Monitor → Investigator → Action → Supervisor)
- **Tools & retrieval:** LangChain, ChromaDB, text-embedding-3-small
- **MCP:** Three MCP servers (reviews, tickets, NPS) using the official MCP Python SDK
- **Frontend:** React + Vite + Tailwind CSS (dark theme)

## Setup

### 1. Environment

```bash
cp .env.example .env
# Edit .env and set:
# OPENAI_API_KEY=sk-your-key
# CHROMA_PERSIST_DIR=./data/chroma  (optional; default ./data/chroma)
```

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Seed data

From the `backend` directory (with venv active):

```bash
export OPENAI_API_KEY=sk-your-key   # required for embeddings
python scripts/seed_data.py
```

This will:

- Create 500 synthetic support tickets (450 normal + 50 crisis)
- Create 200 NPS responses
- Load Amazon reviews from HuggingFace (McAuley-Lab/Amazon-Reviews-2023) or fall back to synthetic reviews
- Add a **crisis scenario:** 50 tickets + 30 reviews about “checkout failed on iOS v2.3.1” in the last 6 hours
- Embed all into ChromaDB (requires `OPENAI_API_KEY`)

### 4. Run backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The app proxies `/api` to the backend at port 8000.

## Demo flow

1. Click **Run Agent Now** in the header.
2. **Monitor Agent** pulls from data (via MCP-style tools) and detects the iOS checkout crisis spike.
3. **Investigator Agent** uses ChromaDB to cross-reference and finds root cause (same version, West Coast, last 6h).
4. **Action Agent** produces a P0 alert, customer response template, routes to Engineering, and raises churn risk (e.g. to 67%).
5. Dashboard updates (CX Health, Churn Risk, Open Issues, NPS).
6. In **Agent Chat**, ask: “Should we roll back the iOS deployment?” — the agent answers with cited evidence from the vector store.

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/agent/run` | Start full agent pipeline; returns `job_id` |
| GET | `/agent/status/{job_id}` | Job status and result |
| GET | `/agent/trace/{job_id}` | Step-by-step agent trace |
| GET | `/dashboard/summary` | CX health, churn risk, NPS, top issues |
| GET | `/dashboard/heatmap` | Issue category × time matrix |
| GET | `/alerts` | Last 20 agent-generated alerts |
| POST | `/chat` | Q&A with source citations (body: `{"message": "..."}`) |

## MCP servers (optional standalone)

The backend uses the same logic in-process. To run MCP servers as separate processes (e.g. for other MCP clients):

```bash
cd backend
# Terminal 1
python -m app.mcp_servers.reviews_mcp
# Terminal 2
python -m app.mcp_servers.tickets_mcp
# Terminal 3
python -m app.mcp_servers.nps_mcp
```

Each server speaks MCP over stdio. Data is read from the same JSON files under `backend/data/` (created by `seed_data.py`). Ensure `DATA_DIR` points to that directory when running the servers.

## Project layout

```
Aiagent/
├── backend/
│   ├── app/
│   │   ├── agents/       # LangGraph: monitor, investigator, action, supervisor, graph
│   │   ├── api/routes/   # FastAPI: agent, dashboard, alerts, chat
│   │   ├── db/           # ChromaDB + data_store (tickets, nps, reviews, alerts, jobs)
│   │   ├── mcp_servers/  # reviews_mcp, tickets_mcp, nps_mcp (MCP SDK)
│   │   ├── models/       # Pydantic schemas
│   │   ├── services/     # reviews, tickets, nps service layer
│   │   ├── config.py
│   │   └── main.py
│   ├── scripts/
│   │   └── seed_data.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # Dashboard, IssueHeatmap, AlertFeed, AgentChat, AgentTracer
│   │   ├── api.js
│   │   └── App.jsx
│   └── package.json
├── .env.example
└── README.md
```

## GitHub: public repo + private hosting

- **Public repo** — Share the code so others can clone, fork, and run it. No secrets in the repo.
- **Private hosting** — When you run or deploy the app, you use your own API key and config only on your machine or in your host’s environment (never in the repo).

### 1. Create a **public** repository on GitHub

1. Go to [github.com/new](https://github.com/new).
2. Name the repo (e.g. `crm-agent`).
3. Set visibility to **Public**.
4. Do **not** add a README, .gitignore, or license (this project already has them).
5. Click **Create repository**.

### 2. Push the project to GitHub

From your machine, in the project root:

```bash
cd /path/to/Aiagent

# If you haven’t committed yet:
git add .
git status   # confirm .env does NOT appear
git commit -m "Initial commit: CRM Agent — CX Intelligence"
git branch -M main

# Add your repo and push
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

Replace `YOUR_USERNAME` and `YOUR_REPO_NAME` with your GitHub username and repo name. The code is now **public**; others can clone it and add their own `.env`.

### 3. Keep hosting private (your API key and data)

**Never commit `.env` or your OpenAI API key.** The repo already ignores them via `.gitignore`.

| Where you run the app | How to use your API key (private) |
|------------------------|------------------------------------|
| **Your computer** | Create `.env` in the project root from `.env.example` and add `OPENAI_API_KEY=sk-...`. This file is not pushed to GitHub. |
| **Hosting (Railway, Render, VPS, etc.)** | In that service’s dashboard, set **Environment variables** (e.g. `OPENAI_API_KEY`). The key stays on the host and is never in the repo. |
| **GitHub Actions / CI** | In the repo: **Settings → Secrets and variables → Actions** → add `OPENAI_API_KEY`. Use it in workflows as a secret; it is not in the code. |

So: **public repo** = everyone sees the code; **private hosting** = only your environments (local or deployed) have your key and data.

---

## Host the app (deploy with your API key)

Your code stays on GitHub with **no API key in the repo**. You deploy to a host and set your key in that host’s environment.

### 1. Deploy backend (e.g. Render)

1. Go to [render.com](https://render.com) → Sign in with **GitHub**.
2. **New → Web Service**. Connect your `crm-agent` repo.
3. **Root directory:** `backend`.
4. **Build command:** `pip install -r requirements.txt`
5. **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. **Environment** → Add:
   - `OPENAI_API_KEY` = your key (mark as **Secret**).
   - (Optional) `FRONTEND_URL` = your frontend URL once it’s deployed (for CORS).
7. Deploy. Copy the backend URL (e.g. `https://crm-agent-xxxx.onrender.com`).

### 2. Deploy frontend (e.g. Render Static Site)

1. **New → Static Site**. Same repo.
2. **Root directory:** `frontend`.
3. **Build command:** `npm install && npm run build`
4. **Publish directory:** `dist`
5. **Environment** → Add:
   - `VITE_API_URL` = your backend URL from step 1 (e.g. `https://crm-agent-xxxx.onrender.com`) — **no trailing slash**.
6. Deploy. Copy the frontend URL (e.g. `https://crm-agent-frontend.onrender.com`).

### 3. Connect backend to frontend (CORS)

In the **backend** service on Render, add (or update) environment variable:

- `FRONTEND_URL` = your frontend URL from step 2 (e.g. `https://crm-agent-frontend.onrender.com`).

Redeploy the backend once. The app will then accept requests from your hosted frontend.

### 4. Data after deploy

- **Option A:** Run `python scripts/seed_data.py` locally (with `OPENAI_API_KEY` in `.env`), then use the app’s **Your data** upload to send tickets/reviews/NPS to the deployed backend.
- **Option B:** Use only **Your data** in the deployed app to upload CSV/JSON. ChromaDB search will work after you run a seed or upload enough data; for full embeddings you’d need to run seed once against the deployed backend (e.g. via a one-off run or a small script that calls your deployed API).

Your API key is only in the **backend** service’s environment on Render; it is never in GitHub or the frontend.

## License

MIT.
