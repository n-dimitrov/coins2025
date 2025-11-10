#!/bin/bash

# Deploy My EuroCoins to Google Cloud Platform - Public Site
# This script is a wrapper around the new deploy.sh script for public site deployment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🌐 My EuroCoins - Public Site Deployment to GCP${NC}"
echo "================================================="
echo ""

# Check if we're in the right directory
if [[ ! -f "main.py" ]]; then
    echo -e "${RED}❌ main.py not found. Please run from project root.${NC}"
    exit 1
fi

# Check if the new deploy.sh script exists
if [[ ! -f "scripts/deploy.sh" ]]; then
    echo -e "${RED}❌ scripts/deploy.sh not found. Please ensure the new deployment script exists.${NC}"
    exit 1
fi

# Check if user is authenticated with gcloud
echo -e "${BLUE}🔐 Checking Google Cloud authentication...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${YELLOW}🔐 Please authenticate with Google Cloud...${NC}"
    gcloud auth login
fi

# Get current project or prompt user to set one
PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")

if [ -z "$PROJECT_ID" ]; then
    echo -e "${YELLOW}📝 No project set. Please enter your Google Cloud project ID:${NC}"
    read -p "Enter your Google Cloud Project ID: " PROJECT_ID
    gcloud config set project $PROJECT_ID
fi

echo -e "${GREEN}✅ Using project: ${PROJECT_ID}${NC}"

# Enable required APIs
echo -e "${BLUE}🔌 Enabling required APIs...${NC}"
gcloud services enable run.googleapis.com
gcloud services enable bigquery.googleapis.com

echo -e "${GREEN}✅ APIs enabled${NC}"
echo ""

# Deploy using the new script with public configuration
echo -e "${BLUE}🚀 Deploying public read-only site to Cloud Run...${NC}"
echo -e "${YELLOW}📋 Configuration:${NC}"
echo "   🌐 Type: Cloud Run"
echo "   🔒 Mode: Public (read-only, no admin access)"
echo "   📍 Service: my-eurocoins"
echo "   📍 Region: us-central1"
echo ""

# Call the new deploy script with public configuration
./scripts/deploy.sh \
    --type cloud-run \
    --env public \
    --project "$PROJECT_ID" \
    --service my-eurocoins \
    --region us-central1 \
    --port 8080

echo ""
echo -e "${GREEN}🎉 Public site deployment completed!${NC}"
echo ""
echo -e "${BLUE}🌐 Public Site Features:${NC}"
echo "   ✅ Coin catalog browsing"
echo "   ✅ Group viewing"
echo "   ✅ Public pages accessible"
echo "   🚫 Admin features disabled (secure for public)"
echo "   🚫 API documentation hidden"
echo "   🚫 Ownership modifications blocked"
echo ""
echo -e "${BLUE}ℹ️  You can manage your deployment at: https://console.cloud.google.com/run${NC}"
