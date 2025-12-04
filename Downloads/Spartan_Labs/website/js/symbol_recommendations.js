// Symbol Recommendations Engine
// Generates buy/sell/hold recommendations for 50+ symbols
// Based on market regime, sector, and VIX correlation
// Spartan Research Station

class SymbolRecommendations {
    constructor() {
        this.apiEndpoint = window.location.origin;
        this.symbols = [];
        this.recommendations = [];
        this.sortColumn = 'recommendation'; // Default sort
        this.sortDirection = 'asc';

        this.init();
    }

    async init() {
        console.log('💡 Initializing Symbol Recommendations Engine...');

        try {
            await this.loadTopSymbols();
            await this.generateRecommendations();
            this.displayRecommendations();
            this.setupSorting();

            console.log('✅ Symbol Recommendations initialized');
        } catch (error) {
            console.error('❌ Recommendations initialization failed:', error);
        }
    }

    async loadTopSymbols() {
        console.log('📡 Loading top 50 symbols...');

        try {
            // Load top symbols from database
            const response = await fetch(
                `${this.apiEndpoint}/api/db/symbols?limit=100`,
                {
                    method: 'GET',
                    headers: { 'Accept': 'application/json' }
                }
            );

            if (response.ok) {
                const data = await response.json();
                const allSymbols = data.symbols || data || [];

                // Filter and prioritize high-quality symbols
                this.symbols = this.selectTopSymbols(allSymbols);

                console.log(`✅ Loaded ${this.symbols.length} symbols for analysis`);
            } else {
                throw new Error(`HTTP ${response.status}`);
            }

        } catch (error) {
            console.error('❌ Symbol loading failed:', error);
            this.useFallbackSymbols();
        }
    }

    selectTopSymbols(allSymbols) {
        // Priority list of top symbols to analyze
        const prioritySymbols = [
            // Mega-cap Tech
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA',
            // Finance
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'V', 'MA',
            // Healthcare
            'UNH', 'JNJ', 'LLY', 'ABBV', 'MRK', 'PFE',
            // Consumer
            'WMT', 'HD', 'COST', 'MCD', 'NKE', 'SBUX',
            // Energy
            'XOM', 'CVX', 'COP', 'SLB',
            // Indices ETFs
            'SPY', 'QQQ', 'IWM', 'DIA',
            // Sector ETFs
            'XLK', 'XLF', 'XLE', 'XLV', 'XLI',
            // Safe Haven
            'GLD', 'TLT', 'VXX',
            // Crypto
            'BTCUSD', 'ETHUSD',
            // International
            'BABA', 'TSM', 'SHEL.L', 'SAP.DE'
        ];

        const selected = [];
        const seen = new Set();

        // First, add priority symbols
        for (const symbol of prioritySymbols) {
            const found = allSymbols.find(s => s.symbol === symbol);
            if (found && !seen.has(found.symbol)) {
                selected.push(found);
                seen.add(found.symbol);
            }
        }

        // Fill remaining slots with database symbols
        for (const symbol of allSymbols) {
            if (selected.length >= 50) break;
            if (!seen.has(symbol.symbol) && symbol.type === 'Stock') {
                selected.push(symbol);
                seen.add(symbol.symbol);
            }
        }

        return selected.slice(0, 50);
    }

