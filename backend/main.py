from dotenv import load_dotenv
from backend.utils.logger import app_logger
load_dotenv(dotenv_path=".env")
app_logger.info("[STARTUP] .env file loaded")

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
app_logger.info("[STARTUP] Imported FastAPI and core libraries.")

from backend.api.routes import db_supabase_sync, portfolio, transactions, data, logs, debug
app_logger.info("[STARTUP] Imported API route modules.")

from backend.utils.scheduler import start_scheduled_tasks, scheduler
app_logger.info("[STARTUP] Imported scheduler utilities.")

from backend.utils.db import create_tables, wait_for_db
app_logger.info("[STARTUP] Imported database utilities.")

app_logger.info("[STARTUP] All modules imported successfully. Proceeding with app setup.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles application startup and shutdown events."""
    # --- Startup ---
    app_logger.info("[STARTUP] Application startup sequence initiated.")
    try:
        wait_for_db()
        create_tables()
        start_scheduled_tasks()
        app_logger.info("[STARTUP] Application startup complete. API is ready.")
    except Exception as e:
        app_logger.exception("[STARTUP] Fatal error during application startup")
        raise

    yield
    
    # --- Shutdown ---
    app_logger.info("[SHUTDOWN] Application shutdown sequence initiated.")
    if scheduler.running:
        scheduler.shutdown()
    app_logger.info("[SHUTDOWN] Application shutdown complete.")

app = FastAPI(
    title="Portfolio Analyzer API",
    description="API to manage and calculate portfolio data.",
    version="1.0.0",
    lifespan=lifespan
)

app_logger.info("[STARTUP] Including API routers...")
app.include_router(portfolio.router, prefix="/portfolio", tags=["Portfolio"])
app.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
app.include_router(data.router, prefix="/data", tags=["Data"])
app.include_router(db_supabase_sync.router, prefix="/db", tags=["Database"])
app.include_router(logs.router, prefix="/logs", tags=["Logs"])
app.include_router(debug.router, prefix="/debug", tags=["Debug"])
app_logger.info("[STARTUP] API routers included.")

@app.get("/", tags=["Root"])
async def read_root():
    """A root endpoint to confirm the API is running."""
    return {"message": "Portfolio Analyzer API is running"}
