# My EuroCoins - Deployment Guide

## Google Cloud Platform Deployment

This guide will help you deploy the My EuroCoins application to Google Cloud Run.

### Prerequisites

1. **Google Cloud Account**: You need a Google Cloud Platform account
2. **Google Cloud CLI**: Install from [https://cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install)
3. **Docker**: Install from [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)
4. **BigQuery Dataset**: Your existing BigQuery dataset with coins data

### Quick Deployment

Run the automated deployment script:

```bash
./scripts/deploy_to_gcp.sh
```

This script will:
- ✅ Check all requirements
- ✅ Authenticate with Google Cloud (if needed)
- ✅ Set up your project
- ✅ Enable required APIs
- ✅ Build and deploy the application
- ✅ Verify the deployment

### Manual Deployment Steps

If you prefer to deploy manually:

1. **Authenticate with Google Cloud**:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Enable required APIs**:
   ```bash
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable run.googleapis.com
   gcloud services enable containerregistry.googleapis.com
   gcloud services enable bigquery.googleapis.com
   ```

3. **Deploy using Cloud Build**:
   ```bash
   gcloud builds submit --config cloudbuild.yaml .
   ```

### Configuration

The application will be deployed with these settings:
- **Region**: us-central1
- **Memory**: 512Mi
- **CPU**: 1 vCPU
- **Max Instances**: 10
- **Min Instances**: 0 (scales to zero)
- **Port**: 8000
- **Public Access**: Enabled

### Environment Variables

The following environment variables are automatically set:
- `APP_ENV=production`
- `GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID`

### Post-Deployment

After successful deployment, you'll receive:
- 🌐 **Application URL**: Your live application
- 📊 **Health Check**: `/api/health` endpoint
- 📖 **API Documentation**: `/api/docs` endpoint

### Monitoring

You can monitor your application at:
- [Google Cloud Console](https://console.cloud.google.com/run)
- [Cloud Build History](https://console.cloud.google.com/cloud-build/builds)
- [Application Logs](https://console.cloud.google.com/logs)

### Costs

The application uses:
- **Cloud Run**: Pay-per-request, free tier available
- **BigQuery**: Pay-per-query, first 1TB/month free
- **Container Registry**: Storage costs for Docker images

### Troubleshooting

If deployment fails:

1. **Check authentication**: `gcloud auth list`
2. **Verify project**: `gcloud config get-value project`
3. **Check APIs**: `gcloud services list --enabled`
4. **View logs**: `gcloud logs read --service=my-eurocoins`

### Updating the Application

To update your deployed application:

1. Make your changes locally
2. Run the deployment script again: `./scripts/deploy_to_gcp.sh`
3. The new version will be automatically deployed

---

## Local Development

For local development, use:

```bash
./scripts/run_local.sh
```

This will start the application at http://localhost:8000

---

**Need help?** Check the [Google Cloud Run documentation](https://cloud.google.com/run/docs) or the application logs in the Google Cloud Console.
