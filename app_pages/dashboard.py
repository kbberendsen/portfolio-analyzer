import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import os
import requests
import time
from backend.streamlit_utils.logs import get_log_files, read_last_n_lines_reversed
from backend.streamlit_utils.data_loader import get_portfolio_performance_daily, get_portfolio_metadata
from backend.streamlit_utils.api import (
    trigger_portfolio_calculation,
    trigger_db_sync,
    delete_data,
    is_backend_alive,
    check_db_health,
)
from backend.streamlit_utils.constants import (
    API_BASE_URL,
    ENV_API_BASE_URL_KEY,
    UPLOADS_DIR,
    TRANSACTIONS_CSV,
    PERFORMANCE_METRIC_RENAME,
    DATE_RANGE_OPTIONS
)

# Auth
if not st.user.is_logged_in:
    st.warning("You must log in to use this app.")
    if st.button("Log in"):
        st.login("auth0")
    st.stop()

# Config
st.set_page_config(page_title="Stock Portfolio Dashboard", page_icon=":bar_chart:", layout="centered")
API_BASE_URL = os.getenv(ENV_API_BASE_URL_KEY, API_BASE_URL)

# --------------------
# APP
# --------------------

with st.sidebar:
    if st.button("Log out", type="primary"):
        st.logout()
        st.stop()

    # Show welcome message only if logged in
    if st.user.is_logged_in and hasattr(st.user, "name"):
        st.markdown(f"Welcome {st.user.name}!")
        #st.markdown(f"Welcome {st.user.sub}!")

with st.sidebar.expander("View Logs", expanded=False):
    log_files = get_log_files()
    if not log_files:
        st.info("No log files found.")
    else:
        selected_log = st.selectbox("Select log file", options=[""] + log_files, format_func=lambda x: x or "— Select a file —")
        if selected_log:
            content = read_last_n_lines_reversed(selected_log, 100)
            st.text_area(f"Contents of {selected_log} (most recent first)", content, height=300)

# Check if backend is alive
if not is_backend_alive():
    st.error("Backend API is not reachable. Please ensure the backend is running.")
    st.stop()  # Stop execution if backend is not reachable

is_db_healthy, db_error = check_db_health()
if not is_db_healthy:
    st.error("⚠️ Cannot connect to the database. Please check backend and DB status.")
    if db_error:
        st.code(db_error, language="text")
    st.stop()

st.title("Stock Portfolio Dashboard")


# --------------------
# Transactions File Upload
# --------------------

# Create uploads directory if it doesn't exist
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Check if the uploads folder contains any CSV files
csv_files = [f for f in os.listdir(UPLOADS_DIR) if f.endswith(".csv")]

# File path for transactions CSV
file_path = os.path.join(UPLOADS_DIR, TRANSACTIONS_CSV)

# Check for transaction file in the uploads folder
if not csv_files:
    st.warning("No DeGiro transaction data found. Please upload a CSV file to proceed. Check GitHub project documention for instructions.")
    st.markdown(
        "📖 [Check the GitHub project documentation for instructions](https://github.com/kbberendsen/portfolio-analyzer)"
    )

    uploaded_file = st.file_uploader("Upload your DeGiro transactions CSV file", type=["csv"])
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        df.to_csv(file_path, index=False)
        st.success("File uploaded successfully! Please reload the page.")
    st.stop()

# Placeholder for the loading spinner while refreshing data on startup
loading_placeholder = st.empty()

# Define startup refresh state variable
if "startup_refresh" not in st.session_state:
    st.session_state.startup_refresh = False  # Indicates refresh hasn't run yet

def check_columns(uploaded_df):    
    try:
        st.write(uploaded_df.head())  # Display the first few rows of the uploaded file

        if uploaded_df.empty:
            st.error("Uploaded file is empty.")
            return False
        
    except Exception as e:
        st.error(f"Error reading the uploaded file: {e}")
        return False

def refresh_data(uploaded_file=None):
    # Check for new transactions file
    if uploaded_file is not None:
        uploaded_df = pd.read_csv(uploaded_file)

        # Read the uploaded file into a DataFrame
        new_data = uploaded_df

        if new_data.empty:
            st.error("The uploaded file is empty after reading.")
            return

        # Save the new data to file
        file_path = os.path.join('uploads', 'Transactions.csv')
        new_data.to_csv(file_path, index=False)
        st.success(f"Data saved to {file_path}")
    
    # Trigger the backend API to refresh data
    try:
        trigger_portfolio_calculation()
    except Exception as e:
        st.error(f"Error occurred while refreshing data: {e}")

