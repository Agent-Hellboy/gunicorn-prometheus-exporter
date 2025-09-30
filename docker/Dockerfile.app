# Sample Flask application with Gunicorn and Prometheus Exporter
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install Python dependencies
COPY docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install gunicorn-prometheus-exporter
RUN pip install --no-cache-dir "gunicorn-prometheus-exporter[all]"

# Copy application code
COPY docker/app.py .
COPY docker/gunicorn.conf.py .

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app

# Create multiprocess directory
RUN mkdir -p /tmp/prometheus_multiproc && \
    chown -R appuser:appuser /tmp/prometheus_multiproc

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
