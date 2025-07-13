API_BASE_URL = "http://127.0.0.1:8000"

# Environment variable key for API URL override
ENV_API_BASE_URL_KEY = "API_BASE_URL"

# Folder paths
UPLOADS_DIR = "uploads"
LOGS_DIR = "logs"

# Filenames
TRANSACTIONS_CSV = "Transactions.csv"

# Date formats
DATE_FORMAT_ISO = "%Y-%m-%d"
DATETIME_FORMAT_ISO = "%Y-%m-%dT%H:%M:%S"

# UI messages
NO_LOG_FILES_MSG = "No log files found."
NO_DATA_FOUND_MSG = "No portfolio data found. Please upload a transaction file and refresh the data."
UPLOAD_SUCCESS_MSG = "File uploaded successfully! Please reload the page."

# Performance metric rename dictionary (for display purposes)
PERFORMANCE_METRIC_RENAME = {
    'product': 'Product',
    'ticker': 'Ticker',
    'quantity': 'Quantity',
    'start_date': 'Start Date',
    'end_date': 'End Date',
    'avg_cost': 'Average Cost (€)',
    'total_cost': 'Total Cost (€)',
    'transaction_costs': 'Transaction Costs (€)',
    'current_value': 'Current Value (€)',
    'current_money_weighted_return': 'Current Money Weighted Return (€)',
    'realized_return': 'Realized Return (€)',
    'net_return': 'Net Return (€)',
    'current_performance_percentage': 'Current Performance (%)',
    'net_performance_percentage': 'Net Performance (%)'
}

# Date range options for your segmented control
DATE_RANGE_OPTIONS = ["1Y", "3M", "1M", "1W", "YTD", "Last year", "Last month", "All time"]