#!/bin/bash

# Define the base log directory and current date
LOG_BASE_DIR="/home/user/cronjobs/logs/portfolio_analyzer"  # Adjust this if necessary
CURRENT_DATE=$(date +%Y-%m-%d)
LOG_FILE="$LOG_BASE_DIR/$CURRENT_DATE.log"

# Ensure the base log directory exists
mkdir -p "$LOG_BASE_DIR"

# Redirect output to the daily log file (append mode)
exec >> "$LOG_FILE" 2>&1

# Add a separator for better readability
echo "===== Log started at $(date +%Y-%m-%d_%H:%M:%S) ====="

# Run db_refresh.py inside the container
echo "Running db_refresh.py inside the container..."
docker exec portfolio-analyzer-container python /app/db_refresh.py

# Run main.py inside the container
echo "Running main.py inside the container..."
docker exec portfolio-analyzer-container python /app/main.py

# Add a separator to mark the end of this log entry
echo "===== Log ended at $(date +%Y-%m-%d_%H:%M:%S) ====="