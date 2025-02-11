import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os

# Set the page title
st.set_page_config(page_title="Portfolio Analysis", page_icon="📊")

st.title("Portfolio Analysis")

# Load portfolio data
portfolio_file = os.path.join('output', 'portfolio_daily.csv')

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
    df = pd.read_csv(portfolio_file)
    
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

        # Keep going back one day if no data is found
        while selected_date >= df["End Date"].min():
            filtered_df = df[df['End Date'] == selected_date]

            if not filtered_df.empty:
                break  # Stop once we find a day with data

            selected_date -= pd.Timedelta(days=1)  # Go back one day

        # Aggregate portfolio split
        portfolio_split = filtered_df.groupby(["Product", "End Date"])[selected_metric].sum().reset_index()
        portfolio_split = portfolio_split[portfolio_split[selected_metric] != 0].sort_values(by=selected_metric)

        # Calculate percentage of total
        total_value = portfolio_split[selected_metric].sum()
        portfolio_split["% of Total"] = (portfolio_split[selected_metric] / total_value) * 100
        portfolio_split["% of Total"] = portfolio_split["% of Total"].round(1)

    # Bar chart for portfolio split
    fig = px.bar(
        portfolio_split,
        x=selected_metric,
        y="Product",
        orientation="h",
        title=f"Portfolio Allocation ({selected_metric})",
        text=portfolio_split.apply(lambda row: f"€ {row[selected_metric]:.0f} ({row['% of Total']}%)", axis=1),  # Add % label
    )

    fig.update_layout(
        title_font_size=24,
        xaxis_title_font_size=16,
        font=dict(
            family="Inter, sans-serif",
            size=14,
        ),
        yaxis=dict(
            title="",
            tickfont=dict(size=14),
            showgrid=False,
        ),
        xaxis=dict(
            tickfont=dict(size=14),
            showgrid=True,
            zeroline=False,
        ),
        bargap=0.3,  # Reduce bar thickness
        margin=dict(l=0, r=0, t=100, b=50),
        height=max(500, len(portfolio_split) * 50),  # Responsive height
    )

    st.plotly_chart(fig, use_container_width=True)

    # Show raw data
    with st.expander("View Portfolio Data"):
        st.dataframe(portfolio_split)

else:
    st.error("Portfolio data not found. Please refresh the dashboard to update the data.")
