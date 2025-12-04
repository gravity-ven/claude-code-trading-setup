// Indicator Data Fetcher
// Fetches real-time data for AUD/JPY, HYG, US 10-Year Yield and other indicators
// Spartan Research Station

class IndicatorDataFetcher {
    constructor() {
        this.apiEndpoint = window.location.origin;
        this.indicatorData = {};
        this.updateInterval = 60000; // 1 minute

        this.init();
    }

    async init() {
        console.log('📊 Initializing Indicator Data Fetcher...');

        try {
            await this.fetchAllIndicators();
            this.displayIndicators();

            // Auto-refresh every minute
            setInterval(() => {
                this.fetchAllIndicators();
                this.displayIndicators();
            }, this.updateInterval);

            console.log('✅ Indicator Data Fetcher initialized');
        } catch (error) {
            console.error('❌ Indicator Data Fetcher initialization failed:', error);
        }
    }

    async fetchAllIndicators() {
        console.log('📡 Fetching indicator data...');

        try {
            // Fetch data in parallel
            const [audjpy, hyg, yield10y, btc, eth, sol, spy, qqq, vix] = await Promise.all([
                this.fetchForex('AUDJPY'),
                this.fetchETF('HYG'),
                this.fetchTreasuryYield('10Y'),
                this.fetchCrypto('BTC-USD'),
                this.fetchCrypto('ETH-USD'),
                this.fetchCrypto('SOL-USD'),
                this.fetchETF('SPY'),
                this.fetchETF('QQQ'),
                this.fetchVIX()
            ]);

            this.indicatorData = {
                audjpy,
                hyg,
                yield10y,
                btc,
                eth,
                sol,
                spy,
                qqq,
                vix
            };

            console.log('✅ Indicator data fetched:', this.indicatorData);
        } catch (error) {
            console.error('❌ Failed to fetch indicator data:', error);
        }
    }

    async fetchForex(pair) {
        try {
            // Try yfinance API first (via our backend)
            const symbol = `${pair}=X`;
            const response = await fetch(`${this.apiEndpoint}/api/market/quote/${symbol}`);

            if (response.ok) {
                const data = await response.json();
                return {
                    value: data.price,
                    change: data.change,
                    changePercent: data.changePercent || ((data.change / (data.price - data.change)) * 100),
                    timestamp: new Date().toISOString()
                };
            }

            // Fallback: try Redis cache
            const cacheResponse = await fetch(`${this.apiEndpoint}/api/cache/forex/${pair}`);
            if (cacheResponse.ok) {
                const cacheData = await cacheResponse.json();
                return {
                    value: cacheData.rate,
                    change: cacheData.change,
                    changePercent: cacheData.changePercent || 0,
                    timestamp: cacheData.timestamp
                };
            }

            return null;
        } catch (error) {
            console.error(`Failed to fetch ${pair}:`, error);
            return null;
        }
    }

    async fetchETF(symbol) {
        try {
            const response = await fetch(`${this.apiEndpoint}/api/market/quote/${symbol}`);

            if (response.ok) {
                const data = await response.json();
                return {
                    value: data.price,
                    change: data.change,
                    changePercent: data.changePercent || ((data.change / (data.price - data.change)) * 100),
                    timestamp: new Date().toISOString()
                };
            }

            return null;
        } catch (error) {
            console.error(`Failed to fetch ${symbol}:`, error);
            return null;
        }
    }

    async fetchTreasuryYield(maturity) {
        try {
            // Use ^TNX for 10-year yield (CBOE Interest Rate 10 Year T-Note)
            const symbol = '^TNX';
            const response = await fetch(`${this.apiEndpoint}/api/market/quote/${symbol}`);

            if (response.ok) {
                const data = await response.json();
                return {
                    value: data.price, // Already in percentage
                    change: data.change,
                    changePercent: data.changePercent || 0,
                    timestamp: new Date().toISOString()
                };
            }

            return null;
        } catch (error) {
            console.error(`Failed to fetch ${maturity} Treasury:`, error);
            return null;
        }
    }

    async fetchCrypto(symbol) {
        try {
            const response = await fetch(`${this.apiEndpoint}/api/market/quote/${symbol}`);

            if (response.ok) {
                const data = await response.json();
                return {
                    value: data.price,
                    change: data.change,
                    changePercent: data.changePercent || ((data.change / (data.price - data.change)) * 100),
                    timestamp: new Date().toISOString()
                };
            }

            return null;
        } catch (error) {
            console.error(`Failed to fetch ${symbol}:`, error);
            return null;
        }
    }

    async fetchVIX() {
        try {
            const symbol = '^VIX';
            const response = await fetch(`${this.apiEndpoint}/api/market/quote/${symbol}`);

            if (response.ok) {
                const data = await response.json();
                return {
                    value: data.price,
                    change: data.change,
                    changePercent: data.changePercent || 0,
                    timestamp: new Date().toISOString()
                };
            }

            return null;
        } catch (error) {
            console.error('Failed to fetch VIX:', error);
            return null;
        }
    }

