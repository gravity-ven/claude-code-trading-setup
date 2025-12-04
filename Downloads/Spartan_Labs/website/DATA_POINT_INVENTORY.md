# 📊 COMPLETE DATA POINT INVENTORY - AUTONOMOUS AGENT MAPPING

**Date**: November 25, 2025
**Purpose**: Map every data point on website to dedicated autonomous agent
**Architecture**: Micro-agent swarm - one agent per data point

---

## 🎯 EXECUTIVE SUMMARY

**Total Data Points Identified**: 89
**Total Unique Data Sources**: 47
**Total Autonomous Agents Needed**: 47
**Update Frequency**: 1-15 minutes depending on data type

---

## 📋 COMPLETE DATA POINT LIST

### **SECTION 1: STEALTH MACRO REGIME DETECTOR**

#### **Agent 1: Dollar Index Agent (UUP)**
- **Data Point**: Dollar Index (UUP ETF)
- **Element IDs**: `stealth-dxy-value`, `stealth-dxy-arrow`, `stealth-dxy-signal`, `stealth-dxy-5d`
- **Data Source**: yfinance (UUP)
- **Required Fields**: price, change, changePercent, changePercent5d
- **Update Frequency**: 1 minute (market hours), 15 min (after hours)
- **Redis Key**: `market:symbol:UUP`
- **Agent File**: `agents/dollar_index_agent.py`

#### **Agent 2: Treasury Yield Agent (10Y)**
- **Data Point**: 10-Year Treasury Yield
- **Element IDs**: `stealth-yield-value`, `stealth-yield-arrow`, `stealth-yield-signal`, `stealth-yield-5d`
- **Data Source**: FRED API (DGS10) OR yfinance (^TNX)
- **Required Fields**: yield percentage, daily change, 5d change
- **Update Frequency**: 15 minutes
- **Redis Key**: `fundamental:economic:DGS10` OR `market:symbol:^TNX`
- **Agent File**: `agents/treasury_10y_agent.py`

#### **Agent 3: Gold Agent (GLD)**
- **Data Point**: Gold ETF Price
- **Element IDs**: `stealth-gold-value`, `stealth-gold-arrow`, `stealth-gold-signal`, `stealth-gold-5d`
- **Data Source**: yfinance (GLD)
- **Required Fields**: price, change, changePercent, changePercent5d
- **Update Frequency**: 1 minute (market hours), 15 min (after hours)
- **Redis Key**: `market:symbol:GLD`
- **Agent File**: `agents/gold_agent.py`

#### **Agent 4: Oil Agent (USO)**
- **Data Point**: Oil ETF Price
- **Element IDs**: `stealth-oil-value`, `stealth-oil-arrow`, `stealth-oil-signal`, `stealth-oil-5d`
- **Data Source**: yfinance (USO)
- **Required Fields**: price, change, changePercent, changePercent5d
- **Update Frequency**: 1 minute (market hours), 15 min (after hours)
- **Redis Key**: `market:symbol:USO`
- **Agent File**: `agents/oil_agent.py`

#### **Agent 5: SPY Agent (Equities)**
- **Data Point**: S&P 500 ETF Price
- **Element IDs**: `stealth-spy-value`, `stealth-spy-arrow`, `stealth-spy-signal`, `stealth-spy-5d`
- **Data Source**: yfinance (SPY)
- **Required Fields**: price, change, changePercent, changePercent5d
- **Update Frequency**: 1 minute (market hours), 15 min (after hours)
- **Redis Key**: `market:symbol:SPY`
- **Agent File**: `agents/spy_agent.py`

#### **Agent 6: VIX Agent (Volatility)**
- **Data Point**: VIX Volatility Index
- **Element IDs**: `stealth-vix-value`, `stealth-vix-arrow`, `stealth-vix-signal`, `stealth-vix-5d`
- **Data Source**: FRED API (VIXCLS) OR yfinance (^VIX)
- **Required Fields**: index value, daily change, 5d change
- **Update Frequency**: 1 minute (market hours), 15 min (after hours)
- **Redis Key**: `fundamental:economic:VIXCLS` OR `market:symbol:^VIX`
- **Agent File**: `agents/vix_agent.py`

