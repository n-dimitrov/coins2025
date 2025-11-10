# 🚀 My EuroCoins Deployment Guide

This guide covers all deployment options for the My EuroCoins application, from local development to production cloud deployment.

## Quick Start

```bash
# Development (all features enabled)
./scripts/start-dev.sh

# Public read-only mode (safe for internet)
./scripts/start-public.sh

# Production deployment
./scripts/deploy.sh --type cloud-run --project your-gcp-project --admin-key "your-secret-key"
```

## 📋 Prerequisites

### All Deployments
- Python 3.11+
- Virtual environment (`.venv` or `venv`)
- Required dependencies from `requirements.txt` or `requirements-prod.txt`

### Cloud Deployments
- Google Cloud SDK (`gcloud` CLI)
- Docker (for containerized deployments)
- Valid Google Cloud project with BigQuery enabled
- Service account with BigQuery permissions

### Production Requirements
- **Admin API Key**: Required for production security
- **SSL Certificate**: Recommended for HTTPS
- **Domain Name**: For public deployment
- **Monitoring**: Health checks and logging

## 🔧 Deployment Options

### 1. Local Development

**Purpose**: Full-featured development environment

```bash
./scripts/start-dev.sh
```

**Features:**
- ✅ All admin endpoints enabled
- ✅ API documentation accessible
- ✅ Hot reload for development
- ✅ Permissive CORS settings
- ⚠️ No authentication required

**Endpoints:**
- Application: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- Admin: http://localhost:8000/api/admin/coins/view

### 2. Public Read-Only Mode

**Purpose**: Safe for public internet deployment

```bash
./scripts/start-public.sh
```

**Features:**
- ✅ Catalog browsing enabled
- ✅ Group viewing enabled
- ❌ Admin endpoints disabled
- ❌ API documentation disabled
- 🔒 Maximum security

**Endpoints:**
- Application: http://localhost:8080
- Health: http://localhost:8080/api/health

### 3. Google Cloud Run

**Purpose**: Scalable cloud deployment with automatic scaling

```bash
./scripts/deploy.sh --type cloud-run --project your-gcp-project --admin-key "your-secret-key"
```

**Features:**
- 🌐 Automatic scaling (0-10 instances)
- 🔒 Production security enabled
- 📊 Integrated monitoring
- 💰 Pay-per-use pricing
- 🚀 Fast global deployment

**Configuration:**
- Memory: 1GB
- CPU: 1 vCPU
- Port: 8080
- Timeout: 300 seconds

### 4. Google App Engine

**Purpose**: Fully managed platform deployment

```bash
./scripts/deploy.sh --type app-engine --project your-gcp-project --admin-key "your-secret-key"
```

**Features:**
- 🔧 Zero server management
- 📈 Automatic scaling
- 🔒 Built-in security
- 📊 Integrated monitoring

### 5. Docker Container

**Purpose**: Containerized deployment for any environment

```bash
./scripts/deploy.sh --type docker
```

**Run the container:**
```bash
docker run -p 8080:8080 --env-file .env myeurocoins:production
```

### 6. Traditional Server

**Purpose**: VPS, dedicated server, or on-premises deployment

```bash
./scripts/deploy.sh --type server --env production --admin-key "your-secret-key"
```

**Includes:**
- Systemd service configuration
- Nginx reverse proxy setup
- SSL/HTTPS configuration
- Security headers

## 🔐 Security Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `APP_ENV` | Environment mode (`development`, `production`) | Yes | `development` |
| `ADMIN_API_KEY` | Admin API authentication key | Production | None |
| `ADMIN_ALLOWED_IPS` | Comma-separated allowed IP addresses | No | `127.0.0.1,::1` |
| `ENABLE_ADMIN_ENDPOINTS` | Enable/disable admin features | No | Auto-detect |
| `GOOGLE_CLOUD_PROJECT` | Google Cloud project ID | Yes | `coins2025` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Service account credentials path | Yes | `./credentials/service_account.json` |

### Security Levels

#### Development Mode (`.env.development`)
- ✅ All features enabled
- ⚠️ Optional authentication
- 🌐 Permissive CORS
- 📚 API documentation accessible

#### Production Mode (`.env.production`)
- 🔒 Admin API key required
- 🛡️ IP restrictions enabled
- 🚫 Strict CORS policy
- 📚 API docs disabled

#### Public Mode (`.env.public`)
- 👁️ Read-only access
- 🚫 Admin endpoints disabled
- 🚫 Ownership modifications disabled
- 🌐 Safe for public internet

### API Authentication

Production admin endpoints require Bearer token authentication:

```bash
# Get admin data
curl -H "Authorization: Bearer YOUR_ADMIN_API_KEY" \
     https://your-domain.com/api/admin/coins/export

# Clear cache
curl -X POST \
     -H "Authorization: Bearer YOUR_ADMIN_API_KEY" \
     https://your-domain.com/api/admin/clear-cache
```

## 🔍 Health Checks and Monitoring

