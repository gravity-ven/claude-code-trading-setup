"""
Base classes for execution engines and broker adapters.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class OrderSide(Enum):
    """Order side."""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Order type."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class OrderStatus(Enum):
    """Order status."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class TimeInForce(Enum):
    """Time in force."""
    DAY = "day"
    GTC = "gtc"  # Good til cancelled
    IOC = "ioc"  # Immediate or cancel
    FOK = "fok"  # Fill or kill


class Order(BaseModel):
    """Trading order."""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: TimeInForce = TimeInForce.DAY
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    filled_avg_price: Optional[float] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    broker_order_id: Optional[str] = None

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
        use_enum_values = True


class Fill(BaseModel):
    """Order fill (execution)."""
    fill_id: str
    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    timestamp: datetime
    commission: float = 0.0


class ExecutionEngine(ABC):
    """
    Abstract base class for execution engines.

    Handles order submission, tracking, and execution across brokers.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize execution engine.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.is_connected = False

    @abstractmethod
    async def connect(self) -> None:
        """Connect to broker."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from broker."""
        pass

    @abstractmethod
    async def submit_order(self, order: Order) -> Order:
        """
        Submit an order to the broker.

        Args:
            order: Order to submit

        Returns:
            Updated order with broker order ID and status
        """
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if successfully cancelled
        """
        pass

    @abstractmethod
    async def get_order_status(self, order_id: str) -> Order:
        """
        Get current status of an order.

        Args:
            order_id: Order ID

        Returns:
            Order with current status
        """
        pass

    @abstractmethod
    async def get_open_orders(self) -> List[Order]:
        """
        Get all open orders.

        Returns:
            List of open orders
        """
        pass

    @abstractmethod
    async def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information.

        Returns:
            Account info including buying power, equity, etc.
        """
        pass

    @abstractmethod
    async def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get current positions.

        Returns:
            List of positions
        """
        pass
