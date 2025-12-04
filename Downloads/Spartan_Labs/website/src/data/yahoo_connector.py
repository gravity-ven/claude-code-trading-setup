"""
Yahoo Finance data connector - FREE market data.

No execution capability, but great for data and testing.
Completely free with no API key required.
"""

from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

import structlog
import yfinance as yf
import pandas as pd

from .base import AssetType, Bar, DataConnector, Quote, TimeFrame


logger = structlog.get_logger()


class YahooFinanceConnector(DataConnector):
    """
    Data connector for Yahoo Finance.

    Pros:
    - Completely free
    - No API key required
    - Good historical data
    - Supports stocks globally

    Cons:
    - No real-time streaming
    - No order execution
    - Data delayed 15-20 minutes
    - Rate limits on requests
    """

    # Map our timeframes to Yahoo's
    TIMEFRAME_MAP = {
        TimeFrame.MIN_1: "1m",
        TimeFrame.MIN_5: "5m",
        TimeFrame.MIN_15: "15m",
        TimeFrame.MIN_30: "30m",
        TimeFrame.HOUR_1: "1h",
        TimeFrame.DAY_1: "1d",
        TimeFrame.WEEK_1: "1wk",
        TimeFrame.MONTH_1: "1mo",
    }

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Yahoo Finance connector.

        Args:
            config: Configuration (mostly empty, no API key needed)
        """
        super().__init__(config)
        logger.info("yahoo_finance_connector_initialized")

    async def connect(self) -> None:
        """Connect to Yahoo Finance (no actual connection needed)."""
        self.is_connected = True
        logger.info("yahoo_finance_connected")

    async def disconnect(self) -> None:
        """Disconnect from Yahoo Finance."""
        self.is_connected = False
        logger.info("yahoo_finance_disconnected")

    async def get_historical_bars(
        self,
        symbol: str,
        timeframe: TimeFrame,
        start: datetime,
        end: datetime,
        limit: Optional[int] = None
    ) -> List[Bar]:
        """
        Fetch historical OHLCV bars from Yahoo Finance.

        Args:
            symbol: Stock ticker
            timeframe: Bar timeframe
            start: Start datetime
            end: End datetime
            limit: Maximum number of bars

        Returns:
            List of Bar objects
        """
        try:
            # Convert timeframe
            interval = self.TIMEFRAME_MAP.get(timeframe, "1h")

            # Download data
            ticker = yf.Ticker(symbol)
            df = ticker.history(
                start=start,
                end=end,
                interval=interval,
                auto_adjust=False
            )

            # Convert to our Bar format
            bars = []
            for timestamp, row in df.iterrows():
                bar = Bar(
                    timestamp=timestamp.to_pydatetime(),
                    symbol=symbol,
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=float(row["Volume"]),
                    asset_type=AssetType.STOCK
                )
                bars.append(bar)

            # Apply limit if specified
            if limit:
                bars = bars[-limit:]

            logger.info(
                "fetched_historical_bars",
                symbol=symbol,
                timeframe=timeframe.value,
                num_bars=len(bars)
            )

            return bars

        except Exception as e:
            logger.error("fetch_historical_bars_error", symbol=symbol, error=str(e))
            return []

    async def get_latest_quote(self, symbol: str) -> Quote:
        """
        Get latest quote for a symbol.

        Args:
            symbol: Stock ticker

        Returns:
            Quote object

        Note: Yahoo Finance data is delayed 15-20 minutes
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Get current price
            current_price = info.get("currentPrice") or info.get("regularMarketPrice", 0)

            # Yahoo doesn't provide bid/ask, so we approximate
            spread = current_price * 0.0005  # Assume 0.05% spread

            quote = Quote(
                timestamp=datetime.now(),
                symbol=symbol,
                bid=current_price - spread,
                ask=current_price + spread,
                bid_size=0.0,  # Not available
                ask_size=0.0,  # Not available
                asset_type=AssetType.STOCK
            )

            return quote

        except Exception as e:
            logger.error("get_latest_quote_error", symbol=symbol, error=str(e))
            raise

    async def stream_bars(
        self,
        symbols: List[str],
        timeframe: TimeFrame,
        callback: Callable
    ) -> None:
        """
        Simulate streaming by polling.

        Args:
            symbols: List of stock symbols
            timeframe: Bar timeframe
            callback: Async function to call with each bar

        Note: Not true streaming, polls every minute
        """
        logger.warning(
            "yahoo_finance_pseudo_streaming",
            message="Yahoo Finance doesn't support real-time streaming. Polling instead."
        )

        try:
            while self.is_connected:
                for symbol in symbols:
                    # Fetch latest bar
                    end = datetime.now()
                    start = end - timedelta(hours=1)

                    bars = await self.get_historical_bars(
                        symbol=symbol,
                        timeframe=timeframe,
                        start=start,
                        end=end,
                        limit=1
                    )

                    if bars:
                        await callback(bars[-1])

                # Wait before next poll
                import asyncio
                await asyncio.sleep(60)

        except Exception as e:
            logger.error("stream_bars_error", error=str(e))

    async def stream_quotes(
        self,
        symbols: List[str],
        callback: Callable
    ) -> None:
        """
        Simulate quote streaming by polling.

        Args:
            symbols: List of stock symbols
            callback: Async function to call with each quote

        Note: Not true streaming, polls every 30 seconds
        """
        logger.warning(
            "yahoo_finance_pseudo_streaming",
            message="Yahoo Finance doesn't support real-time streaming. Polling instead."
        )

        try:
            while self.is_connected:
                for symbol in symbols:
                    quote = await self.get_latest_quote(symbol)
                    await callback(quote)

                # Wait before next poll
                import asyncio
                await asyncio.sleep(30)

        except Exception as e:
            logger.error("stream_quotes_error", error=str(e))
