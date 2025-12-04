# Data Preloader Agent

## Overview

The Data Preloader is a critical component that **blocks website startup** until all required market data is successfully fetched and validated. This ensures users never see empty dashboards or fake data.

## Architecture

### Docker Dependency Gate

```yaml
# docker-compose.yml
services:
  spartan-data-preloader:
    build:
      context: .
      dockerfile: Dockerfile.preloader
    command: python3 src/data_preloader.py
    depends_on:
      - postgres
      - redis
    restart: "no"  # Run once

  spartan-web:
    build: .
    depends_on:
      spartan-data-preloader:
        condition: service_completed_successfully  # ← CRITICAL GATE
    ports:
      - "8888:8888"
```

**How It Works**:
1. `spartan-data-preloader` runs `src/data_preloader.py`
2. If exit code = 0 (success) → `spartan-web` starts
3. If exit code = 1 (failure) → `spartan-web` BLOCKED, entire stack fails

## Validation Rules

### Success Criteria (ALL must pass)

1. **Overall Success Rate**: ≥80% of all data sources successful
2. **Critical Sources**: 100% success required for:
   - US Indices (SPY, QQQ, DIA, IWM)
   - FRED Economic Data (GDP, UNRATE, CPIAUCSL)
   - VIX (Volatility Index)
3. **No Fake Data**: Zero Math.random() or mock values allowed
4. **Data Freshness**: All data <15 minutes old (within cache TTL)

### Failure Scenarios

**Preloader FAILS if**:
- Success rate <80%
- Any critical source fails
- Fake data detected
- Redis connection failure
- PostgreSQL connection failure
- All data sources timeout (>60s total runtime)

## Data Sources (13+ Categories)

### 1. US Indices (Critical)
```python
US_INDICES = {
    'SPY': 'S&P 500 ETF',
    'QQQ': 'Nasdaq 100 ETF',
    'DIA': 'Dow Jones ETF',
    'IWM': 'Russell 2000 ETF'
}
```
**API**: yfinance
**Critical**: Yes
**Fallback**: None (must succeed)

### 2. Global Indices
```python
GLOBAL_INDICES = {
    'EFA': 'MSCI EAFE (Europe, Asia)',
    'EEM': 'Emerging Markets',
    'FXI': 'China Large-Cap',
    'EWJ': 'Japan',
    'EWG': 'Germany',
    'EWU': 'United Kingdom'
}
```
**API**: yfinance
**Critical**: No
**Fallback**: Use cached data if available

### 3. Commodities
```python
COMMODITIES = {
    'GLD': 'Gold ETF',
    'USO': 'Oil ETF',
    'CPER': 'Copper ETF'
}
```
**API**: yfinance
**Critical**: No
**Fallback**: Use previous day's data

### 4. Crypto
```python
CRYPTO = {
    'BTC-USD': 'Bitcoin',
    'ETH-USD': 'Ethereum'
}
```
**API**: yfinance (15-min delay)
**Critical**: No
**Fallback**: Alpha Vantage API if yfinance fails

### 5. Forex
```python
FOREX = {
    'EURUSD=X': 'EUR/USD',
    'GBPUSD=X': 'GBP/USD',
    'USDJPY=X': 'USD/JPY',
    'AUDUSD=X': 'AUD/USD'
}
```
**API**: yfinance
**Critical**: No
**Fallback**: Alpha Vantage API

### 6. Treasuries
```python
TREASURIES = {
    'SHY': '1-3 Year Treasury ETF',
    'IEF': '7-10 Year Treasury ETF',
    'TLT': '20+ Year Treasury ETF'
}
```
**API**: yfinance
**Critical**: No
**Fallback**: Use cached data

### 7. Global Bonds
```python
GLOBAL_BONDS = {
    'BNDX': 'International Bond ETF',
    'EMB': 'Emerging Market Bond ETF'
}
```
**API**: yfinance
**Critical**: No
**Fallback**: Use cached data

### 8. FRED Economic Data (Critical)
```python
FRED_SERIES = {
    'GDP': 'Gross Domestic Product',
    'UNRATE': 'Unemployment Rate',
    'CPIAUCSL': 'Consumer Price Index',
    'FEDFUNDS': 'Federal Funds Rate',
    'T10Y2Y': 'Treasury Yield Spread (10Y-2Y)'
}
```
**API**: FRED API (requires API key)
**Critical**: Yes
**Fallback**: None (must succeed)

