# Data Point Agents System

## 🎯 Overview

A revolutionary **agent-per-data-point architecture** where each data point on the website has its own dedicated agent running 24/7 to ensure genuine data is always available.

```
SPY Agent  <- Dedicated to S&P 500 ETF data
QQQ Agent  <- Dedicated to NASDAQ-100 ETF data  
BTC Agent  <- Dedicated to Bitcoin data
VIX Agent  <- Dedicated to Volatility index
10Y Agent <- Dedicated to 10-Year Treasury yield
```

## 🚀 Quick Start

```bash
# Start all agents with monitoring
./START_DATA_POINT_AGENTS.sh

# Check system status
./CHECK_DATA_POINT_AGENTS.sh

# Stop all agents
./STOP_DATA_POINT_AGENTS.sh
```

## 🏗️ Architecture

### Core Components

1. **Individual Data Point Agents** - Each owns ONE data point
2. **Master Orchestrator** - Coordinates all agents with auto-healing
3. **Health Monitoring API** - Real-time system health and data access
4. **Data Router** - Bridge between main website and agent system

### Data Point Agents

| Agent | Data Point | Primary APIs | Fallback APIs |
|-------|------------|--------------|----------------|
| SPY Agent | S&P 500 ETF | Polygon.io → Yahoo Finance | Alpha Vantage, Twelve Data, Finnhub |
| QQQ Agent | NASDAQ-100 ETF | Polygon.io → Yahoo Finance | Alpha Vantage, Twelve Data, Finnhub |
| BTC-USD Agent | Bitcoin | CoinGecko → Yahoo Finance | Alpha Vantage, Twelve Data, Polygon.io |
| VIX Agent | Volatility Index | FRED → Yahoo Finance | Polygon.io |
| 10Y Treasury Agent | 10Y Treasury Yield | FRED → Yahoo Finance | ETF proxy calculations |

### API Priority Strategy

- **Phase 1**: Paid APIs (highest quality - Polygon.io, FRED, Alpha Vantage)
- **Phase 2**: Free APIs (excellent backup - Yahoo Finance, CoinGecko)
- **Phase 3**: Emergency fallbacks (calculated proxies, cached data)

## 📊 Monitoring & Management

### Health Dashboard (Port 8890)

```bash
# System health
curl http://localhost:8890/api/agents/health

# Individual agent status
curl http://localhost:8890/api/agents/status/spy_agent

# Market summary from all agents
curl http://localhost:8890/api/data/market-summary

# Real-time WebSocket updates
ws://localhost:8890/ws/health
```

### Management Scripts

| Script | Purpose |
|--------|---------|
| `START_DATA_POINT_AGENTS.sh` | Start all agents with monitoring |
| `STOP_DATA_POINT_AGENTS.sh` | Stop all agents gracefully |
| `CHECK_DATA_POINT_AGENTS.sh` | Check system status and health |

### Available Endpoints

#### Agent System (Port 8890)
```
GET /api/agents/health          # System-wide health status
GET /api/agents/status/{agent_id} # Individual agent details
GET /api/agents/metrics          # System performance metrics
GET /api/agents/list             # List all registered agents
GET /api/data/point/{symbol}     # Get data from specific agent
GET /api/data/market-summary     # Market overview
WS /ws/health                   # Real-time health updates
```

#### Data Router (Port 8891)
```
GET /api/data/point/{symbol}     # Forwarded from main server
GET /api/data/market-summary     # Forwarded to agents
GET /api/data/points             # All agent data
GET /api/agents/*                # Agent system endpoints
```

## 🔧 Configuration

### Required Environment Variables

```bash
# Paid APIs (optional but recommended)
POLYGON_IO_API_KEY=your_polygon_key
FRED_API_KEY=your_fred_key
ALPHA_VANTAGE_API_KEY=your_av_key
TWELVE_DATA_API_KEY=your_td_key
FINNHUB_API_KEY=your_finnhub_key

# Database (required)
DATABASE_URL=postgresql://spartan:spartan@localhost:5432/spartan_research_db
POSTGRES_USER=spartan
POSTGRES_PASSWORD=spartan
POSTGRES_DB=spartan_research_db

# Redis (required)
REDIS_HOST=localhost
REDIS_PORT=6379
```

### API Key Requirements

| Data Point | Minimum Required APIs | Recommended APIs |
|-------------|----------------------|------------------|
| SPY, QQQ | Yahoo Finance (free) | Polygon.io + Yahoo Finance |
| BTC-USD | CoinGecko (free) | CoinGecko + Polygon.io |
| VIX | Yahoo Finance (free) | FRED + Yahoo Finance |
| 10Y Treasury | Yahoo Finance (free) | FRED + Yahoo Finance |

## 🛡️ Data Integrity Guarantees

### No Fake Data Policy
- ✅ Returns `null` if all sources fail
- ✅ Never generates simulated values
- ✅ All data source attribution preserved
- ✅ Quality scoring for each data point

