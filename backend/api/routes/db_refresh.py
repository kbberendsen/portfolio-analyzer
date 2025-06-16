from fastapi import APIRouter, HTTPException, status
import os
from backend.services.db_refresh import db_refresh
from backend.utils.logger import app_logger

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
        app_logger.info("Database refresh triggered via /refresh endpoint.")
        db_refresh()
        return {"message": "Database refresh completed successfully."}
    except Exception as e:
        app_logger.error("Error during database refresh", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during database refresh: {e}"
        )
    
@router.post(
    "/initial-db-load",
    status_code=status.HTTP_200_OK,
    tags=["Database"],
    summary="Initial Database Load",
    description="Triggers initial database/parquet sync only if parquet files are missing."
)
def initial_db_load():
    try:
        app_logger.info("Initial DB load check started.")
        output_folder = "output"
        has_parquet = any(f.name.endswith(".parquet") for f in os.scandir(output_folder))

        if not has_parquet:
            app_logger.info("No parquet files found. Triggering initial DB load.")
            db_refresh()
            return {"message": "No parquet files found. Initial DB load triggered."}
        else:
            app_logger.info("Parquet files exist. No initial DB load needed.")
            return {"message": "Parquet files exist. No initial DB load needed."}
    except Exception as e:
        app_logger.error("Error during initial DB load check", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while checking parquet files: {e}"
        )