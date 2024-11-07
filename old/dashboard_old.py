import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import plotly.express as px
import subprocess
import os

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
        subprocess.run(['python', 'main.py'], check=True)  # Use 'python' instead of 'python3' if necessary
        st.success("Data updated successfully!")
    except subprocess.CalledProcessError as e:
        st.error(f"Error occurred while refreshing data: {e}")

##################################################
# Daily
##################################################

# Load data
df = pd.read_csv(os.path.join('output', 'portfolio_monthly.csv'))

# Convert start_date and end_date to datetime format using strptime
df['start_date'] = df['start_date'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d'))
df['end_date'] = df['end_date'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d'))

# Display title
st.title("Stock Portfolio Performance Dashboard")

# File uploader for the user to upload a new CSV file
uploaded_file = st.file_uploader("Upload New Transactions CSV", type=["csv"])

# Refresh Button to update the CSV
if st.button('Refresh Data'):
    refresh_data()

# Sort product options
product_options = sorted(df['product'].unique().tolist())

# Move "Full Portfolio" to the top if it exists
if "Full Portfolio" in product_options:
    product_options.remove("Full portfolio")
    product_options.insert(0, "Full portfolio")

# Set "Full Portfolio" as the default option
default_index = product_options.index("Full portfolio")
selected_product = st.selectbox("Select a Product", options=product_options, index=default_index, key="product_select")

# Get list of performance metrics
performance_metrics = [col for col in df.columns if col not in ['product', 'ticker', 'quantity', 'start_date', 'end_date']]
default_index_per = performance_metrics.index("net_performance_percentage")
selected_metric = st.selectbox("Select a Performance Metric", options=performance_metrics, index=default_index_per, key="metric_select")

# Filter data by selected product
product_df = df[df['product'] == selected_product]

# Date range filter
st.subheader("Filter by End Date Range")

# Convert to datetime
min_date = df['start_date'].min().to_pydatetime()
max_date = df['end_date'].max().to_pydatetime()

# Use string format if needed
min_date, max_date = st.slider(
    "Select Date Range",
    value=(min_date, max_date),
    format="YYYY-MM"
)

# Filter data by date range
filtered_df = product_df[(product_df['end_date'] >= min_date) & (product_df['end_date'] <= max_date)]

# Plot performance over time
if not filtered_df.empty:
    st.subheader(f"{selected_metric} for {selected_product} - By Month")
    
    # Create an interactive line plot using Plotly
    fig = px.line(filtered_df, x='end_date', y=selected_metric, 
                  title=f"{selected_metric} for {selected_product} - By Month", 
                  labels={"end_date": "End Date", selected_metric: selected_metric})
    
    # Adjust the size of the plot
    fig.update_layout(
        width=1200,  # Width of the plot (in pixels)
        height=600,  # Height of the plot (in pixels)
    )

    # Show the plot
    st.plotly_chart(fig, use_container_width=False)
else:
    st.write("No data available for the selected product and date range.")

# Display the data
st.subheader("Monthly data")
st.write(filtered_df)

##################################################
# Daily
##################################################

daily_df = pd.read_csv(os.path.join('output', 'portfolio_daily.csv'))

# Convert start_date and end_date to datetime format using strptime
daily_df['start_date'] = daily_df['start_date'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d'))
daily_df['end_date'] = daily_df['end_date'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d'))

# Sort product options
daily_product_options = sorted(daily_df['product'].unique().tolist())

# Move "Full Portfolio" to the top if it exists
if "Full Portfolio" in daily_product_options:
    product_options.remove("Full portfolio")
    product_options.insert(0, "Full portfolio")

# Set "Full Portfolio" as the default option
default_index = product_options.index("Full portfolio")
daily_selected_product = st.selectbox("Select a Product", options=daily_product_options, index=default_index, key="daily_product_select")

# Get list of performance metrics
# Get list of performance metrics
performance_metrics = [col for col in df.columns if col not in ['product', 'ticker', 'quantity', 'start_date', 'end_date']]
default_index_per = performance_metrics.index("net_performance_percentage")
daily_selected_metric = st.selectbox("Select a Performance Metric", options=performance_metrics, index=default_index_per, key="daily_metric_select")

# Filter data by selected product
daily_product_df = daily_df[daily_df['product'] == daily_selected_product]

# Date range filter
st.subheader("Filter by End Date Range")

# Convert to datetime
daily_min_date = daily_df['start_date'].min().to_pydatetime()
daily_max_date = daily_df['end_date'].max().to_pydatetime()

# Use string format if needed
daily_min_date, daily_max_date = st.slider(
    "Select Date Range",
    value=(daily_min_date, daily_max_date),
    format="YYYY-MM-DD"
)

# Filter data by date range
daily_filtered_df = daily_product_df[(daily_product_df['end_date'] >= daily_min_date) & (daily_product_df['end_date'] <= daily_max_date)]

# Plot performance over time
if not daily_filtered_df.empty:
    st.subheader(f"{daily_selected_metric} for {daily_selected_product} - Daily")
    
    # Create an interactive line plot using Plotly
    daily_fig = px.line(daily_filtered_df, x='end_date', y=daily_selected_metric, 
                  title=f"{daily_selected_metric} for {daily_selected_product} - Daily", 
                  labels={"end_date": "End Date", daily_selected_metric: daily_selected_metric})
    
    # Adjust the size of the plot
    daily_fig.update_layout(
        width=1200,  # Width of the plot (in pixels)
        height=600,  # Height of the plot (in pixels)
    )

    # Show the plot
    st.plotly_chart(daily_fig, use_container_width=False)
else:
    st.write("No data available for the selected product and date range.")

# Display the data
st.subheader("Daily data")
st.write(daily_filtered_df)
