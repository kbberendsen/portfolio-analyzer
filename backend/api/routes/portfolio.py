from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
from backend.services.portfolio import calc_portfolio, background_refresh
from backend.utils.refresh_flag import set_refresh_done, check_refresh_flag

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

@router.post("/refresh", status_code=status.HTTP_200_OK, tags=["Portfolio"])
def refresh_portfolio(background_tasks: BackgroundTasks):
    set_refresh_done(False)  # reset flag
    background_tasks.add_task(background_refresh)
    return {"message": "Portfolio refresh started in background"}

@router.get("/refresh/status", tags=["Portfolio"])
def refresh_status():
    return {"done": check_refresh_flag()}
