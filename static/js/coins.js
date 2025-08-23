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
        this.loading = false;
        
        this.init();
    }

    async init() {
        try {
            await this.loadFilterOptions();
            await this.loadCoins();
            this.setupEventListeners();
            this.renderCoins();
        } catch (error) {
            console.error('Error initializing catalog:', error);
            this.showError('Failed to initialize catalog');
        }
    }

    async loadCoins() {
        this.setLoading(true);
        try {
            const params = new URLSearchParams();
            
            Object.entries(this.currentFilters).forEach(([key, value]) => {
                if (value) params.append(key, value);
            });
            
            params.append('limit', '1000'); // Load all for client-side filtering
            
            const response = await fetch(`/api/coins?${params}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            this.coins = data.coins || [];
            this.applyFilters();
        } catch (error) {
            console.error('Error loading coins:', error);
            this.showError('Failed to load coins');
            this.coins = [];
            this.filteredCoins = [];
        } finally {
            this.setLoading(false);
        }
    }

    async loadFilterOptions() {
        try {
            const response = await fetch('/api/coins/filters');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const options = await response.json();
            
            this.populateCountryFilter(options.countries || []);
            this.populateYearFilter(options.years || []);
        } catch (error) {
            console.error('Error loading filter options:', error);
            // Continue with empty options
        }
    }

    populateCountryFilter(countries) {
        const select = document.getElementById('country-filter');
        if (!select) return;
        
        // Clear existing options except the first one
        select.innerHTML = '<option value="">All Countries</option>';
        
        countries.forEach(country => {
            const option = document.createElement('option');
            option.value = country;
            option.textContent = `${this.getCountryFlag(country)} ${country}`;
            select.appendChild(option);
        });
    }

    populateYearFilter(years) {
        const select = document.getElementById('year-filter');
        if (!select) return;
        
        // Clear existing options except the first one
        select.innerHTML = '<option value="">All Years</option>';
        
        years.forEach(year => {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = year;
            select.appendChild(option);
        });
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
                    coin.feature?.toLowerCase() || '',
                    coin.series?.toLowerCase() || ''
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
        if (!container) return;
        
        const startIndex = (this.currentPage - 1) * this.coinsPerPage;
        const endIndex = startIndex + this.coinsPerPage;
        const coinsToShow = this.filteredCoins.slice(startIndex, endIndex);

        if (coinsToShow.length === 0) {
            container.innerHTML = `
                <div class="col-12 text-center py-5">
                    <div class="empty-state">
                        <i class="fas fa-search fa-3x text-muted mb-3"></i>
                        <h4>No coins found</h4>
                        <p class="text-muted">Try adjusting your filters or search terms</p>
                    </div>
                </div>
            `;
            return;
        }

        container.innerHTML = coinsToShow.map(coin => this.createCoinCard(coin)).join('');
        this.renderPagination();
    }

    createCoinCard(coin) {
        const flag = this.getCountryFlag(coin.country);
        const typeClass = coin.coin_type === 'RE' ? 'bg-success' : 'bg-primary';
        const typeName = coin.coin_type === 'RE' ? 'Regular' : 'Commemorative';
        const imageUrl = coin.image_url || '/static/images/coin-placeholder.png';

        return `
            <div class="col-md-6 col-lg-4 col-xl-3 mb-4">
                <div class="card coin-card h-100">
                    <div class="position-relative">
                        <img 
                            src="${imageUrl}" 
                            class="card-img-top coin-image" 
                            alt="${coin.country} ${coin.value} Euro"
                            loading="lazy"
                            onerror="this.src='/static/images/coin-placeholder.png'"
                        >
                        <span class="badge ${typeClass} position-absolute top-0 start-0 m-2">
                            ${coin.coin_type}
                        </span>
                    </div>
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <h6 class="card-title mb-0">
                                <span class="country-flag me-2">${flag}</span>${coin.country}
                            </h6>
                            <span class="h5 mb-0 text-primary fw-bold">€${coin.value}</span>
                        </div>
                        <p class="card-text text-muted small">${typeName} • ${coin.year}</p>
                        ${coin.feature ? `<p class="card-text small text-truncate" title="${coin.feature}">${coin.feature}</p>` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    renderPagination() {
        const container = document.getElementById('pagination');
        if (!container) return;
        
        const totalPages = Math.ceil(this.filteredCoins.length / this.coinsPerPage);
        
        if (totalPages <= 1) {
            container.innerHTML = '';
            return;
        }

        let pagination = '';
        
        // Previous button
        if (this.currentPage > 1) {
            pagination += `
                <li class="page-item">
                    <a class="page-link" href="#" data-page="${this.currentPage - 1}">Previous</a>
                </li>
            `;
        }

        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            if (i === this.currentPage) {
                pagination += `<li class="page-item active"><span class="page-link">${i}</span></li>`;
            } else if (i === 1 || i === totalPages || (i >= this.currentPage - 2 && i <= this.currentPage + 2)) {
                pagination += `<li class="page-item"><a class="page-link" href="#" data-page="${i}">${i}</a></li>`;
            } else if (i === this.currentPage - 3 || i === this.currentPage + 3) {
                pagination += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
        }

        // Next button
        if (this.currentPage < totalPages) {
            pagination += `
                <li class="page-item">
                    <a class="page-link" href="#" data-page="${this.currentPage + 1}">Next</a>
                </li>
            `;
        }

        container.innerHTML = pagination;

        // Add click handlers for pagination
        container.querySelectorAll('a.page-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(e.target.dataset.page);
                if (page && page !== this.currentPage) {
                    this.currentPage = page;
                    this.renderCoins();
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                }
            });
        });
    }

    updateResultsCount() {
        const counter = document.getElementById('results-count');
        if (!counter) return;
        
        const total = this.filteredCoins.length;
        const showing = Math.min(this.coinsPerPage, total - (this.currentPage - 1) * this.coinsPerPage);
        const start = total === 0 ? 0 : (this.currentPage - 1) * this.coinsPerPage + 1;
        const end = (this.currentPage - 1) * this.coinsPerPage + showing;
        
        if (total === 0) {
            counter.textContent = 'No coins found';
        } else {
            counter.textContent = `Showing ${start}-${end} of ${total} coins`;
        }
    }

    getCountryFlag(country) {
        const flags = {
            'Germany': '🇩🇪', 'France': '🇫🇷', 'Italy': '🇮🇹', 'Spain': '🇪🇸',
            'Finland': '🇫🇮', 'Croatia': '🇭🇷', 'Luxembourg': '🇱🇺', 'Belgium': '🇧🇪',
            'Austria': '🇦🇹', 'Netherlands': '🇳🇱', 'Portugal': '🇵🇹', 'Greece': '🇬🇷',
            'Ireland': '🇮🇪', 'Slovenia': '🇸🇮', 'Slovakia': '🇸🇰', 'Estonia': '🇪🇪',
            'Latvia': '🇱🇻', 'Lithuania': '🇱🇹', 'Malta': '🇲🇹', 'Cyprus': '🇨🇾',
            'Monaco': '🇲🇨', 'Vatican City': '🇻🇦', 'Andorra': '🇦🇩'
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

    setLoading(loading) {
        this.loading = loading;
        const spinner = document.getElementById('loading-spinner');
        if (spinner) {
            spinner.style.display = loading ? 'block' : 'none';
        }
    }

    showError(message) {
        console.error(message);
        // You could implement a toast notification here
    }
}
