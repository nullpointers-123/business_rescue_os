# 🚨 Business Rescue OS — Team Orchestration Plan

A multi-agent AI system (Groq-powered) that detects business problems, researches
real solutions live from the internet, and recommends a recovery plan for human approval.

---

## 1. Team Roles & Responsibilities

| Person | Role | Owns |
|---|---|---|
| **Shreesh** | UI/UX | Dashboard (`frontend/app.py`, Streamlit), problem/recovery visualization, "Approve Plan" flow |
| **Adithya** | Backend | FastAPI orchestrator (`backend/main.py`), agent routing, REST API for the UI |
| **Nidhi** | AI/ML | All Groq-powered agents + the live Web Research Agent (`ai_ml/`) |
| **Shubh** | Integration & Database | Data models, seed data, wiring backend ↔ AI/ML ↔ DB (`database/`) |

Everything is plain Python + one HTML file — no heavy build tooling, so the whole
team can run it in minutes during the hackathon.

---

## 2. System Architecture (matches your PDF)

```
BUSINESS DATA (SQLite, seeded by Shubh)
        ↓
ORCHESTRATOR AI (FastAPI, Adithya)
        ↓
 ┌───────────┬─────────────┬────────────┐
 ↓           ↓             ↓            ↓
SALES     INVENTORY    SUPPLIER     CUSTOMER   (Nidhi — Groq LLM agents)
AGENT     AGENT        AGENT        AGENT
 └───────────┴─────────────┴────────────┘
        ↓
WEB RESEARCH AGENT (Nidhi — DuckDuckGo live search, no key needed)
        ↓
   Search external supplier/distributor options
        ↓
FINANCE AGENT → STRATEGY AGENT (Groq LLM, Nidhi)
        ↓
Risk + Expected Recovery comparison
        ↓
Recovery Plan JSON → Backend API → Dashboard (Shreesh)
        ↓
HUMAN APPROVAL (button in UI, hits /approve endpoint)
```

---

## 3. Free Tools & Sources to Use (all $0 for hackathon use)

| Purpose | Tool | Why | Link |
|---|---|---|---|
| LLM inference (all agents) | **Groq API** | Free tier, extremely fast Llama 3.1/3.3 inference | https://console.groq.com |
| Live web search (suppliers/distributors) | **DuckDuckGo Search (`ddgs` python package)** | 100% free, no API key, no rate-limit signup needed | https://pypi.org/project/ddgs/ |
| Backup/optional richer web search | **Tavily API** | Free tier (1,000 searches/month), built for AI agents, gives clean summarized results | https://tavily.com |
| Backend framework | **FastAPI** | Free, fast, auto-generates API docs at `/docs` | https://fastapi.tiangolo.com |
| Database | **SQLite + SQLAlchemy** | Free, zero-setup, file-based — perfect for a hackathon | https://www.sqlalchemy.org |
| Frontend | **Streamlit** | Pure Python, no HTML/CSS/JS needed, free, works instantly | https://streamlit.io |
| Hosting (optional, for demo) | **Render.com free tier** or **ngrok** (tunnel localhost) | Free, quick public demo link | https://render.com / https://ngrok.com |

> Pick DuckDuckGo (`ddgs`) as your primary web search since it needs **zero signup**.
> Only add Tavily if you have time and want higher-quality summarized results — it needs a free API key from tavily.com.

---

## 4. Timeline (typical 24–36hr hackathon)

| Time | Everyone |
|---|---|
| Hour 0–1 | Team syncs on this README, agrees on API contract (JSON shapes below), Shubh creates DB, Adithya scaffolds FastAPI skeleton |
| Hour 1–6 | Nidhi builds Groq agents + web research agent in isolation (test via `python ai_ml/agents.py`) |
| Hour 1–6 | Shreesh builds static dashboard against **mock JSON** (doesn't need backend yet) |
| Hour 1–6 | Adithya wires FastAPI routes, Shubh wires DB models + seed data |
| Hour 6–12 | Integration: Adithya calls Nidhi's agents from backend routes; Shubh connects DB reads/writes |
| Hour 12–18 | Shreesh connects dashboard to real backend endpoints, replaces mock data |
| Hour 18–24 | End-to-end test: seed a "problem" → orchestrator runs → web research → recovery plan → approve button |
| Hour 24+ | Polish UI, record demo video, prep pitch using the one-liner from the PDF |

---

## 5. Shared API Contract (agree on this FIRST, before splitting up)

**`GET /api/problems`** → list of detected problems (from DB)
**`POST /api/analyze/{problem_id}`** → runs the full agent pipeline, returns a Recovery Report:

```json
{
  "problem": {
    "product": "Product X",
    "units_at_risk": 300,
    "value_at_risk": 30000,
    "root_cause": "Declining demand + excess inventory"
  },
  "external_options": [
    {"name": "Distributor A", "reason": "accepts this product category", "source_url": "..."},
    {"name": "Supplier B", "reason": "better pricing", "source_url": "..."}
  ],
  "recommended_option": "Distributor B",
  "recovery_plan": {
    "expected_recovery": 29500,
    "actions": [
      {"units": 150, "action": "Transfer to high-demand branch"},
      {"units": 100, "action": "Discount"},
      {"units": 50, "action": "Explore external distributor"}
    ],
    "remaining_risk": 500
  }
}
```

**`POST /api/approve/{problem_id}`** → marks plan as approved in DB.

This exact JSON shape is what Shreesh's dashboard renders, Adithya's backend returns,
and Nidhi's `strategy_agent` must output. Agreeing on this early means all 4 of you
can work in parallel without blocking each other.

---

## 6. Folder Structure

```
business_rescue_os/
├── README.md                  ← this file
├── backend/            (Adithya)
│   ├── main.py
│   └── requirements.txt
├── ai_ml/              (Nidhi)
│   ├── agents.py
│   ├── web_research_agent.py
│   └── requirements.txt
├── database/           (Shubh)
│   ├── models.py
│   ├── db.py
│   └── seed_data.py
└── frontend/           (Shreesh)
    ├── app.py          ← Streamlit dashboard (pure Python)
    └── requirements.txt
```

## 7. How to run (whole team, end to end — 100% Python, two terminals)

```bash
# 1. Get a free Groq API key: https://console.groq.com/keys
export GROQ_API_KEY="your_key_here"

# 2. Install deps
pip install -r backend/requirements.txt
pip install -r ai_ml/requirements.txt
pip install -r frontend/requirements.txt

# 3. Seed the database
python -m database.seed_data

# 4. Terminal 1 — run the backend (loads the AI/ML agents)
uvicorn backend.main:app --reload --port 8000

# 5. Terminal 2 — run the dashboard
streamlit run frontend/app.py
```

Streamlit opens automatically in your browser (usually http://localhost:8501)
and talks to the FastAPI backend on port 8000.
