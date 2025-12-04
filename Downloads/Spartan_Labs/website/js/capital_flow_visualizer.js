/**
 * Capital Flow Visualizer
 * Shows real-time capital flows across markets, segments, and countries
 * STRICT NO FAKE DATA POLICY - All data from verified sources
 *
 * @author Spartan Labs
 * @version 1.0.0
 */

class CapitalFlowVisualizer {
    constructor() {
        this.fredClient = null;  // Will be initialized if FredApiClient available
        this.flows = {
            regions: {},      // US, Europe, Asia, Emerging Markets
            sectors: {},      // Technology, Finance, Healthcare, etc.
            segments: {},     // Equities, Bonds, Commodities, Currencies, Crypto
            countries: {}     // Individual country flows
        };
        this.lastUpdate = null;
        this.isInitialized = false;
    }

    async init() {
        console.log('🌊 Initializing Capital Flow Visualizer...');

        try {
            // Initialize FRED API client if available
            if (typeof FredApiClient !== 'undefined') {
                this.fredClient = new FredApiClient();
                console.log('✅ FRED API client initialized');
            }

            // Load capital flow data
            await this.loadCapitalFlows();

            // Display visualizations
            this.displayFlowVisualizations();

            // Auto-refresh every 5 minutes
            setInterval(() => {
                this.refreshFlows();
            }, 300000);

            this.isInitialized = true;
            console.log('✅ Capital Flow Visualizer initialized');

        } catch (error) {
            console.error('❌ Capital Flow Visualizer initialization failed:', error);
        }
    }

    async loadCapitalFlows() {
        console.log('📡 Loading capital flow data from verified sources...');

        try {
            // Load data in parallel from multiple real sources
            await Promise.all([
                this.loadRegionalFlows(),
                this.loadSectorFlows(),
                this.loadSegmentFlows(),
                this.loadCountryFlows()
            ]);

            this.lastUpdate = new Date();
            console.log('✅ Capital flow data loaded successfully');

        } catch (error) {
            console.error('❌ Failed to load capital flow data:', error);
        }
    }

    /**
     * Load regional capital flows (US, Europe, Asia, Emerging Markets)
     * Uses real ETF prices as proxy for regional capital allocation
     */
    async loadRegionalFlows() {
        console.log('🌎 Loading regional capital flows...');

        // Regional ETFs as proxies for capital flows
        const regionalProxies = [
            { region: 'US', symbol: 'SPY', name: 'S&P 500 ETF' },
            { region: 'Europe', symbol: 'VGK', name: 'FTSE Europe ETF' },
            { region: 'Asia', symbol: 'VPL', name: 'FTSE Pacific ETF' },
            { region: 'Emerging', symbol: 'EEM', name: 'Emerging Markets ETF' },
            { region: 'China', symbol: 'FXI', name: 'China Large-Cap ETF' },
            { region: 'Japan', symbol: 'EWJ', name: 'Japan ETF' }
        ];

        for (const proxy of regionalProxies) {
            try {
                // Fetch real-time price data from Yahoo Finance API
                const response = await fetch(`/api/yahoo/${proxy.symbol}`);

                if (response.ok) {
                    const data = await response.json();

                    // Calculate flow indicator from price change
                    if (data && data.chart && data.chart.result) {
                        const result = data.chart.result[0];
                        const quotes = result.indicators.quote[0];
                        const closes = quotes.close.filter(c => c !== null);

                        if (closes.length >= 2) {
                            const currentPrice = closes[closes.length - 1];
                            const previousPrice = closes[closes.length - 2];
                            const priceChange = ((currentPrice - previousPrice) / previousPrice) * 100;

                            this.flows.regions[proxy.region] = {
                                symbol: proxy.symbol,
                                name: proxy.name,
                                price: currentPrice.toFixed(2),
                                change: priceChange.toFixed(2),
                                flow: this.calculateFlowIntensity(priceChange),
                                validated: true,
                                source: 'Yahoo Finance API',
                                timestamp: new Date()
                            };

                            console.log(`✅ ${proxy.region}: ${priceChange > 0 ? 'Inflow' : 'Outflow'} (${priceChange.toFixed(2)}%)`);
                        }
                    }
                }
            } catch (error) {
                console.warn(`⚠️ Failed to load ${proxy.region} flow data:`, error.message);
                // Do NOT set fake data - leave undefined
            }
        }
    }

