# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## System Overview

**Spartan Research Station** - An autonomous, self-healing financial intelligence platform for swing traders and investors with real-time multi-asset market data.

**Tech Stack**: Python 3.11+, PostgreSQL 13+, Redis, Docker, Flask, Vanilla JavaScript, yfinance, asyncio

## Quick Reference

| Action | Command |
|--------|---------|
| Start all (Docker) | `./START_SPARTAN.sh` |
| Start native | `python start_server.py` |
| Health check | `curl localhost:8888/health` |
| View logs | `docker-compose logs -f` |
| Run tests | `pytest tests/` |
| Lint | `ruff check src/` |
| Format | `black src/` |
| Preload data | `python src/data_preloader.py` |

## Port Reference

| Service | Port | File |
|---------|------|------|
| Main Web Server | 8888 | `start_server.py` |
| Daily Planet API | 5000 | `daily_planet_api.py` |
| Swing Dashboard API | 5002 | `swing_dashboard_api.py` |
| GARP API | 5003 | `garp_api.py` |
| Correlation API | 5004 | `correlation_api.py` |
| Trading LLM API | 9005 | `trading_llm_api.py` |
| PostgreSQL | 5432 | - |
| Redis | 6379 | - |

## Development Commands

### Installation

```bash
# Option 1: pip install with dev dependencies
pip install -e ".[dev]"

# Option 2: Manual install
pip install -r requirements.txt
```

### Running the System

```bash
# Native (single terminal)
python start_server.py                    # Main server on :8888

# Native (full microservices - separate terminals)
python start_server.py                    # Port 8888
python daily_planet_api.py                # Port 5000
python swing_dashboard_api.py             # Port 5002
python garp_api.py                        # Port 5003
python correlation_api.py                 # Port 5004
python trading_llm_api.py                 # Port 9005

# Docker (all services)
./START_SPARTAN.sh                        # Full system
docker-compose up -d                      # Background mode
docker-compose down                       # Stop all
```

### Testing

```bash
pytest tests/                             # All tests
pytest -m unit                            # Fast unit tests
pytest -m integration                     # DB/API tests
pytest tests/unit/test_sample.py          # Single file
pytest --cov=src --cov-report=html        # With coverage
pytest -n auto                            # Parallel
```

### Linting & Formatting

```bash
black src/                                # Format
ruff check src/ --fix                     # Lint + auto-fix
mypy src/                                 # Type check
isort src/                                # Sort imports
```

## Architecture

```
Data Sources (yfinance, FRED, Alpha Vantage)
         ↓ [rate-limited]
   Data Preloader (BLOCKING - exit 0 required)
         ↓
  Redis (15min TTL) → PostgreSQL (backup)
         ↓
   Web Server (:8888) + Microservices
         ↓
  IndexedDB (browser, 15min TTL)
```

### Data Preloader Gate (CRITICAL)

Website **CANNOT START** without successful data preload.

**Location**: `src/data_preloader.py`

**Rules**:
- 80%+ success rate across data sources required
- Critical sources MUST succeed: SPY, QQQ, DIA, IWM, VIX, FRED
- Exit code 0 = success, Exit code 1 = website blocked

**Rate Limiting** (Required):
| API | Delay |
|-----|-------|
| yfinance | 2s |
| polygon | 12s |
| alpha_vantage | 12s |
| twelve_data | 8s |
| coingecko | 1.5s |

### Three-Tier Cache

**Flow**: Client → IndexedDB → Redis → PostgreSQL → Null (NO FAKE DATA)

| Tier | Location | TTL | Purpose |
|------|----------|-----|---------|
| 1 | IndexedDB | 15min | Browser cache |
| 2 | Redis | 15min | Server cache |
| 3 | PostgreSQL | Persistent | Backup/history |

**Critical Rule**: Return `null` on cache miss. NEVER generate fake fallback data.

### Microservices (Docker)

9 services in `docker-compose.yml`:
- spartan-web, spartan-postgres, spartan-redis
- spartan-data-preloader (one-shot), spartan-data-refresh (15-min loop)
- spartan-correlation-api, spartan-daily-planet-api, spartan-swing-api, spartan-garp-api

## Critical Rules

### 1. NO FAKE DATA (Absolute)

```
FORBIDDEN: Math.random(), mock data, simulated values
REQUIRED:  Real APIs only (yfinance, FRED, Alpha Vantage)
ON ERROR:  Return NULL/None, never generate fake fallback
```

Users make financial decisions based on this data. Integrity over availability.

### 2. PostgreSQL Only

