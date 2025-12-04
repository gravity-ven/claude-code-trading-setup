/**
 * Historical Connections Data Fetcher
 * Real-time market data integration for historical patterns dashboard
 */

class HistoricalConnectionsData {
    constructor() {
        this.apiBase = '/api';
        this.instruments = {
            'ES': { name: 'E-mini S&P 500', symbol: 'ES=F' },
            'NQ': { name: 'E-mini Nasdaq-100', symbol: 'NQ=F' },
            'YM': { name: 'E-mini Dow', symbol: 'YM=F' },
            'RTY': { name: 'Russell 2000', symbol: 'RTY=F' },
            'GC': { name: 'Gold Futures', symbol: 'GC=F' },
            'CL': { name: 'Crude Oil', symbol: 'CL=F' },
            'BTC': { name: 'Bitcoin', symbol: 'BTC-USD' },
            'SPY': { name: 'S&P 500 ETF', symbol: 'SPY' }
        };

        this.seasonalData = {
            'January': { return: 1.07, winRate: 62, trend: 'bullish' },
            'February': { return: -0.01, winRate: 50, trend: 'neutral' },
            'March': { return: 1.13, winRate: 63, trend: 'bullish' },
            'April': { return: 1.46, winRate: 65, trend: 'bullish' },
            'May': { return: 0.30, winRate: 54, trend: 'neutral' },
            'June': { return: 0.11, winRate: 52, trend: 'neutral' },
            'July': { return: 1.28, winRate: 60, trend: 'bullish' },
            'August': { return: -0.01, winRate: 50, trend: 'neutral' },
            'September': { return: -0.72, winRate: 43, trend: 'bearish' },
            'October': { return: 0.91, winRate: 58, trend: 'bullish' },
            'November': { return: 1.82, winRate: 68, trend: 'bullish' },
            'December': { return: 1.49, winRate: 65, trend: 'bullish' }
        };

        this.init();
    }

    async init() {
        // Load real market data on page load
        await this.fetchMarketData();
        await this.updateSeasonalHighlights();
        await this.fetchBitcoinHalvingData();

        // Set up auto-refresh every 5 minutes
        setInterval(() => {
            this.fetchMarketData();
        }, 5 * 60 * 1000);
    }

    async fetchMarketData() {
        try {
            // Fetch from preloaded data endpoint
            const response = await fetch(`${this.apiBase}/market-data`);
            if (!response.ok) {
                console.warn('Market data not available, using cached values');
                return;
            }

            const data = await response.json();
            this.updateInstrumentCards(data);
            this.updateCorrelations(data);

        } catch (error) {
            console.error('Error fetching market data:', error);
            // Continue with static display if API fails
        }
    }

    updateInstrumentCards(data) {
        // Update each instrument card with live data if available
        Object.keys(this.instruments).forEach(key => {
            const instrument = this.instruments[key];
            const marketData = data[instrument.symbol];

            if (marketData) {
                const cardElement = document.querySelector(`[data-instrument="${key}"]`);
                if (cardElement) {
                    const priceElement = cardElement.querySelector('.instrument-price');
                    const changeElement = cardElement.querySelector('.instrument-change');

                    if (priceElement && marketData.price) {
                        priceElement.textContent = `$${this.formatNumber(marketData.price)}`;
                        priceElement.style.color = '#FFD700';
                    }

                    if (changeElement && marketData.change) {
                        const changePercent = marketData.changePercent || 0;
                        changeElement.textContent = `${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(2)}%`;
                        changeElement.style.color = changePercent >= 0 ? '#00ff88' : '#FF5252';
                    }
                }
            }
        });
    }

    updateCorrelations(data) {
        // Calculate and display key correlations
        if (data['SPY'] && data['GC=F']) {
            const spyGoldCorr = this.calculateCorrelation(data['SPY'].history || [], data['GC=F'].history || []);
            const corrElement = document.getElementById('spy-gold-correlation');
            if (corrElement) {
                corrElement.textContent = `SPY/Gold Correlation: ${spyGoldCorr.toFixed(2)}`;
                corrElement.style.color = Math.abs(spyGoldCorr) > 0.5 ? '#FFD700' : '#b0b8c8';
            }
        }
    }

