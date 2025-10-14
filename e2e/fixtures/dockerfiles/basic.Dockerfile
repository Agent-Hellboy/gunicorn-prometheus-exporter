# Dockerfile for Gunicorn Prometheus Exporter Basic System Test (File-based Multiprocess)
# This creates a consistent environment for testing file-based multiprocess storage

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
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
RUN pip install --no-cache-dir requests psutil gunicorn flask

# Make the system test script executable
RUN chmod +x integration/test_basic.sh

# Create startup script for basic test
RUN echo '#!/bin/bash\n\
# Set environment variables for file-based multiprocess\n\
export PROMETHEUS_MULTIPROC_DIR="/tmp/prometheus_multiproc"\n\
export GUNICORN_WORKERS="2"\n\
\n\
# Create multiprocess directory\n\
mkdir -p "$PROMETHEUS_MULTIPROC_DIR"\n\
echo "Created multiprocess directory: $PROMETHEUS_MULTIPROC_DIR"\n\
\n\
# Run the basic system test\n\
cd /app\n\
# Set environment to skip virtual environment creation\n\
export SKIP_VENV=true\n\
./test_basic.sh --ci\n\
' > /start_basic_test.sh && chmod +x /start_basic_test.sh

# Default command
CMD ["/start_basic_test.sh"]
