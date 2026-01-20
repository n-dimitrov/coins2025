#!/bin/bash

# Deploy My EuroCoins to Google Cloud Platform - Production
# This is a simplified wrapper for production deployment with preset settings

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 My EuroCoins - Production Deployment to Google Cloud${NC}"
echo "============================================================"
echo ""

# Production settings (hardcoded)
DEPLOYMENT_TYPE="cloud-run"
PROJECT_ID="coins2025"
SERVICE_NAME="my-eurocoins"
REGION="us-central1"
PORT="8080"
ENVIRONMENT="production"

# Check if we're in the right directory
if [[ ! -f "main.py" ]]; then
    echo -e "${RED}❌ main.py not found. Please run from project root.${NC}"
    exit 1
fi

# Check if the deploy.sh script exists
if [[ ! -f "scripts/deploy.sh" ]]; then
    echo -e "${RED}❌ scripts/deploy.sh not found.${NC}"
    exit 1
fi

# Check if user is authenticated with gcloud
echo -e "${BLUE}🔐 Checking Google Cloud authentication...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${YELLOW}🔐 Please authenticate with Google Cloud...${NC}"
    gcloud auth login
fi

# Verify project exists
echo -e "${BLUE}📋 Verifying Google Cloud project...${NC}"
if ! gcloud projects describe $PROJECT_ID &>/dev/null; then
    echo -e "${RED}❌ Project '$PROJECT_ID' not found or not accessible${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Using project: ${PROJECT_ID}${NC}"
echo ""

# Enable required APIs
echo -e "${BLUE}🔌 Enabling required Google Cloud APIs...${NC}"
gcloud services enable run.googleapis.com --project=$PROJECT_ID
gcloud services enable cloudbuild.googleapis.com --project=$PROJECT_ID

echo -e "${GREEN}✅ APIs enabled${NC}"
echo ""

# Show deployment configuration
echo -e "${BLUE}📋 Production Deployment Configuration:${NC}"
echo "   📦 Type:        Cloud Run"
echo "   🌍 Environment: Production"
echo "   ☁️  Project:     $PROJECT_ID"
echo "   📍 Service:     $SERVICE_NAME"
echo "   📍 Region:      $REGION"
echo "   🚪 Port:        $PORT"
echo ""
echo -e "${YELLOW}⚠️  Admin Access: COMPLETELY DISABLED${NC}"
echo "   • No admin endpoints"
echo "   • No API documentation"
echo "   • Strict CORS"
echo "   • Production security enabled"
echo ""

echo ""
echo -e "${BLUE}🚀 Starting production deployment...${NC}"
echo ""

# Call deploy.sh with production settings
./scripts/deploy.sh \
    --type $DEPLOYMENT_TYPE \
    --project "$PROJECT_ID" \
    --service $SERVICE_NAME \
    --region $REGION \
    --port $PORT

echo ""
echo -e "${GREEN}🎉 Production deployment completed!${NC}"
echo ""
echo -e "${BLUE}📊 Deployment Information:${NC}"
echo "   Service URL: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME?project=$PROJECT_ID"
echo ""
echo -e "${BLUE}🔍 Monitor Your Deployment:${NC}"
echo "   View logs:"
echo "   gcloud logging read 'resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$SERVICE_NAME\"' --limit 50 --project=$PROJECT_ID"
echo ""
echo "   Check service status:"
echo "   gcloud run services describe $SERVICE_NAME --region $REGION --project=$PROJECT_ID"
echo ""
echo "   Test health endpoint:"
echo "   curl https://\$(gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)' --project=$PROJECT_ID)/api/health"
echo ""
echo -e "${GREEN}✅ Production deployment ready!${NC}"