### 9. Volatility (Critical)
```python
VOLATILITY = {
    '^VIX': 'CBOE Volatility Index'
}
```
**API**: yfinance
**Critical**: Yes
**Fallback**: None (must succeed)

### 10. Sectors
```python
SECTORS = {
    'XLF': 'Financials',
    'XLK': 'Technology',
    'XLE': 'Energy',
    'XLV': 'Healthcare',
    'XLI': 'Industrials',
    'XLP': 'Consumer Staples',
    'XLY': 'Consumer Discretionary',
    'XLU': 'Utilities',
    'XLRE': 'Real Estate'
}
```
**API**: yfinance
**Critical**: No
**Fallback**: Use cached data

### 11. Correlation Matrix
```python
CORRELATION_SYMBOLS = ['SPY', 'QQQ', 'GLD', 'TLT', 'USO', 'BTC-USD']
```
**Calculation**: Pandas correlation matrix on 90-day returns
**Critical**: No
**Fallback**: Skip if any symbol fails

## Implementation

### Main Class: `DataPreloader`

**File**: `src/data_preloader.py`

```python
class DataPreloader:
    """Pre-fetches and validates all data sources before website starts."""

    def __init__(self):
        self.redis_client = None
        self.db_conn = None
        self.session = None

        # API Keys
        self.fred_api_key = os.getenv('FRED_API_KEY')
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.polygon_key = os.getenv('POLYGON_IO_API_KEY')

        # Cache TTL
        self.cache_ttl = 900  # 15 minutes

        # Validation tracking
        self.results = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'critical_failed': []
        }

    async def preload_all(self) -> bool:
        """Preload all data sources. Returns True if validation passes."""
        await self.connect()

        # Preload each category
        await self.preload_us_indices()
        await self.preload_global_indices()
        await self.preload_commodities()
        await self.preload_crypto()
        await self.preload_forex()
        await self.preload_treasuries()
        await self.preload_global_bonds()
        await self.preload_fred_data()
        await self.preload_volatility()
        await self.preload_sectors()
        await self.preload_correlations()

        # Validate results
        return self.validate_results()

    def validate_results(self) -> bool:
        """Check if validation rules pass."""
        success_rate = self.results['success'] / self.results['total']

        # Rule 1: Overall success rate ≥80%
        if success_rate < 0.80:
            logger.error(f"Success rate too low: {success_rate:.2%}")
            return False

        # Rule 2: No critical failures
        if self.results['critical_failed']:
            logger.error(f"Critical sources failed: {self.results['critical_failed']}")
            return False

        # Rule 3: No fake data (checked during fetch)

        logger.info(f"Validation passed: {success_rate:.2%} success rate")
        return True

    async def fetch_yfinance(self, symbol: str, critical: bool = False) -> dict:
        """Fetch data from yfinance with validation."""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1d', interval='1m')

            if data.empty:
                raise ValueError(f"No data returned for {symbol}")

            # Validate no fake data
            if self._contains_fake_data(data):
                raise ValueError(f"Fake data detected for {symbol}")

            # Cache to Redis
            cache_key = f"yfinance:{symbol}"
            await self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(data.to_dict())
            )

            # Store to PostgreSQL
            await self.store_to_postgres(symbol, data)

            self.results['success'] += 1
            self.results['total'] += 1
            return data.to_dict()

        except Exception as e:
            logger.error(f"Failed to fetch {symbol}: {e}")
            self.results['failed'] += 1
            self.results['total'] += 1

            if critical:
                self.results['critical_failed'].append(symbol)

            return None

    def _contains_fake_data(self, data: pd.DataFrame) -> bool:
        """Check if data contains fake/mock values."""
        # Check for repeated values (sign of Math.random())
        if data['Close'].nunique() < len(data) * 0.8:
            return True

        # Check for unrealistic values
        if (data['Close'] <= 0).any():
            return True

        # Check for missing timestamps
        if data.index.to_series().diff().max() > pd.Timedelta('5min'):
            return True

        return False
```

### Async Execution

The preloader uses `asyncio` for concurrent data fetching:

```python
async def preload_us_indices(self):
    """Preload US indices concurrently."""
    tasks = [
        self.fetch_yfinance(symbol, critical=True)
        for symbol in US_INDICES.keys()
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

## Cache Strategy

### Redis Cache (Primary)

**TTL**: 15 minutes (900 seconds)
**Format**: JSON strings
**Keys**: `{source}:{symbol}` (e.g., `yfinance:SPY`)

**Benefits**:
- Ultra-fast retrieval (<1ms)
- Automatic expiration
- Shared across all services

**Example**:
```python
# Cache data
cache_key = f"yfinance:{symbol}"
await redis_client.setex(
    cache_key,
    900,  # 15-min TTL
    json.dumps(data)
)

