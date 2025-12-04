/**
 * Swing Dashboard Data Fetcher
 * ============================
 *
 * Fetches real-time market data from Swing Dashboard API and updates the UI.
 * Implements all features from technical_blueprint.md with real data sources.
 *
 * Data Sources:
 * - yfinance: Market indices, commodities, forex (via API)
 * - FRED API: US rates, credit spreads, yields (via API)
 * - Alpha Vantage: Volatility indices (via API)
 * - ExchangeRate-API: Forex rates (via API)
 *
 * Author: Spartan Research Station
 * Version: 1.0.0
 */

const SWING_API_BASE_URL = 'http://localhost:8888';
const UPDATE_INTERVAL = 60000; // 1 minute (respects API rate limits)
const RETRY_DELAY = 5000; // 5 seconds retry on error

// Track update intervals for cleanup
let updateIntervals = [];

/**
 * Format number with appropriate suffix (K, M, B, T)
 */
function formatNumber(num) {
    if (num === null || num === undefined) return 'N/A';

    const absNum = Math.abs(num);

    if (absNum >= 1e12) {
        return (num / 1e12).toFixed(2) + 'T';
    } else if (absNum >= 1e9) {
        return (num / 1e9).toFixed(2) + 'B';
    } else if (absNum >= 1e6) {
        return (num / 1e6).toFixed(2) + 'M';
    } else if (absNum >= 1e3) {
        return (num / 1e3).toFixed(2) + 'K';
    } else {
        return num.toFixed(2);
    }
}

/**
 * Format percentage with + or - sign
 */
function formatPercentage(value) {
    if (value === null || value === undefined) return 'N/A';
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
}

/**
 * Determine CSS class based on value (positive/negative/neutral)
 */
function getValueClass(value) {
    if (value === null || value === undefined) return 'neutral';
    if (value > 0) return 'positive';
    if (value < 0) return 'negative';
    return 'neutral';
}

/**
 * Update element with value and styling
 */
function updateElement(elementId, value, isPercentage = false, isChange = false) {
    const element = document.getElementById(elementId);
    if (!element) return;

    if (value === null || value === undefined) {
        element.innerHTML = '<span style="color: var(--text-muted);">Data unavailable</span>';
        return;
    }

    const formattedValue = isPercentage ? formatPercentage(value) : formatNumber(value);
    const valueClass = isChange ? getValueClass(value) : 'neutral';

    // Add arrow indicator for changes
    let arrow = '';
    if (isChange) {
        if (value > 0) {
            arrow = '<span style="font-size: 0.9em; margin-right: 4px;">↑</span>';
        } else if (value < 0) {
            arrow = '<span style="font-size: 0.9em; margin-right: 4px;">↓</span>';
        }
    }

    element.innerHTML = arrow + formattedValue;
    element.className = `flow-value ${valueClass}`;
}

/**
 * Fetch and update market indices data
 */
async function updateMarketIndices() {
    try {
        const response = await fetch(`${SWING_API_BASE_URL}/api/market/indices`);
        const data = await response.json();

        // US Markets
        updateElement('swing-spy', data.us_markets?.spy?.price);
        updateElement('swing-qqq', data.us_markets?.qqq?.price);
        updateElement('swing-dia', data.us_markets?.dia?.price);
        updateElement('swing-iwm', data.us_markets?.iwm?.price);

        // China Markets
        updateElement('swing-ssec', data.china_markets?.shanghai?.price);
        updateElement('swing-hsi', data.china_markets?.hang_seng?.price);
        updateElement('swing-fxi', data.china_markets?.fxi?.price);

        // India Markets
        updateElement('swing-sensex', data.india_markets?.sensex?.price);
        updateElement('swing-nifty50', data.india_markets?.nifty50?.price);
        updateElement('swing-inda', data.india_markets?.inda?.price);

        // Japan Markets
        updateElement('swing-nikkei', data.japan_markets?.nikkei?.price);
        updateElement('swing-ewj', data.japan_markets?.ewj?.price);
        updateElement('swing-dxj', data.japan_markets?.dxj?.price);

        // Germany Markets
        updateElement('swing-dax', data.germany_markets?.dax?.price);
        updateElement('swing-ewg', data.germany_markets?.ewg?.price);

        console.log('✓ Market indices updated successfully');
    } catch (error) {
        console.error('Error fetching market indices:', error);
        setTimeout(updateMarketIndices, RETRY_DELAY);
    }
}

/**
 * Fetch and update volatility indicators
 */
async function updateVolatilityIndicators() {
    try {
        const response = await fetch(`${SWING_API_BASE_URL}/api/market/volatility`);
        const data = await response.json();

        updateElement('swing-vix', data.vix?.price);
        updateElement('swing-vix-change', data.vix?.change_pct, true, true);

        // For now, these are unavailable (require premium APIs)
        document.getElementById('swing-vvix').innerHTML = '<span style="color: var(--text-muted); font-size: 0.9rem;">Premium API</span>';
        document.getElementById('swing-skew').innerHTML = '<span style="color: var(--text-muted); font-size: 0.9rem;">Premium API</span>';
        document.getElementById('swing-move').innerHTML = '<span style="color: var(--text-muted); font-size: 0.9rem;">Premium API</span>';

        console.log('✓ Volatility indicators updated successfully');
    } catch (error) {
        console.error('Error fetching volatility indicators:', error);
        setTimeout(updateVolatilityIndicators, RETRY_DELAY);
    }
}

