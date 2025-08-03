"""Main adapter for hftbacktest integration with Strategy Lab data pipeline."""

import json
import logging
import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from src.strategy_lab.data.adapters.hftbacktest import DataPipeline

from .config import MNQConfig
from .data_feed import HftDataFeed, TickData
from .event_processor import Fill, HftEventProcessor, OrderSide, OrderType

logger = logging.getLogger(__name__)


@dataclass
class BacktestResults:
    """Comprehensive backtest results."""

    start_time: float
    end_time: float
    total_trades: int
    total_volume: int
    gross_pnl: float
    net_pnl: float
    total_commission: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    avg_trade_duration: float
    feed_stats: dict[str, Any]
    event_stats: dict[str, Any]
    positions: dict[str, dict[str, Any]]

    @property
    def duration_seconds(self) -> float:
        """Get backtest duration in seconds."""
        return self.end_time - self.start_time

    @property
    def return_percent(self) -> float:
        """Get return as percentage."""
        # Assuming initial capital for return calculation
        initial_capital = 50000.0  # Default $50k
        return (self.net_pnl / initial_capital) * 100 if initial_capital > 0 else 0.0


class HftBacktestAdapter:
    """
    Main adapter for integrating Strategy Lab data pipeline with hftbacktest engine.

    This adapter coordinates:
    - Data streaming from the data pipeline
    - Event processing for order management
    - Strategy execution interface
    - Performance metrics collection
    """

    def __init__(self, config: MNQConfig, data_directory: Path | None = None):
        """Initialize the adapter with configuration."""
        self.config = config
        self.data_directory = data_directory or Path("./data/MNQ")

        # Initialize components
        self.data_feed = HftDataFeed(config)
        self.event_processor = HftEventProcessor(config)
        self.data_pipeline = DataPipeline()

        # Strategy interface
        self.strategy_callback: Callable[[TickData], None] | None = None
        self.on_fill_callback: Callable[[Fill], None] | None = None

        # Backtest state
        self._is_running = False
        self._current_timestamp = 0
        self._current_price = 0.0
        self._backtest_results: BacktestResults | None = None

        logger.info("Initialized HftBacktestAdapter for %s", config.symbol)

    def set_strategy_callback(self, callback: Callable[[TickData], None]):
        """Set strategy callback for tick processing."""
        self.strategy_callback = callback
        logger.debug("Strategy callback registered")

    def set_fill_callback(self, callback: Callable[[Fill], None]):
        """Set callback for order fills."""
        self.on_fill_callback = callback
        self.event_processor.on_order_filled = callback
        logger.debug("Fill callback registered")

    def submit_market_order(
        self, side: OrderSide, quantity: int, timestamp: int | None = None
    ) -> int:
        """Submit a market order through the event processor."""
        if not self._is_running:
            raise RuntimeError("Backtest not running")

        timestamp = timestamp or self._current_timestamp

        order = self.event_processor.submit_order(
            timestamp=timestamp,
            side=side,
            quantity=quantity,
            order_type=OrderType.MARKET,
        )

        # Simulate immediate execution at current price
        if order.status.value != "rejected":
            self.event_processor.process_fill(
                order_id=order.order_id,
                timestamp=timestamp + 1000,  # 1 microsecond later
                fill_price=self._current_price,
                fill_quantity=quantity,
            )

        return order.order_id

    def submit_limit_order(
        self, side: OrderSide, quantity: int, price: float, timestamp: int | None = None
    ) -> int:
        """Submit a limit order through the event processor."""
        if not self._is_running:
            raise RuntimeError("Backtest not running")

        timestamp = timestamp or self._current_timestamp

        order = self.event_processor.submit_order(
            timestamp=timestamp,
            side=side,
            quantity=quantity,
            order_type=OrderType.LIMIT,
            price=price,
        )

        return order.order_id

    def cancel_order(self, order_id: int, timestamp: int | None = None) -> bool:
        """Cancel an order."""
        if not self._is_running:
            raise RuntimeError("Backtest not running")

        timestamp = timestamp or self._current_timestamp
        return self.event_processor.cancel_order(order_id, timestamp)

    def get_current_position(self) -> dict[str, Any]:
        """Get current position information."""
        position = self.event_processor.get_position(self.config.symbol)
        return {
            "quantity": position.quantity,
            "average_price": position.average_price,
            "market_value": position.market_value,
            "unrealized_pnl": position.unrealized_pnl,
            "realized_pnl": position.realized_pnl,
            "is_long": position.is_long,
            "is_short": position.is_short,
            "is_flat": position.is_flat,
        }

    def run_backtest(
        self, start_date: str, end_date: str, contract_months: list[str] | None = None
    ) -> BacktestResults:
        """
        Run a complete backtest for the specified date range.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            contract_months: List of contract months to include
                (e.g., ["03-20", "06-20"])

        Returns:
            BacktestResults with comprehensive performance metrics
        """
        logger.info("Starting backtest: %s to %s", start_date, end_date)

        if not self.strategy_callback:
            raise ValueError("Strategy callback required")

        start_time = time.time()
        self._is_running = True

        try:
            # Get data chunks from pipeline
            data_chunks = self.data_pipeline.process_date_range(
                start_date=start_date,
                end_date=end_date,
                contract_months=contract_months,
                data_directory=self.data_directory,
            )

            # Stream data through the system
            tick_count = 0
            for chunk in data_chunks:
                for tick_data in self.data_feed.create_data_stream(chunk):
                    # Update current state
                    self._current_timestamp = tick_data.timestamp
                    self._current_price = tick_data.price

                    # Update unrealized PnL
                    self.event_processor.update_unrealized_pnl(tick_data.price)

                    # Call strategy
                    if self.strategy_callback:
                        self.strategy_callback(tick_data)

                    tick_count += 1

                    # Progress reporting
                    if tick_count % 100000 == 0:
                        logger.info("Processed %s ticks", f"{tick_count:,}")

            end_time = time.time()

            # Generate results
            self._backtest_results = self._generate_results(start_time, end_time)

            logger.info(
                "Backtest completed: %s ticks in %.2fs",
                f"{tick_count:,}",
                end_time - start_time,
            )
            return self._backtest_results

        finally:
            self._is_running = False

    def _generate_results(self, start_time: float, end_time: float) -> BacktestResults:
        """Generate comprehensive backtest results."""

        # Get performance summary from event processor
        event_summary = self.event_processor.get_performance_summary()
        feed_stats = self.data_feed.get_stats()

        # Calculate additional metrics
        trades = self.event_processor.fills
        trade_returns = []

        if trades:
            # Calculate individual trade returns
            for fill in trades:
                # Simplified return calculation
                trade_returns.append(fill.price * fill.quantity * fill.side.value)

        # Calculate performance metrics
        gross_pnl = event_summary.get("gross_pnl", 0.0)
        net_pnl = event_summary.get("net_pnl", 0.0)
        total_commission = event_summary.get("total_commission", 0.0)

        # Calculate Sharpe ratio (simplified)
        if trade_returns:
            returns_array = np.array(trade_returns)
            mean_return = np.mean(returns_array)
            std_return = np.std(returns_array)
            sharpe_ratio = mean_return / std_return if std_return > 0 else 0.0
        else:
            sharpe_ratio = 0.0

        # Calculate win rate
        winning_trades = sum(1 for ret in trade_returns if ret > 0)
        win_rate = (winning_trades / len(trade_returns) * 100) if trade_returns else 0.0

        # Calculate max drawdown (simplified)
        if trade_returns:
            cumulative_returns = np.cumsum(trade_returns)
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdowns = cumulative_returns - running_max
            max_drawdown = abs(np.min(drawdowns)) if len(drawdowns) > 0 else 0.0
        else:
            max_drawdown = 0.0

        return BacktestResults(
            start_time=start_time,
            end_time=end_time,
            total_trades=len(trades),
            total_volume=event_summary.get("total_volume", 0),
            gross_pnl=gross_pnl,
            net_pnl=net_pnl,
            total_commission=total_commission,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            avg_trade_duration=0.0,  # Would need to calculate from order timestamps
            feed_stats={
                "ticks_processed": feed_stats.ticks_processed,
                "l1_ticks": feed_stats.l1_ticks,
                "l2_ticks": feed_stats.l2_ticks,
                "processing_rate": feed_stats.ticks_per_second,
                "errors": feed_stats.processing_errors,
            },
            event_stats=event_summary,
            positions=event_summary.get("positions", {}),
        )

    def get_live_stats(self) -> dict[str, Any]:
        """Get live statistics during backtest."""
        if not self._is_running:
            return {}

        return {
            "current_timestamp": self._current_timestamp,
            "current_price": self._current_price,
            "current_position": self.get_current_position(),
            "open_orders": len(self.event_processor.get_open_orders()),
            "total_fills": len(self.event_processor.fills),
            "feed_ticks_processed": self.data_feed.stats.ticks_processed,
            "unrealized_pnl": self.event_processor.metrics.unrealized_pnl,
            "realized_pnl": self.event_processor.metrics.realized_pnl,
        }

    def reset(self):
        """Reset adapter state for new backtest."""
        self.event_processor.reset()
        self.data_feed.reset_stats()
        self._current_timestamp = 0
        self._current_price = 0.0
        self._backtest_results = None
        self._is_running = False

        logger.debug("Adapter reset")

    def export_results(self, output_path: Path):
        """Export backtest results to file."""
        if not self._backtest_results:
            raise ValueError("No results to export")

        # Convert results to JSON-serializable format
        results_dict = {
            "config": self.config.to_hftbacktest_config(),
            "performance": {
                "duration_seconds": self._backtest_results.duration_seconds,
                "total_trades": self._backtest_results.total_trades,
                "total_volume": self._backtest_results.total_volume,
                "gross_pnl": self._backtest_results.gross_pnl,
                "net_pnl": self._backtest_results.net_pnl,
                "return_percent": self._backtest_results.return_percent,
                "total_commission": self._backtest_results.total_commission,
                "max_drawdown": self._backtest_results.max_drawdown,
                "sharpe_ratio": self._backtest_results.sharpe_ratio,
                "win_rate": self._backtest_results.win_rate,
            },
            "feed_stats": self._backtest_results.feed_stats,
            "event_stats": self._backtest_results.event_stats,
            "positions": self._backtest_results.positions,
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w") as f:
            json.dump(results_dict, f, indent=2, default=str)

        logger.info("Results exported to %s", output_path)


# Utility functions for adapter usage
def create_simple_strategy_adapter(
    config: MNQConfig | None = None,
) -> HftBacktestAdapter:
    """Create a simple adapter with default configuration."""
    if config is None:
        from .config import (
            create_default_mnq_config,  # pylint: disable=import-outside-toplevel
        )

        config = create_default_mnq_config()

    adapter = HftBacktestAdapter(config)

    # Set up basic logging callbacks
    def log_fill(fill: Fill):
        logger.info("Fill: %d @ %.2f", fill.quantity, fill.price)

    adapter.set_fill_callback(log_fill)

    return adapter


def run_simple_backtest(
    strategy_func: Callable[[TickData, HftBacktestAdapter], None],
    start_date: str,
    end_date: str,
    config: MNQConfig | None = None,
) -> BacktestResults:
    """Run a simple backtest with a strategy function."""

    adapter = create_simple_strategy_adapter(config)

    # Wrap strategy function to pass adapter
    def strategy_wrapper(tick: TickData):
        strategy_func(tick, adapter)

    adapter.set_strategy_callback(strategy_wrapper)

    return adapter.run_backtest(start_date, end_date)


# Example strategy implementation
def example_mean_reversion_strategy(tick: TickData, adapter: HftBacktestAdapter):
    """Example mean reversion strategy for demonstration."""

    # Get current position
    position = adapter.get_current_position()

    # Simple mean reversion logic (placeholder)
    # In practice, would maintain price history and calculate indicators

    if position["is_flat"]:
        # Enter position based on some criteria
        # This is just a placeholder - real strategy would have proper signals
        entry_probability = 0.001  # Very low probability for demo
        if random.random() < entry_probability:
            buy_threshold = 0.5
            side = OrderSide.BUY if random.random() > buy_threshold else OrderSide.SELL
            adapter.submit_market_order(side, 1, tick.timestamp)

    elif not position["is_flat"] and abs(position["unrealized_pnl"]) > 50:
        # Exit logic - take profit or stop loss
        side = OrderSide.SELL if position["quantity"] > 0 else OrderSide.BUY
        adapter.submit_market_order(side, abs(position["quantity"]), tick.timestamp)
