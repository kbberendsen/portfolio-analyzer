import os
from datetime import datetime, timedelta
import pandas as pd
from helpers.transactions import transactions as transactions_import
import json
import warnings

warnings.simplefilter(action='ignore', category=pd.errors.SettingWithCopyWarning)

def calc_portfolio(analyzer, start_date):
    if transactions_import.empty:
        print("No transactions found. Skipping portfolio calculation.")
        return
    
    print('Retrieving portfolio data...')
    
    # Fix data types and definitions
    transactions = transactions_import[transactions_import["Stock"].notna() & (transactions_import["Stock"] != '')]
    transactions["Date"] = pd.to_datetime(transactions["Date"])
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    today = datetime.today()
    end_dates = pd.date_range(start=start_date, end=today, freq='D')[1:]  # Exclude the start_date itself

    # Initialize an empty list to store portfolio data for each day
    portfolio_results_list = []

    # Get recent stock price data for new end_dates
    stock_list = transactions["Stock"].unique().tolist() # All stocks

    yf_start_date = start_date if len(end_dates) > 30 else (today - timedelta(days=30))
    yf_stock_price_data = analyzer.get_price_at_date(stock_list, yf_start_date.strftime('%Y-%m-%d'), (today + timedelta(days=1)).strftime('%Y-%m-%d'))
  
    # Update stock prices to EUR
    # Remove duplicates and create ticker-to-currency dict
    ticker_currency_dict = transactions.drop_duplicates(subset=['Stock', 'Currency'])\
                                    .set_index('Stock')['Currency'].to_dict()

    # Group tickers by currency (excluding EUR)
    currency_ticker_map = {}
    for ticker, currency in ticker_currency_dict.items():
        if currency != 'EUR':
            currency_ticker_map.setdefault(currency, []).append(ticker)

    # Fetch FX rates once per currency
    fx_rates_by_currency = {}
    for currency in currency_ticker_map:
        fx_rates_by_currency[currency] = analyzer.get_fx_rate(
            currency, 'EUR',
            yf_start_date.strftime('%Y-%m-%d'),
            (today + timedelta(days=1)).strftime('%Y-%m-%d')
        )

    # Apply FX rates to stock prices
    for currency, tickers in currency_ticker_map.items():
        fx_rate = fx_rates_by_currency.get(currency)
        if fx_rate is None:
            continue
        for ticker in tickers:
            prices = yf_stock_price_data.get(ticker, {})
            for date, price in prices.items():
                prices[date] = price * fx_rate.get(date, 1)
    
    # Load existing results from Parquet file
    try:
        portfolio_results_df = pd.read_parquet('output/portfolio_performance_daily.parquet')
        print('Loaded portfolio_performance_daily from Parquet')

        # Remove last 2 days to force refresh (get end of day data)
        last_2_days = sorted(portfolio_results_df['end_date'].unique())[-2:]
        portfolio_results_df = portfolio_results_df[~portfolio_results_df['end_date'].isin(last_2_days)]

    except Exception as e:
        print(f'Failed to load portfolio_performance_daily from Parquet: {e}')
        portfolio_results_df = pd.DataFrame(columns=['product', 'ticker', 'quantity', 'start_date', 'end_date', 
                                                        'avg_cost', 'total_cost', 'transaction_costs', 'current_value', 
                                                        'current_money_weighted_return', 'realized_return', 
                                                        'net_return', 'current_performance_percentage', 
                                                        'net_performance_percentage'])
    
    # Load stock prices from Parquet file
    try:
        stock_prices_df = pd.read_parquet('output/stock_prices.parquet')
        stock_prices_df = stock_prices_df.dropna(subset=['price'])
        stock_prices_dict = stock_prices_df.groupby('ticker').apply(lambda x: x.set_index('date')['price'].to_dict()).to_dict()
        print('Loaded stock_prices from Parquet')
    except Exception as e:
        print(f'Failed to load stock_prices from Parquet: {e}')
        stock_prices_dict = {}


    # Append fresh stock price data to stock_prices_dict
    for ticker, prices in yf_stock_price_data.items():
        if ticker in stock_prices_dict:
            stock_prices_dict[ticker].update(prices)
        else:
            stock_prices_dict[ticker] = prices

    # Remove duplicates from stock_prices_dict
    for ticker in stock_prices_dict:
        stock_prices_dict[ticker] = {date: price for date, price in sorted(stock_prices_dict[ticker].items())}

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
                stock_prices=stock_prices_dict
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

    # Save the updated DataFrame to a Parquet file
    portfolio_results_df = portfolio_results_df.dropna()
    portfolio_results_df['quantity'] = portfolio_results_df['quantity'].astype(int)

    # Update product column based on ISIN mapping json
    with open('output/isin_mapping.json', 'r') as f:
        isin_mapping = json.load(f)

    # Build a reverse map: ticker -> display_name
    ticker_to_name = {
        data.get("ticker"): data.get("display_name", "")
        for data in isin_mapping.values()
        if "ticker" in data
    }

    portfolio_results_df['product'] = portfolio_results_df['ticker'].map(ticker_to_name).fillna('')

    # Store parquet files
    # Daily table
    portfolio_results_df.to_parquet(os.path.join('output', 'portfolio_performance_daily.parquet'), index=False)

    # Stock prices
    stock_prices_records = []
    for ticker, date_prices in stock_prices_dict.items():
        currency = ticker_currency_dict.get(ticker, 'EUR')  # Default EUR if missing
        fx_rate_data = fx_rates_by_currency.get(currency, {}) if currency != 'EUR' else {}

        currency_pair = f"{currency}-EUR" if currency != 'EUR' else "EUR-EUR"

        for date, price in date_prices.items():
            # FX rate for the date if not EUR, else 1
            fx_rate = fx_rate_data.get(date, 1) if currency != 'EUR' else 1

            stock_prices_records.append({
                "ticker": ticker,
                "date": date,
                "price": price if price is not None else 0,
                "fx_rate": fx_rate,
                "currency_pair": currency_pair
            })

    stock_prices_df = pd.DataFrame(stock_prices_records)
    stock_prices_df = stock_prices_df.dropna(subset=['price'])
    stock_prices_df.to_parquet(os.path.join('output', 'stock_prices.parquet'), index=False)

    print('Daily output saved locally')

    # Extract monthly data from the daily data
    monthly_results = portfolio_results_df.copy()
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

    # Convert 'end_date' to string in 'YYYY-MM-DD' format
    monthly_results_df['end_date'] = monthly_results_df['end_date'].dt.strftime('%Y-%m-%d')

    # Save the updated DataFrame to a Parquet file
    monthly_results_df.to_parquet(os.path.join('output', 'portfolio_performance_monthly.parquet'), index=False)
    print('Monthly output saved locally')