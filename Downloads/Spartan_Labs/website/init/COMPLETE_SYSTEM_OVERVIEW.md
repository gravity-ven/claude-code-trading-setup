# Spartan Research Station - Complete System Overview

## System Purpose

The Spartan Research Station is an **autonomous, self-healing financial intelligence platform** that provides real-time market data, economic insights, and trading intelligence with **95% uptime guaranteed through AI-powered monitoring**.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SPARTAN RESEARCH STATION                     │
│                                                                 │
│  ┌─────────────────┐     ┌──────────────┐     ┌─────────────┐  │
│  │  Data Preloader │────▶│ Redis Cache  │────▶│ Web Server  │  │
│  │  (Validation)   │     │ (15-min TTL) │     │ (Flask API) │  │
│  └─────────────────┘     └──────────────┘     └─────────────┘  │
│           │                      ▲                     │        │
│           ▼                      │                     ▼        │
│  ┌─────────────────┐     ┌──────────────┐     ┌─────────────┐  │
│  │   PostgreSQL    │     │   Refresh    │     │  Dashboard  │  │
│  │ (Long-term DB)  │     │  Scheduler   │     │ (HTML/JS)   │  │
│  └─────────────────┘     └──────────────┘     └─────────────┘  │
│           ▲                                            │        │
│           │                                            ▼        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           AUTONOMOUS MONITORING LAYER                   │   │
│  │                                                           │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │   Monitor    │  │    Alert     │  │  Claude Code │  │   │
│  │  │   Agent      │─▶│   Watcher    │─▶│  (Tier 2)    │  │   │
│  │  │  (Tier 1)    │  │              │  │              │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│  │                                                           │   │
│  │  95% Auto-Heal    Pattern Detection    5% Complex Issues │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Data Preloader (`src/data_preloader.py`)

**Purpose**: Validate and preload all market data **before** website starts

**Critical Behavior**:
- **Blocks website start** if validation fails
- Docker dependency: `condition: service_completed_successfully`
- Exit code 0 = success → website allowed to start
- Exit code 1 = failure → website blocked

**Data Sources** (13+ categories):
1. US Indices (SPY, QQQ, DIA, IWM) - **Critical**
2. Global Indices (EFA, EEM, FXI, EWJ, etc.)
3. Commodities (GLD, USO, CPER)
4. Crypto (BTC-USD, ETH-USD)
5. Forex (EUR/USD, GBP/USD, USD/JPY, AUD/USD)
6. Treasuries (SHY, IEF, TLT)
7. Global Bonds (BNDX, EMB)
8. FRED Economic Data (GDP, UNRATE, CPIAUCSL) - **Critical**
9. Volatility (VIX) - **Critical**
10. Sectors (XLF, XLK, XLE, XLV, XLI, etc.)
11. Correlation Matrix

**Validation Rules**:
- Overall success rate ≥80%
- Critical sources must succeed (100%)
- No fake data allowed (strict validation)
- Data freshness <15 minutes

**Technology**:
- Language: Python 3.13
- APIs: yfinance, FRED API, Alpha Vantage (fallback)
- Async: `asyncio` for concurrent fetching
- Cache: Redis (15-min TTL)
- Database: PostgreSQL (backup + long-term storage)

**Performance**:
- Runtime: 45-85 seconds (depends on API response times)
- Concurrent fetching: ~20 symbols in parallel
- Retry logic: 3 attempts per source

**Documentation**: `init/agents/data_preloader.md`

---

### 2. Redis Cache

**Purpose**: Ultra-fast in-memory data storage with automatic expiration

**Configuration**:
- TTL: 15 minutes (900 seconds)
- Eviction: Automatic on expiration
- Persistence: Optional (RDB snapshots)

**Key Format**:
```
{source}:{symbol}
Examples:
  yfinance:SPY
  yfinance:QQQ
  fred:GDP
  fred:UNRATE
```

**Data Format**: JSON strings

**Benefits**:
- Sub-millisecond retrieval (<1ms)
- Automatic expiration (no stale data)
- Shared across all services
- Memory-efficient

**Monitoring**:
```bash
# Check keys
redis-cli KEYS "*"

# Check specific data
redis-cli GET "yfinance:SPY"

# Check memory usage
redis-cli INFO memory
```

---

### 3. PostgreSQL Database

**Purpose**: Long-term storage, incident tracking, configuration

**Databases**:
- `spartan_research_db` - Main research database

**Key Tables**:

#### `market_data` - Historical market data
```sql
CREATE TABLE market_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    source VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    open NUMERIC(12,4),
    high NUMERIC(12,4),
    low NUMERIC(12,4),
    close NUMERIC(12,4),
    volume BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(symbol, source, timestamp)
);
```

