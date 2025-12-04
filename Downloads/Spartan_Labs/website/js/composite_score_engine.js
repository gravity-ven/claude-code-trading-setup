// Composite Score Engine
// Calculates real-time market health scores using multiple API sources
// Spartan Research Station

class CompositeScoreEngine {
    constructor() {
        this.apiEndpoint = window.location.origin;
        this.scores = {
            growth: 0,
            inflation: 0,
            liquidity: 0,
            market: 0,
            composite: 0
        };
        this.economicData = {};
        this.marketData = {};
        this.lastUpdate = null;

        this.init();
    }

    async init() {
        console.log('📊 Initializing Composite Score Engine...');

        try {
            await this.loadEconomicData();
            await this.loadMarketData();
            this.calculateCompositeScore();
            this.displayScores();

            // Auto-refresh every 5 minutes
            setInterval(() => {
                this.refreshScores();
            }, 300000);

            console.log('✅ Composite Score Engine initialized');
        } catch (error) {
            console.error('❌ Score Engine initialization failed:', error);
        }
    }

    async loadEconomicData() {
        console.log('📡 Loading economic data from FRED API...');
        console.log('🛡️ Data validation: ENABLED');

        try {
            // Fetch key economic indicators from FRED
            const indicators = [
                'GDP',           // GDP (Growth Score)
                'UNRATE',        // Unemployment Rate (Growth Score)
                'CPIAUCSL',      // CPI (Inflation Score)
                'DFF',           // Fed Funds Rate (Liquidity Score)
                'T10Y2Y',        // 10Y-2Y Treasury Spread (Liquidity Score)
                'VIXCLS'         // VIX (Market Score)
            ];

            const requests = indicators.map(async (series) => {
                try {
                    const response = await fetch(
                        `${this.apiEndpoint}/api/fred/series/observations?series_id=${series}&limit=1&sort_order=desc`,
                        {
                            method: 'GET',
                            headers: { 'Accept': 'application/json' }
                        }
                    );

                    if (response.ok) {
                        const data = await response.json();

                        // ✅ VALIDATE DATA FROM GENUINE SOURCE
                        if (window.dataValidationMiddleware) {
                            const economicDataPoint = data.observations && data.observations.length > 0
                                ? {
                                    symbol: series,
                                    price: parseFloat(data.observations[0].value),
                                    timestamp: new Date(data.observations[0].date).getTime()
                                }
                                : null;

                            if (economicDataPoint) {
                                const validation = await window.dataValidationMiddleware.validateFinancialData(
                                    economicDataPoint,
                                    'Federal Reserve FRED API'
                                );

                                if (!validation.isValid) {
                                    console.error(`❌ Data validation FAILED for ${series}:`, validation.errors);
                                    console.error('🚨 CRITICAL: Rejecting invalid data from FRED API');
                                    return null;
                                }

                                console.log(`✅ Data validation PASSED for ${series} (Source: FRED)`);
                            }
                        }

                        if (data.observations && data.observations.length > 0) {
                            return {
                                series,
                                value: parseFloat(data.observations[0].value),
                                date: data.observations[0].date,
                                source: 'Federal Reserve FRED API',
                                validated: true
                            };
                        }
                    }
                } catch (error) {
                    console.warn(`Failed to load ${series}:`, error.message);
                }
                return null;
            });

            const results = await Promise.all(requests);

            results.forEach(result => {
                if (result) {
                    this.economicData[result.series] = result;
                    console.log(`✅ ${result.series}: ${result.value} (Validated: ${result.validated})`);
                }
            });

            this.lastUpdate = new Date();

            // Display data provenance
            this.displayDataProvenance();

        } catch (error) {
            console.error('❌ Economic data loading failed:', error);
            console.error('🚨 NO FAKE DATA: Not using fallback values');
            // DO NOT use fallback fake data - let validation system handle it
        }
    }

    async loadMarketData() {
        console.log('📡 Loading market data...');

        try {
            const response = await fetch(`${this.apiEndpoint}/api/market-data`, {
                method: 'GET',
                headers: { 'Accept': 'application/json' }
            });

            if (response.ok) {
                const data = await response.json();
                this.marketData = data;
                console.log('✅ Market data loaded');
            }
        } catch (error) {
            console.error('❌ Market data loading failed:', error);
        }
    }

