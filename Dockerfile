# Use an official Python runtime as a base image
FROM python:3.12

# Install cron and other dependencies
RUN apt-get update && apt-get install -y cron

# Set the working directory
WORKDIR /app

# Copy project files into the container
COPY . /app

# Create empty 'output' and 'uploads' directories
RUN mkdir -p /app/output /app/uploads

# Make the cron job script executable
RUN chmod +x /app/cronjobs/db_refresh_cron.sh

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Add the cron job to crontab (run it at a specific time, e.g., every day at 3 AM)
RUN echo "0 3 * * * /app/cronjobs/db_refresh_cron.sh" > /etc/cron.d/db_refresh_cron

# Give appropriate permissions to the cron file
RUN chmod 0644 /etc/cron.d/db_refresh_cron

# Apply the cron job by restarting the cron service
RUN crontab /etc/cron.d/db_refresh_cron

# Expose the Streamlit port
EXPOSE 8501

# Run the cron service in the background, and also start the Streamlit app
CMD cron && streamlit run app.py --server.port=8501 --server.address=0.0.0.0