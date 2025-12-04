# SPARTAN LABS WEBSITE INVENTORY - QUICK REFERENCE SUMMARY

Generated: 2025-11-30 | Complete Detailed Report: `SPARTAN_INVENTORY_REPORT.md`

---

## CRITICAL FACTS AT A GLANCE

Total Pages: 58 | API Servers: 6 | Data Sources: 13+ | Database: PostgreSQL

---

## PAGE CATEGORIES (12 Categories, 58 Pages)

### Quick Navigation by Purpose

```
1. ENTRY POINTS (4)              → Start here: index.html
2. ASSET INTELLIGENCE (6)        → Deep dives: Gold, Bitcoin, Oil, Bonds, Copper, Silver
3. TRADING TIMEFRAMES (4)        → 1-2w, 1-3m, 6-18m, 18-36m swing setups
4. MACRO ANALYSIS (10)           → FRED, economic indicators, inflation, seasonality
5. SCREENERS (7)                 → GARP, Nano Banana, Pattern Discovery
6. CORRELATIONS (4)              → Intermarket relationships, capital flow
7. SENTIMENT (5)                 → Daily Planet, news, breakthroughs, highlights
8. SPECIALIZED (4)               → COT terminal, crypto composite, strategies
9. TRADING JOURNAL (1)           → Trade tracking, equity curve, P&L
10. ADVANCED DASHBOARDS (2)      → Unified dashboard, AlphaStream terminal
11. RESEARCH (2)                 → Historical connections, flashcards
12. TESTING (3+)                 → Diagnostics, validation, utilities
```

---

## REACT MIGRATION PRIORITY

### Tier 1: CRITICAL (5 pages) - Start Here
1. **index.html** - Main dashboard
2. **daily_planet.html** - News aggregation
3. **correlation_matrix.html** - Intermarket analysis
4. **tab_1_2_weeks_swing.html** - Trading view
5. **unified_market_dashboard.html** - Market overview

**Impact:** Foundational pages, high traffic, complex state management

### Tier 2: HIGH (7 pages)
- garp.html, complete_cftc_cot_terminal.html, fred_global_complete.html
- barometers.html, intermarket_relationships.html
- bitcoin_intelligence.html, gold_intelligence.html

**Impact:** Complex filtering, real-time updates, heavy computation

### Tier 3: MEDIUM (8 pages)
- seasonality_research.html, fundamental_analysis.html, econometrics.html
- pattern_discovery_terminal.html, harmonic_cycles.html
- COMPREHENSIVE_TRADING_JOURNAL.html, symbol_research.html
- elite_trading_strategies.html

**Impact:** Display-focused, moderate complexity, computed data

### Tier 4: LOWER (38+ pages)
- Remaining intelligence/reference pages, testing utilities, portals

**Impact:** Simpler pages, less frequent updates

---

## API ENDPOINTS QUICK REFERENCE

### Main Server (Port 8888)
```
/health
/api/db/stats
/api/db/search?query=X
/api/db/symbols?limit=1000&offset=0
/api/market/symbol/{symbol}
/api/market/quote/{symbol}
/api/market/complete
/api/economic/all
/api/economic/indicators?series=X
/api/recession-probability
/api/config
```

### Daily Planet (Port 5000)
```
/api/market-news
/api/economic-calendar
/api/market-movers
/api/sector-rotation
/api/sentiment-analysis
/api/highlights
```

### Swing Dashboard (Port 5002)
```
/api/yahoo/quote?symbols=X,Y,Z
/api/yahoo/chart/{symbol}?interval=1d&range=5d
/api/fred/series/observations?series_id=X
/api/swing-dashboard
```

### GARP (Port 5003)
```
/api/garp/screen
/api/garp/symbols
```

### Correlations (Port 5004)
```
/api/metadata
/api/correlations
/api/correlations/{period}
/api/correlations/{asset1}/{asset2}
```

### Crypto/COT (Port 5005)
```
/api/crypto-composite
/api/cot/market/{ticker}
```

---

## DATA SOURCES MATRIX

### Market Data (yfinance - free)
```
Indices:     SPY, QQQ, DIA, IWM, ^GSPC, ^IXIC, ^DJI, ^RUT, EFA, EEM
Commodities: GC=F, CL=F, HG=F, SI=F, GLD, USO, CPER
Crypto:      BTC-USD, ETH-USD (via CoinGecko)
Forex:       EURUSD=X, GBPUSD=X, USDJPY=X, DX-Y.NYE
Treasuries:  SHY, IEF, TLT, ^TNX
Sectors:     XLK, XLF, XLE, XLV, XLY, XLP, XLI, XLB, XLU, XLRE, XLC
Volatility:  ^VIX, VXX, UVXY
```

### Economic Data (FRED API - free with key)
```
UMCSENT (Consumer Sentiment)      IPMAN (Manufacturing)
MANEMP (Mfg Employment)           SRVPRD (Services)
USSLIND (Leading Indicators)      ICSA (Initial Claims)
HOUST (Housing Starts)            GDP
CPIAUCSL (CPI)                    UNRATE (Unemployment)
FEDFUNDS (Fed Funds Rate)         T10Y2Y (10Y-2Y Spread)
```

### Other Sources
```
CoinGecko:   Crypto data (free, no key)
CFTC.gov:    COT data (manual download)
Polygon.io:  Advanced market data (paid tier)
```

---

## CACHE ARCHITECTURE

```
Browser User
    ↓
IndexedDB (15-min TTL, persistent)
    ↓
Redis Cache (15-min TTL)
    ↓
PostgreSQL Backup (full snapshot)
    ↓
Fresh Fetch (yfinance, FRED, CoinGecko)
```

