/**
 * Intermarket Ticker
 * Real-time ticker display for intermarket relationships
 */

(function() {
    'use strict';

    const TICKER_UPDATE_INTERVAL = 30000;  // 30 seconds
    const API_BASE = window.location.origin;

    class IntermarketTicker {
        constructor(containerId) {
            this.container = document.getElementById(containerId);
            if (!this.container) {
                console.warn('Intermarket ticker container not found');
                return;
            }

            this.symbols = [
                { symbol: 'SPY', name: 'S&P 500' },
                { symbol: 'DIA', name: 'Dow Jones' },
                { symbol: 'QQQ', name: 'NASDAQ' },
                { symbol: 'GLD', name: 'Gold' },
                { symbol: 'SLV', name: 'Silver' }
            ];

            this.init();
        }

        init() {
            this.render();
            this.fetchData();
            setInterval(() => this.fetchData(), TICKER_UPDATE_INTERVAL);
        }

        render() {
            this.container.innerHTML = `
                <div class="intermarket-ticker">
                    <div class="ticker-items" id="ticker-items">
                        ${this.symbols.map(s => this.renderTickerItem(s)).join('')}
                    </div>
                </div>
            `;
        }

        renderTickerItem(symbolData) {
            return `
                <div class="ticker-item" data-symbol="${symbolData.symbol}">
                    <span class="ticker-symbol">${symbolData.symbol}</span>
                    <span class="ticker-name">${symbolData.name}</span>
                    <span class="ticker-price">--</span>
                    <span class="ticker-change">--</span>
                </div>
            `;
        }

        async fetchData() {
            try {
                const response = await fetch(`${API_BASE}/api/market/indices`);
                if (!response.ok) return;

                const data = await response.json();
                if (data.data && Array.isArray(data.data)) {
                    this.updateTicker(data.data);
                }
            } catch (error) {
                console.error('Ticker fetch error:', error);
            }
        }

        updateTicker(marketData) {
            marketData.forEach(item => {
                const tickerItem = this.container.querySelector(`[data-symbol="${item.symbol}"]`);
                if (!tickerItem) return;

                const price = parseFloat(item.price || item.last_price || 0);
                const change = parseFloat(item.change_percent || 0);

                const priceEl = tickerItem.querySelector('.ticker-price');
                const changeEl = tickerItem.querySelector('.ticker-change');

                if (priceEl) {
                    priceEl.textContent = price.toFixed(2);
                }

                if (changeEl) {
                    const changeText = change >= 0 ? `+${change.toFixed(2)}%` : `${change.toFixed(2)}%`;
                    changeEl.textContent = changeText;
                    changeEl.className = `ticker-change ${change >= 0 ? 'positive' : 'negative'}`;
                }
            });
        }
    }

    // Auto-initialize if ticker container exists
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            const tickerContainer = document.getElementById('intermarket-ticker');
            if (tickerContainer) {
                new IntermarketTicker('intermarket-ticker');
            }
        });
    } else {
        const tickerContainer = document.getElementById('intermarket-ticker');
        if (tickerContainer) {
            new IntermarketTicker('intermarket-ticker');
        }
    }

    // Export for manual initialization
    window.IntermarketTicker = IntermarketTicker;

})();
