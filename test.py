import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_price_at_date(stock, date):
    """Fetches end-of-day stock price for a specific date using yfinance."""
    stock_data = yf.Ticker(stock)
    history = stock_data.history(period="1d", start=datetime.strptime(date, '%Y-%m-%d'))
    # Return the closing price for the specified date
    return float(history['Close'].iloc[0]) if not history.empty else None

day_1 = get_price_at_date('2B7K.DE', '2024-11-11')
day_2 = get_price_at_date('2B7K.DE', '2024-11-12')
print(day_1)
print(day_2)