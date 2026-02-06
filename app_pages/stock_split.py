import streamlit as st
import pandas as pd
import os
import yfinance as yf
from backend.streamlit_utils.api import post_api_request
from backend.streamlit_utils.data_loader import get_portfolio_performance_daily
from backend.streamlit_utils.constants import (
    API_BASE_URL,
    ENV_API_BASE_URL_KEY,
    PERFORMANCE_METRIC_RENAME
)

# Config
st.set_page_config(page_title="Stock Split Calculator", page_icon=":bar_chart:", layout="centered")
API_BASE_URL = os.getenv(ENV_API_BASE_URL_KEY, API_BASE_URL)

# Backend triggers
def trigger_portfolio_calculation():
    return post_api_request(
        f"{API_BASE_URL}/portfolio/refresh",
        success_message="Portfolio refresh started in the background."
    )

st.title('Stock Split Calculator')
st.subheader('To Invest and Split')

# Set initial state variables
if 'split_df' not in st.session_state:
    st.session_state.split_df = pd.DataFrame()
if 'result_df' not in st.session_state:
    st.session_state.result_df = pd.DataFrame()
if 'investment_needed' not in st.session_state:
    st.session_state.investment_needed = 0

def refresh_data():
    try:
        # Check if initial db load is needed
        trigger_portfolio_calculation()
    except Exception as e:
        st.error(f"Error occurred while refreshing data: {e}")

@st.cache_data
def get_current_stock_price(ticker_symbol):
    # Create a Ticker object
    ticker = yf.Ticker(ticker_symbol)
    
    # Retrieve the current stock price
    stock_info = ticker.history(period="1d")
    
    # Extract the last closing price or current price
    if not stock_info.empty:
        current_price = stock_info['Close'].iloc[-1]
        return current_price
    else:
        return None

# Load portfolio data
df = get_portfolio_performance_daily()
if not df.empty:
    # Load daily data
    daily_df = df
    daily_df = daily_df.rename(columns=PERFORMANCE_METRIC_RENAME)

    # Get the most recent data
    daily_df_recent_date = sorted(daily_df['End Date'].unique())[-1]

    # Filter dataframe
    daily_df_filtered = daily_df[daily_df['End Date'] == daily_df_recent_date]
    daily_df_filtered = daily_df_filtered[daily_df_filtered['Quantity'] > 0]
    daily_df_filtered = daily_df_filtered[daily_df_filtered['Product'] != 'Full portfolio']

    # Input for the amount to invest
    to_invest = st.number_input('Amount to invest', value=350, step=10)

    # Select products
    current_products = sorted(daily_df_filtered['Product'].unique())
    included_products = st.multiselect(
        "Which stocks should be included in the split calculation?",
        current_products
    )

    # Prepare the split DataFrame for user input and filter by selected products
    filtered_split_df = daily_df_filtered[daily_df_filtered['Product'].isin(included_products)].copy()

    # Replace Current Value from CSV and recalculate using most up-to-date stock prices
    #filtered_split_df['Current Price (€)'] = filtered_split_df['Ticker'].apply(get_current_stock_price)
    filtered_split_df['Current Price (€)'] = filtered_split_df['Current Value (€)'] / filtered_split_df['Quantity']
    filtered_split_df['Current Value (€)'] = filtered_split_df['Current Price (€)'] * filtered_split_df['Quantity']

    filtered_split_df['Current Split (%)'] = round((filtered_split_df['Current Value (€)'] / sum(filtered_split_df['Current Value (€)'])) * 100, 2)
    filtered_split_df['Wanted Split (%)'] = filtered_split_df['Current Split (%)']

    # Save filtered split data in session state
    st.session_state.split_df = filtered_split_df[['Product', 'Ticker', 'Wanted Split (%)', 'Quantity', 'Current Price (€)', 'Current Value (€)', 'Current Split (%)']]

    # Display editable split DataFrame where users can adjust "Wanted Split (%)"
    edited_split_df = st.data_editor(
        st.session_state.split_df,
        column_config={
            "Wanted Split (%)": st.column_config.NumberColumn(
                "Wanted Split (%)",
                min_value=0,
                max_value=100,
                step=1
            )
        },
        disabled=["Product", "Ticker", "Quantity", "Current Price (€)", "Current Value (€)", "Current Split (%)"],
        hide_index=True,
    )

    # Function to calculate the new values in result_df based on Wanted Split
    def calculate_new_values():
        # Save any changes made in the editor back to session state
        if edited_split_df is not None:
            st.session_state.split_df = edited_split_df

        # Calculate the new total value (current value + amount to invest)
        current_total_value = sum(filtered_split_df['Current Value (€)'])
        new_total = to_invest + current_total_value

        # Calculate columns for amount to buy
        split_df = st.session_state.split_df.copy()
        split_df['New Value (€)'] = round((split_df['Wanted Split (%)'] / 100) * new_total, 2)
        split_df['Diff'] = split_df['New Value (€)'] - split_df['Current Value (€)']
        split_df['Amount to Buy'] = round(split_df['Diff'] / split_df['Current Price (€)'], 0)
        split_df['Cost to Buy (€)'] = round(split_df['Amount to Buy'] * split_df['Current Price (€)'], 2)
        split_df['Actual Split (%)'] = round(((split_df['Current Value (€)'] + split_df['Cost to Buy (€)']) / (sum(split_df['Current Value (€)']) + sum(split_df['Cost to Buy (€)']))*100), 2)
        
        # Store result in session state for display
        st.session_state.result_df = split_df[['Product', 'Ticker', 'Amount to Buy', 'Current Price (€)', 'Cost to Buy (€)', 'Actual Split (%)']]
        st.session_state.investment_needed = round(sum(split_df['Cost to Buy (€)']), 2)

    # Add a "Calculate" button to compute new columns
    if st.button("Calculate"):
        calculate_new_values()

    # Display the result_df after calculation
    if not st.session_state.result_df.empty:
        st.divider()
        st.subheader('Amount to Buy')
        st.dataframe(st.session_state.result_df.reset_index(drop=True))
        st.metric(label='Investment needed', value=f'€ {st.session_state.investment_needed}')

    rerun = 0

    st.divider()

    # Refresh Button to update the CSV
    if st.button('Refresh Data'):
        refresh_data()
        calculate_new_values()

    # Refresh stock prices by clearing cache, then rerunning
    if st.button("Refresh Stock Prices"):
        # Clear cached stock price data
        get_current_stock_price.clear()  

        # Remove result_df by making it an empty dataframe
        data = []
        st.session_state.result_df = pd.DataFrame(data)
        
        # Rerun page
        st.rerun()
else:
    if st.button('Refresh Data'):
        refresh_data()
    st.error("Portfolio data not found. Please refresh the dashboard to update the data.")
