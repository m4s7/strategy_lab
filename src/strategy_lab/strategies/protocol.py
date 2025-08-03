"""Strategy protocol definition for type-safe interfaces."""

from abc import abstractmethod
from typing import Any, Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class StrategyProtocol(Protocol):
    """Protocol defining the required interface for all strategies.

    This protocol ensures type safety and provides a clear contract
    for what methods a strategy must implement.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name identifier."""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """Strategy version string."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable strategy description."""
        ...

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """Current strategy parameters."""
        ...

    @abstractmethod
    def initialize(self, **kwargs) -> None:
        """Initialize strategy state and resources.

        Args:
            **kwargs: Strategy-specific initialization parameters
        """
        ...

    @abstractmethod
    def process_tick(
        self,
        timestamp: pd.Timestamp,
        price: float,
        volume: int,
        bid: float,
        ask: float,
        **kwargs,
    ) -> int | None:
        """Process a market data tick and generate trading signal.

        Args:
            timestamp: Tick timestamp
            price: Current price
            volume: Trade volume
            bid: Best bid price
            ask: Best ask price
            **kwargs: Additional tick data

        Returns:
            Trading signal: 1 (buy), -1 (sell), 0 (flat), None (no action)
        """
        ...

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup strategy resources and save state."""
        ...

    # Optional hooks with default implementations
    def on_trade(self, trade_data: dict[str, Any]) -> None:
        """Hook called when a trade is executed.

        Args:
            trade_data: Trade execution details
        """

    def on_market_open(self) -> None:
        """Hook called when market opens."""

    def on_market_close(self) -> None:
        """Hook called when market closes."""

    def on_session_end(self) -> None:
        """Hook called at end of trading session."""

    def get_state(self) -> dict[str, Any]:
        """Get current strategy state for persistence.

        Returns:
            Dictionary containing strategy state
        """
        return {}

    def set_state(self, state: dict[str, Any]) -> None:
        """Restore strategy state from persistence.

        Args:
            state: Previously saved state dictionary
        """


@runtime_checkable
class IndicatorProtocol(Protocol):
    """Protocol for technical indicators used by strategies."""

    @abstractmethod
    def calculate(self, data: pd.Series) -> pd.Series:
        """Calculate indicator values.

        Args:
            data: Input price series

        Returns:
            Calculated indicator values
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Indicator name."""
        ...

    @property
    @abstractmethod
    def period(self) -> int:
        """Indicator period/lookback."""
        ...


@runtime_checkable
class RiskManagerProtocol(Protocol):
    """Protocol for risk management components."""

    @abstractmethod
    def check_risk(
        self, signal: int, current_position: int, portfolio_value: float
    ) -> bool:
        """Check if trade passes risk criteria.

        Args:
            signal: Proposed trading signal
            current_position: Current position size
            portfolio_value: Current portfolio value

        Returns:
            True if trade is allowed, False otherwise
        """
        ...

    @abstractmethod
    def calculate_position_size(
        self, signal: int, portfolio_value: float, current_price: float
    ) -> int:
        """Calculate appropriate position size.

        Args:
            signal: Trading signal
            portfolio_value: Current portfolio value
            current_price: Current market price

        Returns:
            Position size in contracts
        """
        ...


class StrategyMetadata:
    """Strategy metadata container."""

    def __init__(
        self,
        name: str,
        version: str,
        description: str,
        author: str = "",
        tags: list[str] | None = None,
        parameters: dict[str, Any] | None = None,
        requirements: dict[str, Any] | None = None,
    ):
        """Initialize strategy metadata.

        Args:
            name: Strategy name
            version: Strategy version
            description: Human-readable description
            author: Strategy author
            tags: Strategy classification tags
            parameters: Parameter definitions with defaults
            requirements: System and data requirements
        """
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.tags = tags or []
        self.parameters = parameters or {}
        self.requirements = requirements or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "tags": self.tags,
            "parameters": self.parameters,
            "requirements": self.requirements,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StrategyMetadata":
        """Create metadata from dictionary."""
        return cls(**data)
