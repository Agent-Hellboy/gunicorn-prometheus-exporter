# Makefile for Gunicorn Prometheus Exporter

.PHONY: help install test quick-test system-test ci-test force-test docker-test docker-build basic-test basic-quick-test docker-basic-test docker-basic-build clean lint format

# Default target
help:
	@echo "Available targets:"
	@echo "  install           - Install dependencies"
	@echo "  test              - Run unit tests"
	@echo "  quick-test        - Run quick Redis system test (requires Redis running)"
	@echo "  system-test       - Run full Redis system test"
	@echo "  ci-test           - Run CI-optimized Redis system test"
	@echo "  force-test        - Run Redis test with force kill of existing processes"
	@echo "  basic-test        - Run basic file-based system test"
	@echo "  basic-quick-test  - Run quick basic file-based system test"
	@echo "  docker-test       - Run Redis system test in Docker (works on Mac/Windows/Linux)"
	@echo "  docker-build      - Build Docker image for Redis system test"
	@echo "  docker-basic-test - Run basic file-based system test in Docker"
	@echo "  docker-basic-build - Build Docker image for basic system test"
	@echo "  clean             - Clean up test artifacts"
	@echo "  lint              - Run linting"
	@echo "  format            - Format code"

# Install dependencies
install:
	pip install -e ..
	pip install -r requirements-dev.txt

# Run unit tests
test:
	python -m pytest tests/ -v

# Quick Redis system test (requires Redis running)
quick-test:
	@echo "Running quick Redis system test..."
	@echo "Make sure Redis is running: brew services start redis (macOS) or sudo systemctl start redis (Linux)"
	./system_test_redis_integ.sh --quick --no-redis --force

# Full Redis system test (starts Redis automatically)
system-test:
	@echo "Running full Redis system test..."
	./system_test_redis_integ.sh

# CI-optimized Redis system test (timeout-protected, better for CI)
ci-test:
	@echo "Running CI-optimized Redis system test..."
	./system_test_redis_integ.sh --ci

# Force Redis test (kills existing processes)
force-test:
	@echo "Running force Redis test (kills existing processes)..."
	./system_test_redis_integ.sh --force

# Basic file-based system test
basic-test:
	@echo "Running basic file-based system test..."
	./system_test_basic.sh

# Quick basic file-based system test
basic-quick-test:
	@echo "Running quick basic file-based system test..."
	./system_test_basic.sh --quick

# Clean up test artifacts
clean:
	rm -f *.log
	pkill -f "gunicorn.*redis_integration" || true
	pkill -f "gunicorn.*basic" || true
	pkill -f "redis-server" || true
	rm -rf /tmp/prometheus_multiproc || true
	docker rmi gunicorn-prometheus-exporter-test 2>/dev/null || true
	docker rmi gunicorn-prometheus-exporter-basic-test 2>/dev/null || true

# Run linting
lint:
	flake8 ../src/
	pylint ../src/

# Format code
format:
	black ../src/
	isort ../src/

# Docker-based Redis system test (works on Mac/Windows/Linux)
docker-build:
	@echo "Building Docker image for Redis system test..."
	docker build -f Dockerfile -t gunicorn-prometheus-exporter-test ..

docker-test: docker-build
	@echo "Running Redis system test in Docker container..."
	@echo "This works consistently on Mac, Windows, and Linux!"
	docker run --rm \
		--name gunicorn-prometheus-test \
		-p 8088:8088 \
		-p 9093:9093 \
		-p 6379:6379 \
		gunicorn-prometheus-exporter-test

# Docker-based basic system test (works on Mac/Windows/Linux)
docker-basic-build:
	@echo "Building Docker image for basic system test..."
	docker build -f Dockerfile.basic -t gunicorn-prometheus-exporter-basic-test ..

docker-basic-test: docker-basic-build
	@echo "Running basic file-based system test in Docker container..."
	@echo "This works consistently on Mac, Windows, and Linux!"
	docker run --rm \
		--name gunicorn-prometheus-basic-test \
		-p 8088:8088 \
		-p 9093:9093 \
		gunicorn-prometheus-exporter-basic-test

# Development setup
dev-setup: install
	@echo "Setting up development environment..."
	@echo "Make sure Redis is installed and running"
	@echo "Run 'make quick-test' to test the setup"
