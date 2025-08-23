#!/bin/bash

# My EuroCoins - Local Development and Testing Script
# This script sets up and runs the application locally for testing

set -e  # Exit on any error

echo "🪙 My EuroCoins - Local Development Setup"
echo "========================================"

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
    print_warning ".env file not found. Creating default .env file..."
    cat > .env << EOF
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=coins2025
GOOGLE_APPLICATION_CREDENTIALS=./credentials/service_account.json

# BigQuery Configuration
BQ_DATASET=db
BQ_TABLE=catalog

# Application Settings
APP_ENV=development
LOG_LEVEL=INFO
CACHE_DURATION_MINUTES=5

# Server Configuration
PORT=8000
HOST=0.0.0.0
EOF
    print_success "Default .env file created"
else
    print_success ".env file exists"
fi

# Check service account credentials
if [[ ! -f "credentials/service_account.json" ]]; then
    print_warning "Google Cloud service account credentials not found at credentials/service_account.json"
    print_warning "BigQuery functionality may not work without proper credentials"
else
    print_success "Google Cloud credentials found"
fi

# Test imports
print_status "Testing Python imports..."
python3 -c "
import fastapi
import uvicorn
import jinja2
from google.cloud import bigquery
print('✅ All required packages imported successfully')
" || {
    print_error "Failed to import required packages"
    exit 1
}

print_success "All imports successful"

# Test BigQuery connection (if credentials exist)
if [[ -f "credentials/service_account.json" ]]; then
    print_status "Testing BigQuery connection..."
    python3 -c "
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './credentials/service_account.json'
try:
    from google.cloud import bigquery
    client = bigquery.Client(project='coins2025')
    query = 'SELECT 1 as test'
    result = list(client.query(query).result())
    print('✅ BigQuery connection successful')
except Exception as e:
    print(f'⚠️  BigQuery connection failed: {e}')
" || print_warning "BigQuery test failed - continuing anyway"
fi

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
echo "🚀 Starting FastAPI Development Server"
echo "======================================"
echo ""
print_status "Server will be available at:"
echo "  📱 Application: http://localhost:8000"
echo "  📚 API Docs:    http://localhost:8000/api/docs"
echo "  🔍 Health:      http://localhost:8000/api/health"
echo ""
print_status "Press Ctrl+C to stop the server"
echo ""

# Run the FastAPI application
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info
