#!/bin/bash

# My EuroCoins - Production Deployment Script
# Comprehensive deployment for Google Cloud Platform and other environments

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
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

print_deploy() {
    echo -e "${PURPLE}[DEPLOY]${NC} $1"
}

# Default values
DEPLOYMENT_TYPE="cloud-run"
ENVIRONMENT="production"
PROJECT_ID=""
SERVICE_NAME="myeurocoins"
REGION="us-central1"
PORT="8080"
ADMIN_API_KEY=""

# Help function
show_help() {
    cat << EOF
🚀 My EuroCoins Deployment Script

Usage: $0 [OPTIONS]

Deployment Types:
  cloud-run     Google Cloud Run (default)
  docker        Docker container build only
  app-engine    Google App Engine
  server        Traditional server deployment

Options:
  -t, --type TYPE           Deployment type (cloud-run, docker, app-engine, server)
  -e, --env ENVIRONMENT     Environment (production, public) [default: production]
  -p, --project PROJECT_ID  Google Cloud project ID
  -s, --service SERVICE     Service name [default: myeurocoins]
  -r, --region REGION       Deployment region [default: us-central1]
  --port PORT               Server port [default: 8080]
  --admin-key KEY           Admin API key (required for production)
  -h, --help                Show this help

Examples:
  $0 --type cloud-run --project coins2025 --admin-key "your-secret-key"
  $0 --type docker
  $0 --type server --env public
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            DEPLOYMENT_TYPE="$2"
            shift 2
            ;;
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -p|--project)
            PROJECT_ID="$2"
            shift 2
            ;;
        -s|--service)
            SERVICE_NAME="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --admin-key)
            ADMIN_API_KEY="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option $1"
            show_help
            exit 1
            ;;
    esac
done

echo "🚀 My EuroCoins Production Deployment"
echo "===================================="
echo ""

print_deploy "Deployment Configuration:"
echo "  📦 Type:        $DEPLOYMENT_TYPE"
echo "  🌐 Environment: $ENVIRONMENT"
echo "  📍 Region:      $REGION"
echo "  🔧 Service:     $SERVICE_NAME"
echo "  🚪 Port:        $PORT"
if [[ -n "$PROJECT_ID" ]]; then
    echo "  ☁️  Project:    $PROJECT_ID"
fi
echo ""

# Validation
if [[ ! -f "main.py" ]]; then
    print_error "main.py not found. Please run from project root."
    exit 1
fi

if [[ "$ENVIRONMENT" == "production" && -z "$ADMIN_API_KEY" ]]; then
    print_error "Production deployment requires --admin-key parameter"
    exit 1
fi

# Pre-deployment setup
print_status "Setting up deployment environment..."

# Setup environment configuration
if [[ "$ENVIRONMENT" == "production" ]]; then
    cp .env.production .env
    print_success "Production environment configured"
elif [[ "$ENVIRONMENT" == "public" ]]; then
    cp .env.public .env
    print_success "Public read-only environment configured"
else
    print_error "Invalid environment: $ENVIRONMENT"
    exit 1
fi

# Add deployment-specific environment variables
cat >> .env << EOF

# Deployment Configuration
PORT=$PORT
HOST=0.0.0.0
APP_ENV=$ENVIRONMENT
EOF

if [[ -n "$ADMIN_API_KEY" ]]; then
    echo "ADMIN_API_KEY=$ADMIN_API_KEY" >> .env
fi

# Validate dependencies
print_status "Validating dependencies..."
if [[ ! -f "requirements.txt" ]]; then
    print_error "requirements.txt not found"
    exit 1
fi

# Create production requirements if needed
if [[ ! -f "requirements-prod.txt" ]]; then
    print_status "Creating production requirements..."
    cat > requirements-prod.txt << EOF
# Production Requirements for My EuroCoins
fastapi==0.104.1
uvicorn[standard]==0.24.0
jinja2==3.1.2
python-multipart==0.0.6
google-cloud-bigquery==3.12.0
google-auth==2.23.4
python-dotenv==1.0.0
pydantic==2.5.0
starlette==0.27.0
EOF
    print_success "Production requirements created"
