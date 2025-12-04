/**
 * Timeframe Data Fetcher: 1-3 Month Positions
 *
 * Real data sources:
 * - FRED API for economic cycle indicators
 * - Yahoo Finance for correlation matrix and sector rotation
 * - No fake data, only real calculations
 *
 * @author Spartan Labs
 * @version 1.0.0
 */

class TimeframeDataFetcher_1_3_Months {
    constructor() {
        // Initialize FRED API client
        this.fredClient = new FredApiClient({
            useProxy: true,
            baseUrl: '/api/fred'
        });

        // Economic indicators for cycle classification
        this.economicIndicators = {
            gdp: 'GDP',           // GDP Growth
            unemployment: 'UNRATE',   // Unemployment Rate
            inflation: 'CPIAUCSL',    // CPI
            fedFunds: 'DFF'           // Fed Funds Rate
        };

        // Sector ETFs for rotation analysis
        this.sectorETFs = [
            { symbol: 'XLK', name: 'Technology', weight: 1.0 },
            { symbol: 'XLF', name: 'Financial', weight: 1.0 },
            { symbol: 'XLE', name: 'Energy', weight: 1.0 },
            { symbol: 'XLV', name: 'Healthcare', weight: 1.0 },
            { symbol: 'XLI', name: 'Industrial', weight: 1.0 },
            { symbol: 'XLP', name: 'Consumer Staples', weight: 1.0 },
            { symbol: 'XLY', name: 'Consumer Discretionary', weight: 1.0 },
            { symbol: 'XLU', name: 'Utilities', weight: 1.0 },
            { symbol: 'XLB', name: 'Materials', weight: 1.0 }
        ];

        // Correlation matrix symbols
        this.correlationSymbols = ['SPY', 'TLT', 'GLD', 'UUP', 'USO'];
    }

    /**
     * Fetch economic cycle indicator composite
     * @returns {Promise<Object>}
     */
    async fetchEconomicCycleIndicator() {
        try {
            console.log('[1-3M] Fetching economic cycle indicators...');

            // Fetch all economic indicators (last 12 months for trend)
            const endDate = new Date();
            const startDate = new Date();
            startDate.setMonth(startDate.getMonth() - 12);

            const options = {
                startDate: startDate.toISOString().split('T')[0],
                endDate: endDate.toISOString().split('T')[0],
                frequency: 'm', // Monthly
                aggregationMethod: 'avg'
            };

            // Fetch all indicators in parallel
            const [gdpResult, unrateResult, cpiResult, dffResult] = await Promise.all([
                this.fredClient.fetchSeriesObservations(this.economicIndicators.gdp, options),
                this.fredClient.fetchSeriesObservations(this.economicIndicators.unemployment, options),
                this.fredClient.fetchSeriesObservations(this.economicIndicators.inflation, options),
                this.fredClient.fetchSeriesObservations(this.economicIndicators.fedFunds, options)
            ]);

            // Calculate composite score (normalized)
            const composite = this.calculateEconomicComposite({
                gdp: gdpResult.data?.observations || [],
                unemployment: unrateResult.data?.observations || [],
                inflation: cpiResult.data?.observations || [],
                fedFunds: dffResult.data?.observations || []
            });

            return {
                success: true,
                data: composite,
                lastUpdated: new Date().toISOString()
            };

        } catch (error) {
            console.error('[1-3M] Error fetching economic cycle:', error);
            return {
                success: false,
                error: error.message,
                data: null
            };
        }
    }

