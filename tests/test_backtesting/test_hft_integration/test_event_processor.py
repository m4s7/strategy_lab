"""Tests for HftEventProcessor class."""


from src.strategy_lab.backtesting.hft_integration.config import create_testing_config
from src.strategy_lab.backtesting.hft_integration.event_processor import (
    Fill,
    HftEventProcessor,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    PerformanceMetrics,
    Position,
    create_simple_order_manager,
    simulate_market_order_execution,
)


class TestOrderEnums:
    """Test order-related enums."""

    def test_order_type_enum(self):
        """Test OrderType enum values."""
        assert OrderType.MARKET.value == "market"
        assert OrderType.LIMIT.value == "limit"
        assert OrderType.STOP.value == "stop"
        assert OrderType.STOP_LIMIT.value == "stop_limit"

    def test_order_status_enum(self):
        """Test OrderStatus enum values."""
        assert OrderStatus.PENDING.value == "pending"
        assert OrderStatus.FILLED.value == "filled"
        assert OrderStatus.PARTIALLY_FILLED.value == "partially_filled"
        assert OrderStatus.CANCELLED.value == "cancelled"
        assert OrderStatus.REJECTED.value == "rejected"

    def test_order_side_enum(self):
        """Test OrderSide enum values."""
        assert OrderSide.BUY.value == 1
        assert OrderSide.SELL.value == -1


class TestOrder:
    """Test Order class functionality."""

    def test_order_creation(self):
        """Test basic order creation."""
        order = Order(
            order_id=1,
            timestamp=1609459200000000000,
            symbol="MNQ",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=5,
        )

        assert order.order_id == 1
        assert order.symbol == "MNQ"
        assert order.side == OrderSide.BUY
        assert order.quantity == 5
        assert order.status == OrderStatus.PENDING
        assert order.filled_quantity == 0

    def test_remaining_quantity(self):
        """Test remaining quantity calculation."""
        order = Order(
            order_id=1,
            timestamp=1609459200000000000,
            symbol="MNQ",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=10,
            filled_quantity=3,
        )

        assert order.remaining_quantity == 7

    def test_is_complete(self):
        """Test order completion check."""
        order = Order(
            order_id=1,
            timestamp=1609459200000000000,
            symbol="MNQ",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=10,
        )

        assert order.is_complete is False

        order.filled_quantity = 10
        assert order.is_complete is True

        order.filled_quantity = 5
        order.status = OrderStatus.FILLED
        assert order.is_complete is True

    def test_to_hftbacktest_order(self):
        """Test conversion to hftbacktest order format."""
        order = Order(
            order_id=1,
            timestamp=1609459200000000000,
            symbol="MNQ",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=5,
            price=13000.25,
        )

        hft_order = order.to_hftbacktest_order()

        expected = {
            "order_id": 1,
            "timestamp": 1609459200000000000,
            "side": 1,
            "qty": 5,
            "price": 13000.25,
            "order_type": "limit",
        }

        assert hft_order == expected


class TestFill:
    """Test Fill class functionality."""

    def test_fill_creation(self):
        """Test basic fill creation."""
        fill = Fill(
            order_id=1,
            timestamp=1609459200000000000,
            price=13000.25,
            quantity=5,
            side=OrderSide.BUY,
            commission=1.25,
        )

        assert fill.order_id == 1
        assert fill.price == 13000.25
        assert fill.quantity == 5
        assert fill.side == OrderSide.BUY
        assert fill.commission == 1.25

    def test_notional_value(self):
        """Test notional value calculation."""
        fill = Fill(
            order_id=1,
            timestamp=1609459200000000000,
            price=13000.25,
            quantity=5,
            side=OrderSide.BUY,
        )

        assert fill.notional_value == 13000.25 * 5