    useFallbackSymbols() {
        console.log('⚠️ Using fallback symbol list');

        this.symbols = [
            { symbol: 'AAPL', name: 'Apple Inc.', type: 'Stock', sector: 'Technology', exchange: 'NASDAQ' },
            { symbol: 'MSFT', name: 'Microsoft Corporation', type: 'Stock', sector: 'Technology', exchange: 'NASDAQ' },
            { symbol: 'GOOGL', name: 'Alphabet Inc.', type: 'Stock', sector: 'Technology', exchange: 'NASDAQ' },
            { symbol: 'AMZN', name: 'Amazon.com Inc.', type: 'Stock', sector: 'Consumer', exchange: 'NASDAQ' },
            { symbol: 'META', name: 'Meta Platforms Inc.', type: 'Stock', sector: 'Technology', exchange: 'NASDAQ' },
            { symbol: 'NVDA', name: 'NVIDIA Corporation', type: 'Stock', sector: 'Technology', exchange: 'NASDAQ' },
            { symbol: 'TSLA', name: 'Tesla Inc.', type: 'Stock', sector: 'Consumer', exchange: 'NASDAQ' },
            { symbol: 'JPM', name: 'JPMorgan Chase', type: 'Stock', sector: 'Financial', exchange: 'NYSE' },
            { symbol: 'V', name: 'Visa Inc.', type: 'Stock', sector: 'Financial', exchange: 'NYSE' },
            { symbol: 'WMT', name: 'Walmart Inc.', type: 'Stock', sector: 'Consumer', exchange: 'NYSE' },
            { symbol: 'SPY', name: 'SPDR S&P 500 ETF', type: 'ETF', sector: 'Index', exchange: 'NYSE' },
            { symbol: 'QQQ', name: 'Invesco QQQ Trust', type: 'ETF', sector: 'Index', exchange: 'NASDAQ' },
            { symbol: 'GLD', name: 'SPDR Gold Shares', type: 'ETF', sector: 'Commodity', exchange: 'NYSE' },
            { symbol: 'TLT', name: 'iShares 20+ Year Treasury', type: 'ETF', sector: 'Bond', exchange: 'NASDAQ' }
        ];
    }

    async generateRecommendations() {
        console.log('🧮 Generating buy/sell/hold recommendations...');

        // Get market regime from composite score engine
        const marketRegime = window.compositeScoreEngine?.getMarketRegime() || 'recovery';
        const compositeScore = window.compositeScoreEngine?.getScores().composite || 65;

        console.log(`Market Regime: ${marketRegime}, Score: ${compositeScore}`);

        this.recommendations = this.symbols.map((symbol, index) => {
            const rec = this.calculateRecommendation(symbol, marketRegime, compositeScore);

            return {
                rank: index + 1,
                symbol: symbol.symbol,
                name: symbol.name,
                type: symbol.type || 'Stock',
                sector: symbol.sector || 'N/A',
                exchange: symbol.exchange || 'N/A',
                recommendation: rec.action,
                confidence: rec.confidence,
                rationale: rec.rationale,
                targetReturn: rec.targetReturn,
                riskLevel: rec.riskLevel
            };
        });

        console.log(`✅ Generated ${this.recommendations.length} recommendations`);
    }

