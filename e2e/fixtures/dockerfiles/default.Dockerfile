# Dockerfile for Gunicorn Prometheus Exporter System Test
# This creates a consistent environment that works on Mac, Windows, and Linux

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    redis-server \
    redis-tools \
    lsof \
    curl \
    procps \
    coreutils \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Prometheus
ARG PROM_VERSION=2.45.0
RUN set -eux; \
    url="https://github.com/prometheus/prometheus/releases/download/v${PROM_VERSION}/prometheus-${PROM_VERSION}.linux-amd64.tar.gz"; \
    wget -O /tmp/prometheus.tgz "$url"; \
    tar -xzf /tmp/prometheus.tgz -C /tmp; \
    mv /tmp/prometheus-${PROM_VERSION}.linux-amd64/prometheus /usr/local/bin/; \
    mv /tmp/prometheus-${PROM_VERSION}.linux-amd64/promtool /usr/local/bin/; \
    rm -rf /tmp/prometheus*;

# Set working directory
WORKDIR /app

# Copy the project files
COPY . /app/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Install additional test dependencies
RUN pip install --no-cache-dir redis requests psutil gunicorn flask

# Make system test script executable
RUN chmod +x integration/test_redis_integ.sh

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc

# Expose ports
EXPOSE 8088 9093 6379 9090

# Create Prometheus configuration
RUN echo 'global:\n\
  scrape_interval: 15s\n\
  evaluation_interval: 15s\n\
\n\
rule_files:\n\
  # - "first_rules.yml"\n\
  # - "second_rules.yml"\n\
\n\
scrape_configs:\n\
  - job_name: "gunicorn-prometheus-exporter"\n\
    static_configs:\n\
      - targets: ["localhost:9093"]\n\
    scrape_interval: 5s\n\
    metrics_path: "/metrics"\n\
' > /etc/prometheus.yml

# Create startup script
RUN echo '#!/bin/bash\n\
# Start Redis in background\n\
redis-server --daemonize yes\n\
\n\
# Wait for Redis to be ready\n\
while ! redis-cli -h 127.0.0.1 -p 6379 -n 0 ping > /dev/null 2>&1; do\n\
    echo "Waiting for Redis..."\n\
    sleep 1\n\
done\n\
\n\
# Start Prometheus in background\n\
prometheus --config.file=/etc/prometheus.yml --storage.tsdb.path=/tmp/prometheus --web.console.libraries=/usr/local/share/prometheus/console_libraries --web.console.templates=/usr/local/share/prometheus/consoles --web.enable-lifecycle --web.listen-address=:9090 &\n\
\n\
# Wait for Prometheus to be ready\n\
while ! curl -s http://localhost:9090/-/ready > /dev/null 2>&1; do\n\
    echo "Waiting for Prometheus..."\n\
    sleep 1\n\
done\n\
\n\
# Run the Redis integration system test (already in Docker, so no --docker flag needed)\n\
cd /app\n\
export SKIP_VENV=true\n\
# Use environment variables to determine test mode\n\
if [ "$QUICK_MODE" = "true" ]; then\n\
    ./test_redis_integ.sh --quick --ci --no-redis\n\
else\n\
    ./test_redis_integ.sh --ci --no-redis\n\
fi\n\
' > /start_test.sh && chmod +x /start_test.sh

# Default command
CMD ["/start_test.sh"]
