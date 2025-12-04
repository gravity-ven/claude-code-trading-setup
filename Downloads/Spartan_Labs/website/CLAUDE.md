# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 💎 DIAMOND RULE: AUTONOMOUS AGENT CHAINING (MANDATORY)

**CRITICAL: Apply multi-agent thinking to ALL complex tasks in this codebase**

### Auto-Activation for Web Development

Agent chaining MUST activate automatically for:

1. ✅ **New features** - Dashboard components, API endpoints, data visualizations
2. ✅ **Data preloader changes** - Design → Implement → Validate → Test
3. ✅ **API modifications** - Plan → Design → Implement → Document → Test
4. ✅ **Frontend components** - Design → Implement → Test → Accessibility check
5. ✅ **Database schema changes** - Design → Migrate → Validate → Backup
6. ✅ **Bug fixes** - Analyze → Fix → Test → Validate data integrity
7. ✅ **Performance optimization** - Profile → Optimize → Benchmark → Validate
8. ✅ **Security features** - Design → Implement → Audit → Test

### Agent Chain Phases for This Project

**Phase 1: Planning** 🎯
- Understand requirements in context of Spartan Research Station
- Consider data flow: Preloader → Cache → API → Frontend
- Check PostgreSQL schema impact
- Review existing patterns

**Phase 2: Architecture** 🏗️
- Design within three-tier cache architecture
- Plan Redis caching strategy
- Design API contracts
- Consider microservices interactions

**Phase 3: Implementation** 💻
- Write production-quality Python/JavaScript
- Follow existing code patterns
- Implement with NO FAKE DATA (real APIs only)
- Apply rate limiting where needed

**Phase 4: Testing** 🧪
- Unit tests for Python code
- Integration tests for API endpoints
- Frontend testing considerations
- Data validation tests

**Phase 5: Review** 👀
- Code quality check
- PostgreSQL query optimization
- Redis caching validation
- JavaScript performance review

**Phase 6: Security** 🔒
- API authentication check
- Input validation
- SQL injection prevention (PostgreSQL parameterized queries)
- Rate limiting verification

**Phase 7: Documentation** 📚
- Update API documentation
- Add code comments
- Update CLAUDE.md if patterns change
- Note deployment considerations

**Phase 8: Integration** 📦
- Test with Docker compose
- Verify health endpoints
- Check data preloader compatibility
- Validate cache behavior

### Special Cases for This Project

**Data Preloader Changes**: Always chain Plan → Implement → Validate → Test data freshness
**API Endpoint Changes**: Always chain Design → Implement → Document → Test
**Frontend Components**: Always chain Design → Implement → Accessibility → Performance
**Database Changes**: Always chain Design → Backup → Migrate → Validate → Restore plan

### Output Format

Structure responses as:

```markdown
## 🔗 Agent Chain: [Feature/Task Name]

### [Phase 1] 🎯 Planning
<requirements analysis, data flow considerations>

### [Phase 2] 🏗️ Architecture
<system design, cache strategy, API contracts>

### [Phase 3] 💻 Implementation
<production code with real data sources>

### [Phase 4] 🧪 Testing
<test strategy and implementation>

### [Phase 5] 👀 Code Review
<quality checks, optimizations>

### [Phase 6] 🔒 Security Audit
<security validation>

### [Phase 7] 📚 Documentation
<docs updates>

### [Phase 8] 📦 Integration & Delivery
<Docker validation, deployment notes, final artifacts>
```

### Critical Rules for This Project

1. **NO FAKE DATA** - Always use real APIs (yfinance, FRED, etc.), never Math.random()
2. **PostgreSQL ONLY** - No SQLite, no exceptions
3. **Preserve index.html** - Don't modify flashcard navigation without explicit request
4. **Rate Limiting** - Always apply to new data sources
5. **Three-tier Cache** - IndexedDB → Redis → PostgreSQL, no shortcuts

### When NOT to Use Agent Chaining

❌ Quick Docker status checks
❌ Simple file reads
❌ Trivial git operations
❌ User says "quick" or "just show"

**Default: IF IN DOUBT, USE AGENT CHAINING**

---

## System Overview

