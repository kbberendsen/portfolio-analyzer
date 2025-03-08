import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, date, timedelta
from helpers.ticker_mapping import ticker_to_name, isin_to_ticker
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import time

# Load environment variables from .env file
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class DB:
    def __init__(self, supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY):
        # Initialize the Supabase client
        self.supabase: Client = create_client(supabase_url, supabase_key)

        def _retry_operation(operation, max_retries, *args, **kwargs):
            """Helper method to retry an operation with a specified number of retries."""
            for attempt in range(max_retries):
                try:
                    return operation(*args, **kwargs)
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed: {e}")
                    if attempt + 1 == max_retries:
                        print("Max retries reached. Operation failed.")
                        return None
                    time.sleep(attempt + 1)  # Increasing sleep duration after each retry

        self._retry_operation = _retry_operation

    def get_row_count(self, table_name: str, max_retries=3) -> int:
        """Returns the number of rows in the given table."""
        def operation():
            response = self.supabase.table(table_name).select("count").single().execute()
            return response

        return self._retry_operation(operation, max_retries)

    def upsert_to_supabase(self, df: pd.DataFrame, table_name: str, upsert_keys: list, max_retries=5):
        """
        Upsert data to Supabase in bulk with retry mechanism.

        :param df: DataFrame containing the data to be upserted
        :param table: Name of the Supabase table to upsert data into
        :param max_retries: Maximum number of retries for the upsert operation
        """
        # Convert the entire DataFrame to a list of dictionaries for bulk upsert
        data = df.to_dict(orient='records')

        def operation():
            response = self.supabase.table(table_name).upsert(data).execute()
            if 'error' in response:
                print(f"Upsert failed: {response.error_message}")
            else:
                print(f"Successfully upserted {len(data)} rows into {table_name} table.")
            return response

        self._retry_operation(operation, max_retries)

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
            if 'error' in response:
                print("Upsert failed (stock prices)", response["error"])
            else:
                print(f"Successfully upserted {len(data)} rows into {table_name} table.")
            return response

        self._retry_operation(operation, max_retries)

    def fetch_all_df(self, table_name, max_retries=3):
        """Fetch all rows from a Supabase table using pagination."""
        all_rows = []
        page_size = 1000  # Adjust the page size as needed
        offset = 0

        def operation():
            nonlocal offset
            response = self.supabase.table(table_name).select('*').range(offset, offset + page_size - 1).execute()
            if response.data:
                all_rows.extend(response.data)
                offset += page_size
            return response

        while True:
            result = self._retry_operation(operation, max_retries)
            if not result or not result.data:
                break

        return pd.DataFrame(all_rows)