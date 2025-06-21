import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import os
import json

# Set the page title
st.set_page_config(page_title="Portfolio Analysis - Split", page_icon="📊", layout="centered")

st.title("Portfolio Analysis - Split")

# Load portfolio data
portfolio_file = os.path.join('output', 'portfolio_performance_daily.parquet')
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

if os.path.exists(portfolio_file):
    # Load monthly and daily data
    df = pd.read_parquet(portfolio_file)
    
    # Rename columns
    df = df.rename(columns=rename_dict)

    df['End Date'] = df['End Date'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d'))
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

    with st.sidebar:

        # Set the full date range as min and max values for the slider
        max_date = merged_df['End Date'].max().to_pydatetime()
        min_date = merged_df['End Date'].min().to_pydatetime()#max_date - timedelta(days=365)

        # Set the default range to the last 90 days
        default_start_date = max_date - timedelta(days=365)
        
        # Create the slider with the full date range but defaulting to the last 90 days
        selected_start_date, selected_end_date = st.slider(
            "Select Date Range",
            min_value=min_date,
            max_value=max_date,
            value=(default_start_date, max_date),
            format="YYYY-MM-DD"
        )

        # Performance metrics
        performance_metrics = ["Net Return (€)", "Total Cost (€)", "Current Value (€)"]
        default_index_per = performance_metrics.index("Current Value (€)")
        selected_metric = st.selectbox("Select a Performance Metric", options=performance_metrics, index=default_index_per, key="metric_select")

    # Filter data by date range
    filtered_df = merged_df[(merged_df['End Date'] >= selected_start_date) & (merged_df['End Date'] <= selected_end_date)].sort_values(by='End Date')

    # Group by Product Type and aggregate Net Return (€) and Total Cost (€)
    split_df = (
        filtered_df.groupby(["End Date", "Product Type"])[["Net Return (€)", "Total Cost (€)", "Current Value (€)"]]
        .sum()
        .reset_index()
        .sort_values(by="End Date", ascending=False)
    )

    # Color mapping plots
    product_type_colors = {
        "ETF": "#1f77b4",
        "Stock": "orange",
        "Other": "purple"
    }
    
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
            color_discrete_map=product_type_colors
        )
        bar_fig.update_layout(showlegend=False)
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
        st.plotly_chart(pie_fig, use_container_width=True)

    st.divider()

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

    # Layout adjustments
    fig.update_layout(
        width=1200,
        height=500,
        margin=dict(l=0, r=0, t=50, b=50),
        showlegend=True,
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center", yanchor="bottom")
    )

    st.plotly_chart(fig, use_container_width=False)
else:
    st.error("Portfolio data not found. Please run the 'dashboard' page first to generate the portfolio performance data.")
    st.stop()