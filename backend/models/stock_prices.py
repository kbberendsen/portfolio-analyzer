from __future__ import annotations
from sqlalchemy import Column, String, Date, Numeric, PrimaryKeyConstraint
from backend.db.base import Base
from pydantic import BaseModel
from datetime import date

class StockPricesTable(Base):
    __tablename__ = "stock_prices"

    ticker = Column(String)
    date = Column(Date)
    price = Column(Numeric)
    fx_rate = Column(Numeric)
    currency_pair = Column(String)

    __table_args__ = (
        PrimaryKeyConstraint('ticker', 'date'),
    )

class StockPrices(BaseModel):
    """
    Defines the data structure for daily stock prices.
    """
    ticker: str
    date: date
    price: float
    fx_rate: float
    currency_pair: str

    class Config:
        from_attributes = True