from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from backend.services.portfolio import calc_portfolio
from backend.utils.logger import app_logger

router = APIRouter()

@router.post(
    "/calculate", 
    status_code=status.HTTP_200_OK,
    tags=["Portfolio"],
    summary="Trigger Portfolio Performance Calculation",
    description="Triggers the backend process to re-calculate portfolio performance data."
)
def run_portfolio_calculation():
    """
    This endpoint kicks off the data processing job.
    """
    try:
        # Call the function to perform the calculation.
        calc_portfolio()
        
        return {"message": "Portfolio calculation triggered successfully"}
        
    except Exception as e:
        # If the calculation fails, return a 500 error with the details.
        raise HTTPException(
            status_code=500, 
            detail=f"An unexpected error occurred during portfolio calculation: {e}"
        )