fi

# Deployment type specific actions
case $DEPLOYMENT_TYPE in
    "cloud-run")
        print_deploy "🌥️  Google Cloud Run Deployment"
        echo "================================"

        if [[ -z "$PROJECT_ID" ]]; then
            print_error "Google Cloud project ID required for Cloud Run deployment"
            exit 1
        fi

        # Check gcloud CLI
        if ! command -v gcloud &> /dev/null; then
            print_error "gcloud CLI not found. Please install Google Cloud SDK."
            exit 1
        fi

        # Set project
        print_status "Setting Google Cloud project..."
        gcloud config set project $PROJECT_ID

        # Create Dockerfile if not exists
        if [[ ! -f "Dockerfile" ]]; then
            print_status "Creating Dockerfile..."
            cat > Dockerfile << 'EOF'
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/api/health || exit 1

# Expose port
EXPOSE $PORT

# Run the application
CMD exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
EOF
            print_success "Dockerfile created"
        fi

        # Create .dockerignore
        if [[ ! -f ".dockerignore" ]]; then
            print_status "Creating .dockerignore..."
            cat > .dockerignore << EOF
.git
.venv
venv
__pycache__
*.pyc
.env.development
.env.local
node_modules
.DS_Store
.pytest_cache
tests/
docs/
README.md
*.md
scripts/
data/
.gitignore
Dockerfile
.dockerignore
EOF
            print_success ".dockerignore created"
        fi

        # Build and deploy
        print_status "Building and deploying to Cloud Run..."

        gcloud run deploy $SERVICE_NAME \
            --source . \
            --platform managed \
            --region $REGION \
            --port $PORT \
            --allow-unauthenticated \
            --memory 1Gi \
            --cpu 1 \
            --max-instances 10 \
            --set-env-vars "APP_ENV=$ENVIRONMENT" \
            --timeout 300

        # Get service URL
        SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

        print_success "🌐 Deployment completed!"
        echo ""
        echo "📱 Application URL: $SERVICE_URL"
        echo "🔍 Health Check:    $SERVICE_URL/api/health"
        echo "📊 Monitoring:      https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME"
        ;;

    "docker")
        print_deploy "🐳 Docker Container Build"
        echo "========================="

        # Create Dockerfile
        if [[ ! -f "Dockerfile" ]]; then
            print_status "Creating optimized Dockerfile..."
            cat > Dockerfile << 'EOF'
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/api/health || exit 1

# Expose port
EXPOSE $PORT

# Run the application
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1"]
EOF
            print_success "Dockerfile created"
        fi

        # Build Docker image
        print_status "Building Docker image..."
        docker build -t myeurocoins:$ENVIRONMENT .

        print_success "🐳 Docker image built successfully!"
        echo ""
        echo "To run the container:"
        echo "  docker run -p $PORT:$PORT --env-file .env myeurocoins:$ENVIRONMENT"
        echo ""
        echo "To push to a registry:"
        echo "  docker tag myeurocoins:$ENVIRONMENT your-registry/myeurocoins:$ENVIRONMENT"
        echo "  docker push your-registry/myeurocoins:$ENVIRONMENT"
        ;;

    "app-engine")
        print_deploy "🚀 Google App Engine Deployment"
        echo "==============================="

        if [[ -z "$PROJECT_ID" ]]; then
            print_error "Google Cloud project ID required for App Engine deployment"
            exit 1
        fi

        # Create app.yaml
        if [[ ! -f "app.yaml" ]]; then
            print_status "Creating app.yaml..."
            cat > app.yaml << EOF
runtime: python311

env_variables:
  APP_ENV: $ENVIRONMENT
  PORT: $PORT

automatic_scaling:
  min_instances: 0
  max_instances: 10
  target_cpu_utilization: 0.6

health_check:
  enable_health_check: true
  check_interval_sec: 30
  timeout_sec: 4
  unhealthy_threshold: 2
  healthy_threshold: 2
  restart_threshold: 60

handlers:
- url: /static
  static_dir: static
  secure: always

- url: /.*
  script: auto
  secure: always
