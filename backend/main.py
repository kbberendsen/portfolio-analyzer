from fastapi import FastAPI
from backend.api.routes import portfolio, transactions, db_refresh

app = FastAPI(
    title="Portfolio Analyzer API",
    description="API to manage and calculate portfolio data.",
    version="1.0.0"
)

# Include routers
app.include_router(portfolio.router, prefix="/portfolio", tags=["Portfolio"])
app.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
app.include_router(db_refresh.router, prefix="/db")

@app.get("/", tags=["Root"])
async def read_root():
    """A root endpoint to confirm the API is running."""
    return {"message": "Portfolio Analyzer API is running"}
