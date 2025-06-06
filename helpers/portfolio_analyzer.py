import pandas as pd
import yfinance as yf
from datetime import datetime, date
import json
import warnings

warnings.simplefilter(action='ignore', category=pd.errors.SettingWithCopyWarning)

class PortfolioAnalyzer:
    def __init__(self, transactions):
        """Initialize with transaction data (pandas DataFrame)."""
        self.transactions = transactions

    def get_price_at_date(self, tickers, start, end):
        # Convert string dates to datetime
        start = datetime.strptime(start, '%Y-%m-%d')
        end = datetime.strptime(end, '%Y-%m-%d')

        # Download stock data
        stock_data = yf.download(tickers, start=start, end=end, interval="1d")["Close"]

        # Convert timestamps to date strings
        if isinstance(stock_data, pd.Series):  # Single stock case
            stock_prices_str = {date.strftime('%Y-%m-%d'): price for date, price in stock_data.items()}
        else:  # Multiple stocks case
            stock_prices_str = {
                stock: {date.strftime('%Y-%m-%d'): price for date, price in prices.items()}
                for stock, prices in stock_data.to_dict().items()
            }

        return stock_prices_str

    def get_first_last_open_day(self, start_date, end_date, stock_price_data, first=True):
        """Fetches the first or last open market day within a given date range using stock_price_data."""

        # Filter stock_price_data for the given date range
        stock_prices = stock_price_data

        filtered_dates = [date for date in stock_prices.keys() if start_date <= datetime.strptime(date, '%Y-%m-%d') < end_date]

        if not filtered_dates:
            return start_date.strftime('%Y-%m-%d') if first else end_date.strftime('%Y-%m-%d')

        # Return the first or last open market day
        return min(filtered_dates) if first else max(filtered_dates)

    def get_fx_rate(self, first_currency, second_currency, start, end):
        """Fetch FX rate data as { 'YYYY-MM-DD': rate }."""

        ticker = f"{first_currency}{second_currency}=X"
        print(f"Fetching fx rates: {ticker}")

        data = yf.download(ticker, start=start, end=end, interval='1d')

        if data.empty:
            print("Downloaded fx rates data is empty.")
            return {}

        # If data has MultiIndex columns (which happens when only one ticker is used)
        if isinstance(data.columns, pd.MultiIndex):
            close_series = data["Close"][ticker]  # Extract the actual Series
        else:
            close_series = data["Close"]  # Just in case it's flat

        # Build date string: rate dictionary
        fx_rates = {
            date.strftime('%Y-%m-%d'): price
            for date, price in close_series.items()
        }

        return fx_rates

    def calculate_mwr(self, stock, start_date, end_date=date.today().strftime('%Y-%m-%d'), stock_price_data=None):
        """Calculate Money Weighted Return using individual performance tracking for each transaction."""
        
        # Convert dates to datetime format
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d') + pd.Timedelta(days=1)

        # Delete 'nan' values in stock_price_data
        stock_price_data = {k: v for k, v in stock_price_data.items() if v == v}

        # Filter transactions within the date range
        period_transactions = self.transactions[(self.transactions["Date"] >= start_date) & (self.transactions["Date"] <= end_date) & (self.transactions['Stock'] == stock)]
        previous_transactions = self.transactions[(self.transactions["Date"] < start_date) & (self.transactions['Stock'] == stock)]

        all_transactions = pd.concat([previous_transactions, period_transactions], ignore_index=True)

        # Sort transactions by date and time
        all_transactions.sort_values(by=["Date", "Time"], inplace=True)

        # Load ISIN mapping from JSON
        with open('output/isin_mapping.json', 'r') as f:
            isin_mapping = json.load(f)

        # Build a reverse map: ticker -> display_name
        ticker_to_name = {
            data.get("ticker"): data.get("display_name", "")
            for data in isin_mapping.values()
            if "ticker" in data
        }

        product = ticker_to_name.get(stock, "")
        
        # Average cost
        if not all_transactions.empty:
            buys = all_transactions[all_transactions['Action'] == 'BUY']
            quantity_bought = buys['Quantity'].sum()
            avg_cost = -1 * (buys['Cost'].sum() / quantity_bought) if quantity_bought > 0 else 0

        # Initialize variables to track
        realized_return = 0
        quantity_held = 0
        purchase_cost = 0
        transaction_costs_total = 0

        # Track each transaction
        for _, row in all_transactions.iterrows():
            action, row_stock, quantity, transaction_costs = row["Action"], row["Stock"], row["Quantity"], row['Transaction_costs']
            transaction_price = abs(row["Cost"])/abs(row["Quantity"])

            transaction_value = quantity * transaction_price
            
            if action == "BUY":
                # Update total investment and average purchase cost
                purchase_cost += transaction_value
                quantity_held += quantity
                realized_return += transaction_costs
                transaction_costs_total += -1 * transaction_costs

            elif action == "SELL":
                # Calculate realized return based on average purchase cost
                if quantity_held > 0:
                    stock_transactions = all_transactions[all_transactions['Stock']==row_stock]
                    avg_cost_stock = -1 * (stock_transactions[stock_transactions['Action'].isin(['BUY'])]['Cost'].sum() / stock_transactions[stock_transactions['Action'].isin(['BUY'])]['Quantity'].sum())
                    transaction_costs_total += -1 * transaction_costs

                    quantity_held -= abs(quantity)
                    
                    # Calculate gain or loss
                    realized_return += abs(quantity) * (transaction_price - avg_cost_stock) + transaction_costs

        # Calculate current return for remaining holdings
        if quantity_held > 0:
            # Corrected end_date for market open
            end_date_cor = self.get_first_last_open_day(start_date, end_date, stock_price_data, first=False)
            end_date_cor = datetime.strptime(end_date_cor, '%Y-%m-%d')
            
            # Get stock price from pre-fetched data
            end_price = stock_price_data.get(str(end_date_cor.strftime('%Y-%m-%d')), 0)

            if end_price is None:
                end_price = 0

            current_return = (quantity_held*end_price) - (quantity_held*avg_cost)
        else:
            current_return = 0

        # Net return and current value of the stock
        net_return = current_return + realized_return
        current_value = (quantity_held*avg_cost) + current_return
        
        # Performance percentages
        current_performance_percentage = ((current_return) / purchase_cost) * 100 if (current_return and purchase_cost) else 0
        net_performance_percentage = ((current_return + realized_return) / purchase_cost) * 100 if purchase_cost else 0

        return {
            "product": product,
            "ticker": stock,
            "quantity": int(quantity_held),
            "start_date": start_date.strftime('%Y-%m-%d'),
            "end_date": end_date.strftime('%Y-%m-%d'),
            "avg_cost": round(avg_cost, 2),
            "total_cost": round(purchase_cost, 2),
            "transaction_costs": round(transaction_costs_total, 2),
            "current_value": round(current_value, 2),
            "current_money_weighted_return": round(current_return, 2),
            "realized_return": round(realized_return, 2),
            "net_return": round(net_return, 2),
            "current_performance_percentage": round(current_performance_percentage, 2),
            "net_performance_percentage": round(net_performance_percentage, 2)
        }
    
    def calculate_total_portfolio_performance(self, start_date, end_date, stock_results):

        # Initialize accumulators for the metrics
        quantity = 0
        purchase_cost = 0
        transaction_costs_total = 0
        current_value = 0
        current_return = 0
        realized_return = 0
        net_return = 0
        
        # Iterate over each stock and accumulate metrics
        for stock in stock_results.values():
            quantity += stock.get('quantity', 0)
            purchase_cost += stock.get('total_cost', 0)
            transaction_costs_total += stock.get('transaction_costs', 0)
            current_value += stock.get('current_value', 0)
            current_return += stock.get('current_money_weighted_return', 0)
            realized_return += stock.get('realized_return', 0)
            net_return += stock.get('net_return', 0)

        if quantity > 0:
            avg_cost_port = purchase_cost/quantity
        else:
            avg_cost_port = 0

        # Performance percentages
        current_performance_percentage = ((current_return) / purchase_cost) * 100 if (current_return and purchase_cost) else 0
        net_performance_percentage = ((current_return + realized_return) / purchase_cost) * 100 if purchase_cost else 0
        
        # Return the aggregated portfolio performance metrics
        return {
                "product": "Full portfolio",
                "ticker": "FULL",
                "quantity": int(quantity),
                "start_date": start_date,
                "end_date": end_date,
                "avg_cost": round(avg_cost_port, 2),
                "total_cost": round(purchase_cost, 2),
                "transaction_costs": round(transaction_costs_total, 2),
                "current_value": round(current_value, 2),
                "current_money_weighted_return": round(current_return, 2),
                "realized_return": round(realized_return, 2),
                "net_return": round(net_return, 2),
                "current_performance_percentage": round(current_performance_percentage, 2),
                "net_performance_percentage": round(net_performance_percentage, 2)
        }

    def calculate_all_stocks_mwr(self, stocks, start_date, end_date, stock_prices, results=None):
        """Calculate MWR for each stock within the portfolio and full portfolio over the specified period."""

        if results is None:
            results = {}
        
        # Each stock
        for stock in stocks:
            results[stock] = self.calculate_mwr(stock, start_date, end_date, stock_prices[stock])

        # Full portfolio
        results['portfolio'] = self.calculate_total_portfolio_performance(start_date, end_date, results)

        return results
