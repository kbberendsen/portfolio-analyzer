import streamlit as st
import pandas as pd
import requests
import os
from typing import List, Optional, Dict, Any

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

@st.cache_data(ttl=60, show_spinner="Loading data...")
def get_portfolio_performance_daily(
    products: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    Fetches portfolio performance data from the backend API, with optional filters.
    Returns an empty DataFrame if the API call fails or returns no data.
    """
    params = {}
    if products:
        params["products"] = products
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date

    try:
        response = requests.get(
            f"{API_BASE_URL}/data/portfolio-daily", params=params, timeout=20
        )
        response.raise_for_status()
        data = response.json()
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        # Centralize date conversion to ensure consistency across the app
        if "start_date" in df.columns:
            df["start_date"] = pd.to_datetime(df["start_date"])
        if "end_date" in df.columns:
            df["end_date"] = pd.to_datetime(df["end_date"])
        return df
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to load portfolio data from API: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300, show_spinner="Loading filter options...")
def get_portfolio_metadata() -> Dict[str, Any]:
    """
    Fetches metadata for the portfolio, such as product lists and date ranges.
    This is used to populate filter widgets without loading the entire dataset.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/data/portfolio-metadata", timeout=10)
        response.raise_for_status()
        metadata = response.json()

        # Ensure date strings are converted to datetime objects
        if "min_date" in metadata and metadata["min_date"]:
            metadata["min_date"] = pd.to_datetime(metadata["min_date"])
        if "max_date" in metadata and metadata["max_date"]:
            metadata["max_date"] = pd.to_datetime(metadata["max_date"])

        return metadata
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to load portfolio metadata from API: {e}")
        return {"products": [], "min_date": None, "max_date": None}