# Spartan Research Station - Architecture Guide

## System Overview

**Spartan Research Station** - An autonomous, self-healing financial intelligence platform for swing traders and investors with real-time multi-asset market data.

**Tech Stack**: Python 3.13, PostgreSQL 13+, Redis, Docker, Flask, Vanilla JavaScript, yfinance, asyncio

**Critical Architecture**: Data preloader gate → Three-tier cache → Microservices → Autonomous validator

---

## 1. Data Preloader Gate (BLOCKING STARTUP)

### Critical Pattern

Website **CANNOT START** without successful data preload (exit code 0).

**Location**: `src/data_preloader.py`

**Docker Dependency Chain:**
```yaml
spartan-web:
  depends_on:
    spartan-data-preloader:
      condition: service_completed_successfully  # Blocks until exit 0
```

### Validation Rules

- 80%+ success rate across all data sources
- Critical sources MUST succeed: US Indices (SPY, QQQ, DIA, IWM), FRED Economic Data, VIX
- Exit code 0 = success (website starts), Exit code 1 = fail (website blocked)

### Data Sources (13+)

- **US Indices**: SPY, QQQ, DIA, IWM (via yfinance)
- **Global Indices**: EFA, EEM, FXI, EWJ, EWG, EWU
- **Commodities**: GLD, USO, CPER
- **Crypto**: BTC-USD
- **Forex**: EUR/USD, GBP/USD, USD/JPY, AUD/USD
- **Treasuries**: SHY, IEF, TLT
- **Global Bonds**: BNDX, EMB
- **FRED Economic**: GDP, UNRATE, CPIAUCSL, FEDFUNDS, T10Y2Y
- **Volatility**: VIX
- **Sectors**: XLF, XLK, XLE, XLV, XLI, XLP, XLY, XLU, XLRE

### Rate Limiting (Required)

- yfinance: 2s between requests
- polygon: 12s (free tier limit)
- alpha_vantage: 12s
- twelve_data: 8s
- coingecko: 1.5s

### Storage

- **Primary**: Redis (15-minute TTL) - Keys: `market:index:SPY`
- **Backup**: PostgreSQL `preloaded_market_data` table
- **Auto-refresh**: Every 15 minutes via `src/data_refresh_scheduler.py`

---

## 2. Three-Tier Cache Architecture

### Data Flow

**Client → IndexedDB → Redis → PostgreSQL → Null (NO FAKE DATA)**

### Tier 1: IndexedDB (Browser)

- 15-minute TTL
- Instant access, offline capability
- Managed by `js/spartan-preloader.js`

### Tier 2: Redis (Server)

- 15-minute TTL
- Shared across users
- Key pattern: `market:*`, `data:*`

### Tier 3: PostgreSQL (Server)

- Persistent backup
- Historical data
- Tables: `preloaded_market_data`, `market_data`

### Critical Rule

Return `null` on cache miss. NEVER generate fake fallback data.

---

## 3. Microservices Architecture

### Main Web Server (Port 8888)

- `start_server.py` - HTTP server with database API endpoints
- Serves static files (index.html, JS, CSS)
- Proxies to microservice APIs

### API Microservices

- `correlation_api.py` - Port 5004 - Correlation matrix
- `daily_planet_api.py` - Port 5000 - News/insights
- `swing_dashboard_api.py` - Port 5002 - Swing trading timeframes
- `garp_api.py` - Port 5003 - GARP stock screener

### Container Orchestration

**9 Docker services in `docker-compose.yml`:**

- spartan-web (main)
- spartan-postgres (database)
- spartan-redis (cache)
- spartan-data-preloader (one-shot)
- spartan-data-refresh (15-min loop)
- spartan-data-validator (monitor)
- spartan-correlation-api
- spartan-daily-planet-api
- spartan-swing-api
- spartan-garp-api

---

## 4. Autonomous Data Validation System

### Active Agent

`agents/website_data_validator_agent.py`

**Purpose**: Continuously monitors data health and auto-resolves issues

### Agent Hierarchy (95% autonomous)

**1. Data Validator Agent (Active)** - Monitors Redis/PostgreSQL freshness
   - Checks every 60 seconds
   - Logs missing data to `logs/data_validation_*.json`
   - Creates Redis key aliases for symbol mismatches
   - Triggers data refresh on staleness

**2. Data Refresh Scheduler (Active)** - Keeps cache fresh
   - Runs every 15 minutes (900 seconds)
   - Re-executes `src/data_preloader.py`
   - Auto-retries failed sources with exponential backoff

**3. Website Monitor Agent (Disabled)** - Advanced self-healing
   - Location: `agents/website_monitor/website_monitor.mojo`
   - Actions: container restart, cache clear, DB reset, rebuild
   - Incident tracking: PostgreSQL `monitor_incidents`, `monitor_healing_actions` tables
   - Status: Temporarily disabled (Mojo Docker image access issue)

### Claude Code Bridge

When agents detect issues beyond their capability:
- Agent writes trigger file: `logs/trigger_claude_data_fix.json`
- Contains: error details, attempted fixes, required action
- Claude Code watcher: `logs/claude_code_watcher.sh` (if enabled)
- Human escalation: Only for API key issues or systemic failures

---

## Data Endpoint Patterns

### Redis Key Conventions

**Market Data:**
```
market:symbol:SPY           → Current price, change%, timestamp
market:index:^VIX           → Index data
fundamental:economic:DGS10  → FRED economic indicators
fundamental:forex:EURUSD    → Forex pairs
fundamental:fundamentals:AAPL → Company fundamentals
```