### 24/7 Availability
- ✅ Continuous background fetching
- ✅ Auto-restart on failures
- ✅ Intelligent retry with exponential backoff
- ✅ Multiple sources for redundancy

### Real-Time Monitoring
- ✅ Health status per agent
- ✅ Data quality scoring
- ✅ Source tracking
- ✅ Performance metrics

## 📈 Performance Characteristics

### System Resources
- **CPU**: ~10% usage (5 agents + orchestrator)
- **Memory**: ~500MB total (including cache)
- **Network**: Moderate (API rate limiting applied)

### Data Freshness
- **Update Interval**: Every 5 minutes
- **Cache TTL**: 5 minutes (Redis) + 1 hour (PostgreSQL)
- **Stale Threshold**: 10 minutes before considered stale

### Response Times
- **Cache Hit**: <50ms
- **Fresh Fetch**: 1-3 seconds (depends on API)
- **Health Check**: <100ms

## 🔄 Integration with Main Website

### Main Server Integration (Port 8888)

The main server automatically prioritizes data from:
1. **Agent System** (if available) - Highest priority
2. **Legacy Redis Cache** - Fallback
3. **Legacy PostgreSQL** - Final fallback
4. **Direct Fetch** - Emergency only

### Seamless Migration
- ✅ No changes required to frontend code
- ✅ Backward compatible with existing API endpoints
- ✅ Graceful fallback if agents not running
- ✅ Improved reliability when agents are active

## 🚨 Troubleshooting

### Common Issues

**Agents Not Starting**
```bash
# Check logs
tail -f logs/agents/orchestrator.log
tail -f logs/agents/health_api.log

# Check API keys
grep -E "API_KEY" .env

# Check database connection
python3 -c "import psycopg2; conn=psycopg2.connect('postgresql://spartan:spartan@localhost/spartan_research_db'); print('✅ DB connection works')"
```

**API Rate Limits**
```bash
# Check error logs for rate limiting
grep -i "rate\|limit" logs/agents/*.log

# Check API key validity
curl -H "Authorization: Bearer $POLYGON_IO_API_KEY" https://api.polygon.io/v2/aggs/ticker/SPY/prev
```

**Agents Keep Crashing**
```bash
# Check consecutive failures
curl http://localhost:8890/api/agents/metrics

# Check system resources
free -h
df -h

# Restart with cleanup
./STOP_DATA_POINT_AGENTS.sh --cleanup-logs
./START_DATA_POINT_AGENTS.sh
```

## 📁 File Structure

```
website/
├── agents/
│   ├── data_points/           # Individual data point agents
│   │   ├── base_data_point_agent.py
│   │   ├── spy_agent.py
│   │   ├── qqq_agent.py
│   │   ├── btc_usd_agent.py
│   │   ├── vix_agent.py
│   │   └── treasury_10y_agent.py
│   ├── data_point_master_orchestrator.py
│   └── agent_health_api.py
├── logs/agents/               # Agent system logs
├── START_DATA_POINT_AGENTS.sh
├── STOP_DATA_POINT_AGENTS.sh
├── CHECK_DATA_POINT_AGENTS.sh
└── agent_data_router.py       # Bridge to main server
```

## 🎯 Benefits

### For Operators
- **Zero Downtime** - Individual agents restart independently
- **Easy Debugging** - Each data point has clear ownership
- **Scalable** - Add new data points with dedicated agents
- **Monitoring** - Real-time health metrics and alerts

### For Users
- **Higher Reliability** - Multiple sources per data point
- **Faster Updates** - Continuous fetching vs batch processing
- **Better Quality** - Source attribution and quality scoring
- **Transparent** - Always shows data source and freshness

### For Developers
- **Clear Architecture** - One responsibility per agent
- **Testable** - Individual agents can be tested in isolation
- **Maintainable** - Failed agents don't affect others
- **Extensible** - Easy to add new data points and agents

## 🔮 Future Enhancements

### Planned Features
- [ ] **WebSocket Data Streaming** - Real-time price updates
- [ ] **Advanced Analytics** - Cross-data-point correlations
- [ ] **Automated Trading** - Signal generation from agents
- [ ] **Historical Analysis** - Data point performance tracking
- [ ] **Mobile Dashboard** - Agent monitoring on mobile devices

### Potential New Agents
- [ ] **Gold Agent** (GLD)
- [ ] **Oil Agent** (USO)
- [ ] **EUR/USD Agent** (Forex)
- [ ] **DXY Agent** (Dollar Index)
- [ ] **Sector Rotation Agents** (XLF, XLK, XLE, etc.)

---

**🎯 Mission**: Every data point on the website has a dedicated permanent agent ensuring 24/7 genuine data availability with intelligent fallback strategies.

**📊 Status**: Production Ready ✅

**🔄 Last Updated**: December 2024
