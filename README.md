Streamlit dashboard displaying analytics of a DeGiro stock portfolio.

![screenshot_portfolio_dashboard](screenshot_portfolio_dashboard.png)

# Installation

## Docker
Before you start, make sure Docker is installed on your machine/server. See the [official Docker installation guide](https://docs.docker.com/engine/install/) based on your OS.

## Supabase
The app needs a [Supabase database](https://supabase.com/) to store and retrieve stock prices and portfolio performance data from. The Supabase free tier will suffice. Create a new project and create two tables (this can be done in the 'SQL Editor' in the Supabase online dashboard):

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
    PRIMARY KEY (ticker, date)
);

```
After creating the tables, make sure to go to the Supabase project (API) settings to retrieve your __Supabase URL and key__. These will be needed later on in this installation process.

## Install app

### Create a new directory for your project on your machine/server
```
mkdir portfolio-analyzer
cd portfolio-analyzer
```

### Download the docker-compose.yaml from GitHub
```
curl -O https://raw.githubusercontent.com/kbberendsen/portfolio-analyzer/main/docker-compose.yaml
```

### Create the .env file with required values (replace placeholders)
```
cat <<EOT > .env
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
docker compose up --force-recreate -d --build
```
