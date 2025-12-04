/**
 * Market Visualizations for Spartan Research Station
 * Creates Mermaid-like flow charts and graphs for market data
 */

class MarketVisualizations {
    constructor() {
        this.redisData = {};
        this.refreshInterval = 30000; // 30 seconds
        this.init();
    }

    async init() {
        await this.loadMarketData();
        this.createVisualizations();
        // Refresh every 30 seconds
        setInterval(() => {
            this.loadMarketData();
            this.updateVisualizations();
        }, this.refreshInterval);
    }

    async loadMarketData() {
        try {
            // Fetch all market data from our API
            const symbols = ['SPY', 'QQQ', 'DIA', 'IWM', 'GLD', 'USO', 'BTC-USD', 'ETH-USD', '^VIX'];

            for (const symbol of symbols) {
                const response = await fetch(`/api/market/quote/${encodeURIComponent(symbol)}`);
                if (response.ok) {
                    this.redisData[symbol] = await response.json();
                }
            }
        } catch (error) {
            console.error('Error loading market data:', error);
        }
    }

    createVisualizations() {
        // Find or create visualization container
        let vizContainer = document.getElementById('market-visualizations');
        if (!vizContainer) {
            // Insert at the top of main content
            const mainContent = document.querySelector('.container') || document.querySelector('main') || document.body;
            vizContainer = document.createElement('div');
            vizContainer.id = 'market-visualizations';
            vizContainer.style.cssText = `
                padding: 20px;
                background: linear-gradient(135deg, #1a1a2e 0%, #0f0f23 100%);
                border-radius: 12px;
                margin: 20px auto;
                max-width: 1400px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            `;
            mainContent.insertBefore(vizContainer, mainContent.firstChild);
        }

        vizContainer.innerHTML = `
            <h2 style="color: #00ff88; text-align: center; margin-bottom: 30px; font-size: 28px;">
                📊 Real-Time Market Flow Visualization
            </h2>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                ${this.createMarketFlowChart()}
                ${this.createSectorRotationChart()}
                ${this.createRiskSentimentGauge()}
                ${this.createVolatilityChart()}
            </div>

            <div style="margin-top: 30px;">
                ${this.createMarketOverview()}
            </div>
        `;
    }

    createMarketFlowChart() {
        const spy = this.redisData['SPY'] || {};
        const qqq = this.redisData['QQQ'] || {};
        const vix = this.redisData['^VIX'] || {};
        const gld = this.redisData['GLD'] || {};

        const riskMode = (spy.changePercent > 0 && vix.changePercent < 0) ? 'RISK-ON' :
                        (spy.changePercent < 0 && vix.changePercent > 0) ? 'RISK-OFF' : 'NEUTRAL';

        const riskColor = riskMode === 'RISK-ON' ? '#00ff88' :
                         riskMode === 'RISK-OFF' ? '#ff3366' : '#ffaa00';

        return `
            <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 10px;">
                <h3 style="color: #fff; margin-bottom: 15px;">Market Flow</h3>

                <div style="text-align: center; margin: 20px 0;">
                    <div style="display: inline-block; padding: 10px 20px; background: ${riskColor}; color: #000; border-radius: 20px; font-weight: bold;">
                        ${riskMode}
                    </div>
                </div>

                <svg viewBox="0 0 300 200" style="width: 100%; height: auto;">
                    <!-- Flow arrows -->
                    <defs>
                        <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                            <polygon points="0 0, 10 3.5, 0 7" fill="${riskColor}" />
                        </marker>
                    </defs>

                    <!-- Nodes -->
                    <rect x="20" y="20" width="80" height="40" rx="5" fill="#2a2a3e" stroke="${riskColor}" stroke-width="2"/>
                    <text x="60" y="45" text-anchor="middle" fill="#fff" font-size="12">STOCKS</text>

                    <rect x="200" y="20" width="80" height="40" rx="5" fill="#2a2a3e" stroke="#ffaa00" stroke-width="2"/>
                    <text x="240" y="45" text-anchor="middle" fill="#fff" font-size="12">BONDS</text>

                    <rect x="20" y="140" width="80" height="40" rx="5" fill="#2a2a3e" stroke="#00aaff" stroke-width="2"/>
                    <text x="60" y="165" text-anchor="middle" fill="#fff" font-size="12">CRYPTO</text>

                    <rect x="200" y="140" width="80" height="40" rx="5" fill="#2a2a3e" stroke="#ffcc00" stroke-width="2"/>
                    <text x="240" y="165" text-anchor="middle" fill="#fff" font-size="12">GOLD</text>

                    <!-- Flow lines based on market mode -->
                    ${riskMode === 'RISK-ON' ?
                        `<line x1="100" y1="40" x2="200" y2="40" stroke="${riskColor}" stroke-width="2" marker-end="url(#arrowhead)"/>
                         <line x1="60" y1="60" x2="60" y2="140" stroke="${riskColor}" stroke-width="2" marker-end="url(#arrowhead)"/>` :
                        `<line x1="200" y1="40" x2="100" y2="40" stroke="${riskColor}" stroke-width="2" marker-end="url(#arrowhead)"/>
                         <line x1="240" y1="60" x2="240" y2="140" stroke="${riskColor}" stroke-width="2" marker-end="url(#arrowhead)"/>`
                    }

                    <!-- Central indicator -->
                    <circle cx="150" cy="100" r="30" fill="none" stroke="${riskColor}" stroke-width="3" opacity="0.5"/>
                    <text x="150" y="105" text-anchor="middle" fill="${riskColor}" font-size="14" font-weight="bold">
                        ${riskMode === 'RISK-ON' ? '↗' : riskMode === 'RISK-OFF' ? '↘' : '→'}
                    </text>
                </svg>

                <div style="margin-top: 15px; font-size: 12px; color: #999;">
                    <div>SPY: ${spy.price ? `$${spy.price} (${spy.changePercent > 0 ? '+' : ''}${spy.changePercent}%)` : 'Loading...'}</div>
                    <div>VIX: ${vix.price ? `${vix.price} (${vix.changePercent > 0 ? '+' : ''}${vix.changePercent}%)` : 'Loading...'}</div>
                </div>
            </div>
        `;
    }

