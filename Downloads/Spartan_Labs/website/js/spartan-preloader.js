/**
 * SPARTAN RESEARCH STATION - UNIVERSAL DATA PRELOADER
 *
 * Loads ALL market data in the background when the main dashboard loads.
 * Stores data in browser IndexedDB for instant access across all pages.
 * Auto-refreshes data every 15 minutes.
 *
 * Benefits:
 * - All pages load INSTANTLY (data already cached)
 * - Reduced API calls (centralized fetching)
 * - Better user experience (no loading spinners)
 * - Offline capability (data persists in browser)
 */

class SpartanDataPreloader {
    constructor() {
        this.dbName = 'SpartanMarketData';
        this.dbVersion = 1;
        this.db = null;
        this.refreshInterval = 15 * 60 * 1000; // 15 minutes
        this.isPreloading = false;

        // API endpoints
        this.apiBase = 'http://localhost:8888';

        // Data categories to preload
        this.dataCategories = {
            indices: ['^GSPC', '^IXIC', '^DJI', '^RUT', '^VIX'],
            futures: ['ES=F', 'NQ=F', 'YM=F', 'RTY=F'],
            sectors: ['XLK', 'XLF', 'XLE', 'XLV', 'XLY', 'XLP', 'XLI', 'XLB', 'XLU', 'XLRE', 'XLC'],
            commodities: ['GC=F', 'CL=F', '^TNX'],
            currencies: ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'DX-Y.NYE'],
            volatility: ['^VIX', 'VXX', 'UVXY'],

            // FRED economic indicators
            fredSeries: [
                'UMCSENT',  // Consumer Confidence
                'MANEMP',   // Manufacturing Employment
                'SRVPRD',   // Services Index
                'USSLIND',  // Leading Economic Indicators
                'ICSA',     // Initial Claims
                'HOUST',    // Housing Starts
                'GDP',      // GDP
                'CPIAUCSL', // CPI
                'UNRATE',   // Unemployment Rate
                'FEDFUNDS'  // Fed Funds Rate
            ]
        };