    displayIndicators() {
        // AUD/JPY
        if (this.indicatorData.audjpy) {
            const audjpyValue = document.getElementById('audjpy-value');
            const audjpyArrow = document.getElementById('audjpy-arrow');

            if (audjpyValue && this.indicatorData.audjpy.value) {
                audjpyValue.textContent = this.indicatorData.audjpy.value.toFixed(4);

                if (audjpyArrow) {
                    if (this.indicatorData.audjpy.change > 0) {
                        audjpyArrow.textContent = '▲';
                        audjpyArrow.style.color = '#00ff88';
                    } else if (this.indicatorData.audjpy.change < 0) {
                        audjpyArrow.textContent = '▼';
                        audjpyArrow.style.color = '#DC143C';
                    } else {
                        audjpyArrow.textContent = '━';
                        audjpyArrow.style.color = '#FFD700';
                    }
                }
            }
        }

        // HYG
        if (this.indicatorData.hyg) {
            const hygValue = document.getElementById('hyg-value');
            const hygArrow = document.getElementById('hyg-arrow');

            if (hygValue && this.indicatorData.hyg.value) {
                hygValue.textContent = '$' + this.indicatorData.hyg.value.toFixed(2);

                if (hygArrow) {
                    if (this.indicatorData.hyg.change > 0) {
                        hygArrow.textContent = '▲';
                        hygArrow.style.color = '#00ff88';
                    } else if (this.indicatorData.hyg.change < 0) {
                        hygArrow.textContent = '▼';
                        hygArrow.style.color = '#DC143C';
                    } else {
                        hygArrow.textContent = '━';
                        hygArrow.style.color = '#FFD700';
                    }
                }
            }
        }

        // US 10-Year Yield
        if (this.indicatorData.yield10y) {
            const yieldValue = document.getElementById('yield-value');
            const yieldArrow = document.getElementById('yield-arrow');

            if (yieldValue && this.indicatorData.yield10y.value) {
                yieldValue.textContent = this.indicatorData.yield10y.value.toFixed(2) + '%';

                if (yieldArrow) {
                    if (this.indicatorData.yield10y.change > 0) {
                        yieldArrow.textContent = '▲';
                        yieldArrow.style.color = '#00ff88';
                    } else if (this.indicatorData.yield10y.change < 0) {
                        yieldArrow.textContent = '▼';
                        yieldArrow.style.color = '#DC143C';
                    } else {
                        yieldArrow.textContent = '━';
                        yieldArrow.style.color = '#FFD700';
                    }
                }
            }
        }

        // Crypto indicators (Bitcoin)
        if (this.indicatorData.btc) {
            const btcArrow = document.getElementById('crypto-btc-arrow');

            if (btcArrow) {
                if (this.indicatorData.btc.change > 0) {
                    btcArrow.textContent = '▲';
                    btcArrow.style.color = '#00ff88';
                } else if (this.indicatorData.btc.change < 0) {
                    btcArrow.textContent = '▼';
                    btcArrow.style.color = '#DC143C';
                } else {
                    btcArrow.textContent = '━';
                    btcArrow.style.color = '#FFD700';
                }
            }
        }

        // Calculate and display composite score
        this.calculateCompositeScore();
    }

    calculateCompositeScore() {
        let score = 50; // Neutral starting point
        let validIndicators = 0;

        // AUD/JPY contribution (0-33 points)
        if (this.indicatorData.audjpy && this.indicatorData.audjpy.changePercent !== undefined) {
            const audjpyContribution = Math.max(-15, Math.min(15, this.indicatorData.audjpy.changePercent * 3));
            score += audjpyContribution;
            validIndicators++;
        }

        // HYG contribution (0-33 points)
        if (this.indicatorData.hyg && this.indicatorData.hyg.changePercent !== undefined) {
            const hygContribution = Math.max(-15, Math.min(15, this.indicatorData.hyg.changePercent * 3));
            score += hygContribution;
            validIndicators++;
        }

        // 10Y Yield contribution (0-34 points)
        if (this.indicatorData.yield10y && this.indicatorData.yield10y.change !== undefined) {
            const yieldContribution = Math.max(-20, Math.min(20, this.indicatorData.yield10y.change * 5));
            score += yieldContribution;
            validIndicators++;
        }

        // Clamp score to 0-100
        score = Math.max(0, Math.min(100, score));

        // Display composite score
        const scoreElement = document.getElementById('composite-score');
        const labelElement = document.getElementById('composite-label');
        const barElement = document.getElementById('composite-bar');

        if (scoreElement) {
            scoreElement.textContent = Math.round(score);
        }

        if (labelElement) {
            if (score >= 70) {
                labelElement.textContent = 'RISK-ON';
                labelElement.style.color = '#00ff88';
            } else if (score >= 40) {
                labelElement.textContent = 'NEUTRAL';
                labelElement.style.color = '#FFD700';
            } else {
                labelElement.textContent = 'RISK-OFF';
                labelElement.style.color = '#DC143C';
            }
        }

        if (barElement) {
            barElement.style.width = score + '%';
        }
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    window.indicatorDataFetcher = new IndicatorDataFetcher();
});
