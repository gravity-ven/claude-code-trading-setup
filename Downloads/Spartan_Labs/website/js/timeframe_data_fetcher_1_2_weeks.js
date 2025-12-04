/**
 * SPARTAN LABS - 1-2 WEEK SWING TRADING DATA MODULE
 *
 * SHORT-TERM SWING TRADING (1-14 Days)
 * Focus: Daily momentum, short-term trends, intraday reversals
 *
 * CRITICAL RULES:
 * ❌ ZERO Math.random() - EVER
 * ❌ ZERO fake/mock data
 * ✅ ONLY real APIs (FRED, Yahoo Finance, Polygon, Alpha Vantage)
 * ✅ PostgreSQL for storage (NO SQLite)
 *
 * @author Spartan Labs
 * @version 1.0.0
 */

class TimeframeDataFetcher_1_2_Weeks {
    constructor(config = {}) {
        this.timeframe = '1-2 weeks';
        this.fredClient = new FredApiClient();
        this.cacheTTL = config.cacheTTL || 15 * 60 * 1000; // 15 minutes cache
        this.cachePrefix = 'swing_1_2w_';

        // FRED Series IDs for 1-2 week swing trading
        this.fredSeriesIds = {
            // Market Indicators (Daily updates)
            vix: 'VIXCLS',                    // CBOE VIX - Fear gauge
            spx: 'SP500',                      // S&P 500 Index
            dxy: 'DTWEXBGS',                   // USD Dollar Index

            // Short-term Economic Indicators
            treasury10y: 'DGS10',              // 10-Year Treasury Daily
            treasury2y: 'DGS2',                // 2-Year Treasury Daily
            treasury30y: 'DGS30',              // 30-Year Treasury Daily

            // Credit Markets (Daily)
            creditSpread: 'BAMLH0A0HYM2',      // High Yield Credit Spread
            tedSpread: 'TEDRATE',              // TED Spread (Bank Stress)

            // Commodities (Daily)
            gold: 'GOLDAMGBD228NLBM',          // Gold Price London
            oil: 'DCOILWTICO',                 // Crude Oil WTI

            // Volatility Indicators
            move: 'BAMLH0A0HYM2',              // MOVE Index proxy (bond volatility)

            // Economic Activity (Weekly updates)
            initClaims: 'ICSA',                // Initial Jobless Claims (Weekly Thursday)
            contClaims: 'CCSA',                // Continuing Claims (Weekly)
            retailGas: 'GASREGW',              // Gas prices (Weekly Monday)

            // Financial Conditions
            financialStress: 'STLFSI4',        // St. Louis Fed Financial Stress
            chicagoFedIndex: 'CFNAI',          // Chicago Fed National Activity (Monthly)

            // Money Supply (Weekly)
            m2: 'WM2NS',                       // M2 Money Supply (Weekly Monday)

            // Real Estate (Weekly)
            mortgageRate30y: 'MORTGAGE30US'    // 30-Year Mortgage Rate (Weekly Thursday)
        };

        // Yahoo Finance tickers for real-time data
        this.yahooTickers = {
            // Equity Indices
            spx: '^GSPC',                      // S&P 500
            ndx: '^NDX',                       // NASDAQ 100
            dji: '^DJI',                       // Dow Jones
            rut: '^RUT',                       // Russell 2000

            // Volatility
            vix: '^VIX',                       // VIX
            vvix: '^VVIX',                     // VIX of VIX

            // Sector ETFs (Daily rotation tracking)
            xlk: 'XLK',                        // Technology
            xlf: 'XLF',                        // Financials
            xle: 'XLE',                        // Energy
            xlv: 'XLV',                        // Healthcare
            xli: 'XLI',                        // Industrials
            xlp: 'XLP',                        // Consumer Staples
            xly: 'XLY',                        // Consumer Discretionary
            xlu: 'XLU',                        // Utilities
            xlb: 'XLB',                        // Materials
            xlre: 'XLRE',                      // Real Estate

            // Defensive Assets
            tlt: 'TLT',                        // 20+ Year Treasury
            gld: 'GLD',                        // Gold

            // Risk-On Assets
            arkk: 'ARKK',                      // ARK Innovation (risk appetite)
            qqq: 'QQQ',                        // NASDAQ ETF

            // Currency ETFs
            uup: 'UUP',                        // USD Bull
            udn: 'UDN'                         // USD Bear
        };

        // Alpha Vantage for intraday data
        this.alphaVantageKey = 'UEIUKSPCUK1N5432';
        this.alphaVantageBaseUrl = 'https://www.alphavantage.co/query';

        // Local API endpoints (no CORS issues)
        this.localApiBase = 'http://localhost:8888/api';
    }

