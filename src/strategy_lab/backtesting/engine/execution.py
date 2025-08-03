"""Backtest execution logic and coordination."""

import multiprocessing as mp
import time
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

import pandas as pd
import psutil
from tqdm import tqdm

from ...data.ingestion import DataLoader
from ..metrics import MetricsAggregator
from .config import BacktestConfig
from .portfolio import Portfolio, Position, PositionSide
from .results import BacktestResult, TradeRecord


@dataclass
class ExecutionContext:
    """Context for backtest execution."""

    config: BacktestConfig
    portfolio: Portfolio
    metrics: MetricsAggregator
    strategy: Any  # Strategy instance

    # Data management
    data_loader: DataLoader
    current_data: pd.DataFrame | None = None

    # Progress tracking
    total_ticks: int = 0
    processed_ticks: int = 0
    start_time: float = field(default_factory=time.time)

    # Resource monitoring
    peak_memory_mb: float = 0.0
    avg_cpu_percent: float = 0.0
    cpu_samples: list[float] = field(default_factory=list)

    def update_progress(self) -> None:
        """Update progress metrics."""
        self.processed_ticks += 1

        # Update resource metrics
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        self.peak_memory_mb = max(self.peak_memory_mb, memory_mb)

        cpu_percent = process.cpu_percent(interval=0.1)
        self.cpu_samples.append(cpu_percent)
        if len(self.cpu_samples) > 100:
            self.cpu_samples.pop(0)
        self.avg_cpu_percent = sum(self.cpu_samples) / len(self.cpu_samples)

    @property
    def progress_percent(self) -> float:
        """Get progress percentage."""
        if self.total_ticks == 0:
            return 0.0
        return (self.processed_ticks / self.total_ticks) * 100

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time

    @property
    def eta_seconds(self) -> float:
        """Estimate time to completion."""
        if self.processed_ticks == 0:
            return 0.0

        rate = self.processed_ticks / self.elapsed_time
        remaining = self.total_ticks - self.processed_ticks
        return remaining / rate if rate > 0 else 0.0


