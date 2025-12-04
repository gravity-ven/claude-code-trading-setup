"""
Interactive Brokers (IBKR) connector for stocks, options, futures, forex.

IBKR is a professional-grade broker with excellent API support.
Supports paper trading through their paper trading account.
"""

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import structlog
from ib_insync import IB, Stock, MarketOrder, LimitOrder, StopOrder, util

from .base import AssetType, Bar, DataConnector, Quote, TimeFrame


logger = structlog.get_logger()


class IBKRConnector(DataConnector):
    """
    Data connector for Interactive Brokers.

    Supports stocks, options, futures, and forex with both paper and live trading.
    """

    # Map our timeframes to IBKR's
    TIMEFRAME_MAP = {
        TimeFrame.MIN_1: ("1 min", ""),
        TimeFrame.MIN_5: ("5 mins", ""),
        TimeFrame.MIN_15: ("15 mins", ""),
        TimeFrame.MIN_30: ("30 mins", ""),
        TimeFrame.HOUR_1: ("1 hour", ""),
        TimeFrame.HOUR_4: ("4 hours", ""),
        TimeFrame.DAY_1: ("1 day", ""),
        TimeFrame.WEEK_1: ("1 week", ""),
    }

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize IBKR connector.

        Args:
            config: Configuration with host, port, client_id
        """
        super().__init__(config)

        self.host = config.get("host", "127.0.0.1")
        self.port = config.get("port", 7497)  # 7497 for paper, 7496 for live
        self.client_id = config.get("client_id", 1)

        self.ib: Optional[IB] = None

        logger.info(
            "ibkr_connector_initialized",
            host=self.host,
            port=self.port,
            mode="paper" if self.port == 7497 else "live"
        )

    async def connect(self) -> None:
        """Establish connection to IBKR TWS or Gateway."""
        try:
            self.ib = IB()
            await self.ib.connectAsync(self.host, self.port, clientId=self.client_id)

            self.is_connected = True

            logger.info(
                "ibkr_connected",
                account=self.ib.managedAccounts()[0] if self.ib.managedAccounts() else "unknown"
            )

        except Exception as e:
            logger.error("ibkr_connection_failed", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Disconnect from IBKR."""
        try:
            if self.ib:
                self.ib.disconnect()

            self.is_connected = False
            logger.info("ibkr_disconnected")

        except Exception as e:
            logger.error("ibkr_disconnect_error", error=str(e))

    async def get_historical_bars(
        self,
        symbol: str,
        timeframe: TimeFrame,
        start: datetime,
        end: datetime,
        limit: Optional[int] = None
    ) -> List[Bar]:
        """
        Fetch historical OHLCV bars from IBKR.

        Args:
            symbol: Stock symbol
            timeframe: Bar timeframe
            start: Start datetime
            end: End datetime
            limit: Maximum number of bars

        Returns:
            List of Bar objects
        """
        if not self.ib:
            raise RuntimeError("Not connected to IBKR. Call connect() first.")

        try:
            # Create contract
            contract = Stock(symbol, "SMART", "USD")
            await self.ib.qualifyContractsAsync(contract)

            # Get timeframe
            bar_size, _ = self.TIMEFRAME_MAP.get(timeframe, ("1 hour", ""))

            # Calculate duration
            duration_seconds = (end - start).total_seconds()
            if duration_seconds < 86400:  # Less than 1 day
                duration = f"{int(duration_seconds)} S"
            else:
                duration = f"{int(duration_seconds / 86400)} D"

            # Fetch bars
            ib_bars = await self.ib.reqHistoricalDataAsync(
                contract,
                endDateTime=end,
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow="TRADES",
                useRTH=True,  # Regular trading hours only
                formatDate=1
            )

            # Convert to our Bar format
            bars = []
            for ib_bar in ib_bars:
                bar = Bar(
                    timestamp=ib_bar.date,
                    symbol=symbol,
                    open=float(ib_bar.open),
                    high=float(ib_bar.high),
                    low=float(ib_bar.low),
                    close=float(ib_bar.close),
                    volume=float(ib_bar.volume),
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
            raise

    async def get_latest_quote(self, symbol: str) -> Quote:
        """
        Get latest quote for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Quote object
        """
        if not self.ib:
            raise RuntimeError("Not connected to IBKR. Call connect() first.")

        try:
            contract = Stock(symbol, "SMART", "USD")
            await self.ib.qualifyContractsAsync(contract)

            # Request market data
            ticker = self.ib.reqMktData(contract, "", False, False)
            await self.ib.sleep(2)  # Wait for data

            quote = Quote(
                timestamp=datetime.now(),
                symbol=symbol,
                bid=float(ticker.bid) if ticker.bid else 0.0,
                ask=float(ticker.ask) if ticker.ask else 0.0,
                bid_size=float(ticker.bidSize) if ticker.bidSize else 0.0,
                ask_size=float(ticker.askSize) if ticker.askSize else 0.0,
                asset_type=AssetType.STOCK
            )

            # Cancel market data subscription
            self.ib.cancelMktData(contract)

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
        if not self.ib:
            raise RuntimeError("Not connected to IBKR. Call connect() first.")

        try:
            bar_size, _ = self.TIMEFRAME_MAP.get(timeframe, ("1 min", ""))

            for symbol in symbols:
                contract = Stock(symbol, "SMART", "USD")
                await self.ib.qualifyContractsAsync(contract)

                # Subscribe to real-time bars
                bars = self.ib.reqRealTimeBars(
                    contract,
                    5,  # 5 second bars
                    "TRADES",
                    False
                )

                def on_bar_update(bars, hasNewBar):
                    if hasNewBar:
                        ib_bar = bars[-1]
                        bar = Bar(
                            timestamp=ib_bar.time,
                            symbol=symbol,
                            open=float(ib_bar.open),
                            high=float(ib_bar.high),
                            low=float(ib_bar.low),
                            close=float(ib_bar.close),
                            volume=float(ib_bar.volume),
                            asset_type=AssetType.STOCK
                        )
                        util.run(callback(bar))

                bars.updateEvent += on_bar_update

            logger.info("streaming_bars", symbols=symbols)

            # Keep connection alive
            while self.is_connected:
                await self.ib.sleep(1)

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
        if not self.ib:
            raise RuntimeError("Not connected to IBKR. Call connect() first.")

        try:
            for symbol in symbols:
                contract = Stock(symbol, "SMART", "USD")
                await self.ib.qualifyContractsAsync(contract)

                ticker = self.ib.reqMktData(contract, "", False, False)

                def on_ticker_update(ticker):
                    quote = Quote(
                        timestamp=datetime.now(),
                        symbol=symbol,
                        bid=float(ticker.bid) if ticker.bid else 0.0,
                        ask=float(ticker.ask) if ticker.ask else 0.0,
                        bid_size=float(ticker.bidSize) if ticker.bidSize else 0.0,
                        ask_size=float(ticker.askSize) if ticker.askSize else 0.0,
                        asset_type=AssetType.STOCK
                    )
                    util.run(callback(quote))

                ticker.updateEvent += on_ticker_update

            logger.info("streaming_quotes", symbols=symbols)

            # Keep connection alive
            while self.is_connected:
                await self.ib.sleep(1)

        except Exception as e:
            logger.error("stream_quotes_error", error=str(e))
            raise
