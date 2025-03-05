import os
from datetime import datetime, date, timedelta
import pandas as pd
from helpers.transactions import transactions
import time

def calc_monthly(analyzer, start_date='2020-10-01'):
    print('Retrieving monthly data...')

    # Set fixed start date
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    # Initialize today's date as the end of the loop range
    today = datetime.today()

    # Generate list of end dates for the first day of each month from start date to today
    end_dates = pd.date_range(start=start_date, end=today, freq='MS')[1:]  # Exclude the start_date itself

    # Initialize an empty list to store portfolio data for each month
    portfolio_results_list = []
    portfolio_results_df = None

    # Define the path to the cache file
    cache_file_path = os.path.join('data', 'portfolio_results_monthly.pkl')

    # Load existing results from the pickle file if it exists
    try:
        portfolio_results_df = pd.read_pickle(cache_file_path)
        print('Monthly file found')
    except (FileNotFoundError, pd.errors.EmptyDataError):
        # Start with an empty DataFrame if the file doesn't exist
        portfolio_results_df = pd.DataFrame(columns=['product', 'ticker', 'quantity', 'start_date', 'end_date', 'avg_cost', 
                                                    'total_cost', 'current_value', 'current_money_weighted_return', 
                                                    'realized_return', 'net_return', 'current_performance_percentage', 
                                                    'net_performance_percentage'])
        
        
    transactions["Date"] = pd.to_datetime(transactions["Date"])
    stock_list = list(transactions["Stock"].unique())

    # Get the first day of the current month
    first_day_current_month = pd.to_datetime(today).replace(day=1)
    first_day_current_month = first_day_current_month.strftime('%Y-%m-%d')

    # Check if the first day of the current month already exists in portfolio data
    if first_day_current_month in portfolio_results_df['end_date'].unique():
        print(f"Data for {first_day_current_month} already exists. Skipping stock price retrieval.")
    else:
        # Get stock price data for new end_dates
        stock_price_data = analyzer.get_price_at_date(stock_list, start_date.strftime('%Y-%m-%d'), (today + timedelta(days=1)).strftime('%Y-%m-%d'))

        # Loop over each end date, calculate portfolio results, and add to the list
        for end_date in end_dates:
            try:
                # Format end date to string for comparison
                end_date_str = end_date.strftime('%Y-%m-%d')

                # Check if the result for this end date already exists in the DataFrame
                if not portfolio_results_df[portfolio_results_df['end_date'] == end_date_str].empty:
                    continue  # Skip if already present

                print(f'Retrieving data for: {end_date_str}')
                
                transactions_before_end = transactions[transactions["Date"].apply(lambda x: x.strftime('%Y-%m-%d') if isinstance(x, datetime) else x) <= end_date_str]
                
                stock_list = list(transactions_before_end["Stock"].unique())

                # Retrieve stock results using analyzer class
                result = analyzer.calculate_all_stocks_mwr(
                    start_date=start_date.strftime('%Y-%m-%d'), 
                    end_date=end_date_str, 
                    stocks=stock_list,
                    stock_prices=stock_price_data
                )
                
                for key in result:
                    portfolio_data = result.get(key)
                    
                    # Ensure end_date is included in the portfolio_data
                    portfolio_data['end_date'] = end_date_str
                    
                    # Append the new data to the list
                    portfolio_results_list.append(portfolio_data)

            except Exception as e:
                print(f'Failed to retrieve monthly data for {end_date}: {e}')
                continue

    # Combine the list into a DataFrame if there are new results
    if portfolio_results_list:
        new_portfolio_results_df = pd.DataFrame(portfolio_results_list)
        # Append new results to the existing DataFrame
        portfolio_results_df = pd.concat([portfolio_results_df, new_portfolio_results_df], ignore_index=True)

    # Save the updated DataFrame to a pickle file and csv
    portfolio_results_df.to_pickle(cache_file_path)
    portfolio_results_df.to_csv(os.path.join('output', 'portfolio_monthly.csv'), index=False)

    print('Monthly output saved')