# Retrieve data
cached = await redis_client.get(cache_key)
if cached:
    data = json.loads(cached)
```

### PostgreSQL Backup (Secondary)

**Purpose**: Long-term storage and fallback if Redis down

**Schema**:
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

CREATE INDEX idx_market_data_symbol ON market_data(symbol);
CREATE INDEX idx_market_data_timestamp ON market_data(timestamp);
```

## Configuration

### Environment Variables

```bash
# Required
FRED_API_KEY=your_fred_api_key_here

# Optional (fallbacks)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
POLYGON_IO_API_KEY=your_polygon_key

# Infrastructure
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://user:pass@localhost/spartan_research_db

# Preloader settings
PRELOAD_TIMEOUT=60  # Max seconds for entire preload
PRELOAD_RETRY_ATTEMPTS=3
PRELOAD_MIN_SUCCESS_RATE=0.80
```

### Configuration File

**File**: `config/preloader_config.yaml`

```yaml
preloader:
  timeout_seconds: 60
  retry_attempts: 3
  min_success_rate: 0.80
  cache_ttl: 900  # 15 minutes

  critical_sources:
    - SPY
    - QQQ
    - DIA
    - IWM
    - ^VIX
    - FRED:GDP
    - FRED:UNRATE
    - FRED:CPIAUCSL

  fallback_enabled: true
  fallback_sources:
    yfinance: [alpha_vantage, polygon]
    fred: [bea_api]  # Bureau of Economic Analysis
```

## Running the Preloader

### Docker (Production)

```bash
# Run via docker-compose
docker-compose up spartan-data-preloader

# Check exit code
echo $?  # 0 = success, 1 = failure

# View logs
docker-compose logs spartan-data-preloader
```

### Standalone (Development)

```bash
# Run directly
python3 src/data_preloader.py

# With verbose logging
python3 src/data_preloader.py --verbose

# Dry run (no cache writes)
python3 src/data_preloader.py --dry-run

# Skip critical validation (testing only)
python3 src/data_preloader.py --skip-critical
```

## Monitoring

### Health Check

```bash
# During preload (Redis keys)
redis-cli KEYS "yfinance:*"

# After preload (PostgreSQL)
psql spartan_research_db -c "SELECT source, COUNT(*) as symbols, MAX(timestamp) as latest FROM market_data GROUP BY source;"
```

### Performance Metrics

```bash
# View preload statistics
curl http://localhost:8888/api/preloader/stats

# Example response
{
  "last_run": "2025-11-20T10:30:00Z",
  "duration_seconds": 45.2,
  "total_sources": 50,
  "successful": 48,
  "failed": 2,
  "success_rate": 0.96,
  "critical_failures": [],
  "cache_hit_rate": 0.85
}
```

## Troubleshooting

### Preloader Fails to Start Website

```bash
# Check preloader logs
docker-compose logs spartan-data-preloader

# Common issues:
# 1. FRED API key missing
grep FRED_API_KEY .env

# 2. Redis connection failure
redis-cli PING

# 3. PostgreSQL connection failure
psql spartan_research_db -c "SELECT 1;"

# 4. Network issues (check yfinance)
curl -I https://query1.finance.yahoo.com/v8/finance/chart/SPY
```

### Low Success Rate

```bash
# Identify failed sources
docker-compose logs spartan-data-preloader | grep "Failed to fetch"

# Check API rate limits
# yfinance: 2000 requests/hour
# FRED: 120 requests/minute
# Alpha Vantage: 5 requests/minute (free tier)

# Increase timeout
export PRELOAD_TIMEOUT=120
docker-compose up spartan-data-preloader
```

### Critical Source Failures

```bash
# Test individual critical sources
python3 -c "import yfinance as yf; print(yf.Ticker('SPY').history(period='1d'))"
python3 -c "import yfinance as yf; print(yf.Ticker('^VIX').history(period='1d'))"

# Test FRED API
curl "https://api.stlouisfed.org/fred/series/observations?series_id=GDP&api_key=${FRED_API_KEY}&file_type=json"
```

## Related Documentation

- `init/agents/website_monitor.md` - Monitoring and auto-healing
- `init/agents/alert_watcher.md` - Alert system
- `DEPLOYMENT_GUIDE.md` - Full deployment process
- `API_INTEGRATION_GUIDE.md` - API integration details
