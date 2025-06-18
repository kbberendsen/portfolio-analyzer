import pandas as pd
import os
import json
import warnings
import traceback
from backend.utils.logger import app_logger

warnings.simplefilter(action='ignore', category=pd.errors.SettingWithCopyWarning)

# File Paths
TRANSACTION_FILE = 'uploads/Transactions.csv'
MAPPING_FILE = 'output/isin_mapping.json'

def update_isin_mapping_json(df: pd.DataFrame):
    """
    Reads the transactions df, finds new ISINs, and updates the mapping JSON file.
    """
    # Ensure required columns for mapping exist
    required_cols = {'ISIN', 'Product_Name_DeGiro', 'Exchange'}
    if not required_cols.issubset(df.columns):
        app_logger.warning("Columns required for ISIN mapping are missing. Skipping update.")
        return

    # Load existing mapping or initialize an empty one
    existing_mapping = {}
    if os.path.exists(MAPPING_FILE):
        with open(MAPPING_FILE, 'r') as f:
            existing_mapping = json.load(f)
    
    # Find unique ISINs from the transaction data
    isin_list = df[['ISIN', 'Product_Name_DeGiro', 'Exchange']].drop_duplicates()
    isin_list = isin_list[isin_list['ISIN'].notna() & (isin_list['ISIN'].astype(str).str.strip() != "")]

    # Add new ISINs to the mapping without overwriting existing entries
    for isin, name, exchange in isin_list.values:
        if isin not in existing_mapping:
            app_logger.info(f"Adding new ISIN mapping: {isin} -> {name}")
            existing_mapping[isin] = {
                "ticker": "",
                "degiro_name": name,
                "display_name": name,
                "exchange": exchange,
            }
    
    # Ensure the special "FULL_PORTFOLIO" entry exists
    if "FULL_PORTFOLIO" not in existing_mapping:
         existing_mapping["FULL_PORTFOLIO"] = {
            "ticker": "FULL", "degiro_name": "Full portfolio", 
            "display_name": "Full portfolio", "exchange": ""
         }

    # Save the updated mapping back to the JSON file
    with open(MAPPING_FILE, 'w') as f:
        json.dump(existing_mapping, f, indent=4)
    
    return existing_mapping

def load_and_prepare_data() -> pd.DataFrame:
    """
    Loads transactions from CSV, updates mappings, and cleans the data.
    This incorporates the logic from the old `process_transactions` function.
    """
    if not os.path.exists(TRANSACTION_FILE):
        app_logger.warning(f"Transaction file not found at {TRANSACTION_FILE}")
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(TRANSACTION_FILE)

        # Define the column names based on the old script's index-based renaming
        column_names = {
            0: 'Date', 1: 'Time', 2: 'Product_Name_DeGiro', 3: 'ISIN', 
            4: 'Exchange', 6: 'Quantity', 7: 'Price', 8: 'Currency', 
            11: 'Cost', 14: 'Transaction_Costs'
        }
        # Select and rename columns safely using explicit integer indices
        column_indices = [int(i) for i in column_names.keys()]
        df = df.iloc[:, column_indices]
        df.columns = list(column_names.values())
        
        # First, update the ISIN mapping file based on the raw transactions
        try:
            app_logger.info("Updating ISIN mapping from transaction data...")
            isin_mapping = update_isin_mapping_json(df)
            app_logger.info("ISIN mapping updated successfully.")
        except Exception as e:
            app_logger.error(f"Error updating ISIN mapping: {e}", exc_info=True)
            isin_mapping = {}

        # Apply the mapping to the DataFrame
        if isin_mapping:
            df['Stock'] = df['ISIN'].apply(lambda isin: isin_mapping.get(isin, {}).get("ticker", "")).astype(str)
            df['Product'] = df['ISIN'].apply(lambda isin: isin_mapping.get(isin, {}).get("display_name", "")).astype(str)
        else:
            df['Stock'] = ''
            df['Product'] = ''

        # Data cleaning
        df['Action'] = df['Quantity'].apply(lambda x: 'BUY' if x > 0 else 'SELL')
        df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y')
        df['Time'] = pd.to_datetime(df['Time'], format='%H:%M').dt.time
   
        df['Quantity'] = df['Quantity'].fillna(0).astype(float)
        df['Price'] = df['Price'].fillna(0).astype(float)
        df['Cost'] = df['Cost'].fillna(0).astype(float)
        df['Transaction_Costs'] = df['Transaction_Costs'].fillna(0).astype(float)
        
        df = df.dropna()
        # Sort transactions chronologically and return
        return df.sort_values(by=["Date", "Time"]).reset_index(drop=True)

    except Exception as e:
        app_logger.error(f"Error loading or processing transaction data: {e}", exc_info=True)
        return pd.DataFrame()

def get_transactions() -> pd.DataFrame:
    """
    Returns a copy of the cleaned transactions DataFrame.
    Ensures consumers can't modify the original data.
    """
    try:
        app_logger.info("Processing transactions...")
        
        transactions_df = load_and_prepare_data()
        app_logger.info("Transactions processed successfully.")

    except Exception as e:
        app_logger.error(f"Error during transactions processing: {e}", exc_info=True)
        raise e
    
    return transactions_df.copy()