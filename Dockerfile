# Multi-stage build for gunicorn-prometheus-exporter sidecar
FROM python:3.11-slim as builder

# Set build arguments
ARG VERSION=0.2.3
ARG INSTALL_EXTRAS=all

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy source code
COPY src/ ./src/
COPY pyproject.toml ./
COPY README.md ./
COPY LICENSE ./

# Install the package
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir ".[${INSTALL_EXTRAS}]"

# Production stage
FROM python:3.11-slim

# Set labels for metadata
LABEL maintainer="Prince Roshan <princekrroshan01@gmail.com>"
LABEL description="Gunicorn Prometheus Exporter - Sidecar container for monitoring Gunicorn applications"
LABEL version="0.2.3"
LABEL org.opencontainers.image.source="https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter"
LABEL org.opencontainers.image.licenses="MIT"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r gunicorn && useradd -r -g gunicorn gunicorn

# Create directories
RUN mkdir -p /app /tmp/prometheus_multiproc /var/log && \
    chown -R gunicorn:gunicorn /app /tmp/prometheus_multiproc /var/log

# Set working directory
WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy sidecar script and configuration
COPY docker/sidecar.py /app/sidecar.py
COPY docker/gunicorn-prometheus-exporter-basic.yml /app/
COPY docker/entrypoint.sh /app/entrypoint.sh

# Make scripts executable
RUN chmod +x /app/entrypoint.sh

# Set environment variables
ENV PYTHONPATH=/usr/local/lib/python3.11/site-packages
ENV PROMETHEUS_METRICS_PORT=9091
ENV PROMETHEUS_BIND_ADDRESS=0.0.0.0
ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
ENV REDIS_ENABLED=true
ENV GUNICORN_WORKERS=1
ENV SIDECAR_MODE=true

# Expose metrics port
EXPOSE 9091

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9091/metrics || exit 1

# Switch to non-root user
USER gunicorn

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["sidecar"]