        this.init();
    }

    async init() {
        console.log('🚀 Spartan Preloader initializing...');

        // Initialize IndexedDB
        await this.initDB();

        // Check if we have cached data
        const lastUpdate = await this.getLastUpdateTime();
        const now = Date.now();

        if (!lastUpdate || (now - lastUpdate) > this.refreshInterval) {
            // Data is stale or missing - preload now
            console.log('📊 Starting background data preload...');
            await this.preloadAllData();
        } else {
            console.log('✅ Using cached data (fresh within 15 min)');
        }

        // Set up auto-refresh
        this.startAutoRefresh();

        // Expose global access
        window.SpartanData = {
            get: (key) => this.getData(key),
            getYahoo: (symbol) => this.getYahooData(symbol),
            getFred: (seriesId) => this.getFredData(seriesId),
            refresh: () => this.preloadAllData(),
            isReady: () => this.isDataReady()
        };

        console.log('✅ Spartan Preloader ready!');
    }

    async initDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve();
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // Create object stores
                if (!db.objectStoreNames.contains('yahoo')) {
                    db.createObjectStore('yahoo', { keyPath: 'symbol' });
                }
                if (!db.objectStoreNames.contains('fred')) {
                    db.createObjectStore('fred', { keyPath: 'seriesId' });
                }
                if (!db.objectStoreNames.contains('metadata')) {
                    db.createObjectStore('metadata', { keyPath: 'key' });
                }
            };
        });
    }

    async preloadAllData() {
        if (this.isPreloading) {
            console.log('⏳ Preload already in progress...');
            return;
        }

        this.isPreloading = true;
        const startTime = Date.now();

        try {
            // Show loading indicator (optional)
            this.showLoadingIndicator();

            // Preload Yahoo Finance data (all symbols)
            await this.preloadYahooData();

            // Preload FRED economic data
            await this.preloadFredData();

            // Update last refresh time
            await this.setLastUpdateTime(Date.now());

            const duration = ((Date.now() - startTime) / 1000).toFixed(2);
            console.log(`✅ Preload complete in ${duration}s`);

            // Hide loading indicator
            this.hideLoadingIndicator();

            // Dispatch event for other scripts
            window.dispatchEvent(new CustomEvent('spartanDataReady'));

        } catch (error) {
            console.error('❌ Preload error:', error);
        } finally {
            this.isPreloading = false;
        }
    }

    async preloadYahooData() {
        // Combine all Yahoo symbols
        const allSymbols = [
            ...this.dataCategories.indices,
            ...this.dataCategories.futures,
            ...this.dataCategories.sectors,
            ...this.dataCategories.commodities,
            ...this.dataCategories.currencies,
            ...this.dataCategories.volatility
        ];

        console.log(`📈 Preloading ${allSymbols.length} Yahoo Finance symbols...`);

        // Fetch in batches to avoid overwhelming the API
        const batchSize = 10;
        for (let i = 0; i < allSymbols.length; i += batchSize) {
            const batch = allSymbols.slice(i, i + batchSize);
            const symbolsParam = batch.join(',');

            try {
                const response = await fetch(
                    `${this.apiBase}/api/yahoo/quote?symbols=${symbolsParam}`
                );
                const result = await response.json();

                if (result.data) {
                    // Store each symbol's data
                    for (const [symbol, data] of Object.entries(result.data)) {
                        await this.storeYahooData(symbol, data);
                    }
                }
            } catch (error) {
                console.error(`Error fetching batch ${i}-${i+batchSize}:`, error);
            }

            // Small delay between batches
            await this.sleep(100);
        }

        console.log('✅ Yahoo Finance data cached');
    }

    async preloadFredData() {
        console.log(`📊 Preloading ${this.dataCategories.fredSeries.length} FRED series...`);

        for (const seriesId of this.dataCategories.fredSeries) {
            try {
                const response = await fetch(
                    `${this.apiBase}/api/fred/series/observations?series_id=${seriesId}&limit=10&sort_order=desc`
                );
                const result = await response.json();

                if (result.observations) {
                    await this.storeFredData(seriesId, result.observations);
                }
            } catch (error) {
                console.error(`Error fetching FRED ${seriesId}:`, error);
            }

            // Small delay between requests
            await this.sleep(50);
        }

        console.log('✅ FRED economic data cached');
    }

    async storeYahooData(symbol, data) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['yahoo'], 'readwrite');
            const store = transaction.objectStore('yahoo');

            const record = {
                symbol: symbol,
                data: data,
                timestamp: Date.now()
            };

            const request = store.put(record);
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    async storeFredData(seriesId, observations) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['fred'], 'readwrite');
            const store = transaction.objectStore('fred');

            const record = {
                seriesId: seriesId,
                observations: observations,
                timestamp: Date.now()
            };

            const request = store.put(record);
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    async getYahooData(symbol) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['yahoo'], 'readonly');
            const store = transaction.objectStore('yahoo');
            const request = store.get(symbol);

            request.onsuccess = () => {
                if (request.result) {
                    resolve(request.result.data);
                } else {
                    resolve(null);
                }
            };
            request.onerror = () => reject(request.error);
        });
    }

    async getFredData(seriesId) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['fred'], 'readonly');
            const store = transaction.objectStore('fred');
            const request = store.get(seriesId);

            request.onsuccess = () => {
                if (request.result) {
                    resolve(request.result.observations);
                } else {
                    resolve(null);
                }
            };
            request.onerror = () => reject(request.error);
        });
    }

    async getData(key) {
        // Generic getter - try Yahoo first, then FRED
        let data = await this.getYahooData(key);
        if (!data) {
            data = await this.getFredData(key);
        }
        return data;
    }

    async setLastUpdateTime(timestamp) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['metadata'], 'readwrite');
            const store = transaction.objectStore('metadata');

            const record = { key: 'lastUpdate', value: timestamp };
            const request = store.put(record);

            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    async getLastUpdateTime() {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['metadata'], 'readonly');
            const store = transaction.objectStore('metadata');
            const request = store.get('lastUpdate');

            request.onsuccess = () => {
                resolve(request.result ? request.result.value : null);
            };
            request.onerror = () => reject(request.error);
        });
    }

    async isDataReady() {
        const lastUpdate = await this.getLastUpdateTime();
        return lastUpdate !== null;
    }

    startAutoRefresh() {
        // Refresh data every 15 minutes
        setInterval(() => {
            console.log('🔄 Auto-refreshing market data...');
            this.preloadAllData();
        }, this.refreshInterval);
    }

    showLoadingIndicator() {
        // Create floating indicator
        const indicator = document.createElement('div');
        indicator.id = 'spartan-preloader-indicator';
        indicator.innerHTML = `
            <div style="
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: linear-gradient(135deg, #8B0000, #DC143C);
                color: white;
                padding: 15px 25px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                z-index: 9999;
                font-family: 'Inter', sans-serif;
                font-size: 14px;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 10px;
            ">
                <div style="
                    width: 20px;
                    height: 20px;
                    border: 3px solid rgba(255,255,255,0.3);
                    border-top-color: white;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                "></div>
                <span>Loading market data...</span>
            </div>
            <style>
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
            </style>
        `;
        document.body.appendChild(indicator);
    }

    hideLoadingIndicator() {
        const indicator = document.getElementById('spartan-preloader-indicator');
        if (indicator) {
            indicator.style.transition = 'opacity 0.3s';
            indicator.style.opacity = '0';
            setTimeout(() => indicator.remove(), 300);
        }
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Auto-initialize when script loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.spartanPreloader = new SpartanDataPreloader();
    });
} else {
    window.spartanPreloader = new SpartanDataPreloader();
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SpartanDataPreloader;
}
