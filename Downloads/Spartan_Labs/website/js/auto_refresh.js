/**
 * AUTO REFRESH MODULE
 * Automatically refreshes market data without full page reload
 */

(function() {
    'use strict';

    const AUTO_REFRESH_CONFIG = {
        // Refresh intervals (in milliseconds)
        PRICE_DATA_INTERVAL: 15 * 60 * 1000,      // 15 minutes
        FUNDAMENTAL_DATA_INTERVAL: 60 * 60 * 1000, // 1 hour
        INITIAL_DELAY: 5 * 1000,                   // 5 seconds initial delay

        // Enable/disable flags
        ENABLE_PRICE_REFRESH: true,
        ENABLE_FUNDAMENTAL_REFRESH: true,
        ENABLE_NOTIFICATIONS: true,

        // UI feedback
        SHOW_REFRESH_INDICATOR: true
    };

    // Auto-refresh state
    let priceRefreshTimer = null;
    let fundamentalRefreshTimer = null;
    let lastPriceRefresh = null;
    let lastFundamentalRefresh = null;
    let refreshCount = 0;

    /**
     * Initialize auto-refresh system
     */
    function init() {
        console.log('🔄 Auto-refresh system initializing...');

        // Add refresh indicator to page
        if (AUTO_REFRESH_CONFIG.SHOW_REFRESH_INDICATOR) {
            addRefreshIndicator();
        }

        // Start refresh timers after initial delay
        setTimeout(() => {
            if (AUTO_REFRESH_CONFIG.ENABLE_PRICE_REFRESH) {
                startPriceRefresh();
            }

            if (AUTO_REFRESH_CONFIG.ENABLE_FUNDAMENTAL_REFRESH) {
                startFundamentalRefresh();
            }

            console.log('✅ Auto-refresh system active');
        }, AUTO_REFRESH_CONFIG.INITIAL_DELAY);

        // Add visibility change listener (pause when tab hidden)
        document.addEventListener('visibilitychange', handleVisibilityChange);
    }

    /**
     * Add refresh indicator to page
     */
    function addRefreshIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'auto-refresh-indicator';
        indicator.innerHTML = `
            <div style="
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: rgba(0, 0, 0, 0.85);
                color: #0f0;
                padding: 12px 20px;
                border-radius: 8px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                z-index: 9999;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
                border: 1px solid #0f0;
            ">
                <div style="margin-bottom: 5px; font-weight: bold;">🔄 Auto-Refresh Active</div>
                <div id="refresh-status" style="opacity: 0.7;">
                    Next price update: <span id="next-price-refresh">--:--</span><br>
                    Next fundamental update: <span id="next-fundamental-refresh">--:--</span><br>
                    <span style="font-size: 10px;">Refresh count: <span id="refresh-count">0</span></span>
                </div>
            </div>
        `;
        document.body.appendChild(indicator);

        // Update countdown every second
        setInterval(updateRefreshCountdown, 1000);
    }

    /**
     * Update refresh countdown display
     */
    function updateRefreshCountdown() {
        const now = Date.now();

        // Price refresh countdown
        if (lastPriceRefresh) {
            const nextPriceRefresh = lastPriceRefresh + AUTO_REFRESH_CONFIG.PRICE_DATA_INTERVAL;
            const timeUntilPrice = Math.max(0, nextPriceRefresh - now);
            const minutesPrice = Math.floor(timeUntilPrice / 60000);
            const secondsPrice = Math.floor((timeUntilPrice % 60000) / 1000);

            const priceEl = document.getElementById('next-price-refresh');
            if (priceEl) {
                priceEl.textContent = `${minutesPrice}:${secondsPrice.toString().padStart(2, '0')}`;
            }
        }

        // Fundamental refresh countdown
        if (lastFundamentalRefresh) {
            const nextFundamentalRefresh = lastFundamentalRefresh + AUTO_REFRESH_CONFIG.FUNDAMENTAL_DATA_INTERVAL;
            const timeUntilFundamental = Math.max(0, nextFundamentalRefresh - now);
            const minutesFundamental = Math.floor(timeUntilFundamental / 60000);
            const secondsFundamental = Math.floor((timeUntilFundamental % 60000) / 1000);

            const fundamentalEl = document.getElementById('next-fundamental-refresh');
            if (fundamentalEl) {
                fundamentalEl.textContent = `${minutesFundamental}:${secondsFundamental.toString().padStart(2, '0')}`;
            }
        }

        // Update refresh count
        const countEl = document.getElementById('refresh-count');
        if (countEl) {
            countEl.textContent = refreshCount;
        }
    }

    /**
     * Start price data refresh cycle
     */
    function startPriceRefresh() {
        console.log(`🔄 Price refresh cycle started (every ${AUTO_REFRESH_CONFIG.PRICE_DATA_INTERVAL / 60000} minutes)`);

        // Initial refresh
        refreshPriceData();

        // Schedule periodic refreshes
        priceRefreshTimer = setInterval(() => {
            refreshPriceData();
        }, AUTO_REFRESH_CONFIG.PRICE_DATA_INTERVAL);
    }

    /**
     * Start fundamental data refresh cycle
     */
    function startFundamentalRefresh() {
        console.log(`🔄 Fundamental refresh cycle started (every ${AUTO_REFRESH_CONFIG.FUNDAMENTAL_DATA_INTERVAL / 60000} minutes)`);

        // Initial refresh
        refreshFundamentalData();

        // Schedule periodic refreshes
        fundamentalRefreshTimer = setInterval(() => {
            refreshFundamentalData();
        }, AUTO_REFRESH_CONFIG.FUNDAMENTAL_DATA_INTERVAL);
    }

    /**
     * Refresh price data
     */
    async function refreshPriceData() {
        console.log('📊 Refreshing price data...');
        lastPriceRefresh = Date.now();
        refreshCount++;

        try {
            // Get all symbols currently displayed on the page
            const symbols = getDisplayedSymbols();

            if (symbols.length === 0) {
                console.log('ℹ️  No symbols to refresh');
                return;
            }

            console.log(`📊 Refreshing ${symbols.length} symbols...`);

            // Refresh each symbol
            let successCount = 0;
            for (const symbol of symbols) {
                try {
                    const response = await fetch(`/api/market/symbol/${symbol}`);
                    if (response.ok) {
                        const data = await response.json();
                        updateSymbolDisplay(symbol, data.data);
                        successCount++;
                    }
                } catch (error) {
                    console.error(`Error refreshing ${symbol}:`, error);
                }
            }

            console.log(`✅ Price refresh complete: ${successCount}/${symbols.length} symbols updated`);

            if (AUTO_REFRESH_CONFIG.ENABLE_NOTIFICATIONS) {
                showNotification('Price data updated', `${successCount} symbols refreshed`);
            }

        } catch (error) {
            console.error('❌ Price refresh error:', error);
        }
    }

    /**
     * Refresh fundamental data
     */
    async function refreshFundamentalData() {
        console.log('📈 Refreshing fundamental data...');
        lastFundamentalRefresh = Date.now();

        try {
            // Refresh economic indicators
            await refreshEconomicIndicators();

            // Refresh forex rates
            await refreshForexRates();

            console.log('✅ Fundamental refresh complete');

            if (AUTO_REFRESH_CONFIG.ENABLE_NOTIFICATIONS) {
                showNotification('Fundamental data updated', 'Economic indicators refreshed');
            }

        } catch (error) {
            console.error('❌ Fundamental refresh error:', error);
        }
    }

    /**
     * Get symbols currently displayed on page
     */
    function getDisplayedSymbols() {
        const symbols = [];

        // Look for elements with data-symbol attribute
        const elements = document.querySelectorAll('[data-symbol]');
        elements.forEach(el => {
            const symbol = el.getAttribute('data-symbol');
            if (symbol && !symbols.includes(symbol)) {
                symbols.push(symbol);
            }
        });

        // Fallback: try to extract from visible text
        if (symbols.length === 0) {
            // Add common major indices
            symbols.push('SPY', 'QQQ', 'DIA', 'IWM');
        }

        return symbols;
    }

    /**
     * Update symbol display on page
     */
    function updateSymbolDisplay(symbol, data) {
        // Find all elements for this symbol
        const elements = document.querySelectorAll(`[data-symbol="${symbol}"]`);

        elements.forEach(el => {
            // Update price
            const priceEl = el.querySelector('.price') || el.querySelector('[data-price]');
            if (priceEl && data.price) {
                priceEl.textContent = `$${data.price.toFixed(2)}`;

                // Add flash animation
                priceEl.classList.add('updated');
                setTimeout(() => priceEl.classList.remove('updated'), 1000);
            }

            // Update volume
            const volumeEl = el.querySelector('.volume') || el.querySelector('[data-volume]');
            if (volumeEl && data.volume) {
                volumeEl.textContent = formatVolume(data.volume);
            }

            // Update timestamp
            const timestampEl = el.querySelector('.timestamp') || el.querySelector('[data-timestamp]');
            if (timestampEl && data.timestamp) {
                timestampEl.textContent = `Updated: ${new Date(data.timestamp).toLocaleTimeString()}`;
            }
        });
    }

    /**
     * Refresh economic indicators
     */
    async function refreshEconomicIndicators() {
        const indicators = ['GDP', 'UNRATE', 'CPIAUCSL', 'FEDFUNDS'];

        for (const indicator of indicators) {
            try {
                // Economic endpoint will be added
                const response = await fetch(`/api/fundamental/economic/${indicator}`);
                if (response.ok) {
                    const data = await response.json();
                    updateIndicatorDisplay(indicator, data);
                }
            } catch (error) {
                console.debug(`Indicator ${indicator} not yet available`);
            }
        }
    }

    /**
     * Refresh forex rates
     */
    async function refreshForexRates() {
        const pairs = ['EURUSD', 'GBPUSD', 'USDJPY'];

        for (const pair of pairs) {
            try {
                const response = await fetch(`/api/fundamental/forex/${pair}`);
                if (response.ok) {
                    const data = await response.json();
                    updateForexDisplay(pair, data);
                }
            } catch (error) {
                console.debug(`Forex ${pair} not yet available`);
            }
        }
    }

    /**
     * Update indicator display
     */
    function updateIndicatorDisplay(indicator, data) {
        const el = document.querySelector(`[data-indicator="${indicator}"]`);
        if (el && data.value) {
            el.textContent = data.value.toFixed(2);
        }
    }

    /**
     * Update forex display
     */
    function updateForexDisplay(pair, data) {
        const el = document.querySelector(`[data-forex="${pair}"]`);
        if (el && data.price) {
            el.textContent = data.price.toFixed(4);
        }
    }

    /**
     * Show notification
     */
    function showNotification(title, message) {
        // Create temporary notification
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0, 255, 0, 0.9);
            color: #000;
            padding: 15px 20px;
            border-radius: 8px;
            font-family: Arial, sans-serif;
            font-size: 14px;
            z-index: 10000;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            animation: slideIn 0.3s ease-out;
        `;
        notification.innerHTML = `
            <div style="font-weight: bold; margin-bottom: 5px;">${title}</div>
            <div style="opacity: 0.8;">${message}</div>
        `;

        document.body.appendChild(notification);

        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    /**
     * Format volume numbers
     */
    function formatVolume(volume) {
        if (volume >= 1000000) {
            return `${(volume / 1000000).toFixed(1)}M`;
        } else if (volume >= 1000) {
            return `${(volume / 1000).toFixed(1)}K`;
        }
        return volume.toString();
    }

    /**
     * Handle visibility change (pause when hidden)
     */
    function handleVisibilityChange() {
        if (document.hidden) {
            console.log('⏸️  Page hidden - pausing refresh');
            // Timers continue but we could pause them if needed
        } else {
            console.log('▶️  Page visible - resuming refresh');
            // Trigger immediate refresh when page becomes visible
            if (AUTO_REFRESH_CONFIG.ENABLE_PRICE_REFRESH) {
                refreshPriceData();
            }
        }
    }

    /**
     * Stop all refresh cycles
     */
    function stop() {
        if (priceRefreshTimer) {
            clearInterval(priceRefreshTimer);
            priceRefreshTimer = null;
        }
        if (fundamentalRefreshTimer) {
            clearInterval(fundamentalRefreshTimer);
            fundamentalRefreshTimer = null;
        }
        console.log('🛑 Auto-refresh stopped');
    }

    // Add CSS animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(400px);
                opacity: 0;
            }
        }

        .updated {
            animation: flash 1s ease-out;
        }

        @keyframes flash {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; background-color: #0f0; }
        }
    `;
    document.head.appendChild(style);

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Export functions for manual control
    window.SpartanAutoRefresh = {
        init,
        stop,
        refreshPriceData,
        refreshFundamentalData,
        config: AUTO_REFRESH_CONFIG
    };

})();
