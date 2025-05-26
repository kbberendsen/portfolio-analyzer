import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os

# Set the page title
st.set_page_config(page_title="Portfolio Analysis", page_icon="📊", layout="wide")

st.title("Portfolio Analysis")

# Load portfolio data
portfolio_file = os.path.join('output', 'portfolio_performance_daily.parquet')

# Dictionary to rename the performance metrics columns for display purposes
rename_dict = {
    'product': 'Product',
    'ticker': 'Ticker',
    'quantity': 'Quantity',
    'start_date': 'Start Date',
    'end_date': 'End Date',
    'avg_cost': 'Average Cost (€)',
    'total_cost': 'Total Cost (€)',
    'current_value': 'Current Value (€)',
    'current_money_weighted_return': 'Current Money Weighted Return (€)',
    'realized_return': 'Realized Return (€)',
    'net_return': 'Net Return (€)',
    'current_performance_percentage': 'Current Performance (%)',
    'net_performance_percentage': 'Net Performance (%)'
}

if os.path.exists(portfolio_file):
    # Load monthly and daily data
    df = pd.read_parquet(portfolio_file)
    
    # Rename columns
    df = df.rename(columns=rename_dict)

    df['End Date'] = df['End Date'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d'))

    # Remove 'Full Portfolio' entry
    df = df[df["Product"] != "Full portfolio"]

    with st.sidebar:
        # Set the default range to the last 90 days
        default_selected_date = df['End Date'].max()
        
        # Date selection
        selected_date = st.sidebar.date_input("Select End Date", default_selected_date, min_value=df["End Date"].min(), max_value=df["End Date"].max())
        selected_date = pd.to_datetime(selected_date)

        # Metric selection
        metric_options = ['Current Value (€)', 'Net Return (€)', 'Total Cost (€)']
        selected_metric = st.sidebar.selectbox("Select a Performance Metric", metric_options)

        # Add holdings type selector
        holdings_option = st.radio(
            "Select Holdings View",
            options=["Current Holdings", "All Holdings"],
            index=0,
            help="Current Holdings only include products with a non-zero current value"
        )

        # Keep going back one day if no data is found
        while selected_date >= df["End Date"].min():
            filtered_df = df[df['End Date'] == selected_date]

            if not filtered_df.empty:
                break  # Stop once at the first day with data

            selected_date -= pd.Timedelta(days=1)  # Go back one day
        
        # Filter based on holdings option
        if holdings_option == "Current Holdings":
            filtered_df = filtered_df[filtered_df["Quantity"] != 0]

        # Prepare stacked bar chart data
        stacked_df = filtered_df.copy()

        # Only select relevant columns for the stacked bar chart
        stacked_df = stacked_df[['Product', 'Quantity', 'Current Value (€)', 
                                 'Net Return (€)', 'Net Performance (%)', 'Total Cost (€)'
                        ]]

         # Percentage of total
        stacked_df["Current Allocation %"] = stacked_df['Current Value (€)'] / stacked_df['Current Value (€)'].sum() * 100

        # Sort products by allocation and then by total cost
        stacked_df = stacked_df.sort_values(
            by=['Current Allocation %', 'Total Cost (€)'],
            ascending=[False, False]
        )

        df_height_px = 50*len(stacked_df)+35

        # Custom styling function
        def color_net_performance(val):
            color = '#09ab3b' if val > 0 else '#ff2b2b' if val < 0 else 'gray'
            return f'color: {color}'

        # Apply Styler to the "Net Performance (%()" column
        stacked_df = stacked_df.style.map(color_net_performance, subset=["Net Performance (%)"])

    # Show dataframe
    st.dataframe(
        stacked_df,
        height=df_height_px,
        hide_index=True,
        row_height=50,
        column_config={
                "Current Allocation %": st.column_config.ProgressColumn(
                    "Current Allocation %",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                    width="small"
                ),
                "Current Value (€)": st.column_config.NumberColumn(
                    "Current Value (€)",
                    format="€ %.2f"
                ),
                "Net Return (€)": st.column_config.ProgressColumn(
                    "Net Return (€)",
                    format="€ %.2f",
                    min_value=0,
                    max_value=filtered_df['Net Return (€)'].sum(),
                    width="small"
                ),
                "Total Cost (€)": st.column_config.NumberColumn(
                    "Total Cost (€)",
                    format="€ %.2f"
                ),
                "Quantity": st.column_config.NumberColumn(
                    "Quantity",
                    format="%d"
                ),
                "Net Performance (%)": st.column_config.NumberColumn(
                    "Net Performance (%)",
                    format="%.2f%%"
                )
        }
    )

else:
    st.error("Portfolio data not found. Please refresh the dashboard to update the data.")