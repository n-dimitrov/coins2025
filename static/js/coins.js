class CoinCatalog {
    constructor(groupContext = null) {
        this.groupContext = groupContext;
        this.coins = [];
        this.filteredCoins = [];
        this.currentFilters = {
            coin_type: '',
            value: '',
            country: '',
            commemorative: '',
            search: '',
            // Group-specific filters
            ownership_status: '',
            owned_by: ''
        };
        this.currentPage = 1;
        this.coinsPerPage = 20;
        this.loading = false;
        this.currentCoinIndex = 0;
        
        // Initialize the series label generator
        this.seriesLabelGenerator = new SeriesLabelGenerator();
        
        // Cache for generated labels to avoid recalculation
        this.labelCache = new Map();
        
        this.init();
    }

    // Helper method to construct API URLs with proper protocol
    getApiUrl(path) {
        // Ensure we use the same protocol as the current page
        const protocol = window.location.protocol;
        const host = window.location.host;
        
        // If running locally, use relative URLs
        if (host.includes('localhost') || host.includes('127.0.0.1')) {
            return path;
        }
        
        // For production, ensure HTTPS is used
        if (protocol === 'http:' && host.includes('myeurocoins.org')) {
            // Force HTTPS for production
            return `https://${host}${path}`;
        }
        
        // Use relative URL for same-origin requests
        return path;
    }

    /**
     * Generate a label for a series code using the auto-generation system
     * @param {string} seriesCode - The series code to generate label for
     * @param {Object} coinData - Optional coin data for additional context
     * @returns {string} Generated label
     */
    getSeriesLabel(seriesCode, coinData = null) {
        // Check cache first
        const cacheKey = `${seriesCode}${coinData ? `_${coinData.year}` : ''}`;
        if (this.labelCache.has(cacheKey)) {
            return this.labelCache.get(cacheKey);
        }

        // Generate label using the enhanced generator with full context
        const label = this.seriesLabelGenerator.generateLabel(seriesCode, coinData, this.coins);
        
        // Cache the result
        this.labelCache.set(cacheKey, label);
        
        return label;
    }

    /**
     * Generate labels for regular series with intelligent multi-series analysis
     * This method provides the most accurate labels by analyzing all related series
     * @param {string} seriesCode - Regular series code
     * @returns {string} Generated label with proper year range
     */
    getRegularSeriesLabelWithRange(seriesCode) {
        // Check cache first
        const cacheKey = `${seriesCode}_range_context`;
        if (this.labelCache.has(cacheKey)) {
            return this.labelCache.get(cacheKey);
        }

        // Use the enhanced context-aware generation
        const label = this.seriesLabelGenerator.generateRegular(seriesCode, null, this.coins);
        
        // Cache the result
        this.labelCache.set(cacheKey, label);
        
        return label;
    }

    /**
     * Batch generate labels for commemorative filter dropdown
     * @param {Array} commemoratives - Array of commemorative series codes
     * @returns {Object} Mapping of series codes to labels
     */
    generateCommemorativeLabels(commemoratives) {
        const labels = {};
        commemoratives.forEach(seriesCode => {
            labels[seriesCode] = this.getSeriesLabel(seriesCode);
        });
        return labels;
    }

    /**
     * Generate all series labels with full context (used for batch operations)
     * @param {Array} seriesList - Array of all series codes
     * @returns {Object} Mapping of series codes to labels
     */
    generateAllSeriesLabels(seriesList) {
        return this.seriesLabelGenerator.generateBatchLabelsWithContext(seriesList, this.coins);
    }

    /**
     * Clear the label cache (useful when coin data changes)
     */
    clearLabelCache() {
        this.labelCache.clear();
        this.seriesLabelGenerator.clearCache();
    }

    async init() {
        console.log('Group context in init:', this.groupContext);
        try {
            await this.loadFilterOptions();
            this.populateGroupMemberFilter(); // Populate group member filter if in group context
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
            
            // Use group API if in group mode
            const apiPath = this.groupContext 
                ? `/api/coins/group/${this.groupContext.group_key}?${params}`
                : `/api/coins/?${params}`;
            
            const apiUrl = this.getApiUrl(apiPath);
            
            const response = await fetch(apiUrl);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            this.coins = data.coins || [];
            this.applyFilters();
        } catch (error) {
            console.error('Error loading coins:', error);
            console.error('Current location:', window.location.href); // Additional debug info
            this.showError('Failed to load coins: ' + error.message);
            this.coins = [];
            this.filteredCoins = [];
        } finally {
            this.setLoading(false);
        }
    }

    async loadFilterOptions() {
        try {
            const apiUrl = this.getApiUrl('/api/coins/filters');
            
            const response = await fetch(apiUrl);
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
        if (!select) {
            console.error('Commemorative filter select element not found!');
            return;
        }
        
        // Clear existing options except the first one
        select.innerHTML = '<option value="">All Commemoratives</option>';
        
        if (!commemoratives || commemoratives.length === 0) {
            console.warn('No commemoratives data provided');
            return;
        }
        
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
            // Use the auto-generated label
            const label = this.getSeriesLabel(commemorative);
            option.textContent = label;
            select.appendChild(option);
        });
    }

    populateGroupMemberFilter() {
        const select = document.getElementById('owned-by-filter');
        if (!select || !this.groupContext || !this.groupContext.members) return;
        
        // Clear existing options except the first one
        select.innerHTML = '<option value="">All Members</option>';
        
        this.groupContext.members.forEach(member => {
            const option = document.createElement('option');
            // Template uses member.user; fall back to member.name or string member
            const memberLabel = member.user || member.name || (typeof member === 'string' ? member : '');
            option.value = memberLabel;
            option.textContent = memberLabel;
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
            
            // Group-specific filters (only apply if in group context)
            if (this.groupContext) {
                // Ownership status filter
                if (this.currentFilters.ownership_status) {
                    const hasOwners = coin.owners && coin.owners.length > 0;
                    if (this.currentFilters.ownership_status === 'owned' && !hasOwners) {
                        return false;
                    }
                    if (this.currentFilters.ownership_status === 'missing' && hasOwners) {
                        return false;
                    }
                }
                
                // Owned by specific member filter
                if (this.currentFilters.owned_by) {
                    const isOwnedByMember = coin.owners && coin.owners.some(owner => 
                        owner.owner === this.currentFilters.owned_by
                    );
                    if (!isOwnedByMember) {
                        return false;
                    }
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
    // Use semantic classes so we can style CC/RE independently of Bootstrap utility colors
    const typeClass = coin.coin_type === 'RE' ? 'coin-type-re' : 'coin-type-cc';
    const typeName = coin.coin_type === 'RE' ? 'Regular' : 'Commemorative';
        const imageUrl = coin.image_url || '/static/images/coin-placeholder.png';
        
        // Format value to always show 2 decimal places
        const formattedValue = parseFloat(coin.value).toFixed(2);

        // Generate ownership badge for upper right corner if in group mode
        let ownershipBadgeHtml = '';
        
        if (this.groupContext && coin.owners !== undefined) {
            const ownersCount = coin.owners ? coin.owners.length : 0;
            const totalMembers = this.groupContext.members ? this.groupContext.members.length : 0;
            
            if (ownersCount > 0) {
                if (ownersCount === totalMembers) {
                    // Everyone owns it - show star badge with custom circular 3D styling
                    ownershipBadgeHtml = `
                        <span class="position-absolute top-0 end-0 ownership-badge ownership-full" title="Owned by everyone (${ownersCount}/${totalMembers})">
                            ⭐
                        </span>
                    `;
                } else {
                    // Show number of owners with custom circular 3D styling
                    ownershipBadgeHtml = `
                        <span class="position-absolute top-0 end-0 ownership-badge ownership-partial" title="Owned by ${ownersCount}/${totalMembers} members">
                            ${ownersCount}
                        </span>
                    `;
                }
            }
            // No badge for 0 owners (case 1)
        }

        // Ownership info moved to coin details modal - no longer displayed in card body
        let ownershipHtml = '';

        return `
            <div class="col-md-6 col-lg-4 col-xl-3 mb-4">
                <div class="card coin-card h-100 ${this.groupContext ? 'group-mode' : ''}">
                    <div class="position-relative">
                        <div class="coin-image-wrapper">
                            <img 
                                src="${imageUrl}" 
                                class="card-img-top coin-image" 
                                alt="${coin.country} ${coin.value} Euro"
                                loading="lazy"
                                onerror="this.src='/static/images/coin-placeholder.png'"
                            >
                        </div>
                        <span class="badge ${typeClass} position-absolute top-0 start-0">
                            ${coin.coin_type}
                        </span>
                        ${ownershipBadgeHtml}
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
                        ${ownershipHtml}
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
        // Prefer global implementation from /static/js/flags.js
        if (typeof window !== 'undefined' && typeof window.getCountryFlag === 'function') {
            return window.getCountryFlag(country);
        }
        // Fallback inline mapping
        const fallback = {
            'Germany': '🇩🇪', 'France': '🇫🇷', 'Italy': '🇮🇹', 'Spain': '🇪🇸',
            'Finland': '🇫🇮', 'Croatia': '🇭🇷', 'Luxembourg': '🇱🇺', 'Belgium': '🇧🇪',
            'Austria': '🇦🇹', 'Netherlands': '🇳🇱', 'Portugal': '🇵🇹', 'Greece': '🇬🇷',
            'Ireland': '🇮🇪', 'Slovenia': '🇸🇮', 'Slovakia': '🇸🇰', 'Estonia': '🇪🇪',
            'Latvia': '🇱🇻', 'Lithuania': '🇱🇹', 'Malta': '🇲🇹', 'Cyprus': '🇨🇾',
            'Monaco': '🇲🇨', 'Vatican City': '🇻🇦', 'San Marino': '🇸🇲', 'Andorra': '🇦🇩'
        };
        return fallback[country] || '🇪🇺';
    }

    setupEventListeners() {
        // Search functionality
        // Template uses id="search-input" (kebab-case)
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.currentFilters.search = e.target.value;
                this.applyFilters();
            });
        }

        // Filter dropdowns
        const typeFilter = document.getElementById('type-filter');
        if (typeFilter) {
            typeFilter.addEventListener('change', (e) => {
                this.currentFilters.coin_type = e.target.value;
                this.applyFilters();
            });
        }

        const valueFilter = document.getElementById('value-filter');
        if (valueFilter) {
            valueFilter.addEventListener('change', (e) => {
                this.currentFilters.value = e.target.value;
                this.applyFilters();
            });
        }

        const countryFilter = document.getElementById('country-filter');
        if (countryFilter) {
            countryFilter.addEventListener('change', (e) => {
                this.currentFilters.country = e.target.value;
                this.applyFilters();
            });
        }

        const commemorativeFilter = document.getElementById('commemorative-filter');
        if (commemorativeFilter) {
            commemorativeFilter.addEventListener('change', (e) => {
                this.currentFilters.commemorative = e.target.value;
                this.applyFilters();
            });
        }

        // Group-specific filters (if available)
        const ownershipFilter = document.getElementById('ownership-filter');
        if (ownershipFilter) {
            ownershipFilter.addEventListener('change', (e) => {
                this.currentFilters.ownership_status = e.target.value;
                this.applyFilters();
            });
        }

        const ownedByFilter = document.getElementById('owned-by-filter');
        if (ownedByFilter) {
            ownedByFilter.addEventListener('change', (e) => {
                this.currentFilters.owned_by = e.target.value;
                this.applyFilters();
            });
        }

        // Clear filters button
        const clearFiltersBtn = document.getElementById('clear-filters');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => {
                this.clearAllFilters();
            });
        }

        // Coin card clicks (for coin detail modal)
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('coin-card-clickable') || 
                e.target.closest('.coin-card-clickable')) {
                
                const coinElement = e.target.classList.contains('coin-card-clickable') 
                    ? e.target 
                    : e.target.closest('.coin-card-clickable');
                
                const coinId = coinElement.dataset.coinId;
                const coin = this.coins.find(c => c.coin_id === coinId);
                if (coin) {
                    this.showCoinDetailModal(coin);
                }
            }
        });

        // Ownership badge clicks (for owner info modal)
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('ownership-badge')) {
                e.stopPropagation(); // Prevent coin modal from opening
                const coinCard = e.target.closest('.coin-card');
                const coinId = coinCard.querySelector('[data-coin-id]').dataset.coinId;
                const coin = this.coins.find(c => c.coin_id === coinId);
                if (coin && coin.owners && coin.owners.length > 0) {
                    this.showOwnerInfo(coin, e.target);
                }
            }
        });

        // Close owner info modal when clicking outside
        document.addEventListener('click', (e) => {
            const modal = document.getElementById('ownerInfoModal');
            // showOwnerInfo() sets display to 'flex', hideOwnerInfo() sets to 'none'
            if (modal && modal.style.display && modal.style.display !== 'none' && 
                !e.target.closest('.owner-info-content') && 
                !e.target.classList.contains('ownership-badge')) {
                this.hideOwnerInfo();
            }
        });

        // Close owner info modal with ESC key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const modal = document.getElementById('ownerInfoModal');
                if (modal && modal.style.display && modal.style.display !== 'none') {
                    this.hideOwnerInfo();
                }
            }
        });

        // Install a single persistent handler to remove card-pop when the
        // coin detail modal is hidden. This avoids adding a new listener
        // every time the modal is shown which would leak memory.
        if (!this._coinModalHideHandlerInstalled) {
            const coinModalEl = document.getElementById('coinDetailModal');
            if (coinModalEl) {
                // Use a bound instance method so `this` is always correct and
                // so the handler reference can be removed later if needed.
                this._boundClearAllCardPop = this.clearAllCardPop.bind(this);
                coinModalEl.addEventListener('hidden.bs.modal', this._boundClearAllCardPop);
                this._coinModalHideHandlerInstalled = true;
            }
        }
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
            
            // Only fetch additional coin details if we're NOT in group context
            // Group coins already have complete data including ownership
            let coinToDisplay = coin;
            if (!this.groupContext) {
                const detailedCoin = await this.fetchCoinDetails(coin.coin_id);
                coinToDisplay = detailedCoin || coin;
            }
            
            // Populate modal content
            this.populateCoinModal(coinToDisplay);

            // Add a pop class to the corresponding card for a stronger 3D effect
            this.clearAllCardPop();
            const cardEl = document.querySelector(`[data-coin-id="${coin.coin_id}"]`)?.closest('.coin-card');
            if (cardEl) cardEl.classList.add('card-pop');

            // Show modal
            const modalEl = document.getElementById('coinDetailModal');
            const modal = new bootstrap.Modal(modalEl);
            modal.show();

            // The modal hide handler for removing the card-pop class is
            // installed once in setupEventListeners to avoid adding
            // a new listener on every show (prevents memory leaks).

            // Set up navigation handlers
            this.setupModalNavigation();
        } catch (error) {
            console.error('Error showing coin details:', error);
            // Fallback to basic coin data
            this.currentCoinIndex = this.filteredCoins.findIndex(c => c.coin_id === coin.coin_id);
            this.populateCoinModal(coin);
            const modalEl = document.getElementById('coinDetailModal');
            const modal = new bootstrap.Modal(modalEl);
            // Attempt to add pop class to the fallback coin card
            this.clearAllCardPop();
            const fallbackCard = document.querySelector(`[data-coin-id="${coin.coin_id}"]`)?.closest('.coin-card');
            if (fallbackCard) fallbackCard.classList.add('card-pop');
            modal.show();
            // The modal hide handler is installed centrally; no per-show
            // handler is needed here.
            this.setupModalNavigation();
        }
    }

    async fetchCoinDetails(coinId) {
        try {
            const response = await fetch(this.getApiUrl(`/api/coins/${coinId}`));
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
        // Use the same semantic classes as the coin cards so styling can be shared
        const typeClass = coin.coin_type === 'RE' ? 'coin-type-re' : 'coin-type-cc';
        const typeName = coin.coin_type === 'RE' ? 'Regular' : 'Commemorative';
        
        // Use auto-generated series label
        const commemorativeLabel = this.getSeriesLabel(coin.series, coin);
        
        // Create image gallery - for now use single image, can be enhanced later
        const mainImage = coin.image_url || '/static/images/coin-placeholder.png';
        
        // Generate ownership info for modal
        let ownershipModalHtml = '';
        if (this.groupContext && coin.owners !== undefined) {
            if (coin.owners.length > 0) {
                // Sort owners by date (oldest first)
                const sortedOwners = [...coin.owners].sort((a, b) => {
                    const dateA = new Date(a.acquired_date || '1970-01-01');
                    const dateB = new Date(b.acquired_date || '1970-01-01');
                    return dateA - dateB;
                });

                const ownerBadges = sortedOwners.map(owner => 
                    `<span class="badge bg-success me-1 mb-1" title="Owned by ${owner.owner}${owner.acquired_date ? ' (acquired: ' + new Date(owner.acquired_date).toLocaleDateString() + ')' : ''}">${owner.owner}</span>`
                ).join('');
                
                ownershipModalHtml = `
                    <div class="ownership-modal-section">
                        <div class="ownership-modal-header">
                            <i class="fas fa-users me-2"></i>Owned by:
                        </div>
                        <div class="ownership-modal-badges">
                            ${ownerBadges}
                        </div>
                    </div>
                `;
            } else {
                ownershipModalHtml = `
                    <div class="ownership-modal-section">
                        <div class="ownership-modal-header">
                            <i class="fas fa-users me-2"></i>Collection Status:
                        </div>
                        <div class="ownership-modal-badges">
                            <span class="badge bg-outline-secondary">Not owned by group</span>
                        </div>
                    </div>
                `;
            }
        }
        
        const modalContent = `
            <div class="coin-detail-container">
                <div class="coin-header">
                    <div class="d-flex justify-content-between align-items-center">
                        <div class="d-flex align-items-center flex-grow-1 me-2">
                            <span class="country-flag modal-coin-flag">${flag}</span>
                            <span class="ms-2 coin-country modal-coin-country text-truncate" title="${coin.country}">${coin.country}</span>
                        </div>
                        <div class="ms-2">
                            <div class="modal-coin-value">€${formattedValue}</div>
                        </div>
                    </div>

                    <div class="d-flex justify-content-between align-items-center mt-2">
                        <div class="coin-type-year text-muted">
                            ${typeName} &bull; ${coin.year}
                        </div>
                    </div>
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
                        ${ownershipModalHtml}
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
                // Update card pop highlighting: remove previous, add to new
                this.clearAllCardPop();
                const newCard = document.querySelector(`[data-coin-id="${coin.coin_id}"]`)?.closest('.coin-card');
                if (newCard) newCard.classList.add('card-pop');
                // Only fetch additional coin details if we're NOT in group context
                // Group coins already have complete data including ownership
                let coinToDisplay = coin;
                if (!this.groupContext) {
                    const detailedCoin = await this.fetchCoinDetails(coin.coin_id);
                    coinToDisplay = detailedCoin || coin;
                }
                
                // Update modal content
                this.populateCoinModal(coinToDisplay);
                
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

    clearAllCardPop() {
        document.querySelectorAll('.coin-card.card-pop').forEach(el => el.classList.remove('card-pop'));
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

    showOwnerInfo(coin, badgeElement) {
        const modal = document.getElementById('ownerInfoModal');
        const body = document.getElementById('ownerInfoBody');
        
        if (!modal || !body || !coin.owners || coin.owners.length === 0) {
            return;
        }

        // Sort owners by date (oldest first)
        const sortedOwners = [...coin.owners].sort((a, b) => {
            const dateA = new Date(a.acquired_date || '1970-01-01');
            const dateB = new Date(b.acquired_date || '1970-01-01');
            return dateA - dateB;
        });

        // Generate owner list HTML
        const ownersHtml = sortedOwners.map(owner => {
            const formattedDate = this.formatAcquisitionDate(owner.acquired_date);
            return `
                <div class="owner-item">
                    <div class="owner-name">${owner.owner}</div>
                    <div class="owner-date">${formattedDate}</div>
                </div>
            `;
        }).join('');

        body.innerHTML = ownersHtml;

        // Position modal (now centers on screen for better UX)
        this.positionOwnerModal(modal, badgeElement);

        // Show modal with proper display
        modal.style.display = 'flex';
    }

    hideOwnerInfo() {
        const modal = document.getElementById('ownerInfoModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    clearAllFilters() {
        // Reset all filter values
        this.currentFilters = {
            coin_type: '',
            value: '',
            country: '',
            commemorative: '',
            search: '',
            ownership_status: '',
            owned_by: ''
        };
        
        // Reset all form elements
    const searchInput = document.getElementById('search-input');
        if (searchInput) searchInput.value = '';
        
        const typeFilter = document.getElementById('type-filter');
        if (typeFilter) typeFilter.value = '';
        
        const valueFilter = document.getElementById('value-filter');
        if (valueFilter) valueFilter.value = '';
        
        const countryFilter = document.getElementById('country-filter');
        if (countryFilter) countryFilter.value = '';
        
        const commemorativeFilter = document.getElementById('commemorative-filter');
        if (commemorativeFilter) commemorativeFilter.value = '';
        
        const ownershipFilter = document.getElementById('ownership-filter');
        if (ownershipFilter) ownershipFilter.value = '';
        
        const ownedByFilter = document.getElementById('owned-by-filter');
        if (ownedByFilter) ownedByFilter.value = '';
        
        // Reapply filters (which will now show all coins)
        this.applyFilters();
    }

    formatAcquisitionDate(dateString) {
        if (!dateString) {
            return 'Unknown date';
        }

        try {
            const date = new Date(dateString);
            const options = { 
                day: 'numeric', 
                month: 'long', 
                year: 'numeric' 
            };
            return date.toLocaleDateString('en-GB', options);
        } catch (error) {
            return 'Invalid date';
        }
    }

    positionOwnerModal(modal, badgeElement) {
        // For better UX, center the modal on screen instead of positioning relative to badge
        // This provides more space and better readability
        
        // Reset any previous positioning
        const modalContent = modal.querySelector('.owner-info-content');
        modalContent.style.position = 'relative';
        modalContent.style.top = 'auto';
        modalContent.style.left = 'auto';
        modalContent.style.margin = 'auto';
        
        // Set modal to full screen centered
        modal.style.position = 'fixed';
        modal.style.top = '0';
        modal.style.left = '0';
        modal.style.width = '100%';
        modal.style.height = '100%';
        modal.style.alignItems = 'center';
        modal.style.justifyContent = 'center';
        modal.style.display = 'flex';
    }
}
