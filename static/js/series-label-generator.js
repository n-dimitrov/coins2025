/**
 * Auto-generation utility for series labels
 * Replaces static mapping with dynamic generation based on series codes and coin data
 * Enhanced version with multi-series support and intelligent range detection
 */

class SeriesLabelGenerator {
    constructor() {
        // Country code to country name mapping
        this.countryCodeMap = {
            'AND': 'Andorra',
            'AUT': 'Austria', 
            'BEL': 'Belgium',
            'CYP': 'Cyprus',
            'DEU': 'Germany',
            'ESP': 'Spain',
            'EST': 'Estonia',
            'FIN': 'Finland',
            'FRA': 'France',
            'GRC': 'Greece',
            'HRV': 'Croatia',
            'IRL': 'Ireland',
            'ITA': 'Italy',
            'LTU': 'Lithuania',
            'LUX': 'Luxembourg',
            'LVA': 'Latvia',
            'MCO': 'Monaco',
            'MLT': 'Malta',
            'NLD': 'Netherlands',
            'PRT': 'Portugal',
            'SMR': 'San Marino',
            'SVK': 'Slovakia',
            'SVN': 'Slovenia',
            'VAT': 'Vatican City'
        };

        // Special commemorative suffixes with their descriptions
        this.commemorativeSuffixes = {
            'TOR': 'Treaty of Rome',
            'EMU': 'Economic and Monetary Union',
            'TYE': 'Ten Years of Euro',
            'EUF': 'European Flag',
            'ERA': 'Erasmus Programme'
        };

        // Static mapping of series codes to their actual production year ranges
        // Based on official ECB data and coin production history
        this.seriesYearRanges = {
            // Germany - Single series, still active
            'DEU-01': { start: 1999, end: 'now', active: true },
            
            // France - Two series with transition
            'FRA-01': { start: 1999, end: 2021, active: false },
            'FRA-02': { start: 2022, end: 'now', active: true },
            
            // Italy - Single series, still active  
            'ITA-01': { start: 1999, end: 'now', active: true },
            
            // Spain - Multiple series
            'ESP-01': { start: 1999, end: 2013, active: false },
            'ESP-02': { start: 2014, end: 2014, active: false },
            'ESP-03': { start: 2015, end: 'now', active: true },
            
            // Netherlands - Two series
            'NLD-01': { start: 1999, end: 2013, active: false },
            'NLD-02': { start: 2014, end: 'now', active: true },
            
            // Belgium - Three series
            'BEL-01': { start: 1999, end: 2007, active: false },
            'BEL-02': { start: 2008, end: 2013, active: false },
            'BEL-03': { start: 2014, end: 'now', active: true },
            
            // Finland - Two series
            'FIN-01': { start: 1999, end: 2006, active: false },
            'FIN-02': { start: 2007, end: 'now', active: true },
            
            // Monaco - Two series  
            'MCO-01': { start: 2001, end: 2005, active: false },
            'MCO-02': { start: 2006, end: 'now', active: true },
            
            // San Marino - Two series
            'SMR-01': { start: 2006, end: 2016, active: false },
            'SMR-02': { start: 2017, end: 'now', active: true },
            
            // Vatican City - Multiple series (frequent design changes)
            'VAT-01': { start: 2002, end: 2004, active: false },
            'VAT-02': { start: 2005, end: 2005, active: false },
            'VAT-03': { start: 2006, end: 2013, active: false },
            'VAT-04': { start: 2014, end: 2016, active: false },
            'VAT-05': { start: 2017, end: 'now', active: true },
            
            // Single series countries (joined at different times)
            'AUT-01': { start: 2002, end: 'now', active: true },
            'GRC-01': { start: 2002, end: 'now', active: true },
            'IRL-01': { start: 2002, end: 'now', active: true },
            'LUX-01': { start: 2002, end: 'now', active: true },
            'PRT-01': { start: 2002, end: 'now', active: true },
            'SVN-01': { start: 2007, end: 'now', active: true },
            'CYP-01': { start: 2008, end: 'now', active: true },
            'MLT-01': { start: 2008, end: 'now', active: true },
            'SVK-01': { start: 2009, end: 'now', active: true },
            'EST-01': { start: 2011, end: 'now', active: true },
            'LVA-01': { start: 2014, end: 'now', active: true },
            'LTU-01': { start: 2015, end: 'now', active: true },
            'AND-01': { start: 2014, end: 'now', active: true },
            'HRV-01': { start: 2023, end: 'now', active: true }
        };

        // Cache for country series analysis
        this.countrySeriesCache = new Map();
        
        // Current year for "now" calculation
        this.currentYear = new Date().getFullYear();
    }

