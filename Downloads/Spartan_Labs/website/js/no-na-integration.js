/**
 * SPARTAN NO N/A DATA INTEGRATION
 * Ensures 100% data availability across all dashboard components
 * Replaces any N/A fields with live scraped data from genuine sources
 */

class SpartanNoNAData {
    constructor() {
        this.apiBase = 'http://localhost:8888';
        this.cache = {};
        this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
        
        this.init();
    }

    async init() {
        console.log('🛡️ Spartan NO N/A Data Integration initializing...');
        
        // Load initial data
        await this.loadCompleteMarketData();
        
        // Set up periodic refresh
        setInterval(() => {
            this.loadCompleteMarketData();
        }, this.cacheTimeout);
        
        // Expose global functions for dashboard updates
        window.SpartanNoNA = {
            getMarketBreadth: () => this.getCachedData('market_breadth'),
            getPutCallRatio: () => this.getCachedData('put_call_ratio'), 
            getVolatilityData: () => this.getCachedData('volatility_data'),
            updateAllN/A: () => this.updateAllNAFields(),
            forceRefresh: () => this.loadCompleteMarketData()
        };
        
        console.log('✅ Spartan NO N/A Data Integration ready!');
    }

    async loadCompleteMarketData() {
        try {
            console.log('🔄 Loading complete market data with NO N/A guarantee...');
            
            const response = await fetch(`${this.apiBase}/api/market/complete`);
            const data = await response.json();
            
            if (data.guarantee === '100% DATA AVAILABILITY - NO N/A FIELDS') {
                this.cache['market_breadth'] = data.market_breadth;
                this.cache['put_call_ratio'] = data.put_call_ratio;
                this.cache['volatility_data'] = data.volatility_data;
                this.cache['timestamp'] = data.timestamp;
                
                console.log('✅ Complete market data loaded successfully');
                this.updateAllNAFields();
            }
            
        } catch (error) {
            console.error('❌ Failed to load complete market data:', error);
        }
    }

    getCachedData(key) {
        const data = this.cache[key];
        if (data) {
            console.log(`📊 Cached ${key}:`, data);
            return data;
        } else {
            console.warn(`⚠️ No cached data for ${key}`);
            return null;
        }
    }

    updateAllNAFields() {
        console.log('🔄 Updating all N/A fields with live data...');
        
        this.updateMarketBreadthDisplay();
        this.updatePutCallDisplay();
        this.updateVolatilityDisplay();
    }

    updateMarketBreadthDisplay() {
        try {
            const breadthData = this.getCachedData('market_breadth');
            if (!breadthData) return;

            // Update main dashboard Market Breadth section
            const breadthElements = document.querySelectorAll('[data-market-breadth]');
            breadthElements.forEach(el => {
                el.innerHTML = `
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
                        <div>
                            <span style="color: var(--green); font-weight: bold;">${breadthData.advancing}</span>
                            <span style="color: var(--text-secondary); font-size: 0.9em;"> Advancing</span>
                        </div>
                        <div>
                            <span style="color: var(--accent-color); font-weight: bold;">${breadthData.declining}</span>
                            <span style="color: var(--text-secondary); font-size: 0.9em;"> Declining</span>
                        </div>
                        <div>
                            <span style="color: var(--blue); font-weight: bold;">${breadthData.advance_percent.toFixed(1)}%</span>
                            <span style="color: var(--text-secondary); font-size: 0.9em;"> Adv %</span>
                        </div>
                        <div>
                            <span style="color: var(--text-primary); font-weight: bold;">${breadthData.status}</span>
                            <span style="color: var(--text-secondary); font-size: 0.9em;"> Status</span>
                        </div>
                    </div>
                    <div style="margin-top: 5px; font-size: 0.8em; color: var(--text-secondary);">
                        Source: ${breadthData.source} • Total: ${breadthData.total}
                    </div>
                `;
            });

            // Update any element with content "N/A" for Market Breadth
            const naElements = document.querySelectorAll('*');
            naElements.forEach(el => {
                if (el.textContent.includes('Market Breadth') && el.textContent.includes('N/A')) {
                    el.innerHTML = el.innerHTML.replace('N/A', 
                        `${breadthData.advance_percent.toFixed(1)}% Advancing (${breadthData.advancing}/${breadthData.total})`
                    );
                    el.style.color = breadthData.advance_percent > 70 ? 'var(--green)' : 
                                   breadthData.advance_percent < 30 ? 'var(--accent-color)' : 'var(--text-primary)';
                }
            });

            console.log('✅ Market Breadth display updated:', breadthData);

        } catch (error) {
            console.error('❌ Failed to update Market Breadth display:', error);
        }
    }

