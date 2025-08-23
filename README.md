# My EuroCoins 🪙

A modern, interactive web application for exploring and cataloging Euro coins from 1999 to 2025. Browse through regular circulation and commemorative coins from all eurozone countries with a beautiful, responsive interface.

![My EuroCoins Banner](https://img.shields.io/badge/My%20EuroCoins-2025-blue?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJMMTMuMDkgOC4yNkwyMCA5TDEzLjA5IDE1Ljc0TDEyIDIyTDEwLjkxIDE1Ljc0TDQgOUwxMC45MSA4LjI2TDEyIDJaIiBzdHJva2U9IiNGRkYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=)

## 🌟 Features

### 📚 **Comprehensive Catalog**
- **832 Total Coins** from 1999-2025
- **284 Regular Coins** (circulation coins)
- **547 Commemorative Coins** (special editions)
- **27 Countries** including all eurozone nations

### 🎨 **Modern UI Design**
- **Responsive Design** - Works on mobile, tablet, and desktop
- **Clean Interface** with Tailwind CSS
- **Interactive Filters** for easy browsing
- **Country Flags** for quick identification
- **Real Coin Images** from European Central Bank

### 🔍 **Advanced Search & Filtering**
- **Text Search** by country, feature, or description
- **Filter by Type** - Regular (RE) or Commemorative (CC)
- **Year Range** selection (1999-2025)
- **Denomination** filtering (1¢ to €2)
- **Country Selection** with multi-select

### 💡 **User Experience**
- **Fast Performance** with optimized loading
- **Intuitive Navigation** with clean header
- **Hover Effects** and smooth animations
- **Mobile-First** responsive design

## 🏗️ Project Structure

```
coins2025/
├── ui-prototype/           # HTML/CSS prototype
│   └── index.html         # Main UI prototype file
├── streamlit/             # Original Streamlit application
│   ├── catalog.py         # Streamlit coin browser
│   ├── import_catalog.py  # BigQuery data import
│   ├── import_history.py  # Collection history import
│   └── requirements.txt   # Python dependencies
├── data/                  # Coin data files
│   ├── catalog.csv        # Complete coin catalog
│   ├── cc_catalog.json    # Commemorative coins (JSON)
│   ├── re_catalog.json    # Regular coins (JSON)
│   └── history.csv        # Collection history
├── tools/                 # Data collection scripts
│   ├── scrape_cc_catalog.py  # Scrape commemorative coins
│   ├── scrape_re_catalog.py  # Scrape regular coins
│   ├── generate_cc_csv.py    # Generate CC CSV
│   └── generate_re_csv.py    # Generate RE CSV
└── credentials/           # BigQuery service account
    └── service_account.json
```

## 🚀 Getting Started

### Prerequisites
- Modern web browser (Chrome, Firefox, Safari, Edge)
- For development: Git, Node.js (optional for future React/Next.js version)

### Quick Start (HTML Prototype)
1. **Clone the repository**
   ```bash
   git clone https://github.com/n-dimitrov/coins2025.git
   cd coins2025
   ```

2. **Open the prototype**
   ```bash
   # Open in browser
   open ui-prototype/index.html
   # Or serve with a local server
   python -m http.server 8000
   # Then visit http://localhost:8000/ui-prototype/
   ```

### Streamlit Version Setup
1. **Install Python dependencies**
   ```bash
   cd streamlit
   pip install -r requirements.txt
   ```

2. **Configure BigQuery credentials**
   ```bash
   cp config_template.py config.py
   # Edit config.py with your settings
   ```

3. **Run the Streamlit app**
   ```bash
   streamlit run catalog.py
   ```

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

## 🛠️ Technology Stack

### Current (HTML Prototype)
- **HTML5** - Semantic markup
- **Tailwind CSS** - Utility-first styling
- **Vanilla JavaScript** - Interactive functionality
- **Lucide Icons** - Modern icon library
- **Inter Font** - Clean typography

### Backend (Streamlit Version)
- **Python 3.8+** - Core language
- **Streamlit** - Web framework
- **BigQuery** - Data warehouse
- **Pandas** - Data manipulation
- **Google Cloud SDK** - Cloud integration

### Planned (Future React/Next.js Version)
- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Consistent styling
- **shadcn/ui** - Component library
- **Vercel** - Deployment platform

## 📱 Responsive Design

### Mobile (320px+)
- Single column coin grid
- Collapsible filters
- Touch-friendly interactions
- Optimized images

### Tablet (768px+)
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
