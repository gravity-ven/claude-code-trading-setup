# Preloader Cache Integration Guide

## Overview

The Spartan Research Station uses a preloader system (`spartan-preloader.js`) that caches data in `window.SpartanData` to reduce API calls and improve performance.

## Benefits

✅ **Faster page loads** - Data ready before page fully loads
✅ **Reduced API calls** - Less server load
✅ **Better UX** - No loading spinners for cached data
✅ **Offline resilience** - Cached data available even if API is slow/down

## How Preloader Works

1. `spartan-preloader.js` runs on page load (included in most pages)
2. Fetches data from APIs (ports 5000, 5002, 5004)
3. Stores in `window.SpartanData` object
4. Pages check cache before fetching

## Files Currently Using Preloader ✅

These files serve as **good examples**:

1. `barometers.html` - Uses preloaded FRED data
2. `daily_dose.html` - Uses preloaded market data
3. `market_gauges.html` - Uses preloaded indicators

## Preloader Data Structure

```javascript
window.SpartanData = {
    // Market indices (from port 5002)
    market_data: {
        SPY: { price: 450.25, change: 1.5, change_pct: 0.33 },
        QQQ: { price: 380.50, change: -2.1, change_pct: -0.55 }
    },

    // FRED economic data (from port 5002)
    fred_data: {
        DFF: [ {date: "2025-11-19", value: 5.33} ],
        UNRATE: [ {date: "2025-10-01", value: 3.7} ]
    },

    // Correlation matrix (from port 5004)
    correlation_data: {
        matrix: [ [1.0, 0.8, ...], ... ],
        assets: ["SPY", "QQQ", ...]
    },

    // Daily Planet news (from port 5000)
    news_data: {
        market_news: [...],
        economic_calendar: [...]
    }
}
```

## Integration Pattern

### ❌ INCORRECT (Direct API Call)

```javascript
async function loadMarketData() {
    const response = await fetch('http://localhost:5002/api/yahoo/quote?symbols=SPY');
    const data = await response.json();
    updateUI(data);
}
```

### ✅ CORRECT (Check Cache First)

```javascript
async function loadMarketData() {
    // Check preloader cache first
    if (window.SpartanData && window.SpartanData.market_data && window.SpartanData.market_data.SPY) {
        console.log('✅ Using preloaded data');
        updateUI({ data: window.SpartanData.market_data });
        return;
    }

    // Fallback to API if cache miss
    console.log('⚠️ Cache miss - fetching from API');
    try {
        const response = await fetch('http://localhost:5002/api/yahoo/quote?symbols=SPY');
        const data = await response.json();
        updateUI(data);
    } catch (error) {
        console.error('❌ API fetch failed:', error);
        showErrorState();
    }
}
```

## Complete Example: Barometers.html Pattern

```javascript
async function loadFREDData() {
    // 1. Check preloader cache
    if (window.SpartanData && window.SpartanData.fred_data) {
        const data = window.SpartanData.fred_data;
        console.log('✅ Using preloaded FRED data');

        // Process cached data
        if (data.DFF) {
            updateFedFundsRate(data.DFF);
        }
        if (data.UNRATE) {
            updateUnemployment(data.UNRATE);
        }
        return;
    }

    // 2. Fallback to API
    console.log('⚠️ Preloader not available - fetching from API');
    try {
        const dffData = await fetchFREDData('DFF', 1);
        const unrateData = await fetchFREDData('UNRATE', 1);

        updateFedFundsRate(dffData);
        updateUnemployment(unrateData);
    } catch (error) {
        console.error('❌ FRED API failed:', error);
        showErrorState();
    }
}

async function fetchFREDData(series, limit) {
    const response = await fetch(
        `http://localhost:5002/api/fred/series/observations?series_id=${series}&limit=${limit}`
    );
    return await response.json();
}
```

## Files That Need Preloader Integration (29 files)

These files currently fetch without checking cache:

### High Priority (Heavy API Users)
- `fred_global_complete.html` - Multiple FRED series
- `econometrics.html` - Historical data
- `harmonic_cycles.html` - Price data
- `symbol_search_connections.html` - VIX/market data
- `global_capital_flow_swing_trading.html` - Multiple sources

### Medium Priority
- `bitcoin_correlations.html`
- `correlation_matrix.html`
- `breakthrough_insights.html`
- `daily_planet.html`
- `garp.html`

### All Others
- fundamental_analysis.html
- gold_intelligence.html
- highlights.html
- index.html
- intermarket_relationships.html
- market_cycles.html
- oil_intelligence.html
- pattern_discovery_terminal.html
- pattern_finder_hub.html
- seasonality_research.html
- symbol_research.html
- tab_1_2_weeks_swing.html
- test_market_health.html
- test_page_validation.html
- unified_market_dashboard.html

## Migration Steps

For each file:

1. **Identify API calls**
   ```bash
   grep -n "fetch.*localhost" your_file.html
   ```

2. **Add cache check**
   ```javascript
   // Before: Direct fetch
   const data = await fetch('http://localhost:5002/api/yahoo/quote?symbols=SPY');

   // After: Cache-aware
   if (window.SpartanData?.market_data?.SPY) {
       data = window.SpartanData.market_data;
   } else {
       data = await fetch('http://localhost:5002/api/yahoo/quote?symbols=SPY');
   }
   ```

3. **Test**
   - Open DevTools Console
   - Check for `✅ Using preloaded data` messages
   - Verify no duplicate API calls

4. **Fallback safety**
   - Always include try/catch
   - Always have API fallback
   - Never assume cache exists

## Debugging Preloader

### Check Cache Contents

```javascript
// In browser console
console.log(window.SpartanData);
```

### Verify Preloader Loaded

```javascript
// Should see loading messages
// "🔄 Preloading market data..."
// "✅ Preloader complete"
```

### Check Network Tab

- ✅ Good: 1 API call per endpoint (from preloader)
- ❌ Bad: Multiple calls to same endpoint (missing cache check)

## Performance Metrics

**Before Preloader**:
- Page load: 3-5 seconds
- API calls: 20-30 per page
- Data ready: After DOM load

**After Preloader**:
- Page load: 1-2 seconds
- API calls: 5-10 per page (preloader only)
- Data ready: On DOM load

## Next Steps

1. **Audit remaining 29 files** for cache integration opportunities
2. **Add cache checks** following the pattern above
3. **Test** with DevTools Network tab
4. **Monitor** cache hit rates

---

**Last Updated**: November 19, 2025
**Status**: 3/47 files using preloader (6%)
**Goal**: 80%+ cache usage for frequently accessed data
