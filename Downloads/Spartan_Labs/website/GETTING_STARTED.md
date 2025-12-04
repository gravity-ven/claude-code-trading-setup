# Getting Started - Paper Trading in 30 Minutes

This guide will get you paper trading with real-time market data in about 30 minutes.

## Prerequisites

- Python 3.11 or higher
- Internet connection
- A text editor

## Step 1: Get API Keys (10 minutes)

### Required: Anthropic Claude API

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Click "Get API Keys" or go to https://console.anthropic.com/settings/keys
4. Click "Create Key"
5. Copy the key (starts with `sk-ant-...`)
6. Save it somewhere safe - you'll need it in Step 3

**Cost**: ~$3-10/day depending on usage. Claude Sonnet 4.5 is very affordable.

### Recommended: Alpaca Paper Trading (Free!)

1. Go to https://alpaca.markets/
2. Click "Sign Up" → Choose "Paper Trading" (no money required)
3. Verify your email
4. Once logged in, go to "Your API Keys" in the dashboard
5. You'll see:
   - **API Key ID** (starts with `PK...`)
   - **Secret Key** (starts with `...` - click "View" to see it)
6. **IMPORTANT**: Make sure you see "Paper Trading" at the top
7. Copy both keys

**Cost**: $0 - Completely free paper trading with real-time market data!

## Step 2: Install the System (5 minutes)

Open your terminal and run:

```bash
cd /home/user/Spartan_Labs

# Run the automated setup script
chmod +x setup.sh
./setup.sh
```

This will:
- Create a virtual environment
- Install all dependencies
- Create your `.env` file
- Set up directories
- Validate your installation

**Alternative manual installation:**

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Create directories
mkdir -p logs data backtest_results
```

## Step 3: Configure API Keys (2 minutes)

Edit the `.env` file with your API keys:

```bash
nano .env  # or use your favorite editor
```

Update these lines:

```env
# Required - Claude AI
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here

# Recommended - Alpaca Paper Trading (FREE)
ALPACA_API_KEY=PKyour-actual-key-here
ALPACA_API_SECRET=your-actual-secret-here
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

**Save and close** (Ctrl+O, Enter, Ctrl+X if using nano)

## Step 4: Verify Setup (2 minutes)

Run the setup checker:

```bash
python scripts/setup_check.py
```

You should see:
```
✓ Python Version
✓ Dependencies
✓ Environment File
✓ Config File
✓ Directories
✓ Anthropic API

All checks passed! You're ready to start trading.
```

If any checks fail, the script will tell you how to fix them.

## Step 5: Configure Trading Settings (5 minutes)

Review and customize `config/config.yaml`:

```yaml
# Trading Mode - KEEP THIS AS paper_trading!
mode: paper_trading

# Which symbols to trade (start small)
universe:
  stocks:
    custom_tickers:
      - AAPL    # Apple
      - MSFT    # Microsoft
      - GOOGL   # Google
      - TSLA    # Tesla
      - NVDA    # Nvidia

# Risk settings (conservative defaults - good for learning)
risk:
  max_position_size: 0.05      # 5% max per position
  max_portfolio_risk: 0.02     # 2% total risk
  max_drawdown: 0.15           # Stop if 15% drawdown
  stop_loss_percent: 0.03      # 3% stop loss per trade
  take_profit_percent: 0.06    # 6% take profit target
```

**For your first run, I recommend:**
- Keep default settings
- Trade only 2-3 stocks (e.g., AAPL, MSFT)
- Use conservative risk settings

## Step 6: Start Paper Trading! (5 minutes)

Run your first trading session:

```bash
python examples/basic_trading.py
```

You should see output like:

```
[INFO] Loading configuration...
[INFO] Initializing Claude AI engine...
[INFO] Initializing data connector...
[INFO] Alpaca connector initialized
[INFO] Initializing risk manager...
[INFO] Creating trading orchestrator...
[INFO] Starting trading system...
[INFO] Mode: paper_trading
[INFO] Press Ctrl+C to stop

[INFO] Trading iteration start - iteration: 1
[INFO] Fetching market data for: AAPL, MSFT
[INFO] Claude analyzing market conditions...
[INFO] Generating trading signals...
[INFO] Processing signal: AAPL - action: buy - confidence: 0.75
[INFO] Trade validated - symbol: AAPL - approved: True
[INFO] MOCK ORDER: buy 10 AAPL @ market
[INFO] Position opened - symbol: AAPL - quantity: 10

[INFO] Portfolio summary:
  current_capital: $100,000.00
  total_pnl: $0.00
  num_positions: 1
  unrealized_pnl: $0.00
```

