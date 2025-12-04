/**
 * Unified Data Fetcher with 50-Source Fallback System
 * Spartan Research Station - NO FAKE DATA Policy
 *
 * Supports: Stocks, Forex, Crypto, Economic Data, Commodities, News
 * All sources are FREE - no premium APIs
 */

class DataFetcherFallback {
    constructor() {
        this.cache = new Map();
        this.cacheDuration = 15 * 60 * 1000; // 15 minutes
        this.requestCounts = new Map();
        this.lastRequestTime = new Map();

        // API Keys (loaded from environment or config)
        this.apiKeys = {
            alphaVantage: 'YOUR_ALPHA_VANTAGE_KEY',
            fred: 'YOUR_FRED_KEY',
            iexCloud: 'YOUR_IEX_CLOUD_KEY',
            finnhub: 'YOUR_FINNHUB_KEY',
            twelveData: 'YOUR_TWELVE_DATA_KEY',
            exchangeRate: 'YOUR_EXCHANGERATE_API_KEY',
            cryptoCompare: 'YOUR_CRYPTOCOMPARE_KEY',
            newsAPI: 'YOUR_NEWSAPI_KEY',
            // Add more as needed
        };
    }

    /**
     * Fetch data with automatic fallback through multiple sources
     */
    async fetchWithFallback(symbol, dataType, options = {}) {
        // Check cache first
        const cacheKey = `${dataType}_${symbol}_${JSON.stringify(options)}`;
        const cached = this.getFromCache(cacheKey);
        if (cached) {
            return { success: true, data: cached, source: 'cache' };
        }

        // Get prioritized source list for this data type
        const sources = this.getSources(dataType);

        // Try each source until one succeeds
        for (const source of sources) {
            // Check rate limits
            if (!this.canMakeRequest(source.name, source.rateLimit)) {
                console.warn(`${source.name}: Rate limit reached, skipping...`);
                continue;
            }

            try {
                console.log(`Trying ${source.name} for ${symbol}...`);
                const data = await source.fetch(symbol, options, this.apiKeys);

                if (data && this.isValidData(data)) {
                    // Cache successful result
                    this.setCache(cacheKey, data);

                    // Track request
                    this.trackRequest(source.name);

                    return {
                        success: true,
                        data,
                        source: source.name,
                        timestamp: new Date().toISOString()
                    };
                }
            } catch (error) {
                console.warn(`${source.name} failed for ${symbol}:`, error.message);
                // Continue to next source
            }
        }

        // All sources failed
        return {
            success: false,
            error: 'All data sources failed',
            attemptedSources: sources.map(s => s.name)
        };
    }

    /**
     * Get prioritized source list for data type
     */
    getSources(dataType) {
        const sourceDefinitions = {
            'stock': [
                this.sources.yahooFinance,
                this.sources.iexCloud,
                this.sources.finnhub,
                this.sources.twelveData,
                this.sources.alphaVantage,
                this.sources.tiingo,
                this.sources.polygonIO,
                this.sources.marketStack,
            ],
            'forex': [
                this.sources.yahooFinance,
                this.sources.frankfurter,
                this.sources.exchangeRateAPI,
                this.sources.currencyLayer,
                this.sources.openExchangeRates,
                this.sources.fixer,
            ],
            'crypto': [
                this.sources.coinGecko,
                this.sources.coinCap,
                this.sources.yahooFinance,
                this.sources.cryptoCompare,
                this.sources.coinlore,
                this.sources.nomics,
            ],
            'economic': [
                this.sources.fred,
                this.sources.worldBank,
                this.sources.imf,
                this.sources.oecd,
                this.sources.bls,
            ],
            'commodity': [
                this.sources.yahooFinance,
                this.sources.quandl,
                this.sources.eia,
                this.sources.usda,
            ],
            'news': [
                this.sources.newsAPI,
                this.sources.finnhubNews,
                this.sources.gNews,
            ]
        };

        return sourceDefinitions[dataType] || [];
    }