class TestPosition:
    """Test Position class functionality."""

    def test_position_creation(self):
        """Test basic position creation."""
        position = Position(symbol="MNQ")

        assert position.symbol == "MNQ"
        assert position.quantity == 0
        assert position.average_price == 0.0
        assert position.realized_pnl == 0.0
        assert position.unrealized_pnl == 0.0
        assert position.total_commission == 0.0

    def test_position_properties(self):
        """Test position properties."""
        position = Position(symbol="MNQ")

        # Flat position
        assert position.is_flat is True
        assert position.is_long is False
        assert position.is_short is False

        # Long position
        position.quantity = 5
        assert position.is_flat is False
        assert position.is_long is True
        assert position.is_short is False

        # Short position
        position.quantity = -3
        assert position.is_flat is False
        assert position.is_long is False
        assert position.is_short is True

    def test_market_value(self):
        """Test market value calculation."""
        position = Position(symbol="MNQ", quantity=5, average_price=13000.25)

        expected_value = 5 * 13000.25
        assert position.market_value == expected_value

    def test_update_position_opening(self):
        """Test updating position when opening."""
        position = Position(symbol="MNQ")

        fill = Fill(
            order_id=1,
            timestamp=1609459200000000000,
            price=13000.25,
            quantity=5,
            side=OrderSide.BUY,
            commission=1.25,
        )

        position.update_position(fill)

        assert position.quantity == 5
        assert position.average_price == 13000.25
        assert position.total_commission == 1.25

    def test_update_position_adding(self):
        """Test updating position when adding to existing."""
        position = Position(symbol="MNQ", quantity=3, average_price=13000.00)

        fill = Fill(
            order_id=1,
            timestamp=1609459200000000000,
            price=13001.00,
            quantity=2,
            side=OrderSide.BUY,
            commission=1.25,
        )

        position.update_position(fill)

        # Should have 5 contracts total
        assert position.quantity == 5

        # Average price should be weighted average
        expected_avg = (3 * 13000.00 + 2 * 13001.00) / 5
        assert abs(position.average_price - expected_avg) < 0.01

    def test_update_position_closing(self):
        """Test updating position when closing."""
        position = Position(symbol="MNQ", quantity=5, average_price=13000.00)

        # Close entire position
        fill = Fill(
            order_id=1,
            timestamp=1609459200000000000,
            price=13001.00,
            quantity=5,
            side=OrderSide.SELL,
            commission=1.25,
        )

        position.update_position(fill)

        assert position.quantity == 0
        assert position.average_price == 0.0
        assert position.realized_pnl > 0  # Made profit


class TestPerformanceMetrics:
    """Test PerformanceMetrics class functionality."""

    def test_metrics_creation(self):
        """Test basic metrics creation."""
        metrics = PerformanceMetrics()

        assert metrics.orders_submitted == 0
        assert metrics.orders_filled == 0
        assert metrics.total_fills == 0
        assert metrics.realized_pnl == 0.0
        assert metrics.end_time is None

    def test_duration_calculation(self):
        """Test duration calculation."""
        metrics = PerformanceMetrics()
        metrics.start_time = 100.0
        metrics.end_time = 105.0

        assert metrics.duration == 5.0

    def test_fill_rate_calculation(self):
        """Test fill rate calculation."""
        metrics = PerformanceMetrics()

        # No orders submitted
        assert metrics.fill_rate == 0.0

        # Some orders filled
        metrics.orders_submitted = 10
        metrics.orders_filled = 8

        assert metrics.fill_rate == 80.0

    def test_average_latencies(self):
        """Test average latency calculations."""
        metrics = PerformanceMetrics()

        # No latencies recorded
        assert metrics.average_order_latency == 0.0
        assert metrics.average_fill_latency == 0.0

        # Some latencies
        metrics.order_latencies = [1000, 2000, 3000]
        metrics.fill_latencies = [500, 1500]

        assert metrics.average_order_latency == 2000.0
        assert metrics.average_fill_latency == 1000.0