# # Startup refresh logic
if not st.session_state.startup_refresh:
    try:
        # Load metadata to check if it's the first run
        metadata = get_portfolio_metadata()

        if not metadata or not metadata.get("products"):
            with st.spinner("Initial load in progress, please wait..."):
                # Call blocking portfolio calculation to generate initial data
                response = requests.post(f"{API_BASE_URL}/portfolio/calculate", timeout=300)
                response.raise_for_status()
                # Clear caches and reload metadata after initial calculation
                get_portfolio_metadata.clear()
                get_portfolio_performance_daily.clear()
                metadata = get_portfolio_metadata()
                if not metadata or not metadata.get("products"):
                    st.error("Failed to load portfolio data after initial calculation.")
                    st.stop()

    except Exception as e:
        st.toast(f"Error during startup refresh logic: {e}")
        # Attempt to show the ticker mapping page if there's an issue
        st.page_link("app_pages/ticker_mapping.py", label="Click here to check ticker mapping", icon="ℹ️")
        st.stop()

    st.session_state.startup_refresh = True

# Clear the placeholder once the data is ready
loading_placeholder.empty()

try:
    # Load metadata for filters
    metadata = get_portfolio_metadata()
    if not metadata or not metadata.get("products"):
        st.info("No portfolio data found. Please upload a transaction file and refresh the data.")
        st.stop()
except Exception as e:
    st.error(f"Failed to load portfolio metadata: {e}")
    st.stop()

# Move the file uploader and refresh button to the sidebar
with st.sidebar:
    # Sort product options
    product_options = sorted(metadata.get("products", []))
    if "Full portfolio" in product_options:
        product_options.remove("Full portfolio")
        product_options.insert(0, "Full portfolio")

    # Set default index for "Full Portfolio"
    default_index = product_options.index("Full portfolio") if "Full portfolio" in product_options else 0
    selected_product = st.selectbox("Select a Product", options=product_options, index=default_index, key="product_select")

    # Dropdown to select another product for comparison
    compare_product_options = ["None"] + product_options
    selected_compare_product = st.selectbox("Compare with another Product", options=compare_product_options, index=0, key="compare_product_select")

    # Performance metrics
    # Define metrics from the rename_dict to avoid needing the full dataframe upfront
    non_metric_cols = ['Product', 'Ticker', 'Start Date', 'End Date']
    performance_metrics = sorted([v for k, v in PERFORMANCE_METRIC_RENAME.items() if v not in non_metric_cols])
    default_index_per = performance_metrics.index("Net Performance (%)") if "Net Performance (%)" in performance_metrics else 0
    selected_metric = st.selectbox("Select a Performance Metric", options=performance_metrics, index=default_index_per, key="metric_select")

# Prepare list of products to fetch data for
products_to_fetch = [selected_product]
if selected_compare_product != "None":
    products_to_fetch.append(selected_compare_product)

try:
    # Load only the data for the selected products
    df = get_portfolio_performance_daily(products=products_to_fetch)

    if df.empty:
        st.info(f"No data found for product(s): {', '.join(products_to_fetch)}")
        st.stop()

    # Rename columns for display
    df = df.rename(columns=PERFORMANCE_METRIC_RENAME)

except Exception as e:
    st.error(f"Failed to load performance data: {e}")
    st.stop()

# Filter on product
product_df = df[df['Product'] == selected_product]
compare_product_df = df[df['Product'] == selected_compare_product] if selected_compare_product != "None" else pd.DataFrame()

# DATE  FILTER    
# Set the full date range as min and max values for the slider
max_date, min_date = metadata.get("max_date"), metadata.get("min_date")

