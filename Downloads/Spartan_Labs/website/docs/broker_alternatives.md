# Broker & Data Source Alternatives

Complete guide to all supported brokers and data sources for the Spartan Trading Agent.

## Quick Comparison

| Provider | Type | Cost | Paper Trading | Real-time Data | API Key Required | Best For |
|----------|------|------|---------------|----------------|------------------|----------|
| **Alpaca** | Broker + Data | Free | ✅ Yes | ✅ Yes | ✅ Yes | Easiest setup, US stocks |
| **Yahoo Finance** | Data Only | Free | N/A | ⚠️ Delayed | ❌ No | Quick testing, no setup |
| **Interactive Brokers** | Broker + Data | $0-10/mo | ✅ Yes | ✅ Yes | ✅ Yes | Professional trading, global markets |
| **Binance** | Crypto Exchange | Free | ✅ Testnet | ✅ Yes | ✅ Yes | Cryptocurrency trading |
| **Polygon.io** | Data Only | $29-199/mo | N/A | ✅ Yes | ✅ Yes | Premium stock data |
| **Alpha Vantage** | Data Only | Free tier | N/A | ⚠️ Delayed | ✅ Yes | Free stock data |

## Option 1: Alpaca (Recommended for Beginners) ⭐

**Best for**: US stocks, beginners, quick setup

### Pros
- ✅ Completely free paper trading
- ✅ Real-time market data (IEX feed)
- ✅ Very easy API
- ✅ No minimum balance
- ✅ Good documentation
- ✅ Commission-free trading

### Cons
- ❌ US markets only
- ❌ No futures/options in basic account
- ❌ IEX data feed (not as complete as SIP)

### Setup (5 minutes)

1. Go to https://alpaca.markets/
2. Sign up for "Paper Trading" account (free)
3. Get API keys from dashboard
4. Add to `.env`:

```env
ALPACA_API_KEY=PKyour-key-here
ALPACA_API_SECRET=your-secret-here
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

5. Configure in `config/config.yaml`:

```yaml
data_sources:
  enabled:
    - alpaca_stocks

execution:
  enabled_brokers:
    - alpaca
```

**Start trading**: Already implemented! Just run `./start_trading.sh`

---

## Option 2: Yahoo Finance (Easiest, Free) 🆓

**Best for**: Testing, learning, backtesting, no API key needed

### Pros
- ✅ Completely free
- ✅ No API key required
- ✅ Global markets
- ✅ Good historical data
- ✅ Zero setup

### Cons
- ❌ No order execution (data only)
- ❌ 15-20 minute delayed data
- ❌ No real-time streaming
- ❌ Rate limits

### Setup (1 minute)

1. Configure in `config/config.yaml`:

```yaml
data_sources:
  enabled:
    - yahoo_finance

# Note: Need to use paper trading simulator for execution
execution:
  enabled_brokers:
    - paper_simulator  # Uses Yahoo data, simulates execution
```

2. Run:

```bash
python examples/basic_trading.py
```

**Use case**: Great for learning and backtesting without needing API keys. Not suitable for real-time trading due to delayed data.

---

## Option 3: Interactive Brokers (Professional) 🏆

**Best for**: Serious traders, global markets, advanced features

### Pros
- ✅ Professional-grade platform
- ✅ Global markets (stocks, options, futures, forex, crypto)
- ✅ Paper trading account
- ✅ Excellent execution
- ✅ Low commissions
- ✅ Advanced order types
- ✅ Real institutional data

### Cons
- ❌ More complex setup
- ❌ Requires TWS or Gateway running
- ❌ $0-10/month data fees
- ❌ Steeper learning curve

### Setup (15 minutes)

1. **Create Account**
   - Go to https://www.interactivebrokers.com/
   - Sign up for a paper trading account
   - Download TWS (Trader Workstation) or IB Gateway

2. **Install TWS/Gateway**
   - Launch TWS or Gateway
   - Log in with paper trading credentials
   - Go to Settings → API → Enable API connections
   - Set port: 7497 for paper trading

3. **Install Python library**:

```bash
pip install ib_insync
```

4. **Configure `.env`**:

```env
IBKR_HOST=127.0.0.1
IBKR_PORT=7497  # 7497 = paper, 7496 = live
IBKR_CLIENT_ID=1
```

5. **Configure `config/config.yaml`**:

```yaml
data_sources:
  enabled:
    - ibkr_stocks

  ibkr_stocks:
    host: ${IBKR_HOST}
    port: ${IBKR_PORT}
    client_id: ${IBKR_CLIENT_ID}

