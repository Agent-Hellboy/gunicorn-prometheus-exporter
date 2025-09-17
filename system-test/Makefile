# Makefile for Gunicorn Prometheus Exporter

.PHONY: help install test quick-test system-test ci-test clean lint format

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install dependencies"
	@echo "  test         - Run unit tests"
	@echo "  quick-test   - Run quick system test (requires Redis running)"
	@echo "  system-test  - Run full system test"
	@echo "  ci-test      - Run CI-optimized system test"
	@echo "  force-test   - Run test with force kill of existing processes"
	@echo "  clean        - Clean up test artifacts"
	@echo "  lint         - Run linting"
	@echo "  format       - Format code"

# Install dependencies
install:
	pip install -e ../src/
	pip install -r requirements-dev.txt

# Run unit tests
test:
	python -m pytest tests/ -v

# Quick system test (requires Redis running)
quick-test:
	@echo "Running quick system test..."
	@echo "Make sure Redis is running: brew services start redis (macOS) or sudo systemctl start redis (Linux)"
	./system_test.sh --quick --no-redis --force

# Full system test (starts Redis automatically)
system-test:
	@echo "Running full system test..."
	./system_test.sh

# CI-optimized system test (timeout-protected, better for CI)
ci-test:
	@echo "Running CI-optimized system test..."
	./system_test.sh --ci

# Force test (kills existing processes)
force-test:
	@echo "Running force test (kills existing processes)..."
	./system_test.sh --force

# Clean up test artifacts
clean:
	rm -rf test_venv/
	rm -f *.log
	pkill -f "gunicorn.*redis_integration" || true
	pkill -f "redis-server" || true

# Run linting
lint:
	flake8 src/
	pylint src/

# Format code
format:
	black src/
	isort src/

# Development setup
dev-setup: install
	@echo "Setting up development environment..."
	@echo "Make sure Redis is installed and running"
	@echo "Run 'make quick-test' to test the setup"