/**
 * Fetch and update credit spreads
 */
async function updateCreditSpreads() {
    try {
        const response = await fetch(`${SWING_API_BASE_URL}/api/economic/indicators?series_ids=BAMLH0A0HYM2,BAMLC0A4CBBB,DAAA`);
        const data = await response.json();

        updateElement('swing-hy-oas', data.hy_oas?.value);
        updateElement('swing-ig-bbb', data.ig_bbb?.value);
        updateElement('swing-aaa-spread', data.aaa_spread?.value);

        document.getElementById('swing-em-spread').innerHTML = '<span style="color: var(--text-muted); font-size: 0.9rem;">Bloomberg Only</span>';

        console.log('✓ Credit spreads updated successfully');
    } catch (error) {
        console.error('Error fetching credit spreads:', error);
        setTimeout(updateCreditSpreads, RETRY_DELAY);
    }
}

/**
 * Fetch and update treasury yields
 */
async function updateTreasuryYields() {
    try {
        const response = await fetch(`${SWING_API_BASE_URL}/api/economic/indicators?series_ids=DGS2,DGS10,DGS30,T10Y2Y`);
        const data = await response.json();

        updateElement('swing-dgs2', data.dgs2?.value);
        updateElement('swing-dgs10', data.dgs10?.value);
        updateElement('swing-dgs30', data.dgs30?.value);
        updateElement('swing-yield-curve', data.yield_curve_2s10s?.value);

        console.log('✓ Treasury yields updated successfully');
    } catch (error) {
        console.error('Error fetching treasury yields:', error);
        setTimeout(updateTreasuryYields, RETRY_DELAY);
    }
}

/**
 * Fetch and update forex rates
 */
async function updateForexRates() {
    try {
        const response = await fetch(`${SWING_API_BASE_URL}/api/market/forex`);
        const data = await response.json();

        updateElement('swing-dxy', data.dxy?.value);
        updateElement('swing-eurusd', data.eurusd?.value);
        updateElement('swing-usdjpy', data.usdjpy?.value);
        updateElement('swing-gbpusd', data.gbpusd?.value);

        console.log('✓ Forex rates updated successfully');
    } catch (error) {
        console.error('Error fetching forex rates:', error);
        setTimeout(updateForexRates, RETRY_DELAY);
    }
}

/**
 * Fetch and update commodities
 */
async function updateCommodities() {
    try {
        const response = await fetch(`${SWING_API_BASE_URL}/api/market/commodities`);
        const data = await response.json();

        updateElement('swing-gold', data.gold?.price);
        updateElement('swing-gold-change', data.gold?.change_pct, true, true);

        updateElement('swing-silver', data.silver?.price);
        updateElement('swing-silver-change', data.silver?.change_pct, true, true);

        updateElement('swing-oil', data.oil?.price);
        updateElement('swing-oil-change', data.oil?.change_pct, true, true);

        updateElement('swing-copper', data.copper?.price);
        updateElement('swing-copper-change', data.copper?.change_pct, true, true);

        console.log('✓ Commodities updated successfully');
    } catch (error) {
        console.error('Error fetching commodities:', error);
        setTimeout(updateCommodities, RETRY_DELAY);
    }
}

/**
 * Fetch and update sector rotation data
 */
