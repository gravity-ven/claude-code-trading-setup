# Spartan Trading Agent System - Architecture

## Vision
A billion-dollar trading agent powered by Claude AI - modular, scalable, and production-ready.

## Core Philosophy
- **Modular**: Every component is pluggable and replaceable
- **AI-First**: Claude at the center of decision-making
- **Production-Ready**: Built for real money, real scale
- **Observable**: Full visibility into every decision and action

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     SPARTAN TRADING AGENT                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    CLAUDE AI CORE ENGINE                     │
│  ┌────────────┐  ┌────────────┐  ┌─────────────────────┐   │
│  │  Market    │  │  Strategy  │  │   Risk Assessment   │   │
│  │  Analysis  │  │  Generation│  │   & Portfolio Mgmt  │   │
│  └────────────┘  └────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                       │
│              (Strategy Selection & Execution Control)        │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────┴───────────────────┐
        ↓                                       ↓
┌──────────────────┐                  ┌──────────────────┐
│  DATA INGESTION  │                  │ EXECUTION ENGINE │
│                  │                  │                  │
│  • Stock APIs    │                  │  • Alpaca        │
│  • Crypto APIs   │                  │  • IBKR          │
│  • News Feeds    │                  │  • Binance       │
│  • Alt Data      │                  │  • Paper Trading │
└──────────────────┘                  └──────────────────┘
        ↓                                       ↓
┌─────────────────────────────────────────────────────────────┐
│                    PERSISTENCE LAYER                         │
│  • Time-series DB (market data)                             │
│  • PostgreSQL (trades, positions, logs)                     │
│  • Redis (real-time cache)                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              MONITORING & ALERTING SYSTEM                    │
│  • Performance Dashboard                                     │
│  • Real-time Alerts                                         │
│  • Risk Monitoring                                          │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Claude AI Core Engine
**Purpose**: The brain of the system - makes all trading decisions

**Capabilities**:
- Market regime detection
- Sentiment analysis from news/social media
- Pattern recognition in price data
- Strategy generation and optimization
- Risk assessment for every trade
- Portfolio rebalancing decisions
- Anomaly detection

**Modules**:
- `core/claude_engine.py` - Main Claude API integration
- `core/prompts/` - Specialized prompts for different tasks
- `core/memory.py` - Context management for Claude conversations
- `core/reasoning.py` - Multi-step reasoning framework

### 2. Data Ingestion Framework
**Purpose**: Modular connectors for all data sources

**Supported Sources** (pluggable):
- **Stock Data**: Alpaca, Polygon.io, Alpha Vantage, Yahoo Finance
- **Crypto Data**: Binance, Coinbase, CoinGecko
- **News**: NewsAPI, Alpha Vantage News, Twitter/X
- **Alternative Data**: Reddit sentiment, GitHub activity, etc.

**Architecture**:
- Abstract base class `DataConnector`
- Each source is a plugin
- Unified data format across sources
- Real-time streaming + historical batch loading

### 3. Execution Engine
**Purpose**: Execute trades across multiple brokers/exchanges

**Supported Brokers** (pluggable):
- **Stocks**: Alpaca, Interactive Brokers, TD Ameritrade
- **Crypto**: Binance, Coinbase, Kraken
- **Paper Trading**: Simulated execution for testing

**Features**:
- Smart order routing
- Slippage optimization
- Partial fill handling
- Order retry logic
- Position tracking

### 4. Risk Management System
**Purpose**: Prevent catastrophic losses

**Features**:
- Per-trade risk limits
- Portfolio-level risk limits
- Position sizing algorithms
- Stop-loss automation
- Drawdown protection
- Margin monitoring

### 5. Backtesting Framework
**Purpose**: Test strategies on historical data

**Features**:
- Vectorized backtesting for speed
- Event-driven backtesting for accuracy
- Multiple timeframe support
- Realistic slippage/commission modeling
- Walk-forward optimization

### 6. Monitoring & Alerting
**Purpose**: Full system observability

**Features**:
- Real-time P&L tracking
- Trade journal with AI reasoning
- Performance metrics dashboard
- Alert system (email, SMS, Slack)
- Error tracking and recovery

## Data Flow

1. **Market Data** → Data connectors fetch real-time/historical data
2. **Processing** → Clean, normalize, and store in time-series DB
3. **Analysis** → Claude analyzes market conditions and opportunities
4. **Strategy** → Claude generates trading signals with reasoning
5. **Risk Check** → Risk system validates trade against limits
6. **Execution** → Order sent to broker via execution engine
7. **Monitoring** → Track fill, update positions, log to database
8. **Learning** → System learns from outcomes for future decisions

## Technology Stack

### Core
- **Language**: Python 3.11+
- **AI**: Anthropic Claude API (Sonnet 4.5)
- **Async**: asyncio for concurrent operations

### Data & Storage
- **Time-Series**: TimescaleDB or InfluxDB
- **Relational**: PostgreSQL
- **Cache**: Redis
- **Data Processing**: pandas, numpy, polars

### APIs & Integration
- **Web Framework**: FastAPI (for dashboard/API)
- **Brokers**: alpaca-py, ib_insync, ccxt (crypto)
- **Data**: yfinance, alpha_vantage, polygon-api

### Monitoring
- **Metrics**: Prometheus + Grafana
- **Logging**: structlog
- **Alerts**: Twilio, SendGrid, Slack webhooks

### Backtesting
- **Frameworks**: Backtrader, VectorBT, custom engine
- **Optimization**: Optuna

## Configuration System

Every component is configured via YAML/JSON:

```yaml
# config.yaml
mode: paper_trading  # paper_trading, live_trading, backtest

claude:
  model: claude-sonnet-4-5-20250929
  api_key: ${ANTHROPIC_API_KEY}
  max_tokens: 4096

data_sources:
  enabled:
    - alpaca_stocks
    - binance_crypto
    - newsapi

  alpaca_stocks:
    api_key: ${ALPACA_API_KEY}
    api_secret: ${ALPACA_API_SECRET}
    base_url: https://paper-api.alpaca.markets

execution:
  enabled_brokers:
    - alpaca

  alpaca:
    mode: paper
    api_key: ${ALPACA_API_KEY}
    api_secret: ${ALPACA_API_SECRET}

risk:
  max_position_size: 0.05  # 5% of portfolio per position
  max_portfolio_risk: 0.02  # 2% total portfolio risk
  max_drawdown: 0.15  # Stop trading if 15% drawdown
  stop_loss: 0.03  # 3% stop loss per trade

strategies:
  enabled:
    - claude_momentum
    - claude_mean_reversion
    - claude_sentiment
```

## Deployment Options

1. **Local Development**: Run on laptop with paper trading
2. **Cloud VPS**: AWS EC2, DigitalOcean droplet
3. **Kubernetes**: Full orchestration for production scale
4. **Serverless**: AWS Lambda for event-driven components

## Security

- API keys stored in environment variables or secrets manager
- All broker connections over HTTPS/WSS
- Audit log for every trade
- Rate limiting on AI calls
- Emergency kill switch

## Getting Started Path

1. **Phase 1**: Build core framework + paper trading
2. **Phase 2**: Backtest on historical data
3. **Phase 3**: Paper trade live for 1-3 months
4. **Phase 4**: Small capital live trading
5. **Phase 5**: Scale capital as system proves itself

## Success Metrics

- **Sharpe Ratio**: Target > 2.0
- **Max Drawdown**: Target < 15%
- **Win Rate**: Target > 55%
- **Profit Factor**: Target > 1.5
- **Uptime**: Target 99.9%