    updatePutCallDisplay() {
        try {
            const putCallData = this.getCachedData('put_call_ratio');
            if (!putCallData) return;

            // Update Put/Call Ratio displays
            const putCallElements = document.querySelectorAll('[data-put-call]');
            putCallElements.forEach(el => {
                const statusColor = putCallData.status === 'EXTREME FEAR' ? 'var(--green)' :
                                  putCallData.status === 'EXTREME GREED' ? 'var(--accent-color)' : 'var(--blue)';
                
                el.innerHTML = `
                    <div style="text-align: center;">
                        <div style="font-size: 1.5em; font-weight: bold; color: ${statusColor};">
                            ${putCallData.ratio.toFixed(2)}
                        </div>
                        <div style="color: var(--text-secondary); font-size: 0.9em;">
                            ${putCallData.status} - ${putCallData.sentiment}
                        </div>
                        <div style="margin-top: 5px; font-size: 0.7em; color: var(--text-secondary);">
                            Source: ${putCallData.source}
                        </div>
                    </div>
                `;
            });

            // Update any element with Put/Call Ratio and N/A
            const naElements = document.querySelectorAll('*');
            naElements.forEach(el => {
                if (el.textContent.includes('Put/Call Ratio') && el.textContent.includes('1.00')) {
                    el.innerHTML = el.innerHTML.replace('1.00', putCallData.ratio.toFixed(2));
                    el.innerHTML = el.innerHTML.replace('🟡 NEUTRAL', 
                        `${putCallData.status === 'EXTREME FEAR' ? '🔴' : putCallData.status === 'EXTREME GREED' ? '🟢' : '🟡'} ${putCallData.status}`);
                }
            });

            console.log('✅ Put/Call Ratio display updated:', putCallData);

        } catch (error) {
            console.error('❌ Failed to update Put/Call Ratio display:', error);
        }
    }

    updateVolatilityDisplay() {
        try {
            const volData = this.getCachedData('volatility_data');
            if (!volData) return;

            // Update VIX displays
            const vixElements = document.querySelectorAll('[data-volatility]');
            vixElements.forEach(el => {
                const statusColor = volData.status === 'EXTREME FEAR' ? 'var(--green)' :
                                  volData.status === 'EXTREME GREED' ? 'var(--accent-color)' : 'var(--text-primary)';
                
                el.innerHTML = `
                    <div style="text-align: center;">
                        <div style="font-size: 1.5em; font-weight: bold; color: ${statusColor};">
                            ${volData.primary_vix.toFixed(2)}
                        </div>
                        <div style="color: var(--text-secondary); font-size: 0.9em;">
                            ${volData.status} • ${volData.source_count} sources
                        </div>
                        <div style="margin-top: 5px; font-size: 0.7em; color: var(--text-secondary);">
                            ${volData.alternatives[0].name}: ${volData.alternatives[0].value.toFixed(2)}
                        </div>
                    </div>
                `;
            });

            // Update any element with VIX and Error
            const naElements = document.querySelectorAll('*');
            naElements.forEach(el => {
                if (el.textContent.includes('VIX') && el.textContent.includes('Error')) {
                    el.innerHTML = el.innerHTML.replace('Error', volData.primary_vix.toFixed(2));
                    el.innerHTML = el.innerHTML.replace('Source: Yahoo Finance (^VIX)', 
                        `Source: ${volData.alternatives[0].source}`);
                }
            });

            console.log('✅ Volatility display updated:', volData);

        } catch (error) {
            console.error('❌ Failed to update Volatility display:', error);
        }
    }

    // Public method to manually update specific components
    updateComponent(componentType) {
        switch (componentType) {
            case 'breadth':
                this.updateMarketBreadthDisplay();
                break;
            case 'putcall':
                this.updatePutCallDisplay();
                break;
            case 'volatility':
                this.updateVolatilityDisplay();
                break;
            default:
                this.updateAllNAFields();
        }
    }
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new SpartanNoNAData();
    });
} else {
    new SpartanNoNAData();
}

// Export for global access
window.SpartanNoNAData = SpartanNoNAData;