---

### **SECTION 2: VIX COMPOSITE INDICATOR**

#### **Agent 7: Bitcoin Agent (BTC-USD)**
- **Data Point**: Bitcoin Price & Volatility
- **Element IDs**: `crypto-vol-score`, `btc-volatility`
- **Data Source**: yfinance (BTC-USD) OR CoinGecko
- **Required Fields**: price, changePercent5d (for volatility)
- **Update Frequency**: 1 minute (24/7)
- **Redis Key**: `market:symbol:BTC-USD`
- **Agent File**: `agents/bitcoin_agent.py`

#### **Agent 8: Ethereum Agent (ETH-USD)**
- **Data Point**: Ethereum Price & Volatility
- **Element IDs**: `crypto-vol-score`, `eth-volatility`
- **Data Source**: yfinance (ETH-USD) OR CoinGecko
- **Required Fields**: price, changePercent5d
- **Update Frequency**: 1 minute (24/7)
- **Redis Key**: `market:symbol:ETH-USD`
- **Agent File**: `agents/ethereum_agent.py`

---

### **SECTION 3: BEST COMPOSITE INDICATOR**

#### **Agent 9: AUD/JPY Agent (Forex)**
- **Data Point**: Australian Dollar / Japanese Yen
- **Element IDs**: `audjpy-value`, `audjpy-arrow`
- **Data Source**: yfinance (AUDJPY=X) OR Twelve Data
- **Required Fields**: rate, changePercent5d
- **Update Frequency**: 1 minute (forex hours)
- **Redis Key**: `fundamental:forex:AUDJPY` OR `market:symbol:AUDJPY=X`
- **Agent File**: `agents/audjpy_agent.py`

#### **Agent 10: HYG Agent (High Yield Bonds)**
- **Data Point**: High Yield Corporate Bonds ETF
- **Element IDs**: `hyg-value`, `hyg-arrow`
- **Data Source**: yfinance (HYG)
- **Required Fields**: price, changePercent5d
- **Update Frequency**: 1 minute (market hours)
- **Redis Key**: `market:symbol:HYG`
- **Agent File**: `agents/hyg_agent.py`

---

### **SECTION 4: CRYPTO BEST COMPOSITE**

#### **Agent 11: Solana Agent (SOL-USD)**
- **Data Point**: Solana Price
- **Element IDs**: `crypto-sol-arrow`
- **Data Source**: yfinance (SOL-USD) OR CoinGecko
- **Required Fields**: price, changePercent5d
- **Update Frequency**: 1 minute (24/7)
- **Redis Key**: `market:symbol:SOL-USD`
- **Agent File**: `agents/solana_agent.py`

---

### **SECTION 5: RECESSION MODEL**

#### **Agent 12: 3-Month Treasury Agent (DTB3)**
- **Data Point**: 3-Month Treasury Bill Yield
- **Element IDs**: Used in `recession-spread` calculation
- **Data Source**: FRED API (DTB3)
- **Required Fields**: yield percentage
- **Update Frequency**: 15 minutes
- **Redis Key**: `fundamental:economic:DTB3`
- **Agent File**: `agents/treasury_3m_agent.py`

#### **Agent 13: Recession Calculator Agent**
- **Data Point**: Recession Probability (calculated)
- **Element IDs**: `recession-probability`, `recession-risk-level`, `recession-risk-emoji`, `recession-spread`
- **Data Source**: Calculated from DGS10 - DTB3
- **Required Fields**: spread, probability, risk_level
- **Update Frequency**: 15 minutes (after yield updates)
- **Redis Key**: `calculated:recession_probability`
- **Agent File**: `agents/recession_calculator_agent.py`

---

### **SECTION 6: DOMINANT NARRATIVE**

