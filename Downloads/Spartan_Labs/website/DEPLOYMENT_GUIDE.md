# Spartan Research Station - Deployment Guide

**Enterprise-Grade Market Intelligence Platform**
**Database-First Architecture with 50+ Data Sources**

---

## Table of Contents

1. [Quick Start (5 Minutes)](#quick-start-5-minutes)
2. [System Requirements](#system-requirements)
3. [Installation Steps](#installation-steps)
4. [Configuration](#configuration)
5. [Starting the System](#starting-the-system)
6. [Verification](#verification)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)
9. [Production Deployment](#production-deployment)
10. [API Documentation](#api-documentation)

---

## Quick Start (5 Minutes)

**Get Spartan Research Station running in 5 minutes:**

```bash
# 1. Clone repository
git clone https://github.com/yourusername/spartan-labs.git
cd spartan-labs/website

# 2. Copy environment configuration
cp .env.spartan.example .env

# 3. Add your API keys to .env
nano .env  # Edit and add FRED_API_KEY (minimum requirement)

# 4. Start the system
bash START_SPARTAN_RESEARCH_STATION.sh

# 5. Access dashboard
# Browser will auto-open at http://localhost:8888
```

**That's it!** The system will:
- Start PostgreSQL + Redis
- Download data from 30+ sources (2-5 minutes)
- Start web server with instant data
- Begin 1-hour background refresh cycle

---

## System Requirements

### Minimum Requirements

- **OS**: Linux (Ubuntu 20.04+), macOS 11+, Windows 10+ with WSL2
- **Docker**: 20.10+ with Docker Compose
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 10GB free space (database + logs)
- **CPU**: 2 cores minimum, 4+ cores recommended
- **Network**: Stable internet connection (for data downloads)

### Recommended Requirements

- **RAM**: 16GB (for optimal database performance)
- **Disk**: 50GB SSD (TimescaleDB compression + 7 days of logs)
- **CPU**: 8 cores (parallel data fetching)
- **Network**: 100 Mbps+ (faster data downloads)

### Docker Configuration

Ensure Docker has sufficient resources:

```bash
# Check Docker resources
docker info | grep -E "CPUs|Total Memory"

# Recommended Docker settings:
# CPUs: 4+
# Memory: 8GB+
# Swap: 2GB+
# Disk: 50GB+
```

---

## Installation Steps

### 1. Install Docker & Docker Compose

**Ubuntu/Debian:**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker compose version
```

**macOS:**
```bash
# Install Docker Desktop
brew install --cask docker

# Start Docker Desktop app
open -a Docker

# Verify installation
docker --version
docker compose version
```

**Windows (WSL2):**
```powershell
# Install Docker Desktop for Windows
# Download from: https://www.docker.com/products/docker-desktop

# Enable WSL2 backend in Docker Desktop settings

# In WSL2 terminal:
docker --version
docker compose version
```

### 2. Clone Repository

```bash
git clone https://github.com/yourusername/spartan-labs.git
cd spartan-labs/website
```

### 3. Configure Environment

```bash
# Copy example configuration
cp .env.spartan.example .env

# Edit configuration
nano .env  # Or use your preferred editor
```

**Required API Keys** (Minimum to start):

1. **FRED API Key** (ESSENTIAL - Free)
   - Sign up: https://fred.stlouisfed.org/docs/api/api_key.html
   - Limit: 120 requests/minute (very generous)
   - Provides: 816,000+ economic time series

2. **At least one stock data source**:
   - **Option A**: Use Yahoo Finance (FREE, no key required) ✅ RECOMMENDED
   - **Option B**: Alpha Vantage (FREE, 25 req/day)
   - **Option C**: Polygon.io (PAID, unlimited)

**Optional API Keys** (Enhance data coverage):

- Twelve Data (FREE: 800 req/day)
- Finnhub (FREE: 60 req/min)
- IEX Cloud (FREE tier available)
- Tiingo (FREE: 50 req/hour)
- CoinGecko (FREE: 50 req/min, no key)
- NewsAPI (FREE: 100 req/day)
- EIA Energy (FREE, unlimited)

See `.env.spartan.example` for complete list of 50+ sources.

---

## Configuration

### Environment Variables (.env)

**Database Configuration:**
```bash
# PostgreSQL (automatically configured in Docker)
POSTGRES_DB=spartan_research
POSTGRES_USER=spartan_user
POSTGRES_PASSWORD=spartan_pass_2025_CHANGE_THIS  # ⚠️ CHANGE IN PRODUCTION

# Database connection string
DATABASE_URL=postgresql://spartan_user:spartan_pass_2025_CHANGE_THIS@postgres:5432/spartan_research

# Redis cache
REDIS_URL=redis://redis:6379/0
```

**Pre-Loader Configuration:**
```bash
MAX_WORKERS=10                # Parallel download workers (adjust for CPU cores)
TIMEOUT_PER_SOURCE=30         # Timeout per source (seconds)
SUCCESS_THRESHOLD=90          # Minimum success rate to start web (%)
```

**Web Server Configuration:**
```bash
FLASK_ENV=production
FLASK_DEBUG=0                 # Set to 1 for development
SECRET_KEY=generate_with_openssl_rand_hex_32  # ⚠️ CHANGE IN PRODUCTION

MAX_DB_CONNECTIONS=50         # PostgreSQL connection pool size
CACHE_TIMEOUT=300             # Redis cache timeout (5 minutes)
LOG_LEVEL=INFO                # DEBUG, INFO, WARNING, ERROR

CORS_ORIGINS=*                # Comma-separated origins, or * for all
RATE_LIMIT=100/minute         # API rate limit
```

**Background Refresh Configuration:**
```bash
REFRESH_INTERVAL=3600         # 1 hour in seconds (as requested)
```

**Monitoring Configuration:**
```bash
GRAFANA_USER=admin
GRAFANA_PASSWORD=spartan2025_CHANGE_THIS  # ⚠️ CHANGE IN PRODUCTION
```

**API Keys:**
```bash
# PRIMARY SOURCE (Paid)
POLYGON_IO_API_KEY=your_polygon_api_key_here

# ESSENTIAL (Free)
FRED_API_KEY=your_fred_api_key_here  # ⚠️ REQUIRED

# FREE SOURCES (Optional but recommended)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
TWELVE_DATA_API_KEY=your_twelve_data_key_here
FINNHUB_API_KEY=your_finnhub_key_here
# ... (see .env.spartan.example for complete list)
```

### Data Sources Configuration (config/data_sources.yaml)

Already pre-configured with 50+ data sources. No changes needed unless you want to:

- **Enable/disable specific sources**: Set `enabled: false`
- **Adjust priorities**: Change `priority` values (lower = higher priority)
- **Modify symbols**: Edit `symbols` lists for each source
- **Change refresh interval**: Edit `refresh_config.interval_seconds`

---

## Starting the System

### One-Command Startup (Recommended)

```bash
bash START_SPARTAN_RESEARCH_STATION.sh
```

This script will:

1. ✅ Perform pre-flight checks (Docker, Docker Compose, .env file)
2. ✅ Start infrastructure layer (PostgreSQL, Redis)
3. ✅ Wait for databases to be ready
4. ✅ Start pre-loader service (downloads all data)
5. ✅ Monitor pre-loader progress (shows real-time %)
6. ✅ Start web server (instant data from database)
7. ✅ Start background refresh (1-hour cycle)
8. ✅ Start monitoring stack (Prometheus, Grafana)
9. ✅ Open browser to http://localhost:8888

**Expected Timeline:**

- Infrastructure startup: 30-60 seconds
- Pre-loader download: 2-5 minutes (30+ sources)
- Web server ready: 10 seconds
- **Total**: ~3-6 minutes to fully operational

### Manual Startup (Advanced)

```bash
# Start infrastructure
docker-compose -f docker-compose.spartan.yml up -d postgres redis

# Wait for PostgreSQL
docker exec spartan_postgres pg_isready -U spartan_user

# Start pre-loader (one-time data download)
docker-compose -f docker-compose.spartan.yml up -d preloader

# Monitor pre-loader logs
docker logs -f spartan_preloader

# Wait for pre-loader to complete
docker wait spartan_preloader

# Start web server
docker-compose -f docker-compose.spartan.yml up -d web

# Start background refresh
docker-compose -f docker-compose.spartan.yml up -d refresh

# Start monitoring (optional)
docker-compose -f docker-compose.spartan.yml up -d prometheus grafana
```

### Stopping the System

```bash
# Stop all services
docker-compose -f docker-compose.spartan.yml down

# Stop and remove volumes (⚠️ deletes database)
docker-compose -f docker-compose.spartan.yml down -v
```

### Restarting Services

```bash
# Restart specific service
docker-compose -f docker-compose.spartan.yml restart web

# Restart all services
docker-compose -f docker-compose.spartan.yml restart
```

---

## Verification

### Health Checks

**1. System Health:**
```bash
curl http://localhost:8888/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-19T10:30:00",
  "database": "connected",
  "redis": "connected",
  "refresh_status": {
    "in_progress": "false",
    "success_rate": "95.00",
    "total_rows_updated": "12500"
  }
}
```

**2. System Status:**
```bash
curl http://localhost:8888/api/system/status
```

Shows:
- Data source health (success/failure counts)
- Refresh status (last refresh, next refresh)
- Database statistics (row counts per table)

**3. Database Connection:**
```bash
docker exec -it spartan_postgres psql -U spartan_user -d spartan_research -c "SELECT COUNT(*) FROM market_data.indices;"
```

**4. Redis Cache:**
```bash
docker exec -it spartan_redis redis-cli PING
docker exec -it spartan_redis redis-cli HGETALL refresh:status
```

### Test API Endpoints

```bash
# Market indices
curl http://localhost:8888/api/market/indices

# Commodities
curl http://localhost:8888/api/market/commodities

# Forex
curl http://localhost:8888/api/market/forex

# Crypto
curl http://localhost:8888/api/market/crypto

# Economic indicators (FRED)
curl "http://localhost:8888/api/economic/fred?series_ids=GDP,UNRATE,CPIAUCSL"

# Correlations
curl http://localhost:8888/api/analytics/correlations

# Symbol search
curl "http://localhost:8888/api/db/search?query=AAPL&limit=10"
```

### Check Logs

```bash
# All services
docker-compose -f docker-compose.spartan.yml logs -f

# Specific service
docker logs -f spartan_web
docker logs -f spartan_preloader
docker logs -f spartan_refresh

# PostgreSQL logs
docker logs -f spartan_postgres

# Last 100 lines
docker logs --tail 100 spartan_web
```

---

## Monitoring

### Grafana Dashboards

Access Grafana at: http://localhost:3000

**Default credentials:**
- Username: `admin`
- Password: `spartan2025_CHANGE_THIS` (from .env)

**Pre-configured dashboards:**
- System Health (data source uptime, response times)
- Database Performance (query times, connection pool)
- Refresh Status (success rates, data freshness)
- API Performance (endpoint response times, error rates)

### Prometheus Metrics

Access Prometheus at: http://localhost:9090

**Available metrics:**
- `spartan_data_source_success_total` - Total successful fetches per source
- `spartan_data_source_failure_total` - Total failed fetches per source
- `spartan_refresh_duration_seconds` - Refresh cycle duration
- `spartan_api_request_duration_seconds` - API endpoint response times
- `spartan_db_connections_active` - Active database connections

### Command-Line Monitoring

```bash
# Watch refresh status
watch -n 5 'docker exec spartan_redis redis-cli HGETALL refresh:status'

# Monitor database size
docker exec spartan_postgres psql -U spartan_user -d spartan_research -c "
  SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
  FROM pg_tables
  WHERE schemaname IN ('market_data', 'economic_data', 'analytics')
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"

# Monitor container resources
docker stats
```

---

## Troubleshooting

### Pre-Loader Fails to Complete

**Symptom**: Pre-loader container exits with non-zero code

**Solutions**:

1. **Check pre-loader logs:**
   ```bash
   docker logs spartan_preloader
   ```

2. **Verify API keys in .env:**
   ```bash
   cat .env | grep API_KEY
   ```

3. **Check network connectivity:**
   ```bash
   docker exec spartan_preloader ping -c 3 api.stlouisfed.org
   ```

4. **Lower success threshold temporarily:**
   Edit `.env`:
   ```bash
   SUCCESS_THRESHOLD=70  # Lower from 90 to 70
   ```

5. **Retry pre-loader:**
   ```bash
   docker-compose -f docker-compose.spartan.yml up preloader
   ```

### Web Server Won't Start

**Symptom**: Web server container keeps restarting

**Solutions**:

1. **Check web server logs:**
   ```bash
   docker logs spartan_web
   ```

2. **Verify database connection:**
   ```bash
   docker exec spartan_postgres pg_isready -U spartan_user
   ```

3. **Check if pre-loader completed:**
   ```bash
   docker exec spartan_redis redis-cli GET preload:complete
   # Should return "true"
   ```

4. **Test database connection from web container:**
   ```bash
   docker exec spartan_web python3 -c "
   import psycopg2
   conn = psycopg2.connect('postgresql://spartan_user:spartan_pass_2025@postgres:5432/spartan_research')
   print('Database connection: OK')
   "
   ```

### No Data in API Responses

**Symptom**: API endpoints return empty arrays

**Solutions**:

1. **Check if pre-loader ran:**
   ```bash
   docker logs spartan_preloader | grep successful
   ```

2. **Verify data in database:**
   ```bash
   docker exec spartan_postgres psql -U spartan_user -d spartan_research -c "
     SELECT COUNT(*) FROM market_data.indices;
   "
   ```

3. **Check refresh service:**
   ```bash
   docker logs spartan_refresh
   ```

4. **Manually trigger refresh:**
   ```bash
   docker restart spartan_refresh
   ```

### High Memory Usage

**Symptom**: Docker containers consuming excessive RAM

**Solutions**:

1. **Reduce PostgreSQL shared_buffers:**
   Edit `docker-compose.spartan.yml`:
   ```yaml
   command: postgres -c shared_buffers=1GB  # Down from 2GB
   ```

2. **Reduce MAX_WORKERS:**
   Edit `.env`:
   ```bash
   MAX_WORKERS=5  # Down from 10
   ```

3. **Enable TimescaleDB compression:**
   ```bash
   docker exec spartan_postgres psql -U spartan_user -d spartan_research -c "
     SELECT compress_chunk(i) FROM show_chunks('market_data.indices') i;
   "
   ```

### API Rate Limit Errors

**Symptom**: Pre-loader or refresh fails with rate limit errors

**Solutions**:

1. **Disable rate-limited sources temporarily:**
   Edit `config/data_sources.yaml`:
   ```yaml
   - id: alpha_vantage_stocks
     enabled: false  # Disable if hitting limits
   ```

2. **Increase stagger delay:**
   Edit `config/data_sources.yaml`:
   ```yaml
   refresh_config:
     stagger_delay_ms: 500  # Up from 100ms
   ```

3. **Use fallback sources:**
   System automatically falls back to next priority source

---

## Production Deployment

### Security Hardening

**1. Change all default passwords:**
```bash
# In .env
POSTGRES_PASSWORD=<strong_random_password>
GRAFANA_PASSWORD=<strong_random_password>
SECRET_KEY=<generated_with_openssl_rand_hex_32>
```

Generate strong passwords:
```bash
openssl rand -hex 32
```

**2. Restrict CORS origins:**
```bash
# In .env
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

**3. Enable HTTPS:**
- Configure `nginx` service in `docker-compose.spartan.yml`
- Add SSL certificates to `config/ssl/`
- Update nginx configuration to use HTTPS

**4. Enable firewall:**
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 5432/tcp  # Block external PostgreSQL access
sudo ufw deny 6379/tcp  # Block external Redis access
sudo ufw enable
```

**5. Set up regular backups:**
```bash
# Automated PostgreSQL backups
docker exec spartan_postgres pg_dump -U spartan_user spartan_research | gzip > backup_$(date +%Y%m%d).sql.gz

# Add to cron
0 2 * * * /path/to/backup_script.sh  # Daily at 2 AM
```

### Scaling for Production

**1. PostgreSQL performance tuning:**
```yaml
# In docker-compose.spartan.yml
command: |
  postgres
  -c shared_buffers=4GB
  -c effective_cache_size=12GB
  -c work_mem=128MB
  -c maintenance_work_mem=1GB
  -c max_connections=200
```

**2. Redis persistence:**
```yaml
# In docker-compose.spartan.yml
command: redis-server --appendonly yes --maxmemory-policy allkeys-lru
```

**3. Load balancing:**
- Run multiple `web` containers
- Use nginx as reverse proxy/load balancer
- Distribute API requests across instances

**4. Database replication:**
- Set up PostgreSQL primary-replica replication
- Read-heavy queries → replicas
- Write queries → primary

---

## API Documentation

### Market Data Endpoints

**GET /api/market/indices**
- Returns: Latest major market indices (S&P 500, NASDAQ, Dow, etc.)
- Cache: 5 minutes
- Source: PostgreSQL `market_data.indices`

**GET /api/market/commodities**
- Returns: Latest commodity prices (Gold, Oil, Copper, etc.)
- Cache: 5 minutes
- Source: PostgreSQL `market_data.commodities`

**GET /api/market/forex**
- Returns: Latest forex rates
- Cache: 5 minutes
- Source: PostgreSQL `market_data.forex_rates`

**GET /api/market/crypto**
- Returns: Latest crypto prices
- Cache: 5 minutes
- Source: PostgreSQL `market_data.crypto_prices`

**GET /api/market/volatility**
- Returns: Volatility indicators (VIX, VVIX, SKEW, MOVE)
- Cache: 5 minutes
- Source: PostgreSQL `market_data.volatility_indicators`

### Economic Data Endpoints

**GET /api/economic/fred?series_ids=GDP,UNRATE**
- Parameters: `series_ids` (comma-separated FRED series IDs)
- Returns: Latest values for requested FRED series
- Cache: 5 minutes
- Source: PostgreSQL `economic_data.fred_series`

**GET /api/economic/indicators**
- Returns: All economic indicators
- Cache: 5 minutes
- Source: PostgreSQL `economic_data.indicators`

### Analytics Endpoints

**GET /api/analytics/correlations**
- Returns: Asset correlations (60-day, 30-day, 7-day)
- Cache: 5 minutes
- Source: PostgreSQL `analytics.correlations`

**GET /api/analytics/sector_rotation**
- Returns: Sector rotation analysis
- Cache: 5 minutes
- Source: PostgreSQL `analytics.sector_rotation`

**GET /api/analytics/sentiment**
- Returns: Market sentiment indicators
- Cache: 5 minutes
- Source: PostgreSQL `analytics.sentiment_indicators`

### System Endpoints

**GET /health**
- Returns: System health status
- Cache: None
- Use: Health checks, monitoring

**GET /api/system/status**
- Returns: Detailed system status (data sources, refresh, database stats)
- Cache: 10 seconds
- Use: Monitoring dashboards

**GET /api/db/search?query=AAPL&limit=10**
- Parameters: `query` (search term), `limit` (max results)
- Returns: Symbol search results
- Cache: 5 minutes
- Source: PostgreSQL (all market_data tables)

**GET /api/db/stats**
- Returns: Database statistics (total symbols)
- Cache: 5 minutes
- Source: PostgreSQL metadata

---

## Support & Maintenance

### Log Rotation

Logs are automatically rotated by Docker. To configure:

```yaml
# In docker-compose.spartan.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Database Maintenance

**Weekly vacuum:**
```bash
docker exec spartan_postgres psql -U spartan_user -d spartan_research -c "VACUUM ANALYZE;"
```

**Monthly compression (TimescaleDB):**
```bash
docker exec spartan_postgres psql -U spartan_user -d spartan_research -c "
  SELECT compress_chunk(i, if_not_compressed => true)
  FROM show_chunks('market_data.indices', older_than => INTERVAL '7 days') i;
"
```

### Upgrade Procedure

```bash
# 1. Backup database
docker exec spartan_postgres pg_dump -U spartan_user spartan_research > backup.sql

# 2. Pull latest code
git pull origin main

# 3. Rebuild containers
docker-compose -f docker-compose.spartan.yml build

# 4. Restart services
docker-compose -f docker-compose.spartan.yml up -d

# 5. Verify health
curl http://localhost:8888/health
```

---

## Contact & Support

- **Issues**: https://github.com/yourusername/spartan-labs/issues
- **Documentation**: https://github.com/yourusername/spartan-labs/wiki
- **Email**: support@spartanresearch.io

---

**Last Updated**: November 19, 2025
**Version**: 2.0
**Status**: Production Ready