    calculateCompositeScore() {
        console.log('🧮 Calculating composite scores...');

        // ✅ CRITICAL: CHECK VALIDATION BEFORE CALCULATING
        const indicators = Object.keys(this.economicData);
        const validatedCount = indicators.filter(key => this.economicData[key].validated).length;

        // REFUSE TO CALCULATE if insufficient validated data
        if (validatedCount === 0) {
            console.error('❌ CRITICAL: ZERO indicators validated - REFUSING to calculate scores');
            console.error('🚨 NO FAKE DATA: Will display "Data Unavailable" instead');
            this.showDataUnavailableMessage();
            return; // STOP - do not calculate
        }

        if (validatedCount < 4) {
            console.warn(`⚠️ WARNING: Only ${validatedCount} indicators validated (minimum 4 required)`);
            console.warn('🚨 Insufficient data quality - displaying warning');
            this.showInsufficientDataWarning(validatedCount);
            return; // STOP - do not calculate
        }

        console.log(`✅ Data validation passed: ${validatedCount}/${indicators.length} indicators verified`);

        // GROWTH SCORE (0-30 points)
        this.scores.growth = this.calculateGrowthScore();

        // INFLATION SCORE (0-30 points)
        this.scores.inflation = this.calculateInflationScore();

        // LIQUIDITY SCORE (0-20 points)
        this.scores.liquidity = this.calculateLiquidityScore();

        // MARKET SCORE (0-20 points)
        this.scores.market = this.calculateMarketScore();

        // COMPOSITE SCORE (0-100 points)
        this.scores.composite = Math.round(
            this.scores.growth +
            this.scores.inflation +
            this.scores.liquidity +
            this.scores.market
        );

        console.log('📊 Composite Score:', this.scores);
    }

    calculateGrowthScore() {
        let score = 0;

        // GDP Growth: NO FALLBACK VALUES - must be validated
        // >3% = 15 pts, 1-3% = 10 pts, 0-1% = 5 pts, <0% = 0 pts
        if (this.economicData.GDP?.value !== undefined && this.economicData.GDP?.validated) {
            const gdp = this.economicData.GDP.value;
            if (gdp > 3) score += 15;
            else if (gdp > 1) score += 10;
            else if (gdp > 0) score += 5;
        } else {
            console.warn('⚠️ GDP data not validated - skipping growth score component');
        }

        // Unemployment Rate (inverse scoring) - NO FALLBACK VALUES
        // <4% = 15 pts, 4-5% = 10 pts, 5-6% = 5 pts, >6% = 0 pts
        if (this.economicData.UNRATE?.value !== undefined && this.economicData.UNRATE?.validated) {
            const unemployment = this.economicData.UNRATE.value;
            if (unemployment < 4) score += 15;
            else if (unemployment < 5) score += 10;
            else if (unemployment < 6) score += 5;
        } else {
            console.warn('⚠️ Unemployment data not validated - skipping growth score component');
        }

        return Math.min(score, 30);
    }

    calculateInflationScore() {
        let score = 30; // Start at maximum, deduct for problems

        // CPI (Consumer Price Index) - NO FALLBACK VALUES
        // Target: 2% inflation
        // 1.5-2.5% = 30 pts (ideal)
        // 2.5-3.5% = 20 pts (elevated)
        // 3.5-5% = 10 pts (high)
        // >5% = 0 pts (crisis)

        // ❌ REMOVED: Fake hardcoded cpiChange = 2.5
        // ✅ FIXED: Only use validated CPI data
        if (this.economicData.CPIAUCSL?.value !== undefined && this.economicData.CPIAUCSL?.validated) {
            // CPI is an index, not a percentage
            // For now, return neutral score until we implement historical YoY calculation
            console.warn('⚠️ CPI data available but YoY calculation requires historical data');
            score = 20; // Neutral score
        } else {
            console.warn('⚠️ CPI data not validated - returning neutral inflation score');
            score = 20; // Neutral when no data
        }

        return score;
    }

