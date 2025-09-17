# Dockerfile for Gunicorn Prometheus Exporter System Test
# This creates a consistent environment that works on Mac, Windows, and Linux

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    redis-server \
    lsof \
    curl \
    procps \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy the project files
COPY . /app/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Install additional test dependencies
RUN pip install --no-cache-dir redis requests psutil gunicorn flask

# Make system test script executable
RUN chmod +x system-test/system_test_redis_integ.sh

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc

# Expose ports
EXPOSE 8088 9093 6379

# Create startup script
RUN echo '#!/bin/bash\n\
# Start Redis in background\n\
redis-server --daemonize yes\n\
\n\
# Wait for Redis to be ready\n\
while ! redis-cli ping > /dev/null 2>&1; do\n\
    echo "Waiting for Redis..."\n\
    sleep 1\n\
done\n\
\n\
# Run the Redis integration system test (already in Docker, so no --docker flag needed)\n\
cd system-test\n\
export SKIP_VENV=true\n\
./system_test_redis_integ.sh --ci\n\
' > /start_test.sh && chmod +x /start_test.sh

# Default command
CMD ["/start_test.sh"]
