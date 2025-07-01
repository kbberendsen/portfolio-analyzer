# Global status variable
_refresh_status = "idle"  # idle, running, failed

def set_refresh_status(value: str):
    global _refresh_status
    _refresh_status = value
    
def get_refresh_status() -> str:
    return _refresh_status

# --- DB Sync Status ---
_db_sync_status = "idle"  # idle, running, failed

def set_db_sync_status(value: str):
    global _db_sync_status
    _db_sync_status = value

def get_db_sync_status() -> str:
    return _db_sync_status