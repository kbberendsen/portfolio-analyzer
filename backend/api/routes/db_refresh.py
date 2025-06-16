from fastapi import APIRouter, HTTPException, status
from backend.services.db_refresh import db_refresh
import traceback

router = APIRouter()

@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    tags=["Database"],
    summary="Refresh Database and Parquet Files",
    description="Triggers synchronization between Supabase and local Parquet files."
)
def refresh_database():
    try:
        db_refresh()
        return {"message": "Database refresh completed successfully."}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during database refresh: {e}"
        )