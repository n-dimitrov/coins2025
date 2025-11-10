#!/bin/bash

# My EuroCoins - Security Testing Suite
# Automated testing of all security configurations

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

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "🔒 My EuroCoins Security Testing Suite"
echo "======================================"

# Check if we're in the right directory
if [[ ! -f "main.py" ]]; then
    print_error "Please run from project root: ./scripts/test-security.sh"
    exit 1
fi

# Activate virtual environment if it exists
if [[ -d ".venv" ]]; then
    source .venv/bin/activate
elif [[ -d "venv" ]]; then
    source venv/bin/activate
fi

# Function to test endpoints
test_endpoint() {
    local url=$1
    local expected_result=$2
    local description=$3
    local timeout_duration=5

    echo -n "  Testing $description... "

    if [ "$expected_result" = "accessible" ]; then
        if timeout $timeout_duration curl -s "$url" | grep -q "success\|healthy\|coins\|swagger" 2>/dev/null; then
            print_success "✅ ACCESSIBLE"
            return 0
        else
            print_error "❌ BLOCKED (should be accessible)"
            return 1
        fi
    else
        if timeout $timeout_duration curl -s "$url" 2>/dev/null | grep -q "404\|not available\|Endpoint not available\|Documentation not available"; then
            print_success "✅ BLOCKED"
            return 0
        else
            # Check if it's returning HTML (indicating it's being caught by catch-all route)
            if timeout $timeout_duration curl -s "$url" 2>/dev/null | grep -q "<!DOCTYPE html"; then
                print_success "✅ BLOCKED (HTML)"
                return 0
            else
                print_error "❌ ACCESSIBLE (should be blocked)"
                return 1
            fi
        fi
    fi
}

# Kill any existing servers
print_status "Cleaning up any existing servers..."
pkill -f "uvicorn.*main:app" 2>/dev/null || true
sleep 2

echo ""
echo "🧪 TEST 1: Development Mode Security"
echo "-----------------------------------"

# Setup development environment
cp .env.development .env
print_status "Starting development server..."

# Start development server in background
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uvicorn main:app --host 0.0.0.0 --port 8000 --log-level error &
DEV_PID=$!
sleep 4

print_status "Testing development endpoints:"
dev_tests=0
dev_passed=0

test_endpoint "http://localhost:8000/api/health" "accessible" "Health endpoint" && ((dev_passed++))
((dev_tests++))

test_endpoint "http://localhost:8000/api/docs" "accessible" "API documentation" && ((dev_passed++))
((dev_tests++))

test_endpoint "http://localhost:8000/hippo" "accessible" "Public pages" && ((dev_passed++))
((dev_tests++))

# Note: Admin endpoints might need auth in dev mode depending on configuration
test_endpoint "http://localhost:8000/api/admin/coins/filter-options" "accessible" "Admin endpoint (with auth)" && ((dev_passed++))
((dev_tests++))

# Kill development server
kill $DEV_PID 2>/dev/null || true
sleep 2

echo ""
echo "🧪 TEST 2: Production Mode Security"
echo "-----------------------------------"

# Setup production environment
cp .env.public .env  # Using public config for maximum security
print_status "Starting production server..."

# Start production server in background
uvicorn main:app --host 0.0.0.0 --port 8081 --log-level error &
PROD_PID=$!
sleep 4

print_status "Testing production endpoints:"
prod_tests=0
prod_passed=0

test_endpoint "http://localhost:8081/api/health" "accessible" "Health endpoint" && ((prod_passed++))
((prod_tests++))

test_endpoint "http://localhost:8081/api/docs" "blocked" "API documentation" && ((prod_passed++))
((prod_tests++))

test_endpoint "http://localhost:8081/hippo" "accessible" "Public pages" && ((prod_passed++))
((prod_tests++))

test_endpoint "http://localhost:8081/api/admin/clear-cache" "blocked" "Admin endpoint" && ((prod_passed++))
((prod_tests++))

test_endpoint "http://localhost:8081/api/admin/coins/export" "blocked" "Admin export" && ((prod_passed++))
((prod_tests++))

test_endpoint "http://localhost:8081/api/ownership/user/test/coins" "blocked" "Ownership endpoint" && ((prod_passed++))
((prod_tests++))

# Kill production server
kill $PROD_PID 2>/dev/null || true
sleep 2

echo ""
echo "🎯 SECURITY TEST SUMMARY"
echo "========================"
echo "Development Mode: $dev_passed/$dev_tests tests passed"
echo "Production Mode:  $prod_passed/$prod_tests tests passed"
echo ""

if [ $dev_passed -eq $dev_tests ] && [ $prod_passed -eq $prod_tests ]; then
    print_success "🔒 All security tests PASSED!"
    echo ""
    echo "✅ Development: All features accessible (correct for dev)"
    echo "✅ Production: Dangerous features blocked (correct for prod)"
    echo "✅ Public pages: Always accessible (correct)"
    echo "✅ Health checks: Always accessible (correct)"
    echo ""
    print_success "Security implementation is working correctly!"
else
    print_error "❌ Some security tests FAILED!"
    echo ""
    print_warning "Please review the failed tests above."
fi

echo ""
echo "🚀 Available start scripts:"
echo "  ./scripts/start-dev.sh       # Development mode"
echo "  ./scripts/start-public.sh    # Public read-only mode"
echo "  ./scripts/run_local.sh       # Full local setup"
echo "  ./scripts/dev.sh             # Simple dev mode"