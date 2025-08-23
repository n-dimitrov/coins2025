#!/bin/bash

# Docker Cleanup Script for My EuroCoins
# Stops and removes Docker containers and images

echo "🧹 My EuroCoins - Docker Cleanup"
echo "==============================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Container and image names
CONTAINER_NAME="my-eurocoins-test"
IMAGE_NAME="my-eurocoins-local"

# Stop and remove container if it exists
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    print_status "Stopping and removing container: $CONTAINER_NAME"
    docker stop $CONTAINER_NAME 2>/dev/null || true
    docker rm $CONTAINER_NAME 2>/dev/null || true
    print_success "Container removed"
else
    print_status "No container to remove"
fi

# Remove image if it exists
if docker images --format '{{.Repository}}' | grep -q "^${IMAGE_NAME}$"; then
    print_status "Removing image: $IMAGE_NAME"
    docker rmi $IMAGE_NAME 2>/dev/null || true
    print_success "Image removed"
else
    print_status "No image to remove"
fi

# Clean up any dangling images
print_status "Cleaning up dangling images..."
docker image prune -f

print_success "Docker cleanup completed!"