    createSectorRotationChart() {
        const sectors = [
            { symbol: 'XLK', name: 'Tech', color: '#00ff88' },
            { symbol: 'XLF', name: 'Financial', color: '#00aaff' },
            { symbol: 'XLE', name: 'Energy', color: '#ffaa00' },
            { symbol: 'XLV', name: 'Healthcare', color: '#ff66aa' }
        ];

        return `
            <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 10px;">
                <h3 style="color: #fff; margin-bottom: 15px;">Sector Rotation</h3>

                <svg viewBox="0 0 300 200" style="width: 100%; height: auto;">
                    <circle cx="150" cy="100" r="80" fill="none" stroke="#333" stroke-width="2"/>

                    ${sectors.map((sector, i) => {
                        const angle = (i * 90 - 90) * Math.PI / 180;
                        const x = 150 + 60 * Math.cos(angle);
                        const y = 100 + 60 * Math.sin(angle);

                        return `
                            <circle cx="${x}" cy="${y}" r="25" fill="${sector.color}" opacity="0.3"/>
                            <text x="${x}" y="${y}" text-anchor="middle" fill="#fff" font-size="10">
                                ${sector.name}
                            </text>
                        `;
                    }).join('')}

                    <!-- Center indicator -->
                    <text x="150" y="105" text-anchor="middle" fill="#fff" font-size="12" font-weight="bold">
                        ROTATING
                    </text>
                </svg>

                <div style="margin-top: 15px;">
                    <div style="display: flex; justify-content: space-between; font-size: 11px;">
                        <span style="color: #00ff88;">▲ Leading</span>
                        <span style="color: #ffaa00;">● Neutral</span>
                        <span style="color: #ff3366;">▼ Lagging</span>
                    </div>
                </div>
            </div>
        `;
    }

    createRiskSentimentGauge() {
        const spy = this.redisData['SPY'] || {};
        const vix = this.redisData['^VIX'] || {};
        const btc = this.redisData['BTC-USD'] || {};

        // Calculate risk score (0-100)
        let riskScore = 50; // Default neutral
        if (spy.changePercent && vix.price) {
            riskScore = Math.max(0, Math.min(100,
                50 + (spy.changePercent * 5) - (vix.price - 15) * 2
            ));
        }

        const color = riskScore > 70 ? '#00ff88' : riskScore < 30 ? '#ff3366' : '#ffaa00';

        return `
            <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 10px;">
                <h3 style="color: #fff; margin-bottom: 15px;">Risk Sentiment</h3>

                <svg viewBox="0 0 300 200" style="width: 100%; height: auto;">
                    <!-- Gauge background -->
                    <path d="M 50 150 A 100 100 0 0 1 250 150" fill="none" stroke="#333" stroke-width="20"/>

                    <!-- Gauge fill -->
                    <path d="M 50 150 A 100 100 0 0 1 ${50 + riskScore * 2} 150"
                          fill="none" stroke="${color}" stroke-width="20" stroke-linecap="round"/>

                    <!-- Needle -->
                    <line x1="150" y1="150"
                          x2="${150 + 80 * Math.cos((180 - riskScore * 1.8) * Math.PI / 180)}"
                          y2="${150 - 80 * Math.sin((180 - riskScore * 1.8) * Math.PI / 180)}"
                          stroke="${color}" stroke-width="3"/>

                    <circle cx="150" cy="150" r="10" fill="${color}"/>

                    <!-- Labels -->
                    <text x="50" y="180" fill="#ff3366" font-size="12">FEAR</text>
                    <text x="150" y="50" text-anchor="middle" fill="#ffaa00" font-size="12">NEUTRAL</text>
                    <text x="250" y="180" text-anchor="end" fill="#00ff88" font-size="12">GREED</text>

                    <!-- Score -->
                    <text x="150" y="120" text-anchor="middle" fill="#fff" font-size="24" font-weight="bold">
                        ${Math.round(riskScore)}
                    </text>
                </svg>

                <div style="text-align: center; margin-top: 10px; color: ${color}; font-weight: bold;">
                    ${riskScore > 70 ? 'EXTREME GREED' :
                      riskScore > 55 ? 'GREED' :
                      riskScore > 45 ? 'NEUTRAL' :
                      riskScore > 30 ? 'FEAR' : 'EXTREME FEAR'}
                </div>
            </div>
        `;
    }