    /**
     * Generate a human-readable label for any series code
     * @param {string} seriesCode - The series code (e.g., "AND-01", "CC-2007-TOR")
     * @param {Object} coinData - Optional coin data for context (year, country)
     * @param {Array} allCoins - Optional array of all coins for multi-series analysis
     * @returns {string} Generated label
     */
    generateLabel(seriesCode, coinData = null, allCoins = null) {
        if (!seriesCode) return '';

        // Handle commemorative coins (CC-)
        if (seriesCode.startsWith('CC-')) {
            return this.generateCommemorative(seriesCode);
        }

        // Handle regular coins (country codes)
        return this.generateRegular(seriesCode, coinData, allCoins);
    }

    /**
     * Generate label for commemorative coins
     * @param {string} seriesCode - CC series code
     * @returns {string} Generated label
     */
    generateCommemorative(seriesCode) {
        const parts = seriesCode.split('-');
        
        if (parts.length === 2) {
            // Simple format: CC-YYYY -> "YYYY"
            const year = parts[1];
            return year;
        } else if (parts.length === 3) {
            // Special format: CC-YYYY-SUFFIX -> "YYYY Description"
            const year = parts[1];
            const suffix = parts[2];
            const description = this.commemorativeSuffixes[suffix] || suffix;
            return `${year} ${description}`;
        }

        // Fallback
        return seriesCode;
    }

    /**
     * Generate label for regular coins with intelligent multi-series support
     * @param {string} seriesCode - Regular series code (e.g., "FRA-01")
     * @param {Object} coinData - Coin data with year information
     * @param {Array} allCoins - Array of all coins for multi-series analysis
     * @returns {string} Generated label
     */
    generateRegular(seriesCode, coinData = null, allCoins = null) {
        const parts = seriesCode.split('-');
        
        if (parts.length !== 2) {
            return seriesCode; // Fallback for invalid format
        }

        const countryCode = parts[0];
        const seriesNumber = parts[1];
        
        const countryName = this.countryCodeMap[countryCode] || countryCode;

        // If we have all coins data, use intelligent multi-series analysis
        if (allCoins && allCoins.length > 0) {
            return this.generateRegularWithMultiSeriesAnalysis(seriesCode, countryCode, countryName, allCoins);
        }

        // If we have coin data with year, use it for simple case
        if (coinData && coinData.year) {
            return `${countryName} ${coinData.year}`;
        }

        // Otherwise, use series number as fallback
        return `${countryName} (Series ${seriesNumber})`;
    }

    /**
     * Generate label with intelligent multi-series analysis
     * @param {string} seriesCode - The current series code
     * @param {string} countryCode - Country code (e.g., "FRA")
     * @param {string} countryName - Country name (e.g., "France")
     * @param {Array} allCoins - Array of all coins
     * @returns {string} Generated label with proper year range
     */
    generateRegularWithMultiSeriesAnalysis(seriesCode, countryCode, countryName, allCoins) {
        // Get or compute country series analysis
        const cacheKey = countryCode;
        if (!this.countrySeriesCache.has(cacheKey)) {
            const analysis = this.analyzeCountrySeries(countryCode, allCoins);
            this.countrySeriesCache.set(cacheKey, analysis);
        }

        const countryAnalysis = this.countrySeriesCache.get(cacheKey);
        const seriesInfo = countryAnalysis.series[seriesCode];

        if (!seriesInfo) {
            // Fallback if series not found in analysis
            return `${countryName} (${seriesCode})`;
        }

        // Generate label based on series info
        return this.formatSeriesLabel(countryName, seriesInfo, countryAnalysis);
    }

