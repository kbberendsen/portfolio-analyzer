import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import os
import json
from backend.streamlit_utils.data_loader import get_portfolio_performance_daily
from backend.streamlit_utils.constants import PERFORMANCE_METRIC_RENAME, METRIC_HELP_TEXTS

# Set the page title
st.set_page_config(page_title="Portfolio Analysis - Split", page_icon="📊", layout="centered")

st.title("Portfolio Analysis - Split")

# Load portfolio data
mapping_path = os.path.join('output', 'isin_mapping.json')

# Load portfolio data
df = get_portfolio_performance_daily()
if not df.empty:
    # Rename columns
    df = df.rename(columns=PERFORMANCE_METRIC_RENAME)

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
    non_metric_cols = ['Product', 'Ticker', 'Start Date', 'End Date']
    performance_metrics = sorted([v for k, v in PERFORMANCE_METRIC_RENAME.items() if v not in non_metric_cols])
    default_index_per = performance_metrics.index("Net Performance (%)") if "Net Performance (%)" in performance_metrics else 0
    selected_metric = st.selectbox("Select a Performance Metric", options=performance_metrics, index=default_index_per, key="metric_select")
    
    # Group by Product Type and aggregate € metrics
    euro_cols = [col for col in filtered_df.columns if "€" in col]
    split_df = (
        filtered_df
            .groupby(["End Date", "Product Type"])[euro_cols]
            .sum()
            .reset_index()
            .sort_values(by=["End Date", "Product Type"], ascending=False)
    )

    # Add metrics after grouping
    split_df["Net Performance (%)"] = (split_df["Net Return (€)"] / split_df["Total Cost (€)"]) * 100 if split_df["Total Cost (€)"].any() else 0
    split_df["Current Performance (%)"] = (split_df["Current Return (€)"] / split_df["Cost Basis (€)"]) * 100 if split_df["Cost Basis (€)"].any() else 0

    # Round columns to 2 decimal places
    round_cols = [col for col in split_df.columns if "€" in col or "%" in col]
    split_df[round_cols] = split_df[round_cols].round(2)

    # Color mapping plots
    product_type_colors = {
        "ETF": "#1f77b4",
        "Stock": "orange",
        "Other": "purple"
    }

    st.subheader(f"{selected_metric} Over Time by Product Type")

    # Checkboxes for markers and cost basis
    if "show_markers" not in st.session_state:
        st.session_state.show_markers = False
    if "show_cost_basis" not in st.session_state:
        st.session_state.show_cost_basis = False

    # Create two columns
    col1, col2, col3 = st.columns(3)

    # Checkbox for Buy/Sell markers
    with col1:
        st.checkbox(
            "Show Buy/Sell Markers",
            value=st.session_state.show_markers,
            key="show_markers",
            help="Show markers to indicate when buying (green) and selling (red) transactions occurred."
        )

    # Checkbox for Cost Basis (only if metric is Current Value (€))
    with col2:
        if selected_metric == "Current Value (€)":
            st.checkbox(
                "Show Cost Basis (€)",
                value=st.session_state.show_cost_basis,
                key="show_cost_basis",
                help=METRIC_HELP_TEXTS.get('Cost Basis (€)')
            )

    # Plot
    fig = px.line()  # Empty figure

    # Flags for legend entries
    cost_basis_needed = selected_metric == "Current Value (€)" and st.session_state.show_cost_basis
    has_buys = False
    has_sells = False

    # Loop over each product type and add a line
    for product_type in split_df["Product Type"].unique():
        product_data = split_df[split_df["Product Type"] == product_type].sort_values(by="End Date")

        fig.add_scatter(
            x=product_data["End Date"],
            y=product_data[selected_metric],
            mode="lines",
            name=product_type,
            line=dict(shape='spline', smoothing=0.7,
                      color=product_type_colors.get(product_type, "#888"))
        )

        # Add Cost Basis line if checkbox is checked (only for Current Value (€))
        if cost_basis_needed:
            fig.add_scatter(
                x=product_data["End Date"],
                y=product_data["Cost Basis (€)"],
                mode="lines",
                name="Cost Basis (€)",
                showlegend=False,
                line=dict(color="grey", shape="spline", smoothing=0.7, dash="dot")
            )

        # Add Buy/Sell markers (hidden from legend)
        if st.session_state.show_markers:
            product_data["cost_basis_delta"] = product_data["Cost Basis (€)"].diff()
            buys = product_data[product_data["cost_basis_delta"] > 0]
            sells = product_data[product_data["cost_basis_delta"] < 0]

            marker_offset = 0.03 * (product_data[selected_metric].max() - product_data[selected_metric].min())
            if not buys.empty:
                has_buys = True
                fig.add_scatter(
                    x=buys["End Date"],
                    y=buys[selected_metric] + marker_offset,
                    mode="markers",
                    name="Buy",
                    showlegend=False,
                    marker=dict(color="#09ab3b", size=11, symbol="triangle-up", line=dict(color="black", width=0.7)),
                    hovertemplate=(
                        "<b>Buy</b><br>"
                        "Product: " + product_type + "<br>"
                        "Date: %{x}<br>"
                        + selected_metric + ": %{y:.2f}<br>"
                        "Δ Cost Basis: €%{customdata:.2f}<extra></extra>"
                    ),
                    customdata=buys["cost_basis_delta"]
                )

            if not sells.empty:
                has_sells = True
                fig.add_scatter(
                    x=sells["End Date"],
                    y=sells[selected_metric] + marker_offset,
                    mode="markers",
                    name="Sell",
                    showlegend=False,
                    marker=dict(color="#ff2b2b", size=11, symbol="triangle-down", line=dict(color="black", width=0.7)),
                    hovertemplate=(
                        "<b>Sell</b><br>"
                        "Product: " + product_type + "<br>"
                        "Date: %{x}<br>"
                        + selected_metric + ": %{y:.2f}<br>"
                        "Δ Cost Basis: €%{customdata:.2f}<extra></extra>"
                    ),
                    customdata=sells["cost_basis_delta"]
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

    # Add dummy traces for legend at the end
    if cost_basis_needed:
        fig.add_scatter(
            x=[None],
            y=[None],
            mode="lines",
            name="Cost Basis (€)",
            line=dict(color="grey", shape="spline", smoothing=0.7, dash="dot")
        )

    if has_buys:
        fig.add_scatter(
            x=[None],
            y=[None],
            mode="markers",
            name="Buy",
            marker=dict(color="#09ab3b", size=11, symbol="triangle-up", line=dict(color="black", width=0.7))
        )

    if has_sells:
        fig.add_scatter(
            x=[None],
            y=[None],
            mode="markers",
            name="Sell",
            marker=dict(color="#ff2b2b", size=11, symbol="triangle-down", line=dict(color="black", width=0.7))
        )

    # Layout adjustments
    fig.update_layout(
        width=1200,
        height=400,
        margin=dict(l=0, r=0, t=50, b=50),
        showlegend=True,
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center", yanchor="bottom")
    )

    st.plotly_chart(fig, width='content')

    # Chart only if more than 1 product type
    if len(split_df["Product Type"].unique()) > 1:
        st.divider()
        st.subheader(f"{selected_metric} Split by Product Type")

        # Filter the latest day only
        latest_day_df = split_df[split_df["End Date"] == selected_end_date]

        # Decide chart type
        if "%" in selected_metric:
            # BAR CHART (for percentage metrics)
            fig = px.bar(
                latest_day_df,
                x="Product Type",
                y=selected_metric,
                color="Product Type",
                color_discrete_map=product_type_colors,
                text=selected_metric
            )
            fig.update_layout(
                showlegend=False,
                bargap=0.4,
                height=350,
                margin=dict(l=0, r=0, t=25, b=0)
            )

        else:
            # DONUT CHART (absolute metrics with % + €)
            fig = px.pie(
                latest_day_df,
                names="Product Type",
                values=selected_metric,
                color="Product Type",
                color_discrete_map=product_type_colors,
                hole=0.5
            )

            fig.update_traces(
                textinfo="percent+value",
                texttemplate="%{percent}<br>€ %{value:,.0f}",
                hovertemplate=(
                    "<b>%{label}</b><br>"
                    "€ %{value:,.0f}<br>"
                    "%{percent}<extra></extra>"
                )
            )

            fig.update_layout(
                height=350,
                margin=dict(l=0, r=0, t=25, b=0),
                showlegend=True
            )

        st.plotly_chart(fig, use_container_width=True)

    
else:
    st.error("Portfolio data not found. Please run the 'dashboard' page first to generate the portfolio performance data.")
    st.stop()