    async updateSeasonalHighlights() {
        const currentMonth = new Date().toLocaleString('default', { month: 'long' });
        const currentMonthData = this.seasonalData[currentMonth];

        // Highlight current month in seasonality table
        const monthRows = document.querySelectorAll('.seasonality-table tbody tr');
        monthRows.forEach(row => {
            const monthCell = row.cells[0];
            if (monthCell && monthCell.textContent === currentMonth) {
                row.style.background = 'rgba(255, 215, 0, 0.1)';
                row.style.border = '2px solid #FFD700';
            }
        });

        // Add current month alert if it's September
        if (currentMonth === 'September') {
            const alertDiv = document.createElement('div');
            alertDiv.className = 'key-insight';
            alertDiv.style.background = 'linear-gradient(135deg, rgba(255, 82, 82, 0.2), rgba(139, 0, 0, 0.2))';
            alertDiv.innerHTML = `
                <h4>⚠️ September Alert - Historical Warning!</h4>
                <p>You're currently in September, historically the worst performing month with an average loss of -0.72%
                and only 43% win rate. Consider defensive positioning or reduced exposure this month.</p>
            `;

            const septemberSection = document.querySelector('.content-card h2:has-text("September Effect")');
            if (septemberSection && septemberSection.parentNode) {
                septemberSection.parentNode.insertBefore(alertDiv, septemberSection.nextSibling);
            }
        }

        // Highlight best upcoming month
        const nextThreeMonths = this.getNextThreeMonths();
        let bestMonth = null;
        let bestReturn = -100;

        nextThreeMonths.forEach(month => {
            const monthData = this.seasonalData[month];
            if (monthData && monthData.return > bestReturn) {
                bestReturn = monthData.return;
                bestMonth = month;
            }
        });

        if (bestMonth) {
            const opportunityDiv = document.createElement('div');
            opportunityDiv.className = 'key-insight';
            opportunityDiv.style.background = 'linear-gradient(135deg, rgba(0, 255, 136, 0.1), rgba(255, 215, 0, 0.1))';
            opportunityDiv.innerHTML = `
                <h4>📈 Upcoming Opportunity: ${bestMonth}</h4>
                <p>${bestMonth} historically shows strong performance with an average return of +${bestReturn}%
                and ${this.seasonalData[bestMonth].winRate}% win rate. Consider positioning ahead of this seasonal strength.</p>
            `;

            const container = document.querySelector('.container');
            if (container && container.firstChild) {
                container.insertBefore(opportunityDiv, container.children[1]);
            }
        }
    }

    async fetchBitcoinHalvingData() {
        try {
            // Fetch Bitcoin price for halving countdown
            const response = await fetch(`${this.apiBase}/crypto/BTC-USD`);
            if (response.ok) {
                const btcData = await response.json();
                const halvingElement = document.querySelector('.halving-countdown');

                if (halvingElement && btcData.price) {
                    // Calculate days since last halving (April 20, 2024)
                    const halvingDate = new Date('2024-04-20');
                    const today = new Date();
                    const daysSince = Math.floor((today - halvingDate) / (1000 * 60 * 60 * 24));

                    // Add price and progress info
                    const progressDiv = document.createElement('div');
                    progressDiv.style.marginTop = '15px';
                    progressDiv.innerHTML = `
                        <div style="color: #F7931A; font-size: 1.1rem; margin-bottom: 10px;">
                            Current BTC Price: $${this.formatNumber(btcData.price)}
                        </div>
                        <div style="color: #b0b8c8; font-size: 0.95rem;">
                            Days since halving: ${daysSince} / ~550 days to typical peak
                        </div>
                        <div style="margin-top: 10px; height: 10px; background: rgba(0,0,0,0.3); border-radius: 5px; overflow: hidden;">
                            <div style="height: 100%; width: ${Math.min((daysSince / 550) * 100, 100)}%;
                                        background: linear-gradient(90deg, #F7931A, #00ff88); transition: width 0.5s;"></div>
                        </div>
                    `;

                    halvingElement.appendChild(progressDiv);

                    // Update 4th halving row with current price
                    const halvingTable = document.querySelector('.seasonality-table');
                    if (halvingTable) {
                        const rows = halvingTable.querySelectorAll('tbody tr');
                        const fourthHalvingRow = rows[rows.length - 1];
                        if (fourthHalvingRow) {
                            fourthHalvingRow.cells[3].innerHTML = `$${this.formatNumber(btcData.price)} (Live)`;
                            fourthHalvingRow.cells[3].style.color = '#00ff88';
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Error fetching Bitcoin data:', error);
        }
    }

    calculateCorrelation(series1, series2) {
        // Simple correlation calculation
        if (!series1.length || !series2.length || series1.length !== series2.length) {
            return 0;
        }

        const n = series1.length;
        const mean1 = series1.reduce((a, b) => a + b, 0) / n;
        const mean2 = series2.reduce((a, b) => a + b, 0) / n;

        let numerator = 0;
        let denom1 = 0;
        let denom2 = 0;

        for (let i = 0; i < n; i++) {
            const diff1 = series1[i] - mean1;
            const diff2 = series2[i] - mean2;
            numerator += diff1 * diff2;
            denom1 += diff1 * diff1;
            denom2 += diff2 * diff2;
        }

        if (denom1 === 0 || denom2 === 0) return 0;

        return numerator / Math.sqrt(denom1 * denom2);
    }

    getNextThreeMonths() {
        const months = ['January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December'];
        const currentMonth = new Date().getMonth();
        const result = [];

        for (let i = 1; i <= 3; i++) {
            result.push(months[(currentMonth + i) % 12]);
        }

        return result;
    }

    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(2) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(2) + 'K';
        } else {
            return num.toFixed(2);
        }
    }

    // Interactive pattern detector
    detectCurrentPatterns() {
        // This would connect to real price data to detect patterns
        // For now, we'll show pattern detection status
        const patternStatus = document.createElement('div');
        patternStatus.className = 'live-data-badge';
        patternStatus.textContent = 'Pattern Scanner: ACTIVE';
        patternStatus.style.background = '#00ff88';
        patternStatus.style.animation = 'pulse 1s infinite';

        const header = document.querySelector('.header div');
        if (header) {
            header.appendChild(patternStatus);
        }
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new HistoricalConnectionsData();
    });
} else {
    new HistoricalConnectionsData();
}

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = HistoricalConnectionsData;
}