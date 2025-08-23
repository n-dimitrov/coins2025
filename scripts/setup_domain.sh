#!/bin/bash

# Custom Domain Setup Script for myeurocoins.org
# This script helps configure your custom domain with Google Cloud Run

set -e

echo "🌐 Setting up custom domain: myeurocoins.org"
echo "=============================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📋 Current Cloud Run service:${NC}"
SERVICE_URL=$(gcloud run services describe my-eurocoins --region=us-central1 --format="value(status.url)")
echo "Current URL: $SERVICE_URL"

echo -e "\n${YELLOW}📝 Step 1: Configure DNS at Namecheap${NC}"
echo "1. Login to Namecheap Dashboard"
echo "2. Go to Domain List → Manage myeurocoins.org"
echo "3. Go to 'Advanced DNS' tab"
echo "4. Delete existing A and CNAME records"
echo "5. Add these DNS records:"
echo ""
echo "Type: A, Host: @, Value: 216.239.32.21, TTL: Automatic"
echo "Type: A, Host: @, Value: 216.239.34.21, TTL: Automatic" 
echo "Type: A, Host: @, Value: 216.239.36.21, TTL: Automatic"
echo "Type: A, Host: @, Value: 216.239.38.21, TTL: Automatic"
echo "Type: CNAME, Host: www, Value: ghs.googlehosted.com., TTL: Automatic"
echo ""

read -p "Press Enter when DNS records are configured..."

echo -e "\n${YELLOW}📝 Step 2: Verify domain ownership${NC}"
echo "Opening Google Search Console for domain verification..."

# Open Google Search Console
open "https://search.google.com/search-console/welcome?authuser=0&new_domain_name=myeurocoins.org&pli=1" 2>/dev/null || echo "Please open: https://search.google.com/search-console/welcome"

echo ""
echo "In Google Search Console:"
echo "1. Select 'URL prefix' method"
echo "2. Enter: https://myeurocoins.org"
echo "3. Choose 'Domain name provider' method"
echo "4. Add the TXT record to your Namecheap DNS"
echo ""

read -p "Press Enter when domain is verified in Search Console..."

echo -e "\n${YELLOW}📝 Step 3: Create domain mapping${NC}"
echo "Creating domain mapping in Google Cloud..."

# Try to create domain mapping
if gcloud beta run domain-mappings create --service my-eurocoins --domain myeurocoins.org --region us-central1; then
    echo -e "${GREEN}✅ Domain mapping created successfully!${NC}"
else
    echo -e "${RED}❌ Domain mapping failed. Domain might not be verified yet.${NC}"
    echo "Wait 5-10 minutes and try again:"
    echo "gcloud beta run domain-mappings create --service my-eurocoins --domain myeurocoins.org --region us-central1"
fi

echo -e "\n${YELLOW}📝 Step 4: Add www subdomain${NC}"
echo "Creating www subdomain mapping..."

if gcloud beta run domain-mappings create --service my-eurocoins --domain www.myeurocoins.org --region us-central1; then
    echo -e "${GREEN}✅ WWW subdomain mapping created successfully!${NC}"
else
    echo -e "${YELLOW}⚠️ WWW subdomain mapping failed. Try manually later.${NC}"
fi

echo -e "\n${GREEN}🎉 Domain setup process completed!${NC}"
echo ""
echo "Your application will be available at:"
echo "• https://myeurocoins.org"
echo "• https://www.myeurocoins.org"
echo ""
echo "Note: DNS propagation can take 24-48 hours worldwide"
echo "You can check propagation status at: https://dnschecker.org"

echo -e "\n${BLUE}📊 Checking current domain mappings:${NC}"
gcloud beta run domain-mappings list --region us-central1

echo -e "\n${BLUE}🔍 Testing domain (may take a few minutes):${NC}"
echo "Testing myeurocoins.org..."
curl -s -I "https://myeurocoins.org" | head -1 || echo "Domain not ready yet"
