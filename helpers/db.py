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

    def upsert_to_supabase(self, df: pd.DataFrame, table_name: str, upsert_keys: list):
        """
        Upsert data to Supabase in bulk.

        :param df: DataFrame containing the data to be upserted
        :param table: Name of the Supabase table to upsert data into
        """
        # Convert the entire DataFrame to a list of dictionaries for bulk upsert
        data = df.to_dict(orient='records')
        
        # Perform bulk upsert
        response = self.supabase.table(table_name).upsert(data).execute()

        # Check response and handle
        if 'error' in response:
            print(f"Upsert failed: {response.error_message}")
        else:
            print(f"Successfully upserted {len(data)} rows into {table_name} table.")

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
    
