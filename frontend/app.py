"""
UI/UX — Shreesh
-----------------
Pure Python dashboard using Streamlit (no HTML/JS needed).
Talks to Adithya's FastAPI backend over HTTP.

Setup:
    pip install streamlit requests

Run (in a separate terminal, while the backend is running on :8000):
    streamlit run frontend/app.py
"""

import requests
import streamlit as st

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="Business Rescue OS", page_icon="🚨", layout="wide")

st.title("🚨 Business Rescue OS")
st.caption("Ops console — live multi-agent monitoring")

if "report" not in st.session_state:
    st.session_state.report = None
if "current_problem_id" not in st.session_state:
    st.session_state.current_problem_id = None
if "approved" not in st.session_state:
    st.session_state.approved = False


@st.cache_data(ttl=5)
def fetch_problems():
    resp = requests.get(f"{API_BASE}/api/problems", timeout=10)
    resp.raise_for_status()
    return resp.json()


def run_analysis(problem_id: int):
    with st.spinner("Running agents: Sales → Inventory → Finance → Web Research → Strategy…"):
        resp = requests.post(f"{API_BASE}/api/analyze/{problem_id}", timeout=60)
        resp.raise_for_status()
        st.session_state.report = resp.json()
        st.session_state.current_problem_id = problem_id
        st.session_state.approved = False


def approve_plan(problem_id: int):
    resp = requests.post(f"{API_BASE}/api/approve/{problem_id}", timeout=10)
    resp.raise_for_status()
    st.session_state.approved = True


# ---------------------------------------------------------------------------
# Section 1: detected problems
# ---------------------------------------------------------------------------
st.subheader("Detected problems")

try:
    problems = fetch_problems()
except requests.exceptions.RequestException:
    st.error("Can't reach the backend. Make sure `uvicorn backend.main:app` is running on port 8000.")
    st.stop()

if not problems:
    st.info("No problems detected yet. Run `python -m database.seed_data` to load the demo data.")

for p in problems:
    with st.container(border=True):
        col1, col2, col3 = st.columns([4, 2, 1.5])
        with col1:
            st.markdown(f"**{p['product_name']} — {p['problem_type'].replace('_', ' ')}**")
            st.caption(f"{p['root_cause']} · {p['units_at_risk']} units at risk · status: {p['status']}")
        with col2:
            st.markdown(f"### ₹{p['value_at_risk']:,.0f}")
            st.caption("Value at risk")
        with col3:
            st.button("Analyze", key=f"analyze_{p['id']}",
                       on_click=run_analysis, args=(p["id"],))

# ---------------------------------------------------------------------------
# Section 2: recovery report
# ---------------------------------------------------------------------------
report = st.session_state.report
if report:
    st.divider()
    st.subheader("Recovery report")

    st.markdown(f"### {report['problem']['product']} — {report['problem']['units_at_risk']} units at risk")
    st.caption(report["problem"]["root_cause"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Value at risk", f"₹{report['problem']['value_at_risk']:,.0f}")
    c2.metric("Expected recovery", f"₹{report['recovery_plan']['expected_recovery']:,.0f}")
    c3.metric("Remaining risk", f"₹{report['recovery_plan']['remaining_risk']:,.0f}")

    st.markdown("#### 🌐 External options found on the web")
    for opt in report["external_options"]:
        badge = " ✅ **Recommended**" if opt["name"] == report["recommended_option"] else ""
        st.markdown(f"**{opt['name']}**{badge}")
        if opt.get("reason"):
            st.caption(opt["reason"])
        if opt.get("source_url"):
            st.markdown(f"[{opt['source_url']}]({opt['source_url']})")
        st.markdown("---")

    st.markdown("#### 💡 Recommended recovery plan")
    for action in report["recovery_plan"]["actions"]:
        st.markdown(f"- **{action['units']} units** → {action['action']}")

    st.markdown("#### 👤 Human approval")
    if st.session_state.approved:
        st.success("Plan approved. Nothing is contacted automatically — this is a record for your team.")
    else:
        st.button("APPROVE PLAN", type="primary",
                   on_click=approve_plan, args=(st.session_state.current_problem_id,))