**Key Insight:** If data unavailable at any level, system returns `null` (NO FAKE DATA)

---

## SHARED COMPONENTS (For React Migration)

### Data Display (5)
- SymbolQuote, ChartComponent, CorrelationMatrix
- TimeSeriesChart, CandlestickChart

### Input Controls (5)
- SymbolSearcher, TimeframeSelector, DateRangePicker
- IndicatorSelector, FilterPanel

### Dashboard (5)
- StatsCard, AlertBanner, LoadingSpinner
- ErrorBoundary, DataRefreshIndicator

### Tables (5)
- SortableTable, PaginatedTable, ExportableTable
- SearchableTable, HighlightableRows

### Charts (5)
- ScatterPlot, Heatmap, HistogramChart
- AreaChart, BarChart

### Layout (6)
- TabContainer, SidePanel, ModalDialog
- CollapsibleSection, ResponsiveGrid, Header/Footer

**Total Reusable Components: 31**

---

## SYMBOLS TRACKED

- **Stocks:** 8,000+ (GARP screener)
- **Total Symbols:** 12,000+ (Nano Banana scanner)
- **FRED Series:** 200+ economic indicators
- **Crypto Assets:** 100+ (via CoinGecko)
- **Commodities:** 10+ major contracts
- **Forex Pairs:** 8+ major pairs
- **Indices:** 20+ global indices
- **Sectors:** 11 S&P 500 sectors

---

## UNIQUE FEATURES BREAKDOWN

| Feature | Pages | Impact |
|---------|-------|--------|
| Technical Analysis | 15 | Core to trading functionality |
| Macro Analysis | 12 | Economic decision support |
| Sentiment Analysis | 8 | Market timing signals |
| Correlation Analysis | 6 | Risk management |
| Pattern Recognition | 5 | Trade setup identification |
| Risk Management | 4 | Portfolio protection |
| Educational Content | 3 | User learning |

---

## CRITICAL DEPENDENCIES

### Database Tables Required
```
preloaded_market_data    (symbol, price, change_percent, volume, timestamp)
trading_signals          (symbol, signal_type, confidence, timestamp)
correlations             (asset1, asset2, coefficient, period, timestamp)
symbols_database         (symbol, name, type, exchange, metadata)
user_trades              (trade_id, entry, exit, size, pnl, timestamp)
economic_indicators      (series_id, value, date, source)
```

### Python Dependencies (Key)
```
Flask, pandas, numpy, yfinance
psycopg2-binary (PostgreSQL)
redis (caching)
requests, aiohttp (HTTP)
```

### JavaScript Dependencies
```
Chart.js (charting)
Vanilla JS (no framework currently)
IndexedDB API (browser cache)
Fetch API (HTTP requests)
```

---

## PERFORMANCE METRICS

| Metric | Target | Current |
|--------|--------|---------|
| Page Load (cached) | <2s | <2s |
| Data Refresh Frequency | 15min | 15min |
| Cache Hit Rate | 80%+ | 75%+ |
| API Response Time | <500ms | ~800ms |
| Symbols Processed | 12,000+ | 12,000+ |
| Concurrent Users | 100+ | TBD |

---

## MIGRATION EFFORT ESTIMATE

| Phase | Duration | Pages | Complexity |
|-------|----------|-------|------------|
| Foundation | 2 weeks | Setup | Medium |
| Core Pages | 4 weeks | 12 | Medium |
| Extended | 4 weeks | 20 | Low |
| Polish | 2 weeks | 26+ | Low |
| **Total** | **12 weeks** | **58** | **Medium** |

---

## CRITICAL RULES FOR MIGRATION

1. **NO FAKE DATA** - Return `null` on API failure, never generate mock values
2. **PostgreSQL Only** - Replace JSON files with database queries
3. **Preserve Cache Architecture** - Keep 3-tier caching (IndexedDB → Redis → PostgreSQL)
4. **Maintain API Compatibility** - Don't break existing endpoints
5. **Component Reusability** - Build 31+ shared components
6. **Zero Data Loss** - Backup before schema changes

---

## FILES TO REFERENCE

### Main Documentation
- `SPARTAN_INVENTORY_REPORT.md` - Complete detailed report (829 lines)
- `start_server.py` - Backend API implementation
- `js/spartan-preloader.js` - Frontend data caching logic
- `index.html` - Main dashboard (2,051 lines, preserve structure)

### Configuration
- `.env` - API keys, database credentials
- `requirements.txt` - Python dependencies
- `symbols_database.json` - Symbol definitions

### Database
- PostgreSQL schema: `preloaded_market_data`, `trading_signals`, `correlations`
- Redis: `market:symbol:*`, `fred:series:*`, `correlation:*`

---

## NEXT STEPS

1. **Read Full Report**: Open `SPARTAN_INVENTORY_REPORT.md`
2. **Plan Tier 1 Migration**: Start with 5 critical pages
3. **Set Up React Project**: Create component library with 31 shared components
4. **Implement Caching**: Use React Query + Redux/Zustand
5. **Build Backend API Client**: Wrap Flask endpoints
6. **Create Test Suite**: Unit + integration + E2E tests
7. **Deploy to Staging**: Test with real data
8. **Production Release**: Gradually roll out pages

---

## SUCCESS METRICS

- All 58 pages migrated to React within 12 weeks
- 31+ reusable components created
- 80%+ test coverage
- Performance maintained (<2s load time cached)
- Zero data loss
- 100% backward compatibility with existing APIs

---

**Report Complete**
Full Details: `/mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/SPARTAN_INVENTORY_REPORT.md`