**Key Structure:**
- Namespace: `market:`, `fundamental:`, `data:`
- Type: `symbol`, `index`, `economic`, `forex`, `fundamentals`
- Identifier: Symbol or indicator code (uppercase)

**TTL**: 900 seconds (15 minutes) - enforced by data_refresh_scheduler

### PostgreSQL Schema

**Primary Table**: `preloaded_market_data`

```sql
CREATE TABLE preloaded_market_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    data_type VARCHAR(20),  -- 'market', 'economic', 'forex', 'fundamentals'
    price DECIMAL(20,4),
    change_percent DECIMAL(10,4),
    volume BIGINT,
    metadata JSONB,
    timestamp TIMESTAMP NOT NULL,
    source VARCHAR(50)
);
CREATE INDEX idx_symbol_timestamp ON preloaded_market_data(symbol, timestamp DESC);
```

**Query Pattern (for agents):**

```sql
-- Check data freshness
SELECT symbol, timestamp,
       EXTRACT(EPOCH FROM (NOW() - timestamp)) AS age_seconds
FROM preloaded_market_data
WHERE timestamp > NOW() - INTERVAL '20 minutes'
GROUP BY symbol, timestamp
ORDER BY timestamp DESC;

-- Find stale data (older than 20 minutes)
SELECT symbol, MAX(timestamp) AS last_update,
       EXTRACT(EPOCH FROM (NOW() - MAX(timestamp))) AS stale_seconds
FROM preloaded_market_data
GROUP BY symbol
HAVING MAX(timestamp) < NOW() - INTERVAL '20 minutes';
```

### API Endpoint Architecture

**Main Server (`start_server.py:8888`):**

```
/api/market/symbol/{symbol}     → Get market data (Redis → PostgreSQL → Fresh fetch)
/api/market/quote/{symbol}      → Get quote with 5-day change calculation
/api/fundamental/economic/{id}  → FRED economic indicators
/api/fundamental/forex/{pair}   → Forex rates
/api/recession-probability      → Calculated metric (10Y-3M spread)
/api/market/narrative           → Market regime classification
/health                         → Health check endpoint
```

### Data Fetch Priority (implemented in all endpoints)

1. Check Redis (fastest)
2. Check PostgreSQL (reliable backup)
3. Fetch fresh from yfinance/API (last resort)
4. Return `null` if all fail (NO FAKE DATA)

**Example Implementation Pattern:**

```python
def handle_market_symbol(self, symbol):
    # PRIORITY 1: Redis
    if redis_client:
        cached = redis_client.get(f'market:symbol:{symbol}')
        if cached:
            return json.loads(cached)

    # PRIORITY 2: PostgreSQL
    row = db.query("""
        SELECT * FROM preloaded_market_data
        WHERE symbol = %s
        ORDER BY timestamp DESC LIMIT 1
    """, (symbol,))
    if row:
        return dict(row)

    # PRIORITY 3: Fresh fetch
    try:
        data = fetch_from_yfinance(symbol)
        if data:
            # Cache for next time
            redis_client.setex(f'market:symbol:{symbol}', 900, json.dumps(data))
            return data
    except Exception as e:
        logger.error(f"Failed to fetch {symbol}: {e}")

    # NO FAKE DATA - return null
    return None
```

---

## Key Files Reference

### Core Architecture

- `docker-compose.yml` - Orchestrates 9 services with dependency chain
- `start_server.py` - Main HTTP server (port 8888) with DB API endpoints
- `index.html` - Main dashboard with flashcard navigation (2,051 lines)

### Data Flow (Critical Path)

- `src/data_preloader.py` - Initial data fetch (blocks web startup on failure)
- `src/data_refresh_scheduler.py` - Background 15-min refresh loop
- `js/spartan-preloader.js` - Frontend preloader with IndexedDB cache

### Frontend (Vanilla JavaScript - No Framework)

- `js/capital_flow_visualizer.js` - Capital flow visualization
- `js/composite_score_engine.js` - Multi-factor scoring
- `js/fred_api_client.js` - FRED economic data client
- `js/section_visibility_manager.js` - Flashcard navigation controller
- `js/timeframe_data_fetcher_1_2_weeks.js` - Short-term timeframe data
- `js/timeframe_data_fetcher_1_3_months.js` - Medium-term timeframe data
- `js/timeframe_data_fetcher_6_18_months.js` - Long-term timeframe data
- `js/timeframe_data_fetcher_18_36_months.js` - Very long-term timeframe data

### Database

- `db/init.sql` - PostgreSQL schema initialization
- `symbols_database.json` - Global symbols database (10,000+ symbols)

---

## Architecture Quick Mental Model

```
User Browser (IndexedDB cache, 15min)
    ↓
Main Server:8888 (start_server.py)
    ↓
[Redis Cache (15min TTL)] → [PostgreSQL Backup]
    ↑
Data Preloader (runs every 15min)
    ↓
yfinance + FRED + Polygon.io + CoinGecko (real APIs)

Parallel:
- Data Validator Agent (monitors health, auto-fixes)
- Data Refresh Scheduler (keeps cache fresh)
- API Microservices (correlation, swing, garp, daily planet)
```

**Key Principle**: Every endpoint checks Redis → PostgreSQL → Fresh fetch → null (NO FAKE DATA)
