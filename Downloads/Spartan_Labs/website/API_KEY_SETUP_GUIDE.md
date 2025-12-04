# API Key Setup Guide

## Quick Start (TL;DR)

**The system works immediately with ZERO API keys!**

All core data comes from yfinance (Yahoo Finance), which requires no authentication. Optional API keys enhance the system but are not required for startup.

```bash
# Start the system right now (no keys needed!)
./START_SPARTAN.sh

# System will fetch data from 13+ sources using yfinance
```

---

## What Works Without Any API Keys?

The Spartan Research Station is designed to work out-of-the-box using **yfinance** as the primary data source:

### ✅ Available Data (No Keys Required)

| Category | Data Source | Symbols |
|----------|-------------|---------|
| **US Indices** | yfinance | SPY, QQQ, DIA, IWM |
| **Global Indices** | yfinance | EFA, EEM, FXI, EWJ, EWG, EWU |
| **Commodities** | yfinance | GLD (Gold), USO (Oil), CPER (Copper) |
| **Crypto** | yfinance | BTC-USD, ETH-USD |
| **Forex** | yfinance | EUR/USD, GBP/USD, USD/JPY, AUD/USD |
| **Treasuries** | yfinance | SHY, IEF, TLT |
| **Global Bonds** | yfinance | BNDX, EMB |
| **Sectors** | yfinance | XLF, XLK, XLE, XLV, XLI, XLP, XLY, XLU, XLRE |
| **Volatility** | yfinance | ^VIX |
| **Correlations** | Calculated | Matrix of above assets |

### ⚠️ Limited Without FRED Key

| Data Type | Availability |
|-----------|--------------|
| GDP | Not available (FRED required) |
| Unemployment Rate | Not available (FRED required) |
| CPI/Inflation | Not available (FRED required) |
| Fed Funds Rate | Not available (FRED required) |
| Yield Curve Spread | Partial (treasury ETFs as proxy) |

---

## Recommended: FRED API Key (2-Minute Setup)

For complete economic data, get a **free FRED API key**:

### Why FRED?

- **Free**: No cost, no credit card required
- **Fast**: Takes only 2 minutes to set up
- **Essential**: Provides GDP, unemployment, inflation, interest rates
- **Reliable**: 120 requests/minute (more than sufficient)

### How to Get FRED API Key