class TestHftEventProcessor:
    """Test HftEventProcessor class functionality."""

    def test_processor_creation(self):
        """Test basic processor creation."""
        config = create_testing_config()
        processor = HftEventProcessor(config)

        assert processor.config == config
        assert len(processor.orders) == 0
        assert len(processor.positions) == 0
        assert len(processor.fills) == 0
        assert isinstance(processor.metrics, PerformanceMetrics)

    def test_generate_order_id(self):
        """Test order ID generation."""
        config = create_testing_config()
        processor = HftEventProcessor(config)

        # Should generate sequential IDs
        id1 = processor.generate_order_id()
        id2 = processor.generate_order_id()

        assert id1 == 1
        assert id2 == 2

    def test_submit_market_order_valid(self):
        """Test submitting valid market order."""
        config = create_testing_config()
        processor = HftEventProcessor(config)

        order = processor.submit_order(
            timestamp=1609459200000000000,
            side=OrderSide.BUY,
            quantity=5,
            order_type=OrderType.MARKET,
        )

        assert order.status == OrderStatus.PENDING
        assert order.order_id in processor.orders
        assert processor.metrics.orders_submitted == 1

    def test_submit_limit_order_valid(self):
        """Test submitting valid limit order."""
        config = create_testing_config()
        processor = HftEventProcessor(config)

        order = processor.submit_order(
            timestamp=1609459200000000000,
            side=OrderSide.BUY,
            quantity=5,
            order_type=OrderType.LIMIT,
            price=13000.25,
        )

        assert order.status == OrderStatus.PENDING
        assert order.price == 13000.25

    def test_submit_order_invalid_quantity(self):
        """Test submitting order with invalid quantity."""
        config = create_testing_config()
        processor = HftEventProcessor(config)

        order = processor.submit_order(
            timestamp=1609459200000000000,
            side=OrderSide.BUY,
            quantity=0,  # Invalid
            order_type=OrderType.MARKET,
        )

        assert order.status == OrderStatus.REJECTED
        assert processor.metrics.orders_rejected == 1

    def test_submit_order_exceeds_size_limit(self):
        """Test submitting order that exceeds size limit."""
        config = create_testing_config()
        processor = HftEventProcessor(config)

        order = processor.submit_order(
            timestamp=1609459200000000000,
            side=OrderSide.BUY,
            quantity=config.max_order_size + 1,  # Exceeds limit
            order_type=OrderType.MARKET,
        )

        assert order.status == OrderStatus.REJECTED

    def test_submit_order_exceeds_position_limit(self):
        """Test submitting order that would exceed position limit."""
        config = create_testing_config()
        config.position_limit = 5  # Low limit for testing
        processor = HftEventProcessor(config)

        # Create existing position
        processor.positions["MNQ"] = Position(symbol="MNQ", quantity=4)

        # Try to add more than position limit allows
        order = processor.submit_order(
            timestamp=1609459200000000000,
            side=OrderSide.BUY,
            quantity=3,  # Would result in position of 7, exceeding limit of 5
            order_type=OrderType.MARKET,
        )

        assert order.status == OrderStatus.REJECTED

    def test_process_fill_valid(self):
        """Test processing valid fill."""
        config = create_testing_config()
        processor = HftEventProcessor(config)

        # Submit order first
        order = processor.submit_order(
            timestamp=1609459200000000000,
            side=OrderSide.BUY,
            quantity=5,
            order_type=OrderType.MARKET,
        )

        # Process fill
        fill = processor.process_fill(
            order_id=order.order_id,
            timestamp=1609459200001000000,
            fill_price=13000.25,
            fill_quantity=5,
        )

        assert fill is not None
        assert fill.price == 13000.25
        assert fill.quantity == 5
        assert order.status == OrderStatus.FILLED
        assert order.filled_quantity == 5
        assert processor.metrics.total_fills == 1

    def test_process_fill_partial(self):
        """Test processing partial fill."""
        config = create_testing_config()
        config.max_order_size = 20  # Increase limit for this test
        processor = HftEventProcessor(config)

        # Submit order for 10 contracts
        order = processor.submit_order(
            timestamp=1609459200000000000,
            side=OrderSide.BUY,
            quantity=10,
            order_type=OrderType.MARKET,
        )

        # Process partial fill of 3 contracts
        fill = processor.process_fill(
            order_id=order.order_id,
            timestamp=1609459200001000000,
            fill_price=13000.25,
            fill_quantity=3,
        )

        assert fill is not None
        assert order.status == OrderStatus.PARTIALLY_FILLED
        assert order.filled_quantity == 3
        assert order.remaining_quantity == 7

    def test_process_fill_unknown_order(self):
        """Test processing fill for unknown order."""
        config = create_testing_config()
        processor = HftEventProcessor(config)

        fill = processor.process_fill(
            order_id=999,  # Unknown order ID
            timestamp=1609459200001000000,
            fill_price=13000.25,
            fill_quantity=5,
        )

        assert fill is None

    def test_cancel_order_valid(self):
        """Test canceling valid order."""
        config = create_testing_config()
        processor = HftEventProcessor(config)

        # Submit order
        order = processor.submit_order(
            timestamp=1609459200000000000,
            side=OrderSide.BUY,
            quantity=5,
            order_type=OrderType.LIMIT,
            price=13000.25,
        )

        # Cancel order
        success = processor.cancel_order(order.order_id, 1609459200001000000)

        assert success is True
        assert order.status == OrderStatus.CANCELLED
        assert processor.metrics.orders_cancelled == 1

    def test_cancel_order_unknown(self):
        """Test canceling unknown order."""
        config = create_testing_config()
        processor = HftEventProcessor(config)

        success = processor.cancel_order(999, 1609459200001000000)

        assert success is False

    def test_cancel_order_completed(self):
        """Test canceling completed order."""
        config = create_testing_config()
        processor = HftEventProcessor(config)

        # Submit and fill order
        order = processor.submit_order(
            timestamp=1609459200000000000,
            side=OrderSide.BUY,
            quantity=5,
            order_type=OrderType.MARKET,
        )

        processor.process_fill(
            order_id=order.order_id,
            timestamp=1609459200001000000,
            fill_price=13000.25,
            fill_quantity=5,
        )

        # Try to cancel filled order
        success = processor.cancel_order(order.order_id, 1609459200002000000)

        assert success is False

    def test_get_position(self):
        """Test getting position."""
        config = create_testing_config()
        processor = HftEventProcessor(config)

        # Get position for symbol that doesn't exist
        position = processor.get_position("MNQ")

        assert position.symbol == "MNQ"
        assert position.is_flat is True
        assert "MNQ" in processor.positions

    def test_update_unrealized_pnl(self):
        """Test updating unrealized PnL."""
        config = create_testing_config()
        processor = HftEventProcessor(config)

        # Create position
        processor.positions["MNQ"] = Position(
            symbol="MNQ", quantity=5, average_price=13000.00
        )

        # Update unrealized PnL with new price
        processor.update_unrealized_pnl(13001.00)

        position = processor.positions["MNQ"]
        expected_pnl = 5 * (13001.00 - 13000.00)

        assert abs(position.unrealized_pnl - expected_pnl) < 0.01
        assert processor.metrics.unrealized_pnl == position.unrealized_pnl

    def test_get_open_orders(self):
        """Test getting open orders."""
        config = create_testing_config()
        processor = HftEventProcessor(config)

        # Submit some orders
        order1 = processor.submit_order(
            timestamp=1609459200000000000,
            side=OrderSide.BUY,
            quantity=5,
            order_type=OrderType.LIMIT,
            price=13000.25,
        )

        order2 = processor.submit_order(
            timestamp=1609459200001000000,
            side=OrderSide.SELL,
            quantity=3,
            order_type=OrderType.LIMIT,
            price=13001.00,
        )

        # Fill one order
        processor.process_fill(
            order_id=order1.order_id,
            timestamp=1609459200002000000,
            fill_price=13000.25,
            fill_quantity=5,
        )

        open_orders = processor.get_open_orders()

        assert len(open_orders) == 1
        assert open_orders[0].order_id == order2.order_id

    def test_reset(self):
        """Test resetting processor state."""
        config = create_testing_config()
        processor = HftEventProcessor(config)

        # Add some state
        processor.submit_order(
            timestamp=1609459200000000000,
            side=OrderSide.BUY,
            quantity=5,
            order_type=OrderType.MARKET,
        )

        processor.positions["MNQ"] = Position(symbol="MNQ", quantity=5)
        processor.fills.append(Fill(1, 1609459200000000000, 13000.25, 5, OrderSide.BUY))

        # Reset
        processor.reset()

        assert len(processor.orders) == 0
        assert len(processor.positions) == 0
        assert len(processor.fills) == 0
        assert processor.metrics.orders_submitted == 0
        assert processor._next_order_id == 1


class TestUtilityFunctions:
    """Test utility functions."""

    def test_create_simple_order_manager(self):
        """Test creating simple order manager."""
        config = create_testing_config()
        processor = create_simple_order_manager(config)

        assert isinstance(processor, HftEventProcessor)
        assert processor.on_order_filled is not None
        assert processor.on_position_updated is not None
        assert processor.on_order_rejected is not None

    def test_simulate_market_order_execution(self):
        """Test simulating market order execution."""
        config = create_testing_config()
        processor = HftEventProcessor(config)

        fill = simulate_market_order_execution(
            processor=processor,
            timestamp=1609459200000000000,
            side=OrderSide.BUY,
            quantity=5,
            execution_price=13000.25,
        )

        assert fill is not None
        assert fill.price == 13000.25
        assert fill.quantity == 5
        assert fill.side == OrderSide.BUY

        # Check that order was created and filled
        assert processor.metrics.orders_submitted == 1
        assert processor.metrics.orders_filled == 1
