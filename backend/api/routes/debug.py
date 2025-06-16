# backend/routes/debug.py
from fastapi import APIRouter
from backend.utils.scheduler import scheduled_portfolio_job,  scheduled_db_refresh_job

router = APIRouter()

@router.get("/trigger/calculate")
def trigger_now():
    scheduled_portfolio_job()
    return {"message": "Triggered portfolio job manually"}

@router.get("/trigger/db_refresh")
def trigger_now():
    scheduled_db_refresh_job()
    return {"message": "Triggered db_refresh manually"}