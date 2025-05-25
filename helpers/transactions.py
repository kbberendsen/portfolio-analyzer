import pandas as pd
import os
from helpers.ticker_mapping import ticker_to_name, isin_to_ticker

# Path to the user-uploaded transaction file and fallback file
user_file_path = os.path.join('uploads', 'Transactions.csv')
default_file_path = os.path.join('data', 'Transactions.csv')

# Function to process transaction data
def process_transactions(file_path):
    try:
        # Attempt to read the file
        df = pd.read_csv(file_path)

        # Rename based on column index
        df.columns.values[[0, 1, 3, 4, 6, 7, 11, 14]] = [
            'Date', 'Time', 'ISIN', 'Exchange', 'Quantity', 'Price', 'Cost', 'Transaction_costs'
        ]

        # Select and assign the renamed columns
        df_adj = df[['Date', 'Time', 'ISIN', 'Exchange', 'Quantity', 'Price', 'Cost', 'Transaction_costs']]

        # Select and rename the columns
        # df_adj = df[['Datum', 'Tijd', 'ISIN', 'Beurs', 'Aantal', 'Koers', 'Waarde', 'Transactiekosten en/of']].rename(columns={
        #     'Datum': 'Date',
        #     'Tijd': 'Time',
        #     'ISIN': 'ISIN',
        #     'Beurs': 'Exchange',
        #     'Aantal': 'Quantity',
        #     'Koers': 'Price',
        #     'Waarde': 'Cost',
        #     'Transactiekosten en/of': 'Transaction_costs'
        # })
        
        # Map the ISIN values to the new Ticker column
        df_adj['Stock'] = df_adj['ISIN'].map(isin_to_ticker).astype(str)
        
        # Filter out rows where ISIN cannot be mapped
        df_adj = df_adj[df_adj['Stock'] != 'nan']
        
        # Map the ISIN values to the new Product_name column
        df_adj['Product'] = df_adj['Stock'].map(ticker_to_name).astype(str)
        
        # Add the Action column based on the Quantity
        df_adj['Action'] = df_adj['Quantity'].apply(lambda x: 'BUY' if x > 0 else 'SELL')
        
        # Convert the Date column to the desired format
        df_adj['Date'] = pd.to_datetime(df_adj['Date'], format='%d-%m-%Y')

        # Convert the Time column to the desired format (HH:MM)
        df_adj['Time'] = pd.to_datetime(df_adj['Time'], format='%H:%M').dt.time
        
        # Fill NA in transaction costs
        df_adj['Transaction_costs'] = df_adj['Transaction_costs'].fillna(0)

        # Set Quantity to int type
        df_adj["Quantity"] = df_adj["Quantity"].astype(int)
        
        return df_adj
    except Exception as e:
        # Handle any errors during file reading or processing
        print(f"Error processing file {file_path}: {e}")
        return None

# Check if the user-uploaded file exists, otherwise use the default file
if os.path.exists(user_file_path):
    # Process the uploaded file
    transactions = process_transactions(user_file_path)
    if transactions is None:
        # Fall back to the default file in case of error
        transactions = process_transactions(default_file_path)
elif os.path.exists(default_file_path):
    print(f'Processing fallback: {default_file_path}')
    # If the file is not uploaded, use the default file
    transactions = process_transactions(default_file_path)
else:
    print("No transactions file found. Initializing empty DataFrame.")
    transactions = pd.DataFrame(columns=["Date", "Time", "ISIN", "Exchange", "Quantity", "Price", "Cost", "Transaction_costs"])

# Sort transactions chronologically
transactions = transactions.sort_values(by=["Date", "Time"]).reset_index(drop=True)
