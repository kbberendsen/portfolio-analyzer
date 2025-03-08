import time
from helpers.transactions import transactions
from helpers.portfolio_analyzer import PortfolioAnalyzer
from helpers.portfolio import calc_portfolio

# Start timing
start_time = time.time()

# Intialize PortfolioAnalyzer and DB
analyzer = PortfolioAnalyzer(transactions)

calc_portfolio(analyzer, '2020-11-26')
# End timing
end_time = time.time()
print(f"Execution time: {round(end_time - start_time, 2)} seconds")
