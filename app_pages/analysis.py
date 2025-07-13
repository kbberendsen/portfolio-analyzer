import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os
from backend.streamlit_utils.data_loader import get_portfolio_performance_daily

# Auth
if not st.user.is_logged_in:
    st.warning("You must log in to use this app.")
    if st.button("Log in"):
        st.login("auth0")
    st.stop()

# Set the page title
st.set_page_config(page_title="Portfolio Analysis", page_icon="📊", layout="wide")

st.title("Portfolio Analysis")

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

# Load portfolio data
df = get_portfolio_performance_daily()
if not df.empty:
    # Rename columns
    df = df.rename(columns=rename_dict)

    df = df.sort_values(by='End Date', ascending=True)

    # Remove 'Full Portfolio' entry
    df = df[df["Product"] != "Full portfolio"]

    # Set the default date to most recent end date
    default_selected_date = df['End Date'].max()
    
    # Date selection
    selected_date_input = st.date_input("Select End Date", default_selected_date, min_value=df["End Date"].min(), max_value=df["End Date"].max(), width=250)
    selected_date = pd.to_datetime(selected_date_input)
    
    holdings_option = st.segmented_control(
        "Holdings to include",
        options=["Current Holdings", "All Holdings"],
        default="Current Holdings",
        selection_mode="single",
        help="Current Holdings only include products with a non-zero current value"
    )

    filtered_df = df[df['End Date'] <= selected_date]
    if filtered_df.empty:
        st.error("No data found for the selected date. Please select a different date.")
        st.stop()
    
    # Get recent two distinct dates
    filtered_dates = filtered_df['End Date'].unique()[-2:]
    filtered_dates = sorted(filtered_dates)
    date_0 = filtered_dates[0]
    date_1 = filtered_dates[1] if len(filtered_dates) > 1 else date_0

    # Top net return
    top_net_return_start = filtered_df[filtered_df['End Date'] == date_0].get('Net Return (€)', 0).sum()
    top_net_return_end = filtered_df[filtered_df['End Date'] == date_1].get('Net Return (€)', 0).sum()

    if top_net_return_start != 0:
        top_net_return_delta = round((top_net_return_end-top_net_return_start), 2)
        top_net_return_delta_eur = f"+€ {abs(top_net_return_delta)}" if top_net_return_delta > 0 else f"-€ {abs(top_net_return_delta)}"
        top_net_return_delta_per = round(((top_net_return_end-top_net_return_start)/abs(top_net_return_start))*100, 2)
    else:
        top_net_return_delta_eur = 0
        top_net_return_delta_per = 0

    # Top current value
    top_current_value_start = filtered_df[filtered_df['End Date'] == date_0].get('Current Value (€)', 0).sum()
    top_current_value_end = filtered_df[filtered_df['End Date'] == date_1].get('Current Value (€)', 0).sum()

    if top_current_value_start != 0:
        top_current_value_delta = round((top_current_value_end-top_current_value_start), 2)
        top_current_value_delta_eur = f"+€ {abs(top_current_value_delta)}" if top_current_value_delta > 0 else f"-€ {abs(top_current_value_delta)}"
        top_current_value_delta_per = round(((top_current_value_end-top_current_value_start)/(top_current_value_start))*100, 2)
    else:
        top_current_value_delta_eur = 0
        top_current_value_delta_per = 0

    # Today profit/loss
    today_pl = top_net_return_delta
    today_pl_per = top_net_return_delta_per

    # Filter the DataFrame for the recent selected date
    selected_day_df = df[df['End Date'] == date_1]

    # Total profit/loss
    total_pl = selected_day_df['Net Return (€)'].sum()
    total_pl_per = selected_day_df['Net Return (€)'].sum() / selected_day_df['Total Cost (€)'].sum() * 100 if selected_day_df['Total Cost (€)'].sum() != 0 else 0
    
    # Filter based on holdings option
    if holdings_option == "Current Holdings":
        selected_day_df = selected_day_df[selected_day_df["Quantity"] != 0]

    # Prepare display df
    display_df = selected_day_df.copy()

    # Only select relevant columns
    display_df = display_df[['Product', 'Quantity', 'Current Value (€)', 
                                'Net Return (€)', 'Net Performance (%)', 'Total Cost (€)'
                    ]]

    # Create new column with 30-day Net Performance (%) trend as list
    date_L30 = date_1 - timedelta(days=30)
    display_df["Net Performance (%) - Trend"] = display_df.apply(
        lambda row: df[
            (df["Product"] == row["Product"]) &
            (df["End Date"] >= date_L30) &
            (df["End Date"] <= date_1)
        ]["Net Performance (%)"].tolist(),
        axis=1
    )

    # Allocation
    display_df["Current Allocation %"] = display_df['Current Value (€)'] / display_df['Current Value (€)'].sum() * 100

    # Sort products by allocation and then by total cost
    display_df = display_df.sort_values(
        by=['Current Allocation %', 'Total Cost (€)'],
        ascending=[False, False]
    )

    df_height_px = 50*len(display_df)+37

    # Custom styling function
    def color_net_performance(val):
        color = '#09ab3b' if val > 0 else '#ff2b2b' if val < 0 else 'gray'
        return f'color: {color}'
    
    # Final column order
    display_df = display_df[['Product', 'Current Allocation %' ,'Quantity', 'Current Value (€)', 
                                'Net Return (€)', 'Net Performance (%)', 'Net Performance (%) - Trend', 'Total Cost (€)'
                    ]]
    
    def remove_flat_line(arr):
        if len(arr) == 0:
            return None
        if min(arr) == max(arr):
            return None
        return arr

    display_df["Net Performance (%) - Trend"] = display_df["Net Performance (%) - Trend"].apply(remove_flat_line)

    # Apply Styler to the "Net Performance" columns
    display_df_styled = display_df.style.map(color_net_performance, subset=["Net Performance (%)", "Net Return (€)"])

    # Top badges
    badge_value_color = 'green' if top_current_value_delta > 0 else 'red' if top_current_value_delta < 0 else 'gray'
    badge_value_icon = ':material/arrow_upward:' if top_current_value_delta > 0 else ':material/arrow_downward:' if top_current_value_delta < 0 else ':material/info:'
    badge_value_text = f"Portfolio: € {abs(top_current_value_end):,.2f} (∆ +{top_current_value_delta_per}% | {top_current_value_delta_eur}) "if top_current_value_delta > 0 \
                    else f"Portfolio: € {abs(top_current_value_end):,.2f} (∆ {top_current_value_delta_per}% | {top_current_value_delta_eur}) " if top_current_value_delta < 0 \
                    else "Portfolio Empty"

    badge_total_pl_color = 'green' if total_pl > 0 else 'red' if total_pl < 0 else 'gray'
    badge_total_pl_icon = ':material/arrow_upward:' if total_pl > 0 else ':material/arrow_downward:' if total_pl < 0 else ':material/info:'
    badge_total_pl_text = f"All-time Profit: {total_pl_per:.2f}% (€ {abs(total_pl):,.2f})" if total_pl > 0 \
                    else f"All-time Loss: {total_pl_per:.2f}% (-€ {abs(total_pl):,.2f})" if total_pl < 0 \
                    else "No Profit/Loss"
    
    st.markdown(f":{badge_value_color}-badge[{badge_value_icon} {badge_value_text}] :{badge_total_pl_color}-badge[{badge_total_pl_icon} {badge_total_pl_text}]")

    # Show dataframe
    st.dataframe(
        display_df_styled,
        height=df_height_px,
        hide_index=True,
        row_height=50,
        column_config={
                "Product": st.column_config.TextColumn(
                    "Product",
                    width="medium",
                    pinned=True,
                ),

                "Current Allocation %": st.column_config.ProgressColumn(
                    "Allocation (%)",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                    width="small",
                    help="Current allocation percentage of the product in the portfolio (product current value / total current value)."
                ),
                "Current Value (€)": st.column_config.NumberColumn(
                    "Current Value (€)",
                    format="€ %.2f",
                    width="small",
                ),
                "Net Return (€)": st.column_config.NumberColumn(
                    "Profit/Loss (€)",
                    format="€ %.2f",
                    width="small",
                ),
                "Total Cost (€)": st.column_config.NumberColumn(
                    "Total Cost (€)",
                    format="€ %.2f",
                    width="small"
                ),
                "Quantity": st.column_config.NumberColumn(
                    "Quantity",
                    format="%d",
                    width="small"
                ),
                "Net Performance (%)": st.column_config.NumberColumn(
                    "Profit/Loss (%)",
                    format="%.2f%%",
                    width="small"
                ),
                "Net Performance (%) - Trend": st.column_config.AreaChartColumn(
                    "30-day P/L (%)",
                    width="small"
                )
        }
    )

else:
    st.error("Portfolio data not found. Please refresh the dashboard to update the data.")