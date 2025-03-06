from datetime import datetime, date, timedelta
import pandas as pd
from helpers.transactions import transactions
from helpers.portfolio_analyzer import PortfolioAnalyzer
from helpers.db import DB
from helpers.portfolio import calc_monthly, calc_daily

analyzer = PortfolioAnalyzer(transactions)
db = DB()

# Monthly
calc_monthly(analyzer, db)

# Daily
calc_daily(analyzer, db, '2023-12-28')
