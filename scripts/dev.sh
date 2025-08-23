#!/bin/bash

# Development setup and run script for My EuroCoins

echo "🪙 My EuroCoins - Development Setup"
echo "=================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Please create one based on .env.example"
    exit 1
fi

# Run the application
echo "🚀 Starting FastAPI application..."
echo "📍 Application will be available at: http://localhost:8000"
echo "📚 API documentation: http://localhost:8000/api/docs"
echo ""
echo "Press Ctrl+C to stop the server"

uvicorn main:app --reload --host 0.0.0.0 --port 8000
