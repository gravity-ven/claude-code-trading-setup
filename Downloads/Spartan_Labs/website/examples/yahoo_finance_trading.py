"""
Yahoo Finance Trading Example - NO API KEYS REQUIRED!

This example shows how to use the trading system with Yahoo Finance data.

Pros:
- Completely free
- No API key required
- Quick to start

Cons:
- Data delayed 15-20 minutes
- No real execution (paper simulation only)
- Good for learning and backtesting, not live trading
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.claude_engine import ClaudeEngine
from src.core.orchestrator import TradingOrchestrator
from src.data.yahoo_connector import YahooFinanceConnector
from src.risk.risk_manager import RiskManager
from src.utils.config import init_config
import structlog

logging.basicConfig(level=logging.INFO)
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)

logger = structlog.get_logger()


async def main():
    """Main function using Yahoo Finance."""

    print("=" * 60)
    print("Spartan Trading Agent - Yahoo Finance Mode")
    print("=" * 60)
    print()
    print("✓ No API keys required!")
    print("✓ Completely free")
    print("⚠  Data delayed 15-20 minutes (not for live trading)")
    print()
    print("=" * 60)
    print()

    # Load configuration
    logger.info("Loading configuration...")
    config = init_config("config/config.yaml")

    # Initialize Claude AI engine
    logger.info("Initializing Claude AI engine...")
    claude_engine = ClaudeEngine(config.claude)

    # Initialize Yahoo Finance connector
    logger.info("Initializing Yahoo Finance connector (no API key needed)...")
    yahoo_config = config.data_sources.get("yahoo_finance", {})
    data_connector = YahooFinanceConnector(yahoo_config)

    # Initialize mock execution engine (paper simulation)
    logger.info("Initializing paper trading simulator...")
    from examples.basic_trading import MockExecutionEngine
    execution_engine = MockExecutionEngine(config.execution.get("alpaca", {}))

    # Initialize risk manager
    logger.info("Initializing risk manager...")
    initial_capital = 100000  # $100k starting capital
    risk_manager = RiskManager(config.risk, initial_capital)

    # Create orchestrator
    logger.info("Creating trading orchestrator...")
    orchestrator = TradingOrchestrator(
        config=config,
        claude_engine=claude_engine,
        data_connector=data_connector,
        execution_engine=execution_engine,
        risk_manager=risk_manager
    )

    # Start trading
    logger.info("Starting Yahoo Finance trading system...")
    logger.info("Mode: paper_trading (data from Yahoo Finance)")
    logger.info("Press Ctrl+C to stop")
    print()

    try:
        await orchestrator.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal...")
    finally:
        await orchestrator.stop()
        logger.info("Trading system stopped")

        # Print final summary
        summary = risk_manager.get_portfolio_summary()
        print()
        print("=" * 60)
        print("FINAL PORTFOLIO SUMMARY")
        print("=" * 60)
        print(f"Initial Capital: ${summary['initial_capital']:,.2f}")
        print(f"Final Capital: ${summary['current_capital']:,.2f}")
        print(f"Total P&L: ${summary['total_pnl']:,.2f} ({summary['total_pnl_percent']:.2f}%)")
        print(f"Total Trades: {summary['trades_today']}")
        print(f"Open Positions: {summary['num_positions']}")
        print("=" * 60)
        print()
        print("Note: Yahoo Finance data is delayed 15-20 minutes.")
        print("For real-time trading, use Alpaca or Interactive Brokers.")
        print()


if __name__ == "__main__":
    print()
    print("Starting in 3 seconds...")
    print("Make sure you have ANTHROPIC_API_KEY in your .env file")
    print()

    import time
    time.sleep(3)

    asyncio.run(main())
