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

# Date range options
DATE_RANGE_OPTIONS = ["1Y", "3M", "1M", "1W", "YTD", "Last year", "Last month", "All time"]

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
    'current_money_weighted_return': 'Current Return (€)',
    'realized_return': 'Realized Return (€)',
    'net_return': 'Net Return (€)',
    'current_performance_percentage': 'Current Performance (%)',
    'net_performance_percentage': 'Net Performance (%)'
}

# Help texts
METRIC_HELP_TEXTS = {
    'Average Cost (€)': (
        "The average purchase price per unit of the currently held position, "
        "including transaction costs. Calculated as total cost divided by the "
        "number of units currently held."
    ),

    'Total Cost (€)': (
        "The total amount of capital invested into the portfolio over time, including "
        "all purchases and transaction costs. This is a cumulative metric that only "
        "increases and does not decrease when positions are sold."
    ),

    'Transaction Costs (€)': (
        "The total transaction costs paid for the position, such as brokerage "
        "fees. These costs are included in net return and performance calculations."
    ),

    'Current Value (€)': (
        "The total market value of all currently held positions on the last day "
        "of the selected period, based on closing prices."
    ),

    'Current Return (€)': (
        "The unrealized money-weighted profit or loss of all currently held positions "
        "on the last day of the selected period. This return accounts for the timing "
        "and size of investments and represents the difference between current market "
        "value and invested capital in open positions. Sold positions are excluded."
    ),

    'Realized Return (€)': (
        "The profit or loss realized from positions that have been sold during "
        "the selected period. Calculated as selling proceeds minus purchase costs "
        "and transaction costs."
    ),

    'Net Return (€)': (
        "The total portfolio return on the last day of the selected period, "
        "including both realized returns from sold positions and unrealized returns "
        "from currently held positions. This represents the overall profit or loss "
        "of the portfolio."
    ),

    'Current Performance (%)': (
        "The unrealized return of currently held positions expressed as a percentage "
        "of their total cost. Calculated as current return divided by total cost."
    ),

    'Net Performance (%)': (
        "The total portfolio return expressed as a percentage of the total invested "
        "capital. Includes both realized and unrealized returns."
    ),

     'YTD - Net Return (€)': (
        "The year-to-date change in total net return since the end of the previous "
        "calendar year. Calculated as the difference between the current net return "
        "and the net return recorded on the last day of last year. "
        "Includes both realized and unrealized returns."
    ),

    'YTD - Net Performance (%)': (
        "The year-to-date net return expressed as a percentage of the total invested "
        "capital at the end of the previous calendar year. Calculated as the change in "
        "net return since last year-end divided by the total cost at that time. "
        "This is a money-weighted performance measure."
    )
}