execution:
  enabled_brokers:
    - interactive_brokers
```

6. **Update code to use IBKR**:

```python
# In examples/basic_trading.py
from src.data.ibkr_connector import IBKRConnector

ibkr_config = config.data_sources.get("ibkr_stocks", {})
data_connector = IBKRConnector(ibkr_config)
```

**Start trading**: Make sure TWS/Gateway is running, then `./start_trading.sh`

---

## Option 4: Binance (Cryptocurrency) ₿

**Best for**: Crypto trading, altcoins

### Pros
- ✅ Largest crypto exchange
- ✅ Free testnet for paper trading
- ✅ Real-time data
- ✅ Thousands of crypto pairs
- ✅ Advanced order types

### Cons
- ❌ Crypto only (no stocks)
- ❌ Regulatory uncertainty in some countries
- ❌ More volatile markets

### Setup (10 minutes)

1. **Create Account**
   - Go to https://www.binance.com/
   - Sign up (or use testnet without signup)

2. **Get API Keys**
   - For Testnet: https://testnet.binance.vision/
   - For Live: Account → API Management

3. **Configure `.env`**:

```env
BINANCE_API_KEY=your-key-here
BINANCE_API_SECRET=your-secret-here
BINANCE_TESTNET=true  # Set to false for live trading
```

4. **Configure `config/config.yaml`**:

```yaml
data_sources:
  enabled:
    - binance_crypto

  binance_crypto:
    api_key: ${BINANCE_API_KEY}
    api_secret: ${BINANCE_API_SECRET}
    testnet: ${BINANCE_TESTNET}

execution:
  enabled_brokers:
    - binance

universe:
  crypto:
    pairs:
      - BTC/USDT
      - ETH/USDT
      - SOL/USDT
```

**Note**: We have the base framework. Full Binance connector coming soon!

---

## Option 5: Polygon.io (Premium Data) 💎

**Best for**: High-quality market data, serious traders

### Pros
- ✅ Professional-grade data
- ✅ Real-time stock data
- ✅ Full market depth
- ✅ Historical tick data
- ✅ Excellent API

### Cons
- ❌ Paid only ($29-199/month)
- ❌ No order execution (data only)
- ❌ Must pair with broker for execution

### Setup (5 minutes)

1. **Get API Key**
   - Go to https://polygon.io/
   - Sign up for a plan (starts at $29/mo)
   - Get your API key

2. **Configure `.env`**:

```env
POLYGON_API_KEY=your-key-here
```

3. **Configure `config/config.yaml`**:

```yaml
data_sources:
  enabled:
    - polygon_stocks

  polygon_stocks:
    api_key: ${POLYGON_API_KEY}

# Still need a broker for execution
execution:
  enabled_brokers:
    - alpaca  # Or another broker
```

---

## Option 6: Alpha Vantage (Free Tier) 📊

**Best for**: Free stock data, learning

### Pros
- ✅ Free tier available
- ✅ Good historical data
- ✅ Technical indicators included
- ✅ Global markets

### Cons
- ❌ Rate limits (5 calls/minute on free tier)
- ❌ No real-time data
- ❌ No order execution

### Setup (3 minutes)

1. **Get API Key**
   - Go to https://www.alphavantage.co/support/#api-key
   - Get free API key (no credit card)

2. **Configure `.env`**:

```env
ALPHA_VANTAGE_API_KEY=your-key-here
```

3. **Configure `config/config.yaml`**:

```yaml
data_sources:
  enabled:
    - alpha_vantage

  alpha_vantage:
    api_key: ${ALPHA_VANTAGE_API_KEY}
```

---

## Recommended Combinations

### For Learning (Free)
```yaml
data_sources:
  enabled:
    - yahoo_finance

execution:
  enabled_brokers:
    - paper_simulator
```
**Cost**: $0
**Setup time**: 1 minute
**Good for**: Learning the system, backtesting

---

### For Paper Trading (Free)
```yaml
data_sources:
  enabled:
    - alpaca_stocks