# Date selection
date_selection = st.segmented_control(
    "Date Range",
    options=DATE_RANGE_OPTIONS,
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
filtered_df = product_df[(product_df['End Date'] >= selected_start_date) & (product_df['End Date'] <= selected_end_date)].sort_values(by='End Date')

st.subheader(f"{selected_product}")

# Top level metrics
if not filtered_df.empty:

    # Top current value
    top_current_value_start = filtered_df.iloc[-2].get('Current Value (€)', 0) if len(filtered_df) > 1 else 0
    top_current_value_end = filtered_df.iloc[-1].get('Current Value (€)', 0)
    top_current_value_delta = round((top_current_value_end-top_current_value_start), 2)

    if top_current_value_start != 0:
        top_current_value_delta_eur = f"+€ {abs(top_current_value_delta)}" if top_current_value_delta > 0 else f"-€ {abs(top_current_value_delta)}"
        top_current_value_delta_per = round(((top_current_value_end-top_current_value_start)/abs(top_current_value_start))*100, 2)
    else:
        top_current_value_delta_eur = 0
        top_current_value_delta_per = 0

    # Top current return
    top_current_return_start = filtered_df.iloc[-2].get('Current Money Weighted Return (€)', 0) if len(filtered_df) > 1 else 0
    top_current_return_end = filtered_df.iloc[-1].get('Current Money Weighted Return (€)', 0)
    top_current_return_delta = round((top_current_return_end-top_current_return_start), 2)

    if top_current_return_start != 0:
        top_current_return_delta_eur = f"+€ {abs(top_current_return_delta)}" if top_current_return_delta > 0 else f"-€ {abs(top_current_return_delta)}"
        top_current_return_delta_per = round(((top_current_return_end-top_current_return_start)/abs(top_current_return_start))*100, 2)
    else:
        top_current_return_delta_eur = 0
        top_current_return_delta_per = 0

    # Top net return
    top_net_return_start = filtered_df.iloc[-2].get('Net Return (€)', 0) if len(filtered_df) > 1 else 0
    top_net_return_end = filtered_df.iloc[-1].get('Net Return (€)', 0)
    top_net_return_delta = round((top_net_return_end-top_net_return_start), 2)

    if top_net_return_start != 0:
        top_net_return_delta_eur = f"+€ {abs(top_net_return_delta)}" if top_net_return_delta > 0 else f"-€ {abs(top_net_return_delta)}"
        top_net_return_delta_per = round(((top_net_return_end-top_net_return_start)/abs(top_net_return_start))*100, 2)
    else:
        top_net_return_delta_eur = 0
        top_net_return_delta_per = 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Current Value on Last Day", value=f"€ {top_current_value_end}", delta=f"{top_current_value_delta_per} % | {top_current_value_delta_eur}", border=True)
    with col2:
        st.metric(label="Current Return on Last Day", value=f"€ {top_current_return_end}", delta=f"{top_current_return_delta_per} % | {top_current_return_delta_eur}", border=True)
    with col3:
        st.metric(label="Net Return on Last Day", value=f"€ {top_net_return_end}", delta=f"{top_net_return_delta_per} % | {top_net_return_delta_eur}", border=True)
    
    st.divider()

# Plot performance over time
if not filtered_df.empty:
    st.subheader(f"{selected_metric} for {selected_product}")

    # Top metric (selected)
    top_selected_metric_start = filtered_df.iloc[-2].get(selected_metric, 0) if len(filtered_df) > 1 else 0
    top_selected_metric_end = filtered_df.iloc[-1].get(selected_metric, 0)
    top_selected_metric_delta = round((top_selected_metric_end-top_selected_metric_start), 2)

    if top_selected_metric_start != 0:
        top_selected_metric_delta_eur = f"+€ {abs(top_selected_metric_delta)}" if top_selected_metric_delta > 0 else f"-€ {abs(top_selected_metric_delta)}"
        top_selected_metric_delta_per = round(((top_selected_metric_end-top_selected_metric_start)/abs(top_selected_metric_start))*100, 2)
    else:
        top_selected_metric_delta_eur = 0
        top_selected_metric_delta_per = 0

    # Top net return YTD

    # Get last year rows (for returns/cost at the very end of last year)
    last_year_rows = product_df[product_df['End Date'].dt.year == (datetime.now().year-1)].sort_values(by='End Date')

    top_net_return_ytd_start = (
        last_year_rows.iloc[-1].get('Net Return (€)', 0) if not last_year_rows.empty
        else 0
    )

    top_total_cost_ytd_start = (
        last_year_rows.iloc[-1].get('Total Cost (€)', 0) if not last_year_rows.empty
        else 0
    )
    
    if top_total_cost_ytd_start != 0:
        top_net_return_ytd_delta = round((top_net_return_end-top_net_return_ytd_start), 2)
        top_net_return_ytd_delta_eur = f"+€ {abs(top_net_return_ytd_delta)}" if top_net_return_ytd_delta> 0 else f"-€ {abs(top_net_return_ytd_delta)}"
        top_net_return_ytd_delta_per = round(((top_net_return_end-top_net_return_ytd_start)/abs(top_total_cost_ytd_start))*100, 2)
    else:
        top_net_return_ytd_delta_eur = 0
        top_net_return_ytd_delta_per = 0

    # Adjust displayed string based on metric type
    if '€' in selected_metric:
        selected_metric_value = f'€ {top_selected_metric_end}'
        selected_metric_delta = f'{top_selected_metric_delta_per} % | {top_selected_metric_delta_eur}'
    elif '%' in selected_metric:
        selected_metric_value = f'{top_selected_metric_end} %'
        selected_metric_delta = f'{top_selected_metric_delta} %p'
    else:
        selected_metric_value = top_selected_metric_end
        selected_metric_delta = f'{top_selected_metric_delta}'

    # Display top metric (selected)
    if ('Net' in selected_metric) and (str(datetime.now().year) in str(selected_end_date)):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label=selected_metric, value=selected_metric_value, delta=selected_metric_delta, border=False, width="content")
        with col2:
            if top_total_cost_ytd_start == 0:
                pass
            elif selected_metric == 'Net Performance (%)':
                st.metric(label="YTD - Net Performance (%)", value=f"{top_net_return_ytd_delta_per} %", delta=f"{top_net_return_ytd_delta_eur}", border=False, width="content")
            else:
                st.metric(label="YTD - Net Return (€)", value=f" {top_net_return_ytd_delta_eur}", delta=f"{top_net_return_ytd_delta_per} %", border=False, width="content")
        with col3:
            pass
    else:
        st.metric(label=selected_metric, value=selected_metric_value, delta=selected_metric_delta, border=False, width="content")

    # Plot
    fig = px.line()

    # Add the first trace (main product) using add_scatter
    fig.add_scatter(x=filtered_df['End Date'], 
                        y=filtered_df[selected_metric], 
                        mode='lines', 
                        name=f"{selected_product}", 
                        line=dict(color="#1f77b4", shape='spline', smoothing=0.7))
    
    fig.update_layout(width=1200, height=400, margin=dict(l=0, r=0, t=50, b=50),)

    # Add comparison line if another product is selected
    if not compare_product_df.empty:
        compare_filtered_df = compare_product_df[(compare_product_df['End Date'] >= selected_start_date) & (compare_product_df['End Date'] <= selected_end_date)].sort_values(by='End Date')
        fig.add_scatter(x=compare_filtered_df['End Date'], 
                        y=compare_filtered_df[selected_metric], 
                        mode='lines', 
                        name=f"{selected_compare_product}", 
                        line=dict(color='orange', shape='spline', smoothing=0.7))

        # Set legend visible if two lines are plotted
        fig.update_layout(showlegend=True, legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center", yanchor="bottom"))

    st.plotly_chart(fig, use_container_width=False)
else:
    st.write("No data available for the selected product and date range.")

with st.expander("Data", expanded=False):
    st.write(filtered_df.drop(columns=['Start Date']))

with st.sidebar:
    # File uploader for the user to upload a new CSV file
    uploaded_file = st.file_uploader("Upload New Transactions CSV", type=["csv"])

    # Refresh Button to update the CSV
    if st.button('Refresh Data'):
        get_portfolio_metadata.clear()
        get_portfolio_performance_daily.clear()
        st.session_state.startup_refresh = False
        refresh_data(uploaded_file)
        time.sleep(1)
        st.rerun()

    # Refresh Button to refresh database if env variable is set to true
    if os.getenv("USE_SUPABASE", "true").lower() == "true":
        if st.button('Sync with Database'):
            # The trigger_db_sync function calls the API and handles showing
            # a success, warning, or error message.
            if trigger_db_sync():
                time.sleep(2)
                st.rerun()
    
    with st.expander("Delete Data", expanded=False):
        st.warning("This will delete all data from the database. Initial load will be required after this action.")
        if st.button('Delete Data', type="primary"):
            delete_data()
            st.rerun()

# Background refresh logic (runs once per session after startup)
if st.session_state.startup_refresh and "background_refresh_triggered" not in st.session_state:
    try:
        status_resp = requests.get(f"{API_BASE_URL}/portfolio/refresh/status", timeout=5)
        status_info = status_resp.json()
        if status_info.get("status") != "running":
            refresh_resp = requests.post(f"{API_BASE_URL}/portfolio/refresh", timeout=10)
            if refresh_resp.status_code == 409:
                st.toast("Portfolio refresh already in progress.")
            elif refresh_resp.status_code != 200:
                st.warning(f"Unexpected response from refresh endpoint: {refresh_resp.status_code}")
        else:
            st.toast("Portfolio refresh already in progress.")
        st.session_state.background_refresh_triggered = True
    except Exception as e:
        st.toast(f"Error triggering background refresh: {e}")
        st.session_state.background_refresh_triggered = True