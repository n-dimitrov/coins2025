# Next.js Project Structure

## 📁 Proposed Directory Structure

```
my-eurocoins/                          # Root Next.js project
├── README.md                          # Project documentation
├── package.json                       # Dependencies and scripts
├── next.config.js                     # Next.js configuration
├── tailwind.config.js                 # Tailwind CSS configuration
├── tsconfig.json                      # TypeScript configuration
├── .env.local                         # Environment variables
├── .env.example                       # Environment variables template
├── .gitignore                         # Git ignore rules
├── .eslintrc.json                     # ESLint configuration
├── prettier.config.js                 # Prettier configuration
├── playwright.config.ts               # E2E testing configuration
├── jest.config.js                     # Unit testing configuration
├── vercel.json                        # Deployment configuration
│
├── public/                            # Static assets
│   ├── favicon.ico                    # App favicon
│   ├── logo.svg                       # App logo
│   ├── images/                        # Static images
│   └── manifest.json                  # PWA manifest
│
├── src/                               # Source code
│   ├── app/                           # Next.js App Router
│   │   ├── layout.tsx                 # Root layout
│   │   ├── page.tsx                   # Homepage
│   │   ├── loading.tsx                # Global loading UI
│   │   ├── error.tsx                  # Global error UI
│   │   ├── not-found.tsx             # 404 page
│   │   ├── globals.css               # Global styles
│   │   │
│   │   ├── catalog/                   # Catalog pages
│   │   │   ├── page.tsx              # Main catalog page
│   │   │   ├── loading.tsx           # Catalog loading
│   │   │   └── [id]/                 # Individual coin pages
│   │   │       ├── page.tsx          # Coin detail page
│   │   │       └── loading.tsx       # Coin detail loading
│   │   │
│   │   └── api/                       # API routes
│   │       ├── coins/                 # Coins API
│   │       │   ├── route.ts          # GET /api/coins
│   │       │   ├── [id]/route.ts     # GET /api/coins/[id]
│   │       │   └── search/route.ts   # GET /api/coins/search
│   │       ├── countries/route.ts     # Countries API
│   │       ├── filters/route.ts       # Filter options API
│   │       └── stats/route.ts         # Statistics API
│   │
│   ├── components/                    # React components
│   │   ├── ui/                        # shadcn/ui components
│   │   │   ├── button.tsx            # Button variants
│   │   │   ├── input.tsx             # Input fields
│   │   │   ├── select.tsx            # Select dropdowns
│   │   │   ├── card.tsx              # Card component
│   │   │   ├── badge.tsx             # Badge component
│   │   │   ├── skeleton.tsx          # Loading skeletons
│   │   │   ├── pagination.tsx        # Pagination component
│   │   │   ├── slider.tsx            # Range slider
│   │   │   ├── checkbox.tsx          # Checkbox component
│   │   │   ├── tooltip.tsx           # Tooltip component
│   │   │   └── dialog.tsx            # Modal dialog
│   │   │
│   │   ├── layout/                    # Layout components
│   │   │   ├── Navigation.tsx        # Top navigation
│   │   │   ├── Footer.tsx            # Footer component
│   │   │   ├── MobileMenu.tsx        # Mobile navigation
│   │   │   └── Sidebar.tsx           # Filter sidebar
│   │   │
│   │   ├── hero/                      # Hero section components
│   │   │   ├── HeroSection.tsx       # Main hero component
│   │   │   ├── SearchBar.tsx         # Global search
│   │   │   └── StatsGrid.tsx         # Statistics cards
│   │   │
│   │   ├── catalog/                   # Catalog-specific components
│   │   │   ├── CoinGrid.tsx          # Coin grid layout
│   │   │   ├── CoinCard.tsx          # Individual coin card
│   │   │   ├── CoinDetail.tsx        # Coin detail view
│   │   │   ├── FilterSidebar.tsx     # Filter controls
│   │   │   ├── Toolbar.tsx           # Sort/view controls
│   │   │   ├── SearchResults.tsx     # Search results
│   │   │   └── EmptyState.tsx        # No results state
│   │   │
│   │   ├── filters/                   # Filter components
│   │   │   ├── CoinTypeFilter.tsx    # RE/CC filter
│   │   │   ├── CountryFilter.tsx     # Country selection
│   │   │   ├── YearRangeFilter.tsx   # Year range slider
│   │   │   ├── DenominationFilter.tsx # Value checkboxes
│   │   │   ├── SeriesFilter.tsx      # Series selection
│   │   │   └── FilterChips.tsx       # Active filter chips
│   │   │
│   │   ├── shared/                    # Shared components
│   │   │   ├── CountryFlag.tsx       # Country flag emoji
│   │   │   ├── CoinTypeBadge.tsx     # RE/CC badges
│   │   │   ├── LoadingSpinner.tsx    # Loading indicator
│   │   │   ├── ErrorMessage.tsx      # Error display
│   │   │   ├── NoResults.tsx         # Empty state
│   │   │   └── BackButton.tsx        # Navigation back
│   │   │
│   │   └── providers/                 # Context providers
│   │       ├── QueryProvider.tsx     # React Query setup
│   │       ├── ThemeProvider.tsx     # Theme context
│   │       └── FilterProvider.tsx    # Filter state context
│   │
│   ├── lib/                           # Utility libraries
│   │   ├── utils.ts                  # General utilities
│   │   ├── cn.ts                     # Class name utility
│   │   ├── constants.ts              # App constants
│   │   ├── validations.ts            # Zod schemas
│   │   ├── bigquery.ts               # BigQuery client
│   │   ├── cache.ts                  # Caching utilities
│   │   ├── countries.ts              # Country data
│   │   └── denominations.ts          # Coin denominations
│   │
│   ├── hooks/                         # Custom React hooks
│   │   ├── useSearch.ts              # Search functionality
│   │   ├── useFilters.ts             # Filter management
│   │   ├── useCoins.ts               # Coin data fetching
│   │   ├── useDebounce.ts            # Debounced values
│   │   ├── useLocalStorage.ts        # Local storage state
│   │   ├── useMediaQuery.ts          # Responsive utilities
│   │   └── usePagination.ts          # Pagination logic
│   │
│   ├── store/                         # State management
│   │   ├── searchStore.ts            # Search state (Zustand)
│   │   ├── filterStore.ts            # Filter state
│   │   ├── viewStore.ts              # View preferences
│   │   └── index.ts                  # Store exports
│   │
│   ├── types/                         # TypeScript types
│   │   ├── coin.ts                   # Coin data types
│   │   ├── country.ts                # Country types
│   │   ├── filter.ts                 # Filter types
│   │   ├── api.ts                    # API response types
│   │   └── index.ts                  # Type exports
│   │
│   └── styles/                        # Additional styles
│       ├── globals.css               # Global CSS
│       ├── components.css            # Component styles
│       └── animations.css            # Custom animations
│
├── tests/                             # Test files
│   ├── __mocks__/                    # Test mocks
│   │   ├── bigquery.ts              # BigQuery mock
│   │   └── coins.ts                 # Mock coin data
│   ├── components/                   # Component tests
│   │   ├── CoinCard.test.tsx        # Coin card tests
│   │   ├── FilterSidebar.test.tsx   # Filter tests
│   │   └── SearchBar.test.tsx       # Search tests
│   ├── hooks/                        # Hook tests
│   │   ├── useSearch.test.ts        # Search hook tests
│   │   └── useFilters.test.ts       # Filter hook tests
│   ├── pages/                        # Page tests
│   │   ├── catalog.test.tsx         # Catalog page tests
│   │   └── coin-detail.test.tsx     # Detail page tests
│   ├── e2e/                          # End-to-end tests
│   │   ├── catalog.spec.ts          # Catalog E2E tests
│   │   ├── search.spec.ts           # Search E2E tests
│   │   └── filters.spec.ts          # Filter E2E tests
│   └── setup.ts                      # Test setup
│
├── docs/                              # Documentation
│   ├── api.md                        # API documentation
│   ├── components.md                 # Component guide
│   ├── deployment.md                 # Deployment guide
│   └── development.md                # Development setup
│
└── scripts/                           # Build and utility scripts
    ├── build.sh                      # Production build
    ├── dev.sh                        # Development server
    ├── test.sh                       # Run all tests
    ├── lint.sh                       # Linting and formatting
    └── deploy.sh                     # Deployment script
```