**What's happening:**
1. Every minute (configurable), the system:
   - Fetches market data from Alpaca
   - Asks Claude to analyze market conditions
   - Claude generates trading signals with reasoning
   - Validates trades against risk limits
   - Executes trades (in paper mode)
   - Monitors positions for stop loss/take profit

2. You'll see Claude's decisions in real-time
3. All trades are logged to `logs/spartan.log`
4. Portfolio state is tracked continuously

## Step 7: Monitor and Learn

### While Running

Watch the console output to see:
- Market analysis from Claude
- Trading signals with confidence scores
- Trade execution
- Position updates
- P&L changes

### Stop the System

Press `Ctrl+C` to stop. You'll see a final summary:

```
==================================================
FINAL PORTFOLIO SUMMARY
==================================================
Initial Capital: $100,000.00
Final Capital: $100,250.00
Total P&L: $250.00 (0.25%)
Total Trades: 3
Open Positions: 1
==================================================
```

### Check Logs

```bash
tail -f logs/spartan.log
```

This shows detailed logs of all decisions and actions.

## What to Expect

### First Few Minutes
- System starts up and connects to APIs
- Begins analyzing market conditions
- May not trade immediately (this is good - Claude is being cautious)

### First Hour
- You should see 1-3 trades if market conditions are favorable
- Claude will explain its reasoning for each trade
- Positions will be opened and monitored

### First Day
- Goal: System runs without crashes
- Expected: 5-15 trades depending on market volatility
- Focus: Understanding how Claude makes decisions

### First Week
- Goal: Become familiar with the system
- Expected: Start seeing patterns in Claude's trading style
- Focus: Observe performance across different market conditions

## Common Issues and Solutions

### "Anthropic API error"
- Check your API key in `.env`
- Verify you have credits in your Anthropic account
- Check internet connection

### "Alpaca connection failed"
- Verify API keys are correct
- Make sure you're using PAPER trading keys
- Check that `ALPACA_BASE_URL` is `https://paper-api.alpaca.markets`

### "No trading signals generated"
- This is normal! Claude is being cautious
- Market conditions may not be favorable
- Try during US market hours (9:30 AM - 4:00 PM ET)
- Increase the symbol list in `config.yaml`

### "Module not found"
- Make sure you activated the virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

### System seems slow
- Normal! Claude AI takes 2-5 seconds per decision
- This is intentional - quality over speed
- For faster response, reduce `max_tokens` in config

## Next Steps After Your First Run

### Day 1-7: Learn and Observe
- Run for a few hours each day
- Observe Claude's decision-making
- Read the logs to understand reasoning
- Note: Paper trading uses virtual money - experiment freely!

### Week 2: Customize
- Adjust risk parameters in `config.yaml`
- Add/remove trading symbols
- Try different strategies
- Experiment with configuration

### Week 3-4: Validate
- Let it run for longer periods
- Track performance metrics
- Look for consistent profitability
- Identify any issues or improvements

### Month 2+: Backtest
- Test strategies on historical data
- Validate across different market conditions
- Refine approach based on results
- Build confidence before going live

## Important Reminders

⚠️ **Paper Trading Only**
- You're using virtual money
- No real money at risk
- Perfect for learning and testing

⚠️ **Market Hours**
- US stocks trade 9:30 AM - 4:00 PM ET, Mon-Fri
- System will get limited data outside these hours
- Best to run during market hours

⚠️ **Start Small**
- Begin with 2-3 stocks
- Use conservative risk settings
- Focus on learning, not profits

⚠️ **Monitor Regularly**
- Check logs daily
- Review Claude's decisions
- Learn from every trade

⚠️ **Never Go Live Without Validation**
- Paper trade for at least 30-90 days
- Backtest extensively
- Only use real money after proven success

## Support and Resources

- **Architecture**: See `ARCHITECTURE.md`
- **Full Documentation**: See `docs/` directory
- **Roadmap**: See `ROADMAP.md`
- **Examples**: See `examples/` directory
- **Configuration**: See `config/config.yaml`

## Your First Day Checklist

- [ ] Get Anthropic API key
- [ ] Get Alpaca paper trading keys
- [ ] Run `./setup.sh`
- [ ] Configure `.env` with API keys
- [ ] Run `python scripts/setup_check.py`
- [ ] Review `config/config.yaml`
- [ ] Run `python examples/basic_trading.py`
- [ ] Let it run for 1-2 hours
- [ ] Review logs in `logs/spartan.log`
- [ ] Check final P&L summary

## Questions?

Check:
1. Logs: `logs/spartan.log`
2. Setup validation: `python scripts/setup_check.py`
3. Configuration: `config/config.yaml`
4. Documentation: `docs/quick_start.md`

---

**Ready to start?** Run `./setup.sh` and follow the prompts!

Your journey to building a billion-dollar trading system starts now. 🚀
