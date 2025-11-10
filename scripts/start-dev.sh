#!/bin/bash

# My EuroCoins - Development Mode with Security
# All features enabled, perfect for local development

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

echo "🛠️ My EuroCoins - Development Mode"
echo "=================================="

# Check if we're in the right directory
if [[ ! -f "main.py" ]]; then
    print_warning "Please run from project root: ./scripts/start-dev.sh"
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

# Copy development configuration
print_status "Setting up development environment..."
cp .env.development .env
print_success "Development configuration loaded"

echo ""
echo "🔓 DEVELOPMENT SECURITY SETTINGS:"
echo "   ✅ Admin endpoints: ENABLED"
echo "   ✅ API documentation: ENABLED"
echo "   ✅ Ownership modification: ENABLED"
echo "   ⚠️  Authentication: OPTIONAL (dev mode)"
echo "   🌐 CORS: PERMISSIVE"
echo ""

print_status "Starting FastAPI development server..."
echo "📍 Application: http://localhost:8000"
echo "📚 API Docs:    http://localhost:8000/api/docs"
echo "🔧 Admin Panel: http://localhost:8000/api/admin/coins/view"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Set PYTHONPATH and run with uvicorn
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info