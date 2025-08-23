# My EuroCoins - Python/FastAPI Implementation Plan 🐍

Simple, cost-effective implementation using Python FastAPI backend with vanilla JavaScript frontend for Google Cloud deployment.

## 🎯 Simplified Tech Stack

### Backend
```
Python 3.11                  // Core runtime
FastAPI                      // Modern, fast web framework
Uvicorn                      // ASGI server
Jinja2                       // HTML templating
Pydantic                     // Data validation
```

### Frontend
```
HTML5 & CSS3                 // Core web technologies
Vanilla JavaScript           // No frameworks, lightweight
Bootstrap 5.3                // Responsive CSS framework
Font Awesome 6               // Icons (replace Lucide)
```

### Cloud Services
```
Google Cloud Run             // Serverless containers (~$0-5/month)
Google BigQuery (existing)   // Data source (no additional cost)
Google Cloud Storage         // Static assets (~$1/month)
Google Cloud Build           // CI/CD (generous free tier)
```

### Development
```
Docker                       // Containerization
Python venv                  // Local development
```

**Total Cost: $1-6/month for low-medium traffic** 🎉

---

## 🏗️ Project Structure

```
my-eurocoins/
├── Dockerfile                    # Container configuration
├── requirements.txt              # Python dependencies
├── main.py                      # FastAPI application
├── .env                         # Environment variables
├── cloudbuild.yaml              # Google Cloud Build config
│
├── app/                         # Application code
│   ├── __init__.py
│   ├── main.py                  # FastAPI app setup
│   ├── routers/                 # API routes
│   │   ├── __init__.py
│   │   ├── coins.py             # Coin endpoints
│   │   └── health.py            # Health check
│   ├── services/                # Business logic
│   │   ├── __init__.py
│   │   ├── bigquery_service.py  # BigQuery integration
│   │   └── coin_service.py      # Coin operations
│   ├── models/                  # Pydantic models
│   │   ├── __init__.py
│   │   └── coin.py              # Coin data models
│   └── config.py                # Configuration settings
│
├── static/                      # Static frontend files
│   ├── css/
│   │   ├── bootstrap.min.css    # Bootstrap CSS
│   │   └── style.css            # Custom styles
│   ├── js/
│   │   ├── bootstrap.min.js     # Bootstrap JS
│   │   ├── app.js               # Main application logic
│   │   ├── coins.js             # Coin-related functions
│   │   └── filters.js           # Filter functionality
│   └── images/
│       └── logo.png             # App logo
│
├── templates/                   # Jinja2 HTML templates
│   ├── base.html               # Base template
│   ├── index.html              # Homepage
│   ├── catalog.html            # Catalog page
│   └── coin_detail.html        # Individual coin page
│
└── scripts/
    ├── deploy.sh               # Deployment script
    └── dev.sh                  # Development server
```

---

## 📋 Implementation Timeline (2 weeks)

### Week 1: Backend & API (5 days)
**Day 1: Project Setup**
```bash
mkdir my-eurocoins && cd my-eurocoins
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn jinja2 google-cloud-bigquery pydantic
```

**Day 2-3: FastAPI Backend**
- Set up FastAPI app with BigQuery integration
- Create coin API endpoints
- Basic error handling and validation

**Day 4-5: Templates & Static Serving**
- Convert HTML prototype to Jinja2 templates
- Set up static file serving
- Basic responsive layout with Bootstrap

### Week 2: Frontend & Deployment (5 days)
**Day 6-7: JavaScript Frontend**
- Convert prototype JavaScript to vanilla JS
- Implement filtering and search
- API integration with fetch()

**Day 8-9: Docker & Cloud Run**
- Create Dockerfile
- Set up Cloud Build
- Deploy to Cloud Run

**Day 10: Testing & Polish**
- Manual testing
- Performance optimization
- Documentation

---

## 🔧 Core Implementation

### 1. FastAPI Main App (app/main.py)
```python
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.routers import coins, health
from app.services.coin_service import CoinService

app = FastAPI(title="My EuroCoins", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(health.router, prefix="/api")
app.include_router(coins.router, prefix="/api")

# Initialize services
coin_service = CoinService()

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    stats = await coin_service.get_stats()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "stats": stats
    })

@app.get("/catalog", response_class=HTMLResponse)
async def catalog_page(request: Request):
    return templates.TemplateResponse("catalog.html", {
        "request": request
    })

@app.get("/coin/{coin_id}", response_class=HTMLResponse)
async def coin_detail(request: Request, coin_id: str):
    coin = await coin_service.get_coin(coin_id)
    return templates.TemplateResponse("coin_detail.html", {
        "request": request,
        "coin": coin
    })
```

