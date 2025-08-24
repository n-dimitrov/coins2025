class CoinCatalog {
    constructor() {
        this.coins = [];
        this.filteredCoins = [];
        this.currentFilters = {
            coin_type: '',
            value: '',
            country: '',
            commemorative: '',
            search: ''
        };
        this.currentPage = 1;
        this.coinsPerPage = 20;
        this.loading = false;
        this.currentCoinIndex = 0;
        
        // Static mapping for special commemorative series
        this.commemorativeLabels = {
            'CC-2004': '2004',
            'CC-2005': '2005',
            'CC-2006': '2006',
            'CC-2007': '2007',
            'CC-2007-TOR': '2007 Treaty of Rome',
            'CC-2008': '2008',
            'CC-2009': '2009',
            'CC-2009-EMU': '2009 Economic and Monetary Union',
            'CC-2010': '2010',
            'CC-2011': '2011',
            'CC-2012': '2012',
            'CC-2012-TYE': '2012 Ten Years of Euro',
            'CC-2013': '2013',
            'CC-2014': '2014',
            'CC-2015': '2015',
            'CC-2015-EUF': '2015 European Flag',
            'CC-2016': '2016',
            'CC-2017': '2017',
            'CC-2018': '2018',
            'CC-2019': '2019',
            'CC-2020': '2020',
            'CC-2021': '2021',
            'CC-2022': '2022',
            'CC-2022-ERA': '2022 Erasmus Programme',
            'CC-2023': '2023',
            'CC-2024': '2024'
        };

        // Static mapping for regular series
        this.regularLabels = {
            'AND-01': 'Andorra (2014 - now)',
            'AUT-01': 'Austria (2002 - now)', 
            'BEL-01': 'Belgium (1999 - 2008)',
            'BEL-02': 'Belgium (2008 - 2014)',
            'BEL-03': 'Belgium (2014 - now)',
            'CYP-01': 'Cyprus (2008 - now)',
            'DEU-01': 'Germany (1999 - now)',
            'ESP-01': 'Spain (1999 - 2014)',
            'ESP-02': 'Spain (2014 - 2015)',
            'ESP-03': 'Spain (2015 - now)',
            'EST-01': 'Estonia (2011 - now)',
            'FIN-01': 'Finland (1999 - 2007)',
            'FIN-02': 'Finland (2007 - now)',
            'FRA-01': 'France (1999 - 2022)',
            'FRA-02': 'France (2022 - now)',
            'GRC-01': 'Greece (2002 - now)',
            'HRV-01': 'Croatia (2023 - now)',
            'IRL-01': 'Ireland (2002 - now)',
            'ITA-01': 'Italy (1999 - now)',
            'LTU-01': 'Lithuania (2015 - now)',
            'LUX-01': 'Luxembourg (2002 - now)',
            'LVA-01': 'Latvia (2014 - now)',
            'MCO-01': 'Monaco (2001 - 2006)',
            'MCO-02': 'Monaco (2006 - now)',
            'MLT-01': 'Malta (2008 - now)',
            'NLD-01': 'Netherlands (1999 - 2014)',
            'NLD-02': 'Netherlands (2014 - now)',
            'PRT-01': 'Portugal (2002 - now)',
            'SMR-01': 'San Marino (2006 - 2017)',
            'SMR-02': 'San Marino (2017 - now)',
            'SVK-01': 'Slovakia (2009 - now)',
            'SVN-01': 'Slovenia (2007 - now)',
            'VAT-01': 'Vatican City (2002 - 2005)',
            'VAT-02': 'Vatican City (2005 - 2006)',
            'VAT-03': 'Vatican City (2006 - 2014)',
            'VAT-04': 'Vatican City (2014 - 2017)',
            'VAT-05': 'Vatican City (2017 - now)'
        };
        
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
            
            const response = await fetch(`/api/coins/?${params}`);
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
            this.populateValueFilter(options.denominations || []);
            this.populateCommemorativeFilter(options.commemoratives || []);
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

    populateValueFilter(denominations) {
        const select = document.getElementById('value-filter');
        if (!select) return;
        
        // Clear existing options except the first one
        select.innerHTML = '<option value="">All Values</option>';
        
        denominations.forEach(value => {
            const option = document.createElement('option');
            option.value = value;
            // Format value to always show 2 decimal places
            const formattedValue = parseFloat(value).toFixed(2);
            option.textContent = `€${formattedValue}`;
            select.appendChild(option);
        });
    }

    populateCommemorativeFilter(commemoratives) {
        const select = document.getElementById('commemorative-filter');
        if (!select) return;
        
        // Clear existing options except the first one
        select.innerHTML = '<option value="">All Commemoratives</option>';
        
        // Sort commemoratives in descending order (most recent first)
        const sortedCommemorative = commemoratives.sort((a, b) => {
            // Extract year from series code (e.g., CC-2024 -> 2024)
            const yearA = parseInt(a.split('-')[1]) || 0;
            const yearB = parseInt(b.split('-')[1]) || 0;
            return yearB - yearA; // Descending order
        });
        
        sortedCommemorative.forEach(commemorative => {
            const option = document.createElement('option');
            option.value = commemorative;
            // Use the label from mapping, or fallback to the original value
            const label = this.commemorativeLabels[commemorative] || commemorative;
            option.textContent = label;
            select.appendChild(option);
        });
    }

    applyFilters() {
        this.filteredCoins = this.coins.filter(coin => {
            if (this.currentFilters.coin_type && coin.coin_type !== this.currentFilters.coin_type) {
                return false;
            }
            if (this.currentFilters.value && coin.value.toString() !== this.currentFilters.value) {
                return false;
            }
            if (this.currentFilters.country && coin.country !== this.currentFilters.country) {
                return false;
            }
            if (this.currentFilters.commemorative && coin.series !== this.currentFilters.commemorative) {
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
        
        // Format value to always show 2 decimal places
        const formattedValue = parseFloat(coin.value).toFixed(2);

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
                    <div class="card-body coin-card-clickable" data-coin-id="${coin.coin_id}" style="cursor: pointer;">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <h6 class="card-title mb-0">
                                <span class="country-flag me-2">${flag}</span>${coin.country}
                            </h6>
                            <span class="h5 mb-0 text-primary fw-bold">€${formattedValue}</span>
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

        document.getElementById('value-filter')?.addEventListener('change', (e) => {
            this.currentFilters.value = e.target.value;
            this.applyFilters();
        });

        document.getElementById('country-filter')?.addEventListener('change', (e) => {
            this.currentFilters.country = e.target.value;
            this.applyFilters();
        });

        document.getElementById('commemorative-filter')?.addEventListener('change', (e) => {
            this.currentFilters.commemorative = e.target.value;
            this.applyFilters();
        });

        // Clear filters
        document.getElementById('clear-filters')?.addEventListener('click', () => {
            this.currentFilters = { coin_type: '', value: '', country: '', commemorative: '', search: '' };
            document.getElementById('search-input').value = '';
            document.getElementById('type-filter').value = '';
            document.getElementById('value-filter').value = '';
            document.getElementById('country-filter').value = '';
            document.getElementById('commemorative-filter').value = '';
            this.applyFilters();
        });

        // Coin card click handlers
        this.setupCoinCardClickHandlers();
    }

    setupCoinCardClickHandlers() {
        document.addEventListener('click', (e) => {
            const clickableArea = e.target.closest('.coin-card-clickable');
            if (clickableArea) {
                const coinId = clickableArea.dataset.coinId;
                const coin = this.coins.find(c => c.coin_id === coinId);
                if (coin) {
                    this.showCoinDetailModal(coin);
                }
            }
        });
    }

    async showCoinDetailModal(coin) {
        try {
            // Set current coin index for navigation
            this.currentCoinIndex = this.filteredCoins.findIndex(c => c.coin_id === coin.coin_id);
            
            // Fetch additional coin details if needed
            const detailedCoin = await this.fetchCoinDetails(coin.coin_id);
            
            // Populate modal content
            this.populateCoinModal(detailedCoin || coin);
            
            // Show modal
            const modal = new bootstrap.Modal(document.getElementById('coinDetailModal'));
            modal.show();
            
            // Set up navigation handlers
            this.setupModalNavigation();
        } catch (error) {
            console.error('Error showing coin details:', error);
            // Fallback to basic coin data
            this.currentCoinIndex = this.filteredCoins.findIndex(c => c.coin_id === coin.coin_id);
            this.populateCoinModal(coin);
            const modal = new bootstrap.Modal(document.getElementById('coinDetailModal'));
            modal.show();
            this.setupModalNavigation();
        }
    }

    async fetchCoinDetails(coinId) {
        try {
            const response = await fetch(`/api/coins/${coinId}`);
            if (response.ok) {
                const data = await response.json();
                return data.coin;
            }
        } catch (error) {
            console.error('Error fetching coin details:', error);
        }
        return null;
    }

    populateCoinModal(coin) {
        const flag = this.getCountryFlag(coin.country);
        const formattedValue = parseFloat(coin.value).toFixed(2);
        const typeClass = coin.coin_type === 'RE' ? 'bg-success' : 'bg-primary';
        const typeName = coin.coin_type === 'RE' ? 'Regular' : 'Commemorative';
        const commemorativeLabel = this.commemorativeLabels[coin.series] || this.regularLabels[coin.series] || coin.series;
        
        // Create image gallery - for now use single image, can be enhanced later
        const mainImage = coin.image_url || '/static/images/coin-placeholder.png';
        
        const modalContent = `
            <div class="coin-detail-container">
                <div class="coin-header">
                    <div class="coin-title">
                        <span class="country-flag">${flag}</span>
                        ${coin.country}
                        <span class="coin-value-badge">€${formattedValue}</span>
                    </div>
                    <div class="coin-year">${coin.year}</div>
                </div>
                
                <div class="coin-navigation">
                    <button class="nav-btn nav-prev" onclick="window.coinCatalog.navigateToPreviousCoin()" 
                            ${this.currentCoinIndex === 0 ? 'disabled' : ''}>
                        <i class="fas fa-chevron-left"></i>
                    </button>
                    
                    <div class="coin-position">
                        ${this.currentCoinIndex + 1} of ${this.filteredCoins.length}
                    </div>
                    
                    <button class="nav-btn nav-next" onclick="window.coinCatalog.navigateToNextCoin()"
                            ${this.currentCoinIndex === this.filteredCoins.length - 1 ? 'disabled' : ''}>
                        <i class="fas fa-chevron-right"></i>
                    </button>
                </div>
                
                <div class="coin-type-section">
                    <span class="badge ${typeClass}">
                        ${typeName}
                    </span>
                </div>
                
                <div class="coin-image-section">
                    <img src="${mainImage}" 
                         class="coin-main-image" 
                         id="coinMainImage"
                         alt="${coin.country} ${coin.value} Euro"
                         onerror="this.src='/static/images/coin-placeholder.png'">
                </div>
                
                <div class="coin-info-section">
                    <div class="coin-details-wrapper">
                        <div class="coin-simple-info">
                            <div class="info-line">${commemorativeLabel}</div>
                            ${coin.volume ? `<div class="info-line">${coin.volume}</div>` : ''}
                            ${coin.feature ? `<div class="info-description">${coin.feature}</div>` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.querySelector('#coinDetailModal .modal-body').innerHTML = modalContent;
    }

    setupModalNavigation() {
        const modal = document.getElementById('coinDetailModal');
        const modalBody = modal.querySelector('.modal-body');
        
        // Remove existing event listeners
        this.removeModalNavigation();
        
        // Keyboard navigation
        this.modalKeyHandler = (e) => {
            if (modal.classList.contains('show')) {
                if (e.key === 'ArrowLeft') {
                    e.preventDefault();
                    this.navigateToPreviousCoin();
                } else if (e.key === 'ArrowRight') {
                    e.preventDefault();
                    this.navigateToNextCoin();
                }
            }
        };
        
        document.addEventListener('keydown', this.modalKeyHandler);
        
        // Touch/swipe navigation
        let startX = 0;
        let endX = 0;
        
        this.modalTouchStart = (e) => {
            startX = e.touches[0].clientX;
        };
        
        this.modalTouchEnd = (e) => {
            endX = e.changedTouches[0].clientX;
            this.handleSwipe(startX, endX);
        };
        
        modalBody.addEventListener('touchstart', this.modalTouchStart, { passive: true });
        modalBody.addEventListener('touchend', this.modalTouchEnd, { passive: true });
        
        // Clean up on modal hide
        modal.addEventListener('hidden.bs.modal', () => {
            this.removeModalNavigation();
        }, { once: true });
    }

    removeModalNavigation() {
        if (this.modalKeyHandler) {
            document.removeEventListener('keydown', this.modalKeyHandler);
        }
        
        const modal = document.getElementById('coinDetailModal');
        const modalBody = modal.querySelector('.modal-body');
        
        if (this.modalTouchStart) {
            modalBody.removeEventListener('touchstart', this.modalTouchStart);
        }
        if (this.modalTouchEnd) {
            modalBody.removeEventListener('touchend', this.modalTouchEnd);
        }
    }

    handleSwipe(startX, endX) {
        const swipeThreshold = 50; // Minimum distance for a swipe
        const difference = startX - endX;
        
        if (Math.abs(difference) > swipeThreshold) {
            if (difference > 0) {
                // Swipe left - next coin
                this.navigateToNextCoin();
            } else {
                // Swipe right - previous coin
                this.navigateToPreviousCoin();
            }
        }
    }

    async navigateToNextCoin() {
        if (this.currentCoinIndex < this.filteredCoins.length - 1) {
            this.currentCoinIndex++;
            await this.updateModalCoin();
        }
    }

    async navigateToPreviousCoin() {
        if (this.currentCoinIndex > 0) {
            this.currentCoinIndex--;
            await this.updateModalCoin();
        }
    }

    async updateModalCoin() {
        const coin = this.filteredCoins[this.currentCoinIndex];
        if (coin) {
            try {
                // Add slide animation
                const modalBody = document.querySelector('#coinDetailModal .modal-body');
                modalBody.style.opacity = '0.5';
                modalBody.style.transform = 'translateX(10px)';
                
                // Fetch detailed coin info
                const detailedCoin = await this.fetchCoinDetails(coin.coin_id);
                
                // Update modal content
                this.populateCoinModal(detailedCoin || coin);
                
                // Animate back
                setTimeout(() => {
                    modalBody.style.opacity = '1';
                    modalBody.style.transform = 'translateX(0)';
                }, 50);
                
            } catch (error) {
                console.error('Error updating modal coin:', error);
                this.populateCoinModal(coin);
            }
        }
    }

    shareCoin(coinId) {
        const coin = this.coins.find(c => c.coin_id === coinId);
        if (coin) {
            const shareText = `Check out this ${coin.country} €${parseFloat(coin.value).toFixed(2)} coin from ${coin.year}!`;
            const shareUrl = `${window.location.origin}/catalog?search=${encodeURIComponent(coin.coin_id)}`;
            
            if (navigator.share) {
                navigator.share({
                    title: `${coin.country} €${parseFloat(coin.value).toFixed(2)} Coin`,
                    text: shareText,
                    url: shareUrl
                });
            } else {
                // Fallback: copy to clipboard
                navigator.clipboard.writeText(`${shareText} ${shareUrl}`).then(() => {
                    // Show toast notification
                    this.showToast('Link copied to clipboard!');
                }).catch(() => {
                    // Fallback if clipboard API is not available
                    this.showToast('Unable to copy link');
                });
            }
        }
    }

    showToast(message) {
        // Simple toast implementation
        const toast = document.createElement('div');
        toast.className = 'toast-notification';
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
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