    calculateRecommendation(symbol, marketRegime, compositeScore) {
        const sector = symbol.sector || 'Unknown';
        const type = symbol.type || 'Stock';

        // Default values
        let action = 'HOLD';
        let confidence = 'Medium';
        let rationale = 'Neutral market conditions';
        let targetReturn = '5-10%';
        let riskLevel = 'Medium';

        // EXPANSION REGIME (Score >= 85)
        if (marketRegime === 'expansion') {
            if (sector === 'Technology' || sector === 'Consumer') {
                action = 'BUY';
                confidence = 'High';
                rationale = 'Growth sectors thrive in expansion';
                targetReturn = '15-25%';
                riskLevel = 'Medium';
            } else if (sector === 'Financial') {
                action = 'BUY';
                confidence = 'High';
                rationale = 'Rising rates benefit financials';
                targetReturn = '12-20%';
                riskLevel = 'Medium';
            } else if (type === 'ETF' && symbol.symbol === 'TLT') {
                action = 'SELL';
                confidence = 'Medium';
                rationale = 'Bonds underperform in expansion';
                targetReturn = '-5 to 0%';
                riskLevel = 'Low';
            } else {
                action = 'BUY';
                confidence = 'Medium';
                rationale = 'Risk-on environment';
                targetReturn = '8-15%';
                riskLevel = 'Medium';
            }
        }

        // RECOVERY REGIME (Score 65-84)
        else if (marketRegime === 'recovery') {
            if (sector === 'Financial' || sector === 'Industrial') {
                action = 'BUY';
                confidence = 'High';
                rationale = 'Early cycle sectors outperform';
                targetReturn = '12-18%';
                riskLevel = 'Medium';
            } else if (sector === 'Technology') {
                action = 'BUY';
                confidence = 'Medium';
                rationale = 'Growth momentum building';
                targetReturn = '10-15%';
                riskLevel = 'Medium-High';
            } else if (type === 'ETF' && symbol.symbol === 'GLD') {
                action = 'HOLD';
                confidence = 'Medium';
                rationale = 'Gold neutral in recovery';
                targetReturn = '0-5%';
                riskLevel = 'Low';
            } else {
                action = 'BUY';
                confidence = 'Medium';
                rationale = 'Recovery momentum positive';
                targetReturn = '8-12%';
                riskLevel = 'Medium';
            }
        }

        // SLOWDOWN REGIME (Score 45-64)
        else if (marketRegime === 'slowdown') {
            if (sector === 'Healthcare' || sector === 'Utilities' || sector === 'Consumer Staples') {
                action = 'BUY';
                confidence = 'Medium';
                rationale = 'Defensive sectors preferred';
                targetReturn = '5-10%';
                riskLevel = 'Low';
            } else if (sector === 'Technology' || sector === 'Consumer') {
                action = 'HOLD';
                confidence = 'Medium';
                rationale = 'Growth sectors losing momentum';
                targetReturn = '0-5%';
                riskLevel = 'High';
            } else if (type === 'ETF' && symbol.symbol === 'TLT') {
                action = 'BUY';
                confidence = 'High';
                rationale = 'Bonds rally in slowdown';
                targetReturn = '8-15%';
                riskLevel = 'Low';
            } else {
                action = 'HOLD';
                confidence = 'Medium';
                rationale = 'Defensive positioning advised';
                targetReturn = '0-5%';
                riskLevel = 'Medium-High';
            }
        }

        // RECESSION REGIME (Score < 45)
        else {
            if (type === 'ETF' && (symbol.symbol === 'TLT' || symbol.symbol === 'GLD')) {
                action = 'BUY';
                confidence = 'High';
                rationale = 'Safe haven assets protect capital';
                targetReturn = '10-20%';
                riskLevel = 'Low';
            } else if (sector === 'Healthcare' || sector === 'Utilities') {
                action = 'HOLD';
                confidence = 'Medium';
                rationale = 'Defensive sectors hold value';
                targetReturn = '0-5%';
                riskLevel = 'Low-Medium';
            } else if (sector === 'Financial' || sector === 'Energy') {
                action = 'SELL';
                confidence = 'High';
                rationale = 'Cyclical sectors suffer in recession';
                targetReturn = '-10 to -5%';
                riskLevel = 'High';
            } else {
                action = 'SELL';
                confidence = 'Medium';
                rationale = 'Risk-off environment';
                targetReturn = '-5 to 0%';
                riskLevel = 'High';
            }
        }

        return { action, confidence, rationale, targetReturn, riskLevel };
    }

    displayRecommendations() {
        const tableBody = document.getElementById('recommendations-table-body');
        if (!tableBody) {
            console.warn('Recommendations table body not found');
            return;
        }

        // Sort recommendations
        const sorted = this.sortRecommendations(this.recommendations);

        const html = sorted.map(rec => {
            // Recommendation badge color
            let recClass, recIcon;
            if (rec.recommendation === 'BUY') {
                recClass = 'badge-buy';
                recIcon = '📈';
            } else if (rec.recommendation === 'SELL') {
                recClass = 'badge-sell';
                recIcon = '📉';
            } else {
                recClass = 'badge-hold';
                recIcon = '⏸️';
            }

            // Confidence color
            let confClass;
            if (rec.confidence === 'High') confClass = 'badge-high';
            else if (rec.confidence === 'Medium') confClass = 'badge-medium';
            else confClass = 'badge-low';

            // Risk level color
            let riskColor;
            if (rec.riskLevel.includes('High')) riskColor = 'var(--danger-color)';
            else if (rec.riskLevel.includes('Medium')) riskColor = 'var(--warning-color)';
            else riskColor = 'var(--success-color)';

            return `
                <tr onclick="window.open('/symbol_research.html?symbol=${encodeURIComponent(rec.symbol)}', '_blank');">
                    <td style="color: var(--text-muted); font-weight: 600;">${rec.rank}</td>
                    <td style="font-weight: 700; color: var(--accent-color);">${rec.symbol}</td>
                    <td>${rec.name}</td>
                    <td><span class="badge badge-stock">${rec.type}</span></td>
                    <td style="color: var(--text-secondary); font-size: 0.9rem;">${rec.sector}</td>
                    <td><span class="badge ${recClass}">${recIcon} ${rec.recommendation}</span></td>
                    <td><span class="badge ${confClass}">${rec.confidence}</span></td>
                    <td style="color: ${riskColor}; font-weight: 600;">${rec.riskLevel}</td>
                    <td style="color: var(--success-color); font-weight: 600;">${rec.targetReturn}</td>
                    <td style="font-size: 0.85rem; color: var(--text-secondary);">${rec.rationale}</td>
                </tr>
            `;
        }).join('');

        tableBody.innerHTML = html;

        console.log(`✅ Displayed ${sorted.length} recommendations`);
    }

