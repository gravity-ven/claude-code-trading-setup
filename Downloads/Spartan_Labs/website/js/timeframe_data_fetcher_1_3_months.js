/**
 * SPARTAN LABS - 1-3 MONTH SWING TRADING DATA MODULE
 *
 * INTERMEDIATE SWING TRADING (1-3 Months / 4-12 Weeks)
 * Focus: Weekly trends, momentum, intermediate cycles
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

class TimeframeDataFetcher_1_3_Months {
    constructor(config = {}) {
        this.timeframe = '1-3 months';
        this.fredClient = new FredApiClient();
        this.cacheTTL = config.cacheTTL || 60 * 60 * 1000; // 1 hour cache
        this.cachePrefix = 'swing_1_3m_';

        // FRED Series IDs for 1-3 month swing trading
        this.fredSeriesIds = {
            // Market Indices (Weekly/Monthly)
            spx: 'SP500',                      // S&P 500
            wilshire5000: 'WILL5000INDFC',     // Wilshire 5000 (Total Market)

            // Volatility (Weekly)
            vix: 'VIXCLS',                     // VIX Daily

            // Economic Indicators (Monthly)
            unemployment: 'UNRATE',            // Unemployment Rate (Monthly, 1st Friday)
            cpi: 'CPIAUCSL',                   // CPI All Urban (Monthly, ~13th)
            pce: 'PCEPI',                      // PCE Price Index (Monthly, ~last Friday)
            retailSales: 'RSXFS',              // Retail Sales (Monthly, ~13-16th)
            industrialProd: 'INDPRO',          // Industrial Production (Monthly, ~15th)
            capacity: 'TCU',                   // Capacity Utilization (Monthly, ~15th)
            housing: 'HOUST',                  // Housing Starts (Monthly, ~16-19th)
            buildingPermits: 'PERMIT',         // Building Permits (Monthly, ~16-19th)

            // Labor Market (Monthly)
            nonfarmPayrolls: 'PAYEMS',         // Nonfarm Payrolls (Monthly, 1st Friday)
            avgWeeklyHours: 'AWHAETP',         // Avg Weekly Hours (Monthly, 1st Friday)
            avgHourlyEarnings: 'CES0500000003', // Avg Hourly Earnings (Monthly, 1st Friday)
            laborParticipation: 'CIVPART',     // Labor Force Participation (Monthly)

            // Manufacturing (Monthly)
            pmi: 'MANEMP',                     // Manufacturing Employment proxy
            newOrders: 'NEWORDER',             // Manufacturers' New Orders (Monthly)
            durableGoods: 'DGORDER',           // Durable Goods Orders (Monthly, ~26th)

            // Consumer Confidence (Monthly)
            consumerSentiment: 'UMCSENT',      // U. Michigan Consumer Sentiment
            consumerExpectations: 'UMCSENT',   // Consumer Expectations

            // Credit & Lending (Monthly)
            consumerCredit: 'TOTALSL',         // Total Consumer Credit (Monthly, ~5th)
            bankCredit: 'TOTBKCR',             // Bank Credit (Weekly Wed)

            // Treasury Yields (Weekly aggregates)
            treasury10y: 'DGS10',              // 10-Year Treasury
            treasury2y: 'DGS2',                // 2-Year Treasury
            treasury30y: 'DGS30',              // 30-Year Treasury

            // Credit Markets (Weekly)
            creditSpread: 'BAMLH0A0HYM2',      // High Yield Spread
            aaaSpread: 'BAMLC0A0CM',           // AAA Corporate Spread

            // Money Supply (Weekly/Monthly)
            m2: 'WM2NS',                       // M2 Money Supply (Weekly)
            m1: 'WM1NS',                       // M1 Money Supply (Weekly)

            // Financial Conditions (Weekly)
            financialStress: 'STLFSI4',        // St. Louis Fed Financial Stress
            chicagoFed: 'CFNAI',               // Chicago Fed National Activity

            // Real Estate (Monthly)
            mortgageRate: 'MORTGAGE30US',      // 30-Year Mortgage (Weekly)
            housePrices: 'CSUSHPISA',          // Case-Shiller Home Price (Monthly)

            // Commodities (Weekly)
            gold: 'GOLDAMGBD228NLBM',          // Gold London
            oil: 'DCOILWTICO',                 // WTI Crude
            copper: 'PCOPPUSDM',               // Copper Price

            // Currency (Weekly)
            dxy: 'DTWEXBGS',                   // USD Dollar Index

            // Leading Indicators (Monthly)
            leadingIndex: 'USSLIND'            // Leading Economic Index
        };

        // Yahoo Finance tickers for weekly data
        this.yahooTickers = {
            // Major Indices
            spx: '^GSPC',
            ndx: '^NDX',
            dji: '^DJI',
            rut: '^RUT',

            // Volatility
            vix: '^VIX',

            // Sector ETFs
            xlk: 'XLK',
            xlf: 'XLF',
            xle: 'XLE',
            xlv: 'XLV',
            xli: 'XLI',
            xlp: 'XLP',
            xly: 'XLY',
            xlu: 'XLU',
            xlb: 'XLB',
            xlre: 'XLRE',
            xlc: 'XLC',       // Communication Services

            // Style ETFs
            iwf: 'IWF',       // Russell 1000 Growth
            iwb: 'IWB',       // Russell 1000 Value
            iwm: 'IWM',       // Russell 2000 Small Cap

            // International
            efa: 'EFA',       // MSCI EAFE
            eem: 'EEM',       // Emerging Markets
            fxi: 'FXI',       // China Large Cap

            // Fixed Income
            tlt: 'TLT',       // 20+ Year Treasury
            ief: 'IEF',       // 7-10 Year Treasury
            shy: 'SHY',       // 1-3 Year Treasury
            lqd: 'LQD',       // Investment Grade Corp
            hyg: 'HYG',       // High Yield Corp

            // Commodities
            gld: 'GLD',       // Gold
            slv: 'SLV',       // Silver
            uso: 'USO',       // Oil
            dba: 'DBA',       // Agriculture

            // Currency
            uup: 'UUP',       // USD Bull
            fxe: 'FXE',       // Euro
            fxb: 'FXB',       // British Pound
            fxy: 'FXY'        // Japanese Yen
        };

        this.localApiBase = 'http://localhost:8888/api';
    }

    /**
     * MASTER FETCH: Get all 1-3 month swing trading data
     */
    async fetchAllData() {
        console.log('📊 Fetching 1-3 Month Swing Trading Data...');

        try {
            const [
                monthlyEconomic,
                weeklyMarkets,
                sectorTrends,
                fixedIncome,
                commodities,
                internationalMarkets,
                momentumIndicators
            ] = await Promise.all([
                this.fetchMonthlyEconomicData(),
                this.fetchWeeklyMarketData(),
                this.fetchSectorTrends(),
                this.fetchFixedIncomeData(),
                this.fetchCommodityData(),
                this.fetchInternationalData(),
                this.fetchMomentumIndicators()
            ]);

            const dataset = {
                timeframe: this.timeframe,
                timestamp: new Date().toISOString(),
                dataAge: '0-60 minutes',

                economic: monthlyEconomic,
                markets: weeklyMarkets,
                sectors: sectorTrends,
                fixedIncome,
                commodities,
                international: internationalMarkets,
                momentum: momentumIndicators,

                // Derived analysis
                analysis: this.generateIntermediateAnalysis({
                    monthlyEconomic,
                    weeklyMarkets,
                    sectorTrends,
                    fixedIncome,
                    commodities
                }),

                metadata: {
                    sources: ['FRED', 'Yahoo Finance'],
                    lookbackPeriod: '90 days',
                    updateFrequency: '1 hour'
                }
            };

            this.setCached('all_data', dataset);

            return {
                success: true,
                data: dataset
            };

        } catch (error) {
            console.error('❌ Failed to fetch 1-3 month data:', error);

            const cached = this.getCached('all_data');
            if (cached) {
                return {
                    success: true,
                    data: cached,
                    warning: 'Using cached data'
                };
            }

            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Fetch Monthly Economic Data
     * Last 3 months of key economic indicators
     */
    async fetchMonthlyEconomicData() {
        const endDate = this.formatDate(new Date());
        const startDate = this.formatDate(this.getMonthsAgo(3));

        const series = [
            this.fredSeriesIds.unemployment,
            this.fredSeriesIds.cpi,
            this.fredSeriesIds.pce,
            this.fredSeriesIds.retailSales,
            this.fredSeriesIds.industrialProd,
            this.fredSeriesIds.capacity,
            this.fredSeriesIds.housing,
            this.fredSeriesIds.buildingPermits,
            this.fredSeriesIds.nonfarmPayrolls,
            this.fredSeriesIds.consumerSentiment,
            this.fredSeriesIds.consumerCredit,
            this.fredSeriesIds.durableGoods,
            this.fredSeriesIds.leadingIndex
        ];

        const results = await this.fredClient.fetchMultipleSeries(series, {
            startDate,
            endDate,
            sortOrder: 'desc'
        });

        const data = {};
        Object.entries(results.results).forEach(([seriesId, response]) => {
            if (response.success && response.data.observations) {
                const name = this.getSeriesName(seriesId);
                const obs = response.data.observations.filter(o => o.isValid);

                data[name] = {
                    latest: obs[0]?.value || null,
                    previous: obs[1]?.value || null,
                    threeMonthChange: this.calculatePercentChange(obs, 0, 2),
                    trend: this.calculateTrend(obs),
                    values: obs.slice(0, 3)
                };
            }
        });

        return data;
    }

    /**
     * Fetch Weekly Market Data
     * Last 12 weeks of market performance
     */
    async fetchWeeklyMarketData() {
        const markets = {};

        // Fetch weekly data for major indices
        const indices = ['SPX', 'NDX', 'DJI', 'RUT'];

        for (const index of indices) {
            const ticker = this.yahooTickers[index.toLowerCase()];
            const data = await this.fetchYahooWeeklyData(ticker);
            if (data) {
                markets[index] = {
                    current: data.current,
                    weeklyChange: data.weeklyChange,
                    fourWeekChange: data.fourWeekChange,
                    twelveWeekChange: data.twelveWeekChange,
                    trend: this.classifyTrend(data.twelveWeekChange)
                };
            }
        }

        return markets;
    }

    /**
     * Fetch Sector Trends
     * 12-week sector rotation analysis
     */
    async fetchSectorTrends() {
        const sectors = ['XLK', 'XLF', 'XLE', 'XLV', 'XLI', 'XLP', 'XLY', 'XLU', 'XLB', 'XLRE', 'XLC'];
        const sectorData = {};

        for (const ticker of sectors) {
            const data = await this.fetchYahooWeeklyData(ticker);
            if (data) {
                sectorData[ticker] = {
                    name: this.getSectorName(ticker),
                    current: data.current,
                    weeklyChange: data.weeklyChange,
                    monthlyChange: data.fourWeekChange,
                    quarterlyChange: data.twelveWeekChange,
                    relativeStrength: this.calculateRelativeStrength(data),
                    momentum: this.calculateMomentum(data)
                };
            }
        }

        return {
            sectors: sectorData,
            leaders: this.identifyLeaders(sectorData, 3),
            laggards: this.identifyLaggards(sectorData, 3),
            rotation: this.analyzeRotation(sectorData)
        };
    }

    /**
     * Fetch Fixed Income Data
     * Yield curve and credit analysis
     */
    async fetchFixedIncomeData() {
        const endDate = this.formatDate(new Date());
        const startDate = this.formatDate(this.getMonthsAgo(3));

        const [y2, y10, y30, creditSpread, aaaSpread] = await Promise.all([
            this.fredClient.fetchSeriesObservations(this.fredSeriesIds.treasury2y, { startDate, endDate }),
            this.fredClient.fetchSeriesObservations(this.fredSeriesIds.treasury10y, { startDate, endDate }),
            this.fredClient.fetchSeriesObservations(this.fredSeriesIds.treasury30y, { startDate, endDate }),
            this.fredClient.fetchSeriesObservations(this.fredSeriesIds.creditSpread, { startDate, endDate }),
            this.fredClient.fetchSeriesObservations(this.fredSeriesIds.aaaSpread, { startDate, endDate })
        ]);

        const y2Obs = y2.success ? y2.data.observations.filter(o => o.isValid) : [];
        const y10Obs = y10.success ? y10.data.observations.filter(o => o.isValid) : [];
        const y30Obs = y30.success ? y30.data.observations.filter(o => o.isValid) : [];
        const hyObs = creditSpread.success ? creditSpread.data.observations.filter(o => o.isValid) : [];
        const aaaObs = aaaSpread.success ? aaaSpread.data.observations.filter(o => o.isValid) : [];

        return {
            yieldCurve: {
                y2: y2Obs[0]?.value || null,
                y10: y10Obs[0]?.value || null,
                y30: y30Obs[0]?.value || null,
                spread_2_10: y10Obs[0] && y2Obs[0] ? (y10Obs[0].value - y2Obs[0].value).toFixed(2) : null,
                inverted: y10Obs[0] && y2Obs[0] ? y10Obs[0].value < y2Obs[0].value : false,
                trend: this.calculateTrend(y10Obs)
            },
            credit: {
                highYieldSpread: hyObs[0]?.value || null,
                aaaSpread: aaaObs[0]?.value || null,
                hyTrend: this.calculateTrend(hyObs),
                condition: this.assessCreditCondition(hyObs[0]?.value)
            }
        };
    }

    /**
     * Fetch Commodity Data
     * 12-week commodity trends
     */
    async fetchCommodityData() {
        const endDate = this.formatDate(new Date());
        const startDate = this.formatDate(this.getMonthsAgo(3));

        const [gold, oil, copper] = await Promise.all([
            this.fredClient.fetchSeriesObservations(this.fredSeriesIds.gold, { startDate, endDate }),
            this.fredClient.fetchSeriesObservations(this.fredSeriesIds.oil, { startDate, endDate }),
            this.fredClient.fetchSeriesObservations(this.fredSeriesIds.copper, { startDate, endDate })
        ]);

        return {
            gold: this.processCommodityData(gold, 'Gold'),
            oil: this.processCommodityData(oil, 'Oil'),
            copper: this.processCommodityData(copper, 'Copper')
        };
    }

    /**
     * Fetch International Market Data
     */
    async fetchInternationalData() {
        const tickers = {
            developed: ['EFA'],
            emerging: ['EEM'],
            china: ['FXI']
        };

        const data = {};
        for (const [region, symbols] of Object.entries(tickers)) {
            for (const symbol of symbols) {
                const tickerData = await this.fetchYahooWeeklyData(symbol);
                if (tickerData) {
                    data[region] = {
                        symbol,
                        current: tickerData.current,
                        monthlyChange: tickerData.fourWeekChange,
                        quarterlyChange: tickerData.twelveWeekChange,
                        trend: this.classifyTrend(tickerData.twelveWeekChange)
                    };
                }
            }
        }

        return data;
    }

    /**
     * Fetch Momentum Indicators
     * Breadth, volume, and momentum metrics
     */
    async fetchMomentumIndicators() {
        // Fetch advance/decline data proxy using style ETFs
        const [growth, value, smallCap] = await Promise.all([
            this.fetchYahooWeeklyData('IWF'),
            this.fetchYahooWeeklyData('IWB'),
            this.fetchYahooWeeklyData('IWM')
        ]);

        return {
            growthVsValue: growth && value ? {
                spread: growth.weeklyChange - value.weeklyChange,
                leadership: growth.weeklyChange > value.weeklyChange ? 'growth' : 'value'
            } : null,
            smallCapStrength: smallCap ? {
                change: smallCap.twelveWeekChange,
                trend: this.classifyTrend(smallCap.twelveWeekChange),
                riskAppetite: smallCap.twelveWeekChange > 0 ? 'high' : 'low'
            } : null
        };
    }

    /**
     * Generate Intermediate Analysis
     * Comprehensive 1-3 month outlook
     */
    generateIntermediateAnalysis(data) {
        const analysis = {
            economicCycle: this.assessEconomicCycle(data.monthlyEconomic),
            marketTrend: this.assessMarketTrend(data.weeklyMarkets),
            sectorRotation: this.assessSectorRotation(data.sectorTrends),
            riskAppetite: this.assessRiskAppetite(data),
            recommendations: []
        };

        // Generate recommendations
        if (analysis.economicCycle === 'expansion' && analysis.marketTrend === 'bullish') {
            analysis.recommendations.push('Stay long cyclical sectors (XLI, XLF)');
            analysis.recommendations.push('Favor growth over value');
        } else if (analysis.economicCycle === 'contraction') {
            analysis.recommendations.push('Rotate to defensive sectors (XLP, XLU)');
            analysis.recommendations.push('Consider hedges (TLT, GLD)');
        }

        if (data.fixedIncome?.yieldCurve?.inverted) {
            analysis.recommendations.push('⚠️ Yield curve inversion - reduce risk exposure');
        }

        if (analysis.riskAppetite === 'low') {
            analysis.recommendations.push('Defensive positioning recommended');
        } else if (analysis.riskAppetite === 'high') {
            analysis.recommendations.push('Risk-on environment - consider growth names');
        }

        return analysis;
    }

    // ========== HELPER FUNCTIONS ==========

    async fetchYahooWeeklyData(ticker) {
        try {
            // Fetch daily data for last 90 days, aggregate to weekly
            const response = await fetch(`${this.localApiBase}/yahoo/chart/${ticker}?interval=1d&range=3mo`);
            const data = await response.json();

            if (!data?.chart?.result?.[0]) return null;

            const prices = data.chart.result[0].indicators.quote[0].close;
            const timestamps = data.chart.result[0].timestamp;

            if (!prices || prices.length < 60) return null;

            const current = prices[prices.length - 1];
            const oneWeekAgo = prices[prices.length - 6] || prices[prices.length - 1];
            const fourWeeksAgo = prices[prices.length - 23] || prices[prices.length - 1];
            const twelveWeeksAgo = prices[prices.length - 61] || prices[0];

            return {
                current,
                weeklyChange: ((current - oneWeekAgo) / oneWeekAgo * 100).toFixed(2),
                fourWeekChange: ((current - fourWeeksAgo) / fourWeeksAgo * 100).toFixed(2),
                twelveWeekChange: ((current - twelveWeeksAgo) / twelveWeeksAgo * 100).toFixed(2)
            };
        } catch (error) {
            console.warn(`Failed to fetch weekly data for ${ticker}:`, error);
            return null;
        }
    }

    processCommodityData(response, name) {
        if (!response.success) return { name, trend: 'unknown', latest: null };

        const obs = response.data.observations.filter(o => o.isValid);
        return {
            name,
            latest: obs[0]?.value || null,
            monthChange: this.calculatePercentChange(obs, 0, 20),
            quarterChange: this.calculatePercentChange(obs, 0, 60),
            trend: this.calculateTrend(obs)
        };
    }

    assessEconomicCycle(economic) {
        let score = 0;

        if (economic.unemployment?.trend === 'falling') score += 10;
        if (economic.unemployment?.trend === 'rising') score -= 10;

        if (economic.retailSales?.trend === 'rising') score += 10;
        if (economic.industrialProd?.trend === 'rising') score += 10;

        if (economic.leadingIndex?.trend === 'rising') score += 15;
        if (economic.leadingIndex?.trend === 'falling') score -= 15;

        if (score > 20) return 'expansion';
        if (score < -20) return 'contraction';
        return 'neutral';
    }

    assessMarketTrend(markets) {
        if (!markets.SPX) return 'neutral';

        const spxChange = parseFloat(markets.SPX.twelveWeekChange);
        if (spxChange > 10) return 'strong_bullish';
        if (spxChange > 3) return 'bullish';
        if (spxChange < -10) return 'strong_bearish';
        if (spxChange < -3) return 'bearish';
        return 'neutral';
    }

    assessSectorRotation(sectors) {
        const leaders = sectors.leaders || [];
        const cyclicals = ['XLI', 'XLF', 'XLE', 'XLB'];
        const defensives = ['XLP', 'XLU', 'XLV'];

        const cyclicalLeadership = leaders.filter(l => cyclicals.includes(l)).length;
        const defensiveLeadership = leaders.filter(l => defensives.includes(l)).length;

        if (cyclicalLeadership > defensiveLeadership) return 'risk_on';
        if (defensiveLeadership > cyclicalLeadership) return 'risk_off';
        return 'neutral';
    }

    assessRiskAppetite(data) {
        let score = 0;

        if (data.sectorTrends?.rotation === 'risk_on') score += 20;
        if (data.sectorTrends?.rotation === 'risk_off') score -= 20;

        if (data.fixedIncome?.credit?.condition === 'stressed') score -= 30;
        if (data.fixedIncome?.yieldCurve?.inverted) score -= 25;

        if (data.commodities?.copper?.trend === 'rising') score += 10;

        if (score > 20) return 'high';
        if (score < -20) return 'low';
        return 'moderate';
    }

    assessCreditCondition(hySpread) {
        if (!hySpread) return 'unknown';
        if (hySpread > 600) return 'stressed';
        if (hySpread > 400) return 'cautious';
        if (hySpread > 250) return 'normal';
        return 'tight';
    }

    calculatePercentChange(observations, startIdx, endIdx) {
        if (!observations || observations.length <= Math.max(startIdx, endIdx)) return null;
        const start = observations[startIdx]?.value;
        const end = observations[endIdx]?.value;
        if (!start || !end) return null;
        return ((start - end) / end * 100).toFixed(2);
    }

    calculateTrend(observations) {
        if (!observations || observations.length < 3) return 'unknown';
        const validObs = observations.filter(o => o.isValid).slice(0, 10);

        if (validObs.length < 3) return 'unknown';

        const recent = validObs.slice(0, 3).reduce((sum, o) => sum + o.value, 0) / 3;
        const older = validObs.slice(-3).reduce((sum, o) => sum + o.value, 0) / 3;

        const change = ((recent - older) / older * 100);

        if (change > 2) return 'rising';
        if (change < -2) return 'falling';
        return 'stable';
    }

    classifyTrend(changePercent) {
        const change = parseFloat(changePercent);
        if (change > 10) return 'strong_up';
        if (change > 3) return 'up';
        if (change < -10) return 'strong_down';
        if (change < -3) return 'down';
        return 'neutral';
    }

    calculateRelativeStrength(data) {
        const monthlyChange = parseFloat(data.fourWeekChange);
        const quarterlyChange = parseFloat(data.twelveWeekChange);

        return ((monthlyChange * 0.6 + quarterlyChange * 0.4) / 2 + 50);
    }

    calculateMomentum(data) {
        const weekly = parseFloat(data.weeklyChange);
        const monthly = parseFloat(data.monthlyChange);
        const quarterly = parseFloat(data.quarterlyChange);

        const score = (weekly * 0.2 + monthly * 0.3 + quarterly * 0.5);

        if (score > 5) return 'strong_positive';
        if (score > 2) return 'positive';
        if (score < -5) return 'strong_negative';
        if (score < -2) return 'negative';
        return 'neutral';
    }

    identifyLeaders(sectorData, count = 3) {
        return Object.entries(sectorData)
            .filter(([_, data]) => data.relativeStrength !== undefined)
            .sort((a, b) => b[1].relativeStrength - a[1].relativeStrength)
            .slice(0, count)
            .map(([ticker]) => ticker);
    }

    identifyLaggards(sectorData, count = 3) {
        return Object.entries(sectorData)
            .filter(([_, data]) => data.relativeStrength !== undefined)
            .sort((a, b) => a[1].relativeStrength - b[1].relativeStrength)
            .slice(0, count)
            .map(([ticker]) => ticker);
    }

    analyzeRotation(sectorData) {
        const cyclicals = ['XLI', 'XLF', 'XLE', 'XLB', 'XLY'];
        const defensives = ['XLP', 'XLU', 'XLV'];
        const growth = ['XLK', 'XLC'];

        const cyclicalPerf = cyclicals.reduce((sum, t) => sum + (parseFloat(sectorData[t]?.monthlyChange) || 0), 0) / cyclicals.length;
        const defensivePerf = defensives.reduce((sum, t) => sum + (parseFloat(sectorData[t]?.monthlyChange) || 0), 0) / defensives.length;
        const growthPerf = growth.reduce((sum, t) => sum + (parseFloat(sectorData[t]?.monthlyChange) || 0), 0) / growth.length;

        if (cyclicalPerf > defensivePerf && cyclicalPerf > growthPerf) return 'cyclical_rotation';
        if (defensivePerf > cyclicalPerf) return 'defensive_rotation';
        if (growthPerf > cyclicalPerf && growthPerf > defensivePerf) return 'growth_rotation';
        return 'mixed';
    }

    getSectorName(ticker) {
        const names = {
            XLK: 'Technology', XLF: 'Financials', XLE: 'Energy',
            XLV: 'Healthcare', XLI: 'Industrials', XLP: 'Consumer Staples',
            XLY: 'Consumer Discretionary', XLU: 'Utilities', XLB: 'Materials',
            XLRE: 'Real Estate', XLC: 'Communication Services'
        };
        return names[ticker] || ticker;
    }

    getSeriesName(seriesId) {
        const mapping = Object.entries(this.fredSeriesIds).find(([_, id]) => id === seriesId);
        return mapping ? mapping[0] : seriesId;
    }

    formatDate(date) {
        return date.toISOString().split('T')[0];
    }

    getMonthsAgo(months) {
        const date = new Date();
        date.setMonth(date.getMonth() - months);
        return date;
    }

    getCached(key) {
        try {
            const cached = localStorage.getItem(this.cachePrefix + key);
            if (!cached) return null;

            const data = JSON.parse(cached);
            if (Date.now() - data.timestamp < this.cacheTTL) {
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
    window.TimeframeDataFetcher_1_3_Months = TimeframeDataFetcher_1_3_Months;
}

console.log('✅ 1-3 Month Swing Trading Data Module Loaded');
