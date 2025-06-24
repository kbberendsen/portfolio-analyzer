import os
import pandas as pd
from backend.utils.db import DB
from backend.utils.logger import app_logger

def fetch_and_save_parquet(db, table_name, parquet_path):
    """Fetch data from Supabase and save it to a Parquet file."""
    try:
        df = db.fetch_all_df(table_name)
        app_logger.info(f"[DB-REFRESH] Loaded {table_name} from Supabase.")
        df.to_parquet(parquet_path, index=False)
        app_logger.info(f"[DB-REFRESH] {table_name} saved to parquet file at {parquet_path}.")
    except Exception as e:
        app_logger.error(f"[DB-REFRESH] Failed to load {table_name} from Supabase: {e}", exc_info=True)

def upsert_and_replace_parquet(db, df, table_name, parquet_path):
    """Upsert local data to Supabase and replace local Parquet file with Supabase data."""
    try:
        app_logger.info(f"[DB-REFRESH] Upserting local {table_name} data to Supabase.")
        db.upsert_to_supabase(df, table_name)
        df = db.fetch_all_df(table_name)
        df.to_parquet(parquet_path, index=False)
        app_logger.info(f"[DB-REFRESH] Replaced local {table_name} parquet file with Supabase data.")
    except Exception as e:
        app_logger.error(f"[DB-REFRESH] Failed to upsert or replace {table_name}: {e}", exc_info=True)

def process_data(db, table_name, parquet_path):
    """Process data based on whether the Parquet file exists or not."""
    if not os.path.exists(parquet_path):
        app_logger.info(f"[DB-REFRESH] Parquet file for {table_name} not found at {parquet_path}. Fetching and saving new parquet.")
        fetch_and_save_parquet(db, table_name, parquet_path)
    else:
        app_logger.info(f"[DB-REFRESH] Parquet file for {table_name} found at {parquet_path}. Reading and upserting.")
        df = pd.read_parquet(parquet_path)
        upsert_and_replace_parquet(db, df, table_name, parquet_path)

def db_refresh():
    try:
        app_logger.info("[DB-REFRESH] Starting database refresh process...")
        use_supabase = os.getenv("USE_SUPABASE", "false").lower() == "true"
        app_logger.info(f"[DB-REFRESH] USE_SUPABASE flag is set to {use_supabase}.")
        if not use_supabase:
            app_logger.info("[DB-REFRESH] Supabase is disabled. Skipping database operations.")
            return

        db = DB()

        # Parquet file paths
        daily_parquet = 'output/portfolio_performance_daily.parquet'
        stock_prices_parquet = 'output/stock_prices.parquet'

        # Process each table
        process_data(db, 'portfolio_performance_daily', daily_parquet)
        process_data(db, 'stock_prices', stock_prices_parquet)

        app_logger.info("[DB-REFRESH] Database refresh process completed successfully.")
    except Exception as e:
        app_logger.error("[DB-REFRESH] Error during database refresh process", exc_info=True)