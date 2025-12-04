# Quick Start Guide

Get up and running with Spartan Trading Agent in 10 minutes.

## Prerequisites

- Python 3.11 or higher
- An Anthropic API key ([get one here](https://console.anthropic.com/))
- A broker account (Alpaca recommended for stocks, free paper trading)

## Step 1: Installation

```bash
# Clone the repository
git clone https://github.com/gravity-ven/Spartan_Labs.git
cd Spartan_Labs

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Get API Keys

### Required: Anthropic Claude API

1. Go to https://console.anthropic.com/
2. Create an account or log in
3. Generate an API key
4. Copy the key (you'll need it in the next step)

### Recommended: Alpaca (for stock trading)

1. Go to https://alpaca.markets/
2. Sign up for a free account
3. Get your paper trading API keys
4. Copy both the API key and secret key

## Step 3: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your favorite editor
nano .env  # or vim, code, etc.
```

Add your API keys:

```env
# Required
ANTHROPIC_API_KEY=your_anthropic_key_here

# For stock trading with Alpaca
ALPACA_API_KEY=your_alpaca_api_key
ALPACA_API_SECRET=your_alpaca_secret_key
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

## Step 4: Configure Trading Settings

Edit `config/config.yaml` to customize your trading:

```yaml
# Trading mode
mode: paper_trading  # Start with paper trading!

# Enable data sources
data_sources:
  enabled:
    - alpaca_stocks

# Enable brokers
execution:
  enabled_brokers:
    - alpaca

# Risk settings (conservative defaults)
risk:
  max_position_size: 0.05  # 5% max per position
  max_drawdown: 0.15  # Stop if 15% drawdown
  stop_loss_percent: 0.03  # 3% stop loss

# Which symbols to trade
universe:
  stocks:
    custom_tickers:
      - AAPL
      - MSFT
      - GOOGL
```

## Step 5: Run Your First Trade

```bash
# Run the basic example
python examples/basic_trading.py
```

You should see output like:

```
[INFO] Loading configuration...
[INFO] Initializing Claude AI engine...
[INFO] Initializing data connector...
[INFO] Starting trading system...
[INFO] Mode: paper_trading
[INFO] Press Ctrl+C to stop
```

The system will now:
1. Analyze the market every minute
2. Generate trading signals using Claude AI
3. Validate trades against risk rules
4. Execute trades (in paper mode)
5. Monitor positions for stop loss / take profit

## Step 6: Monitor Results

Press `Ctrl+C` to stop the trading system. You'll see a summary:

```
==================================================
FINAL PORTFOLIO SUMMARY
==================================================
Initial Capital: $100,000.00
Final Capital: $101,250.00
Total P&L: $1,250.00 (1.25%)
Total Trades: 5
Open Positions: 2
==================================================
```

## What's Next?

### Backtest Before Live Trading

```bash
# Test your strategy on historical data
python -m src.backtest --strategy claude_momentum --start 2023-01-01 --end 2024-01-01
```

### View the Dashboard

```bash
# Start the web dashboard
python -m src.api.server

# Open http://localhost:8000/dashboard
```

### Customize Your Strategy

Edit `config/config.yaml` to:
- Add more symbols to trade
- Adjust risk parameters
- Change strategy types
- Enable news sentiment analysis

### Go Live (When Ready!)

**IMPORTANT**: Only after thorough testing!

1. Change mode in `config/config.yaml`:
   ```yaml
   mode: live_trading
   ```

2. Update `.env` with live API credentials:
   ```env
   ALPACA_BASE_URL=https://api.alpaca.markets
   ```

3. Start with small capital you can afford to lose

## Troubleshooting

### "Module not found" errors

Make sure you're in the virtual environment:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "Authentication failed"

Check your API keys in `.env`:
- Make sure there are no extra spaces
- Make sure you're using the right keys (paper vs live)

### "No trading signals generated"

This is normal if market conditions aren't favorable. Claude is being cautious.
Try:
- Adding more symbols to your universe
- Adjusting the confidence threshold
- Checking market hours (US stocks trade 9:30 AM - 4:00 PM ET)

### Still stuck?

Check the logs:
```bash
tail -f logs/spartan.log
```

## Safety Reminders

- ✅ Always start with paper trading
- ✅ Backtest on historical data first
- ✅ Start with small capital when going live
- ✅ Never risk more than you can afford to lose
- ✅ Monitor your positions regularly
- ✅ Understand all risks before trading

## Next Steps

- [Read the Architecture](../ARCHITECTURE.md)
- [Customize Strategies](strategies.md)
- [Add Data Sources](data_sources.md)
- [Understanding Risk Management](risk_management.md)
- [API Reference](api_reference.md)

Happy trading! 🚀