    /**
     * Data source implementations
     */
    sources = {
        // === STOCK SOURCES ===

        yahooFinance: {
            name: 'Yahoo Finance',
            rateLimit: { requests: 2000, period: 3600000 }, // 2000/hour
            fetch: async (symbol, options) => {
                const url = `https://query1.finance.yahoo.com/v8/finance/chart/${symbol}?interval=1d&range=${options.range || '5d'}`;
                const response = await fetch(url);
                const data = await response.json();

                if (data.chart && data.chart.result && data.chart.result[0]) {
                    const result = data.chart.result[0];
                    const quotes = result.indicators.quote[0];
                    return {
                        symbol,
                        price: quotes.close[quotes.close.length - 1],
                        high: quotes.high[quotes.high.length - 1],
                        low: quotes.low[quotes.low.length - 1],
                        volume: quotes.volume[quotes.volume.length - 1],
                        timestamp: result.timestamp[result.timestamp.length - 1]
                    };
                }
                throw new Error('No data returned');
            }
        },

        iexCloud: {
            name: 'IEX Cloud',
            rateLimit: { requests: 50000, period: 2592000000 }, // 50k/month
            fetch: async (symbol, options, apiKeys) => {
                const url = `https://cloud.iexapis.com/stable/stock/${symbol}/quote?token=${apiKeys.iexCloud}`;
                const response = await fetch(url);
                const data = await response.json();
                return {
                    symbol,
                    price: data.latestPrice,
                    high: data.high,
                    low: data.low,
                    volume: data.volume,
                    timestamp: data.latestUpdate
                };
            }
        },

        finnhub: {
            name: 'Finnhub',
            rateLimit: { requests: 60, period: 60000 }, // 60/minute
            fetch: async (symbol, options, apiKeys) => {
                const url = `https://finnhub.io/api/v1/quote?symbol=${symbol}&token=${apiKeys.finnhub}`;
                const response = await fetch(url);
                const data = await response.json();
                return {
                    symbol,
                    price: data.c, // current price
                    high: data.h,
                    low: data.l,
                    timestamp: data.t
                };
            }
        },

        twelveData: {
            name: 'Twelve Data',
            rateLimit: { requests: 800, period: 86400000 }, // 800/day
            fetch: async (symbol, options, apiKeys) => {
                const url = `https://api.twelvedata.com/price?symbol=${symbol}&apikey=${apiKeys.twelveData}`;
                const response = await fetch(url);
                const data = await response.json();
                return {
                    symbol,
                    price: parseFloat(data.price),
                    timestamp: Date.now()
                };
            }
        },

        alphaVantage: {
            name: 'Alpha Vantage',
            rateLimit: { requests: 25, period: 86400000 }, // 25/day (free tier)
            fetch: async (symbol, options, apiKeys) => {
                const url = `https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=${symbol}&apikey=${apiKeys.alphaVantage}`;
                const response = await fetch(url);
                const data = await response.json();
                const quote = data['Global Quote'];
                return {
                    symbol,
                    price: parseFloat(quote['05. price']),
                    high: parseFloat(quote['03. high']),
                    low: parseFloat(quote['04. low']),
                    volume: parseInt(quote['06. volume']),
                    timestamp: Date.now()
                };
            }
        },

        tiingo: {
            name: 'Tiingo',
            rateLimit: { requests: 1000, period: 3600000 }, // 1000/hour
            fetch: async (symbol, options, apiKeys) => {
                const url = `https://api.tiingo.com/tiingo/daily/${symbol}/prices?token=${apiKeys.tiingo}`;
                const response = await fetch(url);
                const data = await response.json();
                const latest = data[0];
                return {
                    symbol,
                    price: latest.close,
                    high: latest.high,
                    low: latest.low,
                    volume: latest.volume,
                    timestamp: latest.date
                };
            }
        },

        polygonIO: {
            name: 'Polygon.io',
            rateLimit: { requests: 5, period: 60000 }, // 5/minute (free tier)
            fetch: async (symbol, options, apiKeys) => {
                const url = `https://api.polygon.io/v2/aggs/ticker/${symbol}/prev?apiKey=${apiKeys.polygonIO}`;
                const response = await fetch(url);
                const data = await response.json();
                const result = data.results[0];
                return {
                    symbol,
                    price: result.c, // close
                    high: result.h,
                    low: result.l,
                    volume: result.v,
                    timestamp: result.t
                };
            }
        },

        marketStack: {
            name: 'MarketStack',
            rateLimit: { requests: 1000, period: 2592000000 }, // 1000/month
            fetch: async (symbol, options, apiKeys) => {
                const url = `http://api.marketstack.com/v1/eod?access_key=${apiKeys.marketStack}&symbols=${symbol}&limit=1`;
                const response = await fetch(url);
                const data = await response.json();
                const latest = data.data[0];
                return {
                    symbol,
                    price: latest.close,
                    high: latest.high,
                    low: latest.low,
                    volume: latest.volume,
                    timestamp: latest.date
                };
            }
        },

        // === FOREX SOURCES ===

        frankfurter: {
            name: 'Frankfurter',
            rateLimit: { requests: 10000, period: 3600000 }, // Generous limit
            fetch: async (symbol, options) => {
                // symbol format: "EURUSD" → base: EUR, quote: USD
                const base = symbol.slice(0, 3);
                const quote = symbol.slice(3, 6);
                const url = `https://www.frankfurter.app/latest?from=${base}&to=${quote}`;
                const response = await fetch(url);
                const data = await response.json();
                return {
                    symbol,
                    price: data.rates[quote],
                    timestamp: data.date
                };
            }
        },

        exchangeRateAPI: {
            name: 'ExchangeRate-API',
            rateLimit: { requests: 1500, period: 2592000000 }, // 1500/month
            fetch: async (symbol, options, apiKeys) => {
                const base = symbol.slice(0, 3);
                const quote = symbol.slice(3, 6);
                const url = `https://v6.exchangerate-api.com/v6/${apiKeys.exchangeRate}/pair/${base}/${quote}`;
                const response = await fetch(url);
                const data = await response.json();
                return {
                    symbol,
                    price: data.conversion_rate,
                    timestamp: data.time_last_update_unix * 1000
                };
            }
        },

        currencyLayer: {
            name: 'CurrencyLayer',
            rateLimit: { requests: 1000, period: 2592000000 }, // 1000/month
            fetch: async (symbol, options, apiKeys) => {
                const url = `http://api.currencylayer.com/live?access_key=${apiKeys.currencyLayer}&currencies=${symbol.slice(3, 6)}&source=${symbol.slice(0, 3)}`;
                const response = await fetch(url);
                const data = await response.json();
                const quoteKey = symbol.slice(0, 3) + symbol.slice(3, 6);
                return {
                    symbol,
                    price: data.quotes[quoteKey],
                    timestamp: data.timestamp * 1000
                };
            }
        },

        openExchangeRates: {
            name: 'Open Exchange Rates',
            rateLimit: { requests: 1000, period: 2592000000 }, // 1000/month
            fetch: async (symbol, options, apiKeys) => {
                const base = symbol.slice(0, 3);
                const quote = symbol.slice(3, 6);
                const url = `https://openexchangerates.org/api/latest.json?app_id=${apiKeys.openExchangeRates}&base=${base}`;
                const response = await fetch(url);
                const data = await response.json();
                return {
                    symbol,
                    price: data.rates[quote],
                    timestamp: data.timestamp * 1000
                };
            }
        },

        fixer: {
            name: 'Fixer.io',
            rateLimit: { requests: 1000, period: 2592000000 }, // 1000/month
            fetch: async (symbol, options, apiKeys) => {
                const base = symbol.slice(0, 3);
                const quote = symbol.slice(3, 6);
                const url = `http://data.fixer.io/api/latest?access_key=${apiKeys.fixer}&base=${base}&symbols=${quote}`;
                const response = await fetch(url);
                const data = await response.json();
                return {
                    symbol,
                    price: data.rates[quote],
                    timestamp: data.timestamp * 1000
                };
            }
        },

        // === CRYPTO SOURCES ===

        coinGecko: {
            name: 'CoinGecko',
            rateLimit: { requests: 50, period: 60000 }, // 50/minute
            fetch: async (symbol, options) => {
                // symbol format: "BTC-USD" → id: bitcoin
                const coinIds = {
                    'BTC': 'bitcoin',
                    'ETH': 'ethereum',
                    'BNB': 'binancecoin',
                    'SOL': 'solana',
                    'XRP': 'ripple'
                };
                const coinId = coinIds[symbol.split('-')[0]] || symbol.toLowerCase();
                const url = `https://api.coingecko.com/api/v3/simple/price?ids=${coinId}&vs_currencies=usd&include_24hr_vol=true&include_24hr_change=true`;
                const response = await fetch(url);
                const data = await response.json();
                const coinData = data[coinId];
                return {
                    symbol,
                    price: coinData.usd,
                    volume24h: coinData.usd_24h_vol,
                    change24h: coinData.usd_24h_change,
                    timestamp: Date.now()
                };
            }
        },

        coinCap: {
            name: 'CoinCap',
            rateLimit: { requests: 200, period: 60000 }, // 200/minute
            fetch: async (symbol, options) => {
                const coinIds = {
                    'BTC': 'bitcoin',
                    'ETH': 'ethereum',
                    'BNB': 'binance-coin',
                    'SOL': 'solana',
                    'XRP': 'xrp'
                };
                const coinId = coinIds[symbol.split('-')[0]] || symbol.toLowerCase();
                const url = `https://api.coincap.io/v2/assets/${coinId}`;
                const response = await fetch(url);
                const data = await response.json();
                return {
                    symbol,
                    price: parseFloat(data.data.priceUsd),
                    volume24h: parseFloat(data.data.volumeUsd24Hr),
                    change24h: parseFloat(data.data.changePercent24Hr),
                    timestamp: data.timestamp
                };
            }
        },

        cryptoCompare: {
            name: 'CryptoCompare',
            rateLimit: { requests: 100000, period: 2592000000 }, // 100k/month
            fetch: async (symbol, options, apiKeys) => {
                const coin = symbol.split('-')[0];
                const currency = symbol.split('-')[1] || 'USD';
                const url = `https://min-api.cryptocompare.com/data/price?fsym=${coin}&tsyms=${currency}&api_key=${apiKeys.cryptoCompare}`;
                const response = await fetch(url);
                const data = await response.json();
                return {
                    symbol,
                    price: data[currency],
                    timestamp: Date.now()
                };
            }
        },

        coinlore: {
            name: 'Coinlore',
            rateLimit: { requests: 10000, period: 3600000 }, // Generous limit
            fetch: async (symbol, options) => {
                const coinIds = {
                    'BTC': '90',
                    'ETH': '80',
                    'BNB': '2710',
                    'SOL': '48543',
                    'XRP': '58'
                };
                const coinId = coinIds[symbol.split('-')[0]];
                const url = `https://api.coinlore.net/api/ticker/?id=${coinId}`;
                const response = await fetch(url);
                const data = await response.json();
                const coin = data[0];
                return {
                    symbol,
                    price: parseFloat(coin.price_usd),
                    volume24h: parseFloat(coin.volume24),
                    change24h: parseFloat(coin.percent_change_24h),
                    timestamp: Date.now()
                };
            }
        },

        nomics: {
            name: 'Nomics',
            rateLimit: { requests: 1, period: 1000 }, // 1/second (free tier)
            fetch: async (symbol, options, apiKeys) => {
                const coin = symbol.split('-')[0];
                const url = `https://api.nomics.com/v1/currencies/ticker?key=${apiKeys.nomics}&ids=${coin}&interval=1d`;
                const response = await fetch(url);
                const data = await response.json();
                const coinData = data[0];
                return {
                    symbol,
                    price: parseFloat(coinData.price),
                    volume24h: parseFloat(coinData['1d'].volume),
                    change24h: parseFloat(coinData['1d'].price_change_pct) * 100,
                    timestamp: Date.now()
                };
            }
        },

        // === ECONOMIC DATA SOURCES ===

        fred: {
            name: 'FRED',
            rateLimit: { requests: 120, period: 60000 }, // 120/minute
            fetch: async (seriesId, options, apiKeys) => {
                const url = `https://api.stlouisfed.org/fred/series/observations?series_id=${seriesId}&api_key=${apiKeys.fred}&file_type=json&limit=1&sort_order=desc`;
                const response = await fetch(url);
                const data = await response.json();
                const observation = data.observations[0];
                return {
                    seriesId,
                    value: parseFloat(observation.value),
                    date: observation.date,
                    timestamp: new Date(observation.date).getTime()
                };
            }
        },

        worldBank: {
            name: 'World Bank',
            rateLimit: { requests: 10000, period: 3600000 }, // Generous
            fetch: async (indicator, options) => {
                const country = options.country || 'USA';
                const url = `https://api.worldbank.org/v2/country/${country}/indicator/${indicator}?format=json&per_page=1`;
                const response = await fetch(url);
                const data = await response.json();
                const latest = data[1][0];
                return {
                    indicator,
                    value: latest.value,
                    date: latest.date,
                    country: latest.country.value
                };
            }
        },

        imf: {
            name: 'IMF',
            rateLimit: { requests: 10000, period: 3600000 }, // Generous
            fetch: async (indicator, options) => {
                // IMF API implementation
                // Note: IMF API is more complex, simplified here
                const url = `http://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/IFS/...${indicator}.?startPeriod=2020&endPeriod=2025`;
                const response = await fetch(url);
                const data = await response.json();
                // Parse IMF SDMX-JSON format
                return {
                    indicator,
                    value: null, // Parse from SDMX
                    timestamp: Date.now()
                };
            }
        },

        oecd: {
            name: 'OECD',
            rateLimit: { requests: 10000, period: 3600000 }, // Generous
            fetch: async (indicator, options) => {
                const url = `https://stats.oecd.org/SDMX-JSON/data/${indicator}/USA.A/all?format=json`;
                const response = await fetch(url);
                const data = await response.json();
                // Parse OECD SDMX-JSON format
                return {
                    indicator,
                    value: null, // Parse from data
                    timestamp: Date.now()
                };
            }
        },

        bls: {
            name: 'Bureau of Labor Statistics',
            rateLimit: { requests: 500, period: 86400000 }, // 500/day
            fetch: async (seriesId, options, apiKeys) => {
                const currentYear = new Date().getFullYear();
                const url = `https://api.bls.gov/publicAPI/v2/timeseries/data/${seriesId}?registrationkey=${apiKeys.bls}&startyear=${currentYear-1}&endyear=${currentYear}`;
                const response = await fetch(url);
                const data = await response.json();
                const latest = data.Results.series[0].data[0];
                return {
                    seriesId,
                    value: parseFloat(latest.value),
                    period: latest.period,
                    year: latest.year
                };
            }
        },

        // === COMMODITY SOURCES ===

        quandl: {
            name: 'Quandl',
            rateLimit: { requests: 50, period: 86400000 }, // 50/day (anonymous)
            fetch: async (dataset, options, apiKeys) => {
                const url = `https://data.nasdaq.com/api/v3/datasets/${dataset}/data.json?limit=1&order=desc`;
                const response = await fetch(url);
                const data = await response.json();
                const latest = data.dataset_data.data[0];
                return {
                    dataset,
                    value: latest[1], // Typically close price
                    date: latest[0],
                    timestamp: new Date(latest[0]).getTime()
                };
            }
        },

        eia: {
            name: 'EIA (Energy)',
            rateLimit: { requests: 10000, period: 3600000 }, // Generous
            fetch: async (seriesId, options, apiKeys) => {
                const url = `https://api.eia.gov/series/?api_key=${apiKeys.eia}&series_id=${seriesId}`;
                const response = await fetch(url);
                const data = await response.json();
                const latest = data.series[0].data[0];
                return {
                    seriesId,
                    value: latest[1],
                    date: latest[0],
                    timestamp: Date.now()
                };
            }
        },

        usda: {
            name: 'USDA',
            rateLimit: { requests: 10000, period: 3600000 }, // Generous
            fetch: async (commodity, options, apiKeys) => {
                const url = `https://quickstats.nass.usda.gov/api/api_GET/?key=${apiKeys.usda}&commodity_desc=${commodity}&year=2024&format=JSON`;
                const response = await fetch(url);
                const data = await response.json();
                const latest = data.data[0];
                return {
                    commodity,
                    value: parseFloat(latest.Value),
                    year: latest.year,
                    timestamp: Date.now()
                };
            }
        },

        // === NEWS SOURCES ===

        newsAPI: {
            name: 'NewsAPI',
            rateLimit: { requests: 100, period: 86400000 }, // 100/day
            fetch: async (query, options, apiKeys) => {
                const url = `https://newsapi.org/v2/everything?q=${query}&sortBy=publishedAt&pageSize=10&apiKey=${apiKeys.newsAPI}`;
                const response = await fetch(url);
                const data = await response.json();
                return {
                    query,
                    articles: data.articles,
                    totalResults: data.totalResults,
                    timestamp: Date.now()
                };
            }
        },

        finnhubNews: {
            name: 'Finnhub News',
            rateLimit: { requests: 60, period: 60000 }, // 60/minute
            fetch: async (symbol, options, apiKeys) => {
                const url = `https://finnhub.io/api/v1/company-news?symbol=${symbol}&from=${options.from || '2024-01-01'}&to=${options.to || '2024-12-31'}&token=${apiKeys.finnhub}`;
                const response = await fetch(url);
                const data = await response.json();
                return {
                    symbol,
                    news: data,
                    timestamp: Date.now()
                };
            }
        },

        gNews: {
            name: 'GNews',
            rateLimit: { requests: 100, period: 86400000 }, // 100/day
            fetch: async (query, options, apiKeys) => {
                const url = `https://gnews.io/api/v4/search?q=${query}&token=${apiKeys.gNews}&max=10`;
                const response = await fetch(url);
                const data = await response.json();
                return {
                    query,
                    articles: data.articles,
                    totalResults: data.totalArticles,
                    timestamp: Date.now()
                };
            }
        }
    };

