import os
import pandas as pd
from helpers.db import DB

def fetch_and_save_parquet(db, table_name, parquet_path):
    """Fetch data from Supabase and save it to a Parquet file."""
    try:
        # Fetch data from Supabase
        df = db.fetch_all_df(table_name)
        print(f'Loaded {table_name} from Supabase')
        # Save the data to Parquet file
        df.to_parquet(parquet_path, index=False)
        print(f'{table_name} saved to parquet file.')
    except Exception as e:
        print(f'Failed to load {table_name} from Supabase: {e}')

def upsert_and_replace_parquet(db, df, table_name, parquet_path):
    """Upsert local data to Supabase and replace local Parquet file with Supabase data."""
    try:
        print(f'Upserting local {table_name} data to Supabase')
        db.upsert_to_supabase(df, table_name)
        # Replace the local Parquet file with the Supabase data
        df = db.fetch_all_df(table_name)
        df.to_parquet(parquet_path, index=False)
        print(f'Replaced local {table_name} parquet file with Supabase data.')
    except Exception as e:
        print(f'Failed to upsert or replace {table_name}: {e}')

def process_data(db, table_name, parquet_path):
    """Process data based on whether the Parquet file exists or not."""
    if not os.path.exists(parquet_path):
        # Fetch and save Parquet file if it doesn't exist
        fetch_and_save_parquet(db, table_name, parquet_path)
    else:
        # Read the local Parquet file and upsert/replace data
        df = pd.read_parquet(parquet_path)
        upsert_and_replace_parquet(db, df, table_name, parquet_path)

def db_refresh():
    # Check if Supabase should be used
    use_supabase = os.getenv("USE_SUPABASE", "false").lower() == "true"
    if not use_supabase:
        print("Supabase is disabled. Skipping database operations.")
        return

    # Init db
    db = DB()

    # Define paths for the Parquet files
    daily_portfolio_parquet_path = 'output/portfolio_performance_daily.parquet'
    monthly_portfolio_parquet_path = 'output/portfolio_performance_monthly.parquet'
    stock_prices_parquet_path = 'output/stock_prices.parquet'

    # Process daily, monthly, and stock prices data
    process_data(db, 'portfolio_performance_daily', daily_portfolio_parquet_path)
    process_data(db, 'portfolio_performance_monthly', monthly_portfolio_parquet_path)
    process_data(db, 'stock_prices', stock_prices_parquet_path)

db_refresh()