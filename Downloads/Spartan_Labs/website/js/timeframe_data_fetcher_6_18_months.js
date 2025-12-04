/**
 * SPARTAN LABS - 6-18 MONTH POSITION TRADING DATA MODULE
 *
 * LONG-TERM SWING/POSITION TRADING (6-18 Months)
 * Focus: Macro trends, quarterly earnings, structural shifts
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

class TimeframeDataFetcher_6_18_Months {
    constructor(config = {}) {
        this.timeframe = '6-18 months';
        this.fredClient = new FredApiClient();
        this.cacheTTL = config.cacheTTL || 4 * 60 * 60 * 1000; // 4 hours cache
        this.cachePrefix = 'position_6_18m_';

        // FRED Series IDs for 6-18 month position trading
        this.fredSeriesIds = {
            // GDP & Growth (Quarterly)
            gdp: 'GDP',                        // Real GDP (Quarterly)
            gdpGrowth: 'A191RL1Q225SBEA',      // Real GDP Growth Rate
            gdpPerCapita: 'A939RX0Q048SBEA',   // Real GDP Per Capita

            // Employment & Labor (Monthly aggregates)
            unemployment: 'UNRATE',            // Unemployment Rate
            nonfarmPayrolls: 'PAYEMS',         // Nonfarm Payrolls
            laborParticipation: 'CIVPART',     // Labor Force Participation
            employmentPopRatio: 'EMRATIO',     // Employment-Population Ratio
            avgWeeklyHours: 'AWHAETP',         // Average Weekly Hours
            partTimeEcon: 'LNS12032194',       // Part-Time for Economic Reasons

            // Inflation (Monthly)
            cpi: 'CPIAUCSL',                   // CPI All Urban
            cpiCore: 'CPILFESL',               // Core CPI (ex food & energy)
            pce: 'PCEPI',                      // PCE Price Index
            pceCore: 'PCEPILFE',               // Core PCE (Fed's preferred)
            ppi: 'PPIACO',                     // Producer Price Index

            // Manufacturing & Industry (Monthly)
            industrialProd: 'INDPRO',          // Industrial Production Index
            capacity: 'TCU',                   // Capacity Utilization
            pmi: 'MANEMP',                     // Manufacturing Employment proxy
            newOrders: 'NEWORDER',             // New Orders
            durableGoods: 'DGORDER',           // Durable Goods Orders
            vehicleSales: 'TOTALSA',           // Total Vehicle Sales

            // Consumer (Monthly)
            retailSales: 'RSXFS',              // Advance Retail Sales
            personalIncome: 'PI',              // Personal Income
            personalSpending: 'PCE',           // Personal Consumption Expenditures
            disposableIncome: 'DSPI',          // Disposable Personal Income
            consumerSentiment: 'UMCSENT',      // Michigan Consumer Sentiment
            savingsRate: 'PSAVERT',            // Personal Saving Rate

            // Housing (Monthly)
            housing: 'HOUST',                  // Housing Starts
            buildingPermits: 'PERMIT',         // Building Permits
            existingHomeSales: 'EXHOSLUSM495S', // Existing Home Sales
            newHomeSales: 'HSN1F',             // New Home Sales
            housePrices: 'CSUSHPISA',          // Case-Shiller Home Price Index
            mortgageRate: 'MORTGAGE30US',      // 30-Year Mortgage Rate

            // Credit & Money (Monthly/Weekly)
            consumerCredit: 'TOTALSL',         // Total Consumer Credit
            bankCredit: 'TOTBKCR',             // Bank Credit
            m2: 'M2SL',                        // M2 Money Supply (Monthly)
            m1: 'M1SL',                        // M1 Money Supply (Monthly)
            commercialLoans: 'TOTLL',          // Total Loans & Leases

            // Federal Reserve (Monthly)
            fedFunds: 'FEDFUNDS',              // Federal Funds Rate
            totalAssets: 'WALCL',              // Fed Total Assets
            monetaryBase: 'BOGMBASE',          // Monetary Base

            // Treasury & Yields (Daily aggregates)
            treasury10y: 'DGS10',              // 10-Year Treasury
            treasury2y: 'DGS2',                // 2-Year Treasury
            treasury30y: 'DGS30',              // 30-Year Treasury
            treasury5y: 'DGS5',                // 5-Year Treasury

            // Credit Markets (Daily aggregates)
            aaaSpread: 'BAMLC0A0CM',           // AAA Corporate Spread
            baaSpread: 'BAMLC0A4CBBB',         // BBB Corporate Spread
            highYieldSpread: 'BAMLH0A0HYM2',   // High Yield Spread

            // Commodities (Monthly aggregates)
            gold: 'GOLDAMGBD228NLBM',          // Gold Price
            oil: 'DCOILWTICO',                 // WTI Crude Oil
            copper: 'PCOPPUSDM',               // Copper Price
            crudOilStocks: 'WCSSTUS1',         // US Crude Oil Stocks

            // Currency (Daily aggregates)
            dxy: 'DTWEXBGS',                   // Dollar Index

            // Leading Indicators (Monthly)
            leadingIndex: 'USSLIND',           // Leading Economic Index
            chicagoFed: 'CFNAI',               // Chicago Fed National Activity
            financialStress: 'STLFSI4',        // St. Louis Fed Financial Stress

            // Corporate Profits (Quarterly)
            corporateProfits: 'CP',            // Corporate Profits

            // Trade (Monthly)
            tradeBalance: 'BOPGSTB',           // Trade Balance
            imports: 'IMPGS',                  // Imports of Goods & Services
            exports: 'EXPGS'                   // Exports of Goods & Services
        };

        // Yahoo Finance for long-term market data
        this.yahooTickers = {
            // Major Indices
            spx: '^GSPC', ndx: '^NDX', dji: '^DJI', rut: '^RUT',

            // Sectors
            xlk: 'XLK', xlf: 'XLF', xle: 'XLE', xlv: 'XLV',
            xli: 'XLI', xlp: 'XLP', xly: 'XLY', xlu: 'XLU',
            xlb: 'XLB', xlre: 'XLRE', xlc: 'XLC',

            // International
            efa: 'EFA',   // Developed Markets
            eem: 'EEM',   // Emerging Markets
            fxi: 'FXI',   // China
            ewj: 'EWJ',   // Japan
            ewz: 'EWZ',   // Brazil
            ezu: 'EZU',   // Eurozone

            // Fixed Income
            tlt: 'TLT', ief: 'IEF', shy: 'SHY',
            lqd: 'LQD', hyg: 'HYG', emb: 'EMB',

            // Commodities
            gld: 'GLD', slv: 'SLV', uso: 'USO', dba: 'DBA'
        };

        this.localApiBase = 'http://localhost:8888/api';
    }

    /**
     * MASTER FETCH: Get all 6-18 month position trading data
     */
    async fetchAllData() {
        console.log('📊 Fetching 6-18 Month Position Trading Data...');

        try {
            const [
                macroeconomic,
                marketLongTerm,
                sectorAllocation,
                valuationMetrics,
                globalMacro
            ] = await Promise.all([
                this.fetchMacroeconomicData(),
                this.fetchLongTermMarketData(),
                this.fetchSectorAllocationData(),
                this.fetchValuationMetrics(),
                this.fetchGlobalMacroData()
            ]);

            const dataset = {
                timeframe: this.timeframe,
                timestamp: new Date().toISOString(),
                lookbackPeriod: '18 months',

                macro: macroeconomic,
                markets: marketLongTerm,
                sectors: sectorAllocation,
                valuations: valuationMetrics,
                global: globalMacro,

                // Strategic analysis
                analysis: this.generateStrategicAnalysis({
                    macroeconomic,
                    marketLongTerm,
                    sectorAllocation,
                    valuationMetrics
                }),

                metadata: {
                    sources: ['FRED', 'Yahoo Finance'],
                    updateFrequency: '4 hours',
                    dataQuality: 'high'
                }
            };

            this.setCached('all_data', dataset);

            return { success: true, data: dataset };

        } catch (error) {
            console.error('❌ Failed to fetch 6-18 month data:', error);

            const cached = this.getCached('all_data');
            if (cached) {
                return { success: true, data: cached, warning: 'Using cached data' };
            }

            return { success: false, error: error.message };
        }
    }

    /**
     * Fetch Macroeconomic Data
     * Last 18 months of key economic indicators
     */
    async fetchMacroeconomicData() {
        const endDate = this.formatDate(new Date());
        const startDate = this.formatDate(this.getMonthsAgo(18));

        const quarterlySeries = [
            this.fredSeriesIds.gdp,
            this.fredSeriesIds.gdpGrowth,
            this.fredSeriesIds.corporateProfits
        ];

        const monthlySeries = [
            this.fredSeriesIds.unemployment,
            this.fredSeriesIds.cpi,
            this.fredSeriesIds.pceCore,
            this.fredSeriesIds.industrialProd,
            this.fredSeriesIds.retailSales,
            this.fredSeriesIds.housing,
            this.fredSeriesIds.leadingIndex
        ];

        const [quarterly, monthly] = await Promise.all([
            this.fredClient.fetchMultipleSeries(quarterlySeries, { startDate, endDate }),
            this.fredClient.fetchMultipleSeries(monthlySeries, { startDate, endDate })
        ]);

        const data = {
            growth: this.processQuarterlyData(quarterly.results, 'gdp'),
            inflation: this.processMonthlyData(monthly.results, 'pceCore'),
            employment: this.processMonthlyData(monthly.results, 'unemployment'),
            manufacturing: this.processMonthlyData(monthly.results, 'industrialProd'),
            consumer: this.processMonthlyData(monthly.results, 'retailSales'),
            housing: this.processMonthlyData(monthly.results, 'housing'),
            leading: this.processMonthlyData(monthly.results, 'leadingIndex')
        };

        return data;
    }

    /**
     * Fetch Long-Term Market Data
     * 18-month performance and trends
     */
    async fetchLongTermMarketData() {
        const indices = ['SPX', 'NDX', 'DJI', 'RUT'];
        const markets = {};

        for (const index of indices) {
            const ticker = this.yahooTickers[index.toLowerCase()];
            const data = await this.fetchYahooLongTermData(ticker);

            if (data) {
                markets[index] = {
                    current: data.current,
                    sixMonthReturn: data.sixMonthReturn,
                    twelveMonthReturn: data.twelveMonthReturn,
                    eighteenMonthReturn: data.eighteenMonthReturn,
                    volatility: data.volatility,
                    trend: this.classifyLongTermTrend(data.eighteenMonthReturn),
                    momentum: this.calculateMomentumScore(data)
                };
            }
        }

        return markets;
    }

    /**
     * Fetch Sector Allocation Data
     * Long-term sector trends and allocation
     */
    async fetchSectorAllocationData() {
        const sectors = ['XLK', 'XLF', 'XLE', 'XLV', 'XLI', 'XLP', 'XLY', 'XLU', 'XLB', 'XLRE', 'XLC'];
        const sectorData = {};

        for (const ticker of sectors) {
            const data = await this.fetchYahooLongTermData(ticker);

            if (data) {
                sectorData[ticker] = {
                    name: this.getSectorName(ticker),
                    current: data.current,
                    sixMonthReturn: data.sixMonthReturn,
                    twelveMonthReturn: data.twelveMonthReturn,
                    eighteenMonthReturn: data.eighteenMonthReturn,
                    volatility: data.volatility,
                    sharpeRatio: this.calculateSharpe(data),
                    allocationScore: this.calculateAllocationScore(data)
                };
            }
        }

        return {
            sectors: sectorData,
            recommended: this.identifyTopAllocations(sectorData, 5),
            avoid: this.identifyBottomAllocations(sectorData, 3),
            diversification: this.assessDiversification(sectorData)
        };
    }

    /**
     * Fetch Valuation Metrics
     * Market-wide valuation assessment
     */
    async fetchValuationMetrics() {
        // Note: Real P/E ratios require fundamental data APIs
        // This is a simplified version using proxy indicators

        const endDate = this.formatDate(new Date());
        const startDate = this.formatDate(this.getMonthsAgo(18));

        const [profits, gdp, yields] = await Promise.all([
            this.fredClient.fetchSeriesObservations(this.fredSeriesIds.corporateProfits, { startDate, endDate }),
            this.fredClient.fetchSeriesObservations(this.fredSeriesIds.gdp, { startDate, endDate }),
            this.fredClient.fetchSeriesObservations(this.fredSeriesIds.treasury10y, { startDate, endDate })
        ]);

        const profitsObs = profits.success ? profits.data.observations.filter(o => o.isValid) : [];
        const gdpObs = gdp.success ? gdp.data.observations.filter(o => o.isValid) : [];
        const yieldObs = yields.success ? yields.data.observations.filter(o => o.isValid) : [];

        return {
            corporateProfits: {
                latest: profitsObs[0]?.value || null,
                trend: this.calculateTrend(profitsObs),
                yoyChange: this.calculateYoYChange(profitsObs)
            },
            economicOutput: {
                gdp: gdpObs[0]?.value || null,
                trend: this.calculateTrend(gdpObs)
            },
            yieldEnvironment: {
                current: yieldObs[0]?.value || null,
                sixMonthAvg: this.calculateAverage(yieldObs.slice(0, 120)),
                trend: this.calculateTrend(yieldObs)
            },
            assessment: this.assessValuation(profitsObs, gdpObs, yieldObs)
        };
    }

    /**
     * Fetch Global Macro Data
     * International markets and global trends
     */
    async fetchGlobalMacroData() {
        const regions = {
            developed: 'EFA',
            emerging: 'EEM',
            china: 'FXI',
            japan: 'EWJ',
            europe: 'EZU'
        };

        const global = {};

        for (const [region, ticker] of Object.entries(regions)) {
            const data = await this.fetchYahooLongTermData(ticker);

            if (data) {
                global[region] = {
                    ticker,
                    twelveMonthReturn: data.twelveMonthReturn,
                    eighteenMonthReturn: data.eighteenMonthReturn,
                    volatility: data.volatility,
                    trend: this.classifyLongTermTrend(data.eighteenMonthReturn)
                };
            }
        }

        return {
            regions: global,
            bestPerforming: this.identifyBestRegions(global),
            globalRiskAppetite: this.assessGlobalRisk(global)
        };
    }

    /**
     * Generate Strategic Analysis
     * Comprehensive 6-18 month outlook
     */
    generateStrategicAnalysis(data) {
        const analysis = {
            economicOutlook: this.assessEconomicOutlook(data.macroeconomic),
            marketPhase: this.identifyMarketPhase(data.markets, data.macroeconomic),
            allocationStrategy: this.recommendAllocation(data.sectors, data.macroeconomic),
            riskLevel: this.assessLongTermRisk(data),
            keyThemes: this.identifyKeyThemes(data),
            actionItems: []
        };

        // Generate strategic action items
        if (analysis.economicOutlook === 'expansion') {
            analysis.actionItems.push('Overweight cyclical sectors (XLI, XLF, XLE)');
            analysis.actionItems.push('Increase equity allocation');
        } else if (analysis.economicOutlook === 'late_cycle') {
            analysis.actionItems.push('Begin rotating to quality/defensive names');
            analysis.actionItems.push('Reduce small-cap exposure');
        } else if (analysis.economicOutlook === 'recession') {
            analysis.actionItems.push('Overweight defensive sectors (XLP, XLU, XLV)');
            analysis.actionItems.push('Increase fixed income allocation');
            analysis.actionItems.push('Focus on dividend aristocrats');
        }

        if (analysis.riskLevel === 'high') {
            analysis.actionItems.push('Consider hedging strategies');
            analysis.actionItems.push('Maintain higher cash levels');
        }

        if (data.valuations?.assessment === 'expensive') {
            analysis.actionItems.push('Be selective - focus on value opportunities');
            analysis.actionItems.push('Favor international over domestic equity');
        }

        return analysis;
    }

    // ========== HELPER FUNCTIONS ==========

    async fetchYahooLongTermData(ticker) {
        try {
            const response = await fetch(`${this.localApiBase}/yahoo/chart/${ticker}?interval=1wk&range=2y`);
            const data = await response.json();

            if (!data?.chart?.result?.[0]) return null;

            const prices = data.chart.result[0].indicators.quote[0].close.filter(p => p !== null);

            if (prices.length < 75) return null; // Need at least 18 months

            const current = prices[prices.length - 1];
            const sixMonthsAgo = prices[prices.length - 26] || prices[0];
            const twelveMonthsAgo = prices[prices.length - 52] || prices[0];
            const eighteenMonthsAgo = prices[prices.length - 78] || prices[0];

            return {
                current,
                sixMonthReturn: ((current - sixMonthsAgo) / sixMonthsAgo * 100).toFixed(2),
                twelveMonthReturn: ((current - twelveMonthsAgo) / twelveMonthsAgo * 100).toFixed(2),
                eighteenMonthReturn: ((current - eighteenMonthsAgo) / eighteenMonthsAgo * 100).toFixed(2),
                volatility: this.calculateVolatility(prices),
                prices
            };
        } catch (error) {
            console.warn(`Failed to fetch long-term data for ${ticker}:`, error);
            return null;
        }
    }

    processQuarterlyData(results, seriesKey) {
        const seriesId = this.fredSeriesIds[seriesKey];
        const response = results[seriesId];

        if (!response?.success) return { trend: 'unknown', latest: null };

        const obs = response.data.observations.filter(o => o.isValid);

        return {
            latest: obs[0]?.value || null,
            quarters: obs.slice(0, 6),
            trend: this.calculateTrend(obs),
            yoyChange: this.calculateYoYChange(obs)
        };
    }

    processMonthlyData(results, seriesKey) {
        const seriesId = this.fredSeriesIds[seriesKey];
        const response = results[seriesId];

        if (!response?.success) return { trend: 'unknown', latest: null };

        const obs = response.data.observations.filter(o => o.isValid);

        return {
            latest: obs[0]?.value || null,
            sixMonthAvg: this.calculateAverage(obs.slice(0, 6)),
            twelveMonthAvg: this.calculateAverage(obs.slice(0, 12)),
            trend: this.calculateTrend(obs),
            momentum: this.calculateDataMomentum(obs)
        };
    }

    calculateVolatility(prices) {
        if (prices.length < 20) return null;

        const returns = [];
        for (let i = 1; i < prices.length; i++) {
            returns.push((prices[i] - prices[i-1]) / prices[i-1]);
        }

        const mean = returns.reduce((sum, r) => sum + r, 0) / returns.length;
        const variance = returns.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) / returns.length;
        const stdDev = Math.sqrt(variance);

        return (stdDev * Math.sqrt(52) * 100).toFixed(2); // Annualized volatility
    }

    calculateSharpe(data) {
        const riskFreeRate = 4.5; // Approximate current T-Bill rate
        const return18m = parseFloat(data.eighteenMonthReturn);
        const volatility = parseFloat(data.volatility);

        if (!return18m || !volatility || volatility === 0) return null;

        const annualizedReturn = return18m * (12 / 18);
        const sharpe = (annualizedReturn - riskFreeRate) / volatility;

        return sharpe.toFixed(2);
    }

    calculateAllocationScore(data) {
        const ret = parseFloat(data.eighteenMonthReturn);
        const vol = parseFloat(data.volatility);
        const sharpe = parseFloat(data.sharpeRatio);

        if (!ret || !vol || !sharpe) return 50;

        let score = 50;
        score += (ret / 2); // Reward returns
        score -= (vol / 4); // Penalize volatility
        score += (sharpe * 10); // Reward risk-adjusted returns

        return Math.max(0, Math.min(100, score));
    }

    identifyTopAllocations(sectorData, count) {
        return Object.entries(sectorData)
            .filter(([_, data]) => data.allocationScore !== undefined)
            .sort((a, b) => b[1].allocationScore - a[1].allocationScore)
            .slice(0, count)
            .map(([ticker, data]) => ({ ticker, score: data.allocationScore }));
    }

    identifyBottomAllocations(sectorData, count) {
        return Object.entries(sectorData)
            .filter(([_, data]) => data.allocationScore !== undefined)
            .sort((a, b) => a[1].allocationScore - b[1].allocationScore)
            .slice(0, count)
            .map(([ticker, data]) => ({ ticker, score: data.allocationScore }));
    }

    assessDiversification(sectorData) {
        const returns = Object.values(sectorData)
            .map(s => parseFloat(s.eighteenMonthReturn))
            .filter(r => !isNaN(r));

        if (returns.length < 5) return 'insufficient_data';

        const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
        const variance = returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length;
        const stdDev = Math.sqrt(variance);

        // Higher standard deviation means more dispersion (better diversification opportunities)
        if (stdDev > 15) return 'high_dispersion';
        if (stdDev > 8) return 'moderate_dispersion';
        return 'low_dispersion';
    }

    assessValuation(profitsObs, gdpObs, yieldObs) {
        // Simplified valuation assessment
        if (!profitsObs || !gdpObs || profitsObs.length < 2 || gdpObs.length < 2) {
            return 'unknown';
        }

        const profitsTrend = this.calculateTrend(profitsObs);
        const gdpTrend = this.calculateTrend(gdpObs);
        const currentYield = yieldObs[0]?.value || 4;

        // Strong profits + strong GDP + low yields = expensive
        if (profitsTrend === 'rising' && gdpTrend === 'rising' && currentYield < 3.5) {
            return 'expensive';
        }

        // Falling profits + falling GDP = cheap
        if (profitsTrend === 'falling' && gdpTrend === 'falling') {
            return 'cheap';
        }

        return 'fair';
    }

    identifyBestRegions(global) {
        return Object.entries(global)
            .sort((a, b) => parseFloat(b[1].eighteenMonthReturn) - parseFloat(a[1].eighteenMonthReturn))
            .slice(0, 2)
            .map(([region]) => region);
    }

    assessGlobalRisk(global) {
        const emReturn = parseFloat(global.emerging?.eighteenMonthReturn) || 0;
        const devReturn = parseFloat(global.developed?.eighteenMonthReturn) || 0;

        if (emReturn > devReturn + 10) return 'high_risk_appetite';
        if (emReturn < devReturn - 10) return 'low_risk_appetite';
        return 'moderate';
    }

    assessEconomicOutlook(macro) {
        let score = 0;

        if (macro.growth?.trend === 'rising') score += 20;
        if (macro.growth?.trend === 'falling') score -= 20;

        if (macro.employment?.trend === 'falling') score += 15; // Lower unemployment is good
        if (macro.employment?.trend === 'rising') score -= 15;

        if (macro.leading?.trend === 'rising') score += 25;
        if (macro.leading?.trend === 'falling') score -= 25;

        if (score > 30) return 'strong_expansion';
        if (score > 10) return 'expansion';
        if (score < -30) return 'recession';
        if (score < -10) return 'late_cycle';
        return 'mid_cycle';
    }

    identifyMarketPhase(markets, macro) {
        const spxReturn = parseFloat(markets.SPX?.eighteenMonthReturn) || 0;
        const economicOutlook = this.assessEconomicOutlook(macro);

        if (spxReturn > 25 && economicOutlook === 'expansion') return 'bull_market';
        if (spxReturn < -15 && economicOutlook === 'recession') return 'bear_market';
        if (spxReturn > 10 && economicOutlook === 'late_cycle') return 'late_bull';
        if (spxReturn < 0 && economicOutlook === 'expansion') return 'correction';
        return 'neutral';
    }

    recommendAllocation(sectors, macro) {
        const outlook = this.assessEconomicOutlook(macro);

        if (outlook === 'strong_expansion' || outlook === 'expansion') {
            return {
                equity: 70,
                fixedIncome: 20,
                alternatives: 10,
                sectorFocus: ['XLK', 'XLF', 'XLI'],
                style: 'growth_and_cyclical'
            };
        } else if (outlook === 'recession') {
            return {
                equity: 40,
                fixedIncome: 50,
                alternatives: 10,
                sectorFocus: ['XLP', 'XLU', 'XLV'],
                style: 'defensive_and_quality'
            };
        } else {
            return {
                equity: 55,
                fixedIncome: 35,
                alternatives: 10,
                sectorFocus: ['XLK', 'XLV', 'XLP'],
                style: 'balanced'
            };
        }
    }

    assessLongTermRisk(data) {
        let riskScore = 0;

        if (data.valuations?.assessment === 'expensive') riskScore += 20;
        if (data.macroeconomic?.inflation?.trend === 'rising') riskScore += 15;
        if (data.macroeconomic?.leading?.trend === 'falling') riskScore += 25;
        if (data.markets?.SPX?.volatility > 20) riskScore += 15;

        if (riskScore > 40) return 'high';
        if (riskScore > 20) return 'moderate';
        return 'low';
    }

    identifyKeyThemes(data) {
        const themes = [];

        if (data.macroeconomic?.inflation?.trend === 'rising') {
            themes.push('Rising inflation - favor real assets (commodities, real estate)');
        }

        if (data.macroeconomic?.growth?.trend === 'rising') {
            themes.push('Economic expansion - favor cyclicals and growth');
        }

        if (data.global?.globalRiskAppetite === 'high_risk_appetite') {
            themes.push('Global risk-on - emerging markets attractive');
        }

        if (data.sectors?.diversification === 'high_dispersion') {
            themes.push('High sector dispersion - active management crucial');
        }

        return themes.length > 0 ? themes : ['Neutral environment - balanced approach recommended'];
    }

    calculateMomentumScore(data) {
        const sixM = parseFloat(data.sixMonthReturn);
        const twelveM = parseFloat(data.twelveMonthReturn);
        const eighteenM = parseFloat(data.eighteenMonthReturn);

        const score = (sixM * 0.5 + twelveM * 0.3 + eighteenM * 0.2);

        if (score > 20) return 'strong_positive';
        if (score > 10) return 'positive';
        if (score < -20) return 'strong_negative';
        if (score < -10) return 'negative';
        return 'neutral';
    }

    classifyLongTermTrend(returnPercent) {
        const ret = parseFloat(returnPercent);
        if (ret > 30) return 'strong_uptrend';
        if (ret > 15) return 'uptrend';
        if (ret < -20) return 'strong_downtrend';
        if (ret < -10) return 'downtrend';
        return 'sideways';
    }

    calculateTrend(observations) {
        if (!observations || observations.length < 6) return 'unknown';

        const recent = observations.slice(0, 3).reduce((sum, o) => sum + o.value, 0) / 3;
        const older = observations.slice(-3).reduce((sum, o) => sum + o.value, 0) / 3;

        const change = ((recent - older) / older * 100);

        if (change > 3) return 'rising';
        if (change < -3) return 'falling';
        return 'stable';
    }

    calculateYoYChange(observations) {
        if (!observations || observations.length < 12) return null;

        const current = observations[0]?.value;
        const yearAgo = observations[11]?.value;

        if (!current || !yearAgo) return null;

        return ((current - yearAgo) / yearAgo * 100).toFixed(2);
    }

    calculateAverage(observations) {
        if (!observations || observations.length === 0) return null;
        const validObs = observations.filter(o => o && o.value !== undefined);
        if (validObs.length === 0) return null;

        return (validObs.reduce((sum, o) => sum + o.value, 0) / validObs.length).toFixed(2);
    }

    calculateDataMomentum(observations) {
        if (!observations || observations.length < 6) return 'unknown';

        const recentAvg = this.calculateAverage(observations.slice(0, 3));
        const olderAvg = this.calculateAverage(observations.slice(3, 6));

        if (!recentAvg || !olderAvg) return 'unknown';

        const change = ((recentAvg - olderAvg) / olderAvg * 100);

        if (change > 2) return 'accelerating';
        if (change < -2) return 'decelerating';
        return 'steady';
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
    window.TimeframeDataFetcher_6_18_Months = TimeframeDataFetcher_6_18_Months;
}

console.log('✅ 6-18 Month Position Trading Data Module Loaded');
