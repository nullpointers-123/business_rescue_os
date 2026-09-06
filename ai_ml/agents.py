"""
AI/ML — Nidhi
--------------
All the reasoning agents from the pitch (Sales, Inventory, Supplier, Customer,
Finance, Strategy) powered by Groq's free/fast LLM API, plus the orchestration
function `run_pipeline()` that ties them together with the live
Web Research Agent.

Setup:
    pip install groq
    export GROQ_API_KEY="your_free_key_from_console.groq.com"

Free model used: "llama-3.3-70b-versatile" (Groq's free tier, very fast).
"""

import os
import json
from groq import Groq
from ai_ml.web_research_agent import find_supplier_options

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"


def _ask(system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
    kwargs = {}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        **kwargs,
    )
    return resp.choices[0].message.content


# ---------------------------------------------------------------------------
# Individual agents (each = one focused LLM call)
# ---------------------------------------------------------------------------

def sales_agent(product: dict) -> str:
    return _ask(
        "You are a Sales Analysis Agent for a retail business rescue system. "
        "Be concise (2-3 sentences).",
        f"Product data: {json.dumps(product)}. Why might sales be falling for this product?",
    )


def inventory_agent(product: dict) -> str:
    return _ask(
        "You are an Inventory Risk Agent. Be concise (2-3 sentences).",
        f"Product data: {json.dumps(product)}. Assess excess/slow-moving inventory risk.",
    )


def finance_agent(problem: dict) -> str:
    return _ask(
        "You are a Finance Risk Agent. Be concise (2-3 sentences).",
        f"Problem data: {json.dumps(problem)}. Summarize the financial risk in plain terms.",
    )


def strategy_agent(problem: dict, sales_insight: str, inventory_insight: str,
                    finance_insight: str, external_options: list) -> dict:
    """
    The final decision-making agent. Combines everything (including the
    LIVE web research results) and returns a structured recovery plan as JSON,
    matching the API contract in the README.
    """
    system_prompt = (
        "You are the Strategy Agent for 'Business Rescue OS'. You receive analysis "
        "from other agents plus REAL web search results about external suppliers/"
        "distributors. You must compare options (do nothing / discount / transfer "
        "to another branch / external distributor / combined plan) and output ONLY "
        "valid JSON with this exact shape, no prose outside the JSON:\n"
        "{\n"
        '  "recommended_option": string,\n'
        '  "reason": string,\n'
        '  "expected_recovery": number,\n'
        '  "remaining_risk": number,\n'
        '  "actions": [{"units": number, "action": string}]\n'
        "}\n"
        "Base expected_recovery/remaining_risk on the value_at_risk given, and keep "
        "numbers realistic (recovery should be less than value_at_risk)."
    )

    user_prompt = json.dumps({
        "problem": problem,
        "sales_insight": sales_insight,
        "inventory_insight": inventory_insight,
        "finance_insight": finance_insight,
        "external_options_found_on_web": external_options,
    })

    raw = _ask(system_prompt, user_prompt, json_mode=True)
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Full pipeline — this is what the backend calls
# ---------------------------------------------------------------------------

def run_pipeline(problem: dict, product: dict) -> dict:
    """
    problem: dict from Problem table (units_at_risk, value_at_risk, root_cause...)
    product: dict from Product table (name, category, branch, units_in_stock...)
    Returns the full Recovery Report matching the shared API contract.
    """
    sales_insight = sales_agent(product)
    inventory_insight = inventory_agent(product)
    finance_insight = finance_agent(problem)

    # 🌐 LIVE internet search — this is the "AI searches the internet" step
    external_options_raw = find_supplier_options(
        product_name=product.get("name", ""),
        category=product.get("category", "general"),
    )

    # Turn raw search hits into the option shape used in the pitch
    external_options = [
        {
            "name": o["title"],
            "reason": o["snippet"][:180] if o.get("snippet") else "",
            "source_url": o["url"],
        }
        for o in external_options_raw if o.get("url")
    ]

    plan = strategy_agent(problem, sales_insight, inventory_insight,
                           finance_insight, external_options)

    return {
        "problem": {
            "product": product.get("name"),
            "units_at_risk": problem.get("units_at_risk"),
            "value_at_risk": problem.get("value_at_risk"),
            "root_cause": problem.get("root_cause"),
        },
        "external_options": external_options,
        "recommended_option": plan.get("recommended_option"),
        "recovery_plan": {
            "expected_recovery": plan.get("expected_recovery"),
            "actions": plan.get("actions", []),
            "remaining_risk": plan.get("remaining_risk"),
        },
    }


if __name__ == "__main__":
    # Quick manual test: python -m ai_ml.agents
    demo_product = {"name": "Product X", "category": "general retail",
                     "branch": "Branch A", "units_in_stock": 500}
    demo_problem = {"units_at_risk": 300, "value_at_risk": 30000,
                     "root_cause": "Declining demand + excess inventory"}
    report = run_pipeline(demo_problem, demo_product)
    print(json.dumps(report, indent=2))
