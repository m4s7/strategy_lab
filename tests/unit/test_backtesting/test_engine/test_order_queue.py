"""Tests for order queue functionality."""

from decimal import Decimal

import pandas as pd
import pytest

from strategy_lab.backtesting.engine.order_queue import (
    Order,
    OrderQueue,
    OrderStatus,
    OrderType,
)
from strategy_lab.backtesting.engine.portfolio import Portfolio, PositionSide


class TestOrder:
    """Test Order class functionality."""

    def test_order_creation(self):
        """Test basic order creation."""
        order = Order(
            order_id="TEST_001",
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=1,
            order_type=OrderType.MARKET,
        )

        assert order.order_id == "TEST_001"
        assert order.symbol == "MNQ"
        assert order.side == PositionSide.LONG
        assert order.quantity == 1
        assert order.order_type == OrderType.MARKET
        assert order.status == OrderStatus.PENDING
        assert order.is_pending
        assert not order.is_executed
        assert not order.is_cancelled
        assert order.remaining_quantity == 1

    def test_market_order_execution_logic(self):
        """Test market order can always execute."""
        order = Order(
            order_id="TEST_001",
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=1,
            order_type=OrderType.MARKET,
        )

        # Market orders can execute at any price
        assert order.can_execute_at_price(Decimal("4000"))
        assert order.can_execute_at_price(Decimal("5000"))
        assert order.can_execute_at_price(Decimal("3000"))

    def test_limit_order_execution_logic(self):
        """Test limit order execution logic."""
        # Long limit order at 4000
        long_limit = Order(
            order_id="TEST_001",
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=1,
            order_type=OrderType.LIMIT,
            price=Decimal("4000"),
        )

        # Should execute at or below limit price
        assert long_limit.can_execute_at_price(Decimal("3999"))  # Below limit
        assert long_limit.can_execute_at_price(Decimal("4000"))  # At limit
        assert not long_limit.can_execute_at_price(Decimal("4001"))  # Above limit

        # Short limit order at 4000
        short_limit = Order(
            order_id="TEST_002",
            symbol="MNQ",
            side=PositionSide.SHORT,
            quantity=1,
            order_type=OrderType.LIMIT,
            price=Decimal("4000"),
        )

        # Should execute at or above limit price
        assert short_limit.can_execute_at_price(Decimal("4001"))  # Above limit
        assert short_limit.can_execute_at_price(Decimal("4000"))  # At limit
        assert not short_limit.can_execute_at_price(Decimal("3999"))  # Below limit

    def test_stop_order_execution_logic(self):
        """Test stop order execution logic."""
        # Long stop order at 4000 (buy stop)
        long_stop = Order(
            order_id="TEST_001",
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=1,
            order_type=OrderType.STOP,
            stop_price=Decimal("4000"),
        )

        # Should execute at or above stop price
        assert long_stop.can_execute_at_price(Decimal("4001"))  # Above stop
        assert long_stop.can_execute_at_price(Decimal("4000"))  # At stop
        assert not long_stop.can_execute_at_price(Decimal("3999"))  # Below stop

        # Short stop order at 4000 (sell stop)
        short_stop = Order(
            order_id="TEST_002",
            symbol="MNQ",
            side=PositionSide.SHORT,
            quantity=1,
            order_type=OrderType.STOP,
            stop_price=Decimal("4000"),
        )

        # Should execute at or below stop price
        assert short_stop.can_execute_at_price(Decimal("3999"))  # Below stop
        assert short_stop.can_execute_at_price(Decimal("4000"))  # At stop
        assert not short_stop.can_execute_at_price(Decimal("4001"))  # Above stop

    def test_order_expiration(self):
        """Test order expiration logic."""
        expiry_time = pd.Timestamp("2024-01-01 12:00:00")
        order = Order(
            order_id="TEST_001",
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=1,
            expires_at=expiry_time,
        )

        # Before expiry
        assert not order.is_expired(pd.Timestamp("2024-01-01 11:59:59"))
        # At expiry
        assert order.is_expired(pd.Timestamp("2024-01-01 12:00:00"))
        # After expiry
        assert order.is_expired(pd.Timestamp("2024-01-01 12:00:01"))

        # Order without expiry never expires
        no_expiry_order = Order(
            order_id="TEST_002",
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=1,
        )
        assert not no_expiry_order.is_expired(pd.Timestamp("2030-01-01"))


