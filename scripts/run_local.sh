#!/bin/bash

# My EuroCoins - Local Development and Testing Script
# This script sets up and runs the application locally with Neon PostgreSQL

set -e  # Exit on any error

echo "🪙 My EuroCoins - Local Development Setup (Neon PostgreSQL)"
echo "==========================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if we're in the right directory
if [[ ! -f "main.py" ]]; then
    print_error "main.py not found. Please run this script from the project root directory."
    exit 1
fi

print_status "Checking prerequisites..."

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    print_success "Python version: $PYTHON_VERSION"
else
    print_error "Python 3 is required but not installed."
    exit 1
fi

# Check if virtual environment exists
if [[ ! -d ".venv" ]]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv .venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source .venv/bin/activate

# Check if requirements are installed
print_status "Installing/checking dependencies..."
pip install -q -r requirements.txt
print_success "Dependencies installed"

# Check environment file
if [[ ! -f ".env" ]]; then
    print_error ".env file not found!"
    print_error "Please create .env file with your Neon connection string:"
    print_error ""
    print_error "DATABASE_TYPE=neon"
    print_error "DATABASE_URL=postgresql://user:password@host/database"
    print_error ""
    print_error "Example: postgresql://neondb_owner:password@ep-xyz.us-east-1.neon.tech/neondb"
    exit 1
else
    print_success ".env file exists"

    # Check if DATABASE_URL is set
    if grep -q "DATABASE_URL=" .env; then
        print_success "DATABASE_URL is configured"
    else
        print_error "DATABASE_URL not found in .env file"
        exit 1
    fi

    # Check if DATABASE_TYPE is set to neon
    if grep -q "DATABASE_TYPE=neon" .env; then
        print_success "DATABASE_TYPE is set to neon"
    else
        print_warning "DATABASE_TYPE might not be set to neon"
    fi
fi

# Test imports
print_status "Testing Python imports..."
python3 -c "
import fastapi
import uvicorn
import psycopg
print('✅ All required packages imported successfully')
" || {
    print_error "Failed to import required packages"
    exit 1
}

print_success "All imports successful"

# Test Neon connection
print_status "Testing Neon database connection..."
python3 -c "
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL')

if not db_url:
    print('❌ DATABASE_URL not found in .env')
    exit(1)

try:
    import psycopg
    conn = psycopg.connect(db_url)
    print('✅ Neon connection successful')
    conn.close()
except Exception as e:
    print(f'❌ Neon connection failed: {e}')
    exit(1)
" || {
    print_error "Neon connection test failed"
    exit 1
}

# Check static files
print_status "Checking static files..."
STATIC_FILES=(
    "static/css/style.css"
    "static/js/app.js"
    "static/js/coins.js"
)

for file in "${STATIC_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        print_success "✓ $file"
    else
        print_error "✗ $file missing"
    fi
done

# Check templates
print_status "Checking templates..."
TEMPLATE_FILES=(
    "templates/base.html"
    "templates/index.html"
    "templates/catalog.html"
    "templates/admin.html"
    "templates/404.html"
    "templates/error.html"
)

for file in "${TEMPLATE_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        print_success "✓ $file"
    else
        print_error "✗ $file missing"
    fi
done

echo ""
echo "🚀 Starting FastAPI Development Server (Neon PostgreSQL)"
echo "========================================================"
echo ""
print_status "Server will be available at:"
echo "  📱 Application: http://localhost:8080"
echo "  🔧 Catalog:     http://localhost:8080/catalog"
echo "  🔍 Health:      http://localhost:8080/api/health"
echo ""
print_status "Database: Neon PostgreSQL"
print_status "Environment: development"
print_status "Press Ctrl+C to stop the server"
echo ""

# Run the FastAPI application
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
exec python main.py
