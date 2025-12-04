"""
Trading Orchestrator - Main coordination logic.

Coordinates between Claude AI, data sources, risk management, and execution.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog

from ..data.base import DataConnector, TimeFrame
from ..execution.base import ExecutionEngine, Order, OrderSide, OrderType
from ..risk.risk_manager import RiskManager
from ..utils.config import Config
from .claude_engine import ClaudeEngine


logger = structlog.get_logger()


class TradingOrchestrator:
    """
    Main orchestrator for the Spartan Trading Agent.

    Coordinates all components and implements the trading loop.
    """

    def __init__(
        self,
        config: Config,
        claude_engine: ClaudeEngine,
        data_connector: DataConnector,
        execution_engine: ExecutionEngine,
        risk_manager: RiskManager
    ):
        """
        Initialize the orchestrator.

        Args:
            config: System configuration
            claude_engine: Claude AI engine
            data_connector: Data connector
            execution_engine: Execution engine
            risk_manager: Risk manager
        """
        self.config = config
        self.claude = claude_engine
        self.data = data_connector
        self.execution = execution_engine
        self.risk = risk_manager

        self.is_running = False
        self.iteration_count = 0

        logger.info("orchestrator_initialized", mode=config.mode)

    async def start(self) -> None:
        """Start the trading system."""
        try:
            logger.info("starting_trading_system")

            # Connect all components
            await self.data.connect()
            await self.execution.connect()

            self.is_running = True

            # Start trading loop
            await self.trading_loop()

        except Exception as e:
            logger.error("orchestrator_error", error=str(e))
            raise
        finally:
            await self.stop()

    async def stop(self) -> None:
        """Stop the trading system."""
        logger.info("stopping_trading_system")

        self.is_running = False

        # Disconnect components
        await self.data.disconnect()
        await self.execution.disconnect()

        logger.info("trading_system_stopped")

    async def trading_loop(self) -> None:
        """
        Main trading loop.

        Continuously analyzes market, generates signals, and executes trades.
        """
        while self.is_running:
            try:
                self.iteration_count += 1

                logger.info("trading_iteration_start", iteration=self.iteration_count)

                # 1. Gather market data
                market_data = await self.gather_market_data()

                # 2. Analyze market with Claude
                market_analysis = await self.claude.analyze_market(
                    market_data=market_data
                )

                # 3. Get current portfolio state
                portfolio = await self.get_portfolio_state()

                # 4. Generate trading signals
                signals = await self.claude.generate_trading_signals(
                    market_analysis=market_analysis,
                    portfolio=portfolio,
                    strategy_type="momentum"  # TODO: Make configurable
                )

                # 5. Process each signal
                for signal in signals:
                    await self.process_signal(signal, portfolio, market_analysis)

                # 6. Check existing positions for stop loss / take profit
                await self.monitor_positions()

                # 7. Log portfolio summary
                summary = self.risk.get_portfolio_summary()
                logger.info("portfolio_summary", **summary)

                # Wait before next iteration (e.g., 1 minute for 1m bars)
                await asyncio.sleep(60)

            except Exception as e:
                logger.error("trading_loop_error", error=str(e))
                await asyncio.sleep(60)

    async def gather_market_data(self) -> Dict[str, Any]:
        """
        Gather market data from all sources.

        Returns:
            Dictionary with market data
        """
        # Get universe of symbols to trade
        symbols = self.get_trading_universe()

        market_data = {"symbols": {}}

        # Fetch data for each symbol
        for symbol in symbols[:10]:  # Limit to prevent overload
            try:
                # Get latest quote
                quote = await self.data.get_latest_quote(symbol)

                # Get recent bars
                end = datetime.now()
                start = end.replace(hour=end.hour - 24)  # Last 24 hours

                bars = await self.data.get_historical_bars(
                    symbol=symbol,
                    timeframe=TimeFrame.HOUR_1,
                    start=start,
                    end=end,
                    limit=24
                )

                # Convert to dataframe for analysis
                df = self.data.bars_to_dataframe(bars)

                market_data["symbols"][symbol] = {
                    "current_price": quote.ask,
                    "bid": quote.bid,
                    "ask": quote.ask,
                    "bars": df.to_dict() if not df.empty else {},
                    "volume_24h": df["volume"].sum() if not df.empty else 0
                }

            except Exception as e:
                logger.error("error_fetching_data", symbol=symbol, error=str(e))

        return market_data

    async def process_signal(
        self,
        signal: Dict[str, Any],
        portfolio: Dict[str, Any],
        market_analysis: Dict[str, Any]
    ) -> None:
        """
        Process a trading signal from Claude.

        Args:
            signal: Trading signal
            portfolio: Current portfolio state
            market_analysis: Market analysis context
        """
        symbol = signal.get("symbol")
        action = signal.get("action")
        quantity = signal.get("quantity", 0)
        confidence = signal.get("confidence", 0.5)

        logger.info(
            "processing_signal",
            symbol=symbol,
            action=action,
            quantity=quantity,
            confidence=confidence
        )

        # Skip if confidence too low
        if confidence < 0.6:
            logger.info("signal_skipped_low_confidence", symbol=symbol, confidence=confidence)
            return

        # Skip hold signals
        if action == "hold":
            return

        # Get account info
        account = await self.execution.get_account_info()
        portfolio_value = account.get("portfolio_value", 0)

        # Determine price
        price = signal.get("entry_price", 0)

        # Validate trade with risk manager
        validation = self.risk.validate_trade(
            symbol=symbol,
            quantity=quantity,
            price=price,
            side=action,
            current_portfolio_value=portfolio_value
        )

        if not validation["approved"]:
            logger.warning(
                "trade_rejected",
                symbol=symbol,
                reason=validation["reason"]
            )
            return

        # Use adjusted quantity if modified
        adjusted_quantity = validation["adjusted_quantity"]

        # Log any warnings
        for warning in validation.get("warnings", []):
            logger.warning("trade_warning", warning=warning)

        # Execute trade (in paper trading or live mode)
        if self.config.mode in ["paper_trading", "live_trading"]:
            await self.execute_trade(signal, adjusted_quantity)

    async def execute_trade(
        self,
        signal: Dict[str, Any],
        quantity: float
    ) -> None:
        """
        Execute a trade.

        Args:
            signal: Trading signal
            quantity: Adjusted quantity to trade
        """
        symbol = signal.get("symbol")
        action = signal.get("action")
        entry_price = signal.get("entry_price")
        stop_loss = signal.get("stop_loss")
        take_profit = signal.get("take_profit")

        try:
            # Create order
            order = Order(
                order_id=f"{symbol}_{datetime.now().timestamp()}",
                symbol=symbol,
                side=OrderSide.BUY if action == "buy" else OrderSide.SELL,
                order_type=OrderType.MARKET,  # Use market orders for now
                quantity=quantity,
                time_in_force="day"
            )

            # Submit order
            result = await self.execution.submit_order(order)

            logger.info(
                "order_submitted",
                symbol=symbol,
                side=action,
                quantity=quantity,
                order_id=result.order_id
            )

            # Track position in risk manager
            if action == "buy":
                self.risk.open_position(
                    symbol=symbol,
                    quantity=quantity,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )

        except Exception as e:
            logger.error("order_execution_error", symbol=symbol, error=str(e))

    async def monitor_positions(self) -> None:
        """Monitor existing positions for stop loss / take profit."""
        for symbol, position in list(self.risk.positions.items()):
            try:
                # Get current price
                quote = await self.data.get_latest_quote(symbol)
                current_price = quote.ask

                # Update position and check for actions
                action = self.risk.update_position_price(symbol, current_price)

                if action in ["stop_loss", "take_profit"]:
                    logger.info(
                        "closing_position",
                        symbol=symbol,
                        reason=action,
                        current_price=current_price
                    )

                    # Close position
                    await self.close_position(symbol, current_price, action)

            except Exception as e:
                logger.error("monitor_position_error", symbol=symbol, error=str(e))

    async def close_position(
        self,
        symbol: str,
        price: float,
        reason: str
    ) -> None:
        """
        Close a position.

        Args:
            symbol: Symbol to close
            price: Exit price
            reason: Reason for closing
        """
        position = self.risk.positions.get(symbol)
        if not position:
            return

        try:
            # Create closing order
            order = Order(
                order_id=f"close_{symbol}_{datetime.now().timestamp()}",
                symbol=symbol,
                side=OrderSide.SELL if position.is_long() else OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=abs(position.quantity)
            )

            # Submit order
            await self.execution.submit_order(order)

            # Update risk manager
            result = self.risk.close_position(symbol, price, reason)

            logger.info("position_closed", **result)

        except Exception as e:
            logger.error("close_position_error", symbol=symbol, error=str(e))

    async def get_portfolio_state(self) -> Dict[str, Any]:
        """
        Get current portfolio state.

        Returns:
            Portfolio state dictionary
        """
        account = await self.execution.get_account_info()
        positions = await self.execution.get_positions()
        risk_summary = self.risk.get_portfolio_summary()

        return {
            "account": account,
            "positions": positions,
            "risk": risk_summary
        }

    def get_trading_universe(self) -> List[str]:
        """
        Get list of symbols to trade.

        Returns:
            List of trading symbols
        """
        # Get from config
        universe_config = self.config.universe

        # For now, return custom tickers
        # TODO: Implement SP500, NASDAQ100 universe loading
        return universe_config.get("stocks", {}).get("custom_tickers", ["AAPL"])