    /**
     * Load sector capital flows (Technology, Finance, Healthcare, Energy, etc.)
     * Uses real sector ETF prices
     */
    async loadSectorFlows() {
        console.log('🏭 Loading sector capital flows...');

        const sectorETFs = [
            { sector: 'Technology', symbol: 'XLK' },
            { sector: 'Finance', symbol: 'XLF' },
            { sector: 'Healthcare', symbol: 'XLV' },
            { sector: 'Energy', symbol: 'XLE' },
            { sector: 'Industrials', symbol: 'XLI' },
            { sector: 'Consumer Discretionary', symbol: 'XLY' },
            { sector: 'Consumer Staples', symbol: 'XLP' },
            { sector: 'Utilities', symbol: 'XLU' },
            { sector: 'Real Estate', symbol: 'XLRE' },
            { sector: 'Materials', symbol: 'XLB' },
            { sector: 'Communications', symbol: 'XLC' }
        ];

        for (const etf of sectorETFs) {
            try {
                const response = await fetch(`/api/yahoo/${etf.symbol}`);

                if (response.ok) {
                    const data = await response.json();

                    if (data && data.chart && data.chart.result) {
                        const result = data.chart.result[0];
                        const quotes = result.indicators.quote[0];
                        const closes = quotes.close.filter(c => c !== null);

                        if (closes.length >= 2) {
                            const currentPrice = closes[closes.length - 1];
                            const previousPrice = closes[closes.length - 2];
                            const priceChange = ((currentPrice - previousPrice) / previousPrice) * 100;

                            this.flows.sectors[etf.sector] = {
                                symbol: etf.symbol,
                                price: currentPrice.toFixed(2),
                                change: priceChange.toFixed(2),
                                flow: this.calculateFlowIntensity(priceChange),
                                validated: true,
                                source: 'Yahoo Finance API',
                                timestamp: new Date()
                            };

                            console.log(`✅ ${etf.sector}: ${priceChange.toFixed(2)}%`);
                        }
                    }
                }
            } catch (error) {
                console.warn(`⚠️ Failed to load ${etf.sector} flow data:`, error.message);
                // Do NOT set fake data
            }
        }
    }

    /**
     * Load market segment flows (Equities, Bonds, Commodities, Currencies, Crypto)
     * Uses representative ETFs and indices
     */
    async loadSegmentFlows() {
        console.log('📊 Loading market segment flows...');

        const segmentProxies = [
            { segment: 'Equities', symbol: 'VTI', name: 'Total Stock Market' },
            { segment: 'Bonds', symbol: 'AGG', name: 'Aggregate Bond' },
            { segment: 'Commodities', symbol: 'DBC', name: 'Commodity Index' },
            { segment: 'Gold', symbol: 'GLD', name: 'Gold ETF' },
            { segment: 'Oil', symbol: 'USO', name: 'Oil Fund' },
            { segment: 'Real Estate', symbol: 'VNQ', name: 'REIT ETF' }
        ];

        for (const proxy of segmentProxies) {
            try {
                const response = await fetch(`/api/yahoo/${proxy.symbol}`);

                if (response.ok) {
                    const data = await response.json();

                    if (data && data.chart && data.chart.result) {
                        const result = data.chart.result[0];
                        const quotes = result.indicators.quote[0];
                        const closes = quotes.close.filter(c => c !== null);

                        if (closes.length >= 2) {
                            const currentPrice = closes[closes.length - 1];
                            const previousPrice = closes[closes.length - 2];
                            const priceChange = ((currentPrice - previousPrice) / previousPrice) * 100;

                            this.flows.segments[proxy.segment] = {
                                symbol: proxy.symbol,
                                name: proxy.name,
                                price: currentPrice.toFixed(2),
                                change: priceChange.toFixed(2),
                                flow: this.calculateFlowIntensity(priceChange),
                                validated: true,
                                source: 'Yahoo Finance API',
                                timestamp: new Date()
                            };

                            console.log(`✅ ${proxy.segment}: ${priceChange.toFixed(2)}%`);
                        }
                    }
                }
            } catch (error) {
                console.warn(`⚠️ Failed to load ${proxy.segment} flow data:`, error.message);
                // Do NOT set fake data
            }
        }
    }

