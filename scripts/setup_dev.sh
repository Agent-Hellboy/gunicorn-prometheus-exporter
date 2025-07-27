#!/bin/bash

# Development setup script for gunicorn-prometheus-exporter
# This script installs development dependencies and sets up pre-commit hooks

set -e

echo "🔧 Setting up development environment for gunicorn-prometheus-exporter"
echo "=================================================================="

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo " Error: pyproject.toml not found. Please run this script from the project root."
    exit 1
fi

echo " Installing development dependencies..."
pip install -e ".[dev]"

echo "Installing pre-commit hooks..."
pre-commit install

echo " Setting up tox environments..."
tox --notest

echo ""
echo " Development environment setup complete!"
echo ""
echo "Available commands:"
echo "  tox -e lint          # Run all linting and code quality checks"
echo "  tox -e py39          # Run tests with Python 3.9"
echo "  tox -e py310         # Run tests with Python 3.10"
echo "  tox -e py311         # Run tests with Python 3.11"
echo "  tox -e py312         # Run tests with Python 3.12"
echo "  tox -e py313         # Run tests with Python 3.13"
echo "  pre-commit run --all-files  # Run all pre-commit hooks"
echo "  pre-commit run       # Run pre-commit hooks on staged files"
echo ""
echo "Pre-commit hooks will now run automatically on every commit!"
