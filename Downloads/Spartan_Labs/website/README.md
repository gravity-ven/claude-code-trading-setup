# Spartan Trading Agent

> A billion-dollar trading agent powered by Claude AI - modular, scalable, and production-ready.

## 🎯 Vision

Build an AI-first trading system where Claude AI makes intelligent trading decisions across multiple asset classes, with full modularity and production-grade reliability.

## 🚀 Features

- **🧠 Claude AI Core**: Anthropic's most advanced AI at the center of all trading decisions
- **🔌 Modular Architecture**: Plug and play different data sources, brokers, and strategies
- **📊 Multi-Asset Support**: Stocks, crypto, forex, futures - all in one system
- **⚡ Real-time Processing**: Async architecture for millisecond decision-making
- **🛡️ Risk Management**: Built-in safeguards to protect capital
- **📈 Backtesting**: Test strategies on years of historical data before risking capital
- **📱 Monitoring**: Real-time dashboards and alerts
- **🔒 Production-Ready**: Security, logging, error handling built-in

## 🏗️ Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system design.

```
Claude AI Engine → Strategy Generation → Risk Check → Execution → Monitoring
        ↑                                                              ↓
    Market Data ← Data Ingestion ← Multiple Sources ← News & Sentiment
```

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/gravity-ven/Spartan_Labs.git
cd Spartan_Labs

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your API keys
```

## ⚙️ Configuration

Edit `config/config.yaml` to configure:
- Trading mode (paper/live/backtest)
- Data sources to enable
- Brokers to use
- Risk parameters
- Strategy settings

## 🎮 Quick Start

### 1. Paper Trading (Recommended First)

```bash
# Start with paper trading to test without risking real money
python -m src.main --mode paper

# View the dashboard
open http://localhost:8000/dashboard
```

### 2. Backtesting

```bash
# Test a strategy on historical data
python -m src.backtest --strategy claude_momentum --start 2023-01-01 --end 2024-01-01
```

### 3. Live Trading (After thorough testing!)

```bash
# Go live with real money (use caution!)
python -m src.main --mode live
```

## 📚 Documentation

- [Architecture Overview](ARCHITECTURE.md)
- [Configuration Guide](docs/configuration.md)
- [Strategy Development](docs/strategies.md)
- [Adding Data Sources](docs/data_sources.md)
- [Risk Management](docs/risk_management.md)
- [API Reference](docs/api_reference.md)

## 🧪 Examples

See the `examples/` directory for:
- Basic trading strategy
- Custom data connector
- Risk management rules
- Backtesting workflows

## 🔑 Required API Keys

1. **Anthropic API** (Required): Get from https://console.anthropic.com/
2. **Broker API** (Choose one):
   - Alpaca (stocks): https://alpaca.markets/
   - Binance (crypto): https://www.binance.com/
   - Interactive Brokers: https://www.interactivebrokers.com/
3. **Data Sources** (Optional):
   - Alpha Vantage: https://www.alphavantage.co/
   - Polygon.io: https://polygon.io/
   - NewsAPI: https://newsapi.org/

## ⚠️ Risk Disclaimer

**IMPORTANT**: Trading involves substantial risk of loss. This software is provided for educational and research purposes.

- Start with paper trading
- Never risk more than you can afford to lose
- Past performance does not guarantee future results
- Test thoroughly before using real capital
- The authors are not responsible for any financial losses

## 🛠️ Development

```bash
# Run tests
pytest tests/

# Run linter
ruff check src/

# Format code
black src/

# Type checking
mypy src/
```

## 📊 Project Structure

```
spartan_labs/
├── src/
│   ├── core/           # Claude AI engine and core logic
│   ├── data/           # Data connectors and processing
│   ├── execution/      # Broker integrations and order execution
│   ├── risk/           # Risk management system
│   ├── backtest/       # Backtesting framework
│   ├── monitoring/     # Dashboards and alerting
│   ├── strategies/     # Trading strategies
│   └── utils/          # Utility functions
├── config/             # Configuration files
├── tests/              # Unit and integration tests
├── docs/               # Documentation
├── examples/           # Example code
└── data/               # Local data storage (gitignored)
```

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

See [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

- Powered by [Anthropic Claude](https://www.anthropic.com/)
- Built with Python and modern trading infrastructure

---

**Ready to build the future of AI-powered trading!** 🚀