    setupSorting() {
        // Add click handlers to table headers
        const headers = document.querySelectorAll('.sortable-header');

        headers.forEach(header => {
            header.addEventListener('click', () => {
                const column = header.dataset.column;
                this.handleSort(column);
            });
        });

        console.log('✅ Sorting enabled on table headers');
    }

    handleSort(column) {
        // Toggle direction if same column, otherwise default to asc
        if (this.sortColumn === column) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortColumn = column;
            this.sortDirection = 'asc';
        }

        console.log(`Sorting by ${column} (${this.sortDirection})`);

        // Re-display with new sort
        this.displayRecommendations();

        // Update header indicators
        this.updateSortIndicators();
    }

    sortRecommendations(recommendations) {
        const sorted = [...recommendations];

        sorted.sort((a, b) => {
            let aVal, bVal;

            // Get values based on sort column
            switch (this.sortColumn) {
                case 'symbol':
                    aVal = a.symbol;
                    bVal = b.symbol;
                    break;
                case 'recommendation':
                    // BUY > HOLD > SELL
                    const recOrder = { 'BUY': 3, 'HOLD': 2, 'SELL': 1 };
                    aVal = recOrder[a.recommendation] || 0;
                    bVal = recOrder[b.recommendation] || 0;
                    break;
                case 'confidence':
                    const confOrder = { 'High': 3, 'Medium': 2, 'Low': 1 };
                    aVal = confOrder[a.confidence] || 0;
                    bVal = confOrder[b.confidence] || 0;
                    break;
                case 'sector':
                    aVal = a.sector;
                    bVal = b.sector;
                    break;
                case 'type':
                    aVal = a.type;
                    bVal = b.type;
                    break;
                default:
                    aVal = a.rank;
                    bVal = b.rank;
            }

            // Compare
            let comparison = 0;
            if (aVal > bVal) comparison = 1;
            if (aVal < bVal) comparison = -1;

            // Apply direction
            return this.sortDirection === 'asc' ? comparison : -comparison;
        });

        return sorted;
    }

    updateSortIndicators() {
        // Remove all existing indicators
        document.querySelectorAll('.sort-indicator').forEach(el => el.remove());

        // Add indicator to active column
        const activeHeader = document.querySelector(`[data-column="${this.sortColumn}"]`);
        if (activeHeader) {
            const indicator = document.createElement('span');
            indicator.className = 'sort-indicator';
            indicator.textContent = this.sortDirection === 'asc' ? ' ▲' : ' ▼';
            indicator.style.color = 'var(--accent-color)';
            activeHeader.appendChild(indicator);
        }
    }

    async refresh() {
        console.log('🔄 Refreshing recommendations...');
        await this.loadTopSymbols();
        await this.generateRecommendations();
        this.displayRecommendations();
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Wait for composite score engine to load first
    setTimeout(() => {
        try {
            window.symbolRecommendations = new SymbolRecommendations();
            console.log('✅ Symbol Recommendations loaded');

            // Debug shortcut
            window.refreshRecommendations = () => {
                window.symbolRecommendations.refresh();
            };

        } catch (error) {
            console.error('❌ Symbol Recommendations failed to load:', error);
        }
    }, 2000);
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SymbolRecommendations;
}
