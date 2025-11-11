FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set Python path to include current directory
ENV PYTHONPATH=/app

# Expose port (Cloud Run uses PORT environment variable)
ENV PORT=8080
EXPOSE 8080

# Run the application
CMD exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080}

