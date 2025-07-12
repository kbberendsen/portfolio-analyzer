from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date
from backend.utils.db import get_db
from backend.models.portfolio_daily import PortfolioPerformanceDailyTable, PortfolioPerformanceDaily
from backend.models.stock_prices import StockPricesTable, StockPrices

router = APIRouter()

@router.get("/portfolio-daily", response_model=List[PortfolioPerformanceDaily], tags=["Data"])
def get_portfolio_performance_daily(
    db: Session = Depends(get_db),
    products: Optional[List[str]] = Query(None, description="List of product names to filter by."),
    start_date: Optional[date] = Query(None, description="The start date for the data range (inclusive)."),
    end_date: Optional[date] = Query(None, description="The end date for the data range (inclusive)."),
):
    """
    Retrieves daily portfolio performance data.
    Can be filtered by a list of products and a date range.
    """
    try:
        query = db.query(PortfolioPerformanceDailyTable)

        if products:
            query = query.filter(PortfolioPerformanceDailyTable.product.in_(products))
        
        if start_date:
            # Filter records where the performance date is on or after the start_date
            query = query.filter(PortfolioPerformanceDailyTable.end_date >= start_date)

        if end_date:
            # Filter records where the performance date is on or before the end_date
            query = query.filter(PortfolioPerformanceDailyTable.end_date <= end_date)

        results = query.all()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load portfolio data: {e}")

@router.get("/portfolio-metadata", tags=["Data"], summary="Get Portfolio Metadata for Filters")
def get_portfolio_metadata(db: Session = Depends(get_db)):
    """
    Retrieves distinct product names and the overall date range from the portfolio data.
    Used to populate filter controls in the frontend without loading the entire dataset.
    """
    try:
        # Get min and max dates from the 'end_date' column
        min_date_res, max_date_res = db.query(
            func.min(PortfolioPerformanceDailyTable.end_date),
            func.max(PortfolioPerformanceDailyTable.end_date)
        ).one()

        # Get unique product names
        product_rows = db.query(PortfolioPerformanceDailyTable.product).distinct().all()
        # The result is a list of tuples, e.g., [('Product A',), ('Product B',)], extract the first element
        products = sorted([row[0] for row in product_rows if row[0] is not None])

        return {
            "products": products,
            "min_date": min_date_res.isoformat() if min_date_res else None,
            "max_date": max_date_res.isoformat() if max_date_res else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load portfolio metadata: {e}")

@router.get("/stock-prices", response_model=List[StockPrices], tags=["Data"])
def get_stock_data(db: Session = Depends(get_db)):
    try:
        results = db.query(StockPricesTable).all()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load stock data: {e}")