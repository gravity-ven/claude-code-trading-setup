"""
Alpaca data connector for stock market data.

Provides both historical and real-time data from Alpaca Markets.
"""

from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

import structlog
from alpaca.data import StockHistoricalDataClient
from alpaca.data.live import StockDataStream
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame as AlpacaTimeFrame

from .base import AssetType, Bar, DataConnector, Quote, TimeFrame


logger = structlog.get_logger()


class AlpacaConnector(DataConnector):
    """
    Data connector for Alpaca Markets.

    Supports US stocks with both historical and real-time data.
    """

    # Map our timeframes to Alpaca's
    TIMEFRAME_MAP = {
        TimeFrame.MIN_1: AlpacaTimeFrame.Minute,
        TimeFrame.MIN_5: AlpacaTimeFrame(5, AlpacaTimeFrame.Unit.Minute),
        TimeFrame.MIN_15: AlpacaTimeFrame(15, AlpacaTimeFrame.Unit.Minute),
        TimeFrame.MIN_30: AlpacaTimeFrame(30, AlpacaTimeFrame.Unit.Minute),
        TimeFrame.HOUR_1: AlpacaTimeFrame.Hour,
        TimeFrame.HOUR_4: AlpacaTimeFrame(4, AlpacaTimeFrame.Unit.Hour),
        TimeFrame.DAY_1: AlpacaTimeFrame.Day,
        TimeFrame.WEEK_1: AlpacaTimeFrame.Week,
        TimeFrame.MONTH_1: AlpacaTimeFrame.Month,
    }

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Alpaca connector.

        Args:
            config: Configuration with api_key, api_secret, base_url
        """
        super().__init__(config)

        self.api_key = config.get("api_key")
        self.api_secret = config.get("api_secret")
        self.base_url = config.get("base_url")
        self.data_feed = config.get("data_feed", "iex")

        # Initialize clients
        self.data_client: Optional[StockHistoricalDataClient] = None
        self.stream_client: Optional[StockDataStream] = None

        logger.info(
            "alpaca_connector_initialized",
            base_url=self.base_url,
            data_feed=self.data_feed
        )

    async def connect(self) -> None:
        """Establish connection to Alpaca."""
        try:
            # Create historical data client
            self.data_client = StockHistoricalDataClient(
                api_key=self.api_key,
                secret_key=self.api_secret
            )

            # Create streaming client
            self.stream_client = StockDataStream(
                api_key=self.api_key,
                secret_key=self.api_secret
            )

            self.is_connected = True

            logger.info("alpaca_connected")

        except Exception as e:
            logger.error("alpaca_connection_failed", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Disconnect from Alpaca."""
        try:
            if self.stream_client:
                await self.stream_client.close()

            self.is_connected = False
            logger.info("alpaca_disconnected")

        except Exception as e:
            logger.error("alpaca_disconnect_error", error=str(e))

    async def get_historical_bars(
        self,
        symbol: str,
        timeframe: TimeFrame,
        start: datetime,
        end: datetime,
        limit: Optional[int] = None
    ) -> List[Bar]:
        """
        Fetch historical OHLCV bars from Alpaca.

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            timeframe: Bar timeframe
            start: Start datetime
            end: End datetime
            limit: Maximum number of bars

        Returns:
            List of Bar objects
        """
        if not self.data_client:
            raise RuntimeError("Not connected to Alpaca. Call connect() first.")

        try:
            # Convert to Alpaca timeframe
            alpaca_timeframe = self.TIMEFRAME_MAP.get(timeframe)
            if not alpaca_timeframe:
                raise ValueError(f"Unsupported timeframe: {timeframe}")

            # Create request
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=alpaca_timeframe,
                start=start,
                end=end,
                limit=limit,
                feed=self.data_feed
            )

            # Fetch data
            bars_data = self.data_client.get_stock_bars(request)

            # Convert to our Bar format
            bars = []
            if symbol in bars_data:
                for alpaca_bar in bars_data[symbol]:
                    bar = Bar(
                        timestamp=alpaca_bar.timestamp,
                        symbol=symbol,
                        open=float(alpaca_bar.open),
                        high=float(alpaca_bar.high),
                        low=float(alpaca_bar.low),
                        close=float(alpaca_bar.close),
                        volume=float(alpaca_bar.volume),
                        asset_type=AssetType.STOCK
                    )
                    bars.append(bar)

            logger.info(
                "fetched_historical_bars",
                symbol=symbol,
                timeframe=timeframe.value,
                num_bars=len(bars)
            )

            return bars

        except Exception as e:
            logger.error(
                "fetch_historical_bars_error",
                symbol=symbol,
                error=str(e)
            )
            raise

    async def get_latest_quote(self, symbol: str) -> Quote:
        """
        Get latest quote for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Quote object
        """
        if not self.data_client:
            raise RuntimeError("Not connected to Alpaca. Call connect() first.")

        try:
            request = StockLatestQuoteRequest(
                symbol_or_symbols=symbol,
                feed=self.data_feed
            )

            quotes = self.data_client.get_stock_latest_quote(request)
            alpaca_quote = quotes[symbol]

            quote = Quote(
                timestamp=alpaca_quote.timestamp,
                symbol=symbol,
                bid=float(alpaca_quote.bid_price),
                ask=float(alpaca_quote.ask_price),
                bid_size=float(alpaca_quote.bid_size),
                ask_size=float(alpaca_quote.ask_size),
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
        Stream real-time bars.

        Args:
            symbols: List of stock symbols
            timeframe: Bar timeframe
            callback: Async function to call with each bar
        """
        if not self.stream_client:
            raise RuntimeError("Not connected to Alpaca. Call connect() first.")

        try:
            # Subscribe to bars for each symbol
            for symbol in symbols:
                @self.stream_client.on_bar(symbol)
                async def bar_handler(alpaca_bar):
                    bar = Bar(
                        timestamp=alpaca_bar.timestamp,
                        symbol=alpaca_bar.symbol,
                        open=float(alpaca_bar.open),
                        high=float(alpaca_bar.high),
                        low=float(alpaca_bar.low),
                        close=float(alpaca_bar.close),
                        volume=float(alpaca_bar.volume),
                        asset_type=AssetType.STOCK
                    )
                    await callback(bar)

            # Start streaming
            await self.stream_client.run()

            logger.info("streaming_bars", symbols=symbols, timeframe=timeframe.value)

        except Exception as e:
            logger.error("stream_bars_error", error=str(e))
            raise

    async def stream_quotes(
        self,
        symbols: List[str],
        callback: Callable
    ) -> None:
        """
        Stream real-time quotes.

        Args:
            symbols: List of stock symbols
            callback: Async function to call with each quote
        """
        if not self.stream_client:
            raise RuntimeError("Not connected to Alpaca. Call connect() first.")

        try:
            # Subscribe to quotes for each symbol
            for symbol in symbols:
                @self.stream_client.on_quote(symbol)
                async def quote_handler(alpaca_quote):
                    quote = Quote(
                        timestamp=alpaca_quote.timestamp,
                        symbol=alpaca_quote.symbol,
                        bid=float(alpaca_quote.bid_price),
                        ask=float(alpaca_quote.ask_price),
                        bid_size=float(alpaca_quote.bid_size),
                        ask_size=float(alpaca_quote.ask_size),
                        asset_type=AssetType.STOCK
                    )
                    await callback(quote)

            # Start streaming
            await self.stream_client.run()

            logger.info("streaming_quotes", symbols=symbols)

        except Exception as e:
            logger.error("stream_quotes_error", error=str(e))
            raise
