import os
from datetime import datetime, date, timedelta
import pandas as pd
from helpers.transactions import transactions
import time

def calc_portfolio(analyzer, db, start_date):
    print('Retrieving portfolio data...')
    
    # Fix data types and definitions
    transactions["Date"] = pd.to_datetime(transactions["Date"])
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    today = datetime.today()
    end_dates = pd.date_range(start=start_date, end=today, freq='D')[1:]  # Exclude the start_date itself

    # Initialize an empty list to store portfolio data for each day
    portfolio_results_list = []

    # Load existing results from Supabase
    try:
        db_portfolio_results_df = db.fetch_all_df('portfolio_performance_daily')
        print('Loaded portfolio_performance_daily from Supabase')

        # Remove last 2 days to force refresh (get end of day data)
        last_2_days = sorted(db_portfolio_results_df['end_date'].unique())[-2:]
        db_portfolio_results_df = db_portfolio_results_df[~db_portfolio_results_df['end_date'].isin(last_2_days)]

    except Exception as e:
        print(f'Failed to load portfolio_performance_daily from Supabase: {e}')
        db_portfolio_results_df = pd.DataFrame(columns=['product', 'ticker', 'quantity', 'start_date', 'end_date', 
                                                        'avg_cost', 'total_cost', 'current_value', 
                                                        'current_money_weighted_return', 'realized_return', 
                                                        'net_return', 'current_performance_percentage', 
                                                        'net_performance_percentage'])

    # Get recent stock price data for new end_dates
    stock_list = transactions["Stock"].unique().tolist() # All stocks(today - timedelta(days=60))
    yf_stock_price_data = analyzer.get_price_at_date(stock_list, start_date.strftime('%Y-%m-%d'), (today + timedelta(days=1)).strftime('%Y-%m-%d'))
    try:
        db.store_stock_prices(yf_stock_price_data)
    except Exception as e:
        print(f'Failed to store stock prices in Supabase: {e}')
    
    # Load Supabase tables as cache
    try:
        db_stock_prices_df = db.fetch_all_df('stock_prices')
        db_stock_prices_df = db_stock_prices_df.dropna(subset=['price'])
        db_stock_prices_dict = db_stock_prices_df.groupby('ticker').apply(lambda x: x.set_index('date')['price'].to_dict()).to_dict()
        print('Loaded stock_prices from Supabase')
    except Exception as e:
        print(f'Failed to load stock_prices from Supabase: {e}')


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
            if not db_portfolio_results_df[db_portfolio_results_df['end_date'] == end_date_str].empty:
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
                stock_prices=db_stock_prices_dict
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
        db_portfolio_results_df = pd.concat([db_portfolio_results_df, new_portfolio_results_df], ignore_index=True)

    # Save the updated DataFrame to a csv
    db_portfolio_results_df.to_csv(os.path.join('output', 'portfolio_daily.csv'), index=False)

    print('Daily output saved locally')

    # Extract monthly data from the daily data
    monthly_results = db_portfolio_results_df.copy()
    monthly_results['end_date'] = pd.to_datetime(monthly_results['end_date'])

    # Set index and sort values to ensure correct selection
    monthly_results = monthly_results.sort_values(['ticker', 'end_date'])

    # Resample first-of-month data per ticker
    monthly_results_df = (
        monthly_results.set_index('end_date')
        .groupby('ticker')
        .resample('MS')
        .first()
        .reset_index(level=0, drop=True)
        .reset_index()
    )

    # Save the updated DataFrame to a csv
    monthly_results_df.to_csv(os.path.join('output', 'portfolio_monthly.csv'), index=False)
    print('Monthly output saved locally')

    # Upsert to Supabase with retry mechanism
    db.upsert_to_supabase(db_portfolio_results_df, 'portfolio_performance_daily', ['ticker', 'end_date'])