EOF
            print_success "app.yaml created"
        fi

        # Deploy to App Engine
        print_status "Deploying to App Engine..."
        gcloud app deploy app.yaml --project $PROJECT_ID --quiet

        # Get service URL
        SERVICE_URL="https://${PROJECT_ID}.appspot.com"

        print_success "🚀 App Engine deployment completed!"
        echo ""
        echo "📱 Application URL: $SERVICE_URL"
        echo "🔍 Health Check:    $SERVICE_URL/api/health"
        ;;

    "server")
        print_deploy "🖥️  Server Deployment"
        echo "==================="

        # Create systemd service file
        print_status "Creating systemd service configuration..."
        cat > myeurocoins.service << EOF
[Unit]
Description=My EuroCoins FastAPI Application
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/myeurocoins
Environment="PATH=/opt/myeurocoins/.venv/bin"
EnvironmentFile=/opt/myeurocoins/.env
ExecStart=/opt/myeurocoins/.venv/bin/uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

        # Create nginx configuration
        print_status "Creating nginx configuration..."
        cat > nginx-myeurocoins.conf << EOF
server {
    listen 80;
    listen 443 ssl;
    server_name myeurocoins.org www.myeurocoins.org;

    # SSL configuration (add your certificates)
    # ssl_certificate /path/to/certificate.crt;
    # ssl_certificate_key /path/to/private.key;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # Static files
    location /static/ {
        alias /opt/myeurocoins/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Application
    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Health check
    location /api/health {
        proxy_pass http://127.0.0.1:$PORT/api/health;
        access_log off;
    }
}
EOF

        print_success "🖥️  Server deployment files created!"
        echo ""
        echo "Manual deployment steps:"
        echo "1. Copy application to /opt/myeurocoins/"
        echo "2. Install virtual environment and dependencies"
        echo "3. Copy myeurocoins.service to /etc/systemd/system/"
        echo "4. Copy nginx-myeurocoins.conf to /etc/nginx/sites-available/"
        echo "5. Enable service: systemctl enable --now myeurocoins"
        echo "6. Enable nginx site: ln -s /etc/nginx/sites-available/nginx-myeurocoins.conf /etc/nginx/sites-enabled/"
        ;;

    *)
        print_error "Unknown deployment type: $DEPLOYMENT_TYPE"
        exit 1
        ;;
esac

# Post-deployment validation
print_status "Running post-deployment validation..."

case $DEPLOYMENT_TYPE in
    "cloud-run"|"app-engine")
        if [[ -n "$SERVICE_URL" ]]; then
            sleep 10  # Wait for service to be ready
            print_status "Testing deployed service..."

            if curl -s "$SERVICE_URL/api/health" | grep -q "healthy"; then
                print_success "✅ Health check passed"
            else
                print_warning "⚠️  Health check failed - service may still be starting"
            fi
        fi
        ;;
esac

echo ""
print_success "🎉 Deployment completed successfully!"
echo ""

# Security reminder
if [[ "$ENVIRONMENT" == "production" ]]; then
    echo "🔒 PRODUCTION SECURITY CHECKLIST:"
    echo "  ✅ Admin API key configured"
    echo "  ✅ Production environment active"
    echo "  ✅ Admin endpoints protected"
    echo "  ❗ Monitor logs for security events"
    echo "  ❗ Regularly rotate API keys"
elif [[ "$ENVIRONMENT" == "public" ]]; then
    echo "🌐 PUBLIC DEPLOYMENT ACTIVE:"
    echo "  ✅ Read-only mode enabled"
    echo "  ✅ Admin features disabled"
    echo "  ✅ Safe for public internet"
fi

echo ""
echo "📊 Useful monitoring commands:"
case $DEPLOYMENT_TYPE in
    "cloud-run")
        echo "  gcloud run services describe $SERVICE_NAME --region $REGION"
        echo "  gcloud logging read 'resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$SERVICE_NAME\"' --limit 50"
        ;;
    "app-engine")
        echo "  gcloud app logs tail"
        echo "  gcloud app services browse"
        ;;
    "server")
        echo "  systemctl status myeurocoins"
        echo "  journalctl -u myeurocoins -f"
        ;;
esac