.PHONY: help version-update test build clean

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

release-prep: ## Prepare release by updating version across all files (usage: make release-prep VERSION=0.3.0)
	@if [ -z "$(VERSION)" ]; then \
		echo "Please specify VERSION. Usage: make release-prep VERSION=0.3.0"; \
		exit 1; \
	fi
	@echo "Preparing release for version $(VERSION)..."
	@python3 scripts/release_readiness.py $(VERSION)

test: ## Run tests
	tox

build: ## Build Docker images locally
	docker build -t gunicorn-prometheus-exporter:latest .
	docker build -f docker/Dockerfile.app -t gunicorn-app:latest .

clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
