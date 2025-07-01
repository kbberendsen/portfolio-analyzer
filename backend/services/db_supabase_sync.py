import os
from backend.utils.db_supabase import DB_Supabase
from backend.utils.refresh_status import get_db_sync_status, set_db_sync_status
from backend.utils.logger import app_logger
from backend.utils.db import (
    load_portfolio_performance_from_db,
    load_stock_prices_from_db,
    save_portfolio_performance_to_db,
    save_stock_prices_to_db
)

def run_db_sync():
    """
    Core logic to synchronize data between local PostgreSQL and Supabase.
    - If local DB is empty, it restores data from Supabase.
    - If local DB has data, it backs up the data to Supabase.
    """
    try:
        app_logger.info("[DB-SYNC] Starting database synchronization process...")

        use_supabase = os.getenv("USE_SUPABASE", "false").lower() == "true"
        app_logger.info(f"[DB-SYNC] USE_SUPABASE flag is set to {use_supabase}.")
        if not use_supabase:
            app_logger.info("[DB-SYNC] Supabase is disabled. Skipping sync.")
            return

        # Initialize clients
        supabase_db = DB_Supabase()

        # Check if local database is empty
        app_logger.info("[DB-SYNC] Checking local PostgreSQL for existing data...")
        local_portfolio_df = load_portfolio_performance_from_db()
        local_stock_prices_df = load_stock_prices_from_db()

        if local_portfolio_df.empty and local_stock_prices_df.empty:
            # --- SCENARIO 1: RESTORE FROM SUPABASE ---
            app_logger.info("[DB-SYNC] Local database is empty. Attempting to restore from Supabase.")

            # Fetch portfolio performance
            app_logger.info("[DB-SYNC] Fetching 'portfolio_performance_daily' from Supabase...")
            supabase_portfolio_df = supabase_db.fetch_all_df('portfolio_performance_daily')
            if not supabase_portfolio_df.empty:
                save_portfolio_performance_to_db(supabase_portfolio_df)
                app_logger.info(f"[DB-SYNC] Restored {len(supabase_portfolio_df)} rows to local 'portfolio_performance_daily' table.")
            else:
                app_logger.info("[DB-SYNC] No 'portfolio_performance_daily' data found in Supabase to restore.")

            # Fetch stock prices
            app_logger.info("[DB-SYNC] Fetching 'stock_prices' from Supabase...")
            supabase_stock_prices_df = supabase_db.fetch_all_df('stock_prices')
            if not supabase_stock_prices_df.empty:
                save_stock_prices_to_db(supabase_stock_prices_df)
                app_logger.info(f"[DB-SYNC] Restored {len(supabase_stock_prices_df)} rows to local 'stock_prices' table.")
            else:
                app_logger.info("[DB-SYNC] No 'stock_prices' data found in Supabase to restore.")
            
            app_logger.info("[DB-SYNC] Restore from Supabase process completed.")

        else:
            # --- SCENARIO 2: BACKUP TO SUPABASE ---
            app_logger.info("[DB-SYNC] Local database contains data. Backing up to Supabase.")

            # Backup portfolio performance
            if not local_portfolio_df.empty:
                app_logger.info(f"[DB-SYNC] Upserting {len(local_portfolio_df)} rows to Supabase table 'portfolio_performance_daily'.")
                supabase_db.upsert_to_supabase(local_portfolio_df, 'portfolio_performance_daily')
                app_logger.info("[DB-SYNC] Successfully backed up portfolio performance data.")

            # Backup stock prices
            if not local_stock_prices_df.empty:
                app_logger.info(f"[DB-SYNC] Upserting {len(local_stock_prices_df)} rows to Supabase table 'stock_prices'.")
                supabase_db.upsert_to_supabase(local_stock_prices_df, 'stock_prices')
                app_logger.info("[DB-SYNC] Successfully backed up stock prices data.")
            
            app_logger.info("[DB-SYNC] Backup to Supabase process completed.")

        app_logger.info("[DB-SYNC] Database synchronization process completed successfully.")
    except Exception as e:
        app_logger.error("[DB-SYNC] Error during database synchronization process", exc_info=True)
        raise

def db_supabase_sync():
    """
    Wrapper to run the sync, managing status to prevent concurrent runs.
    """
    if get_db_sync_status() == "running":
        app_logger.warning("[DB-SYNC] Triggered DB sync, but a sync is already in progress. Skipping.")
        return

    try:
        app_logger.info("[DB-SYNC] Starting background DB sync...")
        set_db_sync_status("running")
        run_db_sync()
        app_logger.info("[DB-SYNC] Background DB sync completed successfully.")
        set_db_sync_status("idle")
    except Exception:
        app_logger.error("[DB-SYNC] Error during background DB sync", exc_info=True)
        set_db_sync_status("failed")
        raise