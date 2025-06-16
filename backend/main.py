from fastapi import FastAPI
from backend.api.routes import portfolio, transactions, db_refresh, logs, debug
from backend.utils.scheduler import start_scheduled_tasks
from backend.utils.logger import app_logger

app_logger.info("FastAPI app is starting...")

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