def calc_daily(analyzer, start_date):
    print('Retrieving daily data...')

    # Set fixed start date
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    # Initialize today's date as the end of the loop range
    today = datetime.today()

    # Generate list of daily end dates from start date to today
    end_dates = pd.date_range(start=start_date, end=today, freq='D')[1:]  # Exclude the start_date itself

    # Initialize an empty list to store portfolio data for each month
    portfolio_results_list = []

    # Define the path to the cache file
    cache_file_path = os.path.join('data', 'portfolio_results_daily.pkl')

    # Load existing results from the pickle file if it exists
    try:
        portfolio_results_df = pd.read_pickle(cache_file_path)
        print('Daily file found')

        # Remove last 2 days to force refresh (get end of day data)
        last_2_days = sorted(portfolio_results_df['end_date'].unique())[-2:]
        portfolio_results_df = portfolio_results_df[~portfolio_results_df['end_date'].isin(last_2_days)]

    except (FileNotFoundError, pd.errors.EmptyDataError):
        # Start with an empty DataFrame if the file doesn't exist
        portfolio_results_df = pd.DataFrame(columns=['product', 'ticker', 'quantity', 'start_date', 'end_date', 
                                                    'avg_cost', 'total_cost', 'current_value', 
                                                    'current_money_weighted_return', 'realized_return', 
                                                    'net_return', 'current_performance_percentage', 
                                                    'net_performance_percentage'])
        
    transactions["Date"] = pd.to_datetime(transactions["Date"])

    # Get stock price data for new end_dates
    stock_list = transactions["Stock"].unique().tolist() # All stocks
    stock_price_data = analyzer.get_price_at_date(stock_list, start_date.strftime('%Y-%m-%d'), (today + timedelta(days=1)).strftime('%Y-%m-%d'))

    # Loop over each end date, calculate portfolio results, and add to the list
    for end_date in end_dates:
        # Try to get end_date data, else continue
        try:
            # Format end date to string for comparison
            end_date_str = end_date.strftime('%Y-%m-%d')

            # Skip weekends (Saturday and Sunday)
            if end_date.weekday() >= 5:
                continue  # Skip this iteration if it's a weekend
            
            # Check if the result for this end date already exists in the DataFrame
            if not portfolio_results_df[portfolio_results_df['end_date'] == end_date_str].empty:
                continue  # Skip if already present

            print(f'Retrieving data for: {end_date_str}')

            # Ensure that the transactions before the end date are not empty
            transactions_before_end = transactions[transactions["Date"].apply(lambda x: x.strftime('%Y-%m-%d') if isinstance(x, datetime) else x) <= end_date_str]

            if transactions_before_end.empty:
                print(f"No transactions found for date: {end_date_str}. Skipping...")
                continue

            stock_list = list(transactions_before_end["Stock"].unique())
            
            # Retrieve stock results using analyzer class
            result = analyzer.calculate_all_stocks_mwr(
                start_date=start_date.strftime('%Y-%m-%d'), 
                end_date=end_date_str, 
                stocks=stock_list,
                stock_prices=stock_price_data
            )
            
            for key in result:
                portfolio_data = result.get(key)
                
                # Check if portfolio_data is valid before proceeding
                if portfolio_data is None or not isinstance(portfolio_data, dict):
                    print(f"Stock data is missing or invalid for date: {end_date_str}. Result: {result}")
                    continue
                
                # Ensure end_date is included in the portfolio_data
                portfolio_data['end_date'] = end_date_str
                
                # Append the new data to the list
                portfolio_results_list.append(portfolio_data)

        except Exception as e:
            print(f'Failed to retrieve daily data for {end_date}: {e}')
            continue

    # Combine the list into a DataFrame if there are new results
    if portfolio_results_list:
        new_portfolio_results_df = pd.DataFrame(portfolio_results_list)
        # Append new results to the existing DataFrame
        portfolio_results_df = pd.concat([portfolio_results_df, new_portfolio_results_df], ignore_index=True)

    # Save the updated DataFrame to a pickle file and csv
    portfolio_results_df.to_pickle(cache_file_path)
    portfolio_results_df.to_csv(os.path.join('output', 'portfolio_daily.csv'), index=False)

    # Upsert to Supabase
    analyzer.upsert_to_supabase(portfolio_results_df, 'portfolio_performance_daily', ['ticker', 'end_date'])

    print('Daily output saved')
