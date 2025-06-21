import os
from fastapi import FastAPI
from backend.api.routes import portfolio, transactions, db_refresh, logs, debug
from backend.utils.scheduler import start_scheduled_tasks
from backend.utils.logger import app_logger

# Load .env only in development
DEV_MODE = os.getenv("DEV_MODE", "False").lower() in ("true", "1", "yes")
if DEV_MODE:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=".env")  # Safe even if file is missing
    app_logger.info(".env file loaded in DEV_MODE (api)")

app = FastAPI(
    title="Portfolio Analyzer API",
    description="API to manage and calculate portfolio data.",
    version="1.0.0"
)

app.include_router(portfolio.router, prefix="/portfolio", tags=["Portfolio"])
app.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
app.include_router(db_refresh.router, prefix="/db", tags=["Database"])
app.include_router(logs.router, prefix="/logs", tags=["Logs"])
app.include_router(debug.router, prefix="/debug", tags=["Debug"])

@app.get("/", tags=["Root"])
async def read_root():
    """A root endpoint to confirm the API is running."""
    return {"message": "Portfolio Analyzer API is running"}

start_scheduled_tasks()

app_logger.info("FastAPI app started.")