### 2. BigQuery Service (app/services/bigquery_service.py)
```python
from google.cloud import bigquery
from typing import List, Dict, Optional
import os
from datetime import datetime, timedelta

class BigQueryService:
    def __init__(self):
        self.client = bigquery.Client(project='coins2025')
        self.dataset_id = 'db'
        self.table_id = 'catalog'
        self._cache = {}
        self._cache_duration = timedelta(minutes=5)

    def _get_cache_key(self, query: str, params: dict) -> str:
        return f"{query}:{str(sorted(params.items()))}"

    async def _get_cached_or_query(self, query: str, params: dict = None):
        cache_key = self._get_cache_key(query, params or {})
        
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if datetime.now() - cached_time < self._cache_duration:
                return cached_data

        # Execute query
        job_config = bigquery.QueryJobConfig()
        if params:
            job_config.query_parameters = [
                bigquery.ScalarQueryParameter(k, "STRING", v) 
                for k, v in params.items()
            ]

        query_job = self.client.query(query, job_config=job_config)
        results = list(query_job.result())
        
        # Cache results
        self._cache[cache_key] = (results, datetime.now())
        return results

    async def get_coins(self, filters: dict = None, limit: int = 100, offset: int = 0):
        where_clauses = []
        params = {}

        if filters:
            if filters.get('coin_type'):
                where_clauses.append("coin_type = @coin_type")
                params['coin_type'] = filters['coin_type']
            
            if filters.get('country'):
                where_clauses.append("country = @country")
                params['country'] = filters['country']
            
            if filters.get('year'):
                where_clauses.append("year = @year")
                params['year'] = str(filters['year'])

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = f"""
        SELECT 
            coin_type, year, country, series, value, coin_id,
            image_url, feature, volume
        FROM `{self.client.project}.{self.dataset_id}.{self.table_id}`
        WHERE {where_sql}
        ORDER BY year DESC, country ASC
        LIMIT {limit} OFFSET {offset}
        """

        return await self._get_cached_or_query(query, params)

    async def get_coin_by_id(self, coin_id: str):
        query = f"""
        SELECT *
        FROM `{self.client.project}.{self.dataset_id}.{self.table_id}`
        WHERE coin_id = @coin_id
        """
        
        results = await self._get_cached_or_query(query, {'coin_id': coin_id})
        return results[0] if results else None

    async def get_stats(self):
        query = f"""
        SELECT 
            COUNT(*) as total_coins,
            COUNT(DISTINCT country) as total_countries,
            COUNTIF(coin_type = 'RE') as regular_coins,
            COUNTIF(coin_type = 'CC') as commemorative_coins
        FROM `{self.client.project}.{self.dataset_id}.{self.table_id}`
        """
        
        results = await self._get_cached_or_query(query)
        return dict(results[0]) if results else {}

    async def get_filter_options(self):
        query = f"""
        SELECT 
            ARRAY_AGG(DISTINCT country ORDER BY country) as countries,
            ARRAY_AGG(DISTINCT year ORDER BY year DESC) as years,
            ARRAY_AGG(DISTINCT value ORDER BY value) as denominations
        FROM `{self.client.project}.{self.dataset_id}.{self.table_id}`
        """
        
        results = await self._get_cached_or_query(query)
        return dict(results[0]) if results else {}
```

### 3. Coin API Router (app/routers/coins.py)
```python
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from app.services.bigquery_service import BigQueryService
from app.models.coin import CoinResponse, CoinListResponse, StatsResponse

router = APIRouter(prefix="/coins", tags=["coins"])
bigquery_service = BigQueryService()

@router.get("/", response_model=CoinListResponse)
async def get_coins(
    coin_type: Optional[str] = Query(None, description="Filter by coin type (RE/CC)"),
    country: Optional[str] = Query(None, description="Filter by country"),
    year: Optional[int] = Query(None, description="Filter by year"),
    search: Optional[str] = Query(None, description="Search term"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    filters = {}
    if coin_type:
        filters['coin_type'] = coin_type
    if country:
        filters['country'] = country
    if year:
        filters['year'] = year

    coins = await bigquery_service.get_coins(filters, limit, offset)
    
    # Client-side search if needed
    if search and coins:
        search_lower = search.lower()
        coins = [
            coin for coin in coins 
            if search_lower in coin.country.lower() or 
               (coin.feature and search_lower in coin.feature.lower())
        ]

    return CoinListResponse(
        coins=coins,
        total=len(coins),
        limit=limit,
        offset=offset
    )

@router.get("/{coin_id}", response_model=CoinResponse)
async def get_coin(coin_id: str):
    coin = await bigquery_service.get_coin_by_id(coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail="Coin not found")
    return CoinResponse(coin=coin)

@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    stats = await bigquery_service.get_stats()
    return StatsResponse(**stats)

@router.get("/filters")
async def get_filter_options():
    return await bigquery_service.get_filter_options()
```

