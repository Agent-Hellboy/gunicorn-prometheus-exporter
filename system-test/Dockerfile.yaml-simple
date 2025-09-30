FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies including build tools for gevent
RUN apt-get update && apt-get install -y \
    curl \
    gunicorn \
    build-essential \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app/

# Install only the core dependencies needed for YAML testing
RUN pip install --no-cache-dir \
    psutil>=5.9.8 \
    PyYAML>=6.0.0 \
    gunicorn>=21.2.0 \
    prometheus-client>=0.20.0 \
    redis>=4.0.0

# Install the package in development mode (without dev dependencies)
RUN pip install -e .

# Create directories for test files
RUN mkdir -p /app/config /app/logs

# Copy test app
COPY system-test/test_app.py /app/test_app.py

# Set environment variables
ENV PYTHONPATH=/app
ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc

# Expose ports
EXPOSE 8089 9094

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9094/metrics || exit 1

# Default command
CMD ["python", "-c", "print('YAML test container ready')"]
