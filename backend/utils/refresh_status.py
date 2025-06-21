# Global status variable
_refresh_status = "idle"  # idle, running, failed

def set_refresh_status(value: str):
    global _refresh_status
    _refresh_status = value
    
def get_refresh_status() -> str:
    return _refresh_status