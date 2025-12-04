# Spartan Research Station - Quick Start Guide

## 5-Minute Setup

### Prerequisites

- Docker & Docker Compose installed
- PostgreSQL 13+ running
- Redis running
- FRED API key ([Get one free](https://fred.stlouisfed.org/docs/api/api_key.html))

### Installation

```bash
# 1. Clone repository
cd /path/to/spartan/website

# 2. Configure environment
cp .env.example .env
nano .env  # Add FRED_API_KEY

# 3. Start system
docker-compose up -d

# 4. Verify health
curl http://localhost:8888/health
```

**Expected Output**:
```json
{
  "status": "healthy",
  "preloader": "success",
  "cache": "connected",
  "database": "connected",
  "uptime_seconds": 125
}
```

### First Steps

1. **Open Dashboard**: http://localhost:8888
2. **Check Data**: View global capital flows, indices, commodities
3. **Monitor System**: http://localhost:8888/api/monitor/status
4. **View Logs**: `docker-compose logs -f`

## Architecture Overview (30 seconds)

```
Data Preloader (validates data) → Redis Cache (15-min TTL) → Web Dashboard
                ↓                                              ↑
           PostgreSQL                          Refresh Scheduler (hourly)
                                                               ↑
                                                    Website Monitor (auto-heal)
```

**Critical Components**:

1. **Data Preloader** (`src/data_preloader.py`)
   - Blocks website start without valid data
   - Validates 13+ data sources
   - Exit code 0 = success → website starts

2. **Redis Cache** (15-minute TTL)
   - Ultra-fast data retrieval
   - Automatic expiration
   - Shared across all services

3. **PostgreSQL** (backup + long-term storage)
   - Incident tracking
   - Historical data
   - Configuration storage

4. **Website Monitor** (`agents/website_monitor/`)
   - Checks health every 30 seconds
   - Auto-heals 95% of issues
   - Escalates to Claude Code for complex failures

5. **Refresh Scheduler** (`src/refresh_scheduler.py`)
   - Hourly data refresh
   - Automatic cache updates
   - Rate limit management

## Common Commands

### Starting/Stopping

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d spartan-web

# Stop all services
docker-compose down

# Restart service
docker-compose restart spartan-web

# View logs
docker-compose logs -f spartan-web
```

### Development

```bash
# Start web server (development mode)
python3 start_server.py

# Start simple server (JSON database only)
python3 simple_server.py

# Run data preloader manually
python3 src/data_preloader.py

# Test FRED API
python3 test_fred_api.py

# Validate all data sources
python3 comprehensive_validation_test.py
```

### Debugging

```bash
# Check container status
docker ps

# Check health endpoints
curl http://localhost:8888/health
curl http://localhost:8888/api/db/stats
curl http://localhost:8888/api/cache/stats

# Check Redis cache
redis-cli KEYS "yfinance:*"
redis-cli GET "yfinance:SPY"

# Check PostgreSQL
psql spartan_research_db -c "SELECT * FROM market_data LIMIT 10;"

# View monitor status
curl http://localhost:8888/api/monitor/status

# View recent incidents
psql spartan_research_db -c "SELECT * FROM monitor_incidents ORDER BY timestamp DESC LIMIT 10;"
```

### Data Management

```bash
# Clear Redis cache (force refresh)
redis-cli FLUSHDB

# Rebuild symbol database
python3 create_symbols_database_json.py

# Export market data
psql spartan_research_db -c "\COPY market_data TO 'data_export.csv' CSV HEADER;"

# Import market data
psql spartan_research_db -c "\COPY market_data FROM 'data_import.csv' CSV HEADER;"
```

## Critical Rules

### 1. NO FAKE DATA (Absolute)

```
❌ FORBIDDEN: Math.random(), mock data, simulated values
✅ REQUIRED: Real APIs only - yfinance, FRED, Alpha Vantage
✅ ON ERROR: Return NULL/None, never generate fake fallback
```

### 2. PostgreSQL Only

```
✅ ALLOWED: PostgreSQL 13+ ONLY
❌ FORBIDDEN: SQLite, MySQL, MongoDB
```

### 3. Don't Modify index.html

The `index.html` file (1,744 lines) contains the complete flashcard navigation system. **DO NOT modify, simplify, or replace this file.**

### 4. Data Preloader Gate

Website **CANNOT START** without successful data preload:
- 80%+ success rate required
- Critical sources must succeed (SPY, QQQ, DIA, IWM, VIX, FRED)
- Exit code 0 = success → website starts
- Exit code 1 = failure → website blocked

## Troubleshooting

### Website Won't Start

**Symptom**: `docker-compose up` hangs or fails

**Diagnosis**:
```bash
# Check preloader logs
docker-compose logs spartan-data-preloader

# Common issues:
# 1. FRED API key missing
grep FRED_API_KEY .env

# 2. Redis not running
redis-cli PING

# 3. PostgreSQL not running
psql -l
```

**Fix**:
```bash
# Add FRED API key
echo "FRED_API_KEY=your_key_here" >> .env

# Start Redis
docker-compose up -d redis

# Start PostgreSQL
sudo systemctl start postgresql
```

### Data Not Showing

**Symptom**: Dashboard loads but shows no data

**Diagnosis**:
```bash
# Check cache
redis-cli KEYS "*"

# Check recent data
curl http://localhost:8888/api/market/indices
```

**Fix**:
```bash
# Force data refresh
redis-cli FLUSHDB
docker-compose restart spartan-refresh-scheduler
```

### Container Keeps Restarting

**Symptom**: `docker ps` shows container constantly restarting

**Diagnosis**:
```bash
# View container logs
docker-compose logs spartan-web --tail=100

# Check monitor incidents
psql spartan_research_db -c "SELECT * FROM monitor_incidents WHERE container_name = 'spartan-web' ORDER BY timestamp DESC LIMIT 5;"
```

**Fix**:
```bash
# Let monitor auto-heal (wait 2-3 minutes)
# If persistent, escalate to Claude Code:
# Monitor will automatically trigger Claude Code after 5 failed heal attempts
```

### Monitor Not Healing

**Symptom**: Issues persist, monitor not auto-healing

**Diagnosis**:
```bash
# Check if monitor is running
docker ps | grep monitor

# Check monitor logs
tail -f logs/monitor.log
```

**Fix**:
```bash
# Restart monitor
docker-compose restart spartan-monitor

# Or start manually
mojo run agents/website_monitor/website_monitor.mojo
```

## Performance Expectations

### Startup Time

- **Data Preloader**: 45-85 seconds (depends on API response times)
- **Web Server**: <5 seconds
- **Total Startup**: ~60-90 seconds

### Resource Usage

- **CPU**: ~10% (1 core) for all services
- **Memory**: ~500MB total
- **Disk**: ~2GB (includes Docker images)

### Data Freshness

- **Cache TTL**: 15 minutes
- **Refresh Cycle**: 1 hour (via scheduler)
- **Manual Refresh**: Clear cache to force immediate refresh

### Monitoring Performance

- **Mojo Monitor**: <20ms per check cycle
- **Python Monitor**: ~200ms per check cycle
- **Check Interval**: 30 seconds
- **Auto-Heal Success**: ~95% of issues

## Environment Configuration

### Required Variables

```bash
# .env file
FRED_API_KEY=your_fred_api_key_here
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://user:pass@localhost/spartan_research_db
```

### Optional Variables

```bash
# Data API keys (fallbacks)
ALPHA_VANTAGE_API_KEY=your_key_here
POLYGON_IO_API_KEY=your_key_here

# Preloader settings
PRELOAD_TIMEOUT=60
PRELOAD_MIN_SUCCESS_RATE=0.80

# Cache settings
CACHE_TTL=900  # 15 minutes

# Monitor settings
MONITOR_INTERVAL=30  # seconds
MONITOR_AUTO_HEAL=true
```

## Next Steps

1. **Explore Documentation**:
   - `init/COMPLETE_SYSTEM_OVERVIEW.md` - Full system architecture
   - `init/agents/website_monitor.md` - Monitoring system
   - `init/agents/data_preloader.md` - Data preloading system
   - `init/agents/alert_watcher.md` - Alert monitoring

2. **Customize Dashboard**:
   - Add new data sources in `src/data_preloader.py`
   - Modify dashboards in `*.html` files
   - Update API endpoints in `swing_dashboard_api.py`

3. **Monitor System**:
   - Set up PostgreSQL queries for incident tracking
   - Configure alert notifications (email/Slack)
   - Review monitor logs regularly

4. **Production Deployment**:
   - See `DEPLOYMENT_GUIDE.md` for full deployment process
   - Configure systemd services for auto-start
   - Set up backups for PostgreSQL database

## Support

- **Documentation**: `init/` folder contains comprehensive guides
- **Logs**: Check `logs/` folder and `docker-compose logs`
- **Database**: Query `monitor_incidents` and `alerts` tables
- **Claude Code**: Will auto-trigger for complex issues

---

**Quick Reference Card**:

```bash
# Start system
docker-compose up -d

# Check health
curl http://localhost:8888/health

# View logs
docker-compose logs -f

# Force refresh
redis-cli FLUSHDB && docker-compose restart spartan-refresh-scheduler

# Stop system
docker-compose down
```

**Status Dashboard**: http://localhost:8888/health
**Main Dashboard**: http://localhost:8888
**API Base**: http://localhost:8888/api/