#### `monitor_incidents` - Monitoring incidents
```sql
CREATE TABLE monitor_incidents (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    container_name VARCHAR(255) NOT NULL,
    issue_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    healing_attempts INTEGER DEFAULT 0,
    healing_strategies_tried TEXT[],
    escalated_to_claude BOOLEAN DEFAULT FALSE,
    resolution_status VARCHAR(50),
    resolution_details TEXT,
    resolved_at TIMESTAMPTZ,
    resolution_time_seconds INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### `alerts` - Alert history
```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    container_name VARCHAR(255),
    message TEXT,
    count INTEGER DEFAULT 1,
    action_taken VARCHAR(100),
    escalated BOOLEAN DEFAULT FALSE,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Backup Strategy**:
- Daily automated backups via `pg_dump`
- Retention: 30 days
- Restore tested weekly

---

### 4. Web Server (`start_server.py`)

**Purpose**: Serve dashboards and API endpoints

**Technology**:
- Framework: Flask 3.0
- Port: 8888 (main), 9000 (simple)
- WSGI: Gunicorn (production)

**Key Endpoints**:

#### Health Check
```
GET /health
Response: {"status": "healthy", "uptime": 125, ...}
```

#### Market Data
```
GET /api/market/indices
GET /api/market/commodities
GET /api/market/forex
GET /api/market/crypto
```

#### Economic Data
```
GET /api/economic/fred?series=GDP,UNRATE
```

#### Database
```
GET /api/db/stats
GET /api/db/search?query=AAPL&limit=10
```

#### Cache
```
GET /api/cache/stats
POST /api/cache/clear
```

#### Monitor
```
GET /api/monitor/status
GET /api/monitor/incidents
```

**CORS**: Enabled for development, restricted in production

**Rate Limiting**: 100 requests/minute per IP

---

### 5. Refresh Scheduler (`src/refresh_scheduler.py`)

**Purpose**: Hourly data refresh to keep cache current

**Schedule**:
- Interval: 1 hour
- Offset: 5 minutes past the hour (e.g., 10:05, 11:05)

**Process**:
1. Check if refresh needed (cache age > 55 minutes)
2. Fetch updated data from APIs
3. Validate new data (no fake data)
4. Update Redis cache
5. Store in PostgreSQL
6. Log refresh statistics

**Monitoring**:
```bash
# Check last refresh
curl http://localhost:8888/api/cache/stats

# Force refresh
redis-cli FLUSHDB
docker-compose restart spartan-refresh-scheduler
```

**Technology**:
- Language: Python 3.13
- Scheduler: APScheduler
- Concurrency: Async I/O

---

### 6. Website Monitor (`agents/website_monitor/`)

**Purpose**: Autonomous monitoring and auto-healing (Tier 1)

**Implementation**: Mojo (primary) + Python (fallback)

**Performance**:
- **Mojo**: <20ms per check cycle (100x faster)
- **Python**: ~200ms per check cycle
- Check interval: 30 seconds

**Monitoring Checks**:
1. HTTP health endpoints (200 OK)
2. Container status (running/restarting/exited)
3. Resource usage (CPU, memory, disk)
4. Log patterns (errors, warnings)
5. Data freshness (cache TTL, last update)

**Auto-Healing Strategies**:

1. **Restart Container** (70% success)
   - Trigger: Health check failure, HTTP timeout
   - Action: `docker restart <container>`
   - Cooldown: 60 seconds

2. **Clear Cache** (15% success)
   - Trigger: Stale data, cache corruption
   - Action: `redis-cli FLUSHDB`
   - Cooldown: 30 seconds

3. **Reset DB Connection** (10% success)
   - Trigger: Database connection errors
   - Action: Recycle connection pool
   - Cooldown: 15 seconds

4. **Rebuild Image** (5% success)
   - Trigger: Persistent failures
   - Action: `docker-compose build --no-cache`
   - Cooldown: 300 seconds

**Escalation to Tier 2**:
- Consecutive failures: 5+
- Unknown error patterns
- Data corruption detected

**NESTED Learning**:
- **Outer Layer**: General healing patterns (slow updates)
- **Inner Layer**: Container-specific patterns (fast updates)

**Documentation**: `init/agents/website_monitor.md`

---

### 7. Alert Watcher (`agents/alert_watcher/`)

**Purpose**: Pattern detection and escalation (background monitoring)

**Alert Types**:
1. Data source failures (>3 consecutive)
2. Container crash loops (>5 restarts/hour)
3. Memory leaks (sustained >80%)
4. Disk space critical (<10%)
5. API rate limits exceeded
6. Database connection errors
7. Data corruption
8. Unknown errors