#### **Agent 14: Market Narrative Agent**
- **Data Point**: Market Regime & Narrative (calculated)
- **Element IDs**: `dominant-narrative`
- **Data Source**: Calculated from SPY, VIX, UUP, GLD
- **Required Fields**: narrative text, regime classification
- **Update Frequency**: 5 minutes
- **Redis Key**: `calculated:market_narrative`
- **Agent File**: `agents/market_narrative_agent.py`

---

### **SECTION 7: ADDITIONAL ECONOMIC INDICATORS** (If used on page)

#### **Agent 15-47: Individual FRED Indicators**

| Agent # | Indicator | Symbol | FRED Series | Redis Key | Update Freq |
|---------|-----------|--------|-------------|-----------|-------------|
| 15 | GDP | GDP | GDP | `fundamental:economic:GDP` | Daily |
| 16 | Unemployment | UNRATE | UNRATE | `fundamental:economic:UNRATE` | Monthly |
| 17 | CPI | CPIAUCSL | CPIAUCSL | `fundamental:economic:CPIAUCSL` | Monthly |
| 18 | Core CPI | CPILFESL | CPILFESL | `fundamental:economic:CPILFESL` | Monthly |
| 19 | PCE | PCEPI | PCEPI | `fundamental:economic:PCEPI` | Monthly |
| 20 | Fed Funds | FEDFUNDS | FEDFUNDS | `fundamental:economic:FEDFUNDS` | Daily |
| 21 | 2Y Treasury | DGS2 | DGS2 | `fundamental:economic:DGS2` | Daily |
| 22 | 5Y Treasury | DGS5 | DGS5 | `fundamental:economic:DGS5` | Daily |
| 23 | 30Y Treasury | DGS30 | DGS30 | `fundamental:economic:DGS30` | Daily |
| 24 | M1 Money | M1SL | M1SL | `fundamental:economic:M1SL` | Weekly |
| 25 | M2 Money | M2SL | M2SL | `fundamental:economic:M2SL` | Weekly |
| 26 | Fed Balance | WALCL | WALCL | `fundamental:economic:WALCL` | Weekly |
| 27 | Consumer Sentiment | UMCSENT | UMCSENT | `fundamental:economic:UMCSENT` | Monthly |
| 28 | Housing Starts | HOUST | HOUST | `fundamental:economic:HOUST` | Monthly |
| 29 | Mortgage Rate | MORTGAGE30US | MORTGAGE30US | `fundamental:economic:MORTGAGE30US` | Weekly |
| 30 | Industrial Production | INDPRO | INDPRO | `fundamental:economic:INDPRO` | Monthly |
| 31 | ISM Manufacturing | NAPM | NAPM | `fundamental:economic:NAPM` | Monthly |
| 32 | Trade Balance | BOPGSTB | BOPGSTB | `fundamental:economic:BOPGSTB` | Monthly |
| 33 | Corp Spread BBB | BAA10Y | BAA10Y | `fundamental:economic:BAA10Y` | Daily |
| 34 | High Yield Spread | BAMLH0A0HYM2 | BAMLH0A0HYM2 | `fundamental:economic:BAMLH0A0HYM2` | Daily |

#### **Agent 35-40: Forex Pairs**

| Agent # | Pair | Symbol | Source | Redis Key | Update Freq |
|---------|------|--------|--------|-----------|-------------|
| 35 | EUR/USD | EURUSD=X | yfinance/Twelve Data | `fundamental:forex:EURUSD` | 1 min |
| 36 | GBP/USD | GBPUSD=X | yfinance/Twelve Data | `fundamental:forex:GBPUSD` | 1 min |
| 37 | USD/JPY | USDJPY=X | yfinance/Twelve Data | `fundamental:forex:USDJPY` | 1 min |
| 38 | USD/CAD | USDCAD=X | yfinance/Twelve Data | `fundamental:forex:USDCAD` | 1 min |
| 39 | USD/CHF | USDCHF=X | yfinance/Twelve Data | `fundamental:forex:USDCHF` | 1 min |
| 40 | AUD/USD | AUDUSD=X | yfinance/Twelve Data | `fundamental:forex:AUDUSD` | 1 min |

#### **Agent 41-47: Major Stock Fundamentals** (If used)

