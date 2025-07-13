import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import os
import json
from backend.streamlit_utils.data_loader import get_portfolio_performance_daily

# Auth
if not st.user.is_logged_in:
    st.warning("You must log in to use this app.")
    if st.button("Log in"):
        st.login("auth0")
    st.stop()

# Set the page title
st.set_page_config(page_title="Portfolio Analysis - Split", page_icon="📊", layout="centered")

st.title("Portfolio Analysis - Split")

# Load portfolio data
mapping_path = os.path.join('output', 'isin_mapping.json')

# Dictionary to rename the performance metrics columns for display purposes
rename_dict = {
    'product': 'Product',
    'ticker': 'Ticker',
    'quantity': 'Quantity',
    'start_date': 'Start Date',
    'end_date': 'End Date',
    'avg_cost': 'Average Cost (€)',
    'total_cost': 'Total Cost (€)',
    'transaction_costs': 'Transaction Costs (€)',
    'current_value': 'Current Value (€)',
    'current_money_weighted_return': 'Current Money Weighted Return (€)',
    'realized_return': 'Realized Return (€)',
    'net_return': 'Net Return (€)',
    'current_performance_percentage': 'Current Performance (%)',
    'net_performance_percentage': 'Net Performance (%)'
}

# Load portfolio data
df = get_portfolio_performance_daily()
if not df.empty:
    # Rename columns
    df = df.rename(columns=rename_dict)

    df = df.sort_values(by='End Date', ascending=True)

    # Remove 'Full Portfolio' entry
    df = df[df["Product"] != "Full portfolio"]

    # Load or initialize mapping
    if os.path.exists(mapping_path):
        with open(mapping_path, 'r') as f:
            mapping = json.load(f)

        # Flatten the nested dictionary into a DataFrame
        mapping_df = pd.DataFrame([
            {"ISIN": isin, "Ticker": data.get("ticker", ""), "Exchange": data.get("exchange", ""), "Product Name (DeGiro)": data.get("degiro_name", ""), "Display Name": data.get("display_name", ""), "Product Type": data.get("product_type", "")}
            for isin, data in mapping.items()
            ])
    else:
        st.error("Mapping not found. Make sure to run the 'dashboard' page first to generate the mapping file.")
        st.stop()

    # Join product type form mapping_df to selected_day_df
    merged_df = df.merge(mapping_df[['Ticker', 'Product Type']], left_on='Ticker', right_on='Ticker', how='left')

    # DATE  FILTER    
    # Set the full date range as min and max values for the slider
    max_date = df['End Date'].max()
    min_date = df['End Date'].min()

    # Date selection
    date_selection = st.segmented_control(
        "Date Range",
        options=["1Y", "3M", "1M", "1W", "YTD", "Last year", "Last month", "All time"],
        default="1Y",
        selection_mode="single",
    )

    # Key date anchors
    first_day_this_year = max_date.replace(month=1, day=1)
    first_day_this_month = max_date.replace(day=1)

    # Days since start of this year/month
    days_since_year_start = (max_date - first_day_this_year).days
    days_since_month_start = (max_date - first_day_this_month).days

    # Previous month range
    last_day_prev_month = first_day_this_month - timedelta(days=1)
    first_day_prev_month = last_day_prev_month.replace(day=1)
    days_in_last_month = (last_day_prev_month - first_day_prev_month).days + 1

    # Previous year range
    first_day_prev_year = first_day_this_year.replace(year=max_date.year - 1)
    last_day_prev_year = first_day_prev_year.replace(month=12, day=31)
    days_in_last_year = (last_day_prev_year - first_day_prev_year).days + 1

    # Final mapping
    date_mapping = {
        "1Y": [365, 0],
        "3M": [90, 0],
        "1M": [30, 0],
        "1W": [7, 0],
        "1D": [1, 0],
        "YTD": [days_since_year_start, 0],
        "Last year": [days_in_last_year+days_since_year_start, days_since_year_start + 1],  # +1 to exclude Jan 1
        "Last month": [days_in_last_month+days_since_month_start, days_since_month_start + 1],  # +1 to exclude 1st of current month
        "All time": [(max_date - min_date).days, 0]
    }
    
    selected_start_date = max_date - timedelta(days=date_mapping[date_selection][0])
    selected_end_date = max_date - timedelta(days=date_mapping[date_selection][1])

    # Filter data by date range
    filtered_df = merged_df[(merged_df['End Date'] >= selected_start_date) & (merged_df['End Date'] <= selected_end_date)].sort_values(by='End Date')

    # METRIC FILTER
    # Performance metrics
    performance_metrics = ["Net Performance (%)", "Net Return (€)", "Total Cost (€)", "Current Value (€)"]
    default_index_per = performance_metrics.index("Current Value (€)")
    selected_metric = st.selectbox("Select a Performance Metric", options=performance_metrics, index=default_index_per, key="metric_select", width=250)
    
    # Group by Product Type and aggregate Net Return (€) and Total Cost (€)
    split_df = (
        filtered_df.groupby(["End Date", "Product Type"])[["Net Return (€)", "Total Cost (€)", "Current Value (€)"]]
        .sum()
        .reset_index()
        .sort_values(by=["End Date", "Product Type"], ascending=False)
    )

    # Add metrics after grouping
    split_df["Net Performance (%)"] = (split_df["Net Return (€)"] / split_df["Total Cost (€)"]) * 100 if split_df["Total Cost (€)"].any() else 0

    # Round all columns to 2 decimal places
    split_df = split_df.round({
        "Net Return (€)": 2,
        "Total Cost (€)": 2,
        "Current Value (€)": 2,
        "Net Performance (%)": 2
    })

    # Color mapping plots
    product_type_colors = {
        "ETF": "#1f77b4",
        "Stock": "orange",
        "Other": "purple"
    }

    st.subheader(f"{selected_metric} Over Time by Product Type")

    # Plot
    fig = px.line()  # Empty figure

    # Loop over each product type and add a line
    for product_type in split_df["Product Type"].unique():
        product_data = split_df[split_df["Product Type"] == product_type]

        fig.add_scatter(
            x=product_data["End Date"],
            y=product_data[selected_metric],
            mode="lines",
            name=product_type,
            line=dict(shape='spline', smoothing=0.7,
                      color=product_type_colors.get(product_type, "#888"))
        )

    # Add dashed line at y=0
    if (split_df[selected_metric] < 0).any():
        fig.add_shape(
            type="line",
            x0=split_df["End Date"].min(),
            x1=split_df["End Date"].max(),
            y0=0,
            y1=0,
            line=dict(
                color="black",
                width=1,
                dash="dash"
            ),
            xref="x",
            yref="y"
        )

    # Layout adjustments
    fig.update_layout(
        width=1200,
        height=400,
        margin=dict(l=0, r=0, t=50, b=50),
        showlegend=True,
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center", yanchor="bottom")
    )

    st.plotly_chart(fig, use_container_width=False)

    st.divider()
    
    st.subheader(f"{selected_metric} Split by Product Type")

    # Filter the latest day only
    latest_day_df = split_df[split_df["End Date"] == selected_end_date]

    # Check for negative values in the selected metric
    if (latest_day_df[selected_metric] < 0).any():
        # Use bar chart if any value is negative
        bar_fig = px.bar(
            latest_day_df,
            x="Product Type",
            y=selected_metric,
            color="Product Type",
            color_discrete_map=product_type_colors,
            text=selected_metric
        )
        bar_fig.update_layout(showlegend=False)
        bar_fig.update_layout(bargap=0.4, height=350, margin=dict(l=0, r=0, t=25, b=0))
        st.plotly_chart(bar_fig, use_container_width=True)

    else:
        # Use pie chart if all values are positive
        pie_fig = px.pie(
            latest_day_df,
            names="Product Type",
            values=selected_metric,
            hole=0.5,
            color="Product Type",
            color_discrete_map=product_type_colors
        )
        pie_fig.update_traces(textposition='inside', textinfo='percent+label')
        pie_fig.update_layout(showlegend=False)
        pie_fig.update_layout(height=350, margin=dict(l=0, r=0, t=25, b=0))
        st.plotly_chart(pie_fig, use_container_width=True)

    
else:
    st.error("Portfolio data not found. Please run the 'dashboard' page first to generate the portfolio performance data.")
    st.stop()