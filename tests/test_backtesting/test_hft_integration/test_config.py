"""Tests for MNQ configuration classes."""

from decimal import Decimal

import pytest

from src.strategy_lab.backtesting.hft_integration.config import (
    CommissionStructure,
    ConfigBuilder,
    MNQConfig,
    TradingHours,
    create_default_mnq_config,
    create_high_frequency_config,
    create_scalping_config,
    create_testing_config,
)


class TestCommissionStructure:
    """Test commission structure calculations."""

    def test_default_commission(self):
        """Test default commission values."""
        commission = CommissionStructure()

        assert commission.commission_per_contract == Decimal("0.25")
        assert commission.cme_fee == Decimal("0.10")
        assert commission.nfa_fee == Decimal("0.02")
        assert commission.regulatory_fee_rate == Decimal("0.0000238")

    def test_commission_calculation(self):
        """Test total commission calculation."""
        commission = CommissionStructure()

        # Test 1 contract with $13,000 notional value
        contracts = 1
        notional_value = Decimal("13000.00")

        total = commission.calculate_total_commission(contracts, notional_value)

        # Expected: 0.25 + 0.10 + 0.02 + (13000 * 0.0000238)
        expected = (
            Decimal("0.25")
            + Decimal("0.10")
            + Decimal("0.02")
            + (notional_value * Decimal("0.0000238"))
        )

        assert total == expected
        assert total > Decimal("0.37")  # At least base fees

    def test_multiple_contracts(self):
        """Test commission for multiple contracts."""
        commission = CommissionStructure()

        contracts = 5
        notional_value = Decimal("65000.00")  # 5 * $13,000

        total = commission.calculate_total_commission(contracts, notional_value)

        # Per-contract fees should scale
        base_per_contract = Decimal("0.25") + Decimal("0.10") + Decimal("0.02")
        expected_base = base_per_contract * contracts
        expected_regulatory = notional_value * Decimal("0.0000238")

        assert total == expected_base + expected_regulatory


class TestTradingHours:
    """Test trading hours configuration."""

    def test_default_trading_hours(self):
        """Test default trading hours values."""
        hours = TradingHours()

        # RTH (Regular Trading Hours)
        assert hours.rth_start_hour == 9
        assert hours.rth_start_minute == 30
        assert hours.rth_end_hour == 16
        assert hours.rth_end_minute == 0

        # ETH (Extended Trading Hours)
        assert hours.eth_start_hour == 18
        assert hours.eth_start_minute == 0
        assert hours.eth_end_hour == 17
        assert hours.eth_end_minute == 0

        assert hours.timezone == "America/New_York"


