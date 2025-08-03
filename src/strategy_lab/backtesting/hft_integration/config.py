"""MNQ contract configuration for hftbacktest integration."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass
class TradingHours:
    """MNQ trading hours configuration."""

    # Regular Trading Hours (RTH)
    rth_start_hour: int = 9
    rth_start_minute: int = 30
    rth_end_hour: int = 16
    rth_end_minute: int = 0

    # Extended Trading Hours (ETH)
    eth_start_hour: int = 18  # 6:00 PM ET (previous day)
    eth_start_minute: int = 0
    eth_end_hour: int = 17  # 5:00 PM ET (next day)
    eth_end_minute: int = 0

    # Session breaks
    break_start_hour: int = 17
    break_start_minute: int = 0
    break_end_hour: int = 18
    break_end_minute: int = 0

    timezone: str = "America/New_York"


@dataclass
class CommissionStructure:
    """Commission and fee structure for MNQ trading."""

    # Per contract commission
    commission_per_contract: Decimal = Decimal("0.25")

    # Exchange fees
    cme_fee: Decimal = Decimal("0.10")
    nfa_fee: Decimal = Decimal("0.02")

    # Regulatory fees
    regulatory_fee_rate: Decimal = Decimal("0.0000238")  # Per dollar traded

    def calculate_total_commission(
        self, contracts: int, notional_value: Decimal
    ) -> Decimal:
        """Calculate total commission and fees for a trade."""
        base_commission = self.commission_per_contract * contracts
        exchange_fees = (self.cme_fee + self.nfa_fee) * contracts
        regulatory_fees = notional_value * self.regulatory_fee_rate

        return base_commission + exchange_fees + regulatory_fees


@dataclass
class MNQConfig:
    """Complete MNQ contract configuration for hftbacktest."""

    # Contract specifications
    symbol: str = "MNQ"
    name: str = "Micro E-mini NASDAQ-100"
    exchange: str = "CME"
    currency: str = "USD"

    # Contract sizing
    tick_size: Decimal = Decimal("0.25")  # $0.25 minimum price increment
    contract_multiplier: Decimal = Decimal("2.0")  # $2 per index point
    min_tick_value: Decimal = Decimal("0.50")  # $0.50 per tick (0.25 * 2)

    # Price level specific tick sizes (for higher prices)
    tick_size_table: dict[Decimal, Decimal] | None = None

    # Margin requirements (example values - adjust based on broker)
    initial_margin: Decimal = Decimal("800.00")  # Per contract
    maintenance_margin: Decimal = Decimal("600.00")  # Per contract

    # Trading constraints
    position_limit: int = 1000  # Maximum position size
    max_order_size: int = 100  # Maximum single order size

    # Market data feed configuration
    enable_level1: bool = True
    enable_level2: bool = True
    book_depth: int = 10

    # Simulation parameters
    latency_simulation: bool = True
    min_latency_ns: int = 50_000  # 50 microseconds
    max_latency_ns: int = 500_000  # 500 microseconds

    # Market impact modeling
    enable_market_impact: bool = True
    impact_coefficient: float = 0.01  # Price impact per contract

    # Commission and fees
    commission: CommissionStructure | None = None

    # Trading hours
    trading_hours: TradingHours | None = None

    def __post_init__(self) -> None:
        """Initialize default nested configurations."""
        if self.commission is None:
            self.commission = CommissionStructure()

        if self.trading_hours is None:
            self.trading_hours = TradingHours()

        if self.tick_size_table is None:
            # MNQ has different tick sizes for different price levels
            self.tick_size_table = {
                Decimal("0"): Decimal("0.25"),  # $0 - $499.99: $0.25
                Decimal("500"): Decimal("0.50"),  # $500 - $999.99: $0.50
                Decimal("1000"): Decimal("1.00"),  # $1000+: $1.00
            }

    def get_tick_size_for_price(self, price: Decimal) -> Decimal:
        """Get the appropriate tick size for a given price level."""
        for price_level in sorted(self.tick_size_table.keys(), reverse=True):
            if price >= price_level:
                return self.tick_size_table[price_level]
        return self.tick_size  # Default tick size

    def to_hftbacktest_config(self) -> dict[str, Any]:
        """Convert to hftbacktest compatible configuration."""
        return {
            "symbol": self.symbol,
            "tick_size": float(self.tick_size),
            "lot_size": float(self.contract_multiplier),
            "initial_margin": float(self.initial_margin),
            "maintenance_margin": float(self.maintenance_margin),
            "commission": float(self.commission.commission_per_contract),
            "min_latency": self.min_latency_ns,
            "max_latency": self.max_latency_ns,
            "position_limit": self.position_limit,
            "max_order_size": self.max_order_size,
            "enable_level2": self.enable_level2,
            "book_depth": self.book_depth,
        }

    def validate_config(self) -> bool:
        """Validate configuration parameters."""
        errors = []

        # Basic validation
        if self.tick_size <= 0:
            errors.append("tick_size must be positive")

        if self.contract_multiplier <= 0:
            errors.append("contract_multiplier must be positive")

        if self.initial_margin < self.maintenance_margin:
            errors.append("initial_margin must be >= maintenance_margin")

        if self.position_limit <= 0:
            errors.append("position_limit must be positive")

        if self.max_order_size <= 0:
            errors.append("max_order_size must be positive")

        if self.min_latency_ns >= self.max_latency_ns:
            errors.append("min_latency_ns must be < max_latency_ns")

        # Trading hours validation
        if self.trading_hours.rth_start_hour >= self.trading_hours.rth_end_hour:
            errors.append("Invalid RTH trading hours")

        if errors:
            msg = "Configuration validation failed: " + "; ".join(errors)
            raise ValueError(msg)

        return True


class ConfigBuilder:
    """Builder pattern for creating MNQ configurations."""

    def __init__(self) -> None:
        self.config = MNQConfig()

    def with_symbol(self, symbol: str) -> "ConfigBuilder":
        """Set contract symbol."""
        self.config.symbol = symbol
        return self

    def with_tick_size(self, tick_size: Decimal) -> "ConfigBuilder":
        """Set tick size."""
        self.config.tick_size = tick_size
        return self

    def with_contract_multiplier(self, multiplier: Decimal) -> "ConfigBuilder":
        """Set contract multiplier."""
        self.config.contract_multiplier = multiplier
        return self

    def with_margin(self, initial: Decimal, maintenance: Decimal) -> "ConfigBuilder":
        """Set margin requirements."""
        self.config.initial_margin = initial
        self.config.maintenance_margin = maintenance
        return self

    def with_commission(self, commission: CommissionStructure) -> "ConfigBuilder":
        """Set commission structure."""
        self.config.commission = commission
        return self

    def with_latency(self, min_ns: int, max_ns: int) -> "ConfigBuilder":
        """Set latency simulation parameters."""
        self.config.min_latency_ns = min_ns
        self.config.max_latency_ns = max_ns
        return self

    def with_position_limits(
        self, position_limit: int, max_order_size: int
    ) -> "ConfigBuilder":
        """Set position and order size limits."""
        self.config.position_limit = position_limit
        self.config.max_order_size = max_order_size
        return self

    def with_market_data(
        self, enable_l1: bool = True, enable_l2: bool = True, depth: int = 10
    ) -> "ConfigBuilder":
        """Configure market data settings."""
        self.config.enable_level1 = enable_l1
        self.config.enable_level2 = enable_l2
        self.config.book_depth = depth
        return self

    def enable_simulation_features(
        self, latency: bool = True, market_impact: bool = True
    ) -> "ConfigBuilder":
        """Enable/disable simulation features."""
        self.config.latency_simulation = latency
        self.config.enable_market_impact = market_impact
        return self

    def build(self) -> MNQConfig:
        """Build and validate the configuration."""
        self.config.validate_config()
        return self.config


# Predefined configurations for common scenarios
def create_default_mnq_config() -> MNQConfig:
    """Create default MNQ configuration for standard backtesting."""
    return ConfigBuilder().build()


def create_high_frequency_config() -> MNQConfig:
    """Create MNQ configuration optimized for high-frequency trading."""
    return (
        ConfigBuilder()
        .with_latency(10_000, 100_000)  # Lower latency
        .with_market_data(enable_l1=True, enable_l2=True, depth=20)  # More depth
        .enable_simulation_features(latency=True, market_impact=True)
        .build()
    )


def create_scalping_config() -> MNQConfig:
    """Create MNQ configuration optimized for scalping strategies."""
    return (
        ConfigBuilder()
        .with_latency(25_000, 200_000)  # Moderate latency
        .with_position_limits(position_limit=50, max_order_size=10)  # Smaller positions
        .with_market_data(enable_l1=True, enable_l2=True, depth=10)
        .enable_simulation_features(latency=True, market_impact=True)
        .build()
    )


def create_testing_config() -> MNQConfig:
    """Create MNQ configuration for testing with relaxed constraints."""
    commission = CommissionStructure(
        commission_per_contract=Decimal("0.10"),  # Lower commission for testing
        cme_fee=Decimal("0.05"),
        nfa_fee=Decimal("0.01"),
    )

    return (
        ConfigBuilder()
        .with_commission(commission)
        .with_latency(1_000, 10_000)  # Very low latency for testing
        .with_position_limits(position_limit=10, max_order_size=5)
        .enable_simulation_features(latency=False, market_impact=False)  # Simplified
        .build()
    )