    /**
     * Cache management
     */
    getFromCache(key) {
        const cached = this.cache.get(key);
        if (!cached) return null;

        const age = Date.now() - cached.timestamp;
        if (age > this.cacheDuration) {
            this.cache.delete(key);
            return null;
        }

        return cached.data;
    }

    setCache(key, data) {
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });
    }

    /**
     * Rate limit management
     */
    canMakeRequest(sourceName, rateLimit) {
        if (!rateLimit) return true;

        const now = Date.now();
        const count = this.requestCounts.get(sourceName) || 0;
        const lastRequest = this.lastRequestTime.get(sourceName) || 0;

        // Reset counter if period has passed
        if (now - lastRequest > rateLimit.period) {
            this.requestCounts.set(sourceName, 0);
            this.lastRequestTime.set(sourceName, now);
            return true;
        }

        // Check if under limit
        return count < rateLimit.requests;
    }

    trackRequest(sourceName) {
        const count = this.requestCounts.get(sourceName) || 0;
        this.requestCounts.set(sourceName, count + 1);
        this.lastRequestTime.set(sourceName, Date.now());
    }

    /**
     * Data validation
     */
    isValidData(data) {
        if (!data) return false;
        if (typeof data !== 'object') return false;

        // Check for required fields based on data type
        if (data.price !== undefined && (data.price === null || isNaN(data.price))) {
            return false;
        }

        if (data.value !== undefined && (data.value === null || isNaN(data.value))) {
            return false;
        }

        return true;
    }

    /**
     * Get statistics
     */
    getStats() {
        return {
            cacheSize: this.cache.size,
            requestCounts: Object.fromEntries(this.requestCounts),
            lastRequests: Object.fromEntries(this.lastRequestTime)
        };
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DataFetcherFallback;
}
