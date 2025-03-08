import os
import pandas as pd
from helpers.db import DB
 
db = DB()

def db_refresh(db):
    # Check if Parquet files exist
    portfolio_parquet_path = 'output/portfolio_performance_daily.parquet'
    stock_prices_parquet_path = 'output/stock_prices.parquet'

    if not os.path.exists(portfolio_parquet_path) or not os.path.exists(stock_prices_parquet_path):
        # Fetch all portfolio performance data from Supabase
        try:
            db_portfolio_results_df = db.fetch_all_df('portfolio_performance_daily')
            print('Loaded portfolio_performance_daily from Supabase')
        except Exception as e:
            print(f'Failed to load portfolio_performance_daily from Supabase: {e}')

        # Fetch all stock prices from Supabase
        try:
            db_stock_prices_df = db.fetch_all_df('stock_prices')
            db_stock_prices_df = db_stock_prices_df.dropna(subset=['price'])
            print('Loaded stock_prices from Supabase')
        except Exception as e:
            print(f'Failed to load stock_prices from Supabase: {e}')

        # Save the data to Parquet files
        db_portfolio_results_df.to_parquet(portfolio_parquet_path, index=False)
        db_stock_prices_df.to_parquet(stock_prices_parquet_path, index=False)
        print('Data saved to Parquet files')

    else:
        # Load data from Parquet files
        db_portfolio_results_df = pd.read_parquet(portfolio_parquet_path)
        db_stock_prices_df = pd.read_parquet(stock_prices_parquet_path)
        print('Loaded data from Parquet files')

        # Upsert data to Supabase
        db.upsert_to_supabase(db_portfolio_results_df, 'portfolio_performance_daily')
        db.upsert_to_supabase(db_stock_prices_df, 'stock_prices')

db_refresh(db)