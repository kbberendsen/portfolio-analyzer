import os
import backend.streamlit_utils.constants as constants

LOGS_DIR = constants.LOGS_DIR

def get_log_files():
    if not os.path.exists(LOGS_DIR):
        return []
    return [f for f in os.listdir(LOGS_DIR) if os.path.isfile(os.path.join(LOGS_DIR, f))]

def read_last_n_lines_reversed(filename, n=100):
    with open(os.path.join(LOGS_DIR, filename), 'r', encoding='utf-8') as f:
        lines = f.readlines()
    return "".join(lines[-n:][::-1])