    /**
     * Load country-specific flows using country ETFs
     */
    async loadCountryFlows() {
        console.log('🌍 Loading country-specific capital flows...');

        const countryETFs = [
            { country: 'United States', symbol: 'SPY' },
            { country: 'China', symbol: 'FXI' },
            { country: 'Japan', symbol: 'EWJ' },
            { country: 'United Kingdom', symbol: 'EWU' },
            { country: 'Germany', symbol: 'EWG' },
            { country: 'France', symbol: 'EWQ' },
            { country: 'Canada', symbol: 'EWC' },
            { country: 'Australia', symbol: 'EWA' },
            { country: 'South Korea', symbol: 'EWY' },
            { country: 'India', symbol: 'INDA' },
            { country: 'Brazil', symbol: 'EWZ' },
            { country: 'Mexico', symbol: 'EWW' },
            { country: 'South Africa', symbol: 'EZA' },
            { country: 'Switzerland', symbol: 'EWL' },
            { country: 'Spain', symbol: 'EWP' },
            { country: 'Italy', symbol: 'EWI' }
        ];

        for (const etf of countryETFs) {
            try {
                const response = await fetch(`/api/yahoo/${etf.symbol}`);

                if (response.ok) {
                    const data = await response.json();

                    if (data && data.chart && data.chart.result) {
                        const result = data.chart.result[0];
                        const quotes = result.indicators.quote[0];
                        const closes = quotes.close.filter(c => c !== null);

                        if (closes.length >= 2) {
                            const currentPrice = closes[closes.length - 1];
                            const previousPrice = closes[closes.length - 2];
                            const priceChange = ((currentPrice - previousPrice) / previousPrice) * 100;

                            this.flows.countries[etf.country] = {
                                symbol: etf.symbol,
                                price: currentPrice.toFixed(2),
                                change: priceChange.toFixed(2),
                                flow: this.calculateFlowIntensity(priceChange),
                                validated: true,
                                source: 'Yahoo Finance API',
                                timestamp: new Date()
                            };
                        }
                    }
                }
            } catch (error) {
                console.warn(`⚠️ Failed to load ${etf.country} flow data:`, error.message);
                // Do NOT set fake data
            }
        }
    }

    /**
     * Calculate flow intensity from price change
     * Returns: 'Strong Inflow', 'Moderate Inflow', 'Weak Inflow', 'Neutral', 'Weak Outflow', etc.
     */
    calculateFlowIntensity(priceChange) {
        const abs = Math.abs(priceChange);

        if (priceChange > 2) return 'Strong Inflow';
        if (priceChange > 1) return 'Moderate Inflow';
        if (priceChange > 0.3) return 'Weak Inflow';
        if (priceChange > -0.3) return 'Neutral';
        if (priceChange > -1) return 'Weak Outflow';
        if (priceChange > -2) return 'Moderate Outflow';
        return 'Strong Outflow';
    }

    /**
     * Display capital flow visualizations
     */
    displayFlowVisualizations() {
        console.log('🎨 Displaying capital flow visualizations...');

        // Display regional flows
        this.displayRegionalFlows();

        // Display sector flows
        this.displaySectorFlows();

        // Display segment flows
        this.displaySegmentFlows();

        // Display country flows
        this.displayCountryFlows();

        // Display flow summary
        this.displayFlowSummary();
    }

