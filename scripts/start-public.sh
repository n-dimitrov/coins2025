#!/bin/bash

# My EuroCoins - Public Read-Only Mode
# Maximum security for public internet deployment

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_security() {
    echo -e "${RED}[SECURITY]${NC} $1"
}

echo "🌐 My EuroCoins - Public Read-Only Mode"
echo "======================================="

# Check if we're in the right directory
if [[ ! -f "main.py" ]]; then
    print_warning "Please run from project root: ./scripts/start-public.sh"
    exit 1
fi

# Activate virtual environment if it exists
if [[ -d ".venv" ]]; then
    print_status "Activating virtual environment..."
    source .venv/bin/activate
elif [[ -d "venv" ]]; then
    print_status "Activating virtual environment..."
    source venv/bin/activate
fi

# Copy public configuration
print_status "Setting up public read-only environment..."
cp .env.public .env
print_success "Public configuration loaded"

echo ""
print_security "🔒 PUBLIC SECURITY SETTINGS:"
echo "   ❌ Admin endpoints: DISABLED"
echo "   ❌ API documentation: DISABLED"
echo "   ❌ Ownership modification: DISABLED"
echo "   ✅ Catalog browsing: ENABLED"
echo "   ✅ Group viewing: ENABLED"
echo "   🔒 Security: MAXIMUM"
echo ""
print_security "🌐 This configuration is SAFE for public internet deployment"
echo ""

print_status "Starting FastAPI production server..."
echo "📍 Application: http://localhost:8080"
echo "🔍 Health:      http://localhost:8080/api/health"
echo "👀 Catalog:     http://localhost:8080/catalog"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Set PYTHONPATH and run with uvicorn on port 8080
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
exec uvicorn main:app --host 0.0.0.0 --port 8080 --log-level warning