### Health Check Endpoint

```bash
curl https://your-domain.com/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T12:00:00Z",
  "version": "1.2.0",
  "environment": "production"
}
```

### Monitoring Commands

**Cloud Run:**
```bash
# Service status
gcloud run services describe myeurocoins --region us-central1

# Logs
gcloud logging read 'resource.type="cloud_run_revision"' --limit 50
```

**Docker:**
```bash
# Container health
docker ps
docker logs myeurocoins-app

# Resource usage
docker stats myeurocoins-app
```

**Server:**
```bash
# Service status
systemctl status myeurocoins

# Live logs
journalctl -u myeurocoins -f

# Resource usage
htop
```

## 🌐 Domain Configuration

### DNS Records

```
# A record for main domain
myeurocoins.org.    A    YOUR_SERVER_IP

# CNAME for www subdomain
www.myeurocoins.org. CNAME myeurocoins.org.
```

### SSL Certificate

**Option 1: Let's Encrypt (Recommended)**
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d myeurocoins.org -d www.myeurocoins.org
```

**Option 2: Cloud Provider SSL**
- Google Cloud: Managed SSL certificates
- Cloudflare: Free SSL with CDN

## 🚨 Troubleshooting

### Common Issues

**1. Port Already in Use**
```bash
# Kill existing processes
pkill -f "uvicorn.*main:app"
pkill -f "python main.py"

# Check what's using the port
lsof -i :8080
```

**2. SSL Error on Localhost**
- Ensure `.env` doesn't force HTTPS
- Check CSP headers in templates
- Use HTTP for local development

**3. BigQuery Authentication**
```bash
# Check service account
gcloud auth list

# Test BigQuery access
bq query "SELECT 1 as test"
```

**4. Memory Issues**
```bash
# Check memory usage
free -h

# Increase Cloud Run memory
gcloud run services update myeurocoins --memory 2Gi
```

### Logs and Debugging

**Enable detailed logging:**
```bash
export LOG_LEVEL=DEBUG
./scripts/start-dev.sh
```

**Check application logs:**
```bash
# Local development
tail -f logs/application.log

# Cloud Run
gcloud logging read 'resource.type="cloud_run_revision"' --limit 100

# Docker
docker logs -f myeurocoins-app
```

## 🔄 Deployment Pipeline

### CI/CD with GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Google Cloud
        uses: google-github-actions/setup-gcloud@v1
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ secrets.GCP_PROJECT }}

      - name: Deploy to Cloud Run
        run: |
          ./scripts/deploy.sh \
            --type cloud-run \
            --project ${{ secrets.GCP_PROJECT }} \
            --admin-key "${{ secrets.ADMIN_API_KEY }}"
```

### Blue-Green Deployment

```bash
# Deploy to staging
./scripts/deploy.sh --type cloud-run --service myeurocoins-staging

# Test staging environment
curl https://staging.myeurocoins.org/api/health

# Promote to production
gcloud run services update-traffic myeurocoins --to-revisions=LATEST=100
```

## 📊 Performance Optimization

### Production Optimizations

1. **Enable gzip compression**
2. **Configure CDN** (Cloudflare, Google Cloud CDN)
3. **Optimize database queries**
4. **Enable caching** (Redis, in-memory)
5. **Use production WSGI server** (Gunicorn with multiple workers)

### Scaling Configuration

**Cloud Run:**
```bash
gcloud run services update myeurocoins \
  --min-instances 1 \
  --max-instances 100 \
  --cpu 2 \
  --memory 2Gi \
  --concurrency 80
```

**Docker Compose with Load Balancer:**
```yaml
version: '3.8'
services:
  app:
    deploy:
      replicas: 3
    # ... rest of configuration
```

## 🔒 Security Checklist

### Pre-Deployment Security

- [ ] Generate strong admin API key (32+ characters)
- [ ] Configure IP restrictions for admin access
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Set secure environment variables
- [ ] Review CORS policy
- [ ] Update default credentials
- [ ] Enable security headers
- [ ] Configure firewall rules

### Post-Deployment Security

- [ ] Test health check endpoint
- [ ] Verify admin endpoints are protected
- [ ] Test API authentication
- [ ] Check security headers
- [ ] Monitor access logs
- [ ] Set up alerts for failed authentication

## 📞 Support

For deployment issues:

1. Check this documentation
2. Review application logs
3. Test with security testing script: `./scripts/test-security.sh`
4. Verify environment configuration
5. Create GitHub issue with deployment details

---

**Quick Commands Summary:**

```bash
# Development
./scripts/start-dev.sh

# Production (Cloud Run)
./scripts/deploy.sh --type cloud-run --project YOUR_PROJECT --admin-key "YOUR_KEY"

# Docker
./scripts/deploy.sh --type docker
docker run -p 8080:8080 --env-file .env myeurocoins:production

# Health Check
curl https://your-domain.com/api/health

# Security Test
./scripts/test-security.sh
```