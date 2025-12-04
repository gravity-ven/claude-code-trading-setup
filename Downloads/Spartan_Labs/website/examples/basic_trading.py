"""
Basic Trading Example - How to use Spartan Trading Agent.

This example shows:
1. How to initialize all components
2. How to run a simple trading strategy
3. How to monitor results
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.claude_engine import ClaudeEngine
from src.core.orchestrator import TradingOrchestrator
from src.data.alpaca_connector import AlpacaConnector
from src.risk.risk_manager import RiskManager
from src.utils.config import init_config
import structlog

# Configure logging
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)

logger = structlog.get_logger()


async def main():
    """Main function to run the trading agent."""

    # 1. Load configuration
    logger.info("Loading configuration...")
    config = init_config("config/config.yaml")

    # 2. Initialize Claude AI engine
    logger.info("Initializing Claude AI engine...")
    claude_engine = ClaudeEngine(config.claude)

    # 3. Initialize data connector (Alpaca in this example)
    logger.info("Initializing data connector...")
    alpaca_config = config.data_sources.get("alpaca_stocks", {})
    data_connector = AlpacaConnector(alpaca_config)

    # 4. Initialize execution engine (paper trading for safety)
    # NOTE: We'll implement AlpacaExecutionEngine separately
    logger.info("Initializing execution engine...")
    # execution_engine = AlpacaExecutionEngine(config.execution.get("alpaca"))

    # For now, use a mock execution engine
    from src.execution.base import ExecutionEngine
    execution_engine = MockExecutionEngine(config.execution.get("alpaca", {}))

    # 5. Initialize risk manager
    logger.info("Initializing risk manager...")
    initial_capital = 100000  # $100k starting capital
    risk_manager = RiskManager(config.risk, initial_capital)

    # 6. Create orchestrator
    logger.info("Creating trading orchestrator...")
    orchestrator = TradingOrchestrator(
        config=config,
        claude_engine=claude_engine,
        data_connector=data_connector,
        execution_engine=execution_engine,
        risk_manager=risk_manager
    )

    # 7. Start trading!
    logger.info("Starting trading system...")
    logger.info("Mode: {}".format(config.mode))
    logger.info("Press Ctrl+C to stop")

    try:
        await orchestrator.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal...")
    finally:
        await orchestrator.stop()
        logger.info("Trading system stopped")

        # Print final summary
        summary = risk_manager.get_portfolio_summary()
        logger.info("="*50)
        logger.info("FINAL PORTFOLIO SUMMARY")
        logger.info("="*50)
        logger.info(f"Initial Capital: ${summary['initial_capital']:,.2f}")
        logger.info(f"Final Capital: ${summary['current_capital']:,.2f}")
        logger.info(f"Total P&L: ${summary['total_pnl']:,.2f} ({summary['total_pnl_percent']:.2f}%)")
        logger.info(f"Total Trades: {summary['trades_today']}")
        logger.info(f"Open Positions: {summary['num_positions']}")
        logger.info("="*50)


class MockExecutionEngine:
    """Mock execution engine for testing."""

    def __init__(self, config):
        self.config = config
        self.is_connected = False
        self.orders = []
        self.positions = []

    async def connect(self):
        self.is_connected = True
        logger.info("Mock execution engine connected (paper trading)")

    async def disconnect(self):
        self.is_connected = False

    async def submit_order(self, order):
        logger.info(f"MOCK ORDER: {order.side.value} {order.quantity} {order.symbol} @ market")
        self.orders.append(order)
        return order

    async def cancel_order(self, order_id):
        return True

    async def get_order_status(self, order_id):
        return None

    async def get_open_orders(self):
        return []

    async def get_account_info(self):
        return {
            "portfolio_value": 100000,
            "cash": 50000,
            "buying_power": 100000
        }

    async def get_positions(self):
        return self.positions


if __name__ == "__main__":
    # Run the trading agent
    asyncio.run(main())
