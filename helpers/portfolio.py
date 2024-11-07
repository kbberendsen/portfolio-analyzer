import os
from datetime import datetime, date, timedelta
import pandas as pd
from helpers.transactions import transactions

def calc_monthly(analyzer, start_date='2020-10-01'):
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

    # Loop over each end date, calculate portfolio results, and add to the list
    for end_date in end_dates:
        # Format end date to string for comparison
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # Check if the result for this end date already exists in the DataFrame
        if not portfolio_results_df[portfolio_results_df['end_date'] == end_date_str].empty:
            continue  # Skip if already present

        print(f'Retrieving data for: {end_date_str}')
        
        transactions_before_end = transactions[(transactions["Date"] <= end_date_str)]
        stock_list = list(transactions_before_end["Stock"].unique())
        
        result = analyzer.calculate_all_stocks_mwr(
            start_date=start_date.strftime('%Y-%m-%d'), 
            end_date=end_date_str, 
            stocks=stock_list
        )
        
        for key in result:
            portfolio_data = result.get(key)
            
            # Ensure end_date is included in the portfolio_data
            portfolio_data['end_date'] = end_date_str
            
            # Append the new data to the list
            portfolio_results_list.append(portfolio_data)

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
    # Set fixed start date
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    # Initialize today's date as the end of the loop range
    today = datetime.today()

    # Generate list of end dates for the first day of each month from start date to today
    end_dates = pd.date_range(start=start_date, end=today, freq='D')[1:]  # Exclude the start_date itself

    # Initialize an empty list to store portfolio data for each month
    portfolio_results_list = []

    # Define the path to the cache file
    cache_file_path = os.path.join('data', 'portfolio_results_daily.pkl')

    # Load existing results from the pickle file if it exists
    try:
        portfolio_results_df = pd.read_pickle(cache_file_path)
        print('Daily file found')
    except (FileNotFoundError, pd.errors.EmptyDataError):
        # Start with an empty DataFrame if the file doesn't exist
        portfolio_results_df = pd.DataFrame(columns=['product', 'ticker', 'quantity', 'start_date', 'end_date', 
                                                    'avg_cost', 'total_cost', 'current_value', 
                                                    'current_money_weighted_return', 'realized_return', 
                                                    'net_return', 'current_performance_percentage', 
                                                    'net_performance_percentage'])

    # Loop over each end date, calculate portfolio results, and add to the list
    for end_date in end_dates:
        # Format end date to string for comparison
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # Check if the result for this end date already exists in the DataFrame
        if not portfolio_results_df[portfolio_results_df['end_date'] == end_date_str].empty:
            continue  # Skip if already present

        print(f'Retrieving data for: {end_date_str}')

        # Ensure that the transactions before the end date are not empty
        transactions_before_end = transactions[(transactions["Date"] <= end_date_str)]
        if transactions_before_end.empty:
            print(f"No transactions found for date: {end_date_str}. Skipping...")
            continue

        stock_list = list(transactions_before_end["Stock"].unique())
        
        result = analyzer.calculate_all_stocks_mwr(
            start_date=start_date.strftime('%Y-%m-%d'), 
            end_date=end_date_str, 
            stocks=stock_list
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

    # Combine the list into a DataFrame if there are new results
    if portfolio_results_list:
        new_portfolio_results_df = pd.DataFrame(portfolio_results_list)
        # Append new results to the existing DataFrame
        portfolio_results_df = pd.concat([portfolio_results_df, new_portfolio_results_df], ignore_index=True)

    # Save the updated DataFrame to a pickle file and csv
    portfolio_results_df.to_pickle(cache_file_path)
    portfolio_results_df.to_csv(os.path.join('output', 'portfolio_daily.csv'), index=False)

    print('Daily output saved')
