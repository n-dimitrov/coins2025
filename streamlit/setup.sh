#!/bin/bash
# Setup script for BigQuery coin catalog import

echo "Setting up BigQuery coin catalog import..."

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Verify service account file exists
if [ ! -f "service_account.json" ]; then
    echo "WARNING: service_account.json not found!"
    echo "Please ensure you have a valid Google Cloud service account file."
    echo "The service account needs BigQuery Data Editor and BigQuery Job User permissions."
    exit 1
fi

# Verify data file exists
if [ ! -f "data/catalog.csv" ]; then
    echo "ERROR: data/catalog.csv not found!"
    echo "Please ensure the catalog data file exists."
    exit 1
fi

echo "Setup complete!"
echo ""
echo "Usage:"
echo "  python import_db.py          # Append new data to existing table"
echo "  python import_db.py --replace # Replace all existing data"
echo ""
echo "Make sure your service account has the following permissions:"
echo "  - BigQuery Data Editor"
echo "  - BigQuery Job User"
echo "  - BigQuery Data Viewer"
