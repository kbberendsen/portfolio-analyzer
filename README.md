Streamlit dashboard displaying analytics of a DeGiro stock portfolio.

![screenshot_portfolio_dashboard](screenshot_portfolio_dashboard.png)

## Installation
Before you start, make sure Docker is installed on your machine/server. See the [official Docker installation guide](https://docs.docker.com/engine/install/) based on your OS.

### Create a new directory for your project
```
mkdir portfolio-analyzer
cd portfolio-analyzer
```

## Download the docker-compose.yml from GitHub
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