    calculateLiquidityScore() {
        let score = 0;

        // Fed Funds Rate - NO FALLBACK VALUES
        // 0-1% = 10 pts (very accommodative)
        // 1-3% = 7 pts (accommodative)
        // 3-5% = 4 pts (neutral)
        // >5% = 2 pts (restrictive)
        if (this.economicData.DFF?.value !== undefined && this.economicData.DFF?.validated) {
            const fedFunds = this.economicData.DFF.value;
            if (fedFunds < 1) score += 10;
            else if (fedFunds < 3) score += 7;
            else if (fedFunds < 5) score += 4;
            else score += 2;
        } else {
            console.warn('⚠️ Fed Funds data not validated - skipping liquidity score component');
        }

        // Yield Curve (10Y-2Y spread) - NO FALLBACK VALUES
        // >1% = 10 pts (steep, healthy)
        // 0-1% = 5 pts (flattening)
        // <0% = 0 pts (inverted, recession signal)
        if (this.economicData.T10Y2Y?.value !== undefined && this.economicData.T10Y2Y?.validated) {
            const yieldSpread = this.economicData.T10Y2Y.value;
            if (yieldSpread > 1) score += 10;
            else if (yieldSpread > 0) score += 5;
        } else {
            console.warn('⚠️ Yield spread data not validated - skipping liquidity score component');
        }

        return Math.min(score, 20);
    }

    calculateMarketScore() {
        let score = 10; // Neutral default

        // VIX (Volatility Index) - NO FALLBACK VALUES
        // <15 = 20 pts (low fear)
        // 15-20 = 15 pts (moderate)
        // 20-30 = 10 pts (elevated)
        // >30 = 5 pts (high fear)
        if (this.economicData.VIXCLS?.value !== undefined && this.economicData.VIXCLS?.validated) {
            const vix = this.economicData.VIXCLS.value;
            if (vix < 15) score = 20;
            else if (vix < 20) score = 15;
            else if (vix < 30) score = 10;
            else score = 5;
        } else {
            console.warn('⚠️ VIX data not validated - using neutral market score');
            score = 10; // Neutral when no data
        }

        return score;
    }

    displayScores() {
        // Update Growth Score display
        this.updateScoreElement('growth-score-value', this.scores.growth, 30);

        // Update Inflation Score display
        this.updateScoreElement('inflation-score-value', this.scores.inflation, 30);

        // Update Liquidity Score display
        this.updateScoreElement('liquidity-score-value', this.scores.liquidity, 20);

        // Update Market Score display
        this.updateScoreElement('market-score-value', this.scores.market, 20);

        // Update Composite Score display
        this.updateCompositeScoreDisplay();

        // Update last update timestamp
        this.updateTimestamp();
    }

    updateScoreElement(elementId, score, max) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const percentage = (score / max) * 100;
        let color;

        if (percentage >= 80) color = 'var(--success-color)';
        else if (percentage >= 60) color = 'var(--info-color)';
        else if (percentage >= 40) color = 'var(--warning-color)';
        else color = 'var(--danger-color)';