    /**
     * Analyze all series for a specific country
     * @param {string} countryCode - Country code to analyze
     * @param {Array} allCoins - Array of all coins
     * @returns {Object} Analysis results with series information
     */
    analyzeCountrySeries(countryCode, allCoins) {
        // Filter coins for this country's regular series
        const countryCoins = allCoins.filter(coin => 
            coin.series && 
            coin.series.startsWith(countryCode + '-') && 
            coin.coin_type === 'RE'
        );

        if (countryCoins.length === 0) {
            return { series: {}, seriesList: [] };
        }

        // Group coins by series
        const seriesGroups = {};
        countryCoins.forEach(coin => {
            const series = coin.series;
            if (!seriesGroups[series]) {
                seriesGroups[series] = [];
            }
            seriesGroups[series].push(coin);
        });

        // Analyze each series
        const seriesAnalysis = {};
        const seriesList = Object.keys(seriesGroups).sort(); // Sort series chronologically

        seriesList.forEach((seriesCode, index) => {
            const coins = seriesGroups[seriesCode];
            const years = coins.map(coin => coin.year).filter(year => year).sort((a, b) => a - b);
            
            if (years.length === 0) {
                seriesAnalysis[seriesCode] = {
                    startYear: null,
                    endYear: null,
                    isActive: false,
                    coinCount: coins.length
                };
                return;
            }

            const startYear = Math.min(...years);
            let endYear = Math.max(...years);
            let isActive = false;

            // Determine end year based on series position
            if (index === seriesList.length - 1) {
                // This is the latest series - it's active until now
                endYear = 'now';
                isActive = true;
            } else {
                // Not the latest series - find when next series started
                const nextSeries = seriesList[index + 1];
                if (nextSeries && seriesGroups[nextSeries]) {
                    const nextSeriesCoins = seriesGroups[nextSeries];
                    const nextSeriesYears = nextSeriesCoins.map(coin => coin.year).filter(year => year);
                    if (nextSeriesYears.length > 0) {
                        const nextSeriesStart = Math.min(...nextSeriesYears);
                        // This series ends when the next one starts
                        endYear = nextSeriesStart;
                    }
                }
                isActive = false;
            }

            seriesAnalysis[seriesCode] = {
                startYear,
                endYear,
                isActive,
                coinCount: coins.length,
                years: years
            };
        });

        return {
            series: seriesAnalysis,
            seriesList: seriesList
        };
    }

    /**
     * Format a series label based on series information
     * @param {string} countryName - Country name
     * @param {Object} seriesInfo - Series analysis information
     * @param {Object} countryAnalysis - Full country analysis for context
     * @returns {string} Formatted label
     */
    formatSeriesLabel(countryName, seriesInfo, countryAnalysis) {
        const { startYear, endYear } = seriesInfo;

        if (!startYear) {
            return `${countryName} (Unknown period)`;
        }

        // Check if country has multiple series
        const seriesCount = countryAnalysis.seriesList.length;
        
        if (seriesCount === 1) {
            // Single series: "Country year - now"
            return `${countryName} ${startYear} - now`;
        } else {
            // Multiple series: use actual end year or "now" for last series
            if (endYear === 'now') {
                return `${countryName} ${startYear} - now`;
            } else {
                return `${countryName} ${startYear} - ${endYear}`;
            }
        }
    }

