# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

# 8. (NEW) Start Trading LLM AI Agent System
python trading_llm_api.py       # Port 9005 - AI-powered trading signals
# Dashboard: http://localhost:8888/trading_llm.html
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

## Trading LLM AI Agent System (NEW)

### Overview

**Trading LLM** is an AI-powered multi-asset trading intelligence system that provides real-time trading signals and analysis across:
- **Futures**: Indices (ES, NQ, YM), commodities (GC, CL, NG), currencies, bonds
- **Stocks**: Global equities, ETFs, indices (SPY, QQQ, DIA)
- **Forex**: Major, minor, and exotic currency pairs
- **Bonds**: Government and corporate bonds (TLT, IEF, SHY)
- **Crypto**: Bitcoin, Ethereum, altcoins (BTC-USD, ETH-USD)
- **CFDs**: Contracts for difference across all assets

**Port**: 9005
**Frontend**: `trading_llm.html`
**Database Tables**: `trading_llm_signals`, `trading_llm_trades`, `trading_llm_performance_daily`

### Architecture

**Data Integration Layer**:
```
Barometers API (8001) ──┐
CFTC COT Data ──────────┤
Breakthrough Insights ───┼──→ Trading LLM Engine ──→ Signal Generation
Macro Regime ────────────┤        (Port 9005)              ↓
VIX & Volatility ────────┤                          Frontend Dashboard
Correlation Matrix ──────┘                          + Trade Logging
```

**Self-Improvement Loop**:
```
Trade Execution → Outcome Tracking → Learning System → Strategy Adaptation
      ↑                                                        ↓
      └────────────────── Improved Signals ←──────────────────┘
```

### Core Capabilities

1. **Multi-Source Analysis**
   - Integrates with all Spartan Labs data infrastructure
   - Real-time FRED economic indicators
   - CFTC positioning and institutional flows
   - VIX and volatility regime detection
   - Intermarket correlation analysis

2. **Signal Generation**
   - Signal types: Strong Buy, Buy, Hold, Sell, Strong Sell
   - Confidence scores: 0-100% (multi-factor weighted)
   - Entry levels with price ranges
   - ATR-based stop losses
   - Multiple take-profit targets (R:R optimized)
   - Kelly Criterion position sizing

3. **Time Horizons**
   - **Scalp**: Minutes to hours
   - **Intraday**: Same-day trades
   - **Swing**: 1-2 weeks (primary focus)
   - **Position**: 1-3 months
   - **Trend**: 6-18 months

4. **Self-Improvement**
   - Recursive learning from trade outcomes
   - Skill accumulation and evolution
   - Bidirectional agent integration
   - Meta-cognition and strategy adaptation

### API Endpoints

**Health Check**:
```bash
GET http://localhost:9005/api/health
```

**Analyze Symbol**:
```bash
POST http://localhost:9005/api/analyze
{
  "symbol": "SPY",
  "asset_class": "stocks",
  "time_horizon": "swing"
}
```

**Full Market Scan**:
```bash
GET http://localhost:9005/api/scan
```

**Market Context**:
```bash
GET http://localhost:9005/api/context/summary
```

**Top Signals**:
```bash
GET http://localhost:9005/api/top-signals?limit=10&min_confidence=60
```

**Log Trade**:
```bash
POST http://localhost:9005/api/trades
{
  "signal_id": 123,
  "entry_price": 450.00,
  "quantity": 100,
  "entry_time": "2026-01-01T12:00:00"
}
```

**Performance Metrics**:
```bash
GET http://localhost:9005/api/performance/daily?days=30
```

### Claude Code Integration

**Slash Commands**:

- `/analyze [SYMBOL]` - Analyze specific symbol (e.g., `/analyze SPY`)
- `/scan` - Full market scan across all asset classes
- `/context` - Get current market context
- `/futures` - Futures-specific analysis

**Auto-Activation Keywords** (Genius DNA):
- "analyze trading"
- "market scan"
- "trading signals"
- "futures analysis"
- "stock signals"
- "forex opportunities"
- "crypto trading"
- "multi-asset scan"

### Startup Commands

**Manual Startup**:
```bash
# Start Trading LLM API
python trading_llm_api.py

# Verify running
curl http://localhost:9005/api/health

# Open dashboard
# http://localhost:8888/trading_llm.html
```

**BULLETPROOF_STARTUP Integration**:
```python
from BULLETPROOF_STARTUP import BulletproofStartup

startup = BulletproofStartup()
startup.start_all()  # Includes Trading LLM on Port 9005
```

### Database Schema

**trading_llm_signals**:
- Stores all generated signals with full analysis
- Fields: symbol, asset_class, signal_type, confidence, entry_price, stop_loss, take_profit, etc.

**trading_llm_trades**:
- Logs all trades with entry/exit and P&L calculation
- Fields: signal_id, entry_price, exit_price, quantity, profit_loss, etc.

**trading_llm_performance_daily**:
- Daily aggregated performance metrics
- Fields: date, total_trades, win_rate, profit_factor, sharpe_ratio, max_drawdown

