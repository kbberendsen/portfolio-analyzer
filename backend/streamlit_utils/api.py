import requests
import streamlit as st
import os

# Base URL from environment variable
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


def post_api_request(endpoint: str, success_message: str = None, show_info: bool = False) -> bool:
    """Generic POST request handler for API calls in Streamlit."""
    try:
        response = requests.post(endpoint)
        response.raise_for_status()
        if success_message:
            st.success(success_message)
        elif show_info:
            st.info(response.json().get("message", "Success"))
        return True
    except requests.exceptions.RequestException as e:
        if e.response is not None and e.response.status_code == 409:
            error_msg = e.response.json().get("detail", "A refresh is already in progress.")
            st.warning(error_msg)
            return False

        error_msg = (
            e.response.json().get("detail")
            if e.response and e.response.headers.get("Content-Type", "").startswith("application/json")
            else str(e)
        )
        st.error(f"API Error: {error_msg}")
        return False


# --------------------
# BACKEND ACTIONS
# --------------------

def trigger_portfolio_calculation() -> bool:
    return post_api_request(
        f"{API_BASE_URL}/portfolio/refresh",
        success_message="Portfolio refresh started in the background."
    )


def trigger_db_sync() -> bool:
    return post_api_request(
        f"{API_BASE_URL}/db/sync_db",
        success_message="Database synchronization started in the background."
    )


def delete_data() -> bool:
    return post_api_request(
        f"{API_BASE_URL}/debug/delete-data",
        success_message="All data deleted from the database."
    )


# --------------------
# HEALTH CHECKS
# --------------------

def is_backend_alive() -> bool:
    try:
        response = requests.get(API_BASE_URL, timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def check_db_health() -> tuple[bool, str | None]:
    try:
        response = requests.get(f"{API_BASE_URL}/debug/health/db", timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok":
                return True, None
        return False, f"Unexpected response: {response.status_code} - {response.text}"
    except Exception as e:
        return False, str(e)