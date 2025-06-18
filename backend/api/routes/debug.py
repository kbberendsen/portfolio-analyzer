# backend/routes/debug.py
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from backend.utils.scheduler import scheduled_portfolio_job,  scheduled_db_refresh_job
from backend.services.transactions import get_transactions
from backend.utils.logger import app_logger
import datetime

router = APIRouter()

@router.get("/trigger/calculate")
def trigger_now():
    scheduled_portfolio_job()
    return {"message": "Triggered portfolio job manually"}

@router.get("/trigger/db_refresh")
def trigger_db_refresh():
    scheduled_db_refresh_job()
    return {"message": "Triggered db_refresh manually"}