# Use official Python image
FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Copy project files
COPY . /app

# Create necessary folders
RUN mkdir -p /app/output /app/uploads /app/logs

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Expose Streamlit (public) and FastAPI (internal only)
EXPOSE 8501
EXPOSE 8000

# Run both FastAPI and Streamlit
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port 8000 & streamlit run app.py --server.port=8501 --server.address=0.0.0.0"]