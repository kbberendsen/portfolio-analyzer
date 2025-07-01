# backend/routes/debug.py
from fastapi import APIRouter, HTTPException
from backend.utils.scheduler import scheduled_portfolio_job, scheduled_db_sync_job
from backend.services.transactions import get_transactions
from backend.utils.db import check_postgres_connection, delete_all_data
from backend.utils.logger import app_logger

router = APIRouter()

@router.post("/trigger/calculate")
def trigger_now():
    scheduled_portfolio_job()
    return {"message": "Triggered portfolio job manually"}

@router.post("/trigger/db_refresh")
def trigger_db_refresh():
    scheduled_db_sync_job()
    return {"message": "Triggered db_sync manually"}

@router.delete("/delete-data")
def reset_db():
    """
    Deletes all rows from portfolio_performance_daily and stock_prices tables.
    """
    delete_all_data()
    return {"status": "success", "message": "All data deleted from tables."}

@router.get("/health/db")
def health_check_db():
    if check_postgres_connection():
        return {"status": "ok", "database": "connected"}
    else:
        raise HTTPException(status_code=500, detail="Cannot connect to database")
