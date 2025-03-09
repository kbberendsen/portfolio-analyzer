Streamlit dashboard displaying analytics of a DeGiro stock portfolio.

![screenshot_portfolio_dashboard](screenshot_portfolio_dashboard.png)

## Installation

### Create a new directory for your project
```
mkdir portfolio-analyzer
cd portfolio-analyzer
```

## Download the docker-compose.yml from GitHub
```
curl -O https://raw.githubusercontent.com/kbberendsen/portfolio-analyzer/main/docker-compose-prod.yml
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
docker-compose up --build -d
```
