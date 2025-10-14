# Makefile for Gunicorn Prometheus Exporter

.PHONY: help install unit-test integration-test-redis-quick integration-test-redis-full integration-test-redis-ci integration-test-redis-force integration-test-file-storage integration-test-file-storage-quick e2e-test-redis-docker e2e-test-redis-build e2e-test-file-storage-docker e2e-test-file-storage-build integration-test-yaml-config integration-test-yaml-config-quick e2e-test-yaml-config-docker e2e-test-yaml-config-build clean lint format

# Default target
help:
	@echo "Available targets:"
	@echo "  install                        - Install dependencies"
	@echo "  unit-test                       - Run unit tests"
	@echo "  integration-test-redis-quick   - Run quick Redis integration test (requires Redis running)"
	@echo "  integration-test-redis-full    - Run full Redis integration test (auto-starts Redis)"
	@echo "  integration-test-redis-ci      - Run CI-optimized Redis integration test"
	@echo "  integration-test-redis-force   - Run Redis test with force kill of existing processes"
	@echo "  integration-test-file-storage  - Run file-based storage integration test"
	@echo "  integration-test-file-storage-quick - Run quick file-based storage integration test"
	@echo "  e2e-test-redis-docker          - Run Redis e2e test in Docker (works on Mac/Windows/Linux)"
	@echo "  e2e-test-redis-build           - Build Docker image for Redis e2e test"
	@echo "  e2e-test-file-storage-docker    - Run file-based storage e2e test in Docker"
	@echo "  e2e-test-file-storage-build     - Build Docker image for file-based storage e2e test"
	@echo "  integration-test-yaml-config   - Run YAML configuration integration test"
	@echo "  integration-test-yaml-config-quick - Run quick YAML configuration integration test"
	@echo "  e2e-test-yaml-config-docker     - Run YAML configuration e2e test in Docker"
	@echo "  e2e-test-yaml-config-build      - Build Docker image for YAML configuration e2e test"
	@echo "  clean                          - Clean up test artifacts"
	@echo "  lint                           - Run linting"
	@echo "  format                         - Format code"

# Install dependencies
install:
	pip install -e .
	pip install -r e2e/requirements-dev.txt

# Run unit tests
unit-test:
	python -m pytest tests/ -v

# Quick Redis integration test (requires Redis running)
integration-test-redis-quick:
	@echo "Running quick Redis integration test..."
	@echo "Make sure Redis is running: brew services start redis (macOS) or sudo systemctl start redis (Linux)"
	integration/test_redis_integration.sh --quick --no-redis --force

# Full Redis integration test (starts Redis automatically)
integration-test-redis-full:
	@echo "Running full Redis integration test..."
	integration/test_redis_integration.sh

# CI-optimized Redis integration test (timeout-protected, better for CI)
integration-test-redis-ci:
	@echo "Running CI-optimized Redis integration test..."
	integration/test_redis_integration.sh --ci

# Force Redis test (kills existing processes)
integration-test-redis-force:
	@echo "Running force Redis test (kills existing processes)..."
	integration/test_redis_integration.sh --force

# File-based storage integration test
integration-test-file-storage:
	@echo "Running file-based storage integration test..."
	integration/test_file_storage_integration.sh

# Quick file-based storage integration test
integration-test-file-storage-quick:
	@echo "Running quick file-based storage integration test..."
	integration/test_file_storage_integration.sh --quick

# YAML configuration integration test
integration-test-yaml-config:
	@echo "Running YAML configuration integration test..."
	integration/test_yaml_config_integration.sh

# Quick YAML configuration integration test
integration-test-yaml-config-quick:
	@echo "Running quick YAML configuration integration test..."
	integration/test_yaml_config_integration.sh --quick

# Clean up test artifacts
clean:
	rm -f *.log
	pkill -f "gunicorn.*redis_integration" || true
	pkill -f "gunicorn.*basic" || true
	pkill -f "gunicorn.*yaml" || true
	pkill -f "redis-server" || true
	rm -rf /tmp/prometheus_multiproc || true
	docker rmi gunicorn-prometheus-exporter-test 2>/dev/null || true
	docker rmi gunicorn-prometheus-exporter-basic-test 2>/dev/null || true
	docker rmi gunicorn-prometheus-exporter-yaml-test 2>/dev/null || true

# Run linting
lint:
	flake8 src/
	pylint src/

# Format code
format:
	black src/
	isort src/

# Docker-based Redis e2e test (works on Mac/Windows/Linux)
e2e-test-redis-build:
	@echo "Building Docker image for Redis e2e test..."
	docker build -f e2e/fixtures/dockerfiles/default.Dockerfile -t gunicorn-prometheus-exporter-test .

e2e-test-redis-docker: e2e-test-redis-build
	@echo "Running Redis e2e test in Docker container..."
	@echo "This works consistently on Mac, Windows, and Linux!"
	docker run --rm \
		--name gunicorn-prometheus-test \
		-p 8088:8088 \
		-p 9093:9093 \
		-p 6379:6379 \
		gunicorn-prometheus-exporter-test

# Docker-based file storage e2e test (works on Mac/Windows/Linux)
e2e-test-file-storage-build:
	@echo "Building Docker image for file-based storage e2e test..."
	docker build -f e2e/fixtures/dockerfiles/basic.Dockerfile -t gunicorn-prometheus-exporter-basic-test .

e2e-test-file-storage-docker: e2e-test-file-storage-build
	@echo "Running file-based storage e2e test in Docker container..."
	@echo "This works consistently on Mac, Windows, and Linux!"
	docker run --rm \
		--name gunicorn-prometheus-basic-test \
		-p 8088:8088 \
		-p 9093:9093 \
		gunicorn-prometheus-exporter-basic-test

# Docker-based YAML e2e test (works on Mac/Windows/Linux)
e2e-test-yaml-config-build:
	@echo "Building Docker image for YAML e2e test..."
	docker build -f e2e/fixtures/dockerfiles/yaml-simple.Dockerfile -t gunicorn-prometheus-exporter-yaml-test .

e2e-test-yaml-config-docker: e2e-test-yaml-config-build
	@echo "Running YAML configuration e2e test in Docker container..."
	@echo "This works consistently on Mac, Windows, and Linux!"
	integration/test_yaml_config_integration.sh --docker

# Development setup
dev-setup: install
	@echo "Setting up development environment..."
	@echo "Make sure Redis is installed and running"
	@echo "Run 'make quick-test' to test the setup"