**Spartan Research Station** - An autonomous, self-healing financial intelligence platform for swing traders and investors with real-time multi-asset market data.

**Tech Stack**: Python 3.13, PostgreSQL 13+, Redis, Docker, Flask, Vanilla JavaScript, yfinance, asyncio

**Critical Architecture**: Data preloader gate → Three-tier cache → Microservices → Autonomous monitor

---

## Quick Start Commands

### Native Development Workflow (Recommended)

```bash
# 1. Install PostgreSQL and Redis (one-time setup)
# macOS:
brew install postgresql@15 redis
brew services start postgresql@15
brew services start redis

# Linux:
sudo apt install postgresql-15 redis-server
sudo systemctl start postgresql redis

# Windows WSL2:
sudo apt install postgresql redis-server
sudo service postgresql start
sudo service redis-server start

# 2. Create database and user
createdb spartan_research_db
psql -d spartan_research_db -c "CREATE USER spartan WITH PASSWORD 'spartan';"
psql -d spartan_research_db -c "GRANT ALL PRIVILEGES ON DATABASE spartan_research_db TO spartan;"

# 3. Install Python dependencies
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your FRED_API_KEY (optional but recommended)

# 5. Run data preloader (loads market data)
python src/data_preloader.py

# 6. Start the main web server
python start_server.py
# Server runs on http://localhost:8888

# 7. (Optional) Start API microservices in separate terminals
python correlation_api.py       # Port 5004
python daily_planet_api.py      # Port 5000
python swing_dashboard_api.py   # Port 5002
python garp_api.py              # Port 5003
```

### Docker Workflow (Alternative)

```bash
# Start entire system with Docker
./START_SPARTAN.sh

# Manual Docker control
docker-compose up -d                    # Start all services
docker-compose ps                       # Check service status
docker-compose logs -f                  # View all logs
docker-compose restart spartan-web      # Restart specific service
docker-compose build spartan-web        # Rebuild after dependency changes

# Data management
docker-compose restart spartan-data-preloader     # Force data refresh
docker-compose logs spartan-data-preloader        # Check preloader status

# Health checks
curl http://localhost:8888/health
curl http://localhost:8888/health/data

# Database access
docker exec -it spartan-postgres psql -U spartan -d spartan_research_db

# Redis access
docker exec -it spartan-redis redis-cli
```

### Native Development - Common Commands

```bash
# Check PostgreSQL is running
psql -d spartan_research_db -c "SELECT version();"

# Check Redis is running
redis-cli ping  # Should return "PONG"

# View database tables
psql -d spartan_research_db -c "\dt"

# Check preloaded data
psql -d spartan_research_db -c "SELECT COUNT(*) FROM preloaded_market_data;"

# View Redis cache keys
redis-cli KEYS '*'

# Get cached market data
redis-cli GET market:index:SPY

# Manually refresh data
python src/data_preloader.py

# Run with auto-refresh (every 15 minutes)
python src/data_refresh_scheduler.py
```

### Testing

**Native Development**:

```bash
# Test data preloader
python src/data_preloader.py

# Test main server health
curl http://localhost:8888/health

# Test API endpoints
curl http://localhost:5004/health          # Correlation API (if running)
curl http://localhost:5000/health          # Daily Planet API (if running)
curl http://localhost:5002/api/swing-dashboard/health    # Swing API (if running)
curl http://localhost:5003/api/health      # GARP API (if running)

# Test database connection
python -c "import psycopg2; conn=psycopg2.connect('postgresql://spartan:spartan@localhost/spartan_research_db'); print('✅ Database connected')"

# Check data freshness in PostgreSQL
psql -d spartan_research_db -U spartan -c "SELECT COUNT(*) FROM preloaded_market_data WHERE timestamp > NOW() - INTERVAL '1 hour';"

# Check Redis cache
redis-cli KEYS '*'
redis-cli GET market:index:SPY

# Test yfinance data fetching
python -c "import yfinance as yf; spy=yf.Ticker('SPY'); print(spy.history(period='1d'))"

# Run unit tests (if available)
pytest tests/
```

**Docker Testing**:

