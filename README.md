Streamlit dashboard displaying analytics of a DeGiro stock portfolio.

![screenshot_portfolio_dashboard](screenshot_portfolio_dashboard.png)

# Installation

## Docker
Before you start, make sure Docker is installed on your machine/server. See the [official Docker installation guide](https://docs.docker.com/engine/install/) based on your OS.

## Install app

### Create a new directory for your portfolio analyzer on your machine/server
```
mkdir portfolio-analyzer
cd portfolio-analyzer
```

### Download the docker-compose.yaml from GitHub
```
curl -O https://raw.githubusercontent.com/kbberendsen/portfolio-analyzer/main/docker-compose.yaml
```

### Create the .env file
Create a `.env` file in the same directory as the downloaded docker-compose file. If you want to use a Supabase database ([optional](#optional-supabase-database)), make sure to enter your URL and key values in the .env file and set `USE_SUPABASE` to `"true"`. If not, leave the default values.

```
cat <<EOT > .env
USE_SUPABASE=false
SUPABASE_URL=https://your-supabase-url
SUPABASE_KEY=your-supabase-api-key
EOT
```

### Build and run the Docker container

```
docker compose up --build -d
```

### Updating the container
```
docker compose down
docker compose pull
docker compose up --force-recreate -d --build
```

# Initial run
Go to http://localhost:8501/ to see your stock portfolio dashboard! After running the app, the streamlit port (8501) can be redirected to another domain if desired.

## Upload initial Transactions.csv (from DeGiro)
- When opening the dashboard for the first time, upload a Transactions.csv file.
- This transactions file can be found in your DeGiro portfolio. Go to inbox > transactions and select the full date range of all transactions. then click export (csv).
- Upload the csv in the dashboard. The uploaded file will be stored in the 'uploads' directory in the portfolio-analyzer directory.
- Reload the page. Loading the dashboard for the first time ([after you've mapped the tickers](#ticker-mapping)) might take a few minutes, depending on the date range of transactions. Subsequent runs will take a few seconds to load.

## Updating Transactions.csv
- After new transactions, download the new transactions file from DeGiro. The old file will be overwritten so make sure to select the full date range of transactions each time to not miss any previous transactions.
- To update the transactions data in the dashboard, upload the new transactions file through the sidebar in the dashboard.
- Reload the page.

## Directory structure
After uploading your transaction csv file to the dashboard for the first time, your app directory should look like this:

```
.
├── .env
├── cronjobs
│   └── logs
├── docker-compose.yaml
└── output
    └── cached data files
└── uploads
    └── Transactions.csv
```

## Ticker Mapping

After uploading your transaction data, the app requires **stock tickers** (e.g., `AAPL` for Apple) to fetch price data from Yahoo Finance. However, DeGiro only provides **ISIN identifiers**, not tickers. Therefore, **you need to manually map each ISIN to a ticker** the first time you encounter a new product.

### How to map tickers

1. Go to the **ticker mapping** page.
2. Use the **Auto-fill tickers** button to automatically search for tickers based on the product name (this can take a few seconds).
3. Carefully review all auto-filled tickers. **Exchange-traded funds (ETFs)** in particular can have multiple versions across exchanges — make sure the ticker matches the **correct exchange and price**.
4. If auto-fill fails or the ticker is incorrect:
   - Simplify the **display name** and retry auto-fill.
   - Or: visit [Yahoo Finance](https://finance.yahoo.com).
   - Search for the product name.
   - Choose the ticker with the correct exchange and price.

### Manual editing

- You can **edit the ticker** and **display name** for each ISIN directly in the app.
- You can also **download the mapping as a JSON file**, edit it manually, and re-upload it if needed.
- The **display name** is used throughout the dashboard (e.g., charts and tables), so feel free to customize it.

> ⚠️ If ticker fields remain empty, the app will not show the product. You must complete ticker mapping before proceeding.

## Currency Conversion
The app supports **currency conversion** for products priced in different currencies. It uses [Yahoo Finance](https://finance.yahoo.com) to fetch exchange rates. The app will automatically convert all prices to Euro.

# Optional: Supabase database
The app can utilize a [Supabase database](https://supabase.com/) to store and retrieve your portfolio performance data in the cloud. The Supabase free tier will suffice. Create a new project and create three tables (this can be done in the 'SQL Editor' in the Supabase online dashboard):

**Daily performance table**
```
CREATE TABLE portfolio_performance_daily (
    product VARCHAR,
    ticker VARCHAR,
    quantity INT,
    start_date DATE,
    end_date DATE,
    avg_cost NUMERIC,
    total_cost NUMERIC,
    transaction_costs NUMERIC,
    current_value NUMERIC,
    current_money_weighted_return NUMERIC,
    realized_return NUMERIC,
    net_return NUMERIC,
    current_performance_percentage NUMERIC,
    net_performance_percentage NUMERIC,
    PRIMARY KEY (ticker, end_date)
);
```

**Monthly performance table**
```
CREATE TABLE portfolio_performance_monthly (
    product VARCHAR,
    ticker VARCHAR,
    quantity INT,
    start_date DATE,
    end_date DATE,
    avg_cost NUMERIC,
    total_cost NUMERIC,
    transaction_costs NUMERIC,
    current_value NUMERIC,
    current_money_weighted_return NUMERIC,
    realized_return NUMERIC,
    net_return NUMERIC,
    current_performance_percentage NUMERIC,
    net_performance_percentage NUMERIC,
    PRIMARY KEY (ticker, end_date)
);
```

**Stock prices table**
```
CREATE TABLE stock_prices (
    ticker TEXT,
    date DATE,
    price NUMERIC,
    fx_rate NUMERIC,
    currency_pair, TEXT
    PRIMARY KEY (ticker, date)
);
```
After creating the tables, make sure to go to the Supabase project (API) settings to retrieve your __Supabase URL and key__. These values need to be filled in into the .env file created earlier.
