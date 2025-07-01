from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.utils.db import get_db
from backend.models.portfolio_daily import PortfolioPerformanceDailyTable, PortfolioPerformanceDaily
from backend.models.stock_prices import StockPricesTable, StockPrices

router = APIRouter()

@router.get("/portfolio-daily", response_model=List[PortfolioPerformanceDaily], tags=["Data"])
def get_portfolio_performance_daily(db: Session = Depends(get_db)):
    try:
        results = db.query(PortfolioPerformanceDailyTable).all()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load portfolio data: {e}")

@router.get("/stock-prices", response_model=List[StockPrices], tags=["Data"])
def get_stock_data(db: Session = Depends(get_db)):
    try:
        results = db.query(StockPricesTable).all()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load stock data: {e}")