```bash
# Test data preloader directly
docker exec spartan-data-preloader python src/data_preloader.py

# Test specific API endpoint
curl http://localhost:5004/health          # Correlation API
curl http://localhost:5000/health          # Daily Planet API
curl http://localhost:5002/api/swing-dashboard/health    # Swing API
curl http://localhost:5003/api/health      # GARP API

# Check PostgreSQL data freshness
docker exec -it spartan-postgres psql -U spartan -d spartan_research_db \
  -c "SELECT COUNT(*) FROM preloaded_market_data WHERE timestamp > NOW() - INTERVAL '1 hour';"

# Check Redis cache
docker exec -it spartan-redis redis-cli KEYS '*'
docker exec -it spartan-redis redis-cli GET market:index:SPY
```

---

## Architecture Concepts

### 1. Data Preloader Gate (BLOCKING STARTUP)

**Critical Pattern**: Website **CANNOT START** without successful data preload (exit code 0).

**Location**: `src/data_preloader.py`

**Docker Dependency Chain**:
```yaml
spartan-web:
  depends_on:
    spartan-data-preloader:
      condition: service_completed_successfully  # Blocks until exit 0
```

**Validation Rules**:
- 80%+ success rate across all data sources
- Critical sources MUST succeed: US Indices (SPY, QQQ, DIA, IWM), FRED Economic Data, VIX
- Exit code 0 = success (website starts), Exit code 1 = fail (website blocked)

**Data Sources** (13+):
- US Indices: SPY, QQQ, DIA, IWM (via yfinance)
- Global Indices: EFA, EEM, FXI, EWJ, EWG, EWU
- Commodities: GLD, USO, CPER
- Crypto: BTC-USD
- Forex: EUR/USD, GBP/USD, USD/JPY, AUD/USD
- Treasuries: SHY, IEF, TLT
- Global Bonds: BNDX, EMB
- FRED Economic: GDP, UNRATE, CPIAUCSL, FEDFUNDS, T10Y2Y
- Volatility: VIX
- Sectors: XLF, XLK, XLE, XLV, XLI, XLP, XLY, XLU, XLRE

**Rate Limiting** (Required):
- yfinance: 2s between requests
- polygon: 12s (free tier limit)
- alpha_vantage: 12s
- twelve_data: 8s
- coingecko: 1.5s

**Storage**:
- Primary: Redis (15-minute TTL) - Keys: `market:index:SPY`
- Backup: PostgreSQL `preloaded_market_data` table
- Auto-refresh: Every 15 minutes via `src/data_refresh_scheduler.py`

### 2. Three-Tier Cache Architecture

**Data Flow**: Client → IndexedDB → Redis → PostgreSQL → Null (NO FAKE DATA)

**Tier 1: IndexedDB** (Browser)
- 15-minute TTL
- Instant access, offline capability
- Managed by `js/spartan-preloader.js`

**Tier 2: Redis** (Server)
- 15-minute TTL
- Shared across users
- Key pattern: `market:*`, `data:*`

**Tier 3: PostgreSQL** (Server)
- Persistent backup
- Historical data
- Tables: `preloaded_market_data`, `market_data`

**Critical Rule**: Return `null` on cache miss. NEVER generate fake fallback data.

### 3. Microservices Architecture

**Main Web Server** (Port 8888):
- `start_server.py` - HTTP server with database API endpoints
- Serves static files (index.html, JS, CSS)
- Proxies to microservice APIs

**API Microservices**:
- `correlation_api.py` - Port 5004 - Correlation matrix
- `daily_planet_api.py` - Port 5000 - News/insights
- `swing_dashboard_api.py` - Port 5002 - Swing trading timeframes
- `garp_api.py` - Port 5003 - GARP stock screener

**Container Orchestration**: 9 Docker services in `docker-compose.yml`
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

### 4. Autonomous Monitor Agent (Disabled)

**Current Status**: Website monitor temporarily disabled (Mojo Docker image access issue)

**When Enabled**:
- Two-tier system: Mojo monitor (95% auto-heal) → Claude Code (5% complex issues)
- Location: `agents/website_monitor/website_monitor.mojo`
- Checks every 30 seconds
- Actions: restart, cache clear, DB reset, rebuild
- Incident tracking: PostgreSQL `monitor_incidents`, `monitor_healing_actions` tables

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

## Critical Rules

