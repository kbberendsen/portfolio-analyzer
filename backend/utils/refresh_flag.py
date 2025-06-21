# Simple in-memory flag (works for single-process server)
_refresh_done = False

def set_refresh_done(value: bool):
    global _refresh_done
    _refresh_done = value

def check_refresh_flag() -> bool:
    return _refresh_done