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
        
        # Select and rename the columns
        df_adj = df[['Datum', 'Tijd', 'ISIN', 'Beurs', 'Aantal', 'Koers', 'Waarde', 'Transactiekosten en/of']].rename(columns={
            'Datum': 'Date',
            'Tijd': 'Time',
            'ISIN': 'ISIN',
            'Beurs': 'Exchange',
            'Aantal': 'Quantity',
            'Koers': 'Price',
            'Waarde': 'Cost',
            'Transactiekosten en/of': 'Transaction_costs'
        })
        
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
else:
    print(f'Processing fallback: {default_file_path}')
    # If the file is not uploaded, use the default file
    transactions = process_transactions(default_file_path)
