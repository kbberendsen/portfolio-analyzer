from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from backend.services.db_supabase_sync import db_supabase_sync
from backend.utils.logger import app_logger
from backend.utils.refresh_status import get_db_sync_status

router = APIRouter()

@router.post(
    "/sync_db",
    status_code=status.HTTP_200_OK,
    tags=["Database"],
    summary="Sync local DB with Supabase",
    description=(
        "Triggers synchronization between Supabase and the local database. "
        "If the local DB is empty, it restores from Supabase. "
        "Otherwise, it backs up the local DB to Supabase."
    )
)
def sync_database(background_tasks: BackgroundTasks):
    """
    This endpoint triggers the database synchronization logic.
    """
    current_status = get_db_sync_status()
    if current_status == "running":
        raise HTTPException(status_code=409, detail="Database sync already in progress.")

    try:
        app_logger.info("[DB-SYNC] Database sync triggered via /sync_db endpoint.")
        background_tasks.add_task(db_supabase_sync)
        return {"message": "Database synchronization started in background."}
    except Exception as e:
        app_logger.error("Error during database synchronization", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during database synchronization: {e}"
        )

@router.get("/sync_db/status", tags=["Database"])
def sync_status():
    """Returns the current status of the DB sync process."""
    return {"status": get_db_sync_status()}