**Step 1:** Visit [https://fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html)

**Step 2:** Click **"Request API Key"**

**Step 3:** Fill out the form:
- Name
- Email address
- Agree to terms

**Step 4:** Check your email - key arrives instantly

**Step 5:** Copy the 32-character key

**Step 6:** Add to `.env` file:

```bash
# Edit .env file
nano .env

# Replace this line:
FRED_API_KEY=abcdefghijklmnopqrstuvwxyz123456

# With your actual key:
FRED_API_KEY=your_actual_32_character_key_here
```

**Step 7:** Restart the system:

```bash
./STOP_SPARTAN.sh
./START_SPARTAN.sh
```

**Done!** You now have full economic data.

---

## Optional: Additional Data Sources

All optional - enhance the system but not required for core functionality.

### Stock Market Data (FREE)

| Service | Requests/Day | Provides | Get Key |
|---------|--------------|----------|---------|
| **Polygon.io** | 5/min | Real-time market data | [polygon.io](https://polygon.io/) |
| **Alpha Vantage** | 25/day | Stock/Forex/Crypto | [alphavantage.co](https://www.alphavantage.co/support/#api-key) |
| **Finnhub** | 60/min | Market data & news | [finnhub.io](https://finnhub.io/) |
| **Twelve Data** | 8/min | Stock market data | [twelvedata.com](https://twelvedata.com/) |
| **IEX Cloud** | Free tier | US stock data | [iexcloud.io](https://iexcloud.io/) |
| **Tiingo** | 50/hour | End-of-day prices | [tiingo.com](https://api.tiingo.com/) |
| **Financial Modeling Prep** | 250/day | Financials & data | [financialmodelingprep.com](https://financialmodelingprep.com/) |

### Economic Data (FREE)

| Service | Requests/Day | Provides | Get Key |
|---------|--------------|----------|---------|
| **Quandl** | Free tier | Financial/economic | [quandl.com](https://www.quandl.com/) |
| **BLS** | 500/day | Employment/inflation | [bls.gov](https://www.bls.gov/developers/) |

### Forex Data (FREE)

| Service | Requests/Month | Provides | Get Key |
|---------|----------------|----------|---------|
| **ExchangeRate-API** | 1,500 | Currency rates | [exchangerate-api.com](https://www.exchangerate-api.com/) |
| **Fixer.io** | 100 | Forex rates | [fixer.io](https://fixer.io/) |

### Crypto Data (FREE - Most NO KEY NEEDED!)

| Service | Key Required? | Provides |
|---------|---------------|----------|
| **CoinGecko** | ❌ No | 50 req/min, free |
| **CoinCap** | ❌ No | 200 req/min, free |
| **Blockchain.com** | ❌ No | Free data |
| **CryptoCompare** | ✅ Yes | 100k req/month | [cryptocompare.com](https://min-api.cryptocompare.com/) |

### News Data (FREE)

| Service | Requests/Day | Get Key |
|---------|--------------|---------|
| **NewsAPI** | 100 | [newsapi.org](https://newsapi.org/) |
| **GNews** | 100 | [gnews.io](https://gnews.io/) |

### Commodity Data (FREE)

| Service | Provides | Get Key |
|---------|----------|---------|
| **EIA** | Energy data | [eia.gov](https://www.eia.gov/opendata/register.php) |
| **USDA** | Agricultural | [usda.gov](https://www.usda.gov/) |

---

## Validating Your Configuration

Run the validation script to check your API keys:

```bash
# Check which keys are configured
python3 scripts/validate_env.py
```

**Sample Output:**

```
🔍 SPARTAN LABS - API KEY VALIDATION REPORT
================================================================================

🔴 CRITICAL: ECONOMIC DATA
--------------------------------------------------------------------------------
✅ FRED_API_KEY: Valid FRED API key configured

🟡 RECOMMENDED: ENHANCED DATA SOURCES
--------------------------------------------------------------------------------
Configured: 1/2

✅ POLYGON_IO_API_KEY: Configured
⭕ ALPHA_VANTAGE_API_KEY: Missing

🟢 OPTIONAL: ADDITIONAL DATA SOURCES
--------------------------------------------------------------------------------
Configured: 0/8

================================================================================
📋 SUMMARY & RECOMMENDATIONS
================================================================================

✅ System Status: READY TO START

   The Spartan Research Station uses yfinance as its PRIMARY data source.
   yfinance requires NO API keys and provides:
   • US & Global Stock Indices
   • Commodities (Gold, Oil, Copper)
   • Cryptocurrencies
   • Forex pairs
   • Treasury yields
   • Sector ETFs
   • Volatility (VIX)

   FRED API configured - Full economic data available

   To start the system: ./START_SPARTAN.sh
```

---

## Configuration Priority Levels

### 🔴 Critical (Recommended, but has fallbacks)

- **FRED_API_KEY**: Free economic data (GDP, unemployment, inflation)
  - **Without it**: System uses treasury ETFs as proxy for economic conditions
  - **With it**: Full economic dashboard with all indicators

### 🟡 Recommended (Enhances data quality)

- **POLYGON_IO_API_KEY**: Real-time market data, fills gaps in yfinance
- **ALPHA_VANTAGE_API_KEY**: Additional stock/forex/crypto data

### 🟢 Optional (Nice to have)

- All other keys provide supplementary data sources
- Useful for redundancy and additional features
- Not required for core dashboard functionality

---

## Startup Behavior

### Data Preloader Validation

The system validates data availability before starting:

1. **Pre-fetch data from all sources** (yfinance + configured APIs)
2. **Calculate success rate** across all sources
3. **Validate critical sources**:
   - US Indices (SPY, QQQ, DIA, IWM) - **CRITICAL**
   - VIX - **CRITICAL**
   - Economic data (FRED or fallback) - **CRITICAL**

### Success Criteria

System starts if:
- **80%+ of data sources succeed** (default threshold)
- **No critical source failures**

### What Happens on Failure?

If data preloader fails validation:

```bash
❌ DATA PRELOAD FAILED - DO NOT START WEBSITE
   Total Sources: 13
   Successful: 9
   Failed: 4
   Success Rate: 69.2%

   Failed Sources: FRED_Economic, Global_Indices, ...
   Critical Failures: FRED_Economic

   RECOMMENDATION: Check API keys or lower SUCCESS_THRESHOLD
```

**Options:**
1. **Add FRED API key** (recommended)
2. **Lower threshold** in `.env`:
   ```bash
   SUCCESS_THRESHOLD=70  # Accept 70% success rate
   ```
3. **Check network connection** (firewall blocking API calls?)

---

## Troubleshooting

### Problem: System won't start

**Check data preloader logs:**

```bash
docker-compose logs spartan-data-preloader
```

**Look for:**
- Network errors (firewall blocking?)
- Invalid API keys (check format)
- Rate limit errors (too many requests?)

### Problem: Missing economic data

**Symptom:** Dashboard shows "No data" for GDP, unemployment, inflation

**Solution:** Add FRED API key to `.env`

### Problem: Slow data loading

**Symptom:** Dashboard takes >60 seconds to load data

**Causes:**
- Too many API sources configured (rate limits)
- Network latency
- yfinance throttling

**Solutions:**
1. Disable slow/unnecessary APIs in `.env`
2. Increase cache TTL (Redis TTL: 900 seconds default)
3. Use local data preloader cache

### Problem: API rate limits exceeded

**Symptom:** Logs show "429 Too Many Requests"

**Solutions:**
1. Reduce data refresh frequency (default: 15 minutes)
2. Use fewer optional API sources
3. Upgrade to paid API tiers (if needed)

---

## Environment Variables Reference

### System Configuration (Pre-configured)

```bash
# Database (auto-configured by Docker)
DATABASE_URL=postgresql://spartan:spartan@spartan-postgres:5432/spartan_research_db
REDIS_URL=redis://spartan-redis:6379/0

# API Server
API_HOST=0.0.0.0
API_PORT=8888

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/spartan.log

# Data Preloader
MAX_WORKERS=1              # Parallel fetch workers
SUCCESS_THRESHOLD=80       # Min % of sources that must succeed
```

### Trading Configuration (Optional)

```bash
TRADING_MODE=paper_trading  # paper_trading | live_trading | backtest

# Alpaca (stock trading)
ALPACA_API_KEY=your_key
ALPACA_API_SECRET=your_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Binance (crypto trading)
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
BINANCE_TESTNET=true
```

---

## Best Practices

### For Personal Use (Recommended)

1. **Start with zero keys** - Verify system works with yfinance
2. **Add FRED key** - Get complete economic data (2 minutes)
3. **Optionally add Polygon.io** - Enhanced real-time data
4. **Stop there** - More keys = complexity without major benefit

### For Production Deployment

1. **Configure FRED** - Essential for economic data
2. **Add redundancy** - Alpha Vantage, Polygon.io as backups
3. **Monitor rate limits** - Track API usage
4. **Set up alerts** - Notify on data source failures
5. **Use paid tiers** - For higher rate limits if needed

### Security

1. **Never commit .env to git** - Already in `.gitignore`
2. **Rotate keys periodically** - Especially if exposed
3. **Use environment-specific keys** - Different keys for dev/prod
4. **Restrict key permissions** - Use read-only keys where possible

---

## Summary

### ✅ System Works Without API Keys

The Spartan Research Station is designed to work immediately using free, no-auth data sources (yfinance).

### ⚡ Quick Win: Add FRED Key

For complete economic data, spend 2 minutes getting a free FRED API key.

### 🎯 Optional Enhancements

Additional API keys provide redundancy and enhanced features, but are not required for core functionality.

### 🚀 Start Now

```bash
# No keys? No problem!
./START_SPARTAN.sh

# System fetches data from 13+ sources using yfinance
# Dashboard available at http://localhost:8888
```

---

**Need Help?**

- Check `.env` for inline documentation
- Run `python3 scripts/validate_env.py` for key validation
- View logs: `docker-compose logs -f spartan-data-preloader`
- See `DATA_PRELOADER_GUIDE.md` for detailed preloader docs

---

**Last Updated:** November 20, 2025
