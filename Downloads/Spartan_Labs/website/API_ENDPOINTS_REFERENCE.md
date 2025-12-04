# Spartan Research Station - API Endpoints Reference

## ✅ Server Status
All 5 API servers are **RUNNING** and healthy.

## Port Assignments

| Port | Server | File | Status |
|------|--------|------|--------|
| 5000 | Daily Planet API | daily_planet_api.py | ✅ Running |
| 5002 | Swing Dashboard API | swing_dashboard_api.py | ✅ Running |
| 5003 | GARP API | garp_api.py | ✅ Running |
| 5004 | Correlation API | correlation_api.py | ✅ Running |
| 8888 | Main Server | start_server.py | ✅ Running |

---

## Port 5000 - Daily Planet API

**Health Check**: `GET /health`

### Endpoints

- `GET /api/market-news` - Latest market news
- `GET /api/economic-calendar` - Economic events calendar
- `POST /api/market-movers` - Top gainers/losers
- `POST /api/sector-rotation` - Sector performance
- `GET /api/sentiment-analysis` - Market sentiment

**Used By**: daily_planet.html

---

## Port 5002 - Swing Dashboard API

**Health Check**: `GET /api/swing-dashboard/health`

### Endpoints

#### Market Data
- `GET /api/swing-dashboard/market-indices` - Major indices (SPY, QQQ, DIA)
- `GET /api/swing-dashboard/volatility` - VIX, VVIX, volatility metrics
- `GET /api/swing-dashboard/forex` - Currency pairs
- `GET /api/swing-dashboard/commodities` - Gold, Oil, Copper

#### Economic Data
- `GET /api/swing-dashboard/credit-spreads` - High Yield, Investment Grade
- `GET /api/swing-dashboard/treasury-yields` - US Treasury yields
- `GET /api/swing-dashboard/sector-rotation` - Sector ETF performance
- `GET /api/swing-dashboard/market-health` - Overall market health score

#### Data Proxies (FRED, Yahoo, Alpha Vantage)
- `GET /api/fred/series/observations` - FRED economic data
- `GET /api/fred/<path:fred_path>` - Generic FRED proxy
- `GET /api/yahoo/quote` - Yahoo Finance quote data
- `GET /api/yahoo/chart/<symbol>` - Yahoo Finance chart data
- `GET /api/alpha-vantage/query` - Alpha Vantage data

**Used By**: global_capital_flow_swing_trading.html, tab_1_2_weeks_swing.html, barometers.html, fred_global_complete.html

---

## Port 5003 - GARP API

**Health Check**: `GET /api/health`

### Endpoints

- `GET /api/garp/screen` - Screen stocks by GARP criteria
- `GET /api/garp/stock/<symbol>` - Get individual stock GARP metrics
- `GET /api/garp/sectors` - GARP analysis by sector

**Used By**: garp.html

---

## Port 5004 - Correlation API

**Health Check**: `GET /health`

### Endpoints

- `GET /api/correlations` - Full correlation matrix (48 assets)
- `GET /api/metadata` - Asset metadata (names, categories)
- `GET /api/assets` - List of tracked assets

**Used By**: correlation_matrix.html, bitcoin_correlations.html

---

## Port 8888 - Main Server

**Health Check**: `GET /health`

### Endpoints

#### Symbol Database
- `GET /api/db/stats` - Database statistics
- `GET /api/db/search?query=<symbol>&limit=<n>` - Search symbols
- `GET /api/db/symbols?category=<cat>` - Get symbols by category

**Used By**: All HTML pages (static file server)

---

## Common Issues & Fixes

### ❌ Issue: Using port 8888 for /api/yahoo/quote
**Incorrect**: `http://localhost:8888/api/yahoo/quote?symbols=${symbol}`
**Correct**: `http://localhost:5002/api/yahoo/quote?symbols=${symbol}`

**Affected Files**: tab_1_2_weeks_swing.html

### ✅ Recommended Usage: Preloader Cache

Instead of fetching directly, check preloader cache first:

```javascript
// ✅ CORRECT - Check preloader first
if (window.SpartanData && window.SpartanData.market_data) {
    const data = window.SpartanData.market_data;
    // Use cached data
} else {
    // Fallback to API fetch
    const response = await fetch('http://localhost:5002/api/yahoo/quote?symbols=SPY');
}
```

**Files Using Preloader** (Good examples):
- barometers.html
- daily_dose.html
- market_gauges.html

**Files NOT Using Preloader** (Need fix):
- 29 files fetch without checking cache first

---

## Testing API Endpoints

```bash
# Test all health endpoints
curl http://localhost:5000/health
curl http://localhost:5002/api/swing-dashboard/health
curl http://localhost:5003/api/health
curl http://localhost:5004/health
curl http://localhost:8888/health

# Test specific endpoints
curl "http://localhost:5002/api/yahoo/quote?symbols=SPY"
curl "http://localhost:5004/api/correlations"
curl "http://localhost:8888/api/db/stats"
```

---

**Last Updated**: November 19, 2025
**Status**: All servers operational
**Next Steps**: Fix incorrect port usage, add preloader cache integration