## 📦 Key Dependencies

### Core Dependencies
```json
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "typescript": "^5.0.0",
    "@next/font": "^14.0.0",
    
    "@tanstack/react-query": "^5.0.0",
    "zustand": "^4.4.0",
    "react-hook-form": "^7.47.0",
    "zod": "^3.22.0",
    
    "@google-cloud/bigquery": "^7.0.0",
    "redis": "^4.6.0",
    
    "tailwindcss": "^3.3.0",
    "@tailwindcss/forms": "^0.5.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.0.0",
    
    "framer-motion": "^10.16.0",
    "lucide-react": "^0.290.0",
    
    "next-themes": "^0.2.0",
    "react-intersection-observer": "^9.5.0",
    "use-debounce": "^10.0.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/react": "^18.0.0",
    "@types/react-dom": "^18.0.0",
    
    "eslint": "^8.0.0",
    "eslint-config-next": "^14.0.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "prettier": "^3.0.0",
    "prettier-plugin-tailwindcss": "^0.5.0",
    
    "jest": "^29.0.0",
    "jest-environment-jsdom": "^29.0.0",
    "@testing-library/react": "^13.0.0",
    "@testing-library/jest-dom": "^6.0.0",
    "@testing-library/user-event": "^14.0.0",
    
    "@playwright/test": "^1.40.0",
    
    "husky": "^8.0.0",
    "lint-staged": "^15.0.0",
    "commitlint": "^18.0.0",
    "@commitlint/cli": "^18.0.0",
    "@commitlint/config-conventional": "^18.0.0"
  }
}
```

## 🚀 Development Scripts

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "lint:fix": "next lint --fix",
    "type-check": "tsc --noEmit",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    
    "db:generate": "prisma generate",
    "db:push": "prisma db push",
    "db:studio": "prisma studio",
    
    "prepare": "husky install",
    "commit": "git-cz",
    "release": "semantic-release"
  }
}
```

## 🔧 Configuration Files

### Next.js Configuration
```javascript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  images: {
    domains: ['www.ecb.europa.eu'],
    formats: ['image/webp', 'image/avif'],
  },
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },
};

module.exports = nextConfig;
```

### Tailwind Configuration
```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        // Add custom euro coin colors
        euro: {
          gold: "#FFD700",
          silver: "#C0C0C0",
          copper: "#B87333",
        },
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-in-out",
        "slide-up": "slideUp 0.3s ease-out",
        "coin-flip": "coinFlip 0.6s ease-in-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate"), require("@tailwindcss/forms")],
};
```

This structure provides a solid foundation for building the My EuroCoins application with clear separation of concerns, scalable architecture, and modern development practices! 🏗️