**Alert Severity**:
- **INFO**: Log only
- **WARNING**: Log + increment counter
- **CRITICAL**: Log + trigger auto-heal
- **EMERGENCY**: Log + escalate to Claude Code

**Pattern Matching**:
- Regex patterns on container logs
- Threshold-based alerts
- Duration-based alerts (sustained high usage)

**Escalation Flow**:
```
Alert Detected
    ↓
Counter Incremented
    ↓
Threshold Reached?
    ↓ Yes
Execute Action (auto-heal or escalate)
    ↓
Log to Database
    ↓
Notify (optional: email/Slack)
```

**Documentation**: `init/agents/alert_watcher.md`

---

### 8. Claude Code Integration (Tier 2)

**Purpose**: AI-powered root cause analysis and fixes for complex issues

**Trigger Conditions**:
- 5+ consecutive auto-heal failures
- Unknown error patterns
- Data corruption detected
- Container crash loops (>5/hour)

**Process**:
1. Monitor/Alert Watcher detects persistent issue
2. Log incident to PostgreSQL
3. Gather context:
   - Container logs (last 500 lines)
   - Resource usage stats
   - Recent git commits
   - System state
4. Invoke Claude Code with context
5. Claude Code analyzes:
   - Reviews logs for error patterns
   - Checks configuration files
   - Examines code for bugs
   - Identifies root cause
6. Claude Code fixes:
   - Code changes
   - Configuration updates
   - Database migrations
   - Dependency updates
7. Monitor verifies fix
8. Log resolution to database

**NESTED Learning Integration**:
- **Outer Layer**: General problem-solving strategies
- **Inner Layer**: Issue-specific tactics
- Continual learning without catastrophic forgetting

**Security**:
- Rate limiting: Max 10 invocations/hour
- Approval required for destructive ops
- All actions logged to database
- Read-only access by default

---

## Data Flow

### Startup Sequence

```
1. docker-compose up
    ↓
2. Start Redis (dependency)
    ↓
3. Start PostgreSQL (dependency)
    ↓
4. Start Data Preloader
    ↓
5. Fetch & validate all data sources
    ↓
6. Write to Redis + PostgreSQL
    ↓
7. Preloader exits with code 0 (success)
    ↓
8. Start Web Server (dependency met)
    ↓
9. Start Refresh Scheduler
    ↓
10. Start Monitor Agent
    ↓
11. Start Alert Watcher
    ↓
12. System Ready ✓
```

### User Request Flow

```
1. User opens http://localhost:8888
    ↓
2. Browser loads index.html
    ↓
3. JavaScript fetches data from API
    GET /api/market/indices
    ↓
4. Flask server checks Redis cache
    ↓
5. Cache hit? Return data (< 1ms)
   Cache miss? Fetch from API + cache (1-3s)
    ↓
6. Return JSON to browser
    ↓
7. JavaScript renders dashboard
    ↓
8. Auto-refresh every 15 minutes
```

### Monitoring Flow (Continuous)

```
Every 30 seconds:

1. Monitor checks all containers
    ↓
2. Health endpoints OK?
   Yes → Continue monitoring
   No  → Execute healing strategy
    ↓
3. Healing strategy successful?
   Yes → Log resolution + continue
   No  → Retry (max 3 attempts)
    ↓
4. After 3 failures:
    ↓
5. Escalate to Claude Code
    ↓
6. Claude Code analyzes + fixes
    ↓
7. Monitor verifies fix
    ↓
8. Log resolution + continue monitoring
```

---

## Technology Stack

### Backend
- **Language**: Python 3.13
- **Framework**: Flask 3.0
- **Async**: asyncio
- **Database ORM**: SQLAlchemy
- **Cache**: Redis
- **Database**: PostgreSQL 13+

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Custom styling (Spartan color scheme)
- **JavaScript**: Vanilla JS (no frameworks)
- **Charts**: D3.js, Chart.js

### Data APIs
- **yfinance**: US/Global indices, commodities, forex
- **FRED API**: Economic data (GDP, UNRATE, CPI, etc.)
- **Alpha Vantage**: Fallback for crypto/forex
- **Polygon.io**: Alternative stock data (optional)

### Monitoring
- **Mojo**: Ultra-fast monitoring (primary)
- **Python**: Monitoring fallback
- **Docker**: Containerization
- **Docker Compose**: Orchestration

### Infrastructure
- **Redis**: In-memory cache
- **PostgreSQL**: Relational database
- **Docker**: Container runtime
- **Systemd**: Service management (production)

---

## Performance Characteristics

