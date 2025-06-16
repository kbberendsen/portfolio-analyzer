from fastapi import APIRouter, HTTPException
from typing import List

router = APIRouter()

SCHEDULER_LOG_FILE_PATH = "logs/scheduler.log"
APP_LOG_FILE_PATH = "logs/app.log"

@router.get("/scheduler")
def read_logs(lines: int = 50) -> List[str]:
    try:
        with open(SCHEDULER_LOG_FILE_PATH) as f:
            return f.readlines()[-lines:]
    except FileNotFoundError:
        raise HTTPException(404, "Log file not found")
    
@router.get("/app")
def read_app_logs(lines: int = 50) -> List[str]:
    try:
        with open(APP_LOG_FILE_PATH) as f:
            return f.readlines()[-lines:]
    except FileNotFoundError:
        raise HTTPException(404, "App log file not found")