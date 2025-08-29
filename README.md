# My EuroCoins 🪙

A comprehensive, interactive web application for exploring and cataloging Euro coins from 1999 to 2025. Built with Python FastAPI backend and vanilla JavaScript frontend, deployed on Google Cloud Run with BigQuery data storage for optimal performance and cost efficiency.

**Live Site**: [myeurocoins.org](https://myeurocoins.org)

![My EuroCoins Banner](https://img.shields.io/badge/My%20EuroCoins-2025-blue?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJMMTMuMDkgOC4yNkwyMCA5TDEzLjA5IDE1Ljc0TDEyIDIyTDEwLjkxIDE1Ljc0TDQgOUwxMC45MSA4LjI2TDEyIDJaIiBzdHJva2U9IiNGRkYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=)

[![Deploy Status](https://img.shields.io/badge/deploy-passing-green?style=flat-square)](https://myeurocoins.org)
[![Python](https://img.shields.io/badge/python-3.12+-blue?style=flat-square)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-green?style=flat-square)](https://fastapi.tiangolo.com)
[![Google Cloud](https://img.shields.io/badge/Google%20Cloud-Run-blue?style=flat-square)](https://cloud.google.com/run)

## � Changelog

### [1.1.0] - 2025-08-29

#### ✨ New Features
- **BigQuery Service Initialization**: Initialize BigQueryService at startup and remove runtime fallback in GroupService
- **Group Member Management**: Add group member extender mode with header display and ownership management
- **Admin History View**: Default history shows current-owned coins with include-inactive toggle and per-user export
- **Modal Image Interaction**: Make coin image clickable to open modal with pointer cursor
- **Catalog 3D Effects**: Add 3D card hover effects, hero background, and improved coin card styling
- **Admin Import UX**: Enhanced import UX with conflict handling and editable IDs
- **Group Homepage Hero**: Show group-specific latest coins in homepage hero section

#### 🔧 Improvements
- **Ownership Tracking**: Accept string UUID group_id in ownership endpoints and merge owners into coin details
- **UI Enhancements**: 
  - Move Add/Remove buttons to ownership header
  - Highlight selected group member in ownership lists
  - Make group badge clickable with improved contrast
  - Align modal header with card layout and make it sticky
  - Remove nested scrollbars in coin detail modal
  - Color coin-detail image circle by group/owner/selected rules
- **Header Layout**: Move menu left, group badge right with compact navbar spacing
- **SEO Optimization**: Use explicit canonical_path to avoid alternate/redirect canonicals
- **Admin UI**: Various tweaks and improvements to admin interface

#### 🐛 Bug Fixes
- **Ownership Filter**: Ensure ownership lists include only group members with case-insensitive joins
- **Modal Hide Listener**: Fix binding of clearAllCardPop handler for coinDetailModal hide event
- **Memory Leak Prevention**: Use single persistent hidden.bs.modal handler instead of per-show listeners

#### 📊 Data Updates
- **Catalog Updates**: Updated coin catalog data (1665+ changes)
- **History Data**: Refreshed ownership history data (2982+ changes)
- **Commemorative Coins**: Updated CC catalog with latest data
- **Regular Coins**: Updated RE catalog with current information

## �🚀 Quick Start

### Prerequisites
- Python 3.12+
- Google Cloud CLI (optional for local BigQuery access)
- Docker (for deployment)

## 🛠️ Development

### Local Development Setup
```bash
# Clone the repository
git clone https://github.com/n-dimitrov/coins2025.git
cd coins2025

# Create and activate Python virtual environment
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.template .env
# Edit .env with your Google Cloud credentials

# Run development server
python main.py
# or using scripts
./scripts/run_local.sh

# Visit: http://localhost:8000
```

### Docker Development
```bash
# Build and run with Docker
docker build -t myeurocoins .
docker run -p 8000:8000 --env-file .env myeurocoins

# Or use docker-compose for full stack
docker-compose up --build
```

### Production Deployment
```bash
# Deploy to Google Cloud Run (automated via Cloud Build)
git push origin main

# Or manual deployment
gcloud builds submit --config cloudbuild.yaml

# Using deployment script
chmod +x scripts/deploy_to_gcp.sh
./scripts/deploy_to_gcp.sh
```

## 🌟 Features

### 📚 **Comprehensive Catalog**
- **1000+ Total Coins** from 1999-2025 (continuously updated)
- **Regular Circulation Coins** from all eurozone countries with series variations
- **Commemorative €2 Coins** including special series and joint European issues
- **27 Countries** covering all eurozone nations and micro-states
- **Real Coin Images** sourced from European Central Bank official database

### 👥 **Group Collection Management**
- **Group Creation & Management** - Create groups for family, friends, or collecting clubs
- **Ownership Tracking** - Track which group members own which coins
- **Collection Status Filters** - Filter by owned/missing coins in group context
- **Member-Specific Views** - See collections by individual group members
- **Ownership Badges** - Visual indicators showing ownership status and counts

### 🎨 **Modern UI Design**
- **Fully Responsive** - Optimized for mobile, tablet, and desktop
- **Bootstrap 5** with custom styling for professional appearance
- **Interactive Filtering** with real-time search and multi-criteria selection
- **Country Flags** for instant visual identification
- **Accessibility Compliant** following WCAG 2.1 guidelines
- **Modal Coin Details** with image gallery and navigation

### 🔍 **Advanced Search & Filtering**
- **Real-time Text Search** across country names, features, and descriptions
- **Type Filtering** - Regular (RE) vs Commemorative (CC) coins
- **Denomination Filtering** from 1¢ to €2 coins
- **Country Multi-Selection** with visual flag indicators
- **Commemorative Series Filtering** with human-readable labels
- **Group Filters** - Ownership status and member-specific filtering

### ⚡ **Performance & Architecture**
- **FastAPI Backend** with async BigQuery integration for blazing speed
- **Vanilla JavaScript Frontend** - no framework overhead, pure performance
- **Intelligent Caching** system to minimize BigQuery costs and improve response times
- **Google Cloud Run** deployment with automatic scaling (0-1000+ instances)
- **Docker Containerization** for consistent deployment across environments
- **CDN Integration** for static assets delivery

## 🏗️ Tech Stack

### Backend
- **Python 3.12** - Core runtime
- **FastAPI** - Modern, fast web framework
- **Uvicorn** - ASGI server
- **Google Cloud BigQuery** - Data warehouse
- **Pydantic** - Data validation and serialization

### Frontend
- **HTML5 & CSS3** - Core web technologies
- **Vanilla JavaScript ES6+** - No framework dependencies
- **Bootstrap 5** - Responsive CSS framework
- **Font Awesome 6** - Icon library

### Infrastructure & Deployment
- **Google Cloud Run** - Serverless containers with auto-scaling
- **Google Cloud Build** - Automated CI/CD pipeline
- **Google BigQuery** - Scalable data warehouse for coin catalog
- **Docker** - Containerization for consistent deployments

## 📁 Project Structure

```
coins2025/
├── app/                        # FastAPI application
│   ├── __init__.py            # Package initialization
│   ├── config.py              # Configuration settings
│   ├── models/                # Pydantic data models
│   │   ├── __init__.py
│   │   └── coin.py            # Coin data structures
│   ├── routers/               # API route handlers
│   │   ├── __init__.py
│   │   ├── coins.py           # Coin API endpoints
│   │   ├── health.py          # Health check endpoint
│   │   └── pages.py           # HTML page routes
│   └── services/              # Business logic
│       ├── __init__.py
│       ├── bigquery_service.py # BigQuery integration
│       └── group_service.py    # Group management
├── templates/                 # Jinja2 HTML templates
│   ├── base.html             # Base template with navigation
│   ├── index.html            # Homepage
│   ├── catalog.html          # Coin catalog page
│   ├── error.html            # Error pages
│   └── 404.html              # 404 error page
├── static/                    # Static assets
│   ├── css/
│   │   └── style.css         # Custom styles
│   ├── js/
│   │   ├── app.js            # Main application logic
│   │   └── coins.js          # Coin catalog functionality
│   └── images/               # Icons, favicons, and images
├── docs/                     # Documentation
│   ├── ADDING_SERIES.md      # Guide for adding new coin series
│   ├── DEPLOYMENT.md         # Production deployment guide
│   ├── IMPLEMENTATION_PLAN.md # Technical architecture
│   ├── GROUPS_IMPLEMENTATION_PLAN.md # Group features design
│   ├── MODAL_IMPLEMENTATION.md # Modal system documentation
│   ├── OWNERSHIP_API_SUMMARY.md # Ownership API reference
│   └── OWNERSHIP_BADGE_IMPLEMENTATION.md # Ownership badges
├── data/                     # Data files and imports
│   ├── catalog.csv           # Complete coin catalog
│   ├── groups.csv            # Group definitions
│   ├── group_users.csv       # Group membership
│   ├── history.csv           # Ownership history
│   ├── cc_catalog.json       # Commemorative coins
│   └── re_catalog.json       # Regular coins
├── tools/                    # Data management tools
│   ├── import_catalog.py     # Import coin catalog to BigQuery
│   ├── import_groups.py      # Import group data
│   ├── import_history.py     # Import ownership history
│   ├── scrape_cc_catalog.py  # Scrape commemorative coin data
│   └── scrape_re_catalog.py  # Scrape regular coin data
├── scripts/                  # Deployment and utility scripts
│   ├── deploy_to_gcp.sh     # Google Cloud deployment
│   ├── run_local.sh         # Local development server
│   └── test_docker.sh       # Docker testing
├── credentials/              # Service account credentials
├── main.py                   # Application entry point
├── Dockerfile               # Container configuration
├── cloudbuild.yaml          # Google Cloud Build config
├── requirements.txt         # Python dependencies
└── README.md                # This file
```
## 💰 Cost & Performance

### Monthly Operating Costs (Production)
- **Google Cloud Run**: $2-5 (scales to zero when not in use)
- **BigQuery**: $0-1 (existing dataset, optimized queries with caching)
- **Cloud Build**: $0 (free tier covers typical usage)
- **Container Registry**: $0.10 (minimal storage requirements)
- **Cloud Storage**: $0.50 (static assets and backups)
- **Custom Domain**: $12/year (optional)
- **Total**: **$3-7/month** for thousands of users

### Performance Metrics
- **Cold Start**: <1.5 seconds (optimized Python FastAPI)
- **Response Time**: <200ms (with intelligent caching)
- **Availability**: 99.95% (Google Cloud Run SLA)
- **Scalability**: Auto-scales 0-1000+ instances
- **Cache Hit Rate**: >90% (reduces BigQuery costs)
- **Mobile Performance**: 95+ Lighthouse score

## 📊 Data Schema

### Coin Catalog Structure
| Field | Type | Description |
|-------|------|-------------|
| `coin_type` | STRING | "RE" (Regular) or "CC" (Commemorative) |
| `year` | INTEGER | Year issued (1999-2025) |
| `country` | STRING | Issuing country |
| `series` | STRING | Series identifier (e.g., "DEU-01") |
| `value` | FLOAT | Denomination (0.01 to 2.0 euros) |
| `coin_id` | STRING | Unique identifier |
| `image_url` | STRING | ECB coin image URL |
| `feature` | STRING | Description (for commemorative coins) |
| `volume` | STRING | Mintage information |

### Countries Included
🇦🇩 Andorra • 🇦🇹 Austria • 🇧🇪 Belgium • 🇭🇷 Croatia • 🇨🇾 Cyprus • 🇪🇪 Estonia • 🇫🇮 Finland • 🇫🇷 France • 🇩🇪 Germany • 🇬🇷 Greece • 🇮🇪 Ireland • 🇮🇹 Italy • 🇱🇻 Latvia • 🇱🇹 Lithuania • 🇱🇺 Luxembourg • 🇲🇹 Malta • 🇲🇨 Monaco • 🇳🇱 Netherlands • 🇵🇹 Portugal • 🇸🇰 Slovakia • 🇸🇮 Slovenia • 🇪🇸 Spain • 🇻🇦 Vatican City

### Commemorative Series Examples
- **UNESCO World Heritage Sites** (Spain, Malta, etc.)
- **German Federal States (Bundesländer)** series
- **Lithuanian Ethnographic Regions** series
- **Grand Ducal Dynasty** (Luxembourg)
- **European Capital Cities** series
- **Anniversary Commemoratives** (Treaties, institutions, etc.)

## � Responsive Design

### Mobile (320px+)
- Single column coin grid
- Collapsible filters
- Touch-friendly interactions
- Optimized images

### Tablet (768px+)
- Two-column coin grid
- Sidebar filters
- Enhanced hover states

### Desktop (1024px+)
- Multi-column coin grid
- Fixed sidebar navigation
- Advanced filter options
- Keyboard shortcuts

## 🔧 API Endpoints

### Health Check Endpoints
```
GET  /api/health                # Basic health check
GET  /api/ready                 # Readiness check
GET  /api/health/bigquery       # BigQuery connectivity check
```

### Coin Catalog Endpoints
```
GET  /api/coins                 # List coins with filters
GET  /api/coins/{coin_id}       # Get specific coin details
GET  /api/coins/stats           # Get collection statistics
GET  /api/coins/filters         # Get available filter options
GET  /api/coins/group/{group_name} # List coins with group ownership
```

### Ownership Management Endpoints
```
POST /api/ownership/add         # Add coin to user's collection
POST /api/ownership/remove      # Remove coin from user's collection
GET  /api/ownership/user/{user_name}/coins      # Get user's owned coins
GET  /api/ownership/coin/{coin_id}/owners       # Get coin's current owners
GET  /api/ownership/user/{user_name}/history    # Get user's ownership history
```

### Group Management Endpoints
```
POST /groups/                   # Create new group
GET  /groups/                   # List all groups
GET  /groups/{group_key}        # Get group details
PUT  /groups/{group_key}        # Update group
DELETE /groups/{group_key}      # Delete group

POST /groups/{group_key}/users  # Add user to group
GET  /groups/{group_key}/users  # List group members
PUT  /groups/{group_key}/users/{user_name}   # Update group member
DELETE /groups/{group_key}/users/{user_name} # Remove user from group
```

### Admin Endpoints
#### Coin Management
```
POST /api/admin/coins/upload    # Upload coin CSV file
POST /api/admin/coins/import    # Import coins to BigQuery
GET  /api/admin/coins/export    # Export coins as CSV
GET  /api/admin/coins/view      # View coins in admin interface
POST /api/admin/coins/reset     # Reset coin catalog
GET  /api/admin/coins/filter-options # Get coin filter options
```

#### History Management
```
POST /api/admin/history/upload  # Upload history CSV file
POST /api/admin/history/import  # Import history to BigQuery
GET  /api/admin/history/export  # Export history as CSV
POST /api/admin/history/import-csv-direct # Direct CSV import
GET  /api/admin/history/view    # View history in admin interface
POST /api/admin/history/reset   # Reset ownership history
GET  /api/admin/history/filter-options # Get history filter options
```

#### System Management
```
POST /api/admin/clear-cache     # Clear application cache
```

### Page Endpoints (HTML Responses)
```
GET  /                          # Homepage
GET  /catalog                   # Coin catalog page
GET  /coin/{coin_id}            # Individual coin details page
GET  /Admin                     # Admin panel page
GET  /favicon.ico               # Favicon

GET  /{group_name}/catalog      # Group catalog page
GET  /{group_name}/coin/{coin_id} # Group coin details page
GET  /{group_name}              # Group homepage
GET  /{group_name}/{member_name}/catalog  # Member catalog page
GET  /{group_name}/{member_name} # Member homepage
```

### Query Parameters

#### Coin Filtering
```
?coin_type=RE|CC               # Filter by coin type (Regular/Commemorative)
?value=0.01|0.02|0.05|0.10|0.20|0.50|1.00|2.00 # Filter by denomination
?country=Germany               # Filter by country
?commemorative=CC-2024         # Filter by commemorative series
?search=europa                 # Text search across country/feature
?limit=20                      # Results per page (max 2000)
?offset=0                      # Pagination offset
```

#### Group Coin Filtering
```
?coin_type=RE|CC               # Filter by coin type
?value=0.01-2.00               # Filter by denomination
?country=Germany               # Filter by country
?commemorative=CC-2024         # Filter by commemorative series
?owned_by=username             # Filter by specific group member
?ownership_status=owned|missing # Filter by ownership status
?search=europa                 # Text search
?limit=20                      # Results per page
?offset=0                      # Pagination offset
```

#### Ownership History Filtering
```
?group_id=uuid                 # Filter by group ID
```

### Request/Response Examples

#### Add Ownership
```json
POST /api/ownership/add
{
  "name": "john_doe",
  "coin_id": "DEU-01-2002",
  "date": "2024-01-15",
  "created_by": "admin"
}
```

#### Create Group
```json
POST /groups/
{
  "name": "Family Collectors",
  "description": "Family coin collection group"
}
```

#### Add Group Member
```json
POST /groups/family-collectors/users
{
  "user": "john_doe",
  "alias": "John"
}
```

### Authentication & Authorization
- **Admin endpoints**: Require administrative access
- **Group management**: Users can manage their own groups
- **Ownership**: Users can manage their own coin ownership
- **Public access**: Catalog browsing and statistics are publicly accessible

### Rate Limiting
- API endpoints include rate limiting to prevent abuse
- Admin endpoints have stricter limits
- Health check endpoints are unlimited for monitoring

### Error Responses
```json
{
  "detail": "Error description",
  "status_code": 400
}
```

### Interactive API Documentation
- **Swagger UI**: `/api/docs`
- **ReDoc**: `/api/redoc`
- Full OpenAPI specification available at runtime

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally with `python main.py`
5. Submit a pull request

### Development Guidelines
- **Python**: Follow PEP 8, use type hints, document functions
- **JavaScript**: Use ES6+ features, avoid jQuery, modular design
- **HTML**: Semantic markup, accessibility attributes
- **CSS**: Follow Bootstrap conventions, use custom properties
- **Testing**: Write unit tests for new features
- **Documentation**: Update relevant docs with changes

### Adding New Coin Series
For detailed instructions on adding new commemorative series or regular coin series, see [docs/ADDING_SERIES.md](docs/ADDING_SERIES.md).

### Code Quality
```bash
# Format Python code
black app/ --line-length 88

# Lint Python code
flake8 app/ --max-line-length 88

# Type checking
mypy app/

# Run tests
pytest tests/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **European Central Bank** - Official coin images and technical specifications
- **Google Cloud Platform** - Robust infrastructure and BigQuery data warehouse
- **FastAPI** - Modern, high-performance web framework
- **Bootstrap** - Responsive design framework
- **Font Awesome** - Comprehensive icon library

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally with `uvicorn app.main:app --reload`
5. Submit a pull request

### Development Guidelines
- **Python**: Follow PEP 8, use type hints, document functions
- **JavaScript**: Use ES6+ features, avoid jQuery, modular design
- **HTML**: Semantic markup, accessibility attributes
- **CSS**: Follow Bootstrap conventions, use custom properties
- **Testing**: Write unit tests for new features
- **Documentation**: Update relevant docs with changes

### Adding New Coin Series
For detailed instructions on adding new commemorative series or regular coin series, see [docs/ADDING_SERIES.md](docs/ADDING_SERIES.md).

### Code Quality
```bash
# Format Python code
black app/ --line-length 88

# Lint Python code
flake8 app/ --max-line-length 88

# Type checking
mypy app/

# Run tests
pytest tests/
```

## � License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **European Central Bank** - Official coin images and technical specifications
- **Google Cloud Platform** - Robust infrastructure and BigQuery data warehouse
- **FastAPI** - Modern, high-performance web framework
- **Bootstrap** - Responsive design framework
- **Font Awesome** - Comprehensive icon library

## 📚 Documentation

- [Adding New Series Guide](docs/ADDING_SERIES.md) - Comprehensive guide for adding new coin series
- [Implementation Plan](docs/IMPLEMENTATION_PLAN.md) - Technical architecture and decisions
- [Groups Implementation](docs/GROUPS_IMPLEMENTATION_PLAN.md) - Group features design and implementation
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment instructions
- [Modal Implementation](docs/MODAL_IMPLEMENTATION.md) - Coin detail modal system
- [Ownership API](docs/OWNERSHIP_API_SUMMARY.md) - Group ownership API reference
- [Ownership Badges](docs/OWNERSHIP_BADGE_IMPLEMENTATION.md) - Visual ownership indicators
- [API Documentation](https://myeurocoins.org/docs) - Interactive API documentation

## 📧 Contact & Support

- **Website**: [myeurocoins.org](https://myeurocoins.org)
- **Repository**: [github.com/n-dimitrov/coins2025](https://github.com/n-dimitrov/coins2025)
- **Issues**: [Submit an issue](https://github.com/n-dimitrov/coins2025/issues)
- **Discussions**: [GitHub Discussions](https://github.com/n-dimitrov/coins2025/discussions)

---

**Built with ❤️ for Euro coin enthusiasts worldwide** 🌍

*Data source: European Central Bank | Last updated: August 2025*
- Two-column coin grid
- Sidebar filters
- Enhanced navigation

### Desktop (1024px+)
- Four-column coin grid
- Persistent filter sidebar
- Full feature set
- Keyboard shortcuts

## 🎯 Roadmap

### Phase 1: ✅ HTML Prototype (Current)
- [x] Modern UI design
- [x] Responsive layout
- [x] Interactive filters
- [x] Sample coin data
- [x] Country flags integration

### Phase 2: 🚧 React/Next.js Application
- [ ] Next.js setup with TypeScript
- [ ] BigQuery API integration
- [ ] Real-time search functionality
- [ ] Advanced filtering system
- [ ] Coin detail pages

### Phase 3: 🔮 Enhanced Features
- [ ] User authentication
- [ ] Collection tracking
- [ ] Favorites system
- [ ] Export functionality
- [ ] Mobile app (React Native)

### Phase 4: 🌟 Advanced Features
- [ ] Social features
- [ ] Price tracking
- [ ] Educational content
- [ ] Community marketplace
- [ ] API for developers

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Commit with descriptive message**
   ```bash
   git commit -m "feat: add amazing feature"
   ```
5. **Push to your branch**
   ```bash
   git push origin feature/amazing-feature
   ```
6. **Open a Pull Request**

### Development Guidelines
- Follow existing code style
- Add comments for complex logic
- Test on multiple screen sizes
- Ensure accessibility compliance
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **European Central Bank** - Official coin images and data
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide** - Beautiful icon library
- **Inter Font** - Excellent typography
- **Streamlit** - Rapid prototyping framework

## 📧 Contact

- **GitHub**: [@n-dimitrov](https://github.com/n-dimitrov)
- **Project**: [coins2025](https://github.com/n-dimitrov/coins2025)

---

**2025 My EuroCoins** - Discover the beauty of European numismatics! 🪙✨
