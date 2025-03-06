import yfinance as yf
from datetime import datetime, date, timedelta
import pandas as pd
from helpers.db import DB


def get_price_at_date(tickers, start, end):
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

data = get_price_at_date([ 'AAPL', 'MSFT'], '2023-01-01', '2023-01-05')

data_to_insert = [
            {"ticker": ticker, "date": date, "price": price}
            for ticker, date_prices in data.items()
            for date, price in date_prices.items()
        ]

#print(data_to_insert)

def get_first_last_open_day(stock, start_date, end_date, first=True):
        """Fetches the first or last open market day within a given date range."""
        stock_data = yf.Ticker(stock)
        history = stock_data.history(start=start_date, end=end_date)
        print (history)
        if first:
            return history.index[0].strftime('%Y-%m-%d') if not history.empty else start_date
        else:
            return history.index[-1].strftime('%Y-%m-%d') if not history.empty else end_date

db = DB()
print(db.get_row_count('portfolio_performance_daily'))