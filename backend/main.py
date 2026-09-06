"""
Backend — Adithya
-------------------
The Orchestrator AI from the architecture diagram. A FastAPI server that:
  1. Exposes detected problems from the DB (Shubh's models)
  2. Runs the full agent pipeline (Nidhi's ai_ml/agents.py) on demand
  3. Stores the resulting Recovery Report
  4. Lets a human approve the plan (per the PDF: AI never auto-executes)

Run:
    uvicorn backend.main:app --reload --port 8000

Then open http://localhost:8000/docs for the auto-generated API playground,
or open frontend/index.html which talks to this server.
"""

import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database.db import init_db, SessionLocal
from database.models import Product, Problem, RecoveryReport
from ai_ml.agents import run_pipeline

app = FastAPI(title="Business Rescue OS")

# Allow the plain-HTML frontend (opened via file:// or a dev server) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/problems")
def list_problems():
    db = SessionLocal()
    try:
        problems = db.query(Problem).all()
        return [
            {
                "id": p.id,
                "product_id": p.product_id,
                "product_name": p.product.name if p.product else None,
                "problem_type": p.problem_type,
                "units_at_risk": p.units_at_risk,
                "value_at_risk": p.value_at_risk,
                "root_cause": p.root_cause,
                "status": p.status,
            }
            for p in problems
        ]
    finally:
        db.close()


@app.post("/api/analyze/{problem_id}")
def analyze(problem_id: int):
    """Runs Sales -> Inventory -> Finance -> Web Research -> Strategy agents."""
    db = SessionLocal()
    try:
        problem = db.query(Problem).filter(Problem.id == problem_id).first()
        if not problem:
            raise HTTPException(status_code=404, detail="Problem not found")

        product = problem.product

        problem_dict = {
            "units_at_risk": problem.units_at_risk,
            "value_at_risk": problem.value_at_risk,
            "root_cause": problem.root_cause,
        }
        product_dict = {
            "name": product.name,
            "category": product.category,
            "branch": product.branch,
            "units_in_stock": product.units_in_stock,
        }

        # 🔴 This is the call that runs every agent, including the LIVE
        #     internet search for real suppliers/distributors.
        report = run_pipeline(problem_dict, product_dict)

        # Persist the report
        db_report = RecoveryReport(
            problem_id=problem.id,
            external_options_json=json.dumps(report["external_options"]),
            recommended_option=report["recommended_option"],
            expected_recovery=report["recovery_plan"]["expected_recovery"],
            remaining_risk=report["recovery_plan"]["remaining_risk"],
            plan_json=json.dumps(report["recovery_plan"]["actions"]),
        )
        problem.status = "analyzed"
        db.add(db_report)
        db.commit()

        return report
    finally:
        db.close()


@app.post("/api/approve/{problem_id}")
def approve(problem_id: int):
    """Human-in-the-loop approval — the AI never contacts suppliers itself."""
    db = SessionLocal()
    try:
        problem = db.query(Problem).filter(Problem.id == problem_id).first()
        if not problem:
            raise HTTPException(status_code=404, detail="Problem not found")

        report = (
            db.query(RecoveryReport)
            .filter(RecoveryReport.problem_id == problem_id)
            .order_by(RecoveryReport.id.desc())
            .first()
        )
        if not report:
            raise HTTPException(status_code=400, detail="No recovery report to approve yet")

        report.approved = 1
        problem.status = "approved"
        db.commit()

        return {"status": "approved", "problem_id": problem_id}
    finally:
        db.close()
