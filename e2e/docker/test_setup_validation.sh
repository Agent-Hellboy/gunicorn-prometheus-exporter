#!/bin/bash

# Test script to verify Docker setup for YAML configuration testing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✓ PASS${NC}: $message"
    elif [ "$status" = "FAIL" ]; then
        echo -e "${RED}✗ FAIL${NC}: $message"
    elif [ "$status" = "INFO" ]; then
        echo -e "${YELLOW}ℹ INFO${NC}: $message"
    fi
}

# Test configuration
TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$TEST_DIR/.." && pwd)"
# Use PROJECT_ROOT for all file operations

print_status "INFO" "Testing Docker setup for YAML configuration..."

# Check if Docker is available
if ! command -v docker > /dev/null 2>&1; then
    print_status "FAIL" "Docker not found. Please install Docker."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_status "FAIL" "Docker is not running. Please start Docker."
    exit 1
fi

print_status "PASS" "Docker is available and running"

# Check if docker-compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    print_status "FAIL" "docker-compose not found. Please install docker-compose."
    exit 1
fi

print_status "PASS" "docker-compose is available"

# Check if required files exist
required_files=(
    "Dockerfile.yaml-test"
    "docker-compose.yaml-test.yml"
    "test_app.py"
    "gunicorn.yaml.conf.py"
    "prometheus.yml"
    "test_configs/basic.yml"
    "test_configs/redis.yml"
    "test_configs/ssl.yml"
)

for file in "${required_files[@]}"; do
    if [ -f "$SYSTEM_TEST_DIR/$file" ]; then
        print_status "PASS" "Required file exists: $file"
    else
        print_status "FAIL" "Required file missing: $file"
        exit 1
    fi
done

# Test Docker build
print_status "INFO" "Testing Docker build..."
cd "$PROJECT_ROOT"
if docker build -f "$SYSTEM_TEST_DIR/Dockerfile.yaml-test" -t gunicorn-yaml-test . > /dev/null 2>&1; then
    print_status "PASS" "Docker image builds successfully"
else
    print_status "FAIL" "Docker image build failed"
    exit 1
fi

# Test docker-compose syntax
print_status "INFO" "Testing docker-compose syntax..."
cd "$SYSTEM_TEST_DIR"
if docker-compose -f docker-compose.yaml-test.yml config > /dev/null 2>&1; then
    print_status "PASS" "docker-compose configuration is valid"
else
    print_status "FAIL" "docker-compose configuration is invalid"
    exit 1
fi

# Cleanup test image
docker rmi gunicorn-yaml-test > /dev/null 2>&1 || true

print_status "PASS" "All Docker setup tests passed!"
print_status "INFO" "You can now run: ../../integration/test_yaml_config.sh --docker --quick"
