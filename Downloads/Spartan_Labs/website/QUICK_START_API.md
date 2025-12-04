# Quick Start: API Key Configuration

## TL;DR - Start in 30 Seconds

```bash
# System works immediately with ZERO API keys!
./START_SPARTAN.sh

# Wait 60 seconds for data preload
# Open http://localhost:8888
```

**Done!** Full dashboard with 30+ market data sources.

---

## What's Already Working

The system uses **yfinance** (Yahoo Finance) which requires **NO API keys**:

- US & Global Stock Indices
- Commodities (Gold, Oil, Copper)  
- Cryptocurrencies (Bitcoin, Ethereum)
- Forex pairs (EUR/USD, GBP/USD, etc.)
- Treasury bonds & yields
- All 9 market sectors
- VIX volatility index
- Correlation matrix

---

## Optional: Add Economic Data (2 Minutes)

For GDP, unemployment, and inflation data:

### Step 1: Get Free FRED API Key

Visit: https://fred.stlouisfed.org/docs/api/api_key.html

1. Click "Request API Key"
2. Fill form (name, email)
3. Check email for 32-character key

### Step 2: Configure Key

```bash
# Edit .env file
nano .env

# Find this line:
FRED_API_KEY=abcdefghijklmnopqrstuvwxyz123456

# Replace with your actual 32-character key
FRED_API_KEY=your_actual_key_here
```

### Step 3: Restart

```bash
./STOP_SPARTAN.sh
./START_SPARTAN.sh
```

**Done!** Now you have complete economic indicators.

---

## Validate Your Configuration

Check which keys are configured:

```bash
python3 scripts/validate_env.py
```

Output shows:
- Which keys are configured
- Which are missing (with instructions)
- System readiness status

---

## Documentation

- **API_KEY_SETUP_GUIDE.md** - Complete setup guide (50+ free data sources)
- **NO_API_KEY_START.md** - Zero-config quick start
- **API_SETUP_SUMMARY.md** - Configuration summary
- **.env** - Inline documentation for all keys

---

## System Design

**Primary Data Source**: yfinance (no auth required)
**Optional Enhancement**: FRED API (free, 2-minute setup)
**Additional Sources**: 50+ optional APIs (all free tiers)

**Key Principle**: System NEVER blocks startup due to missing API keys.

---

**Questions?**

Check the documentation files above or run the validation script.

The system is designed to work immediately, with optional enhancements.
