from datetime import datetime, date, timedelta
import pandas as pd
from helpers.transactions import transactions
from helpers.portfolio_analyzer import PortfolioAnalyzer
from helpers.portfolio import calc_monthly, calc_daily

analyzer = PortfolioAnalyzer(transactions)

# Monthly
calc_monthly(analyzer)

# Daily
calc_daily(analyzer, '2024-08-01')
