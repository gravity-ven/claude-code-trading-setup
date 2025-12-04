# Zero API Key Quick Start

## Start the System Right Now (No Setup Required!)

The Spartan Research Station works **immediately** with zero API keys.

```bash
# Clone and start (no API keys needed!)
cd /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website
./START_SPARTAN.sh

# Wait 60 seconds for data preload...
# Open browser: http://localhost:8888
```

**That's it!** You now have a fully functional financial intelligence dashboard.

---

## What You Get Without API Keys

### All Core Data Sources (Via yfinance - Free, No Auth)

- US Stock Indices: S&P 500, Nasdaq, Dow, Russell 2000
- Global Markets: Europe, Asia, Emerging Markets
- Commodities: Gold, Oil, Copper
- Cryptocurrencies: Bitcoin, Ethereum
- Forex: Major currency pairs (EUR/USD, GBP/USD, etc.)
- Fixed Income: Treasury bonds (short, medium, long-term)
- Sectors: All 9 major sectors (Tech, Finance, Energy, etc.)
- Volatility: VIX index
- Correlations: Asset correlation matrix

### Full Dashboard Features

- Real-time market data (15-minute delayed via yfinance)
- Historical charts (1 year of data)
- Correlation analysis
- Sector performance
- Global market overview
- Commodity tracking
- Volatility monitoring

### What's Missing Without FRED API Key

Only economic indicators require a (free) FRED API key:

- GDP growth
- Unemployment rate
- Inflation (CPI)
- Fed Funds Rate

**But you still get:**
- Treasury yields (via yfinance ETFs)
- Yield curve visualization
- Interest rate proxies

---

## Optional: 2-Minute FRED Setup

Want complete economic data? Get a free FRED API key:

1. Visit: https://fred.stlouisfed.org/docs/api/api_key.html
2. Click "Request API Key"
3. Enter name, email, agree to terms
4. Check email for 32-character key
5. Edit `.env` file and replace placeholder FRED_API_KEY
6. Restart: `./STOP_SPARTAN.sh && ./START_SPARTAN.sh`

**Done!** Now you have GDP, unemployment, inflation, and Fed Funds Rate.

---

## Summary

- Works immediately with NO API keys
- 30+ assets tracked using free yfinance API
- Optional FRED key for economic data (2 minutes)
- Production ready with auto-healing monitoring

**The Spartan Research Station: Zero-config financial intelligence.**
