import time
import os
import subprocess
from helpers.transactions import transactions
from helpers.portfolio_analyzer import PortfolioAnalyzer
from helpers.portfolio import calc_portfolio

# Start timing
start_time = time.time()

# Initialize PortfolioAnalyzer and DB
analyzer = PortfolioAnalyzer(transactions)

# Check if the folder exists and contains .parquet files
output_folder = "output"
parquet_files = [f for f in os.scandir(output_folder) if f.name.endswith(".parquet")]

if not parquet_files:
    print("No .parquet files found in the output folder. Running db_refresh.py...")
    subprocess.run(["python", "db_refresh.py"])
else:
    print("Parquet files found in the output folder. Skipping db_refresh.py...")

# Main execution function
calc_portfolio(analyzer, "2020-11-26")

# End timing
end_time = time.time()
print(f"Execution time: {round(end_time - start_time, 2)} seconds")
