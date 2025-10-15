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
PROJECT_ROOT="$(cd "$TEST_DIR/../.." && pwd)"
# Use PROJECT_ROOT for all file operations

print_status "INFO" "Testing general Docker environment setup..."

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

# Check if docker compose is available, install if needed
if ! docker compose version > /dev/null 2>&1; then
    print_status "INFO" "docker compose not found. Attempting to install..."

    # Try to install docker-compose-plugin (modern approach)
    if command -v apt-get > /dev/null 2>&1; then
        # Ubuntu/Debian
        print_status "INFO" "Installing docker-compose-plugin via apt..."
        sudo apt-get update -qq
        sudo apt-get install -y docker-compose-plugin
    elif command -v yum > /dev/null 2>&1; then
        # CentOS/RHEL
        print_status "INFO" "Installing docker-compose-plugin via yum..."
        sudo yum install -y docker-compose-plugin
    elif command -v dnf > /dev/null 2>&1; then
        # Fedora
        print_status "INFO" "Installing docker-compose-plugin via dnf..."
        sudo dnf install -y docker-compose-plugin
    elif command -v apk > /dev/null 2>&1; then
        # Alpine Linux
        print_status "INFO" "Installing docker-compose via apk..."
        sudo apk add --no-cache docker-compose
    elif command -v brew > /dev/null 2>&1; then
        # macOS
        print_status "INFO" "Installing docker-compose via brew..."
        brew install docker-compose
    else
        # Fallback: try standalone docker-compose
        print_status "INFO" "Trying standalone docker-compose installation..."
        if command -v curl > /dev/null 2>&1; then
            sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
            sudo chmod +x /usr/local/bin/docker-compose
        else
            print_status "FAIL" "Cannot install docker compose. Please install Docker with compose support manually."
            exit 1
        fi
    fi

    # Verify installation
    if docker compose version > /dev/null 2>&1; then
        print_status "PASS" "docker compose installed successfully"
    elif docker-compose version > /dev/null 2>&1; then
        print_status "PASS" "docker-compose installed successfully"
    else
        print_status "FAIL" "docker compose installation failed"
        exit 1
    fi
else
    print_status "PASS" "docker compose is available"
fi

# Check if basic project files exist
basic_files=(
    "Dockerfile"
    "docker-compose.yml"
    "pyproject.toml"
    "README.md"
)

for file in "${basic_files[@]}"; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        print_status "PASS" "Required file exists: $file"
    else
        print_status "FAIL" "Required file missing: $file"
        exit 1
    fi
done

# Test Docker build
print_status "INFO" "Testing main Dockerfile build..."
cd "$PROJECT_ROOT"
if docker build -t gunicorn-prometheus-exporter-sidecar:test . > /dev/null 2>&1; then
    print_status "PASS" "Main Docker image builds successfully"
else
    print_status "FAIL" "Main Docker image build failed"
    exit 1
fi

# Test docker compose syntax
print_status "INFO" "Testing docker compose syntax..."
cd "$PROJECT_ROOT"
if docker compose config > /dev/null 2>&1; then
    print_status "PASS" "docker compose configuration is valid"
elif docker-compose config > /dev/null 2>&1; then
    print_status "PASS" "docker-compose configuration is valid"
else
    print_status "FAIL" "docker compose configuration is invalid"
    exit 1
fi

# Test basic container run
print_status "INFO" "Testing basic container execution..."
if docker run --rm gunicorn-prometheus-exporter-sidecar:test help > /dev/null 2>&1; then
    print_status "PASS" "Container runs successfully"
else
    print_status "FAIL" "Container execution failed"
    exit 1
fi

# Cleanup test image
docker rmi gunicorn-prometheus-exporter-sidecar:test > /dev/null 2>&1 || true

print_status "PASS" "All Docker environment tests passed!"
print_status "INFO" "Docker environment is ready for E2E testing"
print_status "INFO" "You can now run the other E2E tests: test_standalone_images.sh, test_docker_compose.sh, test_sidecar_redis.sh"
