import time
from helpers.transactions import transactions
from helpers.portfolio_analyzer import PortfolioAnalyzer
from helpers.db import DB
from helpers.portfolio import calc_portfolio
from helpers.db_refresh import db_refresh

# Start timing
start_time = time.time()

# Intialize PortfolioAnalyzer and DB
analyzer = PortfolioAnalyzer(transactions)
db = DB()

calc_portfolio(analyzer, db, '2020-11-26')

# End timing
end_time = time.time()
print(f"Execution time: {round(end_time - start_time, 2)} seconds")