### 1. NO FAKE DATA (Absolute)

```
❌ FORBIDDEN: Math.random(), mock data, simulated values
✅ REQUIRED: Real APIs only (yfinance, FRED, Alpha Vantage)
✅ ON ERROR: Return NULL/None, never generate fake fallback data
```

**Why**: Users make financial decisions based on this data. Integrity over availability.

### 2. PostgreSQL Only

```
✅ ALLOWED: PostgreSQL 13+ ONLY
❌ FORBIDDEN: SQLite, MySQL, MongoDB
```

**Databases**:
- `spartan_research_db` - Main database
- `spartan_trading_db` - Trading agent (separate project)

### 3. Preserve index.html Structure

The `index.html` file (2,051 lines) contains the complete flashcard navigation system. **DO NOT modify, simplify, or replace** this file unless specifically requested by the user.

### 4. Rate Limiting Required

**ALWAYS** apply rate limiting when adding new data sources to prevent API blocks:
- Add delays to `REQUEST_DELAYS` dict in `src/data_preloader.py`
- Use `rate_limit(api_name)` before each API call
- Test with `docker exec spartan-data-preloader python src/data_preloader.py`

---

## Common Development Tasks

### Fixing Preloader Failures

**Symptom**: Website won't start, preloader exits with code 1

**Debug**:
```bash
# Check preloader logs
docker-compose logs spartan-data-preloader

# Look for validation errors
docker-compose logs spartan-data-preloader | grep "❌"

# Check exit code
docker inspect spartan-data-preloader --format='{{.State.ExitCode}}'
```

**Common Fixes**:
1. Add missing API keys to `.env` (especially `FRED_API_KEY`)
2. Temporarily lower `SUCCESS_THRESHOLD` in `src/data_preloader.py`
3. Disable problematic sources in preloader config
4. Check network connectivity to APIs
5. Verify rate limiting delays are sufficient

### Adding New Data Source

**Steps**:

1. Edit `src/data_preloader.py`:

```python
async def preload_new_source(self):
    """Fetch new data source"""
    try:
        # CRITICAL: Apply rate limiting
        rate_limit('api_name')

        # Fetch data using REAL API (no fake data)
        data = await fetch_from_real_api()

        # Cache in Redis (15-min TTL)
        await self.redis_client.set(
            f'data:new_source',
            json.dumps(data),
            ex=self.cache_ttl
        )

        # Backup to PostgreSQL
        await self.save_to_db('new_source', data)

        return True
    except Exception as e:
        logger.error(f"Failed to fetch new source: {e}")
        return False  # Don't raise - allows other sources to continue

# Add to preload_all_data()
results["New_Source"] = await self.preload_new_source()
```

2. Add rate limiting configuration:

```python
# At top of file
REQUEST_DELAYS = {
    # ...existing delays...
    'api_name': 5.0,  # 5 seconds between requests
}
```

3. Update validation threshold calculation to include new source

4. Test:
```bash
docker exec spartan-data-preloader python src/data_preloader.py
```

### Debugging Data Issues

**Data Not Showing on Dashboard**:

1. Check if preloader ran successfully:
   ```bash
   docker logs spartan-data-preloader | grep "✅"
   ```

2. Verify Redis cache:
   ```bash
   docker exec -it spartan-redis redis-cli
   > KEYS *
   > GET market:index:SPY
   ```

3. Check PostgreSQL backup:
   ```bash
   docker exec -it spartan-postgres psql -U spartan -d spartan_research_db \
     -c "SELECT COUNT(*) FROM preloaded_market_data WHERE timestamp > NOW() - INTERVAL '1 hour';"
   ```

4. Check browser console for JavaScript errors

**Container Keeps Restarting**:

1. Check logs for the specific container:
   ```bash
   docker-compose logs -f spartan-research-station
   ```

2. Check health endpoint:
   ```bash
   curl http://localhost:8888/health
   ```

3. Restart with rebuild:
   ```bash
   docker-compose build spartan-research-station
   docker-compose up -d spartan-research-station
   ```

### Modifying Frontend JavaScript

**Pattern** (three-tier cache):