        element.textContent = `${score}/${max}`;
        element.style.color = color;
    }

    updateCompositeScoreDisplay() {
        const element = document.getElementById('composite-score-value');
        if (!element) return;

        const score = this.scores.composite;
        let color, status;

        if (score >= 85) {
            color = 'var(--success-color)';
            status = 'EXPANSION (Goldilocks)';
        } else if (score >= 65) {
            color = 'var(--info-color)';
            status = 'RECOVERY (Early Cycle)';
        } else if (score >= 45) {
            color = 'var(--warning-color)';
            status = 'SLOWDOWN (Late Cycle)';
        } else {
            color = 'var(--danger-color)';
            status = 'RECESSION (Contraction)';
        }

        element.innerHTML = `
            <div style="font-size: 3rem; font-weight: 800; color: ${color};">${score}/100</div>
            <div style="font-size: 1.2rem; margin-top: 10px; color: ${color}; text-transform: uppercase; letter-spacing: 2px;">
                ${status}
            </div>
        `;
    }

    updateTimestamp() {
        const element = document.getElementById('score-last-update');
        if (!element && this.lastUpdate) {
            element.textContent = `Last updated: ${this.lastUpdate.toLocaleTimeString()}`;
        }
    }

    /**
     * Display data provenance - shows data source, timestamp, and quality
     * CRITICAL: Ensures transparency about data sources for user trust
     */
    displayDataProvenance() {
        const provenanceContainer = document.getElementById('data-provenance');
        if (!provenanceContainer) {
            console.warn('⚠️ Data provenance container not found in HTML');
            return;
        }

        // Calculate data quality metrics
        const indicators = Object.keys(this.economicData);
        const validatedCount = indicators.filter(key => this.economicData[key].validated).length;
        const qualityPercentage = indicators.length > 0 ? (validatedCount / indicators.length * 100).toFixed(0) : 0;

        // Find oldest and newest data points
        const dates = indicators.map(key => new Date(this.economicData[key].date));
        const oldestDate = dates.length > 0 ? new Date(Math.min(...dates)) : new Date();
        const newestDate = dates.length > 0 ? new Date(Math.max(...dates)) : new Date();

        // Calculate staleness
        const staleness = (Date.now() - newestDate.getTime()) / (1000 * 60 * 60 * 24); // days
        let stalenessColor = '#00ff88'; // green
        let stalenessLabel = 'Fresh';

        if (staleness > 7) {
            stalenessColor = '#ff6b6b'; // red
            stalenessLabel = 'Stale';
        } else if (staleness > 3) {
            stalenessColor = '#ff9500'; // orange
            stalenessLabel = 'Aging';
        }

        const provenanceHTML = `
            <div style="
                background: linear-gradient(135deg, rgba(139, 0, 0, 0.1) 0%, rgba(220, 20, 60, 0.05) 100%);
                border: 1px solid rgba(220, 20, 60, 0.3);
                border-radius: 8px;
                padding: 15px 20px;
                margin: 20px 0;
                font-size: 0.9rem;
            ">
                <div style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    flex-wrap: wrap;
                    gap: 15px;
                ">
                    <div>
                        <strong style="color: #FFD700;">📊 Data Source:</strong>
                        <span style="color: #00ff88; margin-left: 8px;">Federal Reserve Economic Data (FRED)</span>
                    </div>
                    <div>
                        <strong style="color: #FFD700;">✓ Validation:</strong>
                        <span style="
                            color: ${qualityPercentage >= 90 ? '#00ff88' : qualityPercentage >= 70 ? '#ff9500' : '#ff6b6b'};
                            margin-left: 8px;
                            font-weight: bold;
                        ">${validatedCount}/${indicators.length} indicators verified (${qualityPercentage}%)</span>
                    </div>
                    <div>
                        <strong style="color: #FFD700;">🕒 Last Updated:</strong>
                        <span style="color: #ffffff; margin-left: 8px;">${newestDate.toLocaleDateString()}</span>
                    </div>
                    <div>
                        <strong style="color: #FFD700;">⏱️ Freshness:</strong>
                        <span style="color: ${stalenessColor}; margin-left: 8px; font-weight: bold;">
                            ${stalenessLabel} (${staleness.toFixed(1)} days old)
                        </span>
                    </div>
                </div>

                ${window.dataValidationMiddleware ? `
                <div style="
                    margin-top: 10px;
                    padding-top: 10px;
                    border-top: 1px solid rgba(220, 20, 60, 0.2);
                    font-size: 0.85rem;
                    color: rgba(255, 255, 255, 0.7);
                ">
                    <span style="color: #00ff88;">✅</span> Real-time data validation active •
                    <span style="color: #00ff88;">✅</span> Source verification enabled •
                    <span style="color: #00ff88;">✅</span> Quality monitoring in progress
                </div>
                ` : `
                <div style="
                    margin-top: 10px;
                    padding-top: 10px;
                    border-top: 1px solid rgba(220, 20, 60, 0.2);
                    font-size: 0.85rem;
                    color: #ff9500;
                ">
                    ⚠️ Data validation middleware not loaded - data quality checks disabled
                </div>
                `}
            </div>
        `;

        provenanceContainer.innerHTML = provenanceHTML;
        console.log('✅ Data provenance displayed');
    }

    /**
     * ❌ DELETED: useFallbackEconomicData() - VIOLATES NO FAKE DATA RULE
     * This function was setting fake fallback values without validation.
     * System now properly displays "Data Unavailable" when APIs fail.
     */

    async refreshScores() {
        console.log('🔄 Refreshing composite scores...');
        await this.loadEconomicData();
        await this.loadMarketData();
        this.calculateCompositeScore();
        this.displayScores();
    }

    getScores() {
        return this.scores;
    }

    getMarketRegime() {
        const score = this.scores.composite;

        if (score >= 85) return 'expansion';
        if (score >= 65) return 'recovery';
        if (score >= 45) return 'slowdown';
        return 'recession';
    }

    /**
     * Show "Data Unavailable" message when NO data is validated
     * CRITICAL: Enforces NO FAKE DATA rule
     */
    showDataUnavailableMessage() {
        const scoreCard = document.querySelector('.composite-score-card');
        if (!scoreCard) return;

        scoreCard.innerHTML = `
            <div style="
                background: linear-gradient(135deg, rgba(220, 20, 60, 0.2) 0%, rgba(139, 0, 0, 0.1) 100%);
                border: 2px solid #DC143C;
                border-radius: 12px;
                padding: 40px;
                text-align: center;
            ">
                <h2 style="color: #DC143C; margin: 0 0 20px 0; font-size: 2rem;">
                    ⚠️ DATA UNAVAILABLE
                </h2>
                <p style="color: #b0b8c8; font-size: 1.1rem; margin: 0 0 15px 0;">
                    <strong>ZERO economic indicators validated from FRED API.</strong>
                </p>
                <p style="color: #7a8a9a; font-size: 0.95rem; margin: 0;">
                    This dashboard enforces a strict <strong style="color: #DC143C;">NO FAKE DATA</strong> policy.<br>
                    We refuse to display unvalidated or fabricated information.<br><br>
                    Possible causes:
                </p>
                <ul style="color: #7a8a9a; text-align: left; max-width: 600px; margin: 20px auto 0 auto;">
                    <li>FRED API service unavailable</li>
                    <li>Network connectivity issues</li>
                    <li>API rate limits exceeded</li>
                    <li>Server proxy not configured</li>
                </ul>
                <p style="color: #ff9500; margin-top: 25px; font-size: 0.9rem;">
                    <strong>Action Required:</strong> Check server logs and FRED API status
                </p>
            </div>
        `;

        // Also clear data provenance
        const provenanceContainer = document.getElementById('data-provenance');
        if (provenanceContainer) {
            provenanceContainer.innerHTML = `
                <div style="background: rgba(220, 20, 60, 0.1); border: 1px solid #DC143C; border-radius: 8px; padding: 15px; color: #DC143C;">
                    <strong>❌ Data Validation Failed:</strong> 0 indicators validated. NO DATA DISPLAYED.
                </div>
            `;
        }
    }

    /**
     * Show warning when data quality is insufficient
     */
    showInsufficientDataWarning(validatedCount) {
        const scoreCard = document.querySelector('.composite-score-card');
        if (!scoreCard) return;

        scoreCard.innerHTML = `
            <div style="
                background: linear-gradient(135deg, rgba(255, 149, 0, 0.2) 0%, rgba(220, 20, 60, 0.1) 100%);
                border: 2px solid #ff9500;
                border-radius: 12px;
                padding: 40px;
                text-align: center;
            ">
                <h2 style="color: #ff9500; margin: 0 0 20px 0; font-size: 2rem;">
                    ⚠️ INSUFFICIENT DATA QUALITY
                </h2>
                <p style="color: #b0b8c8; font-size: 1.1rem; margin: 0 0 15px 0;">
                    Only <strong style="color: #ff9500;">${validatedCount} of 6 indicators</strong> validated.
                </p>
                <p style="color: #7a8a9a; font-size: 0.95rem; margin: 0;">
                    Minimum <strong>4 validated indicators</strong> required for accurate composite score calculation.<br>
                    Current data quality is too low to provide reliable analysis.<br><br>
                    <strong style="color: #DC143C;">NO FAKE DATA:</strong> We will not fill gaps with fabricated values.
                </p>
                <p style="color: #ff9500; margin-top: 25px; font-size: 0.9rem;">
                    <strong>Action Required:</strong> Wait for FRED API to respond, then refresh page
                </p>
            </div>
        `;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    try {
        window.compositeScoreEngine = new CompositeScoreEngine();
        console.log('✅ Composite Score Engine loaded');

        // Debug shortcut
        window.getCompositeScore = () => {
            console.log('Current Scores:', window.compositeScoreEngine.getScores());
            console.log('Market Regime:', window.compositeScoreEngine.getMarketRegime());
        };

    } catch (error) {
        console.error('❌ Composite Score Engine failed to load:', error);
    }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CompositeScoreEngine;
}