    displayRegionalFlows() {
        const container = document.getElementById('regional-flows');
        if (!container) {
            console.warn('⚠️ Regional flows container not found');
            return;
        }

        const regions = Object.keys(this.flows.regions);
        if (regions.length === 0) {
            container.innerHTML = '<p style="color: #ff6b6b;">⚠️ Regional flow data unavailable</p>';
            return;
        }

        let html = '<h3 style="color: #FFD700; margin-bottom: 20px;">🌎 Regional Capital Flows</h3>';
        html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;">';

        regions.forEach(region => {
            const flow = this.flows.regions[region];
            const isInflow = parseFloat(flow.change) > 0;
            const color = isInflow ? '#00ff88' : '#ff6b6b';
            const arrow = isInflow ? '↗' : '↘';

            html += `
                <div style="
                    background: linear-gradient(135deg, ${isInflow ? 'rgba(0, 255, 136, 0.1)' : 'rgba(255, 107, 107, 0.1)'} 0%, rgba(18, 32, 58, 0.5) 100%);
                    border: 1px solid ${color};
                    border-radius: 8px;
                    padding: 15px;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <h4 style="margin: 0; color: #FFD700;">${region}</h4>
                        <span style="font-size: 1.5rem; color: ${color};">${arrow}</span>
                    </div>
                    <div style="font-size: 0.9rem; color: #b0b8c8;">
                        <div style="margin: 5px 0;"><strong>${flow.symbol}:</strong> $${flow.price}</div>
                        <div style="margin: 5px 0; color: ${color};">
                            <strong>Change:</strong> ${flow.change > 0 ? '+' : ''}${flow.change}%
                        </div>
                        <div style="margin: 5px 0; color: #7a8a9a;">
                            <strong>Flow:</strong> ${flow.flow}
                        </div>
                    </div>
                    <div style="margin-top: 10px; font-size: 0.75rem; color: #7a8a9a;">
                        Source: ${flow.source} | ${flow.timestamp.toLocaleTimeString()}
                    </div>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;
    }

    displaySectorFlows() {
        const container = document.getElementById('sector-flows');
        if (!container) {
            console.warn('⚠️ Sector flows container not found');
            return;
        }

        const sectors = Object.keys(this.flows.sectors);
        if (sectors.length === 0) {
            container.innerHTML = '<p style="color: #ff6b6b;">⚠️ Sector flow data unavailable</p>';
            return;
        }

        // Sort sectors by flow strength (price change)
        const sortedSectors = sectors.sort((a, b) => {
            return parseFloat(this.flows.sectors[b].change) - parseFloat(this.flows.sectors[a].change);
        });

        let html = '<h3 style="color: #FFD700; margin-bottom: 20px; margin-top: 40px;">🏭 Sector Capital Flows</h3>';
        html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 12px;">';

        sortedSectors.forEach(sector => {
            const flow = this.flows.sectors[sector];
            const isInflow = parseFloat(flow.change) > 0;
            const color = isInflow ? '#00ff88' : '#ff6b6b';
            const barWidth = Math.min(Math.abs(parseFloat(flow.change)) * 30, 100);

            html += `
                <div style="
                    background: rgba(18, 32, 58, 0.5);
                    border: 1px solid rgba(220, 20, 60, 0.3);
                    border-radius: 6px;
                    padding: 12px;
                ">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="font-size: 0.9rem; font-weight: bold;">${sector}</span>
                        <span style="color: ${color}; font-weight: bold;">${flow.change > 0 ? '+' : ''}${flow.change}%</span>
                    </div>
                    <div style="
                        width: 100%;
                        height: 8px;
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 4px;
                        overflow: hidden;
                    ">
                        <div style="
                            width: ${barWidth}%;
                            height: 100%;
                            background: ${color};
                            transition: width 0.5s ease;
                        "></div>
                    </div>
                    <div style="margin-top: 8px; font-size: 0.75rem; color: #7a8a9a;">
                        ${flow.symbol}: $${flow.price} | ${flow.flow}
                    </div>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;
    }

    displaySegmentFlows() {
        const container = document.getElementById('segment-flows');
        if (!container) {
            console.warn('⚠️ Segment flows container not found');
            return;
        }

        const segments = Object.keys(this.flows.segments);
        if (segments.length === 0) {
            container.innerHTML = '<p style="color: #ff6b6b;">⚠️ Market segment flow data unavailable</p>';
            return;
        }

        let html = '<h3 style="color: #FFD700; margin-bottom: 20px; margin-top: 40px;">📊 Market Segment Flows</h3>';
        html += '<div style="display: flex; flex-wrap: wrap; gap: 15px; justify-content: space-around;">';

        segments.forEach(segment => {
            const flow = this.flows.segments[segment];
            const isInflow = parseFloat(flow.change) > 0;
            const color = isInflow ? '#00ff88' : '#ff6b6b';

            html += `
                <div style="
                    background: radial-gradient(circle at top, ${isInflow ? 'rgba(0, 255, 136, 0.2)' : 'rgba(255, 107, 107, 0.2)'}, rgba(18, 32, 58, 0.8));
                    border: 2px solid ${color};
                    border-radius: 12px;
                    padding: 20px;
                    min-width: 180px;
                    text-align: center;
                ">
                    <div style="font-size: 2rem; margin-bottom: 10px;">${this.getSegmentIcon(segment)}</div>
                    <h4 style="margin: 0 0 10px 0; color: #FFD700;">${segment}</h4>
                    <div style="font-size: 1.5rem; color: ${color}; font-weight: bold; margin: 10px 0;">
                        ${flow.change > 0 ? '+' : ''}${flow.change}%
                    </div>
                    <div style="font-size: 0.85rem; color: #b0b8c8; margin: 8px 0;">
                        ${flow.name} (${flow.symbol})
                    </div>
                    <div style="font-size: 0.9rem; color: ${color}; margin-top: 10px;">
                        ${flow.flow}
                    </div>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;
    }

    displayCountryFlows() {
        const container = document.getElementById('country-flows');
        if (!container) {
            console.warn('⚠️ Country flows container not found');
            return;
        }

        const countries = Object.keys(this.flows.countries);
        if (countries.length === 0) {
            container.innerHTML = '<p style="color: #ff6b6b;">⚠️ Country flow data unavailable</p>';
            return;
        }

        // Sort countries by flow strength
        const sortedCountries = countries.sort((a, b) => {
            return parseFloat(this.flows.countries[b].change) - parseFloat(this.flows.countries[a].change);
        });

        let html = '<h3 style="color: #FFD700; margin-bottom: 20px; margin-top: 40px;">🌍 Country-Specific Flows</h3>';
        html += '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px;">';

        sortedCountries.forEach(country => {
            const flow = this.flows.countries[country];
            const isInflow = parseFloat(flow.change) > 0;
            const color = isInflow ? '#00ff88' : '#ff6b6b';

            html += `
                <div style="
                    background: rgba(18, 32, 58, 0.3);
                    border-left: 4px solid ${color};
                    padding: 10px;
                    border-radius: 4px;
                ">
                    <div style="font-weight: bold; margin-bottom: 5px;">${country}</div>
                    <div style="color: ${color}; font-size: 1.1rem; margin: 5px 0;">
                        ${flow.change > 0 ? '+' : ''}${flow.change}%
                    </div>
                    <div style="font-size: 0.75rem; color: #7a8a9a;">
                        ${flow.symbol} | ${flow.flow}
                    </div>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;
    }

    displayFlowSummary() {
        const container = document.getElementById('flow-summary');
        if (!container) return;

        const totalRegions = Object.keys(this.flows.regions).length;
        const totalSectors = Object.keys(this.flows.sectors).length;
        const totalSegments = Object.keys(this.flows.segments).length;
        const totalCountries = Object.keys(this.flows.countries).length;

        const inflowRegions = Object.values(this.flows.regions).filter(f => parseFloat(f.change) > 0).length;
        const inflowSectors = Object.values(this.flows.sectors).filter(f => parseFloat(f.change) > 0).length;

        container.innerHTML = `
            <div style="
                background: linear-gradient(135deg, rgba(220, 20, 60, 0.1) 0%, rgba(139, 0, 0, 0.05) 100%);
                border: 1px solid #DC143C;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 30px;
            ">
                <h3 style="color: #FFD700; margin: 0 0 15px 0;">📈 Capital Flow Summary</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                    <div>
                        <div style="font-size: 0.9rem; color: #7a8a9a;">Regions Tracked</div>
                        <div style="font-size: 1.5rem; color: #00ff88; font-weight: bold;">${totalRegions}</div>
                        <div style="font-size: 0.8rem; color: #b0b8c8;">${inflowRegions} showing inflows</div>
                    </div>
                    <div>
                        <div style="font-size: 0.9rem; color: #7a8a9a;">Sectors Tracked</div>
                        <div style="font-size: 1.5rem; color: #00ff88; font-weight: bold;">${totalSectors}</div>
                        <div style="font-size: 0.8rem; color: #b0b8c8;">${inflowSectors} showing inflows</div>
                    </div>
                    <div>
                        <div style="font-size: 0.9rem; color: #7a8a9a;">Market Segments</div>
                        <div style="font-size: 1.5rem; color: #00ff88; font-weight: bold;">${totalSegments}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.9rem; color: #7a8a9a;">Countries Tracked</div>
                        <div style="font-size: 1.5rem; color: #00ff88; font-weight: bold;">${totalCountries}</div>
                    </div>
                </div>
                <div style="margin-top: 15px; font-size: 0.85rem; color: #7a8a9a;">
                    <strong>Last Update:</strong> ${this.lastUpdate.toLocaleString()} |
                    <strong>Data Source:</strong> Real-time market data from Yahoo Finance API
                </div>
            </div>
        `;
    }

    getSegmentIcon(segment) {
        const icons = {
            'Equities': '📈',
            'Bonds': '📜',
            'Commodities': '🌾',
            'Gold': '🥇',
            'Oil': '🛢️',
            'Real Estate': '🏢'
        };
        return icons[segment] || '💹';
    }

    async refreshFlows() {
        console.log('🔄 Refreshing capital flows...');
        await this.loadCapitalFlows();
        this.displayFlowVisualizations();
    }
}

// Initialize on page load if containers exist
if (typeof window !== 'undefined') {
    window.addEventListener('DOMContentLoaded', () => {
        const flowContainer = document.getElementById('capital-flow-container');
        if (flowContainer) {
            const visualizer = new CapitalFlowVisualizer();
            visualizer.init();
            window.capitalFlowVisualizer = visualizer; // Expose globally
        }
    });
}