    /**
     * Calculate economic composite score from FRED data
     * @param {Object} indicators - Raw FRED observations
     * @returns {Object}
     */
    calculateEconomicComposite(indicators) {
        // Get latest values (most recent non-null observation)
        const getLatestValue = (observations) => {
            const validObs = observations.filter(o => o.isValid);
            return validObs.length > 0 ? validObs[validObs.length - 1].value : null;
        };

        const gdpLatest = getLatestValue(indicators.gdp);
        const unemploymentLatest = getLatestValue(indicators.unemployment);
        const inflationLatest = getLatestValue(indicators.inflation);
        const fedFundsLatest = getLatestValue(indicators.fedFunds);

        // Calculate 3-month change (trend)
        const getThreeMonthChange = (observations) => {
            const validObs = observations.filter(o => o.isValid);
            if (validObs.length < 4) return 0;
            const latest = validObs[validObs.length - 1].value;
            const threeMonthsAgo = validObs[validObs.length - 4].value;
            return ((latest - threeMonthsAgo) / threeMonthsAgo) * 100;
        };

        const gdpChange = getThreeMonthChange(indicators.gdp);
        const unemploymentChange = getThreeMonthChange(indicators.unemployment);
        const inflationChange = getThreeMonthChange(indicators.inflation);

        // Composite score calculation (0-100 scale)
        // GDP growth positive = +25, Unemployment falling = +25, Inflation moderate = +25, Fed accommodative = +25
        let score = 50; // Neutral baseline

        // GDP contribution (positive growth = good)
        if (gdpChange > 0) score += 15;
        else if (gdpChange < -2) score -= 15;

        // Unemployment contribution (falling = good)
        if (unemploymentChange < -0.5) score += 15;
        else if (unemploymentChange > 0.5) score -= 15;

        // Inflation contribution (2-3% target = good)
        const inflationRate = inflationLatest || 0;
        if (inflationRate >= 2 && inflationRate <= 3) score += 10;
        else if (inflationRate > 5) score -= 15;

        // Fed Funds contribution (lower = accommodative)
        if (fedFundsLatest < 2) score += 10;
        else if (fedFundsLatest > 4) score -= 10;

        // Classify regime based on composite score
        let regime = 'Neutral';
        let allocation = { stocks: 60, bonds: 30, cash: 10 }; // Default balanced

        if (score >= 65) {
            regime = 'Expansion';
            allocation = { stocks: 75, bonds: 20, cash: 5 };
        } else if (score <= 35) {
            regime = 'Recession';
            allocation = { stocks: 30, bonds: 50, cash: 20 };
        } else if (score < 50) {
            regime = 'Slowdown';
            allocation = { stocks: 50, bonds: 35, cash: 15 };
        }

        return {
            compositeScore: Math.max(0, Math.min(100, score)),
            regime,
            allocation,
            indicators: {
                gdp: { latest: gdpLatest, change: gdpChange },
                unemployment: { latest: unemploymentLatest, change: unemploymentChange },
                inflation: { latest: inflationLatest, change: inflationChange },
                fedFunds: { latest: fedFundsLatest }
            },
            interpretation: this.interpretRegime(regime)
        };
    }

    /**
     * Interpret economic regime
     * @param {string} regime
     * @returns {string}
     */
    interpretRegime(regime) {
        const interpretations = {
            'Expansion': 'Economy growing strongly. Favor cyclical stocks, reduce defensive positions.',
            'Slowdown': 'Growth moderating. Balance growth and defensive sectors.',
            'Recession': 'Economic contraction. Favor bonds, utilities, consumer staples.',
            'Neutral': 'Mixed signals. Maintain balanced allocation across asset classes.'
        };
        return interpretations[regime] || interpretations['Neutral'];
    }

    /**
     * Fetch 90-day correlation matrix using Yahoo Finance proxy
     * @returns {Promise<Object>}
     */
    async fetch90DayCorrelationMatrix() {
        try {
            console.log('[1-3M] Fetching 90-day correlation matrix...');

            // Calculate date range (90 days back)
            const endDate = Math.floor(Date.now() / 1000);
            const startDate = endDate - (90 * 24 * 60 * 60);

            // Fetch historical data for all symbols
            const promises = this.correlationSymbols.map(symbol =>
                this.fetchYahooHistory(symbol, startDate, endDate)
            );

            const results = await Promise.all(promises);

            // Extract closing prices
            const priceData = {};
            results.forEach((result, index) => {
                const symbol = this.correlationSymbols[index];
                priceData[symbol] = result.closes || [];
            });

            // Calculate correlation matrix
            const correlationMatrix = this.calculateCorrelationMatrix(priceData);

            return {
                success: true,
                data: correlationMatrix,
                lastUpdated: new Date().toISOString()
            };

        } catch (error) {
            console.error('[1-3M] Error fetching correlation matrix:', error);
            return {
                success: false,
                error: error.message,
                data: null
            };
        }
    }

    /**
     * Fetch Yahoo Finance historical data via proxy
     * @param {string} symbol
     * @param {number} startDate - Unix timestamp
     * @param {number} endDate - Unix timestamp
     * @returns {Promise<Object>}
     */
    async fetchYahooHistory(symbol, startDate, endDate) {
        try {
            const url = `/api/yahoo/${symbol}?period1=${startDate}&period2=${endDate}&interval=1d`;
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`Yahoo Finance API error: ${response.status}`);
            }