### 4. Pydantic Models (app/models/coin.py)
```python
from pydantic import BaseModel
from typing import List, Optional

class Coin(BaseModel):
    coin_type: str
    year: int
    country: str
    series: str
    value: float
    coin_id: str
    image_url: Optional[str] = None
    feature: Optional[str] = None
    volume: Optional[str] = None

class CoinResponse(BaseModel):
    coin: Coin

class CoinListResponse(BaseModel):
    coins: List[Coin]
    total: int
    limit: int
    offset: int

class StatsResponse(BaseModel):
    total_coins: int
    total_countries: int
    regular_coins: int
    commemorative_coins: int
```

### 5. Base HTML Template (templates/base.html)
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}My EuroCoins{% endblock %}</title>
    
    <!-- Bootstrap CSS -->
    <link href="/static/css/bootstrap.min.css" rel="stylesheet">
    <link href="/static/css/style.css" rel="stylesheet">
    
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-light bg-white shadow-sm">
        <div class="container">
            <a class="navbar-brand d-flex align-items-center" href="/">
                <div class="coin-logo me-3">🪙</div>
                <div>
                    <h1 class="h5 mb-0 fw-bold">My EuroCoins</h1>
                    <small class="text-muted">Collection • 2025</small>
                </div>
            </a>
            <div class="navbar-nav">
                <a class="nav-link" href="/catalog">Catalog</a>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <main>
        {% block content %}{% endblock %}
    </main>

    <!-- Footer -->
    <footer class="bg-dark text-white mt-5">
        <div class="container py-4 text-center">
            <p class="mb-0">2025 My EuroCoins</p>
        </div>
    </footer>

    <!-- Bootstrap JS -->
    <script src="/static/js/bootstrap.min.js"></script>
    <script src="/static/js/app.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

