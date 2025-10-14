# Makefile for Gunicorn Prometheus Exporter

.PHONY: all help install unit-test test integration-test-redis-quick integration-test-redis-full integration-test-redis-ci integration-test-redis-force integration-test-file-storage integration-test-file-storage-quick e2e-test-redis-docker e2e-test-redis-build e2e-test-file-storage-docker e2e-test-file-storage-build integration-test-yaml-config integration-test-yaml-config-quick e2e-test-yaml-config-docker e2e-test-yaml-config-build clean lint format dev-setup

all: help

# Default target
help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage: make \033[36m<target>\033[0m\n\nTargets:\n"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-35s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# Install dependencies
install: ## Install dependencies
	pip install -e ..
	pip install -r ../requirements-dev.txt

# Run unit tests
unit-test: ## Run unit tests
	python -m pytest ../tests/ -v

# Alias for convenience and tooling compatibility
test: unit-test ## Alias for unit-test

# Quick Redis integration test (requires Redis running)
integration-test-redis-quick: ## Run quick Redis integration test (requires Redis running)
	@echo "Running quick Redis integration test..."
	@echo "Make sure Redis is running: brew services start redis (macOS) or sudo systemctl start redis (Linux)"
	../integration/test_redis_integration.sh --quick --no-redis --force

# Full Redis integration test (starts Redis automatically)
integration-test-redis-full: ## Run full Redis integration test (auto-starts Redis)
	@echo "Running full Redis integration test..."
	../integration/test_redis_integration.sh

# CI-optimized Redis integration test (timeout-protected, better for CI)
integration-test-redis-ci: ## Run CI-optimized Redis integration test
	@echo "Running CI-optimized Redis integration test..."
	../integration/test_redis_integration.sh --ci

# Force Redis test (kills existing processes)
integration-test-redis-force: ## Run Redis test with force kill of existing processes
	@echo "Running force Redis test (kills existing processes)..."
	../integration/test_redis_integration.sh --force

# File-based storage integration test
integration-test-file-storage: ## Run file-based storage integration test
	@echo "Running file-based storage integration test..."
	../integration/test_file_storage_integration.sh

# Quick file-based storage integration test
integration-test-file-storage-quick: ## Run quick file-based storage integration test
	@echo "Running quick file-based storage integration test..."
	../integration/test_file_storage_integration.sh --quick

# YAML configuration integration test
integration-test-yaml-config: ## Run YAML configuration integration test
	@echo "Running YAML configuration integration test..."
	../integration/test_yaml_config_integration.sh

# Quick YAML configuration integration test
integration-test-yaml-config-quick: ## Run quick YAML configuration integration test
	@echo "Running quick YAML configuration integration test..."
	../integration/test_yaml_config_integration.sh --quick

# Clean up test artifacts
clean: ## Clean up test artifacts
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
lint: ## Run linting
	flake8 src/
	pylint src/

# Format code
format: ## Format code
	black src/
	isort src/

# Docker-based Redis e2e test (works on Mac/Windows/Linux)
e2e-test-redis-build: ## Build Docker image for Redis e2e test
	@echo "Building Docker image for Redis e2e test..."
	docker build -f fixtures/dockerfiles/default.Dockerfile -t gunicorn-prometheus-exporter-test ..

e2e-test-redis-docker: e2e-test-redis-build ## Run Redis e2e test in Docker (works on Mac/Windows/Linux)
	@echo "Running Redis e2e test in Docker container..."
	@echo "This works consistently on Mac, Windows, and Linux!"
	docker run --rm \
		--name gunicorn-prometheus-test \
		-p 8088:8088 \
		-p 9093:9093 \
		-p 6379:6379 \
		gunicorn-prometheus-exporter-test

# Docker-based file storage e2e test (works on Mac/Windows/Linux)
e2e-test-file-storage-build: ## Build Docker image for file-based storage e2e test
	@echo "Building Docker image for file-based storage e2e test..."
	docker build -f fixtures/dockerfiles/basic.Dockerfile -t gunicorn-prometheus-exporter-basic-test ..

e2e-test-file-storage-docker: e2e-test-file-storage-build ## Run file-based storage e2e test in Docker
	@echo "Running file-based storage e2e test in Docker container..."
	@echo "This works consistently on Mac, Windows, and Linux!"
	docker run --rm \
		--name gunicorn-prometheus-basic-test \
		-p 8088:8088 \
		-p 9093:9093 \
		gunicorn-prometheus-exporter-basic-test

# Docker-based YAML e2e test (works on Mac/Windows/Linux)
e2e-test-yaml-config-build: ## Build Docker image for YAML configuration e2e test
	@echo "Building Docker image for YAML e2e test..."
	docker build -f fixtures/dockerfiles/yaml-simple.Dockerfile -t gunicorn-prometheus-exporter-yaml-test ..

e2e-test-yaml-config-docker: e2e-test-yaml-config-build ## Run YAML configuration e2e test in Docker
	@echo "Running YAML configuration e2e test in Docker container..."
	@echo "This works consistently on Mac, Windows, and Linux!"
	../integration/test_yaml_config_integration.sh --docker

# Quick test (runs unit tests only)
quick-test: ## Quick test (unit tests only)
	@echo "Running quick test (unit tests only)..."
	python -m pytest ../tests/ -v --tb=short

# Development setup
dev-setup: install ## Set up development environment
	@echo "Setting up development environment..."
	@echo "Make sure Redis is installed and running"
	@echo "Run 'make quick-test' to test the setup"