            const data = await response.json();

            // Extract closing prices
            const closes = data.chart?.result?.[0]?.indicators?.quote?.[0]?.close || [];
            const timestamps = data.chart?.result?.[0]?.timestamp || [];

            return {
                symbol,
                closes: closes.filter(c => c !== null),
                timestamps,
                count: closes.length
            };

        } catch (error) {
            console.error(`[1-3M] Error fetching ${symbol}:`, error);
            return { symbol, closes: [], timestamps: [], count: 0 };
        }
    }

    /**
     * Calculate Pearson correlation matrix
     * @param {Object} priceData - Symbol -> closes array
     * @returns {Object}
     */
    calculateCorrelationMatrix(priceData) {
        const symbols = Object.keys(priceData);
        const matrix = {};

        // Calculate returns for each symbol
        const returns = {};
        symbols.forEach(symbol => {
            returns[symbol] = this.calculateReturns(priceData[symbol]);
        });

        // Calculate pairwise correlations
        symbols.forEach(symbol1 => {
            matrix[symbol1] = {};
            symbols.forEach(symbol2 => {
                const correlation = this.calculatePearsonCorrelation(
                    returns[symbol1],
                    returns[symbol2]
                );
                matrix[symbol1][symbol2] = correlation;
            });
        });

        return {
            matrix,
            symbols,
            interpretation: this.interpretCorrelations(matrix)
        };
    }

    /**
     * Calculate daily returns from price series
     * @param {Array<number>} prices
     * @returns {Array<number>}
     */
    calculateReturns(prices) {
        const returns = [];
        for (let i = 1; i < prices.length; i++) {
            if (prices[i - 1] && prices[i]) {
                returns.push((prices[i] - prices[i - 1]) / prices[i - 1]);
            }
        }
        return returns;
    }

    /**
     * Calculate Pearson correlation coefficient
     * @param {Array<number>} x
     * @param {Array<number>} y
     * @returns {number}
     */
    calculatePearsonCorrelation(x, y) {
        const n = Math.min(x.length, y.length);
        if (n < 2) return 0;

        let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0, sumY2 = 0;

        for (let i = 0; i < n; i++) {
            sumX += x[i];
            sumY += y[i];
            sumXY += x[i] * y[i];
            sumX2 += x[i] * x[i];
            sumY2 += y[i] * y[i];
        }

        const numerator = (n * sumXY) - (sumX * sumY);
        const denominator = Math.sqrt(((n * sumX2) - (sumX * sumX)) * ((n * sumY2) - (sumY * sumY)));

        if (denominator === 0) return 0;

        return numerator / denominator;
    }

    /**
     * Interpret correlation matrix
     * @param {Object} matrix
     * @returns {string}
     */
    interpretCorrelations(matrix) {
        const spyTlt = matrix['SPY']?.['TLT'] || 0;
        const spyGld = matrix['SPY']?.['GLD'] || 0;

        if (spyTlt < -0.5) {
            return 'Strong negative SPY-TLT correlation suggests flight-to-safety dynamics active.';
        } else if (spyGld > 0.5) {
            return 'Positive SPY-GLD correlation indicates risk-on environment with inflation concerns.';
        } else {
            return 'Mixed correlations suggest transitional market regime.';
        }
    }

    /**
     * Fetch sector rotation rankings (3-month performance)
     * @returns {Promise<Object>}
     */
    async fetchSectorRotationRankings() {
        try {
            console.log('[1-3M] Fetching sector rotation rankings...');

            // Calculate date range (3 months back)
            const endDate = Math.floor(Date.now() / 1000);
            const startDate = endDate - (90 * 24 * 60 * 60);

            // Fetch historical data for all sector ETFs
            const promises = this.sectorETFs.map(sector =>
                this.fetchYahooHistory(sector.symbol, startDate, endDate)
            );

            const results = await Promise.all(promises);

            // Calculate performance and trend for each sector
            const sectorPerformance = results.map((result, index) => {
                const sector = this.sectorETFs[index];
                const closes = result.closes;

                if (closes.length < 2) {
                    return {
                        symbol: sector.symbol,
                        name: sector.name,
                        return3M: 0,
                        trend: 'Neutral',
                        trendSlope: 0
                    };
                }

                // 3-month return
                const startPrice = closes[0];
                const endPrice = closes[closes.length - 1];
                const return3M = ((endPrice - startPrice) / startPrice) * 100;

                // Calculate trend (linear regression slope)
                const trend = this.calculateTrendSlope(closes);

                return {
                    symbol: sector.symbol,
                    name: sector.name,
                    return3M,
                    trend: trend > 0.01 ? 'Up' : (trend < -0.01 ? 'Down' : 'Neutral'),
                    trendSlope: trend
                };
            });

            // Sort by 3-month return (descending)
            sectorPerformance.sort((a, b) => b.return3M - a.return3M);

            // Identify top 3 (Buy) and bottom 3 (Sell)
            const top3 = sectorPerformance.slice(0, 3);
            const bottom3 = sectorPerformance.slice(-3);

            return {
                success: true,
                data: {
                    rankings: sectorPerformance,
                    buy: top3,
                    sell: bottom3,
                    interpretation: `Buy: ${top3.map(s => s.symbol).join(', ')}. Sell: ${bottom3.map(s => s.symbol).join(', ')}.`
                },
                lastUpdated: new Date().toISOString()
            };

        } catch (error) {
            console.error('[1-3M] Error fetching sector rotation:', error);
            return {
                success: false,
                error: error.message,
                data: null
            };
        }
    }

    /**
     * Calculate trend slope using linear regression
     * @param {Array<number>} values
     * @returns {number}
     */
    calculateTrendSlope(values) {
        const n = values.length;
        if (n < 2) return 0;

        let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;

        for (let i = 0; i < n; i++) {
            sumX += i;
            sumY += values[i];
            sumXY += i * values[i];
            sumX2 += i * i;
        }

        const slope = ((n * sumXY) - (sumX * sumY)) / ((n * sumX2) - (sumX * sumX));
        return slope;
    }

    /**
     * Generate intermediate-term trade setups (1-3 month horizon)
     * Based on sector rotation and economic cycle
     * @param {Object} sectorData - Sector rotation data
     * @param {Object} economicData - Economic cycle data
     * @returns {Array}
     */
    generateIntermediateTermSetups(sectorData, economicData) {
        const setups = [];

        if (!sectorData || !economicData) return setups;

        const topSectors = sectorData.buy || [];
        const regime = economicData.regime || 'Neutral';

        // Generate setups for top 3 sectors
        topSectors.forEach((sector, index) => {
            const setup = {
                id: index + 1,
                symbol: sector.symbol,
                name: sector.name,
                direction: 'Long',
                timeframe: '1-3 Months',
                entry: `Current levels (${sector.return3M > 0 ? 'on strength' : 'on pullback'})`,
                target: `+${(sector.return3M * 0.5).toFixed(1)}% to +${(sector.return3M * 1.2).toFixed(1)}%`,
                stop: `-${Math.abs(sector.return3M * 0.3).toFixed(1)}%`,
                rationale: `Top performer in ${regime} regime. 3M return: ${sector.return3M.toFixed(2)}%. Trend: ${sector.trend}.`,
                confidence: sector.return3M > 5 ? 'High' : 'Medium'
            };
            setups.push(setup);
        });

        return setups;
    }

    /**
     * Fetch all data for 1-3 month timeframe
     * @returns {Promise<Object>}
     */
    async fetchAllData() {
        console.log('[1-3M] Fetching all data for 1-3 month timeframe...');

        const [economicCycle, correlationMatrix, sectorRotation] = await Promise.all([
            this.fetchEconomicCycleIndicator(),
            this.fetch90DayCorrelationMatrix(),
            this.fetchSectorRotationRankings()
        ]);

        // Generate trade setups based on analysis
        const setups = this.generateIntermediateTermSetups(
            sectorRotation.data,
            economicCycle.data
        );

        return {
            success: true,
            economicCycle,
            correlationMatrix,
            sectorRotation,
            tradeSetups: setups,
            lastUpdated: new Date().toISOString()
        };
    }
}

// Export for browser usage
if (typeof window !== 'undefined') {
    window.TimeframeDataFetcher_1_3_Months = TimeframeDataFetcher_1_3_Months;
}

// Export for Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TimeframeDataFetcher_1_3_Months;
}