| Agent # | Stock | Symbol | Source | Data | Update Freq |
|---------|-------|--------|--------|------|-------------|
| 41 | Apple | AAPL | Finnhub | P/E, EPS, Market Cap | Daily |
| 42 | Microsoft | MSFT | Finnhub | P/E, EPS, Market Cap | Daily |
| 43 | Google | GOOGL | Finnhub | P/E, EPS, Market Cap | Daily |
| 44 | Amazon | AMZN | Finnhub | P/E, EPS, Market Cap | Daily |
| 45 | Tesla | TSLA | Finnhub | P/E, EPS, Market Cap | Daily |
| 46 | Meta | META | Finnhub | P/E, EPS, Market Cap | Daily |
| 47 | NVIDIA | NVDA | Finnhub | P/E, EPS, Market Cap | Daily |

---

## 🏗️ AUTONOMOUS AGENT ARCHITECTURE

### **Agent Design Principles**

1. **One Agent = One Data Point** (or closely related set)
2. **Self-Contained**: Each agent knows its source, schedule, and storage
3. **Fault Tolerant**: Agent failure doesn't affect others
4. **Observable**: Each agent logs its status
5. **Controllable**: Can start/stop/restart individually

### **Agent Base Class**

```python
class AutonomousDataAgent:
    def __init__(self, name, symbol, source, update_interval):
        self.name = name
        self.symbol = symbol
        self.source = source
        self.update_interval = update_interval
        self.redis_key = None
        self.running = False

    async def fetch_data(self):
        """Override in subclass - fetches from specific source"""
        pass

    async def store_data(self, data):
        """Stores to Redis + PostgreSQL"""
        pass

    async def run(self):
        """Main loop - fetch and store on interval"""
        pass

    def stop(self):
        """Graceful shutdown"""
        pass
```

### **Agent Communication**

- **Storage**: Redis (primary), PostgreSQL (backup)
- **Coordination**: None required (independent agents)
- **Status**: Each agent writes to `agent:status:{name}`
- **Health**: Orchestrator monitors `last_update` timestamp

---

## 📊 AGENT DEPLOYMENT MATRIX

### **Priority Tier 1: Critical for Page Display** (14 agents)

| Priority | Agent | Why Critical | Deploy Order |
|----------|-------|--------------|--------------|
| 1 | SPY Agent | Used in multiple sections | 1 |
| 2 | VIX Agent | Used in multiple sections | 2 |
| 3 | Dollar (UUP) Agent | Stealth Macro, Narrative | 3 |
| 4 | 10Y Yield Agent | Stealth Macro, Recession | 4 |
| 5 | 3M Yield Agent | Recession Model | 5 |
| 6 | Gold Agent | Stealth Macro, Narrative | 6 |
| 7 | Oil Agent | Stealth Macro | 7 |
| 8 | Bitcoin Agent | VIX Composite, Crypto Composite | 8 |
| 9 | Ethereum Agent | VIX Composite, Crypto Composite | 9 |
| 10 | Solana Agent | Crypto Composite | 10 |
| 11 | AUD/JPY Agent | Best Composite | 11 |
| 12 | HYG Agent | Best Composite | 12 |
| 13 | Recession Calculator | Recession Model | 13 |
| 14 | Market Narrative | Dominant Narrative | 14 |

### **Priority Tier 2: Enhanced Data** (26 agents)

- 20 FRED Economic Indicators (GDP, Unemployment, CPI, etc.)
- 6 Forex Pairs

### **Priority Tier 3: Premium Features** (7 agents)

- 7 Stock Fundamentals (AAPL, MSFT, etc.)

---

## 🚀 DEPLOYMENT STRATEGY

### **Phase 1: Launch Critical Agents** (Priority Tier 1)

```bash
# Launch orchestrator
python agent_orchestrator.py --tier 1

# Verify all 14 critical agents running
python agent_orchestrator.py --status

# Check Redis for data
redis-cli KEYS 'market:symbol:*' | wc -l  # Should show 14+
```

