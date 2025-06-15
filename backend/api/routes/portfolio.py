from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from backend.services.portfolio import calc_portfolio
import traceback

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
    A successful request will result in a 200 code response.
    """
    try:
        # Call the function to perform the calculation.
        calc_portfolio()
        
        # Explicitly return a 200 response to confirm
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Portfolio calculation completed successfully."
            }
        )
        
    except Exception as e:
        traceback.print_exc()
        # If the calculation fails, return a 500 error with the details.
        raise HTTPException(
            status_code=500, 
            detail=f"An unexpected error occurred during portfolio calculation: {e}"
        )