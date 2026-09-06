"""
Integration & Database — Shubh
--------------------------------
Run this once to create the DB and load the exact example from the pitch PDF:
500 units of Product X, 300 at risk, ₹30,000 value at risk.

Run:  python -m database.seed_data
"""

from database.db import init_db, SessionLocal
from database.models import Product, Problem


def seed():
    init_db()
    db = SessionLocal()

    # Avoid duplicate seeding
    if db.query(Product).first():
        print("DB already seeded.")
        return

    product = Product(
        name="Product X",
        branch="Branch A",
        units_in_stock=500,
        unit_price=100.0,
        category="general_retail",
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    problem = Problem(
        product_id=product.id,
        problem_type="excess_inventory",
        units_at_risk=300,
        value_at_risk=30000.0,
        root_cause="Declining demand + excess inventory in Branch A",
        status="detected",
    )
    db.add(problem)
    db.commit()

    print(f"Seeded product id={product.id}, problem id={problem.id}")
    db.close()


if __name__ == "__main__":
    seed()
