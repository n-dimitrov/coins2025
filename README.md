# My EuroCoins 🪙

A modern, interactive web application for exploring and cataloging Euro coins from 1999 to 2025. Built with Python FastAPI backend and vanilla JavaScript frontend, deployed on Google Cloud Run for optimal performance and cost efficiency.

![My EuroCoins Banner](https://img.shields.io/badge/My%20EuroCoins-2025-blue?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJMMTMuMDkgOC4yNkwyMCA5TDEzLjA5IDE1Ljc0TDEyIDIyTDEwLjkxIDE1Ljc0TDQgOUwxMC45MSA4LjI2TDEyIDJaIiBzdHJva2U9IiNGRkYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=)

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Google Cloud CLI
- Docker (for deployment)

### Development Setup
```bash
# Clone repository
git clone https://github.com/n-dimitrov/coins2025.git
cd coins2025

# Setup Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload --port 8000

# Visit: http://localhost:8000
```

### Production Deployment
```bash
# Deploy to Google Cloud Run
gcloud builds submit --config cloudbuild.yaml

# Or use the deployment script
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

## 🌟 Features

### 📚 **Comprehensive Catalog**
- **832 Total Coins** from 1999-2025
- **284 Regular Coins** (circulation coins)
- **547 Commemorative Coins** (special editions)
- **27 Countries** including all eurozone nations

### 🎨 **Modern UI Design**
- **Responsive Design** - Works on mobile, tablet, and desktop
- **Bootstrap 5** for consistent styling
- **Interactive Filters** for easy browsing
- **Country Flags** for quick identification
- **Real Coin Images** from European Central Bank

### 🔍 **Advanced Search & Filtering**
- **Text Search** by country, feature, or description
- **Filter by Type** - Regular (RE) or Commemorative (CC)
- **Year Range** selection (1999-2025)
- **Denomination** filtering (1¢ to €2)
- **Country Selection** with multi-select

### ⚡ **Performance & Technology**
- **FastAPI** backend with async BigQuery integration
- **Vanilla JavaScript** frontend (no framework overhead)
- **In-memory caching** to reduce BigQuery costs
- **Google Cloud Run** deployment with auto-scaling
- **Docker** containerization for consistent deployment

## 🏗️ Tech Stack

### Backend
- **Python 3.11** - Core runtime
- **FastAPI** - Modern, fast web framework
- **Uvicorn** - ASGI server
- **Google Cloud BigQuery** - Data warehouse
- **Pydantic** - Data validation

### Frontend
- **HTML5 & CSS3** - Core web technologies
- **Vanilla JavaScript** - No framework dependencies
- **Bootstrap 5** - Responsive CSS framework
- **Font Awesome 6** - Icon library

### Infrastructure
- **Google Cloud Run** - Serverless containers
- **Google Cloud Build** - CI/CD pipeline
- **Docker** - Containerization
- **Google BigQuery** - Database (existing)

## 📁 Project Structure

```
coins2025/
├── app/                        # FastAPI application
│   ├── main.py                 # App setup and routes
│   ├── routers/                # API route handlers
## 💰 Cost & Performance

### Monthly Operating Costs
- **Google Cloud Run**: $1-3 (scales to zero when not in use)
- **BigQuery**: $0 (existing dataset, minimal additional queries)
- **Cloud Build**: $0 (free tier sufficient)
- **Container Registry**: $0.10 (minimal storage)
- **Total**: **$1-4/month** for thousands of users

### Performance Metrics
- **Cold Start**: <2 seconds (Python FastAPI)
- **Response Time**: <500ms (with caching)
- **Availability**: 99.95% (Google Cloud Run SLA)
- **Scalability**: Auto-scales 0-1000 instances

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

### Public Endpoints
```
GET  /                     # Homepage
GET  /catalog              # Catalog page
GET  /coin/{coin_id}       # Individual coin details

GET  /api/health           # Health check
GET  /api/coins            # List coins with filters
GET  /api/coins/{coin_id}  # Get specific coin
GET  /api/coins/stats      # Get collection statistics
GET  /api/coins/filters    # Get filter options
```

### Query Parameters
```
?coin_type=RE|CC          # Filter by type
?country=Germany          # Filter by country
?year=2023               # Filter by year
?search=europa           # Text search
?limit=20                # Results per page
?offset=0                # Pagination offset
```

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally with `uvicorn app.main:app --reload`
5. Submit a pull request

### Code Standards
- Python: Follow PEP 8
- JavaScript: Use ES6+ features
- HTML: Semantic markup
- CSS: Follow Bootstrap conventions

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **European Central Bank** for coin images and data
- **Google Cloud Platform** for infrastructure
- **FastAPI** for the excellent web framework
- **Bootstrap** for responsive design components

## 📧 Contact

- **Repository**: [github.com/n-dimitrov/coins2025](https://github.com/n-dimitrov/coins2025)
- **Issues**: [Submit an issue](https://github.com/n-dimitrov/coins2025/issues)

---

**Built with ❤️ for Euro coin enthusiasts worldwide** 🌍
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
