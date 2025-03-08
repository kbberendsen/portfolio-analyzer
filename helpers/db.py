import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, date, timedelta
from helpers.ticker_mapping import ticker_to_name, isin_to_ticker
from supabase import create_client, Client
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class DB:
    def __init__(self, supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY):
        # Initialize the Supabase client
        self.supabase: Client = create_client(supabase_url, supabase_key)

    def get_row_count(self, table_name: str) -> int:
        """Returns the number of rows in the given table."""
        # Fetch the row count using Supabase client
        response = self.supabase.table(table_name).select("count").single().execute()
        
        return response

    def upsert_to_supabase(self, df: pd.DataFrame, table_name: str, upsert_keys: list, max_retries=3):
        """
        Upsert data to Supabase in bulk with retry mechanism.

        :param df: DataFrame containing the data to be upserted
        :param table: Name of the Supabase table to upsert data into
        :param max_retries: Maximum number of retries for the upsert operation
        """
        # Convert the entire DataFrame to a list of dictionaries for bulk upsert
        data = df.to_dict(orient='records')
        
        # Perform bulk upsert with retry mechanism
        for attempt in range(max_retries):
            try:
                response = self.supabase.table(table_name).upsert(data).execute()
                # Check response and handle
                if 'error' in response:
                    print(f"Upsert failed: {response.error_message}")
                else:
                    print(f"Successfully upserted {len(data)} rows into {table_name} table.")
                    break
            except Exception as e:
                print(f"Upsert attempt {attempt + 1} failed: {e}")
                if attempt + 1 == max_retries:
                    print("Max retries reached. Upsert operation failed.")

    def store_stock_prices(self, stock_price_data):
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

        # Upsert data in bulk to avoid looping inserts
        response = self.supabase.table(table_name).upsert(data).execute()

        if 'error' in response:
            print("Upsert failed (stock prices)", response["error"])
        else:
            print(f"Successfully upserted {len(data)} rows into {table_name} table.")

    def fetch_all_df(self, table_name):
        """Fetch all rows from a Supabase table using pagination."""
        all_rows = []
        page_size = 1000  # Adjust the page size as needed
        offset = 0

        while True:
            response = self.supabase.table(table_name).select('*').range(offset, offset + page_size - 1).execute()
            if response.data:
                all_rows.extend(response.data)
                offset += page_size
            else:
                break

        return pd.DataFrame(all_rows)

