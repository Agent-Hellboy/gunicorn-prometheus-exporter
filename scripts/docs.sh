#!/bin/bash

# Documentation development script for Gunicorn Prometheus Exporter

set -e

echo "Documentation Development Script"
echo "================================"

# Check if we're in the right directory
if [ ! -f "mkdocs.yml" ]; then
    echo "Error: mkdocs.yml not found. Please run this script from the project root."
    exit 1
fi

# Function to install dependencies
install_deps() {
    echo "Installing documentation dependencies..."
    pip install mkdocs mkdocs-material mkdocs-minify-plugin
}

# Function to build documentation
build_docs() {
    echo "Building documentation..."
    mkdocs build
    echo "Documentation built successfully in ./site/"
}

# Function to serve documentation locally
serve_docs() {
    echo "Starting local documentation server..."
    echo "Visit http://127.0.0.1:8000 to view the documentation"
    echo "Press Ctrl+C to stop the server"
    mkdocs serve
}

# Function to clean build artifacts
clean_docs() {
    echo "Cleaning build artifacts..."
    rm -rf site/
    echo "Build artifacts cleaned."
}

# Main script logic
case "${1:-serve}" in
    "install")
        install_deps
        ;;
    "build")
        build_docs
        ;;
    "serve")
        serve_docs
        ;;
    "clean")
        clean_docs
        ;;
    "all")
        install_deps
        build_docs
        serve_docs
        ;;
    *)
        echo "Usage: $0 {install|build|serve|clean|all}"
        echo ""
        echo "Commands:"
        echo "  install  - Install documentation dependencies"
        echo "  build    - Build documentation"
        echo "  serve    - Serve documentation locally (default)"
        echo "  clean    - Clean build artifacts"
        echo "  all      - Install, build, and serve"
        exit 1
        ;;
esac
