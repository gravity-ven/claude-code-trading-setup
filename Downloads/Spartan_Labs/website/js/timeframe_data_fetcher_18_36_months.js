/**
 * SPARTAN LABS - 18-36 MONTH LONG-TERM INVESTMENT DATA MODULE
 *
 * LONG-TERM INVESTING (18-36 Months / 1.5-3 Years)
 * Focus: Secular trends, economic cycles, structural shifts
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

class TimeframeDataFetcher_18_36_Months {
    constructor(config = {}) {
        this.timeframe = '18-36 months';
        this.fredClient = new FredApiClient();
        this.cacheTTL = config.cacheTTL || 24 * 60 * 60 * 1000; // 24 hours cache
        this.cachePrefix = 'longterm_18_36m_';

        // FRED Series IDs for multi-year analysis
        this.fredSeriesIds = {
            // GDP & National Accounts (Quarterly/Annual)
            gdp: 'GDP',                        // Real GDP
            gdpNominal: 'GDPC1',               // Nominal GDP
            gdpGrowth: 'A191RL1Q225SBEA',      // Real GDP Growth
            gdpPerCapita: 'A939RX0Q048SBEA',   // Real GDP Per Capita
            gdi: 'GDI',                        // Gross Domestic Income

            // Corporate Sector (Quarterly)
            corporateProfits: 'CP',            // Corporate Profits
            corporateProfitsGDP: 'A053RC1Q027SBEA', // Corp Profits as % of GDP

            // Labor Market (Annual aggregates)
            unemployment: 'UNRATE',            // Unemployment Rate
            nonfarmPayrolls: 'PAYEMS',         // Total Nonfarm Payrolls
            laborParticipation: 'CIVPART',     // Labor Force Participation
            productivity: 'OPHNFB',            // Nonfarm Business Productivity

            // Prices & Inflation (Annual)
            cpi: 'CPIAUCSL',                   // Consumer Price Index
            pce: 'PCEPI',                      // PCE Price Index
            gdpDeflator: 'GDPDEF',             // GDP Deflator
            inflation5YrExp: 'T5YIE',          // 5-Year Inflation Expectations
            inflation10YrExp: 'T10YIE',        // 10-Year Inflation Expectations

            // Interest Rates & Monetary Policy (Quarterly/Annual)
            fedFunds: 'FEDFUNDS',              // Federal Funds Rate
            treasury10y: 'DGS10',              // 10-Year Treasury
            treasury30y: 'DGS30',              // 30-Year Treasury
            realRate10y: 'DFII10',             // 10-Year TIPS (Real Rate)
            termPremium: 'THREEFYTP10',        // 10-Year Term Premium

            // Federal Reserve Balance Sheet (Quarterly)
            fedAssets: 'WALCL',                // Fed Total Assets
            monetaryBase: 'BOGMBASE',          // Monetary Base

            // Credit & Debt (Quarterly)
            totalDebt: 'GFDEBTN',              // Federal Debt Total
            debtToGDP: 'GFDEGDQ188S',          // Debt-to-GDP Ratio
            householdDebt: 'HDTGPDUSQ163N',    // Household Debt to GDP
            corporateDebt: 'NCBDBIQ027S',      // Nonfinancial Corporate Debt

            // Housing (Annual aggregates)
            housePriceIndex: 'CSUSHPISA',      // Case-Shiller National Home Price
            housingStarts: 'HOUST',            // Housing Starts
            homeownership: 'RHORUSQ156N',      // Homeownership Rate

            // Demographics (Annual)
            population: 'POPTHM',              // Total Population
            workingAgePop: 'LFWA64TTUSM647S',  // Working Age Population

            // International Trade (Annual)
            tradeBalance: 'BOPGSTB',           // Trade Balance
            currentAccount: 'NETFI',           // Current Account Balance
            exports: 'EXPGS',                  // Exports
            imports: 'IMPGS',                  // Imports

            // Productivity & Wages (Annual)
            laborProductivity: 'OPHNFB',       // Labor Productivity
            realWages: 'LES1252881600Q',       // Real Median Weekly Earnings
            unitLaborCost: 'ULCNFB',           // Unit Labor Costs

            // Commodities (Annual aggregates)
            goldPrice: 'GOLDAMGBD228NLBM',     // Gold
            oilPrice: 'DCOILWTICO',            // WTI Oil
            copperPrice: 'PCOPPUSDM',          // Copper
            crbIndex: 'PPIACO',                // CRB Commodity Index proxy

            // Currency (Annual aggregates)
            dollarIndex: 'DTWEXBGS',           // US Dollar Index

            // Leading Indicators (Annual)
            leadingIndex: 'USSLIND',           // Leading Economic Index
            yieldCurveSpread: 'T10Y2Y',        // 10Y-2Y Spread (recession indicator)

            // Financial Stress (Quarterly)
            financialStress: 'STLFSI4',        // St. Louis Fed Financial Stress
            chicagoFed: 'CFNAI'                // Chicago Fed National Activity
        };

        // Yahoo Finance for multi-year market data
        this.yahooTickers = {
            // Major US Indices
            spx: '^GSPC', ndx: '^NDX', dji: '^DJI', rut: '^RUT',

            // Sectors
            xlk: 'XLK', xlf: 'XLF', xle: 'XLE', xlv: 'XLV',
            xli: 'XLI', xlp: 'XLP', xly: 'XLY', xlu: 'XLU',
            xlb: 'XLB', xlre: 'XLRE', xlc: 'XLC',

            // International Developed
            efa: 'EFA',   // EAFE (Europe, Australasia, Far East)
            vea: 'VEA',   // FTSE Developed Markets
            ewj: 'EWJ',   // Japan
            ezu: 'EZU',   // Eurozone
            ewu: 'EWU',   // UK
            ewg: 'EWG',   // Germany

            // Emerging Markets
            eem: 'EEM',   // MSCI Emerging Markets
            vwo: 'VWO',   // FTSE Emerging Markets
            fxi: 'FXI',   // China Large Cap
            ewz: 'EWZ',   // Brazil
            rsx: 'RSX',   // Russia (if available)
            inda: 'INDA', // India

            // Fixed Income
            tlt: 'TLT',   // 20+ Year Treasury
            ief: 'IEF',   // 7-10 Year Treasury
            shy: 'SHY',   // 1-3 Year Treasury
            tip: 'TIP',   // TIPS
            lqd: 'LQD',   // Investment Grade Corporate
            hyg: 'HYG',   // High Yield
            emb: 'EMB',   // Emerging Market Bonds

            // Commodities
            gld: 'GLD',   // Gold
            slv: 'SLV',   // Silver
            uso: 'USO',   // Oil
            dba: 'DBA',   // Agriculture
            dbc: 'DBC',   // Commodity Index

            // Real Estate
            vnq: 'VNQ',   // US REIT
            vnqi: 'VNQI'  // International REIT
        };

        this.localApiBase = 'http://localhost:8888/api';
    }

    /**
     * MASTER FETCH: Get all 18-36 month long-term investment data
     */
    async fetchAllData() {
        console.log('📊 Fetching 18-36 Month Long-Term Investment Data...');

        try {
            const [
                secularTrends,
                economicCycle,
                structuralShifts,
                globalDynamics,
                assetClassReturns
            ] = await Promise.all([
                this.fetchSecularTrends(),
                this.fetchEconomicCycleData(),
                this.fetchStructuralShifts(),
                this.fetchGlobalDynamics(),
                this.fetchAssetClassReturns()
            ]);

            const dataset = {
                timeframe: this.timeframe,
                timestamp: new Date().toISOString(),
                lookbackPeriod: '3 years',

                secular: secularTrends,
                cycle: economicCycle,
                structural: structuralShifts,
                global: globalDynamics,
                assetClasses: assetClassReturns,

                // Strategic long-term analysis
                analysis: this.generateLongTermAnalysis({
                    secularTrends,
                    economicCycle,
                    structuralShifts,
                    globalDynamics,
                    assetClassReturns
                }),

                metadata: {
                    sources: ['FRED', 'Yahoo Finance'],
                    updateFrequency: '24 hours',
                    perspective: 'multi-year strategic'
                }
            };

            this.setCached('all_data', dataset);

            return { success: true, data: dataset };

        } catch (error) {
            console.error('❌ Failed to fetch 18-36 month data:', error);

            const cached = this.getCached('all_data');
            if (cached) {
                return { success: true, data: cached, warning: 'Using cached data' };
            }

            return { success: false, error: error.message };
        }
    }

    /**
     * Fetch Secular Trends
     * Multi-year economic and market trends
     */
    async fetchSecularTrends() {
        const endDate = this.formatDate(new Date());
        const startDate = this.formatDate(this.getYearsAgo(3));

        const series = [
            this.fredSeriesIds.gdpGrowth,
            this.fredSeriesIds.productivity,
            this.fredSeriesIds.inflation10YrExp,
            this.fredSeriesIds.corporateProfitsGDP,
            this.fredSeriesIds.debtToGDP,
            this.fredSeriesIds.laborParticipation,
            this.fredSeriesIds.dollarIndex
        ];

        const results = await this.fredClient.fetchMultipleSeries(series, {
            startDate,
            endDate,
            sortOrder: 'desc'
        });

        return {
            growth: this.analyzeSecularTrend(results.results[this.fredSeriesIds.gdpGrowth], 'GDP Growth'),
            productivity: this.analyzeSecularTrend(results.results[this.fredSeriesIds.productivity], 'Productivity'),
            inflation: this.analyzeSecularTrend(results.results[this.fredSeriesIds.inflation10YrExp], 'Inflation Expectations'),
            profitability: this.analyzeSecularTrend(results.results[this.fredSeriesIds.corporateProfitsGDP], 'Corporate Profits'),
            leverage: this.analyzeSecularTrend(results.results[this.fredSeriesIds.debtToGDP], 'Debt-to-GDP'),
            demographics: this.analyzeSecularTrend(results.results[this.fredSeriesIds.laborParticipation], 'Labor Participation'),
            dollar: this.analyzeSecularTrend(results.results[this.fredSeriesIds.dollarIndex], 'Dollar Strength')
        };
    }

    /**
     * Fetch Economic Cycle Data
     * Where are we in the business cycle?
     */
    async fetchEconomicCycleData() {
        const endDate = this.formatDate(new Date());
        const startDate = this.formatDate(this.getYearsAgo(3));

        const [unemployment, leading, yieldCurve, profits] = await Promise.all([
            this.fredClient.fetchSeriesObservations(this.fredSeriesIds.unemployment, { startDate, endDate }),
            this.fredClient.fetchSeriesObservations(this.fredSeriesIds.leadingIndex, { startDate, endDate }),
            this.fredClient.fetchSeriesObservations(this.fredSeriesIds.yieldCurveSpread, { startDate, endDate }),
            this.fredClient.fetchSeriesObservations(this.fredSeriesIds.corporateProfits, { startDate, endDate })
        ]);

        const unempObs = unemployment.success ? unemployment.data.observations.filter(o => o.isValid) : [];
        const leadObs = leading.success ? leading.data.observations.filter(o => o.isValid) : [];
        const yieldObs = yieldCurve.success ? yieldCurve.data.observations.filter(o => o.isValid) : [];
        const profitsObs = profits.success ? profits.data.observations.filter(o => o.isValid) : [];

        return {
            phase: this.identifyBusinessCyclePhase(unempObs, leadObs, profitsObs),
            unemployment: {
                current: unempObs[0]?.value || null,
                trend: this.calculateLongTrend(unempObs),
                cycleLow: Math.min(...unempObs.slice(0, 36).map(o => o.value)),
                cycleHigh: Math.max(...unempObs.slice(0, 36).map(o => o.value))
            },
            leadingIndicators: {
                current: leadObs[0]?.value || null,
                trend: this.calculateLongTrend(leadObs),
                signal: this.interpretLeadingIndex(leadObs)
            },
            yieldCurve: {
                current: yieldObs[0]?.value || null,
                inverted: yieldObs[0]?.value < 0,
                inversionDuration: this.calculateInversionDuration(yieldObs),
                recessionProbability: this.calculateRecessionProbability(yieldObs)
            }
        };
    }

    /**
     * Fetch Structural Shifts
     * Long-term structural changes in economy
     */
    async fetchStructuralShifts() {
        const endDate = this.formatDate(new Date());
        const startDate = this.formatDate(this.getYearsAgo(5)); // 5 years for structural analysis

        const [fedAssets, debtGDP, productivity, realWages] = await Promise.all([
            this.fredClient.fetchSeriesObservations(this.fredSeriesIds.fedAssets, { startDate, endDate }),
            this.fredClient.fetchSeriesObservations(this.fredSeriesIds.debtToGDP, { startDate, endDate }),
            this.fredClient.fetchSeriesObservations(this.fredSeriesIds.productivity, { startDate, endDate }),
            this.fredClient.fetchSeriesObservations(this.fredSeriesIds.realWages, { startDate, endDate })
        ]);

        return {
            monetaryPolicy: {
                fedBalanceSheet: this.analyzeFedBalanceSheet(fedAssets),
                regime: this.identifyMonetaryRegime(fedAssets)
            },
            fiscalPosition: {
                debtLevel: this.analyzeDebtLevel(debtGDP),
                sustainability: this.assessFiscalSustainability(debtGDP)
            },
            productivity: {
                trend: this.analyzeLongTermProductivity(productivity),
                implications: this.interpretProductivityTrend(productivity)
            },
            wageDynamics: {
                realWageTrend: this.calculateLongTrend(realWages.success ? realWages.data.observations : []),
                workerPowerShift: this.assessLaborMarketPower(realWages)
            }
        };
    }

    /**
     * Fetch Global Dynamics
     * International markets and capital flows
     */
    async fetchGlobalDynamics() {
        const regions = {
            us: '^GSPC',
            developed: 'EFA',
            emerging: 'EEM',
            china: 'FXI',
            japan: 'EWJ',
            europe: 'EZU',
            india: 'INDA',
            brazil: 'EWZ'
        };

        const global = {};

        for (const [region, ticker] of Object.entries(regions)) {
            const data = await this.fetchMultiYearData(ticker);
            if (data) {
                global[region] = {
                    ticker,
                    oneYearReturn: data.oneYearReturn,
                    twoYearReturn: data.twoYearReturn,
                    threeYearReturn: data.threeYearReturn,
                    cagr: data.cagr,
                    volatility: data.volatility,
                    maxDrawdown: data.maxDrawdown,
                    trend: this.classifyMultiYearTrend(data.threeYearReturn)
                };
            }
        }

        return {
            regions: global,
            leadership: this.identifyRegionalLeadership(global),
            diversification: this.assessGlobalDiversification(global),
            emergingVsDeveloped: this.compareEmergingDeveloped(global)
        };
    }

    /**
     * Fetch Asset Class Returns
     * Multi-year performance across all asset classes
     */
    async fetchAssetClassReturns() {
        const assetClasses = {
            usEquity: '^GSPC',
            intlEquity: 'EFA',
            emEquity: 'EEM',
            bonds: 'AGG',
            tips: 'TIP',
            highYield: 'HYG',
            gold: 'GLD',
            commodities: 'DBC',
            reits: 'VNQ'
        };

        const returns = {};

        for (const [asset, ticker] of Object.entries(assetClasses)) {
            const data = await this.fetchMultiYearData(ticker);
            if (data) {
                returns[asset] = {
                    ticker,
                    cagr: data.cagr,
                    volatility: data.volatility,
                    sharpe: this.calculateSharpeRatio(data.cagr, data.volatility),
                    maxDrawdown: data.maxDrawdown,
                    calmarRatio: this.calculateCalmarRatio(data.cagr, data.maxDrawdown)
                };
            }
        }

        return {
            assetClasses: returns,
            bestPerforming: this.identifyBestAssets(returns, 3),
            worstPerforming: this.identifyWorstAssets(returns, 3),
            optimalAllocation: this.recommendOptimalAllocation(returns)
        };
    }

    /**
     * Generate Long-Term Analysis
     * Strategic 18-36 month outlook and allocation
     */
    generateLongTermAnalysis(data) {
        const analysis = {
            secularOutlook: this.assessSecularOutlook(data.secular),
            cyclePosition: data.cycle?.phase || 'unknown',
            structuralThemes: this.identifyStructuralThemes(data.structural),
            globalOpportunities: this.identifyGlobalOpportunities(data.global),
            portfolioConstruction: this.buildStrategicPortfolio(data),
            riskFactors: this.identifyLongTermRisks(data),
            strategicRecommendations: []
        };

        // Generate strategic recommendations
        if (analysis.secularOutlook === 'disinflationary_growth') {
            analysis.strategicRecommendations.push('Favor equities over bonds - growth without inflation pressure');
            analysis.strategicRecommendations.push('Overweight technology and growth sectors');
        } else if (analysis.secularOutlook === 'stagflation') {
            analysis.strategicRecommendations.push('Increase allocation to real assets (commodities, TIPS, REITs)');
            analysis.strategicRecommendations.push('Reduce duration in fixed income');
        }

        if (analysis.cyclePosition === 'early_expansion') {
            analysis.strategicRecommendations.push('Aggressive equity positioning - early cycle is best for stocks');
            analysis.strategicRecommendations.push('Favor small-caps and cyclicals');
        } else if (analysis.cyclePosition === 'late_cycle') {
            analysis.strategicRecommendations.push('Begin defensive rotation - late cycle fragility');
            analysis.strategicRecommendations.push('Increase quality bias and cash reserves');
        } else if (analysis.cyclePosition === 'recession') {
            analysis.strategicRecommendations.push('Maximum defensive posture - bonds, gold, utilities');
            analysis.strategicRecommendations.push('Prepare for recovery opportunities');
        }

        if (data.global?.leadership?.region === 'emerging') {
            analysis.strategicRecommendations.push('Allocate 15-20% to emerging markets');
        }

        if (data.structural?.monetaryPolicy?.regime === 'tight') {
            analysis.strategicRecommendations.push('Higher cash yields attractive - consider elevated cash allocation');
        }

        return analysis;
    }

    // ========== HELPER FUNCTIONS ==========

    async fetchMultiYearData(ticker) {
        try {
            const response = await fetch(`${this.localApiBase}/yahoo/chart/${ticker}?interval=1mo&range=5y`);
            const data = await response.json();

            if (!data?.chart?.result?.[0]) return null;

            const prices = data.chart.result[0].indicators.quote[0].close.filter(p => p !== null);

            if (prices.length < 36) return null; // Need at least 3 years

            const current = prices[prices.length - 1];
            const oneYearAgo = prices[prices.length - 13] || prices[0];
            const twoYearsAgo = prices[prices.length - 25] || prices[0];
            const threeYearsAgo = prices[prices.length - 37] || prices[0];

            const oneYearReturn = ((current - oneYearAgo) / oneYearAgo * 100).toFixed(2);
            const twoYearReturn = ((current - twoYearsAgo) / twoYearsAgo * 100).toFixed(2);
            const threeYearReturn = ((current - threeYearsAgo) / threeYearsAgo * 100).toFixed(2);

            const cagr = (Math.pow(current / threeYearsAgo, 1/3) - 1) * 100;
            const volatility = this.calculateAnnualizedVolatility(prices);
            const maxDrawdown = this.calculateMaxDrawdown(prices);

            return {
                current,
                oneYearReturn,
                twoYearReturn,
                threeYearReturn,
                cagr: cagr.toFixed(2),
                volatility,
                maxDrawdown,
                prices
            };
        } catch (error) {
            console.warn(`Failed to fetch multi-year data for ${ticker}:`, error);
            return null;
        }
    }

    analyzeSecularTrend(response, name) {
        if (!response?.success) return { name, trend: 'unknown' };

        const obs = response.data.observations.filter(o => o.isValid);
        const longTrend = this.calculateLongTrend(obs);
        const momentum = this.calculateMomentum(obs);

        return {
            name,
            latest: obs[0]?.value || null,
            threeYearAvg: this.calculateAverage(obs.slice(0, 12)),
            trend: longTrend,
            momentum,
            direction: this.interpretSecularDirection(longTrend, momentum)
        };
    }

    identifyBusinessCyclePhase(unemployment, leading, profits) {
        if (!unemployment || !leading || unemployment.length < 12 || leading.length < 12) {
            return 'unknown';
        }

        const unempTrend = this.calculateLongTrend(unemployment);
        const leadTrend = this.calculateLongTrend(leading);
        const unempCurrent = unemployment[0].value;
        const unempLow = Math.min(...unemployment.slice(0, 36).map(o => o.value));

        // Early expansion: unemployment falling, leading rising
        if (unempTrend === 'falling' && leadTrend === 'rising') {
            return 'early_expansion';
        }

        // Mid expansion: unemployment low and stable, leading positive
        if (unempCurrent < unempLow + 0.5 && leadTrend === 'rising') {
            return 'mid_expansion';
        }

        // Late cycle: unemployment very low, leading starting to fall
        if (unempCurrent <= unempLow + 0.3 && leadTrend === 'falling') {
            return 'late_cycle';
        }

        // Recession: unemployment rising, leading falling
        if (unempTrend === 'rising' && leadTrend === 'falling') {
            return 'recession';
        }

        return 'transition';
    }

    interpretLeadingIndex(observations) {
        if (!observations || observations.length < 6) return 'unknown';

        const trend = this.calculateLongTrend(observations);
        const current = observations[0]?.value || 0;

        if (trend === 'rising' && current > 0.5) return 'strong_expansion_ahead';
        if (trend === 'rising') return 'expansion_ahead';
        if (trend === 'falling' && current < -0.5) return 'recession_warning';
        if (trend === 'falling') return 'slowdown_ahead';
        return 'neutral';
    }

    calculateInversionDuration(yieldObs) {
        if (!yieldObs || yieldObs.length === 0) return 0;

        let months = 0;
        for (const obs of yieldObs) {
            if (obs.value < 0) {
                months++;
            } else {
                break;
            }
        }
        return months;
    }

    calculateRecessionProbability(yieldObs) {
        const inversionDuration = this.calculateInversionDuration(yieldObs);

        if (inversionDuration >= 6) return 'high';
        if (inversionDuration >= 3) return 'moderate';
        if (inversionDuration >= 1) return 'low';
        return 'very_low';
    }

    analyzeFedBalanceSheet(response) {
        if (!response.success) return { trend: 'unknown' };

        const obs = response.data.observations.filter(o => o.isValid);
        const current = obs[0]?.value || null;
        const yearAgo = obs[12]?.value || current;
        const threeYearsAgo = obs[36]?.value || current;

        return {
            current,
            yearOverYear: yearAgo ? ((current - yearAgo) / yearAgo * 100).toFixed(2) : null,
            threeYearChange: threeYearsAgo ? ((current - threeYearsAgo) / threeYearsAgo * 100).toFixed(2) : null,
            trend: this.calculateLongTrend(obs)
        };
    }

    identifyMonetaryRegime(fedAssets) {
        if (!fedAssets.success) return 'unknown';

        const obs = fedAssets.data.observations.filter(o => o.isValid);
        const trend = this.calculateLongTrend(obs);

        if (trend === 'rising') return 'accommodative';
        if (trend === 'falling') return 'tight';
        return 'neutral';
    }

    analyzeDebtLevel(response) {
        if (!response.success) return { level: 'unknown' };

        const obs = response.data.observations.filter(o => o.isValid);
        const current = obs[0]?.value || null;

        return {
            current,
            trend: this.calculateLongTrend(obs),
            assessment: current > 100 ? 'very_high' : current > 75 ? 'high' : current > 50 ? 'moderate' : 'manageable'
        };
    }

    assessFiscalSustainability(debtResponse) {
        if (!debtResponse.success) return 'unknown';

        const obs = debtResponse.data.observations.filter(o => o.isValid);
        const trend = this.calculateLongTrend(obs);
        const current = obs[0]?.value || 0;

        if (current > 120 && trend === 'rising') return 'unsustainable';
        if (current > 100 && trend === 'rising') return 'concerning';
        if (trend === 'stable' || trend === 'falling') return 'stable';
        return 'manageable';
    }

    analyzeLongTermProductivity(response) {
        if (!response.success) return { trend: 'unknown' };

        const obs = response.data.observations.filter(o => o.isValid);
        return {
            trend: this.calculateLongTrend(obs),
            momentum: this.calculateMomentum(obs),
            interpretation: this.interpretProductivityTrend(response)
        };
    }

    interpretProductivityTrend(response) {
        if (!response.success) return 'unknown';

        const obs = response.data.observations.filter(o => o.isValid);
        const trend = this.calculateLongTrend(obs);

        if (trend === 'rising') return 'Positive for long-term growth and non-inflationary expansion';
        if (trend === 'falling') return 'Headwind to growth, potential stagflation risk';
        return 'Neutral - stable productivity';
    }

    assessLaborMarketPower(response) {
        if (!response.success) return 'unknown';

        const obs = response.data.observations.filter(o => o.isValid);
        const trend = this.calculateLongTrend(obs);

        if (trend === 'rising') return 'labor_gaining_power';
        if (trend === 'falling') return 'capital_dominant';
        return 'balanced';
    }

    identifyRegionalLeadership(global) {
        const regions = Object.entries(global)
            .filter(([region, data]) => region !== 'us' && data.threeYearReturn)
            .sort((a, b) => parseFloat(b[1].threeYearReturn) - parseFloat(a[1].threeYearReturn));

        return {
            region: regions[0]?.[0] || 'unknown',
            return: regions[0]?.[1].threeYearReturn || null
        };
    }

    assessGlobalDiversification(global) {
        const returns = Object.values(global)
            .map(r => parseFloat(r.threeYearReturn))
            .filter(r => !isNaN(r));

        if (returns.length < 3) return 'insufficient_data';

        const stdDev = this.calculateStdDev(returns);

        if (stdDev > 25) return 'high_dispersion';
        if (stdDev > 15) return 'moderate_dispersion';
        return 'low_dispersion';
    }

    compareEmergingDeveloped(global) {
        const emerging = parseFloat(global.emerging?.threeYearReturn) || 0;
        const developed = parseFloat(global.developed?.threeYearReturn) || 0;

        const spread = emerging - developed;

        return {
            spread: spread.toFixed(2),
            leadership: spread > 5 ? 'emerging' : spread < -5 ? 'developed' : 'neutral'
        };
    }

    identifyBestAssets(returns, count) {
        return Object.entries(returns)
            .sort((a, b) => parseFloat(b[1].cagr) - parseFloat(a[1].cagr))
            .slice(0, count)
            .map(([asset, data]) => ({ asset, cagr: data.cagr }));
    }

    identifyWorstAssets(returns, count) {
        return Object.entries(returns)
            .sort((a, b) => parseFloat(a[1].cagr) - parseFloat(b[1].cagr))
            .slice(0, count)
            .map(([asset, data]) => ({ asset, cagr: data.cagr }));
    }

    recommendOptimalAllocation(returns) {
        // Simplified strategic asset allocation based on Sharpe ratios
        const ranked = Object.entries(returns)
            .filter(([_, data]) => data.sharpe !== null)
            .sort((a, b) => parseFloat(b[1].sharpe) - parseFloat(a[1].sharpe));

        return {
            topAssets: ranked.slice(0, 5).map(([asset]) => asset),
            suggested: {
                equity: 60,
                bonds: 30,
                alternatives: 10
            }
        };
    }

    assessSecularOutlook(secular) {
        const growth = secular.growth?.trend;
        const inflation = secular.inflation?.trend;

        if (growth === 'rising' && inflation === 'falling') return 'disinflationary_growth';
        if (growth === 'rising' && inflation === 'rising') return 'inflationary_growth';
        if (growth === 'falling' && inflation === 'rising') return 'stagflation';
        if (growth === 'falling' && inflation === 'falling') return 'deflation';
        return 'mixed';
    }

    identifyStructuralThemes(structural) {
        const themes = [];

        if (structural.productivity?.trend === 'rising') {
            themes.push('Productivity revival supports non-inflationary growth');
        }

        if (structural.fiscalPosition?.sustainability === 'unsustainable') {
            themes.push('⚠️ Fiscal sustainability concerns - long-term bond vigilance');
        }

        if (structural.monetaryPolicy?.regime === 'tight') {
            themes.push('Tight monetary policy - higher discount rates for equities');
        }

        return themes.length > 0 ? themes : ['No major structural themes identified'];
    }

    identifyGlobalOpportunities(global) {
        const opportunities = [];

        const leadership = global.leadership?.region;
        if (leadership && leadership !== 'us') {
            opportunities.push(`${leadership} markets showing relative strength`);
        }

        if (global.emergingVsDeveloped?.leadership === 'emerging') {
            opportunities.push('Emerging markets cycle turning positive');
        }

        return opportunities.length > 0 ? opportunities : ['Maintain US-centric allocation'];
    }

    buildStrategicPortfolio(data) {
        const cycle = data.cycle?.phase;
        const secular = this.assessSecularOutlook(data.secular);

        const baseAllocation = {
            usEquity: 50,
            intlEquity: 15,
            bonds: 25,
            alternatives: 10
        };

        // Adjust based on cycle
        if (cycle === 'early_expansion') {
            baseAllocation.usEquity += 10;
            baseAllocation.bonds -= 10;
        } else if (cycle === 'recession') {
            baseAllocation.usEquity -= 15;
            baseAllocation.bonds += 15;
        }

        // Adjust based on secular trends
        if (secular === 'stagflation') {
            baseAllocation.alternatives += 10;
            baseAllocation.bonds -= 10;
        }

        return baseAllocation;
    }

    identifyLongTermRisks(data) {
        const risks = [];

        if (data.cycle?.yieldCurve?.inverted) {
            risks.push('Yield curve inversion - recession risk elevated');
        }

        if (data.structural?.fiscalPosition?.sustainability === 'unsustainable') {
            risks.push('Fiscal sustainability concerns');
        }

        if (data.secular?.leverage?.trend === 'rising') {
            risks.push('Rising leverage in the economy');
        }

        return risks.length > 0 ? risks : ['No major long-term risks identified'];
    }

    calculateLongTrend(observations) {
        if (!observations || observations.length < 12) return 'unknown';

        const recent = this.calculateAverage(observations.slice(0, 6));
        const older = this.calculateAverage(observations.slice(-6));

        if (!recent || !older) return 'unknown';

        const change = ((recent - older) / older * 100);

        if (change > 5) return 'rising';
        if (change < -5) return 'falling';
        return 'stable';
    }

    calculateMomentum(observations) {
        if (!observations || observations.length < 12) return 'unknown';

        const recentTrend = this.calculateLongTrend(observations.slice(0, 6));
        const olderTrend = this.calculateLongTrend(observations.slice(6, 18));

        if (recentTrend === 'rising' && olderTrend === 'stable') return 'accelerating';
        if (recentTrend === 'falling' && olderTrend === 'stable') return 'decelerating';
        return 'steady';
    }

    interpretSecularDirection(trend, momentum) {
        if (trend === 'rising' && momentum === 'accelerating') return 'strong_positive';
        if (trend === 'rising') return 'positive';
        if (trend === 'falling' && momentum === 'decelerating') return 'strong_negative';
        if (trend === 'falling') return 'negative';
        return 'neutral';
    }

    classifyMultiYearTrend(threeYearReturn) {
        const ret = parseFloat(threeYearReturn);
        if (ret > 50) return 'strong_bull';
        if (ret > 20) return 'bull';
        if (ret < -30) return 'bear';
        if (ret < -10) return 'weak';
        return 'sideways';
    }

    calculateAnnualizedVolatility(prices) {
        const returns = [];
        for (let i = 1; i < prices.length; i++) {
            returns.push((prices[i] - prices[i-1]) / prices[i-1]);
        }

        const mean = returns.reduce((sum, r) => sum + r, 0) / returns.length;
        const variance = returns.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) / returns.length;
        const stdDev = Math.sqrt(variance);

        return (stdDev * Math.sqrt(12) * 100).toFixed(2); // Annualized from monthly
    }

    calculateMaxDrawdown(prices) {
        let maxDrawdown = 0;
        let peak = prices[0];

        for (const price of prices) {
            if (price > peak) {
                peak = price;
            }
            const drawdown = (peak - price) / peak * 100;
            if (drawdown > maxDrawdown) {
                maxDrawdown = drawdown;
            }
        }

        return maxDrawdown.toFixed(2);
    }

    calculateSharpeRatio(cagr, volatility) {
        const riskFreeRate = 4.5;
        const annualReturn = parseFloat(cagr);
        const vol = parseFloat(volatility);

        if (!annualReturn || !vol || vol === 0) return null;

        return ((annualReturn - riskFreeRate) / vol).toFixed(2);
    }

    calculateCalmarRatio(cagr, maxDrawdown) {
        const annualReturn = parseFloat(cagr);
        const mdd = parseFloat(maxDrawdown);

        if (!annualReturn || !mdd || mdd === 0) return null;

        return (annualReturn / mdd).toFixed(2);
    }

    calculateAverage(observations) {
        if (!observations || observations.length === 0) return null;
        const validObs = observations.filter(o => o && o.value !== undefined);
        if (validObs.length === 0) return null;

        return validObs.reduce((sum, o) => sum + o.value, 0) / validObs.length;
    }

    calculateStdDev(values) {
        const mean = values.reduce((sum, v) => sum + v, 0) / values.length;
        const variance = values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / values.length;
        return Math.sqrt(variance);
    }

    formatDate(date) {
        return date.toISOString().split('T')[0];
    }

    getYearsAgo(years) {
        const date = new Date();
        date.setFullYear(date.getFullYear() - years);
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
    window.TimeframeDataFetcher_18_36_Months = TimeframeDataFetcher_18_36_Months;
}

console.log('✅ 18-36 Month Long-Term Investment Data Module Loaded');