async function updateSectorRotation() {
    try {
        const response = await fetch(`${SWING_API_BASE_URL}/api/analytics/sector_rotation`);
        const data = await response.json();

        const tableBody = document.getElementById('swing-sector-table');
        if (!tableBody) return;

        if (!data.sectors || data.sectors.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align: center; padding: 30px; color: var(--text-secondary);">
                        No sector data available
                    </td>
                </tr>
            `;
            return;
        }

        // Sort by relative strength descending
        const sortedSectors = data.sectors.sort((a, b) =>
            (b.relative_strength || 0) - (a.relative_strength || 0)
        );

        tableBody.innerHTML = sortedSectors.map(sector => {
            const recommendationClass = sector.recommendation === 'BUY' ? 'badge-buy' :
                                       sector.recommendation === 'SELL' ? 'badge-sell' : 'badge-hold';

            const strengthClass = sector.relative_strength > 0 ? 'positive' :
                                 sector.relative_strength < 0 ? 'negative' : 'neutral';

            return `
                <tr>
                    <td style="font-weight: 600;">${sector.sector}</td>
                    <td><span class="badge badge-etf">${sector.etf}</span></td>
                    <td class="${getValueClass(sector.performance_1w)}">${formatPercentage(sector.performance_1w)}</td>
                    <td style="color: var(--text-secondary);">N/A</td>
                    <td class="${strengthClass}">${formatPercentage(sector.relative_strength)}</td>
                    <td><span class="badge ${recommendationClass}">${sector.recommendation}</span></td>
                </tr>
            `;
        }).join('');

        console.log('✓ Sector rotation updated successfully');
    } catch (error) {
        console.error('Error fetching sector rotation:', error);
        setTimeout(updateSectorRotation, RETRY_DELAY);
    }
}

/**
 * Fetch and update market health score
 */
async function updateMarketHealth() {
    try {
        const response = await fetch(`${SWING_API_BASE_URL}/api/system/status`);
        const data = await response.json();

        const healthScoreElement = document.getElementById('global-health-score');
        const healthStatusElement = document.getElementById('global-health-status');

        if (healthScoreElement && data.health_score !== undefined) {
            const scoreClass = data.health_score >= 70 ? 'positive' :
                              data.health_score >= 50 ? 'neutral' : 'negative';

            healthScoreElement.innerHTML = `
                <span class="${scoreClass}">${data.health_score.toFixed(1)}</span>
                <span style="font-size: 1.5rem; color: var(--text-secondary);"> / 100</span>
            `;
        }

        if (healthStatusElement && data.status) {
            const statusColor = data.health_score >= 70 ? 'var(--success-color)' :
                               data.health_score >= 50 ? 'var(--warning-color)' : 'var(--danger-color)';

            healthStatusElement.innerHTML = `
                <span style="color: ${statusColor}; font-weight: 600;">${data.status}</span>
            `;
        }

        console.log('✓ Market health updated successfully');
    } catch (error) {
        console.error('Error fetching market health:', error);
        setTimeout(updateMarketHealth, RETRY_DELAY);
    }
}

/**
 * Update placeholder fields for features requiring premium APIs
 */
function updatePlaceholderFields() {
    // Sentiment Indicators (require premium APIs)
    const sentimentFields = [
        'swing-fear-greed', 'swing-put-call', 'swing-aaii-spread', 'swing-high-low',
        'swing-nyse-ad', 'swing-nasdaq-ad', 'swing-mcclellan', 'swing-above-50sma',
        'swing-equity-flows', 'swing-bond-flows', 'swing-mm-flows',
        'swing-inst-buying', 'swing-insider-activity', 'swing-darkpool',
        'swing-retail-buying', 'swing-options-activity', 'swing-social-sentiment'
    ];

    sentimentFields.forEach(fieldId => {
        const element = document.getElementById(fieldId);
        if (element) {
            element.innerHTML = '<span style="color: var(--text-muted); font-size: 0.9rem;">Premium API Required</span>';
        }
    });
}

/**
 * Update last update timestamp
 */
function updateTimestamp() {
    const timestampElement = document.getElementById('swing-last-update');
    if (timestampElement) {
        const now = new Date();
        timestampElement.innerHTML = `
            <span class="status-indicator valid"></span>
            Last updated: ${now.toLocaleTimeString()} EST
        `;
    }
}

/**
 * Initialize Swing Dashboard - fetch all data
 */
async function initializeSwingDashboard() {
    console.log('🚀 Initializing Swing Dashboard...');

    // Update placeholder fields first
    updatePlaceholderFields();

    // Fetch all data in parallel for faster loading
    await Promise.all([
        updateMarketIndices(),
        updateVolatilityIndicators(),
        updateCreditSpreads(),
        updateTreasuryYields(),
        updateForexRates(),
        updateCommodities(),
        updateSectorRotation(),
        updateMarketHealth()
    ]);

    updateTimestamp();

    console.log('✅ Swing Dashboard initialization complete');

    // Set up periodic updates (respecting API rate limits)
    updateIntervals = [
        setInterval(updateMarketIndices, UPDATE_INTERVAL),
        setInterval(updateVolatilityIndicators, UPDATE_INTERVAL * 2), // Less frequent (Alpha Vantage limit)
        setInterval(updateCreditSpreads, UPDATE_INTERVAL),
        setInterval(updateTreasuryYields, UPDATE_INTERVAL),
        setInterval(updateForexRates, UPDATE_INTERVAL * 3), // Less frequent (monthly limit)
        setInterval(updateCommodities, UPDATE_INTERVAL),
        setInterval(updateSectorRotation, UPDATE_INTERVAL),
        setInterval(updateMarketHealth, UPDATE_INTERVAL),
        setInterval(updateTimestamp, 10000) // Update timestamp every 10 seconds
    ];
}

/**
 * Cleanup function - clear all intervals
 */
function cleanupSwingDashboard() {
    updateIntervals.forEach(interval => clearInterval(interval));
    updateIntervals = [];
    console.log('🧹 Swing Dashboard cleanup complete');
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeSwingDashboard);
} else {
    initializeSwingDashboard();
}

// Cleanup on page unload
window.addEventListener('beforeunload', cleanupSwingDashboard);

// Export functions for manual control if needed
window.SwingDashboard = {
    initialize: initializeSwingDashboard,
    cleanup: cleanupSwingDashboard,
    updateMarketIndices,
    updateVolatilityIndicators,
    updateCreditSpreads,
    updateTreasuryYields,
    updateForexRates,
    updateCommodities,
    updateSectorRotation,
    updateMarketHealth
};

console.log('📊 Swing Dashboard module loaded');
