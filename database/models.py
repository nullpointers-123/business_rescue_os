"""
Integration & Database — Shubh
--------------------------------
Defines the core tables for Business Rescue OS using SQLAlchemy + SQLite.
SQLite is used because it's free, file-based, and needs zero setup — perfect
for a hackathon demo. Swapping to Postgres later only means changing the
DB_URL in db.py.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    branch = Column(String, nullable=False)
    units_in_stock = Column(Integer, default=0)
    unit_price = Column(Float, default=0.0)
    category = Column(String, default="general")

    problems = relationship("Problem", back_populates="product")


class Problem(Base):
    """A detected business problem (e.g. excess inventory, falling sales)."""
    __tablename__ = "problems"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    problem_type = Column(String, nullable=False)   # e.g. "excess_inventory"
    units_at_risk = Column(Integer, default=0)
    value_at_risk = Column(Float, default=0.0)
    root_cause = Column(Text, default="")
    status = Column(String, default="detected")     # detected -> analyzed -> approved
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="problems")


class RecoveryReport(Base):
    """Stores the final agent-generated recovery plan for a problem."""
    __tablename__ = "recovery_reports"

    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey("problems.id"))
    external_options_json = Column(Text)   # JSON string of web research results
    recommended_option = Column(String)
    expected_recovery = Column(Float)
    remaining_risk = Column(Float)
    plan_json = Column(Text)               # JSON string of the action plan
    approved = Column(Integer, default=0)  # 0/1 boolean
    created_at = Column(DateTime, default=datetime.utcnow)
