// Global Symbols Database Loader
// Loads 12,444+ instruments from PostgreSQL database via API
// Displays regional breakdowns with Spartan theme
// Spartan Research Station

class GlobalSymbolsDatabaseLoader {
    constructor() {
        this.apiEndpoint = window.location.origin + '/api/db';
        this.cache = new Map();
        this.allSymbols = [];

        this.init();
    }

    async init() {
        console.log('🌍 Initializing Global Symbols Database Loader...');

        try {
            await this.loadAllSymbols();
            await this.loadRegionalBreakdowns();
            this.setupSearch();

            console.log('✅ Global database loaded successfully');
        } catch (error) {
            console.error('❌ Database loading failed:', error);
            this.showError(error.message);
        }
    }

    async loadAllSymbols() {
        try {
            console.log('📡 Loading all symbols from PostgreSQL database...');

            // Load all symbols (no limit)
            const response = await fetch(`${this.apiEndpoint}/symbols?limit=15000`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Cache-Control': 'no-cache'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            this.allSymbols = data.symbols || data || [];

            console.log(`✅ Loaded ${this.allSymbols.length} symbols from database`);

            // Update total count
            this.updateDatabaseStats();

            return this.allSymbols;

        } catch (error) {
            console.error('❌ Error loading symbols:', error);
            throw error;
        }
    }

    updateDatabaseStats() {
        const totalElement = document.getElementById('total-instruments');
        if (totalElement && this.allSymbols.length > 0) {
            totalElement.textContent = this.allSymbols.length.toLocaleString();
        }

        // Update database timestamp
        const dbUpdateElement = document.getElementById('db-last-update');
        if (dbUpdateElement) {
            dbUpdateElement.innerHTML = `
                <span class="status-indicator valid"></span>
                Database loaded: ${this.allSymbols.length.toLocaleString()} instruments
                <br>Last updated: ${new Date().toLocaleTimeString()}
            `;
        }
    }

    async loadRegionalBreakdowns() {
        try {
            console.log('🗺️ Loading regional breakdowns...');

            // Separate symbols by region
            const regions = this.categorizeByRegion(this.allSymbols);

            // Update UK
            await this.displayRegionData('UK', regions.uk);

            // Update Europe
            await this.displayRegionData('Europe', regions.europe);

            // Update China/HK
            await this.displayRegionData('China', regions.china);

            console.log('✅ Regional breakdowns loaded');

        } catch (error) {
            console.error('❌ Error loading regional breakdowns:', error);
        }
    }

    categorizeByRegion(symbols) {
        const regions = {
            uk: [],
            europe: [],
            china: [],
            usa: [],
            other: []
        };

        for (const symbol of symbols) {
            const country = (symbol.country || '').toUpperCase();
            const exchange = (symbol.exchange || '').toUpperCase();
            const ticker = (symbol.symbol || '').toUpperCase();

            // UK stocks
            if (country === 'UK' || exchange === 'LSE' || ticker.endsWith('.L')) {
                regions.uk.push(symbol);
            }
            // European stocks
            else if (
                ['GERMANY', 'FRANCE', 'NETHERLANDS', 'SWITZERLAND', 'SPAIN', 'ITALY'].includes(country) ||
                ['XETRA', 'DAX', 'EURONEXT', 'SIX', 'BME', 'BIT'].includes(exchange) ||
                ticker.endsWith('.DE') || ticker.endsWith('.PA') || ticker.endsWith('.AS') ||
                ticker.endsWith('.SW') || ticker.endsWith('.MC') || ticker.endsWith('.MI')
            ) {
                regions.europe.push(symbol);
            }
            // China/HK stocks
            else if (
                ['CHINA', 'HONG KONG', 'HK'].includes(country) ||
                ['HKEX', 'SSE', 'SZSE'].includes(exchange) ||
                ticker.endsWith('.HK') || ticker.endsWith('.SS') || ticker.endsWith('.SZ')
            ) {
                regions.china.push(symbol);
            }
            // USA stocks
            else if (
                country === 'USA' || country === 'US' ||
                ['NASDAQ', 'NYSE', 'NYSE MKT', 'NYSE ARCA'].includes(exchange)
            ) {
                regions.usa.push(symbol);
            }
            else {
                regions.other.push(symbol);
            }
        }

        console.log('📊 Regional categorization:', {
            UK: regions.uk.length,
            Europe: regions.europe.length,
            China: regions.china.length,
            USA: regions.usa.length,
            Other: regions.other.length
        });

        return regions;
    }

    async displayRegionData(regionName, stocks) {
        const regionKey = regionName.toLowerCase();

        // Update count
        const countElement = document.getElementById(`${regionKey}-count`);
        if (countElement) {
            countElement.textContent = stocks.length.toLocaleString();
            countElement.className = 'flow-value neutral';
        }

        // Update validation message
        const validationElement = document.getElementById(`${regionKey}-validation`);
        if (validationElement) {
            validationElement.innerHTML = `
                <span class="status-indicator valid"></span>
                ${stocks.length} stocks loaded from database
                <br>Last updated: ${new Date().toLocaleTimeString()}
            `;
            validationElement.className = 'validation-message success';
        }

        // Display top stocks
        this.displayTopStocks(regionKey, stocks);
    }

    displayTopStocks(regionKey, stocks) {
        const containerElement = document.getElementById(`${regionKey}-top-stocks`);
        if (!containerElement) return;

        // Take first 15 stocks (already sorted by market cap in database)
        const topStocks = stocks.slice(0, 15);

        if (topStocks.length === 0) {
            containerElement.innerHTML = `
                <div style="text-align: center; color: var(--text-muted); padding: 40px;">
                    No stocks found for this region
                </div>
            `;
            return;
        }

        // Create stock list with Spartan styling
        const stockListHTML = topStocks.map((stock, index) => {
            const symbol = stock.symbol || 'N/A';
            const name = stock.name || 'Unknown';
            const exchange = stock.exchange || '';
            const sector = stock.sector || 'Various';

            return `
                <div style="
                    background: var(--bg-darker);
                    border-left: 3px solid var(--accent-color);
                    padding: 15px;
                    margin-bottom: 12px;
                    border-radius: 6px;
                    transition: all 0.3s ease;
                    cursor: pointer;
                "
                onmouseover="this.style.background='var(--bg-card)'; this.style.transform='translateX(5px)';"
                onmouseout="this.style.background='var(--bg-darker)'; this.style.transform='translateX(0)';">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="color: var(--accent-color); font-weight: 700; font-size: 1.1rem; margin-bottom: 5px;">
                                ${index + 1}. ${symbol}
                            </div>
                            <div style="color: var(--text-secondary); font-size: 0.95rem; margin-bottom: 3px;">
                                ${name}
                            </div>
                            <div style="color: var(--text-muted); font-size: 0.85rem;">
                                ${exchange} • ${sector}
                            </div>
                        </div>
                        <div style="
                            background: var(--accent-color);
                            color: var(--bg-darker);
                            padding: 5px 12px;
                            border-radius: 4px;
                            font-weight: 600;
                            font-size: 0.85rem;
                        ">
                            #${index + 1}
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        containerElement.innerHTML = stockListHTML;
    }

    setupSearch() {
        const searchInput = document.getElementById('global-symbol-search');
        const searchResults = document.getElementById('search-results');

        if (!searchInput || !searchResults) return;

        let searchTimeout;

        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);

            const query = e.target.value.trim();

            if (query.length < 2) {
                searchResults.innerHTML = `
                    <div style="text-align: center; color: var(--text-muted); padding: 40px;">
                        Type at least 2 characters to search
                    </div>
                `;
                return;
            }

            // Debounce search
            searchTimeout = setTimeout(() => {
                this.performSearch(query);
            }, 300);
        });
    }

    async performSearch(query) {
        const searchResults = document.getElementById('search-results');
        if (!searchResults) return;

        try {
            // Show loading
            searchResults.innerHTML = `
                <div style="text-align: center; color: var(--text-muted); padding: 40px;">
                    <span class="loading"></span> Searching ${this.allSymbols.length.toLocaleString()} symbols...
                </div>
            `;

            // Search via PostgreSQL API
            const response = await fetch(`${this.apiEndpoint}/search?query=${encodeURIComponent(query)}&limit=50`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Cache-Control': 'no-cache'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const results = await response.json();
            const symbols = results.symbols || results || [];

            this.displaySearchResults(symbols, query);

        } catch (error) {
            console.error('❌ Search failed:', error);
            searchResults.innerHTML = `
                <div style="text-align: center; color: var(--danger-color); padding: 40px;">
                    Search failed: ${error.message}
                    <br><small>Using local cache instead...</small>
                </div>
            `;

            // Fallback to local search
            this.performLocalSearch(query);
        }
    }

    performLocalSearch(query) {
        const searchResults = document.getElementById('search-results');
        if (!searchResults) return;

        const queryUpper = query.toUpperCase();

        const filtered = this.allSymbols.filter(stock => {
            const symbol = (stock.symbol || '').toUpperCase();
            const name = (stock.name || '').toUpperCase();

            return symbol.includes(queryUpper) || name.includes(queryUpper);
        }).slice(0, 50);

        this.displaySearchResults(filtered, query);
    }

    displaySearchResults(results, query) {
        const searchResults = document.getElementById('search-results');
        if (!searchResults) return;

        if (results.length === 0) {
            searchResults.innerHTML = `
                <div style="text-align: center; color: var(--text-muted); padding: 40px;">
                    No results found for "${query}"
                    <br><small>Try searching for: AAPL, MSFT, SHEL.L, SAP.DE, 0700.HK</small>
                </div>
            `;
            return;
        }

        const resultsHTML = results.map((stock, index) => {
            const symbol = stock.symbol || 'N/A';
            const name = stock.name || 'Unknown';
            const exchange = stock.exchange || '';
            const country = stock.country || '';
            const type = stock.type || 'Stock';

            // Highlight matching text
            const highlightSymbol = this.highlightMatch(symbol, query);
            const highlightName = this.highlightMatch(name, query);

            return `
                <div style="
                    background: var(--bg-darker);
                    border-left: 3px solid var(--info-color);
                    padding: 12px 15px;
                    margin-bottom: 8px;
                    border-radius: 6px;
                    transition: all 0.2s ease;
                    cursor: pointer;
                "
                onmouseover="this.style.background='var(--bg-card)'; this.style.borderLeftColor='var(--accent-color)';"
                onmouseout="this.style.background='var(--bg-darker)'; this.style.borderLeftColor='var(--info-color)';"
                onclick="window.open('/symbol_research.html?symbol=${encodeURIComponent(symbol)}', '_blank');">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div style="flex: 1;">
                            <div style="color: var(--accent-color); font-weight: 700; font-size: 1rem; margin-bottom: 4px;">
                                ${highlightSymbol}
                            </div>
                            <div style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 3px;">
                                ${highlightName}
                            </div>
                            <div style="color: var(--text-muted); font-size: 0.8rem;">
                                ${exchange} ${country ? '• ' + country : ''} • ${type}
                            </div>
                        </div>
                        <div style="
                            background: var(--info-color);
                            color: var(--bg-darker);
                            padding: 4px 10px;
                            border-radius: 4px;
                            font-weight: 600;
                            font-size: 0.75rem;
                            white-space: nowrap;
                        ">
                            VIEW →
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        searchResults.innerHTML = `
            <div style="color: var(--text-secondary); margin-bottom: 15px; font-size: 0.9rem;">
                Found ${results.length} result${results.length !== 1 ? 's' : ''} for "${query}"
            </div>
            ${resultsHTML}
        `;
    }

    highlightMatch(text, query) {
        if (!query || !text) return text;

        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<span style="background: var(--accent-color); color: var(--bg-darker); padding: 2px 4px; border-radius: 3px;">$1</span>');
    }

    showError(message) {
        const dbUpdateElement = document.getElementById('db-last-update');
        if (dbUpdateElement) {
            dbUpdateElement.innerHTML = `
                <span class="status-indicator invalid"></span>
                Error loading database: ${message}
                <br>Please ensure PostgreSQL server is running
            `;
        }
    }

    // Public methods
    async refresh() {
        await this.loadAllSymbols();
        await this.loadRegionalBreakdowns();
    }

    getSymbolCount() {
        return this.allSymbols.length;
    }

    getRegionalStats() {
        return this.categorizeByRegion(this.allSymbols);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing Global Symbols Database Loader...');

    try {
        // Create global instance
        window.globalSymbolsDatabase = new GlobalSymbolsDatabaseLoader();
        console.log('✅ Database loader initialized');

        // Add debug shortcuts
        window.debugDatabase = () => {
            console.log('🔍 Database Debug Info:');
            console.log('Total symbols:', window.globalSymbolsDatabase.getSymbolCount());
            console.log('Regional stats:', window.globalSymbolsDatabase.getRegionalStats());
        };

    } catch (error) {
        console.error('❌ Database loader initialization failed:', error);
    }

    // Setup Symbol Analysis Table Search
    setupSymbolAnalysisSearch();
});

// Symbol Analysis Table Search Functionality
function setupSymbolAnalysisSearch() {
    const searchInput = document.getElementById('analysis-symbol-search');
    const resultsTable = document.getElementById('analysis-results-table');

    if (!searchInput || !resultsTable) {
        console.log('Symbol analysis search elements not found');
        return;
    }

    let searchTimeout;

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();

        clearTimeout(searchTimeout);

        if (query.length < 1) {
            // Show default message
            resultsTable.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align: center; padding: 60px; color: var(--text-muted);">
                        <div style="font-size: 3rem; margin-bottom: 20px;">🔍</div>
                        <div style="font-size: 1.2rem; margin-bottom: 10px;">Start searching to view results</div>
                        <div style="font-size: 0.9rem;">Type a symbol or company name in the search box above</div>
                    </td>
                </tr>
            `;
            return;
        }

        // Show loading
        resultsTable.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 40px; color: var(--text-secondary);">
                    <span class="loading"></span> Searching...
                </td>
            </tr>
        `;

        // Debounce search
        searchTimeout = setTimeout(async () => {
            await performTableSearch(query, resultsTable);
        }, 300);
    });

    console.log('✅ Symbol Analysis table search initialized');
}

async function performTableSearch(query, resultsTable) {
    try {
        console.log(`🔍 Searching table for: ${query}`);

        // Try API search first
        const apiEndpoint = window.location.origin + '/api/db';
        const response = await fetch(
            `${apiEndpoint}/search?query=${encodeURIComponent(query)}&limit=100`,
            {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Cache-Control': 'no-cache'
                }
            }
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const results = await response.json();
        const symbols = results.symbols || results || [];

        displayTableResults(symbols, query, resultsTable);

    } catch (error) {
        console.error('❌ Table search failed:', error);

        // Fallback to local cache if available
        if (window.globalSymbolsDatabase && window.globalSymbolsDatabase.allSymbols) {
            const queryUpper = query.toUpperCase();
            const filtered = window.globalSymbolsDatabase.allSymbols.filter(stock => {
                const symbol = (stock.symbol || '').toUpperCase();
                const name = (stock.name || '').toUpperCase();
                return symbol.includes(queryUpper) || name.includes(queryUpper);
            }).slice(0, 100);

            displayTableResults(filtered, query, resultsTable);
        } else {
            resultsTable.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align: center; padding: 40px; color: var(--danger-color);">
                        Search failed: ${error.message}
                        <br><small>Please try again or check your connection</small>
                    </td>
                </tr>
            `;
        }
    }
}

function displayTableResults(results, query, resultsTable) {
    if (results.length === 0) {
        resultsTable.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 40px; color: var(--text-muted);">
                    <div style="font-size: 2rem; margin-bottom: 10px;">❌</div>
                    <div style="font-size: 1.1rem; margin-bottom: 5px;">No results found for "${query}"</div>
                    <div style="font-size: 0.9rem;">Try searching for: AAPL, MSFT, SHEL.L, SAP.DE, 0700.HK</div>
                </td>
            </tr>
        `;
        return;
    }

    const tableHTML = results.map((stock, index) => {
        const symbol = stock.symbol || 'N/A';
        const name = stock.name || 'Unknown';
        const exchange = stock.exchange || 'N/A';
        const country = stock.country || 'N/A';
        const type = stock.type || 'Stock';
        const sector = stock.sector || '-';

        // Highlight matching text
        const highlightSymbol = highlightMatch(symbol, query);
        const highlightName = highlightMatch(name, query);

        // Badge color based on type
        let badgeClass = 'badge-stock';
        if (type.toLowerCase().includes('crypto')) badgeClass = 'badge-crypto';
        else if (type.toLowerCase().includes('future')) badgeClass = 'badge-futures';
        else if (type.toLowerCase().includes('forex')) badgeClass = 'badge-forex';
        else if (type.toLowerCase().includes('etf')) badgeClass = 'badge-etf';

        return `
            <tr onclick="window.open('/symbol_research.html?symbol=${encodeURIComponent(symbol)}', '_blank');">
                <td style="color: var(--text-muted); font-weight: 600;">${index + 1}</td>
                <td style="font-weight: 700; color: var(--accent-color);">${highlightSymbol}</td>
                <td>${highlightName}</td>
                <td><span class="badge ${badgeClass}">${type}</span></td>
                <td style="color: var(--text-secondary);">${exchange}</td>
                <td style="color: var(--text-secondary);">${country}</td>
                <td style="color: var(--text-muted); font-size: 0.9rem;">${sector}</td>
            </tr>
        `;
    }).join('');

    resultsTable.innerHTML = tableHTML;

    console.log(`✅ Displayed ${results.length} results in table`);
}

function highlightMatch(text, query) {
    if (!query || !text) return text;

    const regex = new RegExp(`(${query})`, 'gi');
    return text.replace(regex, '<span class="highlight">$1</span>');
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GlobalSymbolsDatabaseLoader;
}