```javascript
// 1. Check IndexedDB first
const cachedData = await window.SpartanData.get('symbol:SPY');
if (cachedData && isFresh(cachedData)) {
    return cachedData;
}

// 2. Fetch from API (checks Redis → PostgreSQL internally)
const freshData = await fetch('/api/market/symbol/SPY');

// 3. Store in IndexedDB for next time
await window.SpartanData.store('symbol:SPY', freshData);
```

**Rules**:
1. Never add `Math.random()` or fake data
2. Always use three-tier cache pattern
3. Preserve existing data validation logic
4. Test locally: `docker-compose restart spartan-research-station`

### Modifying Python API Servers

**Rules**:
1. Use `async`/`await` for all I/O operations
2. Always validate API responses before caching
3. Return `None` on errors (never fake data)
4. Add comprehensive error logging
5. Apply rate limiting for external APIs
6. Test endpoint: `curl http://localhost:{port}/health`

**Example**:

```python
from flask import Flask, jsonify
import yfinance as yf

app = Flask(__name__)

@app.route('/api/data/<symbol>')
def get_symbol_data(symbol):
    try:
        # Fetch real data
        ticker = yf.Ticker(symbol)
        data = ticker.history(period='1d')

        # Validate response
        if data.empty:
            return jsonify({'error': 'No data available'}), 404

        # Return real data
        return jsonify({
            'symbol': symbol,
            'price': float(data['Close'][-1]),
            'timestamp': data.index[-1].isoformat()
        })
    except Exception as e:
        # Log error
        app.logger.error(f"Error fetching {symbol}: {e}")

        # Return error (NO fake data)
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})
```

---

## Environment Configuration

**Required Environment Variables** (`.env`):

```bash
# Essential (required for startup)
FRED_API_KEY=your_fred_key                    # Economic data

# Optional (for enhanced data coverage)
ALPHA_VANTAGE_API_KEY=your_av_key
POLYGON_IO_API_KEY=your_polygon_key
TWELVE_DATA_API_KEY=your_td_key
FINNHUB_API_KEY=your_finnhub_key

# Monitor Agent (optional - currently disabled)
ANTHROPIC_API_KEY=sk-ant-...                  # For Claude AI diagnosis

# Database (auto-configured in Docker)
DATABASE_URL=postgresql://spartan:spartan@postgres:5432/spartan_research_db
POSTGRES_USER=spartan
POSTGRES_PASSWORD=spartan
POSTGRES_DB=spartan_research_db
```

---

## Performance Characteristics

### Startup Time
- Infrastructure (PostgreSQL + Redis): 5-10 seconds
- Data Preloader: 30-60 seconds (13+ sources with rate limiting)
- Web Server: 5-10 seconds
- **Total**: 45-85 seconds to fully operational

### Resource Usage
- PostgreSQL: 1-5% CPU, 100MB RAM
- Redis: <1% CPU, 20MB RAM
- Web Server: 2-10% CPU, 150MB RAM
- **Total**: ~10% CPU, ~500MB RAM

---

## Troubleshooting Guide

### Preloader Validation Failures

**Error**: `❌ Data validation failed: Only X% sources succeeded (threshold: 80%)`

**Solution**:
1. Check which sources failed: `docker-compose logs spartan-data-preloader | grep "❌"`
2. Verify API keys in `.env` file
3. Test individual source by running preloader with logging
4. Temporarily lower threshold OR disable problematic source

### Website Won't Start

**Symptom**: `spartan-web` container exits immediately

**Debug**:
```bash
# Check if preloader completed successfully
docker inspect spartan-data-preloader --format='{{.State.ExitCode}}'
# Should return 0

# If non-zero, fix preloader first
docker-compose logs spartan-data-preloader

# Check web server logs
docker-compose logs spartan-web
```

### Data Staleness

**Symptom**: Dashboard shows old data (>15 minutes)

**Debug**:
```bash
# Check if refresh scheduler is running
docker-compose ps spartan-data-refresh

# Check refresh logs
docker-compose logs spartan-data-refresh | tail -20

# Check Redis cache freshness
docker exec -it spartan-redis redis-cli
> TTL market:index:SPY
# Should show seconds remaining (up to 900 for 15 min)

# Manually trigger refresh
docker-compose restart spartan-data-refresh
```

