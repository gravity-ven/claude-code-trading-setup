# Spartan Trading Agent - Examples

This directory contains examples showing how to use the Spartan Trading Agent.

## Examples

### 1. Basic Trading (`basic_trading.py`)

The most basic example showing how to:
- Initialize all components
- Run the trading loop
- Monitor results

**Usage:**

```bash
# Make sure you've set up your .env file first
cp ../.env.example ../.env
# Edit .env with your API keys

# Install dependencies
pip install -r ../requirements.txt

# Run the example
python basic_trading.py
```

### 2. Backtest Strategy (Coming Soon)

Example showing how to backtest a strategy on historical data.

### 3. Custom Strategy (Coming Soon)

Example showing how to create your own custom trading strategy.

### 4. Custom Data Source (Coming Soon)

Example showing how to add a new data source connector.

## Safety First!

All examples default to **paper trading mode**. Never use real money until you've:

1. Backtested thoroughly on historical data
2. Paper traded successfully for 1-3 months
3. Started with small capital
4. Understand all risks involved

## Configuration

Each example uses the configuration file at `config/config.yaml`. Key settings:

- `mode`: Set to `paper_trading`, `live_trading`, or `backtest`
- `risk`: Adjust risk parameters
- `strategies.enabled`: Choose which strategies to run
- `data_sources.enabled`: Choose which data sources to use

## Getting Help

If you run into issues:

1. Check the logs in `logs/spartan.log`
2. Review the configuration in `config/config.yaml`
3. Make sure all API keys are set in `.env`
4. Check the main documentation in `../docs/`

## Next Steps

After running the basic example:

1. **Read the Architecture**: See `../ARCHITECTURE.md`
2. **Customize Configuration**: Edit `../config/config.yaml`
3. **Add Strategies**: See `../docs/strategies.md`
4. **Monitor Performance**: Use the dashboard (coming soon)
5. **Optimize**: Use backtesting to refine your approach
