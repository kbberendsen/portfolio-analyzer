import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_price_at_date(stock, date):
    """Fetches end-of-day stock price for a specific date using yfinance."""
    stock_data = yf.Ticker(stock)
    history = stock_data.history(period="1d", start=datetime.strptime(date, '%Y-%m-%d'))
    # Return the closing price for the specified date
    return float(history['Close'].iloc[0]) if not history.empty else None

# day_1 = get_price_at_date('XYZ', '2020-11-11')
# day_2 = get_price_at_date('XYZ', '2024-11-12')
# print(day_1)
# print(day_2)

tickers = ['XYZ', 'PYPL','NQSE.DE']

def get_price_at_date(tickers, date):
    stock_data = yf.download(tickers, start=date, end=(datetime.strptime(date, '%Y-%m-%d') + timedelta(days=4)).strftime('%Y-%m-%d'), interval="1d")#["Close"]
    return stock_data#.to_dict()

# stock_price_data = get_price_at_date(tickers, '2025-02-04')
# print(stock_price_data)

# end_date_cor = datetime.strptime('2025-02-07', '%Y-%m-%d')
# end_date_cor_ts = pd.Timestamp(end_date_cor).tz_localize('UTC') # Convert end_date to a pandas Timestamp with UTC
# end_price = stock_price_data.get('XYZ', {}).get(end_date_cor_ts, 0)
# print(end_price)

test = get_price_at_date(tickers, '2025-02-08')
print(test)