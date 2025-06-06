import pandas as pd
import os
import json
import warnings

warnings.simplefilter(action='ignore', category=pd.errors.SettingWithCopyWarning)

# Path to the user-uploaded transaction file and fallback file
user_file_path = os.path.join('uploads', 'Transactions.csv')
default_file_path = os.path.join('data', 'Transactions.csv')

mapping_path = os.path.join('output', 'isin_mapping.json')

# Function to process transaction data
def process_transactions(file_path):
    try:
        # Attempt to read the file
        df = pd.read_csv(file_path)

        # Rename based on column index
        df.columns.values[[0, 1, 2, 3, 4, 6, 7, 8, 11, 14]] = [
            'Date', 'Time', 'Product Name DeGiro', 'ISIN', 'Exchange', 'Quantity', 'Price', 'Currency', 'Cost', 'Transaction_costs'
        ]

        # Select and assign the renamed columns
        df_adj = df[['Date', 'Time', 'Product Name DeGiro', 'ISIN', 'Exchange', 'Quantity', 'Price', 'Currency', 'Cost', 'Transaction_costs']]

        # Check if mapping file exists
        if os.path.exists(mapping_path):
            with open(mapping_path, 'r') as f:
                isin_mapping = json.load(f)

            df_adj['Stock'] = df_adj['ISIN'].apply(lambda isin: isin_mapping.get(isin, {}).get("ticker", "")).astype(str)
            df_adj['Product'] = df_adj['ISIN'].apply(lambda isin: isin_mapping.get(isin, {}).get("display_name", "")).astype(str)
        else:
            # If file doesn't exist, set both columns to None
            df_adj['Stock'] = None
            df_adj['Product'] = None

        # Filter out rows where ticker is missing
        #df_adj = df_adj[df_adj['Stock'] != '']

        # Add the Action column based on the Quantity
        df_adj['Action'] = df_adj['Quantity'].apply(lambda x: 'BUY' if x > 0 else 'SELL')
        
        # Convert the Date column to the desired format
        df_adj['Date'] = pd.to_datetime(df_adj['Date'], format='%d-%m-%Y')

        # Convert the Time column to the desired format (HH:MM)
        df_adj['Time'] = pd.to_datetime(df_adj['Time'], format='%H:%M').dt.time
        
        # Fill NA in transaction costs
        df_adj['Transaction_costs'] = df_adj['Transaction_costs'].fillna(0)

        # Set Quantity to int type
        df_adj['Quantity'] = df_adj['Quantity'].fillna(0)
        df_adj['Quantity'] = df_adj['Quantity'].astype(int)
        
        return df_adj
    except Exception as e:
        # Handle any errors during file reading or processing
        print(f"Error processing file {file_path}: {e}")
        return None

# Check if the user-uploaded file exists, otherwise use the default file
if os.path.exists(user_file_path):
    # Process the uploaded file
    transactions = process_transactions(user_file_path)
else:
    print("No transactions file found. Initializing empty DataFrame.")
    transactions = pd.DataFrame(columns=['Date', 'Time', 'Product Name DeGiro', 'ISIN', 'Exchange', 'Quantity', 'Price', 'Currency', 'Cost', 'Transaction_costs'])

# Sort transactions chronologically
try:
    transactions = transactions.sort_values(by=["Date", "Time"]).reset_index(drop=True)
except Exception as e:
    print(f"Error sorting transactions: {e}")
    transactions = pd.DataFrame(columns=['Date', 'Time', 'Product Name DeGiro', 'ISIN', 'Exchange', 'Quantity', 'Price', 'Currency', 'Cost', 'Transaction_costs'])
    pass

# Generate ISIN mapping json

# Ensure required columns are present
required_columns = {'ISIN', 'Product Name DeGiro'}
if not required_columns.issubset(transactions.columns):
    raise ValueError("Required columns 'ISIN' and 'Product Name DeGiro' not found in DataFrame.")

# Load existing mapping if it exists
if os.path.exists(mapping_path):
    with open(mapping_path, 'r') as f:
        existing_mapping = json.load(f)
else:
    existing_mapping = {}

# Add any new ISINs without overwriting existing ones
isin_list = transactions[['ISIN', 'Product Name DeGiro', 'Exchange']].drop_duplicates()
isin_list = isin_list[isin_list['ISIN'].notna() & (isin_list['ISIN'].astype(str).str.strip() != "")]
for isin, name, exchange in isin_list.values:
    if isin not in existing_mapping:
        print(f"Adding new ISIN mapping: {isin} -> {name}")
        existing_mapping[isin] = {
            "ticker": "",
            "degiro_name": name,
            "display_name": name,
            "exchange": exchange,
        }

# Add special "FULL_PORTFOLIO" entry
existing_mapping["FULL_PORTFOLIO"] = {
    "ticker": "FULL",
    "degiro_name": "Full portfolio",
    "display_name": "Full portfolio",
    "exchange": ""
}

# Save the updated mapping
with open(mapping_path, 'w') as f:
    json.dump(existing_mapping, f, indent=4)