class BacktestExecutor:
    """Executes backtests with resource management."""

    def __init__(self, config: BacktestConfig):
        """Initialize executor.

        Args:
            config: Backtest configuration
        """
        self.config = config
        self.context: ExecutionContext | None = None
        self._progress_bar: tqdm | None = None

    def execute(self) -> BacktestResult:
        """Execute the backtest.

        Returns:
            BacktestResult with execution results
        """
        # Initialize components
        self._initialize_context()

        try:
            # Load data
            self._load_data()

            # Run backtest
            self._run_backtest()

            # Generate results
            return self._generate_results()

        finally:
            # Cleanup
            self._cleanup()

    def _initialize_context(self) -> None:
        """Initialize execution context."""
        # Create portfolio
        portfolio = Portfolio(
            initial_capital=self.config.execution.initial_capital,
            commission_per_trade=self.config.execution.commission,
            slippage_per_trade=self.config.execution.slippage,
        )

        # Create metrics aggregator
        metrics = MetricsAggregator(
            starting_equity=self.config.execution.initial_capital, update_frequency=100
        )

        # Load strategy
        strategy = self._load_strategy()

        # Create data loader
        data_loader = DataLoader(data_path=self.config.data.data_path)

        # Create context
        self.context = ExecutionContext(
            config=self.config,
            portfolio=portfolio,
            metrics=metrics,
            strategy=strategy,
            data_loader=data_loader,
        )

    def _load_strategy(self) -> Any:
        """Load and initialize strategy.

        Returns:
            Initialized strategy instance
        """
        # Import strategy module dynamically
        module_path = self.config.strategy.module
        module_parts = module_path.split(".")

        # Import the module
        module = __import__(module_path, fromlist=[module_parts[-1]])

        # Find strategy class (assume it matches the module name or has 'Strategy' in the name)
        strategy_class = None
        for name in dir(module):
            obj = getattr(module, name)
            if (
                isinstance(obj, type)
                and hasattr(obj, "initialize")
                and hasattr(obj, "process_tick")
                and hasattr(obj, "cleanup")
            ):
                strategy_class = obj
                break

        if strategy_class is None:
            raise ValueError(f"No strategy class found in {module_path}")

        # Initialize strategy with parameters
        return strategy_class(**self.config.strategy.parameters)

    def _load_data(self) -> None:
        """Load data for backtest period."""
        if not self.context:
            raise RuntimeError("Context not initialized")

        # Get date range
        start_date, end_date = self.config.get_date_range()

        # Load data
        self.context.current_data = self.context.data_loader.load_data(
            start_date=start_date, end_date=end_date, columns=None  # Load all columns
        )

        # Set total ticks
        self.context.total_ticks = len(self.context.current_data)

        # Initialize progress bar
        if self.config.execution.progress_interval > 0:
            self._progress_bar = tqdm(
                total=self.context.total_ticks, desc="Backtesting", unit="ticks"
            )

    def _run_backtest(self) -> None:
        """Run the backtest execution."""
        if not self.context or self.context.current_data is None:
            raise RuntimeError("Context or data not initialized")

        # Initialize strategy
        self.context.strategy.initialize()

        # Process each tick
        for idx, row in self.context.current_data.iterrows():
            # Check resource limits
            self._check_resource_limits()

            # Update portfolio prices
            price = Decimal(str(row["price"]))
            prices = {self.config.data.symbol: price}
            self.context.portfolio.update_prices(prices, idx)

            # Process tick through strategy
            signal = self.context.strategy.process_tick(
                timestamp=idx,
                price=float(price),
                volume=row.get("volume", 0),
                bid=float(row.get("bid", row["price"])),
                ask=float(row.get("ask", row["price"])),
            )

            # Execute trading logic based on signal
            self._execute_signal(signal, price, idx)

            # Update progress
            self.context.update_progress()
            if (
                self._progress_bar
                and self.context.processed_ticks
                % self.config.execution.progress_interval
                == 0
            ):
                self._progress_bar.update(self.config.execution.progress_interval)

        # Close any remaining positions
        self._close_all_positions()

        # Finalize strategy
        self.context.strategy.cleanup()

    def _execute_signal(
        self, signal: int, price: Decimal, timestamp: pd.Timestamp
    ) -> None:
        """Execute trading signal.

        Args:
            signal: Trading signal (-1, 0, 1)
            price: Current price
            timestamp: Current timestamp
        """
        if not self.context:
            return

        symbol = self.config.data.symbol
        current_position = self.context.portfolio.get_position(symbol)

        # Determine action based on signal and current position
        if signal > 0:  # Buy signal
            if current_position is None:
                # Open long position
                position = self.context.portfolio.open_position(
                    symbol=symbol,
                    side=PositionSide.LONG,
                    quantity=1,  # Default to 1 contract
                    price=price,
                    timestamp=timestamp,
                )
                # Track in metrics
                trade_id = len(self.context.metrics.metrics.completed_trades) + 1
                self.context.metrics.open_trade(
                    trade_id=trade_id,
                    entry_price=price,
                    quantity=1,
                    entry_time=timestamp,
                    side="BUY",
                )
            elif current_position.side == PositionSide.SHORT:
                # Close short and open long
                self._close_position(current_position, price, timestamp)
                # Open new long
                self._execute_signal(signal, price, timestamp)

        elif signal < 0:  # Sell signal
            if current_position is None:
                # Open short position
                position = self.context.portfolio.open_position(
                    symbol=symbol,
                    side=PositionSide.SHORT,
                    quantity=1,
                    price=price,
                    timestamp=timestamp,
                )
                # Track in metrics
                trade_id = len(self.context.metrics.metrics.completed_trades) + 1
                self.context.metrics.open_trade(
                    trade_id=trade_id,
                    entry_price=price,
                    quantity=1,
                    entry_time=timestamp,
                    side="SELL",
                )
            elif current_position.side == PositionSide.LONG:
                # Close long and open short
                self._close_position(current_position, price, timestamp)
                # Open new short
                self._execute_signal(signal, price, timestamp)

        elif signal == 0 and current_position:  # Flat signal
            # Close current position
            self._close_position(current_position, price, timestamp)

    def _close_position(
        self, position: Position, price: Decimal, timestamp: pd.Timestamp
    ) -> None:
        """Close a position and update metrics.

        Args:
            position: Position to close
            price: Exit price
            timestamp: Exit timestamp
        """
        if not self.context:
            return

        # Close in portfolio
        self.context.portfolio.close_position(
            symbol=position.symbol, price=price, timestamp=timestamp, position=position
        )

        # Update metrics
        trade_id = len(self.context.metrics.metrics.completed_trades) + 1
        self.context.metrics.close_trade(
            trade_id=trade_id,
            exit_price=price,
            exit_time=timestamp,
            commission=position.commission,
        )

    def _close_all_positions(self) -> None:
        """Close all open positions at end of backtest."""
        if not self.context or self.context.current_data is None:
            return

        # Get last price
        last_row = self.context.current_data.iloc[-1]
        last_price = Decimal(str(last_row["price"]))
        last_timestamp = last_row.name

        # Close all positions
        for symbol, positions in self.context.portfolio.positions.items():
            for position in positions:
                if position.is_open:
                    self._close_position(position, last_price, last_timestamp)

    def _check_resource_limits(self) -> None:
        """Check and enforce resource limits."""
        if not self.context:
            return

        # Check memory limit
        process = psutil.Process()
        memory_gb = process.memory_info().rss / 1024 / 1024 / 1024
        if memory_gb > self.config.execution.max_memory_gb:
            raise MemoryError(
                f"Memory limit exceeded: {memory_gb:.2f}GB > "
                f"{self.config.execution.max_memory_gb}GB"
            )

        # Check CPU limit (averaged)
        if self.context.avg_cpu_percent > self.config.execution.max_cpu_percent:
            # Throttle execution
            time.sleep(0.01)  # Small delay to reduce CPU usage

    def _generate_results(self) -> BacktestResult:
        """Generate backtest results.

        Returns:
            BacktestResult object
        """
        if not self.context:
            raise RuntimeError("Context not initialized")

        # Update final metrics
        self.context.metrics.update_all_metrics()

        # Create trade records
        trades = []
        for position in self.context.portfolio.closed_positions:
            trade = TradeRecord(
                symbol=position.symbol,
                side=position.side.value,
                entry_time=position.entry_time,
                entry_price=float(position.entry_price),
                exit_time=position.exit_time,
                exit_price=float(position.exit_price),
                quantity=position.quantity,
                pnl=float(position.realized_pnl),
                commission=float(position.commission),
            )
            trades.append(trade)

        # Create result
        result = BacktestResult(
            config=self.config,
            start_time=datetime.fromtimestamp(self.context.start_time),
            end_time=datetime.now(),
            # Performance metrics
            total_pnl=float(self.context.metrics.metrics.performance.total_pnl),
            total_trades=len(trades),
            winning_trades=self.context.metrics.metrics.performance.winning_trades,
            losing_trades=self.context.metrics.metrics.performance.losing_trades,
            win_rate=float(self.context.metrics.metrics.performance.win_rate),
            profit_factor=float(self.context.metrics.metrics.performance.profit_factor),
            # Risk metrics
            max_drawdown=float(self.context.metrics.metrics.risk.max_drawdown),
            sharpe_ratio=self.context.metrics.metrics.risk.sharpe_ratio,
            # Execution metrics
            total_ticks=self.context.total_ticks,
            execution_time=self.context.elapsed_time,
            peak_memory_mb=self.context.peak_memory_mb,
            avg_cpu_percent=self.context.avg_cpu_percent,
            # Data
            trades=trades,
            equity_curve=self.context.portfolio.equity_curve,
            timestamps=self.context.portfolio.timestamps,
        )

        return result

    def _cleanup(self) -> None:
        """Clean up resources."""
        if self._progress_bar:
            self._progress_bar.close()

        # Clear large data structures
        if self.context:
            self.context.current_data = None


def execute_backtest_parallel(
    configs: list[BacktestConfig], max_workers: int | None = None
) -> list[BacktestResult]:
    """Execute multiple backtests in parallel.

    Args:
        configs: List of backtest configurations
        max_workers: Maximum parallel workers (default: CPU count)

    Returns:
        List of backtest results
    """
    if max_workers is None:
        max_workers = mp.cpu_count()

    # Execute backtests in parallel
    with mp.Pool(processes=max_workers) as pool:
        results = pool.map(_execute_single_backtest, configs)

    return results


def _execute_single_backtest(config: BacktestConfig) -> BacktestResult:
    """Execute a single backtest (for parallel execution).

    Args:
        config: Backtest configuration

    Returns:
        Backtest result
    """
    executor = BacktestExecutor(config)
    return executor.execute()
