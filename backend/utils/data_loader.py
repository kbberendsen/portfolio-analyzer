import streamlit as st
import pandas as pd
import requests
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

@st.cache_data(ttl=60, show_spinner="Loading data...") # Cache for 60 seconds to avoid re-fetching on every script rerun
def load_portfolio_performance_from_api() -> pd.DataFrame:
    """
    Fetches portfolio performance data from the backend API.
    Returns an empty DataFrame if the API call fails or returns no data.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/data/portfolio-daily", timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        # Centralize date conversion to ensure consistency across the app
        if 'start_date' in df.columns:
            df['start_date'] = pd.to_datetime(df['start_date'])
        if 'end_date' in df.columns:
            df['end_date'] = pd.to_datetime(df['end_date'])
        return df
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to load portfolio data from API: {e}")
        return pd.DataFrame()