import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_price_at_date(stock, date):
    """Fetches stock price at a specific date using yfinance."""
    stock_data = yf.Ticker(stock)
    history = stock_data.history(start=date, end=(datetime.strptime(date, '%Y-%m-%d') )) #+ timedelta(days=1)).strftime('%Y-%m-%d')
    return float(history['Close'].iloc[0]) if not history.empty else None

def get_price_at_date(stock, date):
    """Fetches end-of-day stock price for a specific date using yfinance."""
    stock_data = yf.Ticker(stock)
    history = stock_data.history(period="1d", start=datetime.strptime(date, '%Y-%m-%d'))
    # Return the closing price for the specified date
    return float(history['Close'].iloc[0]) if not history.empty else None

test = get_price_at_date('NQSE.DE', '2024-11-09')
print(test)