    /**
     * MASTER FETCH: Get all 1-2 week swing trading data
     * Returns comprehensive dataset for short-term swing analysis
     */
    async fetchAllData() {
        console.log('📊 Fetching 1-2 Week Swing Trading Data...');

        try {
            const [
                dailyFredData,
                weeklyFredData,
                marketData,
                sectorRotation,
                volatilityMetrics,
                economicPulse
            ] = await Promise.all([
                this.fetchDailyFREDData(),
                this.fetchWeeklyFREDData(),
                this.fetchMarketData(),
                this.fetchSectorRotation(),
                this.fetchVolatilityMetrics(),
                this.fetchEconomicPulse()
            ]);

            const dataset = {
                timeframe: this.timeframe,
                timestamp: new Date().toISOString(),
                dataAge: '0-15 minutes',

                // Core datasets
                dailyFred: dailyFredData,
                weeklyFred: weeklyFredData,
                markets: marketData,
                sectors: sectorRotation,
                volatility: volatilityMetrics,
                economic: economicPulse,

                // Derived signals
                signals: this.generateSwingSignals({
                    dailyFredData,
                    weeklyFredData,
                    marketData,
                    sectorRotation,
                    volatilityMetrics
                }),

                // Data quality metadata
                metadata: {
                    sources: ['FRED', 'Yahoo Finance', 'Alpha Vantage'],
                    cached: false,
                    apiCallsMade: 6,
                    nextUpdate: new Date(Date.now() + this.cacheTTL).toISOString()
                }
            };

            // Cache the dataset
            this.setCached('all_data', dataset);

            return {
                success: true,
                data: dataset
            };

        } catch (error) {
            console.error('❌ Failed to fetch 1-2 week data:', error);

            // Try to return cached data
            const cached = this.getCached('all_data');
            if (cached) {
                return {
                    success: true,
                    data: cached,
                    warning: 'Using cached data due to API failure'
                };
            }

            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Fetch Daily FRED Economic Data
     * Last 14 days of daily indicators
     */
    async fetchDailyFREDData() {
        const endDate = this.formatDate(new Date());
        const startDate = this.formatDate(this.getDaysAgo(14));

        const series = [
            this.fredSeriesIds.vix,
            this.fredSeriesIds.treasury10y,
            this.fredSeriesIds.treasury2y,
            this.fredSeriesIds.treasury30y,
            this.fredSeriesIds.creditSpread,
            this.fredSeriesIds.tedSpread,
            this.fredSeriesIds.gold,
            this.fredSeriesIds.oil,
            this.fredSeriesIds.dxy,
            this.fredSeriesIds.financialStress
        ];

        const results = await this.fredClient.fetchMultipleSeries(series, {
            startDate,
            endDate,
            sortOrder: 'desc'
        });

        if (!results.success) {
            throw new Error('Failed to fetch daily FRED data');
        }

        // Transform to usable format
        const data = {};
        Object.entries(results.results).forEach(([seriesId, response]) => {
            if (response.success && response.data.observations) {
                const seriesName = this.getSeriesNameFromId(seriesId);
                data[seriesName] = {
                    values: response.data.observations.filter(o => o.isValid),
                    latest: response.data.observations.find(o => o.isValid)?.value || null,
                    change: this.calculateChange(response.data.observations),
                    trend: this.calculateTrend(response.data.observations)
                };
            }
        });

        return data;
    }

    /**
     * Fetch Weekly FRED Economic Data
     * Last 2 weeks of weekly indicators
     */
    async fetchWeeklyFREDData() {
        const endDate = this.formatDate(new Date());
        const startDate = this.formatDate(this.getDaysAgo(14));

        const series = [
            this.fredSeriesIds.initClaims,
            this.fredSeriesIds.contClaims,
            this.fredSeriesIds.retailGas,
            this.fredSeriesIds.m2,
            this.fredSeriesIds.mortgageRate30y
        ];

        const results = await this.fredClient.fetchMultipleSeries(series, {
            startDate,
            endDate,
            sortOrder: 'desc'
        });

        if (!results.success) {
            throw new Error('Failed to fetch weekly FRED data');
        }

        const data = {};
        Object.entries(results.results).forEach(([seriesId, response]) => {
            if (response.success && response.data.observations) {
                const seriesName = this.getSeriesNameFromId(seriesId);
                data[seriesName] = {
                    values: response.data.observations.filter(o => o.isValid),
                    latest: response.data.observations.find(o => o.isValid)?.value || null,
                    weekOverWeekChange: this.calculateWeekOverWeek(response.data.observations)
                };
            }
        });

        return data;
    }

    /**
     * Fetch Real-Time Market Data
     * Current prices and intraday momentum
     */
    async fetchMarketData() {
        const tickers = Object.values(this.yahooTickers);

        // Use local Yahoo Finance proxy to avoid CORS
        const promises = tickers.map(async (ticker) => {
            try {
                const response = await fetch(`${this.localApiBase}/yahoo/quote?symbols=${ticker}`);
                const data = await response.json();
                return { ticker, data: data.quoteResponse?.result?.[0] || null };
            } catch (error) {
                console.warn(`Failed to fetch ${ticker}:`, error);
                return { ticker, data: null };
            }
        });

        const results = await Promise.all(promises);

        // Transform to keyed object
        const marketData = {};
        results.forEach(({ ticker, data }) => {
            if (data) {
                const name = this.getTickerName(ticker);
                marketData[name] = {
                    symbol: ticker,
                    price: data.regularMarketPrice,
                    change: data.regularMarketChange,
                    changePercent: data.regularMarketChangePercent,
                    volume: data.regularMarketVolume,
                    dayHigh: data.regularMarketDayHigh,
                    dayLow: data.regularMarketDayLow,
                    fiftyDayAvg: data.fiftyDayAverage,
                    twoHundredDayAvg: data.twoHundredDayAverage
                };
            }
        });

        return marketData;
    }

    /**
     * Fetch Sector Rotation Data
     * Daily sector performance for rotation analysis
     */
    async fetchSectorRotation() {
        const sectorTickers = ['XLK', 'XLF', 'XLE', 'XLV', 'XLI', 'XLP', 'XLY', 'XLU', 'XLB', 'XLRE'];

        const sectorData = {};

        for (const ticker of sectorTickers) {
            try {
                const response = await fetch(`${this.localApiBase}/yahoo/quote?symbols=${ticker}`);
                const data = await response.json();
                const quote = data.quoteResponse?.result?.[0];

                if (quote) {
                    sectorData[ticker] = {
                        name: this.getSectorName(ticker),
                        price: quote.regularMarketPrice,
                        change: quote.regularMarketChange,
                        changePercent: quote.regularMarketChangePercent,
                        volume: quote.regularMarketVolume,
                        relativeStrength: this.calculateRelativeStrength(quote)
                    };
                }
            } catch (error) {
                console.warn(`Failed to fetch sector ${ticker}:`, error);
            }
        }

        // Calculate rotation metrics
        const rotation = {
            leaders: this.identifyLeaders(sectorData),
            laggards: this.identifyLaggards(sectorData),
            momentum: this.calculateSectorMomentum(sectorData),
            rawData: sectorData
        };

        return rotation;
    }

    /**
     * Fetch Volatility Metrics
     * VIX, term structure, skew indicators
     */
    async fetchVolatilityMetrics() {
        const vixData = await this.fetchVIXData();
        const termStructure = await this.fetchVIXTermStructure();

        return {
            vix: vixData,
            termStructure,
            regime: this.classifyVolatilityRegime(vixData),
            signal: this.generateVolatilitySignal(vixData, termStructure)
        };
    }

    /**
     * Fetch Economic Pulse
     * Real-time economic sentiment from daily indicators
     */
    async fetchEconomicPulse() {
        // Combine daily FRED data with sentiment analysis
        const pulse = {
            creditConditions: await this.analyzeCreditConditions(),
            financialStress: await this.analyzeFinancialStress(),
            commodityTrends: await this.analyzeCommodityTrends(),
            yieldCurve: await this.analyzeYieldCurve()
        };

        pulse.overallScore = this.calculateEconomicScore(pulse);

        return pulse;
    }

    /**
     * Generate Swing Trading Signals
     * Based on 1-2 week timeframe analysis
     */
    generateSwingSignals(data) {
        const signals = {
            direction: null,      // 'bullish', 'bearish', 'neutral'
            strength: 0,          // 0-100
            confidence: 0,        // 0-100
            factors: [],          // Contributing factors
            recommendations: []   // Specific actions
        };

        let bullishScore = 0;
        let bearishScore = 0;

        // VIX Analysis
        if (data.volatility?.vix?.latest < 15) {
            bullishScore += 10;
            signals.factors.push('Low VIX (complacency)');
        } else if (data.volatility?.vix?.latest > 25) {
            bearishScore += 10;
            signals.factors.push('Elevated VIX (fear)');
        }

        // Sector Rotation
        if (data.sectors?.leaders?.includes('XLK') || data.sectors?.leaders?.includes('XLF')) {
            bullishScore += 15;
            signals.factors.push('Tech/Financial leadership (risk-on)');
        }
        if (data.sectors?.leaders?.includes('XLU') || data.sectors?.leaders?.includes('XLP')) {
            bearishScore += 15;
            signals.factors.push('Defensive sector leadership (risk-off)');
        }

        // Credit Spread Analysis
        if (data.economic?.creditConditions?.widening) {
            bearishScore += 20;
            signals.factors.push('Credit spreads widening (stress)');
        } else {
            bullishScore += 10;
            signals.factors.push('Credit spreads stable');
        }

        // Yield Curve
        if (data.economic?.yieldCurve?.inverted) {
            bearishScore += 25;
            signals.factors.push('Yield curve inversion (recession risk)');
        }

        // Market Breadth
        if (data.markets?.ndx?.changePercent > data.markets?.spx?.changePercent * 1.5) {
            bullishScore += 10;
            signals.factors.push('Tech outperformance (momentum)');
        }

        // Determine direction
        const netScore = bullishScore - bearishScore;
        if (netScore > 20) {
            signals.direction = 'bullish';
            signals.strength = Math.min(bullishScore, 100);
            signals.recommendations.push('Consider long positions in leading sectors');
            signals.recommendations.push('Focus on momentum names (XLK, QQQ)');
        } else if (netScore < -20) {
            signals.direction = 'bearish';
            signals.strength = Math.min(bearishScore, 100);
            signals.recommendations.push('Reduce risk exposure');
            signals.recommendations.push('Rotate to defensive sectors (XLU, XLP)');
            signals.recommendations.push('Consider hedges (VXX, TLT)');
        } else {
            signals.direction = 'neutral';
            signals.strength = 50;
            signals.recommendations.push('Range-bound market - trade support/resistance');
            signals.recommendations.push('Focus on stock selection over direction');
        }

        signals.confidence = Math.min(Math.abs(netScore) * 2, 100);

        return signals;
    }

    // ========== HELPER FUNCTIONS ==========

    getSeriesNameFromId(seriesId) {
        const mapping = Object.entries(this.fredSeriesIds).find(([name, id]) => id === seriesId);
        return mapping ? mapping[0] : seriesId;
    }

    getTickerName(ticker) {
        const mapping = Object.entries(this.yahooTickers).find(([name, t]) => t === ticker);
        return mapping ? mapping[0] : ticker;
    }

    getSectorName(ticker) {
        const names = {
            XLK: 'Technology',
            XLF: 'Financials',
            XLE: 'Energy',
            XLV: 'Healthcare',
            XLI: 'Industrials',
            XLP: 'Consumer Staples',
            XLY: 'Consumer Discretionary',
            XLU: 'Utilities',
            XLB: 'Materials',
            XLRE: 'Real Estate'
        };
        return names[ticker] || ticker;
    }

    calculateChange(observations) {
        if (!observations || observations.length < 2) return null;
        const validObs = observations.filter(o => o.isValid);
        if (validObs.length < 2) return null;

        const latest = validObs[0].value;
        const previous = validObs[1].value;
        return ((latest - previous) / previous * 100).toFixed(2);
    }

    calculateTrend(observations) {
        if (!observations || observations.length < 5) return 'insufficient_data';
        const validObs = observations.filter(o => o.isValid).slice(0, 14);

        if (validObs.length < 5) return 'insufficient_data';

        const recentAvg = validObs.slice(0, 3).reduce((sum, o) => sum + o.value, 0) / 3;
        const olderAvg = validObs.slice(-3).reduce((sum, o) => sum + o.value, 0) / 3;

        const change = ((recentAvg - olderAvg) / olderAvg * 100);

        if (change > 2) return 'rising';
        if (change < -2) return 'falling';
        return 'stable';
    }

    calculateWeekOverWeek(observations) {
        if (!observations || observations.length < 2) return null;
        const validObs = observations.filter(o => o.isValid);
        if (validObs.length < 2) return null;

        const thisWeek = validObs[0].value;
        const lastWeek = validObs[1].value;
        return ((thisWeek - lastWeek) / lastWeek * 100).toFixed(2);
    }

    calculateRelativeStrength(quote) {
        if (!quote.fiftyDayAverage || !quote.twoHundredDayAverage) return 50;

        const priceVs50 = (quote.regularMarketPrice / quote.fiftyDayAverage - 1) * 100;
        const priceVs200 = (quote.regularMarketPrice / quote.twoHundredDayAverage - 1) * 100;

        const score = (priceVs50 * 0.6 + priceVs200 * 0.4);
        return Math.max(0, Math.min(100, 50 + score * 2));
    }

    identifyLeaders(sectorData) {
        return Object.entries(sectorData)
            .sort((a, b) => b[1].relativeStrength - a[1].relativeStrength)
            .slice(0, 3)
            .map(([ticker]) => ticker);
    }

    identifyLaggards(sectorData) {
        return Object.entries(sectorData)
            .sort((a, b) => a[1].relativeStrength - b[1].relativeStrength)
            .slice(0, 3)
            .map(([ticker]) => ticker);
    }

    calculateSectorMomentum(sectorData) {
        const avgChange = Object.values(sectorData)
            .reduce((sum, s) => sum + (s.changePercent || 0), 0) / Object.keys(sectorData).length;

        if (avgChange > 1) return 'strong_positive';
        if (avgChange > 0.25) return 'positive';
        if (avgChange < -1) return 'strong_negative';
        if (avgChange < -0.25) return 'negative';
        return 'neutral';
    }

    async fetchVIXData() {
        const response = await fetch(`${this.localApiBase}/yahoo/quote?symbols=^VIX`);
        const data = await response.json();
        return data.quoteResponse?.result?.[0] || null;
    }

    async fetchVIXTermStructure() {
        // VIX futures term structure (approximated via VIX spot vs VXX)
        const [vix, vxx] = await Promise.all([
            fetch(`${this.localApiBase}/yahoo/quote?symbols=^VIX`).then(r => r.json()),
            fetch(`${this.localApiBase}/yahoo/quote?symbols=VXX`).then(r => r.json())
        ]);

        const vixSpot = vix.quoteResponse?.result?.[0]?.regularMarketPrice || null;
        const vxxPrice = vxx.quoteResponse?.result?.[0]?.regularMarketPrice || null;

        return {
            spot: vixSpot,
            futures: vxxPrice,
            contango: vxxPrice && vixSpot ? vxxPrice > vixSpot : null
        };
    }

    classifyVolatilityRegime(vixData) {
        if (!vixData?.regularMarketPrice) return 'unknown';
        const vix = vixData.regularMarketPrice;

        if (vix < 12) return 'extremely_low';
        if (vix < 15) return 'low';
        if (vix < 20) return 'normal';
        if (vix < 30) return 'elevated';
        return 'high';
    }

    generateVolatilitySignal(vixData, termStructure) {
        const vix = vixData?.regularMarketPrice;
        if (!vix) return 'no_data';

        if (vix > 25 && termStructure.contango === false) {
            return 'extreme_fear_buy_opportunity';
        }
        if (vix < 12) {
            return 'complacency_caution';
        }
        return 'normal';
    }

    async analyzeCreditConditions() {
        const result = await this.fredClient.fetchSeriesObservations(
            this.fredSeriesIds.creditSpread,
            { limit: 14, sortOrder: 'desc' }
        );

        if (!result.success) return { widening: false, level: 'unknown' };

        const obs = result.data.observations.filter(o => o.isValid);
        if (obs.length < 2) return { widening: false, level: 'unknown' };

        const latest = obs[0].value;
        const previous = obs[1].value;

        return {
            latest,
            widening: latest > previous,
            level: latest > 500 ? 'stress' : latest > 300 ? 'caution' : 'normal'
        };
    }

    async analyzeFinancialStress() {
        const result = await this.fredClient.fetchSeriesObservations(
            this.fredSeriesIds.financialStress,
            { limit: 14, sortOrder: 'desc' }
        );

        if (!result.success) return { level: 'unknown' };

        const obs = result.data.observations.filter(o => o.isValid);
        if (obs.length === 0) return { level: 'unknown' };

        const latest = obs[0].value;

        return {
            latest,
            level: latest > 0.5 ? 'high' : latest > 0 ? 'moderate' : latest > -0.5 ? 'low' : 'very_low',
            trend: this.calculateTrend(obs)
        };
    }

    async analyzeCommodityTrends() {
        const [gold, oil] = await Promise.all([
            this.fredClient.fetchSeriesObservations(this.fredSeriesIds.gold, { limit: 14 }),
            this.fredClient.fetchSeriesObservations(this.fredSeriesIds.oil, { limit: 14 })
        ]);

        return {
            gold: {
                trend: gold.success ? this.calculateTrend(gold.data.observations) : 'unknown',
                latest: gold.success ? gold.data.observations.find(o => o.isValid)?.value : null
            },
            oil: {
                trend: oil.success ? this.calculateTrend(oil.data.observations) : 'unknown',
                latest: oil.success ? oil.data.observations.find(o => o.isValid)?.value : null
            }
        };
    }

    async analyzeYieldCurve() {
        const [y2, y10, y30] = await Promise.all([
            this.fredClient.fetchSeriesObservations(this.fredSeriesIds.treasury2y, { limit: 5 }),
            this.fredClient.fetchSeriesObservations(this.fredSeriesIds.treasury10y, { limit: 5 }),
            this.fredClient.fetchSeriesObservations(this.fredSeriesIds.treasury30y, { limit: 5 })
        ]);

        const y2Val = y2.success ? y2.data.observations.find(o => o.isValid)?.value : null;
        const y10Val = y10.success ? y10.data.observations.find(o => o.isValid)?.value : null;
        const y30Val = y30.success ? y30.data.observations.find(o => o.isValid)?.value : null;

        if (!y2Val || !y10Val) return { inverted: false, spread: null };

        const spread = y10Val - y2Val;

        return {
            y2: y2Val,
            y10: y10Val,
            y30: y30Val,
            spread,
            inverted: spread < 0,
            signal: spread < 0 ? 'recession_warning' : spread < 0.25 ? 'flattening' : 'normal'
        };
    }

    calculateEconomicScore(pulse) {
        let score = 50; // Neutral baseline

        if (pulse.creditConditions?.level === 'stress') score -= 20;
        if (pulse.creditConditions?.level === 'caution') score -= 10;

        if (pulse.financialStress?.level === 'high') score -= 15;
        if (pulse.financialStress?.level === 'moderate') score -= 5;
        if (pulse.financialStress?.level === 'low') score += 5;

        if (pulse.yieldCurve?.inverted) score -= 25;
        if (pulse.yieldCurve?.signal === 'flattening') score -= 10;

        if (pulse.commodityTrends?.gold?.trend === 'rising') score -= 5; // Flight to safety
        if (pulse.commodityTrends?.oil?.trend === 'rising') score += 5; // Economic growth

        return Math.max(0, Math.min(100, score));
    }

    formatDate(date) {
        return date.toISOString().split('T')[0];
    }

    getDaysAgo(days) {
        const date = new Date();
        date.setDate(date.getDate() - days);
        return date;
    }

    getCached(key) {
        try {
            const cached = localStorage.getItem(this.cachePrefix + key);
            if (!cached) return null;

            const data = JSON.parse(cached);
            const age = Date.now() - data.timestamp;

            if (age < this.cacheTTL) {
                return data.value;
            }
            return null;
        } catch {
            return null;
        }
    }

    setCached(key, value) {
        try {
            localStorage.setItem(this.cachePrefix + key, JSON.stringify({
                value,
                timestamp: Date.now()
            }));
        } catch (error) {
            console.warn('Cache storage failed:', error);
        }
    }
}

// Export for browser usage
if (typeof window !== 'undefined') {
    window.TimeframeDataFetcher_1_2_Weeks = TimeframeDataFetcher_1_2_Weeks;
}

console.log('✅ 1-2 Week Swing Trading Data Module Loaded');