```
ALLOWED:   PostgreSQL 13+ ONLY
FORBIDDEN: SQLite, MySQL, MongoDB
```

Database: `spartan_research_db`

### 3. Preserve index.html Structure

The `index.html` file (2,051 lines) contains the complete flashcard navigation system. **DO NOT modify** unless specifically requested.

### 4. Rate Limiting Required

When adding new data sources:
1. Add delay to `REQUEST_DELAYS` dict in `src/data_preloader.py`
2. Use `rate_limit(api_name)` before each API call
3. Test: `python src/data_preloader.py`

## Key Files

### Core
| File | Purpose |
|------|---------|
| `docker-compose.yml` | Orchestrates 9 services |
| `start_server.py` | Main HTTP server (port 8888) |
| `index.html` | Main dashboard (2,051 lines) |
| `src/data_preloader.py` | Initial data fetch (blocking) |
| `src/data_refresh_scheduler.py` | 15-min refresh loop |

### Frontend (Vanilla JS)
| File | Purpose |
|------|---------|
| `js/spartan-preloader.js` | IndexedDB cache |
| `js/composite_score_engine.js` | Multi-factor scoring |
| `js/fred_api_client.js` | FRED data client |
| `js/section_visibility_manager.js` | Flashcard navigation |

### Trading LLM
| File | Purpose |
|------|---------|
| `trading_llm_api.py` | AI signals API (port 9005) |
| `trading_llm_engine.py` | Analysis engine |
| `trading_llm.html` | Dashboard |

**Full docs**: `TRADING_LLM_INTEGRATION_COMPLETE.md`

## Environment Variables

**Required** (`.env`):
```bash
FRED_API_KEY=your_fred_key                # Economic data (required)
```

**Optional**:
```bash
ALPHA_VANTAGE_API_KEY=your_key
POLYGON_IO_API_KEY=your_key
ANTHROPIC_API_KEY=sk-ant-...              # For Claude AI
DATABASE_URL=postgresql://spartan:spartan@localhost/spartan_research_db
```

## Troubleshooting

### Preloader Fails

```bash
# Check logs
docker-compose logs spartan-data-preloader | grep ""

# Check exit code
docker inspect spartan-data-preloader --format='{{.State.ExitCode}}'
```

**Fixes**:
1. Add missing API keys to `.env`
2. Lower `SUCCESS_THRESHOLD` in `src/data_preloader.py`
3. Check network connectivity

### Data Not Showing

1. Verify Redis: `redis-cli GET market:index:SPY`
2. Check PostgreSQL: `psql -d spartan_research_db -c "SELECT COUNT(*) FROM preloaded_market_data;"`
3. Check browser console for JS errors

### Container Restart Loop

```bash
docker-compose logs -f <container-name>
curl http://localhost:8888/health
docker-compose build <container-name> && docker-compose up -d <container-name>
```

## Adding New Data Source

1. Edit `src/data_preloader.py`:
```python
async def preload_new_source(self):
    rate_limit('api_name')  # CRITICAL
    data = await fetch_from_real_api()  # NO FAKE DATA
    await self.redis_client.set(f'data:new_source', json.dumps(data), ex=self.cache_ttl)
    await self.save_to_db('new_source', data)
    return True
```

2. Add to `REQUEST_DELAYS`: `'api_name': 5.0`

3. Test: `python src/data_preloader.py`

## AI Features

### DeepSeek mHC Integration

Multi-path analysis (Technical, Fundamental, Macro, Sentiment) triggers automatically when analyzing trading symbols.

```bash
# Auto-triggers on natural language
"analyze SPY"
"should I buy Bitcoin?"

# Or explicit
/mhc-signal SPY
```

**Docs**: `MHC_QUICK_START.md`, `docs/DEEPSEEK_MHC_INTEGRATION.md`

### Alpha Projects

| Command | Purpose |
|---------|---------|
| `/polygraph [SYMBOL]` | Earnings call confidence |
| `/shockwave [EVENT]` | Supply chain effects |
| `/gitval [REPO]` | Code quality valuation |
| `/legal [COMPANY]` | Litigation impact |
| `/regime` | Macro regime detection |

**Docs**: `AI_TRADING_DNA.md`

## Related Documentation

| File | Purpose |
|------|---------|
| `AI_TRADING_DNA.md` | 5 High-Impact AI Trading Projects |
| `TRADING_LLM_INTEGRATION_COMPLETE.md` | Trading LLM full docs |
| `MHC_QUICK_START.md` | mHC 60-second guide |
| `README.md` | Project overview |

---

**Version**: 2.0.0 | **Status**: Production Ready
