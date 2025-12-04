/**
 * FRED API Client for Spartan Research Station
 *
 * Wrapper for FRED (Federal Reserve Economic Data) API access through backend proxy
 *
 * CRITICAL RULES:
 * ❌ ZERO Math.random() - EVER
 * ❌ ZERO fake/mock data
 * ✅ ONLY real FRED API data
 * ✅ Return NULL on errors (no fake fallbacks)
 *
 * @author Spartan Labs
 * @version 1.0.0
 */

class FredApiClient {
    constructor(config = {}) {
        // API endpoint (proxied through backend on port 5002)
        this.baseUrl = config.baseUrl || 'http://localhost:8888/api/fred';

        // Cache settings (15 minutes default)
        this.cacheTTL = config.cacheTTL || 15 * 60 * 1000;
        this.cache = new Map();

        // Rate limiting (120 requests per minute for FRED API)
        this.rateLimit = {
            maxRequests: 120,
            perMinute: 60 * 1000,
            requests: [],
        };

        // Error handling
        this.retryAttempts = config.retryAttempts || 3;
        this.retryDelay = config.retryDelay || 1000;
    }

    /**
     * Fetch multiple FRED series concurrently
     *
     * @param {Array<Object>} seriesArray - Array of series objects with {id, name}
     * @param {Object} options - Options: startDate, endDate, limit
     * @returns {Promise<Object>} Object with series results keyed by series ID
     */
    async fetchMultipleSeries(seriesArray, options = {}) {
        try {
            // Validate input
            if (!Array.isArray(seriesArray) || seriesArray.length === 0) {
                console.error('FredApiClient: seriesArray must be a non-empty array');
                return null;
            }

            // Check rate limiting
            await this._enforceRateLimit();

            // Fetch all series in parallel (with rate limiting)
            const fetchPromises = seriesArray.map(async (series) => {
                const seriesId = typeof series === 'string' ? series : series.id || series;

                try {
                    const data = await this.fetchSeriesObservations(seriesId, options);
                    return {
                        id: seriesId,
                        data: data,
                        success: data !== null
                    };
                } catch (error) {
                    console.error(`FredApiClient: Error fetching ${seriesId}:`, error);
                    return {
                        id: seriesId,
                        data: null,
                        success: false,
                        error: error.message
                    };
                }
            });

            // Wait for all fetches to complete
            const results = await Promise.all(fetchPromises);

            // Convert array to object keyed by series ID
            const resultObject = {};
            results.forEach(result => {
                resultObject[result.id] = result;
            });

            return resultObject;

        } catch (error) {
            console.error('FredApiClient.fetchMultipleSeries error:', error);
            return null;
        }
    }

    /**
     * Fetch observations for a single FRED series
     *
     * @param {string} seriesId - FRED series ID (e.g., 'VIXCLS', 'DGS10')
     * @param {Object} options - Options: startDate, endDate, limit, sortOrder
     * @returns {Promise<Object>} FRED API response or null on error
     */
    async fetchSeriesObservations(seriesId, options = {}) {
        try {
            // Validate series ID
            if (!seriesId || typeof seriesId !== 'string') {
                console.error('FredApiClient: Invalid series ID');
                return null;
            }

            // Build cache key
            const cacheKey = this._buildCacheKey(seriesId, options);

            // Check cache
            const cached = this._getCache(cacheKey);
            if (cached !== null) {
                return cached;
            }

            // Check rate limiting
            await this._enforceRateLimit();

            // Build query parameters
            const params = new URLSearchParams({
                series_id: seriesId,
                limit: options.limit || '100',
                sort_order: options.sortOrder || 'desc'
            });

            // Add date filters if provided
            if (options.startDate) {
                params.append('observation_start', this._formatDate(options.startDate));
            }
            if (options.endDate) {
                params.append('observation_end', this._formatDate(options.endDate));
            }

            // Make API request with retry logic
            const url = `${this.baseUrl}/series/observations?${params}`;
            const data = await this._fetchWithRetry(url);

            // Validate response
            if (!data || data.error) {
                console.error(`FredApiClient: API error for ${seriesId}:`, data?.error);
                return null;
            }

            // Cache successful response
            this._setCache(cacheKey, data);

            // Record request for rate limiting
            this._recordRequest();

            return data;

        } catch (error) {
            console.error(`FredApiClient.fetchSeriesObservations error (${seriesId}):`, error);
            return null;
        }
    }

    /**
     * Clear all cached data
     */
    clearCache() {
        this.cache.clear();
        console.log('FredApiClient: Cache cleared');
    }

    /**
     * Get cache statistics
     */
    getCacheStats() {
        return {
            entries: this.cache.size,
            ttl: this.cacheTTL,
            rateLimit: {
                requests: this.rateLimit.requests.length,
                max: this.rateLimit.maxRequests
            }
        };
    }

    // ========== PRIVATE METHODS ==========

    /**
     * Fetch with automatic retry on failure
     */
    async _fetchWithRetry(url, attempt = 1) {
        try {
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            return data;

        } catch (error) {
            // Retry on failure (up to retryAttempts)
            if (attempt < this.retryAttempts) {
                console.warn(`FredApiClient: Retry ${attempt}/${this.retryAttempts} for ${url}`);
                await this._delay(this.retryDelay * attempt);
                return this._fetchWithRetry(url, attempt + 1);
            } else {
                console.error(`FredApiClient: All retry attempts failed for ${url}:`, error);
                return null;
            }
        }
    }

    /**
     * Enforce rate limiting (120 requests per minute)
     */
    async _enforceRateLimit() {
        const now = Date.now();

        // Remove requests older than 1 minute
        this.rateLimit.requests = this.rateLimit.requests.filter(
            time => now - time < this.rateLimit.perMinute
        );

        // Check if we've hit the rate limit
        if (this.rateLimit.requests.length >= this.rateLimit.maxRequests) {
            const oldestRequest = this.rateLimit.requests[0];
            const waitTime = this.rateLimit.perMinute - (now - oldestRequest);

            if (waitTime > 0) {
                console.warn(`FredApiClient: Rate limit reached, waiting ${waitTime}ms`);
                await this._delay(waitTime);
            }
        }
    }

    /**
     * Record a request for rate limiting
     */
    _recordRequest() {
        this.rateLimit.requests.push(Date.now());
    }

    /**
     * Build cache key from series ID and options
     */
    _buildCacheKey(seriesId, options) {
        const parts = [seriesId];

        if (options.limit) parts.push(`limit:${options.limit}`);
        if (options.sortOrder) parts.push(`sort:${options.sortOrder}`);
        if (options.startDate) parts.push(`start:${this._formatDate(options.startDate)}`);
        if (options.endDate) parts.push(`end:${this._formatDate(options.endDate)}`);

        return parts.join('|');
    }

    /**
     * Get data from cache
     */
    _getCache(key) {
        const cached = this.cache.get(key);

        if (!cached) {
            return null;
        }

        // Check if cache is expired
        const now = Date.now();
        if (now - cached.timestamp > this.cacheTTL) {
            this.cache.delete(key);
            return null;
        }

        return cached.data;
    }

    /**
     * Set data in cache
     */
    _setCache(key, data) {
        this.cache.set(key, {
            data: data,
            timestamp: Date.now()
        });
    }

    /**
     * Format date for FRED API (YYYY-MM-DD)
     */
    _formatDate(date) {
        if (typeof date === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(date)) {
            return date; // Already formatted
        }

        const d = new Date(date);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');

        return `${year}-${month}-${day}`;
    }

    /**
     * Delay helper (for rate limiting and retries)
     */
    _delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FredApiClient;
}
