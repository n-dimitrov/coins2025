#!/bin/bash

# Docker Local Testing Script for My EuroCoins
# Tests Docker build and container functionality

set -e

echo "🐳 My EuroCoins - Docker Local Testing"
echo "====================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

print_success "Docker is installed and running"

# Docker image name
IMAGE_NAME="my-eurocoins-local"
CONTAINER_NAME="my-eurocoins-test"

# Cleanup any existing container
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    print_status "Removing existing container..."
    docker rm -f $CONTAINER_NAME
fi

# Remove existing image if it exists
if docker images --format '{{.Repository}}' | grep -q "^${IMAGE_NAME}$"; then
    print_status "Removing existing image..."
    docker rmi $IMAGE_NAME
fi

# Build Docker image
print_status "Building Docker image..."
docker build -t $IMAGE_NAME . || {
    print_error "Docker build failed"
    exit 1
}

print_success "Docker image built successfully"

# Check if credentials exist for mounting
MOUNT_CREDENTIALS=""
if [[ -f "credentials/service_account.json" ]]; then
    MOUNT_CREDENTIALS="-v $(pwd)/credentials:/app/credentials"
    print_status "Will mount credentials for BigQuery access"
else
    print_warning "No credentials found - BigQuery functionality may not work"
fi

# Run Docker container
print_status "Starting Docker container..."
docker run -d \
    --name $CONTAINER_NAME \
    -p 8080:8000 \
    -e APP_ENV=development \
    -e GOOGLE_CLOUD_PROJECT=coins2025 \
    -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service_account.json \
    $MOUNT_CREDENTIALS \
    $IMAGE_NAME || {
    print_error "Failed to start Docker container"
    exit 1
}

print_success "Docker container started"

# Wait for the application to start
print_status "Waiting for application to start..."
sleep 5

# Test health endpoint
print_status "Testing health endpoint..."
for i in {1..10}; do
    if curl -s http://localhost:8080/api/health > /dev/null; then
        print_success "Health endpoint responding"
        break
    else
        if [[ $i -eq 10 ]]; then
            print_error "Health endpoint not responding after 10 attempts"
            docker logs $CONTAINER_NAME
            docker rm -f $CONTAINER_NAME
            exit 1
        fi
        sleep 2
    fi
done

# Test API endpoints
print_status "Testing API endpoints..."

# Test health endpoint
HEALTH_RESPONSE=$(curl -s http://localhost:8080/api/health)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    print_success "✓ Health endpoint working"
else
    print_warning "✗ Health endpoint response: $HEALTH_RESPONSE"
fi

# Test homepage
if curl -s http://localhost:8080/ | grep -q "My EuroCoins"; then
    print_success "✓ Homepage loading"
else
    print_warning "✗ Homepage not loading properly"
fi

# Test API docs
if curl -s http://localhost:8080/api/docs | grep -q "swagger"; then
    print_success "✓ API documentation available"
else
    print_warning "✗ API documentation not loading"
fi

# Show container logs (last 20 lines)
echo ""
print_status "Recent container logs:"
docker logs --tail 20 $CONTAINER_NAME

echo ""
print_success "Docker container is running successfully!"
echo ""
echo "🌐 Access URLs:"
echo "  📱 Application:    http://localhost:8080"
echo "  📚 API Docs:       http://localhost:8080/api/docs"
echo "  🔍 Health Check:   http://localhost:8080/api/health"
echo ""
echo "🔧 Container Management:"
echo "  View logs:    docker logs $CONTAINER_NAME"
echo "  Stop:         docker stop $CONTAINER_NAME"
echo "  Remove:       docker rm $CONTAINER_NAME"
echo ""
echo "⏹️  To stop and cleanup:"
echo "  ./scripts/docker_cleanup.sh"
echo ""

# Ask if user wants to keep it running
echo -n "Keep container running? (y/N): "
read -r KEEP_RUNNING

if [[ ! "$KEEP_RUNNING" =~ ^[Yy]$ ]]; then
    print_status "Stopping and removing container..."
    docker stop $CONTAINER_NAME
    docker rm $CONTAINER_NAME
    print_success "Container stopped and removed"
else
    print_status "Container will keep running in the background"
    print_status "Use 'docker stop $CONTAINER_NAME' to stop it later"
fi
