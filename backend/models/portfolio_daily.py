from __future__ import annotations
from sqlalchemy import Column, String, Integer, Date, Numeric, PrimaryKeyConstraint
from backend.db.base import Base
from pydantic import BaseModel
from datetime import date

class PortfolioPerformanceDailyTable(Base):
    __tablename__ = "portfolio_performance_daily"

    product = Column(String)
    ticker = Column(String)
    quantity = Column(Integer)
    start_date = Column(Date)
    end_date = Column(Date)
    avg_cost = Column(Numeric)
    cost_basis = Column(Numeric)
    total_cost = Column(Numeric)
    transaction_costs = Column(Numeric)
    current_value = Column(Numeric)
    current_money_weighted_return = Column(Numeric)
    realized_return = Column(Numeric)
    net_return = Column(Numeric)
    current_performance_percentage = Column(Numeric)
    net_performance_percentage = Column(Numeric)

    __table_args__ = (
        PrimaryKeyConstraint('ticker', 'end_date'),
    )

class PortfolioPerformanceDaily(BaseModel):
    """
    Defines the data structure for daily portfolio performance.
    """
    product: str
    ticker: str
    quantity: int
    start_date: date
    end_date: date
    avg_cost: float
    cost_basis: float
    total_cost: float
    transaction_costs: float
    current_value: float
    current_money_weighted_return: float
    realized_return: float
    net_return: float
    current_performance_percentage: float
    net_performance_percentage: float

    class Config:
        from_attributes = True