### **Phase 2: Launch Enhanced Data** (Priority Tier 2)

```bash
# Launch FRED indicators
python agent_orchestrator.py --tier 2

# Verify 40 agents total
python agent_orchestrator.py --status | grep "Running" | wc -l
```

### **Phase 3: Launch Premium Features** (Priority Tier 3)

```bash
# Launch stock fundamentals
python agent_orchestrator.py --tier 3

# Verify all 47 agents
python agent_orchestrator.py --status --all
```

---

## 📈 MONITORING & HEALTH CHECKS

### **Agent Health Metrics**

Each agent reports:
- **Last Update Time**: Timestamp of last successful data fetch
- **Success Rate**: % of successful fetches in last hour
- **Error Count**: Number of failures since start
- **Data Freshness**: Age of current cached data

### **Orchestrator Dashboard**

```bash
# View real-time agent status
python agent_orchestrator.py --dashboard

Output:
┌─────────────────────────────────────────────────────────┐
│ AUTONOMOUS AGENT SWARM - DASHBOARD                      │
├─────────────────────────────────────────────────────────┤
│ Total Agents: 47                                        │
│ Running: 47        Stopped: 0        Failed: 0         │
│                                                         │
│ TIER 1 (Critical): 14/14 ✅                            │
│   SPY Agent          ✅ 5s ago   Success: 100%         │
│   VIX Agent          ✅ 3s ago   Success: 100%         │
│   Dollar Agent       ✅ 8s ago   Success: 100%         │
│   ...                                                   │
│                                                         │
│ TIER 2 (Enhanced): 26/26 ✅                            │
│ TIER 3 (Premium): 7/7 ✅                               │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 BENEFITS OF MICRO-AGENT ARCHITECTURE

1. **Fault Isolation**: One agent failure doesn't crash system
2. **Scalability**: Add new data points = add new agent
3. **Resource Optimization**: Each agent uses minimal resources
4. **Update Flexibility**: Different update frequencies per agent
5. **Easy Debugging**: Clear logs per data point
6. **Independent Deployment**: Deploy/update agents individually
7. **Load Distribution**: Spread API calls across time
8. **Resilience**: Automatic retry and fallback per agent

---

## 📝 IMPLEMENTATION FILES

**Core Framework**:
1. `autonomous_agent_base.py` - Base class for all agents
2. `agent_orchestrator.py` - Launcher and monitor
3. `agent_config.yaml` - Agent definitions and schedules

**Tier 1 Agents** (agents/tier1/):
1. `spy_agent.py` - S&P 500 ETF
2. `vix_agent.py` - Volatility Index
3. `dollar_agent.py` - Dollar Index
4. `treasury_10y_agent.py` - 10-Year Yield
5. `treasury_3m_agent.py` - 3-Month Yield
6. `gold_agent.py` - Gold ETF
7. `oil_agent.py` - Oil ETF
8. `bitcoin_agent.py` - Bitcoin
9. `ethereum_agent.py` - Ethereum
10. `solana_agent.py` - Solana
11. `audjpy_agent.py` - AUD/JPY Forex
12. `hyg_agent.py` - High Yield Bonds
13. `recession_calculator_agent.py` - Recession Model
14. `market_narrative_agent.py` - Narrative Generator

**Tier 2 Agents** (agents/tier2/):
- 20 FRED indicator agents
- 6 Forex pair agents

**Tier 3 Agents** (agents/tier3/):
- 7 Stock fundamental agents

---

## 🔄 NEXT STEPS

1. ✅ **Create Data Point Inventory** (THIS FILE)
2. ⏭️ **Implement Base Agent Class**
3. ⏭️ **Implement Tier 1 Critical Agents** (14 agents)
4. ⏭️ **Create Agent Orchestrator**
5. ⏭️ **Deploy & Test Tier 1**
6. ⏭️ **Implement Tier 2 & 3 Agents**
7. ⏭️ **Full System Test**

---

**Document Version**: 1.0
**Total Agents**: 47
**Status**: Ready for implementation
**Next**: Create autonomous_agent_base.py
