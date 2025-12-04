"""
Base classes for data connectors.

All data sources implement the DataConnector interface for consistency.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import pandas as pd
from pydantic import BaseModel


class AssetType(Enum):
    """Asset type enumeration."""
    STOCK = "stock"
    CRYPTO = "crypto"
    FOREX = "forex"
    FUTURES = "futures"
    OPTIONS = "options"


class TimeFrame(Enum):
    """Time frame enumeration."""
    TICK = "tick"
    MIN_1 = "1m"
    MIN_5 = "5m"
    MIN_15 = "15m"
    MIN_30 = "30m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY_1 = "1d"
    WEEK_1 = "1w"
    MONTH_1 = "1M"


class Bar(BaseModel):
    """
    Standard OHLCV bar data.

    All data connectors should convert their data to this format.
    """
    timestamp: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    asset_type: AssetType

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True


class Quote(BaseModel):
    """Real-time quote data."""
    timestamp: datetime
    symbol: str
    bid: float
    ask: float
    bid_size: float
    ask_size: float
    asset_type: AssetType


class Trade(BaseModel):
    """Individual trade (tick) data."""
    timestamp: datetime
    symbol: str
    price: float
    size: float
    side: str  # "buy" or "sell"
    asset_type: AssetType


class NewsArticle(BaseModel):
    """News article data."""
    timestamp: datetime
    source: str
    title: str
    content: str
    url: Optional[str] = None
    sentiment: Optional[float] = None  # -1.0 to 1.0
    symbols: List[str] = []


class DataConnector(ABC):
    """
    Abstract base class for all data connectors.

    Implementations provide data from different sources (Alpaca, Binance, etc.)
    in a standardized format.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the data connector.

        Args:
            config: Configuration dictionary for this connector
        """
        self.config = config
        self.is_connected = False

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to data source."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from data source."""
        pass

    @abstractmethod
    async def get_historical_bars(
        self,
        symbol: str,
        timeframe: TimeFrame,
        start: datetime,
        end: datetime,
        limit: Optional[int] = None
    ) -> List[Bar]:
        """
        Fetch historical OHLCV bars.

        Args:
            symbol: Trading symbol
            timeframe: Bar timeframe
            start: Start datetime
            end: End datetime
            limit: Maximum number of bars to return

        Returns:
            List of Bar objects
        """
        pass

    @abstractmethod
    async def get_latest_quote(self, symbol: str) -> Quote:
        """
        Get latest quote for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Quote object
        """
        pass

    @abstractmethod
    async def stream_bars(
        self,
        symbols: List[str],
        timeframe: TimeFrame,
        callback: Any
    ) -> None:
        """
        Stream real-time bars.

        Args:
            symbols: List of symbols to stream
            timeframe: Bar timeframe
            callback: Async function to call with each bar
        """
        pass

    @abstractmethod
    async def stream_quotes(
        self,
        symbols: List[str],
        callback: Any
    ) -> None:
        """
        Stream real-time quotes.

        Args:
            symbols: List of symbols to stream
            callback: Async function to call with each quote
        """
        pass

    def bars_to_dataframe(self, bars: List[Bar]) -> pd.DataFrame:
        """
        Convert list of bars to pandas DataFrame.

        Args:
            bars: List of Bar objects

        Returns:
            DataFrame with OHLCV data
        """
        if not bars:
            return pd.DataFrame()

        df = pd.DataFrame([
            {
                "timestamp": bar.timestamp,
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
            }
            for bar in bars
        ])

        df.set_index("timestamp", inplace=True)
        return df


class NewsConnector(ABC):
    """
    Abstract base class for news data connectors.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the news connector.

        Args:
            config: Configuration dictionary
        """
        self.config = config

    @abstractmethod
    async def get_news(
        self,
        symbols: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 50
    ) -> List[NewsArticle]:
        """
        Fetch news articles.

        Args:
            symbols: Filter by symbols (if supported)
            keywords: Filter by keywords
            start: Start datetime
            end: End datetime
            limit: Maximum number of articles

        Returns:
            List of NewsArticle objects
        """
        pass

    @abstractmethod
    async def stream_news(
        self,
        symbols: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        callback: Any = None
    ) -> None:
        """
        Stream real-time news.

        Args:
            symbols: Filter by symbols
            keywords: Filter by keywords
            callback: Async function to call with each article
        """
        pass
