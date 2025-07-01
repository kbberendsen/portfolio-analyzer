import requests
import streamlit as st

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