    createVolatilityChart() {
        const vix = this.redisData['^VIX'] || {};
        const vixLevel = vix.price || 20;
        const barHeight = Math.min(150, vixLevel * 5);

        const levels = [
            { threshold: 40, label: 'PANIC', color: '#ff0000' },
            { threshold: 30, label: 'HIGH', color: '#ff6600' },
            { threshold: 20, label: 'ELEVATED', color: '#ffaa00' },
            { threshold: 15, label: 'NORMAL', color: '#00ff88' },
            { threshold: 0, label: 'LOW', color: '#0088ff' }
        ];

        const currentLevel = levels.find(l => vixLevel >= l.threshold);

        return `
            <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 10px;">
                <h3 style="color: #fff; margin-bottom: 15px;">Volatility Monitor</h3>

                <svg viewBox="0 0 300 200" style="width: 100%; height: auto;">
                    <!-- Background levels -->
                    ${levels.map((level, i) => `
                        <rect x="50" y="${40 + i * 30}" width="200" height="30"
                              fill="${level.color}" opacity="0.1"/>
                        <text x="255" y="${55 + i * 30}" fill="${level.color}" font-size="10">
                            ${level.label}
                        </text>
                    `).join('')}

                    <!-- Current VIX bar -->
                    <rect x="120" y="${190 - barHeight}" width="60" height="${barHeight}"
                          fill="${currentLevel?.color || '#fff'}" opacity="0.8" rx="5"/>

                    <!-- VIX value -->
                    <text x="150" y="${180 - barHeight}" text-anchor="middle" fill="#fff"
                          font-size="20" font-weight="bold">
                        ${vixLevel.toFixed(2)}
                    </text>

                    <!-- Label -->
                    <text x="150" y="195" text-anchor="middle" fill="#999" font-size="12">
                        VIX INDEX
                    </text>

                    <!-- Change indicator -->
                    <text x="150" y="30" text-anchor="middle" fill="${vix.changePercent > 0 ? '#ff3366' : '#00ff88'}"
                          font-size="14" font-weight="bold">
                        ${vix.changePercent > 0 ? '↑' : '↓'} ${Math.abs(vix.changePercent || 0).toFixed(2)}%
                    </text>
                </svg>
            </div>
        `;
    }

    createMarketOverview() {
        const data = Object.values(this.redisData);
        const gainers = data.filter(d => d.changePercent > 0).sort((a,b) => b.changePercent - a.changePercent).slice(0, 5);
        const losers = data.filter(d => d.changePercent < 0).sort((a,b) => a.changePercent - b.changePercent).slice(0, 5);

        return `
            <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 10px;">
                <h3 style="color: #fff; margin-bottom: 20px;">Market Overview</h3>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div>
                        <h4 style="color: #00ff88; margin-bottom: 10px;">📈 Top Gainers</h4>
                        ${gainers.map(g => `
                            <div style="display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                                <span style="color: #fff;">${g.symbol}</span>
                                <span style="color: #00ff88;">+${g.changePercent.toFixed(2)}%</span>
                            </div>
                        `).join('')}
                    </div>

                    <div>
                        <h4 style="color: #ff3366; margin-bottom: 10px;">📉 Top Losers</h4>
                        ${losers.map(l => `
                            <div style="display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                                <span style="color: #fff;">${l.symbol}</span>
                                <span style="color: #ff3366;">${l.changePercent.toFixed(2)}%</span>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <div style="margin-top: 20px; text-align: center; color: #999; font-size: 12px;">
                    Last Updated: ${new Date().toLocaleTimeString()}
                </div>
            </div>
        `;
    }

    updateVisualizations() {
        this.createVisualizations();
    }
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new MarketVisualizations());
} else {
    new MarketVisualizations();
}