### API Rate Limiting Errors

**Symptom**: `429 Too Many Requests` or similar errors in logs

**Solution**:
1. Increase delay in `REQUEST_DELAYS` dict in `src/data_preloader.py`
2. Verify rate limit decorators are applied to all API calls
3. Check if multiple services are hitting same API simultaneously
4. Consider upgrading to paid API tier if needed

### Native Development Issues

**PostgreSQL Connection Errors**:

```bash
# Check if PostgreSQL is running
psql -V  # Check version
pg_isready  # Check if server is ready

# Start PostgreSQL
# macOS: brew services start postgresql@15
# Linux: sudo systemctl start postgresql
# WSL2: sudo service postgresql start

# Check connection
psql -d spartan_research_db -U spartan

# If database doesn't exist, create it
createdb spartan_research_db
```

**Redis Connection Errors**:

```bash
# Check if Redis is running
redis-cli ping  # Should return "PONG"

# Start Redis
# macOS: brew services start redis
# Linux: sudo systemctl start redis
# WSL2: sudo service redis-server start

# Check Redis data
redis-cli
> KEYS *
> GET market:index:SPY
```

**Python Module Import Errors**:

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt

# Check Python version
python --version  # Should be 3.13+
```

**Port Already in Use**:

```bash
# Find process using port 8888
lsof -i :8888  # macOS/Linux
netstat -ano | findstr :8888  # Windows

# Kill the process
kill -9 <PID>  # macOS/Linux

# Or use a different port
python start_server.py --port 8889
```

**Data Preloader Fails on Native Setup**:

```bash
# Run preloader with verbose logging
python src/data_preloader.py --verbose

# Check environment variables
cat .env | grep FRED_API_KEY

# Test Redis connection
python -c "import redis; r=redis.Redis(); print(r.ping())"

# Test PostgreSQL connection
python -c "import psycopg2; conn=psycopg2.connect('postgresql://spartan:spartan@localhost/spartan_research_db'); print('Connected')"
```

---

## Git Workflow

**Commits**:
- Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`
- Include co-author: `Co-Authored-By: Claude <noreply@anthropic.com>`

**Before Pushing**:
1. Test locally with Docker: `docker-compose up -d`
2. Run health checks: `curl http://localhost:8888/health`
3. Verify data preloader succeeds: `docker-compose logs spartan-data-preloader | grep "✅"`
4. Check git status: `git status`

---

## Portability

### Native Development

**Supported Platforms**: macOS, Linux, Windows WSL2

**Requirements**:
- Python 3.13+
- PostgreSQL 13+ (running locally)
- Redis 6.0+ (running locally)
- 2GB RAM minimum, 4GB recommended
- 1GB disk space

**Quick Setup**:
1. Install PostgreSQL and Redis (see "Native Development Workflow" above)
2. Create database and user
3. Install Python dependencies: `pip install -r requirements.txt`
4. Configure `.env` file
5. Run preloader: `python src/data_preloader.py`
6. Start server: `python start_server.py`

### Docker Development

**Supported Platforms**: macOS, Linux, Windows WSL2

**Requirements**:
- Docker Desktop 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum, 8GB recommended
- 5GB disk space

**Quick Setup**:
- Run: `./START_SPARTAN.sh` (auto-detects OS and configures)

### Native vs Docker: When to Use Each

**Use Native Development When**:
- Developing locally and want fast iteration
- Debugging Python code directly
- Don't want Docker overhead
- Running on resource-constrained machine
- Need direct access to PostgreSQL/Redis

**Use Docker When**:
- Deploying to production
- Need consistent environment across team
- Want isolated services
- Testing full microservices architecture
- Need autonomous monitoring agent

---

## Related Documentation

- `DATA_PRELOADER_GUIDE.md` - Detailed preloader architecture
- `WEBSITE_MONITOR_QUICKSTART.md` - Monitor agent setup
- `CLAUDE_AUTONOMOUS_MODE.md` - Claude AI integration
- `DEPLOYMENT_GUIDE.md` - Production deployment
- `ARCHITECTURE.md` - Full system architecture
- `README.md` - Project overview

---

**Last Updated**: November 23, 2025
**Version**: 1.3.0
**Status**: Production Ready
