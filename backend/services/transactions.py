import pandas as pd
import os
import json
import warnings
import traceback
import re
from backend.utils.logger import app_logger

warnings.simplefilter(action='ignore', category=pd.errors.SettingWithCopyWarning)

# File Paths
TRANSACTION_FILE = 'uploads/Transactions.csv'
MAPPING_FILE = 'output/isin_mapping.json'

def detect_decimal_separator(file_path: str) -> str:
    """
    Detects whether ',' or '.' is the decimal separator in the given CSV file.
    Looks at the first 20 lines of data.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i > 5:  # only check first 5 lines
                break
            # Skip header
            if i == 0:
                continue
            # Look for quoted numeric values -> European style
            if re.search(r'"\d+,\d+"', line):
                return ","
            # Look for dot decimals -> US style
            if re.search(r'\d+\.\d+', line):
                return "."
    # Default fallback
    return "."

def update_isin_mapping_json(df: pd.DataFrame):
    """
    Reads the transactions df, finds new ISINs, and updates the mapping JSON file.
    """
    # Ensure required columns for mapping exist
    required_cols = {'ISIN', 'Product_Name_DeGiro', 'Exchange'}
    if not required_cols.issubset(df.columns):
        app_logger.warning("[ISIN-MAPPING] Columns required for ISIN mapping are missing. Skipping update.")
        return

    # Load existing mapping or initialize an empty one
    existing_mapping = {}
    if os.path.exists(MAPPING_FILE):
        with open(MAPPING_FILE, 'r') as f:
            existing_mapping = json.load(f)

    def is_valid_isin(isin: str) -> bool:
        return isinstance(isin, str) and re.fullmatch(r"[A-Z]{2}[A-Z0-9]{10}", isin) is not None
    
    # Find unique ISINs from the transaction data
    isin_list = df[['ISIN', 'Product_Name_DeGiro', 'Exchange']].drop_duplicates()
    isin_list = isin_list[isin_list['ISIN'].notna() & (isin_list['ISIN'].astype(str).str.strip() != "")]
    isin_list = isin_list[isin_list['ISIN'].apply(is_valid_isin)]

    # Add new ISINs to the mapping without overwriting existing entries
    for isin, name, exchange in isin_list.values:
        if isin not in existing_mapping:
            app_logger.info(f"[ISIN-MAPPING] Adding new ISIN mapping: {isin} -> {name}")
            existing_mapping[isin] = {
                "ticker": "",
                "degiro_name": name,
                "display_name": name,
                "exchange": exchange,
                "product_type": "",
            }
    
    # Ensure the special "FULL_PORTFOLIO" entry exists
    if "FULL_PORTFOLIO" not in existing_mapping:
         existing_mapping["FULL_PORTFOLIO"] = {
            "ticker": "FULL", "degiro_name": "Full portfolio", 
            "display_name": "Full portfolio", "exchange": "", "product_type": ""
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
        app_logger.warning(f"[TRANSACTIONS] Transaction file not found at {TRANSACTION_FILE}")
        return pd.DataFrame()
    
    try:
        decimal_sep = detect_decimal_separator(TRANSACTION_FILE)
        thousands_sep = "." if decimal_sep == "," else None

        df = pd.read_csv(
            TRANSACTION_FILE,
            delimiter=",",
            decimal=decimal_sep,
            thousands=thousands_sep,
            dtype={6: str}
        )

        # Define the column names, index-based renaming
        column_names = {
            0: 'Date', 1: 'Time', 2: 'Product_Name_DeGiro', 3: 'ISIN', 
            4: 'Exchange', 6: 'Quantity', 7: 'Price', 8: 'Currency', 
            11: 'Cost', 14: 'Transaction_costs'
        }
        # Select and rename columns safely using explicit integer indices
        column_indices = [int(i) for i in column_names.keys()]
        df = df.iloc[:, column_indices]
        df.columns = list(column_names.values())
        
        # First, update the ISIN mapping file based on the raw transactions
        try:
            app_logger.info("[ISIN-MAPPING] Updating ISIN mapping from transaction data...")
            isin_mapping = update_isin_mapping_json(df)
            app_logger.info("[ISIN-MAPPING] ISIN mapping updated successfully.")
        except Exception as e:
            app_logger.error(f"[ISIN-MAPPING] Error updating ISIN mapping: {e}", exc_info=True)
            isin_mapping = {}

        # Apply the mapping to the DataFrame
        if isin_mapping:
            df['Stock'] = df['ISIN'].apply(lambda isin: isin_mapping.get(isin, {}).get("ticker", "")).astype(str)
            df['Product'] = df['ISIN'].apply(lambda isin: isin_mapping.get(isin, {}).get("display_name", "")).astype(str)
        else:
            df['Stock'] = ''
            df['Product'] = ''

        # Data cleaning
        df['Quantity'] = (
            df['Quantity']
                .astype(str)
                .str.extract(r'^(-?\d+)', expand=False)  # <- allow optional '-'
                .fillna(0)
                .astype(int)
        )
        df['Action'] = df['Quantity'].apply(lambda x: 'BUY' if x > 0 else 'SELL')
        df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y', errors='coerce').dt.date
        df['Time'] = pd.to_datetime(df['Time'], format='%H:%M', errors='coerce').dt.time

        df['Price'] = df['Price'].fillna(0).astype(float)
        df['Cost'] = df['Cost'].fillna(0).astype(float)
        df['Transaction_costs'] = df['Transaction_costs'].fillna(0).astype(float)
        
        df = df.dropna()
        # Sort transactions chronologically and return
        return df.sort_values(by=["Date", "Time"]).reset_index(drop=True)

    except Exception as e:
        app_logger.error(f"[TRANSACTIONS] Error loading or processing transaction data: {e}", exc_info=True)
        return pd.DataFrame()

def get_transactions() -> pd.DataFrame:
    """
    Returns a copy of the cleaned transactions DataFrame.
    Ensures consumers can't modify the original data.
    """
    try:
        app_logger.info("[TRANSACTIONS] Processing transactions...")
        
        transactions_df = load_and_prepare_data()
        app_logger.info("[TRANSACTIONS] Transactions processed successfully.")

    except Exception as e:
        app_logger.error(f"[TRANSACTIONS] Error during transactions processing: {e}", exc_info=True)
        raise e
    
    return transactions_df.copy()