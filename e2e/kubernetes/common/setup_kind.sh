#!/bin/bash

# Common Kind cluster setup for Kubernetes tests

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅${NC} $1"
}

# Install kubectl
install_kubectl() {
    print_status "Installing kubectl..."
    # Detect OS and architecture
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        ARCH="amd64"
    elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
        ARCH="arm64"
    fi

    KUBECTL_URL="https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/${OS}/${ARCH}/kubectl"
    print_status "Downloading kubectl from: $KUBECTL_URL"

    curl -LO "$KUBECTL_URL"
    chmod +x kubectl
    sudo mv kubectl /usr/local/bin/
    print_success "kubectl installed for $OS-$ARCH"
}

# Install kind
install_kind() {
    print_status "Installing kind..."
    # Detect OS and architecture
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        ARCH="amd64"
    elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
        ARCH="arm64"
    fi

    KIND_URL="https://kind.sigs.k8s.io/dl/v0.20.0/kind-${OS}-${ARCH}"
    print_status "Downloading kind from: $KIND_URL"

    curl -Lo ./kind "$KIND_URL"
    chmod +x ./kind
    sudo mv ./kind /usr/local/bin/kind
    print_success "kind installed for $OS-$ARCH"
}

# Create kind cluster
create_kind_cluster() {
    local cluster_name="$1"
    local num_workers="${2:-2}"  # Default 2 workers

    print_status "Creating kind cluster: $cluster_name with $num_workers workers..."

    cat <<EOF > kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
EOF

    # Add worker nodes
    for ((i=1; i<=num_workers; i++)); do
        echo "- role: worker" >> kind-config.yaml
    done

    kind create cluster --name "$cluster_name" --config kind-config.yaml --wait 300s
    rm kind-config.yaml

    print_success "Kind cluster created: $cluster_name"
}

# Load Docker images into kind cluster
load_images_to_kind() {
    local cluster_name="$1"
    shift
    local images=("$@")

    for image in "${images[@]}"; do
        print_status "Loading image: $image"
        kind load docker-image "$image" --name "$cluster_name"
    done

    print_success "All images loaded into kind cluster"
}

# Delete kind cluster
delete_kind_cluster() {
    local cluster_name="$1"
    print_status "Deleting kind cluster: $cluster_name..."
    kind delete cluster --name "$cluster_name"
    print_success "Kind cluster deleted"
}
