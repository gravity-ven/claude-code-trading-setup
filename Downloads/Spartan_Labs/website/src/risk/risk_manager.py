"""
Risk Management System for Spartan Trading Agent.

Implements various risk controls to protect capital:
- Position sizing
- Portfolio risk limits
- Drawdown protection
- Concentration limits
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import structlog

from ..utils.config import RiskConfig


logger = structlog.get_logger()


class Position:
    """Represents an open trading position."""

    def __init__(
        self,
        symbol: str,
        quantity: float,
        entry_price: float,
        entry_time: datetime,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ):
        """Initialize a position."""
        self.symbol = symbol
        self.quantity = quantity
        self.entry_price = entry_price
        self.entry_time = entry_time
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.current_price = entry_price

    def update_price(self, price: float) -> None:
        """Update current price."""
        self.current_price = price

    def unrealized_pnl(self) -> float:
        """Calculate unrealized P&L."""
        return (self.current_price - self.entry_price) * self.quantity

    def unrealized_pnl_percent(self) -> float:
        """Calculate unrealized P&L as percentage."""
        return ((self.current_price - self.entry_price) / self.entry_price) * 100

    def market_value(self) -> float:
        """Calculate current market value."""
        return self.current_price * abs(self.quantity)

    def is_long(self) -> bool:
        """Check if position is long."""
        return self.quantity > 0

    def is_short(self) -> bool:
        """Check if position is short."""
        return self.quantity < 0


class RiskManager:
    """
    Central risk management system.

    Validates all trades against risk rules and manages portfolio risk.
    """

    def __init__(self, config: RiskConfig, initial_capital: float):
        """
        Initialize risk manager.

        Args:
            config: Risk configuration
            initial_capital: Starting capital
        """
        self.config = config
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.peak_capital = initial_capital

        self.positions: Dict[str, Position] = {}
        self.daily_pnl: float = 0.0
        self.total_pnl: float = 0.0

        self.trades_today: int = 0
        self.consecutive_losses: int = 0
        self.last_trade_time: Optional[datetime] = None

        self.is_trading_halted = False
        self.halt_reason: Optional[str] = None

        logger.info(
            "risk_manager_initialized",
            initial_capital=initial_capital,
            max_drawdown=config.max_drawdown
        )

    def validate_trade(
        self,
        symbol: str,
        quantity: float,
        price: float,
        side: str,
        current_portfolio_value: float
    ) -> Dict[str, Any]:
        """
        Validate a proposed trade against risk rules.

        Args:
            symbol: Trading symbol
            quantity: Number of shares/contracts
            price: Entry price
            side: "buy" or "sell"
            current_portfolio_value: Current total portfolio value

        Returns:
            Dictionary with validation result:
            {
                "approved": bool,
                "reason": str,
                "adjusted_quantity": float (if position size reduced),
                "warnings": List[str]
            }
        """
        warnings = []
        adjusted_quantity = quantity

        # Check if trading is halted
        if self.is_trading_halted:
            return {
                "approved": False,
                "reason": f"Trading halted: {self.halt_reason}",
                "adjusted_quantity": 0,
                "warnings": []
            }

        # Check daily loss limit
        if self._check_daily_loss_limit():
            return {
                "approved": False,
                "reason": "Daily loss limit reached",
                "adjusted_quantity": 0,
                "warnings": []
            }

        # Check maximum drawdown
        if self._check_max_drawdown():
            self.halt_trading("Maximum drawdown exceeded")
            return {
                "approved": False,
                "reason": "Maximum drawdown exceeded - trading halted",
                "adjusted_quantity": 0,
                "warnings": []
            }

        # Check position size limits
        trade_value = abs(quantity * price)
        max_position_value = current_portfolio_value * self.config.max_position_size

        if trade_value > max_position_value:
            adjusted_quantity = int(max_position_value / price)
            warnings.append(
                f"Position size reduced from {quantity} to {adjusted_quantity} "
                f"to comply with max position size limit"
            )

        # Check if this would exceed maximum positions
        if symbol not in self.positions and len(self.positions) >= self.config.max_positions:
            return {
                "approved": False,
                "reason": f"Maximum number of positions ({self.config.max_positions}) reached",
                "adjusted_quantity": 0,
                "warnings": warnings
            }

        # Check concentration risk (single position)
        if symbol in self.positions:
            existing_position = self.positions[symbol]
            total_quantity = existing_position.quantity + (quantity if side == "buy" else -quantity)
            new_value = abs(total_quantity * price)
            max_single_stock_value = current_portfolio_value * self.config.max_single_stock

            if new_value > max_single_stock_value:
                warnings.append(
                    f"Trade would exceed maximum single stock allocation "
                    f"({self.config.max_single_stock * 100}%)"
                )
                # Reduce quantity
                max_additional = (max_single_stock_value - existing_position.market_value()) / price
                adjusted_quantity = max(0, int(max_additional))

        # Check leverage
        if self.config.max_leverage < 1.0:
            warnings.append(f"Leverage limited to {self.config.max_leverage}x")

        # Final approval
        if adjusted_quantity <= 0:
            return {
                "approved": False,
                "reason": "Adjusted position size is zero or negative",
                "adjusted_quantity": 0,
                "warnings": warnings
            }

        logger.info(
            "trade_validated",
            symbol=symbol,
            original_quantity=quantity,
            adjusted_quantity=adjusted_quantity,
            approved=True
        )

        return {
            "approved": True,
            "reason": "Trade approved",
            "adjusted_quantity": adjusted_quantity,
            "warnings": warnings
        }

    def open_position(
        self,
        symbol: str,
        quantity: float,
        entry_price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> None:
        """
        Record a new position being opened.

        Args:
            symbol: Trading symbol
            quantity: Position size (positive for long, negative for short)
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
        """
        position = Position(
            symbol=symbol,
            quantity=quantity,
            entry_price=entry_price,
            entry_time=datetime.now(),
            stop_loss=stop_loss,
            take_profit=take_profit
        )

        self.positions[symbol] = position
        self.last_trade_time = datetime.now()

        logger.info(
            "position_opened",
            symbol=symbol,
            quantity=quantity,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit
        )

    def close_position(
        self,
        symbol: str,
        exit_price: float,
        reason: str = "manual"
    ) -> Dict[str, Any]:
        """
        Close a position and calculate P&L.

        Args:
            symbol: Trading symbol
            exit_price: Exit price
            reason: Reason for closing

        Returns:
            Position details with P&L
        """
        if symbol not in self.positions:
            logger.warning("attempted_to_close_nonexistent_position", symbol=symbol)
            return {}

        position = self.positions[symbol]
        pnl = (exit_price - position.entry_price) * position.quantity
        pnl_percent = ((exit_price - position.entry_price) / position.entry_price) * 100

        # Update capital and P&L tracking
        self.current_capital += pnl
        self.daily_pnl += pnl
        self.total_pnl += pnl
        self.trades_today += 1

        # Update peak capital
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital

        # Track consecutive losses
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0

        # Check circuit breaker
        if (self.config.circuit_breaker.get("enabled", False) and
            self.consecutive_losses >= self.config.circuit_breaker.get("consecutive_losses", 5)):
            cooldown = self.config.circuit_breaker.get("cooldown_minutes", 60)
            self.halt_trading(f"Circuit breaker: {self.consecutive_losses} consecutive losses")

        result = {
            "symbol": symbol,
            "quantity": position.quantity,
            "entry_price": position.entry_price,
            "exit_price": exit_price,
            "pnl": pnl,
            "pnl_percent": pnl_percent,
            "hold_time": datetime.now() - position.entry_time,
            "reason": reason
        }

        # Remove position
        del self.positions[symbol]

        logger.info(
            "position_closed",
            symbol=symbol,
            pnl=pnl,
            pnl_percent=pnl_percent,
            reason=reason
        )

        return result

    def update_position_price(self, symbol: str, current_price: float) -> Optional[str]:
        """
        Update position with current price and check stop loss/take profit.

        Args:
            symbol: Trading symbol
            current_price: Current market price

        Returns:
            Action to take: "stop_loss", "take_profit", or None
        """
        if symbol not in self.positions:
            return None

        position = self.positions[symbol]
        position.update_price(current_price)

        # Check stop loss
        if position.stop_loss:
            if position.is_long() and current_price <= position.stop_loss:
                return "stop_loss"
            elif position.is_short() and current_price >= position.stop_loss:
                return "stop_loss"

        # Check take profit
        if position.take_profit:
            if position.is_long() and current_price >= position.take_profit:
                return "take_profit"
            elif position.is_short() and current_price <= position.take_profit:
                return "take_profit"

        return None

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get current portfolio summary.

        Returns:
            Dictionary with portfolio statistics
        """
        total_market_value = sum(pos.market_value() for pos in self.positions.values())
        total_unrealized_pnl = sum(pos.unrealized_pnl() for pos in self.positions.values())
        current_drawdown = self._calculate_drawdown()

        return {
            "current_capital": self.current_capital,
            "initial_capital": self.initial_capital,
            "total_pnl": self.total_pnl,
            "total_pnl_percent": (self.total_pnl / self.initial_capital) * 100,
            "daily_pnl": self.daily_pnl,
            "unrealized_pnl": total_unrealized_pnl,
            "positions_value": total_market_value,
            "num_positions": len(self.positions),
            "max_positions": self.config.max_positions,
            "current_drawdown": current_drawdown,
            "max_drawdown_limit": self.config.max_drawdown,
            "trades_today": self.trades_today,
            "consecutive_losses": self.consecutive_losses,
            "is_trading_halted": self.is_trading_halted,
            "halt_reason": self.halt_reason
        }

    def _check_daily_loss_limit(self) -> bool:
        """Check if daily loss limit has been reached."""
        daily_loss_limit = self.initial_capital * self.config.daily_loss_limit
        return self.daily_pnl < -daily_loss_limit

    def _check_max_drawdown(self) -> bool:
        """Check if maximum drawdown has been exceeded."""
        drawdown = self._calculate_drawdown()
        return drawdown > self.config.max_drawdown

    def _calculate_drawdown(self) -> float:
        """Calculate current drawdown from peak."""
        if self.peak_capital == 0:
            return 0.0
        return (self.peak_capital - self.current_capital) / self.peak_capital

    def halt_trading(self, reason: str) -> None:
        """
        Halt all trading.

        Args:
            reason: Reason for halting
        """
        self.is_trading_halted = True
        self.halt_reason = reason
        logger.warning("trading_halted", reason=reason)

    def resume_trading(self) -> None:
        """Resume trading after halt."""
        self.is_trading_halted = False
        self.halt_reason = None
        logger.info("trading_resumed")

    def reset_daily_stats(self) -> None:
        """Reset daily statistics (call at start of each trading day)."""
        self.daily_pnl = 0.0
        self.trades_today = 0
        logger.info("daily_stats_reset")
