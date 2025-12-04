# Spartan Research Station - Complete System Architecture

## 🎯 Mission
Enterprise-grade financial market intelligence platform with 50+ data sources, database-first architecture, and zero-latency user experience.

## 🏛️ Core Principles

### 1. Database-First Architecture
```
External API → Download → PostgreSQL Database → Website Render
                    ↓
              Never fetch again (until 1-hour refresh)
```

**Rule**: Once data is downloaded, it NEVER leaves the database. Website reads from database ONLY.

### 2. Branding
- **Name**: Spartan Research Station
- **Logo**: spartan_logo.png
- **Colors**:
  - Primary: Dark Navy Blue (#0f2742)
  - Accent: Spartan Red (#c83737)
  - Success: #00ff88
  - Danger: #ff5252

### 3. Data Refresh Strategy
- **Frequency**: Every 1 hour (3600 seconds)
- **Method**: Background service updates database silently
- **User Impact**: Zero - users always see cached data

### 4. Enterprise Requirements
- Comprehensive testing (unit, integration, load, security)
- 99.9% uptime target
- Proper error handling and logging
- Monitoring and health checks
- Disaster recovery

## 📊 System Components

### Component 1: PostgreSQL Database (Primary Data Store)

**Schema**: `spartan_research`

**Tables** (17 total):

```sql
-- Market Data Tables
market_indices          -- S&P 500, NASDAQ, Dow, etc. (50+ indices)
commodities            -- Gold, Oil, Copper, etc. (20+ commodities)
forex_rates            -- USD/EUR, USD/JPY, etc. (40+ pairs)
crypto_prices          -- BTC, ETH, SOL, etc. (30+ cryptos)
treasury_yields        -- 2Y, 10Y, 30Y treasuries
credit_spreads         -- HY OAS, IG BBB spreads
volatility_indicators  -- VIX, VVIX, SKEW, MOVE

-- Economic Data Tables
economic_indicators    -- GDP, CPI, Unemployment, etc. (100+ series)
fred_series           -- Complete FRED data cache (1000+ series)

-- Market Analytics
correlations          -- Asset correlation matrix (60-day rolling)
sector_rotation       -- Sector ETF performance tracking
sentiment_indicators  -- Put/call ratio, Fear & Greed, AAII
market_breadth        -- Advance/decline, new highs/lows

-- System Tables
data_sources          -- Configuration of 50+ sources
download_log          -- Track all downloads (audit trail)
health_status         -- Real-time health of each source
api_rate_limits       -- Track API usage and limits
```

**Total Storage**: ~100GB (5 years historical data)

### Component 2: Redis Cache (Speed Layer)

**Purpose**: Ultra-fast access to most recent data

**Structure**:
```
quotes:{symbol}         # Latest quote (60s TTL)
chart:{symbol}:{tf}     # Chart data (5min TTL)
health:{source_id}      # Source health status
preload:status          # Pre-load completion status
refresh:last_run        # Last refresh timestamp
```

**Total Memory**: 4GB allocated

### Component 3: Pre-Loader Service

**Purpose**: Download ALL data BEFORE website starts

**Process**:
```
1. Start PostgreSQL + Redis
2. Load 50+ data source configuration
3. Parallel download (10 workers)
4. Validate each source
5. Insert into PostgreSQL
6. Cache in Redis
7. Mark preload complete
8. START web server
```

**Duration**: 3-5 minutes (one-time on startup)

**Success Criteria**: ≥ 90% of sources operational

### Component 4: Background Refresh Service

**Purpose**: Keep data fresh without user disruption

**Schedule**: Every 1 hour (cron: `0 * * * *`)

**Process**:
```
1. Fetch updated data from all 50+ sources
2. Validate new data
3. UPDATE PostgreSQL (transactional)
4. UPDATE Redis cache
5. Log refresh completion
6. Monitor for errors
```

**User Impact**: Zero (reads from stable cache during update)

### Component 5: Web Server (Flask)

**Purpose**: Serve pre-loaded data instantly

**Architecture**:
- **NO external API calls** in request handlers
- **ALL data** from PostgreSQL/Redis
- **Sub-second** response times
- **Health endpoints** for monitoring

**API Structure**:
```
/api/market/indices          → PostgreSQL: market_indices
/api/market/commodities      → PostgreSQL: commodities
/api/market/forex            → PostgreSQL: forex_rates
/api/economic/indicators     → PostgreSQL: economic_indicators
/api/analytics/correlations  → PostgreSQL: correlations
/health                      → System health check
/api/system/status           → Data freshness status
```

### Component 6: Data Source Manager

**Purpose**: Manage 50+ external data sources

**Categories**:
1. **Stocks** (18 sources): Yahoo, Polygon, Alpha Vantage, Finnhub, etc.
2. **Forex** (12 sources): OANDA, ECB, Fixer, etc.
3. **Crypto** (13 sources): Binance, CoinGecko, Kraken, etc.
4. **Economic** (8 sources): FRED, World Bank, IMF, etc.
5. **Commodities** (5 sources): CME, Yahoo, etc.
6. **Options** (7 sources): CBOE, EODHD, etc.

**Features**:
- Fallback cascade (primary → secondary → tertiary)
- Rate limit management
- API key rotation
- Error recovery
- Health tracking

## 🚀 Startup Sequence

### Phase 1: Infrastructure (0-10s)
```bash
docker-compose up -d postgres redis
# Wait for health checks
```

### Phase 2: Pre-Loader (10s - 5min)
```bash
docker-compose up -d preloader
# Downloads all data from 50+ sources
# Populates PostgreSQL + Redis
# Logs progress to Redis
```

### Phase 3: Web Server (5min - 5min 10s)
```bash
# Waits for preloader completion
docker-compose up -d web
# Starts ONLY after database is populated
```

### Phase 4: Browser Launch (5min 10s)
```bash
# Auto-open browser to fully loaded website
open http://localhost:8888
# User sees INSTANT data (no loading spinners)
```

### Phase 5: Background Refresh (Continuous)
```bash
# Starts after web server is running
docker-compose up -d refresh_service
# Runs every 1 hour
```

## 🏗️ File Structure

```
spartan_research_station/
├── docker-compose.yml              # Complete orchestration
├── Dockerfile.preloader            # Pre-loader service
├── Dockerfile.web                  # Web server
├── Dockerfile.refresh              # Background refresh
│
├── config/
│   ├── data_sources.yaml           # 50+ source definitions
│   ├── spartan_theme.css           # Logo-based color scheme
│   └── database.yaml               # PostgreSQL configuration
│
├── db/
│   ├── init/
│   │   ├── 01_create_schemas.sql   # Database schemas
│   │   ├── 02_create_tables.sql    # 17 tables
│   │   ├── 03_create_indexes.sql   # Performance indexes
│   │   └── 04_create_functions.sql # Helper functions
│   └── migrations/                 # Schema updates
│
├── src/
│   ├── preloader/
│   │   ├── main.py                 # Pre-loader entry point
│   │   ├── worker_pool.py          # Parallel workers
│   │   ├── data_fetcher.py         # Fetch from sources
│   │   ├── validator.py            # Data validation
│   │   ├── db_writer.py            # Write to PostgreSQL
│   │   └── health_monitor.py       # Track source health
│   │
│   ├── refresh/
│   │   ├── main.py                 # Background refresh
│   │   ├── scheduler.py            # 1-hour cron
│   │   └── update_db.py            # Atomic updates
│   │
│   ├── web/
│   │   ├── app.py                  # Flask application
│   │   ├── routes/
│   │   │   ├── market.py           # Market data endpoints
│   │   │   ├── economic.py         # Economic endpoints
│   │   │   ├── analytics.py        # Analytics endpoints
│   │   │   └── system.py           # Health/status
│   │   └── db/
│   │       ├── postgres.py         # PostgreSQL client
│   │       └── redis.py            # Redis client
│   │
│   ├── data_sources/
│   │   ├── base.py                 # Abstract base class
│   │   ├── stocks/                 # 18 stock sources
│   │   ├── forex/                  # 12 forex sources
│   │   ├── crypto/                 # 13 crypto sources
│   │   ├── economic/               # 8 economic sources
│   │   ├── commodities/            # 5 commodity sources
│   │   └── options/                # 7 options sources
│   │
│   └── utils/
│       ├── logger.py               # Structured logging
│       ├── config_loader.py        # YAML config reader
│       └── toon_formatter.py       # TOON format support
│
├── static/
│   ├── css/
│   │   └── spartan_theme.css       # Complete theme
│   ├── js/
│   │   └── [existing 13 modules]
│   └── images/
│       └── spartan_logo.png
│
├── templates/
│   └── [48 HTML dashboards updated]
│
├── tests/
│   ├── unit/                       # Unit tests
│   ├── integration/                # Integration tests
│   ├── load/                       # Load tests (Locust)
│   ├── security/                   # Security tests (Bandit)
│   └── e2e/                        # End-to-end tests (Selenium)
│
├── monitoring/
│   ├── grafana/                    # Grafana dashboards
│   ├── prometheus/                 # Prometheus config
│   └── alerts/                     # Alert rules
│
├── scripts/
│   ├── START_SPARTAN.sh            # One-command startup
│   ├── STOP_SPARTAN.sh             # Graceful shutdown
│   ├── run_tests.sh                # Enterprise test suite
│   └── backup_database.sh          # Database backup
│
└── docs/
    ├── DEPLOYMENT.md               # Deployment guide
    ├── API_REFERENCE.md            # Complete API docs
    ├── TESTING.md                  # Testing guide
    └── MONITORING.md               # Monitoring guide
```

## 🧪 Enterprise Testing Strategy

### 1. Unit Tests (pytest)
- Test each data source connector
- Test database operations
- Test data validation
- **Coverage Target**: 85%+

### 2. Integration Tests
- Test pre-loader with real APIs
- Test database → web server flow
- Test background refresh
- **Success Rate**: 95%+

### 3. Load Tests (Locust)
- Simulate 1000+ concurrent users
- Measure response times
- Check database connection pooling
- **Target**: <200ms p95 response time

### 4. Security Tests (Bandit, Safety)
- SQL injection prevention
- XSS prevention
- API key security
- **Zero Critical Issues**

### 5. End-to-End Tests (Selenium)
- Test full user workflows
- Verify all 48 dashboards load
- Check data rendering
- **100% Dashboard Coverage**

## 📈 Performance Targets

| Metric | Target | How Measured |
|--------|--------|--------------|
| Page Load Time | <1s | Chrome DevTools |
| API Response Time (p95) | <200ms | Prometheus |
| Database Query Time (p95) | <50ms | PostgreSQL logs |
| Cache Hit Rate | >95% | Redis INFO |
| System Uptime | 99.9% | Uptime monitoring |
| Data Freshness | ≤1 hour | Health endpoint |
| Pre-Load Duration | <5 min | Docker logs |
| Background Refresh | <2 min | Refresh service logs |

## 🔐 Security Measures

1. **API Keys**: Stored in environment variables only
2. **Database**: Password-protected, no root access
3. **Network**: Isolated Docker network
4. **Input Validation**: All user inputs sanitized
5. **Rate Limiting**: Per-IP rate limits on API
6. **HTTPS**: SSL/TLS in production
7. **Audit Logs**: All data access logged

## 🚨 Monitoring & Alerts

### Health Checks
- PostgreSQL: `pg_isready`
- Redis: `redis-cli ping`
- Web Server: `/health` endpoint
- Each Data Source: Test connection

### Alerts (via Email/SMS)
- Database connection failure
- >10% data sources failing
- API response time >1s
- Disk space <10%
- Memory usage >90%

### Metrics (Prometheus + Grafana)
- Request rate
- Response times
- Error rates
- Database connections
- Cache hit rates
- Data source health

## 🎨 Spartan Theme (Logo-Based)

### Color Palette
```css
--spartan-navy:      #0f2742;  /* Background (from logo) */
--spartan-red:       #c83737;  /* Accents (from logo) */
--spartan-red-light: #e04e4e;  /* Hover states */
--spartan-red-dark:  #a02828;  /* Pressed states */
--success-green:     #00ff88;  /* Positive values */
--danger-red:        #ff5252;  /* Negative values */
--text-primary:      #ffffff;  /* White text */
--text-secondary:    #b0b8c8;  /* Gray text */
```

### Typography
- **Headings**: Inter Bold
- **Body**: Inter Regular
- **Monospace**: Source Code Pro

### Logo Placement
- Top-left corner (40px height)
- Login page (centered, 120px height)
- Footer (30px height)

## 🔄 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     SPARTAN RESEARCH STATION                     │
│                      Data Flow Architecture                      │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐
│ 50+ External │
│  Data APIs   │ ← Polygon.io, FRED, Yahoo, Alpha Vantage, etc.
└──────┬───────┘
       │
       │ (Pre-Loader fetches once on startup)
       ↓
┌──────────────────┐
│  Pre-Loader      │ ← 10 parallel workers
│  Service         │ ← Validate all data
└──────┬───────────┘
       │
       ├─────────────┐
       │             │
       ↓             ↓
┌─────────────┐ ┌─────────┐
│ PostgreSQL  │ │  Redis  │
│  Database   │ │  Cache  │
│ (Persistent)│ │ (Fast)  │
└──────┬──────┘ └────┬────┘
       │             │
       └──────┬──────┘
              │
              │ (Web server reads ONLY from cache)
              ↓
       ┌──────────────┐
       │  Web Server  │ ← NO external API calls
       │   (Flask)    │ ← Database queries only
       └──────┬───────┘
              │
              │ (Instant response)
              ↓
       ┌──────────────┐
       │   Browser    │ ← User sees instant data
       │  (HTML/JS)   │ ← No loading spinners
       └──────────────┘

┌─────────────────────────────────────────────────────────────────┐
│           Background Refresh (Every 1 Hour)                      │
└─────────────────────────────────────────────────────────────────┘

       ┌──────────────┐
       │   Cron Job   │ ← Runs every hour
       └──────┬───────┘
              │
              ↓
       ┌──────────────────┐
       │ Refresh Service  │ ← Fetch updated data
       └──────┬───────────┘
              │
              ├─────────────┐
              │             │
              ↓             ↓
       ┌─────────────┐ ┌─────────┐
       │ PostgreSQL  │ │  Redis  │
       │  (UPDATE)   │ │ (UPDATE)│
       └─────────────┘ └─────────┘

       Users continue browsing → Zero impact
```

## 📅 Implementation Timeline

### Week 1: Foundation
- Day 1-2: Database schema + Docker setup
- Day 3-4: Pre-loader service
- Day 5-7: Data source connectors (20/50)

### Week 2: Core System
- Day 8-10: Remaining data sources (50/50)
- Day 11-12: Background refresh service
- Day 13-14: Web server API endpoints

### Week 3: Frontend & Testing
- Day 15-17: Update 48 HTML dashboards
- Day 18-19: Unit + integration tests
- Day 20-21: Load + security tests

### Week 4: Polish & Deploy
- Day 22-23: Monitoring + alerts
- Day 24-25: Documentation
- Day 26-27: End-to-end testing
- Day 28: Production deployment

## ✅ Definition of Done

- [ ] All 50+ data sources integrated and operational
- [ ] Pre-loader completes in <5 minutes
- [ ] All data cached in PostgreSQL (never re-fetch)
- [ ] 1-hour background refresh working
- [ ] All 48 HTML pages updated with Spartan branding
- [ ] Page load time <1 second
- [ ] Test coverage >85%
- [ ] Load test: 1000 concurrent users passing
- [ ] Security scan: Zero critical issues
- [ ] Documentation complete
- [ ] Monitoring dashboards live
- [ ] Production deployment successful

---

**Status**: 🏗️ **UNDER CONSTRUCTION**
**Target Completion**: 4 weeks from start
**Quality Standard**: Enterprise-grade, production-ready
