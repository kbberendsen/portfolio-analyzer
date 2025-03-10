import os
import pandas as pd
from helpers.db import DB
 
db = DB()

def db_refresh(db):
    # Check if Parquet files exist
    daily_portfolio_parquet_path = 'output/portfolio_performance_daily.parquet'
    monthly_portfolio_parquet_path = 'output/portfolio_performance_monthly.parquet'
    stock_prices_parquet_path = 'output/stock_prices.parquet'

    # Daily
    if not os.path.exists(daily_portfolio_parquet_path):
        # Fetch daily portfolio performance data from Supabase
        try:
            db_daily_portfolio_results_df = db.fetch_all_df('portfolio_performance_daily')
            print('Loaded portfolio_performance_daily from Supabase')
            # Save the data to Parquet files
            db_daily_portfolio_results_df.to_parquet(daily_portfolio_parquet_path, index=False)
            print('Daily saved to parquet file.')
        except Exception as e:
            print(f'Failed to load portfolio_performance_daily from Supabase: {e}')

    else:
        print('Upserting local daily data to Supabase')
        db_daily_portfolio_results_df = pd.read_parquet(daily_portfolio_parquet_path)
        db.upsert_to_supabase(db_daily_portfolio_results_df, 'portfolio_performance_daily')

    # Monthly
    if not os.path.exists(monthly_portfolio_parquet_path):
        # Fetch monthly portfolio performance data from Supabase
        try:
            db_monthly_portfolio_results_df = db.fetch_all_df('portfolio_performance_monthly')
            print('Loaded portfolio_performance_monthly from Supabase')
            db_monthly_portfolio_results_df.to_parquet(monthly_portfolio_parquet_path, index=False)
            print('Monthly saved to parquet file.')
        except Exception as e:
            print(f'Failed to load portfolio_performance_monthly from Supabase: {e}')
       
    else:
        print('Upserting local monthly data to Supabase')
        db_monthly_portfolio_results_df = pd.read_parquet(monthly_portfolio_parquet_path)
        db.upsert_to_supabase(db_monthly_portfolio_results_df, 'portfolio_performance_monthly')

    # Stock prices
    if not os.path.exists(stock_prices_parquet_path):
        # Fetch all stock prices from Supabase
        try:
            db_stock_prices_df = db.fetch_all_df('stock_prices')
            db_stock_prices_df = db_stock_prices_df.dropna(subset=['price'])
            print('Loaded stock_prices from Supabase')
            db_stock_prices_df.to_parquet(stock_prices_parquet_path, index=False)
            print('Stock prices saved to parquet file.')
        except Exception as e:
            print(f'Failed to load stock_prices from Supabase: {e}')

    else:
        print('Upserting local stock prices data to Supabase')
        db_stock_prices_df = pd.read_parquet(stock_prices_parquet_path)
        db.upsert_to_supabase(db_stock_prices_df, 'stock_prices')

db_refresh(db)