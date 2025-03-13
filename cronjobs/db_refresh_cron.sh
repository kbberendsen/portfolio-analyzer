#!/bin/bash

# Define the base log directory and current date
LOG_BASE_DIR="/app/cronjobs/logs/db_refresh" 
CURRENT_DATE=$(date +%Y-%m-%d)
LOG_FILE="$LOG_BASE_DIR/$CURRENT_DATE.log"

# Ensure the base log directory exists
mkdir -p "$LOG_BASE_DIR"

# Redirect output to the daily log file (append mode)
exec >> "$LOG_FILE" 2>&1

# Change to the root app directory before running Python scripts
cd /app

# Load environment variables manually
export $(grep -v '^#' /app/.env | xargs)

# Add a separator for better readability
echo "===== Log started at $(date +%Y-%m-%d_%H:%M:%S) ====="

# Run db_refresh.py inside the container
echo "Running db_refresh.py inside the container..."
/usr/local/bin/python3 /app/db_refresh.py

# Run main.py inside the container
echo "Running main.py inside the container..."
/usr/local/bin/python3 /app/main.py

# Add a separator to mark the end of this log entry
echo "===== Log ended at $(date +%Y-%m-%d_%H:%M:%S) ====="