### Startup Time
- Data Preloader: 45-85 seconds
- Web Server: <5 seconds
- Total: ~60-90 seconds

### Resource Usage
- CPU: ~10% (1 core) for all services
- Memory: ~500MB total
- Disk: ~2GB (includes Docker images)

### Data Freshness
- Cache TTL: 15 minutes
- Refresh cycle: 1 hour
- Manual refresh: Instant (clear cache)

### Monitoring
- Check cycle: 30 seconds
- Auto-heal success: ~95%
- Escalation rate: ~5%
- Claude Code resolution: 2-10 minutes

### API Performance
- Cache hit: <1ms
- Cache miss: 1-3 seconds (API fetch)
- Rate limits:
  - yfinance: 2000 req/hour
  - FRED: 120 req/minute
  - Alpha Vantage: 5 req/minute (free tier)

---

## Deployment Modes

### Development (Local)

```bash
# Start services
docker-compose up -d

# Or run directly
python3 start_server.py
```

**Characteristics**:
- Hot reload enabled
- Verbose logging
- CORS unrestricted
- No HTTPS

### Production (Docker)

```bash
# Build images
docker-compose -f docker-compose.yml build

# Start with restart policy
docker-compose up -d --restart=always
```

**Characteristics**:
- Gunicorn WSGI server
- Rate limiting enabled
- HTTPS required
- Systemd integration
- Automated backups
- Log rotation

### Production (Systemd)

```ini
# /etc/systemd/system/spartan-research.service
[Unit]
Description=Spartan Research Station
After=docker.service postgresql.service redis.service

[Service]
Type=simple
User=spartan
WorkingDirectory=/opt/spartan/website
ExecStart=/usr/bin/docker-compose up
Restart=always

[Install]
WantedBy=multi-user.target
```

**Commands**:
```bash
sudo systemctl enable spartan-research
sudo systemctl start spartan-research
sudo systemctl status spartan-research
```

---

## Security

### Data Validation
- No fake data allowed (strict checks)
- Input sanitization on all API endpoints
- SQL injection prevention (parameterized queries)
- XSS prevention (content escaping)

### Authentication (Optional)
- API key authentication
- JWT tokens
- Rate limiting per user

### Infrastructure
- Docker socket access controlled
- PostgreSQL password authentication
- Redis AUTH enabled (production)
- HTTPS required (production)

### Monitoring
- All actions logged to database
- Incident tracking with audit trail
- Claude Code actions require approval for destructive ops
- Read-only access by default

---

## Maintenance

### Daily Tasks
- Check monitor incidents: `psql -c "SELECT * FROM monitor_incidents WHERE timestamp > NOW() - INTERVAL '24 hours';"`
- Verify data freshness: `curl http://localhost:8888/api/cache/stats`
- Review alert counts: `curl http://localhost:8888/api/alerts/stats`

### Weekly Tasks
- Review auto-heal effectiveness
- Analyze escalation patterns
- Check disk space
- Rotate logs

### Monthly Tasks
- Database vacuum: `VACUUM ANALYZE;`
- Backup verification
- Dependency updates: `pip install -U -r requirements.txt`
- Security audit

---

## Troubleshooting Guide

See `init/QUICK_START.md` for common issues and fixes.

---

## Documentation Index

### Quick Start
- `init/QUICK_START.md` - 5-minute setup guide

### Components
- `init/agents/data_preloader.md` - Data preloading system
- `init/agents/website_monitor.md` - Monitoring and auto-healing
- `init/agents/alert_watcher.md` - Alert detection and escalation

### Deployment
- `DEPLOYMENT_GUIDE.md` - Full deployment process
- `ARCHITECTURE.md` - Detailed architecture
- `API_INTEGRATION_GUIDE.md` - API integration

### Development
- `CLAUDE.md` - Claude Code instructions
- `README.md` - Project overview
- `GETTING_STARTED.md` - Developer setup

---

## System Philosophy

**Principles**:
1. **No Fake Data**: Real APIs only, strict validation
2. **Autonomous Operation**: 95% self-healing, 5% AI-powered fixes
3. **Data Integrity**: PostgreSQL for reliability, Redis for speed
4. **Continuous Learning**: NESTED learning for improvement
5. **Observability**: Comprehensive logging and incident tracking

**Goals**:
- **Uptime**: 95%+ through autonomous monitoring
- **Data Quality**: 100% real data, no mock/fake values
- **Performance**: <1ms cache hits, <3s API fetches
- **Maintainability**: Self-documenting, self-healing
- **Scalability**: Horizontal scaling via Docker containers

---

**This system is designed to run autonomously with minimal human intervention, continuously learning and improving through NESTED learning and Claude Code integration.**
