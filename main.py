import time
import os
import subprocess
from helpers.transactions import transactions
from helpers.portfolio_analyzer import PortfolioAnalyzer
from helpers.portfolio import calc_portfolio

# Start timing
start_time = time.time()

# Check if the folder exists and is empty
output_folder = "output"
if not os.path.exists(output_folder) or not any(os.scandir(output_folder)):
    print("Output folder is empty. Running db_refresh.py...")
    subprocess.run(["python", "db_refresh.py"])
else:
    print("Output folder is not empty. Skipping db_refresh.py...")

# Initialize PortfolioAnalyzer and DB
analyzer = PortfolioAnalyzer(transactions)

calc_portfolio(analyzer, "2020-11-26")

# End timing
end_time = time.time()
print(f"Execution time: {round(end_time - start_time, 2)} seconds")