class TestOrderQueue:
    """Test OrderQueue functionality."""

    def test_queue_initialization(self):
        """Test order queue initialization."""
        queue = OrderQueue(batch_size=5, process_interval=50)

        assert queue.batch_size == 5
        assert queue.process_interval == 50
        assert queue.get_pending_orders_count() == 0
        assert queue.total_orders_submitted == 0
        assert queue.total_orders_executed == 0
        assert queue.total_orders_cancelled == 0

    def test_submit_order(self):
        """Test order submission."""
        queue = OrderQueue()

        order_id = queue.submit_order(
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=1,
            order_type=OrderType.MARKET,
        )

        assert order_id.startswith("ORD_")
        assert queue.get_pending_orders_count() == 1
        assert queue.total_orders_submitted == 1
        assert queue.get_order_status(order_id) == OrderStatus.PENDING

    def test_cancel_order(self):
        """Test order cancellation."""
        queue = OrderQueue()

        order_id = queue.submit_order(
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=1,
        )

        # Cancel the order
        assert queue.cancel_order(order_id)
        assert queue.get_pending_orders_count() == 0
        assert queue.total_orders_cancelled == 1
        assert queue.get_order_status(order_id) == OrderStatus.CANCELLED

        # Try to cancel again - should fail
        assert not queue.cancel_order(order_id)

    def test_batch_processing_trigger(self):
        """Test batch processing trigger logic."""
        queue = OrderQueue(batch_size=3, process_interval=10)

        # Not enough orders or time
        assert not queue.should_process_batch(5)

        # Add orders to reach batch size
        for i in range(3):
            queue.submit_order(symbol="MNQ", side=PositionSide.LONG, quantity=1)

        # Should trigger due to batch size
        assert queue.should_process_batch(5)

        # Reset and test time interval
        queue = OrderQueue(batch_size=10, process_interval=5)
        queue.submit_order(symbol="MNQ", side=PositionSide.LONG, quantity=1)
        queue.last_process_tick = 0

        # Should trigger due to time interval
        assert queue.should_process_batch(10)

    def test_market_order_execution(self):
        """Test market order execution in batch."""
        queue = OrderQueue()
        portfolio = Portfolio(initial_capital=Decimal("100000"))

        # Submit market order
        order_id = queue.submit_order(
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=1,
            order_type=OrderType.MARKET,
        )

        # Process batch
        prices = {"MNQ": Decimal("4000")}
        timestamp = pd.Timestamp.now()
        executed_orders = queue.process_batch(prices, timestamp, portfolio, 1)

        # Verify execution
        assert len(executed_orders) == 1
        assert executed_orders[0].order_id == order_id
        assert executed_orders[0].status == OrderStatus.EXECUTED
        assert executed_orders[0].executed_price == Decimal("4000")
        assert executed_orders[0].executed_quantity == 1

        # Verify portfolio has position
        assert portfolio.has_position("MNQ")
        position = portfolio.get_position("MNQ")
        assert position.side == PositionSide.LONG
        assert position.quantity == 1

    def test_limit_order_execution(self):
        """Test limit order execution logic."""
        queue = OrderQueue()
        portfolio = Portfolio(initial_capital=Decimal("100000"))

        # Submit limit order to buy at 3990
        order_id = queue.submit_order(
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=1,
            order_type=OrderType.LIMIT,
            price=Decimal("3990"),
        )

        # Price above limit - should not execute
        prices = {"MNQ": Decimal("4000")}
        timestamp = pd.Timestamp.now()
        executed_orders = queue.process_batch(prices, timestamp, portfolio, 1)
        assert len(executed_orders) == 0

        # Price at limit - should execute
        prices = {"MNQ": Decimal("3990")}
        executed_orders = queue.process_batch(prices, timestamp, portfolio, 2)
        assert len(executed_orders) == 1
        assert executed_orders[0].executed_price == Decimal("3990")

    def test_order_expiration_handling(self):
        """Test handling of expired orders."""
        queue = OrderQueue()
        portfolio = Portfolio(initial_capital=Decimal("100000"))

        # Submit order that will expire
        expiry_time = pd.Timestamp("2024-01-01 12:00:00")
        order_id = queue.submit_order(
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=1,
            expires_at=expiry_time,
        )

        # Process batch after expiry
        prices = {"MNQ": Decimal("4000")}
        current_time = pd.Timestamp("2024-01-01 12:00:01")  # After expiry
        executed_orders = queue.process_batch(prices, current_time, portfolio, 1)

        # Order should be cancelled, not executed
        assert len(executed_orders) == 0
        assert queue.get_order_status(order_id) == OrderStatus.CANCELLED
        assert queue.total_orders_cancelled == 1

    def test_stop_loss_take_profit_integration(self):
        """Test stop loss and take profit integration with orders."""
        queue = OrderQueue()
        portfolio = Portfolio(initial_capital=Decimal("100000"))

        # Submit order with stop loss and take profit
        order_id = queue.submit_order(
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=1,
            order_type=OrderType.MARKET,
            stop_loss_price=Decimal("3950"),
            take_profit_price=Decimal("4100"),
        )

        # Execute the order
        prices = {"MNQ": Decimal("4000")}
        timestamp = pd.Timestamp.now()
        executed_orders = queue.process_batch(prices, timestamp, portfolio, 1)

        # Verify position has stop loss and take profit set
        assert len(executed_orders) == 1
        position = portfolio.get_position("MNQ")
        assert position.stop_loss_price == Decimal("3950")
        assert position.take_profit_price == Decimal("4100")

    def test_multiple_orders_batch_processing(self):
        """Test processing multiple orders in a batch."""
        queue = OrderQueue()
        portfolio = Portfolio(initial_capital=Decimal("500000"))

        # Submit multiple orders
        order_ids = []
        for i in range(5):
            order_id = queue.submit_order(
                symbol="MNQ",
                side=PositionSide.LONG,
                quantity=1,
                order_type=OrderType.MARKET,
                notes=f"Order {i+1}",
            )
            order_ids.append(order_id)

        # Process all orders in batch
        prices = {"MNQ": Decimal("4000")}
        timestamp = pd.Timestamp.now()
        executed_orders = queue.process_batch(prices, timestamp, portfolio, 1)

        # All orders should execute (we have enough capital)
        assert len(executed_orders) == 5
        for i, order in enumerate(executed_orders):
            assert order.order_id in order_ids
            assert order.status == OrderStatus.EXECUTED

    def test_insufficient_capital_handling(self):
        """Test handling of orders when insufficient capital."""
        queue = OrderQueue()
        portfolio = Portfolio(initial_capital=Decimal("1000"))  # Very small capital

        # Submit large order that exceeds capital
        order_id = queue.submit_order(
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=100,  # Large quantity
            order_type=OrderType.MARKET,
        )

        # Process batch - should fail due to insufficient capital
        prices = {"MNQ": Decimal("4000")}
        timestamp = pd.Timestamp.now()
        executed_orders = queue.process_batch(prices, timestamp, portfolio, 1)

        # Order should be rejected due to insufficient capital
        assert len(executed_orders) == 0
        assert (
            queue.get_order_status(order_id) == OrderStatus.REJECTED
        )  # Correctly rejected

    def test_order_statistics(self):
        """Test order queue statistics."""
        queue = OrderQueue()
        portfolio = Portfolio(initial_capital=Decimal("100000"))

        # Submit and execute some orders
        for i in range(3):
            queue.submit_order(symbol="MNQ", side=PositionSide.LONG, quantity=1)

        # Cancel one order
        order_ids = list(queue.pending_orders.keys())
        queue.cancel_order(order_ids[0])

        # Execute remaining orders
        prices = {"MNQ": Decimal("4000")}
        timestamp = pd.Timestamp.now()
        queue.process_batch(prices, timestamp, portfolio, 1)

        # Check statistics
        stats = queue.get_statistics()
        assert stats["total_orders_submitted"] == 3
        assert stats["total_orders_executed"] == 2
        assert stats["total_orders_cancelled"] == 1
        assert stats["pending_orders"] == 0
        assert stats["execution_rate"] == 2 / 3

    def test_orders_for_symbol_filtering(self):
        """Test getting orders for specific symbol."""
        queue = OrderQueue()

        # Submit orders for different symbols
        mnq_order = queue.submit_order(symbol="MNQ", side=PositionSide.LONG, quantity=1)
        es_order = queue.submit_order(symbol="ES", side=PositionSide.LONG, quantity=1)
        another_mnq_order = queue.submit_order(
            symbol="MNQ", side=PositionSide.SHORT, quantity=1
        )

        # Get orders for MNQ
        mnq_orders = queue.get_orders_for_symbol("MNQ")
        es_orders = queue.get_orders_for_symbol("ES")

        assert len(mnq_orders) == 2
        assert len(es_orders) == 1
        assert all(order.symbol == "MNQ" for order in mnq_orders)
        assert all(order.symbol == "ES" for order in es_orders)

    def test_position_replacement_logic(self):
        """Test that orders properly replace existing positions."""
        queue = OrderQueue()
        portfolio = Portfolio(initial_capital=Decimal("100000"))

        # Open long position
        long_order = queue.submit_order(
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=1,
            order_type=OrderType.MARKET,
        )

        prices = {"MNQ": Decimal("4000")}
        timestamp = pd.Timestamp.now()
        queue.process_batch(prices, timestamp, portfolio, 1)

        # Verify long position exists
        position = portfolio.get_position("MNQ")
        assert position.side == PositionSide.LONG

        # Submit short order (should close long and open short)
        short_order = queue.submit_order(
            symbol="MNQ",
            side=PositionSide.SHORT,
            quantity=1,
            order_type=OrderType.MARKET,
        )

        queue.process_batch(prices, timestamp, portfolio, 2)

        # Verify position is now short
        position = portfolio.get_position("MNQ")
        assert position.side == PositionSide.SHORT

    def test_clear_completed_orders(self):
        """Test clearing old completed orders."""
        queue = OrderQueue()
        portfolio = Portfolio(initial_capital=Decimal("100000"))

        # Submit and execute many orders
        for i in range(20):
            queue.submit_order(symbol="MNQ", side=PositionSide.LONG, quantity=1)

        # Execute all orders
        prices = {"MNQ": Decimal("4000")}
        timestamp = pd.Timestamp.now()
        queue.process_batch(prices, timestamp, portfolio, 1)

        # Cancel some orders (simulate)
        for i in range(5):
            order_id = f"FAKE_{i}"
            fake_order = Order(
                order_id=order_id, symbol="MNQ", side=PositionSide.LONG, quantity=1
            )
            fake_order.status = OrderStatus.CANCELLED
            queue.cancelled_orders.append(fake_order)

        # Clear old orders, keep only 5 recent
        initial_executed = len(queue.executed_orders)
        initial_cancelled = len(queue.cancelled_orders)

        queue.clear_completed_orders(keep_recent=5)

        # Should keep only 5 most recent
        assert len(queue.executed_orders) <= 5
        assert len(queue.cancelled_orders) <= 5
