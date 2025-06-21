import streamlit as st
import pandas as pd
import os
import json
import requests
import time

# Set the page title
st.set_page_config(page_title="Ticker Mapping", page_icon="📊", layout="wide")
st.title("Ticker Mapping")

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000") # Use environment variable for API URL

# Call transactions processing (API)
try:
    transactions_url = f"{API_BASE_URL}/transactions/all"
    response = requests.get(transactions_url)

except Exception as e:
    st.error("Could not connect to the transaction processing API.")
    st.exception(e)
    st.stop()

# Paths
mapping_path = os.path.join('output', 'isin_mapping.json')

# Load or initialize mapping
if 'df' not in st.session_state:
    if os.path.exists(mapping_path):
        with open(mapping_path, 'r') as f:
            mapping = json.load(f)

        # Flatten the nested dictionary into a DataFrame
        st.session_state.df = pd.DataFrame([
            {"ISIN": isin, "Ticker": data.get("ticker", ""), "Exchange": data.get("exchange", ""), "Product Name (DeGiro)": data.get("degiro_name", ""), "Display Name": data.get("display_name", "")}
            for isin, data in mapping.items()
        ])
    else:
        st.error("Mapping not found. Make sure to run the 'dashboard' page first to generate the mapping file.")
        st.stop()

# Filter out FULL
st.session_state.df = st.session_state.df[st.session_state.df["Ticker"] != "FULL"]

# Display editable DataFrame
edited_df = st.data_editor(
    st.session_state.df.sort_values(by=["Product Name (DeGiro)"], ascending=True),
    disabled=["ISIN", "Exchange", "Product Name (DeGiro)"],
    hide_index=True,
    num_rows="fixed",  # Optional: prevents adding new rows manually
    key="editable_table"
)

# Save logic
def save_mapping(df):
    # Fixed full portfolio entry
    full_portfolio_entry = {
        "ISIN": "FULL_PORTFOLIO",
        "Ticker": "FULL",
        "Exchange": "",
        "Product Name (DeGiro)": "Full portfolio",
        "Display Name": "Full portfolio"
    }
    df = df[df["ISIN"] != "FULL_PORTFOLIO"]
    df = pd.concat([df, pd.DataFrame([full_portfolio_entry])], ignore_index=True)

    # Save df to session state
    st.session_state.df = df

    updated_mapping = {
        row['ISIN']: {
            "ticker": row.get("Ticker", ""),
            "degiro_name": row.get("Product Name (DeGiro)", ""),
            "display_name": row.get("Display Name", ""),
            "exchange": row.get("Exchange", "")
        }
        for _, row in st.session_state.df.iterrows()
    }

    with open(mapping_path, 'w') as f:
        json.dump(updated_mapping, f, indent=4)

    st.success("Mapping saved successfully!")

# Yahoo Finance ticker search
def search_ticker(query, preferred_exchanges=None):
    url = f"https://query1.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=10&newsCount=0&listsCount=0"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://finance.yahoo.com"
    }

    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        quotes = data.get("quotes", [])
        if not quotes:
            return "", ""

        # Filter if preferred exchanges are given
        if preferred_exchanges:
            for exch in preferred_exchanges:
                for quote in quotes:
                    if quote.get("exchange") == exch and "symbol" in quote:
                        return quote["symbol"], quote.get("longname", "")

        # Fallback to first valid result
        for quote in quotes:
            if "symbol" in quote:
                return quote["symbol"], quote.get("longname", "")

    except Exception as e:
        print(f"Search error: {e}")
        return "", ""

    return "", ""

st.info("Simplify the 'Display Name' column above to improve auto-fill results. E.g. 'Gamestop' instead of 'GAMESTOP CORPORATION C'")
    
if st.button("Auto-fill empty tickers using display name"):
    st.session_state.df = edited_df
    new_df = st.session_state.df.copy()
    for i, row in new_df.iterrows():
        if not row["Ticker"]:
            display_name = row["Display Name"] if row["Display Name"] else row["Product Name (DeGiro)"]
            exch = row["Exchange"] if row["Exchange"] else None
            print(f"Searching for ticker for product: {display_name} on exchange: {exch}")
            guessed_ticker = search_ticker(display_name, exch)
            if guessed_ticker:
                new_df.at[i, "Ticker"] = guessed_ticker[0]
            time.sleep(1)
    st.session_state.df = new_df
    save_mapping(new_df)
    st.rerun()

# Save button
if st.button("Save mapping"):
    save_mapping(edited_df)

# Move the file uploader and refresh button to the sidebar
with st.sidebar:
    with st.expander("Upload/download mapping JSON file", expanded=False):

        # JSON mapping file uploader
        uploaded_mapping = st.file_uploader("Upload ISIN mapping JSON file", type=["json"])

        if uploaded_mapping:
            try:
                # Read and parse the uploaded JSON file
                new_mapping = json.load(uploaded_mapping)
                
                # Validate keys and structure (basic check)
                if not isinstance(new_mapping, dict):
                    st.error("Uploaded JSON is not a valid dictionary.")
                else:
                    # Update session state DataFrame from uploaded JSON
                    st.session_state.df = pd.DataFrame([
                        {
                            "ISIN": isin,
                            "Ticker": data.get("ticker", ""),
                            "Exchange": data.get("exchange", ""),
                            "Product Name (DeGiro)": data.get("degiro_name", ""),
                            "Display Name": data.get("display_name", "")
                        }
                        for isin, data in new_mapping.items()
                    ])

                    # Save uploaded mapping to file to overwrite existing one
                    with open(mapping_path, 'w') as f:
                        json.dump(new_mapping, f, indent=4)

                    st.success("Mapping file uploaded and loaded successfully!")
                    st.rerun()

            except Exception as e:
                st.error(f"Error loading uploaded JSON file: {e}")
        
        if os.path.exists(mapping_path):
            with open(mapping_path, 'rb') as f:
                json_bytes = f.read()

        # Download button for the current mapping
        st.download_button(
            label="Download current ISIN mapping as JSON",
            data=json_bytes,
            file_name="isin_mapping.json",
            mime="application/json"
        )

    # Reset tickers logic with confirmation
    with st.expander("⚠️ Reset all tickers and display names (this cannot be undone)", expanded=False):
        st.warning("This will clear all tickers from the table and reset altered display names. Are you sure?")
        if st.button("Reset", type="primary"):
            reset_df = st.session_state.df.copy()
            reset_df["Ticker"] = ""
            reset_df["Display Name"] = reset_df["Product Name (DeGiro)"]
            st.session_state.df = reset_df
            save_mapping(reset_df)
            st.success("All tickers and display names have been reset.")
            st.rerun()