**trading_llm_self_improvement_log**:
- Tracks learning events and strategy adaptations
- Fields: timestamp, event_type, signal_id, outcome, adaptation_action

### Risk Management

**Default Parameters**:
- Maximum position size: 2% of account
- Maximum daily loss: 5% of account
- Maximum drawdown before shutdown: 15%
- Stop loss: 2.0 × ATR
- Take profit: 2.0 × Risk (R:R ratio)

**Signal Filtering**:
- Minimum confidence threshold: 60% (configurable)
- Asset class diversification enforced
- Time horizon balance maintained

### Performance Tracking

**Metrics**:
- Win Rate: Percentage of profitable trades
- Profit Factor: Gross profit / gross loss
- Sharpe Ratio: Risk-adjusted returns
- Max Drawdown: Largest peak-to-trough decline
- Average R:R: Average risk-reward ratio
- Signal Accuracy: Confidence vs. actual outcomes

**Self-Learning**:
- Daily adaptation based on outcomes
- Weekly strategy review and optimization
- Monthly meta-analysis and evolution

### Integration with Other Systems

**Consumes From**:
- COT Agents: CFTC positioning data
- Data Guardian: Validated market data
- Barometers API: Real-time sentiment

**Produces To**:
- Trading Dashboards: Signal visualization
- Alert Systems: High-confidence opportunities
- Downstream Agents: Inter-agent signals

### Files

**Core Engine**:
- `trading_llm_engine.py` (868 lines) - Main analysis engine
- `trading_llm_api.py` (817 lines) - Flask API server
- `trading_llm_self_improvement.py` (834 lines) - Learning system

**Frontend**:
- `trading_llm.html` (907 lines) - Dashboard with real-time signals

**Database**:
- `trading_llm_schema.sql` (382 lines) - PostgreSQL schema

**Orchestration**:
- `BULLETPROOF_STARTUP.py` (114 lines) - Startup coordination

**Claude Commands**:
- `.claude/commands/trading/analyze.md` - Symbol analysis
- `.claude/commands/trading/scan.md` - Market scan
- `.claude/commands/trading/context.md` - Market context
- `.claude/commands/trading/futures.md` - Futures analysis

### Usage Examples

**Daily Market Scan**:
```python
import requests

# Morning routine - scan all markets
response = requests.get("http://localhost:9005/api/scan")
signals = response.json()

# Filter high-confidence signals
high_conf = [s for s in signals if s['confidence'] >= 70]

# Review top 10 opportunities
for signal in high_conf[:10]:
    print(f"{signal['symbol']}: {signal['signal_type']} ({signal['confidence']}%)")
```

**Individual Symbol Analysis**:
```python
# Deep dive on Nasdaq futures
response = requests.post("http://localhost:9005/api/analyze", json={
    "symbol": "NQ",
    "asset_class": "futures",
    "time_horizon": "swing"
})

analysis = response.json()
print(f"Signal: {analysis['signal_type']}")
print(f"Entry: {analysis['entry_price']}")
print(f"Stop: {analysis['stop_loss']}")
print(f"Target: {analysis['take_profit']}")
```

**Trade Logging & Performance**:
```python
# Log trade entry
trade = requests.post("http://localhost:9005/api/trades", json={
    "signal_id": 123,
    "entry_price": 450.00,
    "quantity": 100,
    "entry_time": "2026-01-01T12:00:00"
})

# Log trade exit
requests.put(f"http://localhost:9005/api/trades/{trade['id']}", json={
    "exit_price": 465.00,
    "exit_time": "2026-01-01T14:30:00"
})

# View performance
perf = requests.get("http://localhost:9005/api/performance/daily?days=30")
print(f"Win Rate: {perf['win_rate']}%")
print(f"Profit Factor: {perf['profit_factor']}")
print(f"Sharpe Ratio: {perf['sharpe_ratio']}")
```

### Best Practices

1. **Always Check Market Context First**: Review macro regime and risk sentiment before taking signals
2. **Filter by Confidence**: Use 60-70% minimum confidence thresholds
3. **Diversify Asset Classes**: Don't concentrate in a single asset or time horizon
4. **Log All Trades**: Enable self-improvement through rigorous tracking
5. **Monitor Self-Learning**: Review adaptation events and strategy evolution weekly

### Security

**Data Integrity** (PLATINUM RULE):
- All data from verified sources only
- No fake data generation, ever
- Real-time validation of all inputs

**API Security**:
- Localhost-only binding by default
- API key authentication for remote access
- Rate limiting on all endpoints

**Risk Limits**:
- Hard stops on position sizing
- Circuit breakers on daily losses
- Automatic shutdown on max drawdown

### Status

✅ **Active and Integrated**
📊 **Database**: PostgreSQL (spartan_research_db)
🌐 **Frontend**: http://localhost:8888/trading_llm.html
🔗 **Dependencies**: All Spartan Labs data infrastructure
🤖 **Self-Improvement**: Enabled with daily adaptation
🔄 **Bidirectional**: Consumes and produces agent signals

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
