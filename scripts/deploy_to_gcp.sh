#!/bin/bash

# Deploy My EuroCoins to Google Cloud Platform
# This script deploys the FastAPI application to Google Cloud Run

set -e  # Exit on any error

echo "🚀 Deploying My EuroCoins to Google Cloud Platform..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if required tools are installed
check_requirements() {
    echo -e "${BLUE}📋 Checking requirements...${NC}"
    
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}❌ Google Cloud CLI (gcloud) is not installed.${NC}"
        echo "Please install it from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed.${NC}"
        echo "Please install Docker from: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    echo -e "${GREEN}✅ All requirements satisfied${NC}"
}

# Set up Google Cloud project
setup_project() {
    echo -e "${BLUE}🔧 Setting up Google Cloud project...${NC}"
    
    # Check if user is authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        echo -e "${YELLOW}🔐 Please authenticate with Google Cloud...${NC}"
        gcloud auth login
    fi
    
    # Get current project or prompt user to set one
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")
    
    if [ -z "$PROJECT_ID" ]; then
        echo -e "${YELLOW}📝 No project set. Please set your Google Cloud project ID:${NC}"
        read -p "Enter your Google Cloud Project ID: " PROJECT_ID
        gcloud config set project $PROJECT_ID
    fi
    
    echo -e "${GREEN}✅ Using project: ${PROJECT_ID}${NC}"
    
    # Enable required APIs
    echo -e "${BLUE}🔌 Enabling required APIs...${NC}"
    gcloud services enable cloudbuild.googleapis.com
    gcloud services enable run.googleapis.com
    gcloud services enable containerregistry.googleapis.com
    gcloud services enable bigquery.googleapis.com
    
    echo -e "${GREEN}✅ APIs enabled${NC}"
}

# Build and deploy using Cloud Build
deploy_application() {
    echo -e "${BLUE}🏗️  Building and deploying application...${NC}"
    
    # Submit build to Cloud Build
    echo -e "${YELLOW}📦 Submitting build to Google Cloud Build...${NC}"
    gcloud builds submit --config cloudbuild.yaml .
    
    echo -e "${GREEN}✅ Application deployed successfully!${NC}"
    
    # Get the service URL
    SERVICE_URL=$(gcloud run services describe my-eurocoins --region=us-central1 --format="value(status.url)")
    
    echo -e "${GREEN}🎉 Deployment complete!${NC}"
    echo -e "${BLUE}🌐 Your application is available at: ${SERVICE_URL}${NC}"
    echo -e "${BLUE}📊 Health check: ${SERVICE_URL}/api/health${NC}"
    echo -e "${BLUE}📖 API docs: ${SERVICE_URL}/api/docs${NC}"
}

# Verify deployment
verify_deployment() {
    echo -e "${BLUE}🔍 Verifying deployment...${NC}"
    
    SERVICE_URL=$(gcloud run services describe my-eurocoins --region=us-central1 --format="value(status.url)" 2>/dev/null || echo "")
    
    if [ -n "$SERVICE_URL" ]; then
        echo -e "${YELLOW}🏥 Checking health endpoint...${NC}"
        if curl -s "${SERVICE_URL}/api/health" | grep -q "healthy"; then
            echo -e "${GREEN}✅ Application is healthy and running!${NC}"
        else
            echo -e "${YELLOW}⚠️  Health check inconclusive, but service is deployed${NC}"
        fi
    else
        echo -e "${RED}❌ Could not retrieve service URL${NC}"
    fi
}

# Main execution
main() {
    echo -e "${GREEN}🪙 My EuroCoins - Google Cloud Deployment${NC}"
    echo "================================================"
    
    check_requirements
    setup_project
    deploy_application
    verify_deployment
    
    echo ""
    echo -e "${GREEN}🎉 Deployment process completed!${NC}"
    echo -e "${BLUE}ℹ️  You can manage your deployment at: https://console.cloud.google.com/run${NC}"
}

# Run main function
main "$@"
