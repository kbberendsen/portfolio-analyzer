from datetime import datetime, date, timedelta
import pandas as pd
from helpers.transactions import transactions
from helpers.portfolio_analyzer import PortfolioAnalyzer
from helpers.db import DB
from helpers.portfolio import calc_portfolio

# Intialize PortfolioAnalyzer and DB
analyzer = PortfolioAnalyzer(transactions)
db = DB()

calc_portfolio(analyzer, db, '2020-11-26')
