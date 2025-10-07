import pandas as pd
import numpy as np
from supabase import create_client, Client
import os
import time
import decimal
from datetime import date, datetime
from backend.utils.logger import app_logger

class DB_Supabase:
    def __init__(self):
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_KEY = os.getenv("SUPABASE_KEY")
        # Initialize the Supabase client
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

        def _retry_operation(operation, max_retries, *args, **kwargs):
            """Helper method to retry an operation with logging and backoff."""
            for attempt in range(max_retries):
                try:
                    return operation(*args, **kwargs)
                except Exception as e:
                    app_logger.warning(f"[DB-SYNC] Attempt {attempt + 1} failed: {e}")
                    if attempt + 1 == max_retries:
                        app_logger.error("[DB-SYNC] Max retries reached. Operation failed.")
                        return None
                    time.sleep(attempt + 0.5)  # exponential backoff could be added here

        self._retry_operation = _retry_operation

    def get_row_count(self, table_name: str, max_retries=3) -> int:
        """Returns the number of rows in the given table."""
        def operation():
            response = self.supabase.table(table_name).select("count").single().execute()
            if response.status_code != 200:
                app_logger.error(f"[DB-SYNC] Error getting row count for '{table_name}': Status {response.status_code}")
                return 0
            return response.data.get('count', 0) if response.data else 0

        return self._retry_operation(operation, max_retries)

    def upsert_to_supabase(self, df: pd.DataFrame, table_name: str, max_retries=5):
        """
        Upsert data to Supabase in bulk with retry mechanism.
        Logs result and returns response for checking.
        """
        if df.empty:
            app_logger.info(f"[DB-SYNC] Skipping upsert: DataFrame for '{table_name}' is empty.")
            return None
        
        df = df.copy()

        # Convert datetime and date columns to ISO format
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].apply(lambda x: x.isoformat() if pd.notnull(x) else None)
            elif df[col].apply(lambda x: isinstance(x, (date, datetime))).any():
                df[col] = df[col].apply(lambda x: x.isoformat() if pd.notnull(x) else None)

        # Convert Decimal columns to float
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, decimal.Decimal)).any():
                df[col] = df[col].apply(lambda x: float(x) if pd.notnull(x) else None)

        data = df.to_dict(orient='records')

        def operation():
            response = self.supabase.table(table_name).upsert(data).execute()

            if response.status_code != 200:
                app_logger.error(f"[DB-SYNC] Upsert to '{table_name}' failed: Status {response.status_code}")
                return 0
            else:
                app_logger.info(f"[DB-SYNC] Successfully upserted {len(data)} rows to '{table_name}'.")
            return response

        return self._retry_operation(operation, max_retries)

    def store_stock_prices(self, stock_price_data, max_retries=3):
        """
        Efficiently stores stock prices in the 'stock_prices' table using batch upsert.
        """
        table_name = "stock_prices"

        # Flatten the dict into a list of records for batch processing
        data = [
            {"ticker": ticker, "date": date, "price": None if np.isnan(price) else price}
            for ticker, date_prices in stock_price_data.items()
            for date, price in date_prices.items()
        ]

        def operation():
            response = self.supabase.table(table_name).upsert(data).execute()

            if response.status_code != 200:
                app_logger.error(f"[DB-SYNC] Stock price upsert failed: Status {response.status_code}")
                return 0
            else:
                app_logger.info(f"[DB-SYNC] Successfully upserted {len(data)} rows to '{table_name}'.")
            return response

        return self._retry_operation(operation, max_retries)

    def fetch_all_df(self, table_name, max_retries=3):
        """Fetch all rows from a Supabase table using pagination."""
        all_rows = []
        page_size = 1000  # Adjust the page size as needed
        offset = 0

        def operation():
            nonlocal offset
            response = self.supabase.table(table_name).select('*').range(offset, offset + page_size - 1).execute()

            if response.status_code != 200:
                app_logger.error(f"[DB-SYNC] Error fetching rows from '{table_name}': Status {response.status_code}")
                return 0
            
            if response.data:
                all_rows.extend(response.data)
                offset += page_size
            return response

        while True:
            result = self._retry_operation(operation, max_retries)
            if not result or not result.data:
                break

        df = pd.DataFrame(all_rows)
        app_logger.info(f"[DB-SYNC] Fetched {len(df)} rows from '{table_name}'.")
        return df