    /**
     * Generate label with year range for regular series (legacy method, enhanced)
     * @param {string} seriesCode - Regular series code
     * @param {Array} coinsInSeries - Array of coins in this series
     * @returns {string} Generated label with year range
     */
    generateRegularWithRange(seriesCode, coinsInSeries) {
        const parts = seriesCode.split('-');
        
        if (parts.length !== 2) {
            return seriesCode;
        }

        const countryCode = parts[0];
        const countryName = this.countryCodeMap[countryCode] || countryCode;

        if (!coinsInSeries || coinsInSeries.length === 0) {
            return `${countryName} (Series ${parts[1]})`;
        }

        // Find min and max years
        const years = coinsInSeries.map(coin => coin.year).filter(year => year).sort((a, b) => a - b);
        
        if (years.length === 0) {
            return `${countryName} (Series ${parts[1]})`;
        }

        const minYear = years[0];
        const maxYear = years[years.length - 1];

        if (minYear === maxYear) {
            return `${countryName} ${minYear}`;
        }

        // Determine if series is still active (assume active if max year is recent)
        const yearsSinceLastCoin = this.currentYear - maxYear;
        const isActive = yearsSinceLastCoin <= 2;

        const endYear = isActive ? 'now' : maxYear;
        return `${countryName} (${minYear} - ${endYear})`;
    }

    /**
     * Batch generate labels for multiple series codes with full context
     * @param {Array} seriesList - Array of series codes
     * @param {Array} allCoins - Array of all coins for context
     * @returns {Object} Mapping of series codes to generated labels
     */
    generateBatchLabelsWithContext(seriesList, allCoins = []) {
        const labels = {};
        
        seriesList.forEach(seriesCode => {
            if (seriesCode.startsWith('CC-')) {
                labels[seriesCode] = this.generateCommemorative(seriesCode);
            } else {
                // For regular coins, use full context analysis
                labels[seriesCode] = this.generateRegular(seriesCode, null, allCoins);
            }
        });

        return labels;
    }

    /**
     * Batch generate labels for commemorative filter dropdown (legacy method)
     * @param {Array} seriesList - Array of series codes
     * @param {Object} coinsData - Optional mapping of series to coin arrays
     * @returns {Object} Mapping of series codes to generated labels
     */
    generateBatchLabels(seriesList, coinsData = {}) {
        const labels = {};
        
        seriesList.forEach(seriesCode => {
            const coinsInSeries = coinsData[seriesCode];
            
            if (seriesCode.startsWith('CC-')) {
                labels[seriesCode] = this.generateCommemorative(seriesCode);
            } else {
                // For regular coins, try to use year range if available
                if (coinsInSeries && coinsInSeries.length > 0) {
                    labels[seriesCode] = this.generateRegularWithRange(seriesCode, coinsInSeries);
                } else {
                    // Fallback to simple generation
                    const sampleCoin = coinsInSeries && coinsInSeries[0];
                    labels[seriesCode] = this.generateRegular(seriesCode, sampleCoin);
                }
            }
        });

        return labels;
    }

    /**
     * Clear the country series cache (useful when coin data changes)
     */
    clearCache() {
        this.countrySeriesCache.clear();
    }

    /**
     * Add or update a country code mapping
     * @param {string} code - 3-letter country code
     * @param {string} name - Country name
     */
    addCountryMapping(code, name) {
        this.countryCodeMap[code] = name;
        // Clear cache since country mapping changed
        this.clearCache();
    }

    /**
     * Add or update a commemorative suffix mapping
     * @param {string} suffix - Suffix code
     * @param {string} description - Human-readable description
     */
    addCommemorativeSuffix(suffix, description) {
        this.commemorativeSuffixes[suffix] = description;
    }
}

// Export for both browser and Node.js environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SeriesLabelGenerator;
} else if (typeof window !== 'undefined') {
    window.SeriesLabelGenerator = SeriesLabelGenerator;
}