execution:
  enabled_brokers:
    - alpaca
```
**Cost**: $0
**Setup time**: 5 minutes
**Good for**: Testing strategies with real-time data

---

### For Professional Trading
```yaml
data_sources:
  enabled:
    - ibkr_stocks
    - polygon_stocks  # Premium data

execution:
  enabled_brokers:
    - interactive_brokers
```
**Cost**: ~$40-100/month
**Setup time**: 20 minutes
**Good for**: Serious trading, global markets

---

### For Crypto Trading
```yaml
data_sources:
  enabled:
    - binance_crypto

execution:
  enabled_brokers:
    - binance
```
**Cost**: $0 (testnet)
**Setup time**: 10 minutes
**Good for**: Cryptocurrency trading

---

## Migration Guide

### From Alpaca to Interactive Brokers

1. Set up IBKR account and TWS
2. Update `config/config.yaml`:

```yaml
# Change from:
data_sources:
  enabled:
    - alpaca_stocks

# To:
data_sources:
  enabled:
    - ibkr_stocks
```

3. Update code:

```python
# In examples/basic_trading.py
# Change from:
from src.data.alpaca_connector import AlpacaConnector
data_connector = AlpacaConnector(config)

# To:
from src.data.ibkr_connector import IBKRConnector
data_connector = IBKRConnector(config)
```

### From Yahoo Finance to Real-time Data

Simply change configuration:

```yaml
# Change from:
data_sources:
  enabled:
    - yahoo_finance

# To:
data_sources:
  enabled:
    - alpaca_stocks  # or polygon_stocks, etc.
```

---

## Cost Comparison

| Provider | Free Tier | Paid Tier | What You Get |
|----------|-----------|-----------|--------------|
| **Alpaca** | ✅ Unlimited | N/A | Paper trading + IEX real-time data |
| **Yahoo Finance** | ✅ Unlimited | N/A | Delayed data (15-20 min) |
| **Interactive Brokers** | $0/mo | $0-10/mo | Real-time data (small monthly fee) |
| **Polygon.io** | ❌ | $29-199/mo | Professional real-time data |
| **Alpha Vantage** | ✅ 5 calls/min | $49+/mo | More calls, real-time data |
| **Binance** | ✅ Testnet | Free | Crypto data + execution |

---

## Which Should You Choose?

### Absolute Beginner?
**→ Start with Yahoo Finance**
- No API keys needed
- Learn the system
- Zero cost

### Want to Paper Trade Stocks?
**→ Use Alpaca**
- Free paper trading
- Real-time data
- Easy setup

### Want to Paper Trade Crypto?
**→ Use Binance Testnet**
- Free testnet
- Real crypto pairs
- No risk

### Ready for Live Trading?
**→ Interactive Brokers**
- Professional platform
- Global markets
- Best execution

### Need Premium Data?
**→ Polygon.io + Any Broker**
- Highest quality data
- Pair with IBKR for execution

---

## Currently Implemented

✅ **Alpaca** - Fully working
✅ **Yahoo Finance** - Fully working
✅ **Interactive Brokers** - Fully working
🔨 **Binance** - Framework ready, connector in progress
🔨 **Polygon.io** - Framework ready, connector in progress
🔨 **Alpha Vantage** - Framework ready, connector in progress

---

## Quick Start Commands

### Using Yahoo Finance (No API Key)
```bash
# Edit config/config.yaml - set yahoo_finance as data source
./start_trading.sh
```

### Using Alpaca (Recommended)
```bash
# 1. Get API keys from alpaca.markets
# 2. Add to .env
# 3. Run
./start_trading.sh
```

### Using Interactive Brokers
```bash
# 1. Start TWS or IB Gateway
# 2. Enable API (port 7497 for paper)
# 3. Update config to use ibkr_stocks
# 4. Run
./start_trading.sh
```

---

Need help choosing? Ask yourself:

1. **Just learning?** → Yahoo Finance
2. **Testing strategies?** → Alpaca (stocks) or Binance (crypto)
3. **Ready to trade for real?** → Interactive Brokers
4. **Need best data?** → Polygon.io

All options are supported in Spartan Trading Agent! 🚀