class TestMNQConfig:
    """Test MNQ configuration class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = MNQConfig()

        assert config.symbol == "MNQ"
        assert config.name == "Micro E-mini NASDAQ-100"
        assert config.exchange == "CME"
        assert config.currency == "USD"

        # Contract specifications
        assert config.tick_size == Decimal("0.25")
        assert config.contract_multiplier == Decimal("2.0")
        assert config.min_tick_value == Decimal("0.50")

        # Margin requirements
        assert config.initial_margin == Decimal("800.00")
        assert config.maintenance_margin == Decimal("600.00")

        # Position limits
        assert config.position_limit == 1000
        assert config.max_order_size == 100

        # Market data
        assert config.enable_level1 is True
        assert config.enable_level2 is True
        assert config.book_depth == 10

    def test_post_init(self):
        """Test post-initialization setup."""
        config = MNQConfig()

        # Check that nested objects are created
        assert config.commission is not None
        assert isinstance(config.commission, CommissionStructure)

        assert config.trading_hours is not None
        assert isinstance(config.trading_hours, TradingHours)

        assert config.tick_size_table is not None
        assert len(config.tick_size_table) == 3

    def test_tick_size_table(self):
        """Test tick size table functionality."""
        config = MNQConfig()

        # Test different price levels
        assert config.get_tick_size_for_price(Decimal("100")) == Decimal("0.25")
        assert config.get_tick_size_for_price(Decimal("500")) == Decimal("0.50")
        assert config.get_tick_size_for_price(Decimal("1000")) == Decimal("1.00")
        assert config.get_tick_size_for_price(Decimal("1500")) == Decimal("1.00")

    def test_hftbacktest_config_conversion(self):
        """Test conversion to hftbacktest format."""
        config = MNQConfig()
        hft_config = config.to_hftbacktest_config()

        assert hft_config["symbol"] == "MNQ"
        assert hft_config["tick_size"] == 0.25
        assert hft_config["lot_size"] == 2.0
        assert hft_config["position_limit"] == 1000
        assert hft_config["enable_level2"] is True

    def test_config_validation_success(self):
        """Test successful configuration validation."""
        config = MNQConfig()
        assert config.validate_config() is True

    def test_config_validation_failures(self):
        """Test configuration validation failures."""

        # Invalid tick size
        config = MNQConfig(tick_size=Decimal("0"))
        with pytest.raises(ValueError, match="tick_size must be positive"):
            config.validate_config()

        # Invalid margin relationship
        config = MNQConfig(
            initial_margin=Decimal("500"), maintenance_margin=Decimal("600")
        )
        with pytest.raises(
            ValueError, match="initial_margin must be >= maintenance_margin"
        ):
            config.validate_config()

        # Invalid position limit
        config = MNQConfig(position_limit=0)
        with pytest.raises(ValueError, match="position_limit must be positive"):
            config.validate_config()

        # Invalid latency configuration
        config = MNQConfig(min_latency_ns=100_000, max_latency_ns=50_000)
        with pytest.raises(ValueError, match="min_latency_ns must be < max_latency_ns"):
            config.validate_config()


class TestConfigBuilder:
    """Test configuration builder pattern."""

    def test_builder_basic(self):
        """Test basic builder functionality."""
        config = (
            ConfigBuilder().with_symbol("TEST").with_tick_size(Decimal("0.50")).build()
        )

        assert config.symbol == "TEST"
        assert config.tick_size == Decimal("0.50")

    def test_builder_complete(self):
        """Test complete builder configuration."""
        commission = CommissionStructure(commission_per_contract=Decimal("0.50"))

        config = (
            ConfigBuilder()
            .with_symbol("TEST")
            .with_tick_size(Decimal("1.00"))
            .with_contract_multiplier(Decimal("5.0"))
            .with_margin(Decimal("1000"), Decimal("800"))
            .with_commission(commission)
            .with_latency(10_000, 50_000)
            .with_position_limits(500, 50)
            .with_market_data(enable_l1=True, enable_l2=False, depth=5)
            .enable_simulation_features(latency=False, market_impact=False)
            .build()
        )

        assert config.symbol == "TEST"
        assert config.tick_size == Decimal("1.00")
        assert config.contract_multiplier == Decimal("5.0")
        assert config.initial_margin == Decimal("1000")
        assert config.maintenance_margin == Decimal("800")
        assert config.commission.commission_per_contract == Decimal("0.50")
        assert config.min_latency_ns == 10_000
        assert config.max_latency_ns == 50_000
        assert config.position_limit == 500
        assert config.max_order_size == 50
        assert config.enable_level1 is True
        assert config.enable_level2 is False
        assert config.book_depth == 5
        assert config.latency_simulation is False
        assert config.enable_market_impact is False

    def test_builder_validation(self):
        """Test builder validation."""
        with pytest.raises(ValueError):
            (ConfigBuilder().with_tick_size(Decimal("0")).build())  # Invalid


class TestPredefinedConfigs:
    """Test predefined configuration functions."""

    def test_default_config(self):
        """Test default configuration creation."""
        config = create_default_mnq_config()

        assert config.symbol == "MNQ"
        assert config.validate_config() is True

    def test_high_frequency_config(self):
        """Test high-frequency trading configuration."""
        config = create_high_frequency_config()

        assert config.min_latency_ns == 10_000
        assert config.max_latency_ns == 100_000
        assert config.book_depth == 20
        assert config.latency_simulation is True
        assert config.enable_market_impact is True

    def test_scalping_config(self):
        """Test scalping configuration."""
        config = create_scalping_config()

        assert config.position_limit == 50
        assert config.max_order_size == 10
        assert config.min_latency_ns == 25_000
        assert config.max_latency_ns == 200_000

    def test_testing_config(self):
        """Test testing configuration."""
        config = create_testing_config()

        assert config.commission.commission_per_contract == Decimal("0.10")
        assert config.position_limit == 10
        assert config.max_order_size == 5
        assert config.latency_simulation is False
        assert config.enable_market_impact is False
