import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import plotly.express as px
import subprocess
import os

# Set the page title for the browser tab
st.set_page_config(page_title="Stock Portfolio Dashboard", page_icon=":bar_chart:")

st.title("Stock Portfolio Dashboard")

# Placeholder for the loading spinner while refreshing data on startup
loading_placeholder = st.empty()

uploaded_file = None

# Define startup refresh state variable
if "startup_refresh" not in st.session_state:
    st.session_state.startup_refresh = False  # Indicates refresh hasn't run yet

def check_columns(uploaded_df):
    # Define the expected columns for the transaction data
    required_columns = ['Datum', 'ISIN', 'Beurs', 'Aantal', 'Koers', 'Waarde', 'Transactiekosten en/of']
    
    try:
        st.write(uploaded_df.head())  # Display the first few rows of the uploaded file

        if uploaded_df.empty:
            st.error("Uploaded file is empty.")
            return False
        
        if all(col in uploaded_df.columns for col in required_columns):
            return True
        else:
            st.error("The uploaded file does not contain the required columns.")
            return False
        
    except Exception as e:
        st.error(f"Error reading the uploaded file: {e}")
        return False

def refresh_data():
    # Check for new transactions file
    if uploaded_file is not None:
        uploaded_df = pd.read_csv(uploaded_file)

        if not check_columns(uploaded_df):
            st.error("The uploaded CSV file does not have the required columns. Please upload a valid file.")
            return

        # Read the uploaded file into a DataFrame
        new_data = uploaded_df

        if new_data.empty:
            st.error("The uploaded file is empty after reading.")
            return

        # Save the new data to file
        file_path = os.path.join('uploads', 'Transactions.csv')
        new_data.to_csv(file_path, index=False)
        st.success(f"Data saved to {file_path}")
    
    # Run the 'main.py' script to update the CSV
    try:
        subprocess.run(['python', 'main.py'], check=True)
        if st.session_state.startup_refresh:
            st.success(f"Data updated successfully! (Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    except subprocess.CalledProcessError as e:
        st.error(f"Error occurred while refreshing data: {e}")

def clear_cache():
    cache_path_monthly = os.path.join('data', 'portfolio_results_monthly.pkl')
    cache_path_daily = os.path.join('data', 'portfolio_results_daily.pkl')

    if os.path.isfile(cache_path_monthly):
        os.remove(cache_path_monthly)
        print(f"{cache_path_monthly} has been deleted.")

    if os.path.isfile(cache_path_daily):
        os.remove(cache_path_daily)
        print(f"{cache_path_daily} has been deleted.")

    st.info("Data cleared. Use 'Refresh Data' to update data. This will take a few minutes.")

# Startup loading spinner
if not st.session_state.startup_refresh:
    with loading_placeholder.container():
        with st.spinner("Loading data..."):
            refresh_data()
            st.session_state.startup_refresh = True  # Mark that refresh has run

# Clear the placeholder once the data is ready
loading_placeholder.empty()

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

# Load monthly and daily data
df = pd.read_csv(os.path.join('output', 'portfolio_monthly.csv'))
daily_df = pd.read_csv(os.path.join('output', 'portfolio_daily.csv'))

# Rename columns
df = df.rename(columns=rename_dict)
daily_df = daily_df.rename(columns=rename_dict)

# Convert dates to datetime format
df['Start Date'] = df['Start Date'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d'))
df['End Date'] = df['End Date'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d'))

daily_df['Start Date'] = daily_df['Start Date'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d'))
daily_df['End Date'] = daily_df['End Date'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d'))

# Move the file uploader and refresh button to the sidebar
with st.sidebar:
    # Tabs for Daily and Monthly data
    tab_selection = st.radio(label="Select Data View", options=["Daily", "Monthly"])

    # Sort product options
    product_options = sorted(df['Product'].unique().tolist())
    if "Full portfolio" in product_options:
        product_options.remove("Full portfolio")
        product_options.insert(0, "Full portfolio")

    # Set default index for "Full Portfolio"
    default_index = product_options.index("Full portfolio")
    selected_product = st.selectbox("Select a Product", options=product_options, index=default_index, key="product_select")

    # Performance metrics
    performance_metrics = [col for col in df.columns if col not in ['Product', 'Ticker', 'Start Date', 'End Date']]
    default_index_per = performance_metrics.index("Net Performance (%)")
    selected_metric = st.selectbox("Select a Performance Metric", options=performance_metrics, index=default_index_per, key="metric_select")

# Handle monthly data
if tab_selection == "Monthly":
    st.header(f"{selected_product} - Monthly")

    with st.sidebar:

        # Set the full date range as min and max values for the slider
        min_date = df['Start Date'].min().to_pydatetime()
        max_date = df['End Date'].max().to_pydatetime()

        # Set the default start date
        default_start_date = min_date
        
        # Create the slider
        selected_start_date, selected_end_date = st.slider(
            "Select Date Range",
            min_value=min_date,
            max_value=max_date,
            value=(default_start_date, max_date),
            format="YYYY-MM"
        )
    
    # Filter on product
    product_df = df[df['Product'] == selected_product]
    
    # Filter data by date range
    filtered_df = product_df[(product_df['End Date'] >= selected_start_date) & (product_df['End Date'] <= selected_end_date)]

    # Top level metrics
    if not filtered_df.empty:

        # Top current value
        top_current_value_start = filtered_df.iloc[-2].get('Current Value (€)', 0)
        top_current_value_end = filtered_df.iloc[-1].get('Current Value (€)', 0)

        if top_current_value_start != 0:
            top_current_value_delta = round((top_current_value_end-top_current_value_start), 2)
            top_current_value_delta_eur = f"+€ {abs(top_current_value_delta)}" if top_current_value_delta > 0 else f"-€ {abs(top_current_value_delta)}"
            top_current_value_delta_per = round(((top_current_value_end-top_current_value_start)/(top_current_value_start))*100, 2)
        else:
            top_current_value_delta_eur = 0
            top_current_value_delta_per = 0

        # Top current return
        top_current_return_start = filtered_df.iloc[-2].get('Current Money Weighted Return (€)', 0)
        top_current_return_end = filtered_df.iloc[-1].get('Current Money Weighted Return (€)', 0)

        if top_current_return_start != 0:
            top_current_return_delta = round((top_current_return_end-top_current_return_start), 2)
            top_current_return_delta_eur = f"+€ {abs(top_current_return_delta)}" if top_current_return_delta > 0 else f"-€ {abs(top_current_return_delta)}"
            top_current_return_delta_per = round(((top_current_return_end-top_current_return_start)/(top_current_return_start))*100, 2)
        else:
            top_current_return_delta_eur = 0
            top_current_return_delta_per = 0

        # Top net return
        top_net_return_start = filtered_df.iloc[-2].get('Net Return (€)', 0)
        top_net_return_end = filtered_df.iloc[-1].get('Net Return (€)', 0)

        if top_net_return_start != 0:
            top_net_return_delta = round((top_net_return_end-top_net_return_start), 2)
            top_net_return_delta_eur = f"+€ {abs(top_net_return_delta)}" if top_net_return_delta > 0 else f"-€ {abs(top_net_return_delta)}"
            top_net_return_delta_per = round(((top_net_return_end-top_net_return_start)/(top_net_return_start))*100, 2)
        else:
            top_current_delta_eur = 0
            top_net_return_delta_per = 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Last Month Current Value", value=f"€ {top_current_value_end}", delta=f"{top_current_value_delta_per} % | {top_current_value_delta_eur}")
        with col2:
            st.metric(label="Last Month Current Return", value=f"€ {top_current_return_end}", delta=f"{top_current_return_delta_per} % | {top_current_return_delta_eur}")
        with col3:
            st.metric(label="Last Month Net Return", value=f"€ {top_net_return_end}", delta=f"{top_net_return_delta_per} % | {top_net_return_delta_eur}")

        st.divider()

    # Plot performance over time
    if not filtered_df.empty:
        st.subheader(f"{selected_metric} for {selected_product}")
        fig = px.line(filtered_df, x='End Date', y=selected_metric, 
                      title=f"{selected_metric} for {selected_product}", 
                      labels={"end_date": "End Date", selected_metric: selected_metric})
        fig.update_traces(line_shape='spline')  # Smooth spline interpolation
        fig.update_traces(line_smoothing=0.7)
        fig.update_layout(width=1200, height=500)
        st.plotly_chart(fig, use_container_width=False)

    else:
        st.write("No data available for the selected product and date range.")

    st.subheader("Monthly Data")
    st.write(filtered_df)

# Handle daily data
elif tab_selection == "Daily":
    st.header(f"{selected_product} - Daily")
 
    # Filter on product
    product_df = df[df['Product'] == selected_product]
    daily_product_df = daily_df[daily_df['Product'] == selected_product]

    with st.sidebar:

        # Set the full date range as min and max values for the slider
        #daily_min_date = daily_df['Start Date'].min().to_pydatetime()
        daily_max_date = daily_df['End Date'].max().to_pydatetime()
        # Subtract 3 months from the max date
        daily_min_date = daily_max_date - timedelta(days=365)

        # Set the default range to the last 90 days
        default_start_date = daily_max_date - timedelta(days=90)
        
        # Create the slider with the full date range but defaulting to the last 90 days
        selected_start_date, selected_end_date = st.slider(
            "Select Date Range",
            min_value=daily_min_date,
            max_value=daily_max_date,
            value=(default_start_date, daily_max_date),
            format="YYYY-MM-DD"
        )

    # Filter data by date range
    daily_filtered_df = daily_product_df[(daily_product_df['End Date'] >= selected_start_date) & (daily_product_df['End Date'] <= selected_end_date)].sort_values(by='End Date')

    # Top level metrics
    if not daily_filtered_df.empty:
        # Top current value
        top_current_value_start = daily_filtered_df.iloc[-2].get('Current Value (€)', 0)
        top_current_value_end = daily_filtered_df.iloc[-1].get('Current Value (€)', 0)

        if top_current_value_start != 0:
            top_current_value_delta = round((top_current_value_end-top_current_value_start), 2)
            top_current_value_delta_eur = f"+€ {abs(top_current_value_delta)}" if top_current_value_delta > 0 else f"-€ {abs(top_current_value_delta)}"
            top_current_value_delta_per = round(((top_current_value_end-top_current_value_start)/(top_current_value_start))*100, 2)
        else:
            top_current_value_delta_eur = 0
            top_current_value_delta_per = 0

        # Top current return
        top_current_return_start = daily_filtered_df.iloc[-2].get('Current Money Weighted Return (€)', 0)
        top_current_return_end = daily_filtered_df.iloc[-1].get('Current Money Weighted Return (€)', 0)

        if top_current_return_start != 0:
            top_current_return_delta = round((top_current_return_end-top_current_return_start), 2)
            top_current_return_delta_eur = f"+€ {abs(top_current_return_delta)}" if top_current_return_delta > 0 else f"-€ {abs(top_current_return_delta)}"
            top_current_return_delta_per = round(((top_current_return_end-top_current_return_start)/(top_current_return_start))*100, 2)
        else:
            top_current_return_delta_eur = 0
            top_current_return_delta_per = 0

        # Top net return
        top_net_return_start = daily_filtered_df.iloc[-2].get('Net Return (€)', 0)
        top_net_return_end = daily_filtered_df.iloc[-1].get('Net Return (€)', 0)

        if top_net_return_start != 0:
            top_net_return_delta = round((top_net_return_end-top_net_return_start), 2)
            top_net_return_delta_eur = f"+€ {abs(top_net_return_delta)}" if top_net_return_delta > 0 else f"-€ {abs(top_net_return_delta)}"
            top_net_return_delta_per = round(((top_net_return_end-top_net_return_start)/(top_net_return_start))*100, 2)
        else:
            top_net_return_delta_eur = 0
            top_net_return_delta_per = 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Current Value on Last Day", value=f"€ {top_current_value_end}", delta=f"{top_current_value_delta_per} % | {top_current_value_delta_eur}")
        with col2:
            st.metric(label="Current Return on Last Day", value=f"€ {top_current_return_end}", delta=f"{top_current_return_delta_per} % | {top_current_return_delta_eur}")
        with col3:
            st.metric(label="Net Return on Last Day", value=f"€ {top_net_return_end}", delta=f"{top_net_return_delta_per} % | {top_net_return_delta_eur}")
        
        st.divider()
    
    # Plot performance over time
    if not daily_filtered_df.empty:
        st.subheader(f"{selected_metric} for {selected_product}")

        # Top metric (selected)
        top_selected_metric_start = daily_filtered_df.iloc[-2].get(selected_metric, 0)
        top_selected_metric_end = daily_filtered_df.iloc[-1].get(selected_metric, 0)

        if top_selected_metric_start != 0:
            top_selected_metric_delta = round((top_selected_metric_end-top_selected_metric_start), 2)
            top_selected_metric_delta_eur = f"+€ {abs(top_selected_metric_delta)}" if top_selected_metric_delta > 0 else f"-€ {abs(top_selected_metric_delta)}"
            top_selected_metric_delta_per = round(((top_selected_metric_end-top_selected_metric_start)/(top_selected_metric_start))*100, 2)
        else:
            top_selected_metric_delta_eur = 0
            top_selected_metric_delta_per = 0

        # Top net return YTD

        # Get last year rows (for returns/cost at the very end of last year)
        last_year_rows = daily_product_df[daily_product_df['End Date'].dt.year == (datetime.now().year-1)].sort_values(by='End Date')

        top_net_return_ytd_start = (
            last_year_rows.iloc[-1].get('Net Return (€)', 0) if not last_year_rows.empty
            else 0
        )

        top_total_cost_ytd_start = (
            last_year_rows.iloc[-1].get('Total Cost (€)', 0) if not last_year_rows.empty
            else 0
        )
        
        if top_total_cost_ytd_start != 0:
            top_net_return_ytd_delta_eur = round((top_net_return_end-top_net_return_ytd_start), 2)
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
                st.metric(label=selected_metric, value=selected_metric_value, delta=selected_metric_delta)
            with col2:
                if selected_metric == 'Net Performance (%)':
                    st.metric(label="YTD - Net Performance (%)", value=f"{top_net_return_ytd_delta_per} %", delta=f"€ {top_net_return_ytd_delta_eur}")
                else:
                    st.metric(label="YTD - Net Return (€)", value=f" € {top_net_return_ytd_delta_eur}", delta=f"{top_net_return_ytd_delta_per} %")
            with col3:
                pass
        else:
            st.metric(label=selected_metric, value=selected_metric_value, delta=selected_metric_delta)

        # Plot
        daily_fig = px.line(daily_filtered_df, x='End Date', y=selected_metric, 
                            title=f"{selected_metric} for {selected_product}", 
                            labels={"end_date": "End Date", selected_metric: selected_metric})
        daily_fig.update_traces(line_shape='spline')  # Smooth spline interpolation
        daily_fig.update_traces(line_smoothing=0.7)
        daily_fig.update_layout(width=1200, height=500)
        st.plotly_chart(daily_fig, use_container_width=False)
    else:
        st.write("No data available for the selected product and date range.")

    st.subheader("Daily Data")
    st.write(daily_filtered_df)

# File upload
with st.sidebar:
    # File uploader for the user to upload a new CSV file
    uploaded_file = st.file_uploader("Upload New Transactions CSV", type=["csv"])

    # Refresh Button to update the CSV
    if st.button('Refresh Data'):
        refresh_data()
    
    if st.button('Clear Cached Data', type="primary"):
        clear_cache()