### 6. Catalog JavaScript (static/js/coins.js)
```javascript
class CoinCatalog {
    constructor() {
        this.coins = [];
        this.filteredCoins = [];
        this.currentFilters = {
            coin_type: '',
            country: '',
            year: '',
            search: ''
        };
        this.currentPage = 1;
        this.coinsPerPage = 20;
        
        this.init();
    }

    async init() {
        await this.loadFilterOptions();
        await this.loadCoins();
        this.setupEventListeners();
        this.renderCoins();
    }

    async loadCoins() {
        try {
            const params = new URLSearchParams();
            
            Object.entries(this.currentFilters).forEach(([key, value]) => {
                if (value) params.append(key, value);
            });
            
            params.append('limit', '1000'); // Load all for client-side filtering
            
            const response = await fetch(`/api/coins?${params}`);
            const data = await response.json();
            
            this.coins = data.coins;
            this.applyFilters();
        } catch (error) {
            console.error('Error loading coins:', error);
            this.showError('Failed to load coins');
        }
    }

    async loadFilterOptions() {
        try {
            const response = await fetch('/api/coins/filters');
            const options = await response.json();
            
            this.populateCountryFilter(options.countries);
            this.populateYearFilter(options.years);
        } catch (error) {
            console.error('Error loading filter options:', error);
        }
    }

    applyFilters() {
        this.filteredCoins = this.coins.filter(coin => {
            if (this.currentFilters.coin_type && coin.coin_type !== this.currentFilters.coin_type) {
                return false;
            }
            if (this.currentFilters.country && coin.country !== this.currentFilters.country) {
                return false;
            }
            if (this.currentFilters.year && coin.year.toString() !== this.currentFilters.year) {
                return false;
            }
            if (this.currentFilters.search) {
                const search = this.currentFilters.search.toLowerCase();
                const searchFields = [
                    coin.country.toLowerCase(),
                    coin.feature?.toLowerCase() || ''
                ];
                if (!searchFields.some(field => field.includes(search))) {
                    return false;
                }
            }
            return true;
        });
        
        this.currentPage = 1;
        this.renderCoins();
        this.updateResultsCount();
    }

    renderCoins() {
        const container = document.getElementById('coins-grid');
        const startIndex = (this.currentPage - 1) * this.coinsPerPage;
        const endIndex = startIndex + this.coinsPerPage;
        const coinsToShow = this.filteredCoins.slice(startIndex, endIndex);

        if (coinsToShow.length === 0) {
            container.innerHTML = '<div class="col-12 text-center py-5"><h4>No coins found</h4></div>';
            return;
        }

        container.innerHTML = coinsToShow.map(coin => this.createCoinCard(coin)).join('');
        this.renderPagination();
    }

    createCoinCard(coin) {
        const flag = this.getCountryFlag(coin.country);
        const typeClass = coin.coin_type === 'RE' ? 'bg-success' : 'bg-primary';
        const typeName = coin.coin_type === 'RE' ? 'Regular' : 'Commemorative';

        return `
            <div class="col-md-6 col-lg-4 col-xl-3 mb-4">
                <div class="card coin-card h-100">
                    <div class="position-relative">
                        <img src="${coin.image_url}" class="card-img-top coin-image" alt="${coin.country} ${coin.value} Euro">
                        <span class="badge ${typeClass} position-absolute top-0 start-0 m-2">${coin.coin_type}</span>
                    </div>
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <h6 class="card-title mb-0">
                                <span class="me-2">${flag}</span>${coin.country}
                            </h6>
                            <span class="h5 mb-0 text-primary fw-bold">€${coin.value}</span>
                        </div>
                        <p class="card-text text-muted small">${typeName} • ${coin.year}</p>
                        ${coin.feature ? `<p class="card-text small text-truncate">${coin.feature}</p>` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    getCountryFlag(country) {
        const flags = {
            'Germany': '🇩🇪', 'France': '🇫🇷', 'Italy': '🇮🇹', 'Spain': '🇪🇸',
            'Finland': '🇫🇮', 'Croatia': '🇭🇷', 'Luxembourg': '🇱🇺', 'Belgium': '🇧🇪',
            'Austria': '🇦🇹', 'Netherlands': '🇳🇱', 'Portugal': '🇵🇹', 'Greece': '🇬🇷'
        };
        return flags[country] || '🇪🇺';
    }

    setupEventListeners() {
        // Search input
        const searchInput = document.getElementById('search-input');
        let searchTimeout;
        searchInput?.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.currentFilters.search = e.target.value;
                this.applyFilters();
            }, 300);
        });

        // Filter selects
        document.getElementById('type-filter')?.addEventListener('change', (e) => {
            this.currentFilters.coin_type = e.target.value;
            this.applyFilters();
        });

        document.getElementById('country-filter')?.addEventListener('change', (e) => {
            this.currentFilters.country = e.target.value;
            this.applyFilters();
        });

        document.getElementById('year-filter')?.addEventListener('change', (e) => {
            this.currentFilters.year = e.target.value;
            this.applyFilters();
        });

        // Clear filters
        document.getElementById('clear-filters')?.addEventListener('click', () => {
            this.currentFilters = { coin_type: '', country: '', year: '', search: '' };
            document.getElementById('search-input').value = '';
            document.getElementById('type-filter').value = '';
            document.getElementById('country-filter').value = '';
            document.getElementById('year-filter').value = '';
            this.applyFilters();
        });
    }

    // ... Additional methods for pagination, error handling, etc.
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('catalog-page')) {
        new CoinCatalog();
    }
});
```

### 7. Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 8. Requirements.txt
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
jinja2==3.1.2
google-cloud-bigquery==3.13.0
pydantic==2.5.0
python-multipart==0.0.6
```

### 9. Cloud Build Configuration (cloudbuild.yaml)
```yaml
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/my-eurocoins:$COMMIT_SHA', '.']
  
  # Push the container image to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/my-eurocoins:$COMMIT_SHA']
  
  # Deploy container image to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
    - 'run'
    - 'deploy'
    - 'my-eurocoins'
    - '--image'
    - 'gcr.io/$PROJECT_ID/my-eurocoins:$COMMIT_SHA'
    - '--region'
    - 'us-central1'
    - '--platform'
    - 'managed'
    - '--allow-unauthenticated'
    - '--memory'
    - '512Mi'
    - '--cpu'
    - '1'
    - '--max-instances'
    - '10'

images:
  - gcr.io/$PROJECT_ID/my-eurocoins:$COMMIT_SHA
```

---

## 🚀 Deployment Commands

### Local Development
```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload --port 8000

# Visit: http://localhost:8000
```

### Google Cloud Deploy
```bash
# Build and deploy
gcloud builds submit --config cloudbuild.yaml

# Or manual deploy
docker build -t gcr.io/coins2025/my-eurocoins .
docker push gcr.io/coins2025/my-eurocoins

gcloud run deploy my-eurocoins \
  --image gcr.io/coins2025/my-eurocoins \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1
```

## 💰 Cost Benefits

- **Cloud Run**: Pay only when serving requests (~$0-5/month)
- **No database hosting**: Use existing BigQuery
- **Minimal dependencies**: Faster builds, lower costs
- **Static assets**: Served efficiently from Cloud Run
- **Simple caching**: In-memory cache reduces BigQuery queries

---

## 🌐 Complete Deployment Guide

### Prerequisites
```bash
# Install Google Cloud CLI
brew install --cask google-cloud-sdk

# Authenticate
gcloud auth login
gcloud config set project coins2025

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable bigquery.googleapis.com
```

### Environment Setup
```bash
# Create service account for BigQuery
gcloud iam service-accounts create my-eurocoins-sa \
  --display-name="My EuroCoins Service Account"

# Grant BigQuery permissions
gcloud projects add-iam-policy-binding coins2025 \
  --member="serviceAccount:my-eurocoins-sa@coins2025.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"

# Create and download service account key
gcloud iam service-accounts keys create service-account-key.json \
  --iam-account=my-eurocoins-sa@coins2025.iam.gserviceaccount.com
```

### Environment Variables (.env)
```bash
# Google Cloud
GOOGLE_CLOUD_PROJECT=coins2025
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json

# BigQuery
BQ_DATASET=db
BQ_TABLE=catalog

# App Settings
APP_ENV=production
LOG_LEVEL=INFO
CACHE_DURATION_MINUTES=5
```

### Production Deployment Steps

**Step 1: Build and Deploy**
```bash
# Submit build to Cloud Build
gcloud builds submit --config cloudbuild.yaml

# Check deployment status
gcloud run services describe my-eurocoins --region=us-central1
```

**Step 2: Configure Custom Domain (Optional)**
```bash
# Map custom domain
gcloud run domain-mappings create \
  --service my-eurocoins \
  --domain your-domain.com \
  --region us-central1
```

**Step 3: Enable HTTPS and Security**
```bash
# Update service with security headers
gcloud run services update my-eurocoins \
  --region us-central1 \
  --set-env-vars="SECURE_HEADERS=true"
```

### Monitoring and Maintenance

**Performance Monitoring**
```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# Monitor metrics
gcloud monitoring dashboards list
```

**Cost Optimization**
- Set minimum instances to 0 (scale to zero)
- Use 512Mi memory (sufficient for this app)
- Enable CPU throttling for cost savings
- Monitor BigQuery usage monthly

**Security Best Practices**
- Use least privilege IAM roles
- Enable Cloud Armor for DDoS protection
- Implement rate limiting in FastAPI
- Regular security updates for dependencies

### Development Workflow

**Local Development**
```bash
# Clone and setup
git clone https://github.com/n-dimitrov/coins2025.git
cd coins2025
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload --port 8000
```

**Continuous Deployment**
```bash
# Create Cloud Build trigger
gcloud builds triggers create github \
  --repo-name=coins2025 \
  --repo-owner=n-dimitrov \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml
```

### Cost Estimation (Monthly)

| Service | Usage | Cost |
|---------|-------|------|
| Cloud Run | 100k requests, 512Mi RAM | $1-3 |
| BigQuery | Existing dataset queries | $0 |
| Cloud Build | 10 builds/month | $0 (free tier) |
| Container Registry | 1GB storage | $0.10 |
| **Total** | | **$1-4/month** |

### Troubleshooting

**Common Issues:**
1. **BigQuery Permission Denied**: Check service account IAM roles
2. **Cold Start Latency**: Consider min instances = 1 for production
3. **Memory Limits**: Monitor Cloud Run metrics, adjust if needed
4. **Build Failures**: Check Dockerfile and dependencies

**Health Checks:**
- App health: `https://your-app.run.app/api/health`
- BigQuery connection: `https://your-app.run.app/api/coins/stats`

This approach gives you a production-ready app with the same beautiful UI, deployed on Google Cloud for under $5/month! 🎉

## 🎯 Summary

**What You Get:**
✅ Beautiful responsive web app matching your prototype  
✅ Fast Python/FastAPI backend with BigQuery integration  
✅ Vanilla JavaScript frontend (no framework complexity)  
✅ Docker containerized deployment on Cloud Run  
✅ Automatic scaling and cost optimization  
✅ Production-ready with monitoring and security  

**Timeline: 2 weeks** | **Cost: $1-4/month** | **Scalable to 100k+ users**
