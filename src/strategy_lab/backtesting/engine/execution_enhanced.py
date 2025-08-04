"""Enhanced backtest execution with data pipeline integration."""

import logging
import pickle
import time
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterator

import pandas as pd
import psutil

try:
    from tqdm import tqdm
except ImportError:
    # Mock tqdm if not available
    class MockTqdm:
        def __init__(self, *args, **kwargs):
            self.desc = kwargs.get("desc", "")
            self.total = kwargs.get("total", 0)
            self.current = 0

        def update(self, n=1):
            self.current += n

        def set_description(self, desc):
            self.desc = desc

        def close(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    tqdm = MockTqdm

from ...strategies.registry import registry as strategy_registry
from ..data_integration import BacktestDataProvider
from ..metrics import MetricsAggregator
from ..metrics.comprehensive import (
    ComprehensiveMetricsCalculator,
    convert_portfolio_trades_to_performance_trades,
)
from .config import BacktestConfig
from .order_queue import OrderQueue, OrderType
from .portfolio import Portfolio, Position, PositionSide
from .results import BacktestResult, TradeRecord

logger = logging.getLogger(__name__)


@dataclass
class RiskLimits:
    """Risk management limits for backtesting."""

    max_position_size: int = 10  # Maximum position size in contracts
    max_drawdown_percent: float = 0.20  # Maximum drawdown before circuit breaker
    position_size_limit_enabled: bool = True
    drawdown_circuit_breaker_enabled: bool = True
    validate_signals: bool = True


@dataclass
class EnhancedExecutionContext:
    """Enhanced context for backtest execution with risk management."""

    config: BacktestConfig
    portfolio: Portfolio
    metrics: MetricsAggregator
    strategy: Any  # Strategy instance
    data_provider: BacktestDataProvider
    risk_limits: RiskLimits = field(default_factory=RiskLimits)
    order_queue: OrderQueue = field(default_factory=OrderQueue)

    # Progress tracking
    total_ticks: int = 0
    processed_ticks: int = 0
    start_time: float = field(default_factory=time.time)

    # Resource monitoring
    peak_memory_mb: float = 0.0
    avg_cpu_percent: float = 0.0
    cpu_samples: list[float] = field(default_factory=list)

    # Risk monitoring
    max_observed_drawdown: float = 0.0
    circuit_breaker_triggered: bool = False
    position_violations: int = 0
    signal_validation_errors: int = 0

    # Checkpointing
    checkpoint_interval: int = 10000  # Checkpoint every N ticks
    last_checkpoint_tick: int = 0
    checkpoint_dir: Path | None = None

    def update_progress(self) -> None:
        """Update progress metrics."""
        self.processed_ticks += 1

        # Update resource metrics
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        self.peak_memory_mb = max(self.peak_memory_mb, memory_mb)

        cpu_percent = process.cpu_percent(interval=0.01)
        self.cpu_samples.append(cpu_percent)
        if len(self.cpu_samples) > 100:
            self.cpu_samples.pop(0)
        self.avg_cpu_percent = sum(self.cpu_samples) / len(self.cpu_samples)

        # Update risk monitoring
        current_drawdown = abs(float(self.portfolio.current_drawdown_percent))
        self.max_observed_drawdown = max(self.max_observed_drawdown, current_drawdown)

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

    def should_trigger_circuit_breaker(self) -> bool:
        """Check if circuit breaker should be triggered."""
        if not self.risk_limits.drawdown_circuit_breaker_enabled:
            return False

        current_drawdown = abs(float(self.portfolio.current_drawdown_percent))
        return current_drawdown >= self.risk_limits.max_drawdown_percent

    def should_create_checkpoint(self) -> bool:
        """Check if a checkpoint should be created.

        Returns:
            True if checkpoint should be created
        """
        if self.checkpoint_dir is None:
            return False

        return (
            self.processed_ticks - self.last_checkpoint_tick
        ) >= self.checkpoint_interval

    def create_checkpoint(self) -> str:
        """Create a checkpoint of the current execution state.

        Returns:
            Path to the created checkpoint file
        """
        if self.checkpoint_dir is None:
            raise ValueError("Checkpoint directory not set")

        # Create checkpoint directory if it doesn't exist
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Create checkpoint filename with timestamp and tick count
        checkpoint_name = f"checkpoint_{self.processed_ticks}_{int(time.time())}.pkl"
        checkpoint_path = self.checkpoint_dir / checkpoint_name

        # Prepare checkpoint data
        checkpoint_data = {
            "processed_ticks": self.processed_ticks,
            "portfolio_state": self._serialize_portfolio(),
            "risk_metrics": {
                "max_observed_drawdown": self.max_observed_drawdown,
                "circuit_breaker_triggered": self.circuit_breaker_triggered,
                "position_violations": self.position_violations,
                "signal_validation_errors": self.signal_validation_errors,
            },
            "strategy_state": self._serialize_strategy_state(),
            "timestamp": datetime.now(),
        }

        # Save checkpoint
        with open(checkpoint_path, "wb") as f:
            pickle.dump(checkpoint_data, f)

        self.last_checkpoint_tick = self.processed_ticks
        logger.info(
            f"Created checkpoint at tick {self.processed_ticks}: {checkpoint_path}"
        )

        return str(checkpoint_path)

    def _serialize_portfolio(self) -> dict:
        """Serialize portfolio state for checkpointing.

        Returns:
            Serializable portfolio state dictionary
        """
        return {
            "cash": float(self.portfolio.cash),
            "positions": [
                {
                    "symbol": pos.symbol,
                    "side": pos.side.value,
                    "quantity": pos.quantity,
                    "entry_price": float(pos.entry_price),
                    "entry_time": pos.entry_time,
                    "current_price": float(pos.current_price),
                    "stop_loss_price": float(pos.stop_loss_price)
                    if pos.stop_loss_price
                    else None,
                    "take_profit_price": float(pos.take_profit_price)
                    if pos.take_profit_price
                    else None,
                    "commission": float(pos.commission),
                    "slippage": float(pos.slippage),
                }
                for symbol_positions in self.portfolio.positions.values()
                for pos in symbol_positions
                if pos.is_open
            ],
            "closed_positions": len(self.portfolio.closed_positions),
            "equity_curve": [float(x) for x in self.portfolio.equity_curve],
            "timestamps": self.portfolio.timestamps,
            "peak_equity": float(self.portfolio.peak_equity),
            "current_drawdown": float(self.portfolio.current_drawdown),
            "max_drawdown": float(self.portfolio.max_drawdown),
        }

    def _serialize_strategy_state(self) -> dict:
        """Serialize strategy state for checkpointing.

        Returns:
            Serializable strategy state dictionary
        """
        # Basic strategy state - strategies can override this
        strategy_state = {
            "class_name": self.strategy.__class__.__name__,
            "parameters": getattr(self.strategy, "parameters", {}),
        }

        # If strategy has custom serialization method, use it
        if hasattr(self.strategy, "get_checkpoint_state"):
            strategy_state.update(self.strategy.get_checkpoint_state())

        return strategy_state


class EnhancedBacktestExecutor:
    """Enhanced backtest executor with data pipeline integration and risk management."""

    def __init__(self, config: BacktestConfig, checkpoint_dir: Path | None = None):
        """Initialize enhanced executor.

        Args:
            config: Backtest configuration
            checkpoint_dir: Optional directory for checkpoints
        """
        self.config = config
        self.context: EnhancedExecutionContext | None = None
        self._progress_bar: tqdm | None = None
        self.checkpoint_dir = checkpoint_dir

    def execute(self) -> BacktestResult:
        """Execute the backtest with data pipeline integration.

        Returns:
            BacktestResult with execution results
        """
        logger.info(f"Starting enhanced backtest: {self.config.name}")

        # Initialize components
        self._initialize_context()

        try:
            # Initialize data stream
            self._initialize_data_stream()

            # Run enhanced backtest
            self._run_enhanced_backtest()

            # Generate results
            return self._generate_results()

        finally:
            # Cleanup
            self._cleanup()

    def _initialize_context(self) -> None:
        """Initialize enhanced execution context."""
        # Create portfolio with enhanced features
        portfolio = Portfolio(
            initial_capital=self.config.execution.initial_capital,
            commission_per_trade=self.config.execution.commission,
            slippage_per_trade=self.config.execution.slippage,
        )

        # Create metrics aggregator
        metrics = MetricsAggregator(
            starting_equity=self.config.execution.initial_capital, update_frequency=100
        )

        # Load strategy from registry
        strategy = self._load_strategy_from_registry()

        # Create data provider
        data_provider = BacktestDataProvider(self.config)

        # Create risk limits from config
        risk_limits = RiskLimits(
            max_position_size=self.config.strategy.parameters.get(
                "max_position_size", 10
            ),
            max_drawdown_percent=self.config.strategy.parameters.get(
                "max_drawdown_percent", 0.20
            ),
            position_size_limit_enabled=self.config.strategy.parameters.get(
                "enable_position_limits", True
            ),
            drawdown_circuit_breaker_enabled=self.config.strategy.parameters.get(
                "enable_circuit_breaker", True
            ),
            validate_signals=self.config.strategy.parameters.get(
                "validate_signals", True
            ),
        )

        # Create enhanced context
        self.context = EnhancedExecutionContext(
            config=self.config,
            portfolio=portfolio,
            metrics=metrics,
            strategy=strategy,
            data_provider=data_provider,
            risk_limits=risk_limits,
        )

        # Set up checkpointing if directory provided
        if self.checkpoint_dir:
            self.context.checkpoint_dir = self.checkpoint_dir
            logger.info(f"Checkpointing enabled: {self.checkpoint_dir}")

        logger.info("Enhanced execution context initialized")

    def _load_strategy_from_registry(self) -> Any:
        """Load strategy from registry with enhanced error handling.

        Returns:
            Initialized strategy instance
        """
        try:
            # Try to load from registry first
            strategy_name = self.config.strategy.name
            if strategy_name in strategy_registry.list_strategies():
                logger.info(f"Loading strategy '{strategy_name}' from registry")
                return strategy_registry.create_strategy(
                    strategy_name, **self.config.strategy.parameters
                )

            # Fallback to module loading
            logger.warning(
                f"Strategy '{strategy_name}' not in registry, trying module loading"
            )
            return self._load_strategy_from_module()

        except Exception as e:
            logger.error(f"Failed to load strategy: {e}")
            raise RuntimeError(f"Strategy loading failed: {e}") from e

    def _load_strategy_from_module(self) -> Any:
        """Fallback strategy loading from module path."""
        module_path = self.config.strategy.module
        module_parts = module_path.split(".")

        # Import the module
        module = __import__(module_path, fromlist=[module_parts[-1]])

        # Find strategy class
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

        return strategy_class(**self.config.strategy.parameters)

    def _initialize_data_stream(self) -> None:
        """Initialize data stream and validate data availability."""
        if not self.context:
            raise RuntimeError("Context not initialized")

        logger.info("Initializing data stream...")

        # Initialize data provider
        init_stats = self.context.data_provider.initialize()
        logger.info(f"Data provider initialized: {init_stats}")

        # Get data stream
        data_stream = self.context.data_provider.get_data_stream()

        # Estimate total ticks from data statistics
        stats = data_stream.get_stats()
        self.context.total_ticks = stats.get("estimated_total_records", 0)

        if self.context.total_ticks == 0:
            logger.warning(
                "Could not estimate total ticks, progress tracking may be inaccurate"
            )

        # Initialize progress bar
        if self.config.execution.progress_interval > 0:
            self._progress_bar = tqdm(
                total=self.context.total_ticks or None,
                desc=f"Backtesting {self.config.strategy.name}",
                unit="ticks",
            )

    def _run_enhanced_backtest(self) -> None:
        """Run the enhanced backtest with streaming data."""
        if not self.context:
            raise RuntimeError("Context not initialized")

        logger.info("Starting enhanced backtest execution")

        # Initialize strategy
        self.context.strategy.initialize()

        # Get data stream
        data_stream = self.context.data_provider.get_data_stream()

        try:
            # Process data in chunks from the stream
            for chunk in data_stream.stream_ticks():
                if self._should_stop_execution():
                    logger.warning("Execution stopped due to circuit breaker")
                    break

                self._process_data_chunk(chunk)

            # Close any remaining positions
            self._close_all_positions()

        except Exception as e:
            logger.error(f"Error during backtest execution: {e}")
            raise

        finally:
            # Finalize strategy
            self.context.strategy.cleanup()

        logger.info("Enhanced backtest execution completed")

    def _process_data_chunk(self, chunk: pd.DataFrame) -> None:
        """Process a chunk of tick data.

        Args:
            chunk: DataFrame containing tick data
        """
        if not self.context or chunk.empty:
            return

        # Process each tick in the chunk
        for idx, row in chunk.iterrows():
            # Check resource limits
            self._check_resource_limits()

            # Convert timestamp index to pandas timestamp if needed
            timestamp = pd.Timestamp(idx) if not isinstance(idx, pd.Timestamp) else idx

            # Update portfolio prices
            price = Decimal(str(row["price"]))
            prices = {self.config.data.symbol: price}
            self.context.portfolio.update_prices(prices, timestamp)

            # Check for stop-loss and take-profit triggers
            self._process_stop_loss_take_profit_triggers(timestamp)

            # Process order queue if needed
            if self.context.order_queue.should_process_batch(
                self.context.processed_ticks
            ):
                self._process_order_queue_batch(prices, timestamp)

            # Process tick through strategy
            signal = self.context.strategy.process_tick(
                timestamp=timestamp,
                price=float(price),
                volume=int(row.get("volume", 0)),
                bid=float(row.get("bid", row["price"])),
                ask=float(row.get("ask", row["price"])),
                level=row.get("level", "1"),
                mdt=int(row.get("mdt", 2)),  # Default to trade
            )

            # Execute trading logic with risk management
            self._execute_signal_with_risk_management(signal, price, timestamp)

            # Update progress
            self._update_progress()

            # Check for checkpointing
            if self.context.should_create_checkpoint():
                self.context.create_checkpoint()

            # Check circuit breaker
            if self.context.should_trigger_circuit_breaker():
                self.context.circuit_breaker_triggered = True
                logger.warning(
                    f"Circuit breaker triggered! Drawdown: "
                    f"{self.context.max_observed_drawdown:.2%}"
                )
                break

    def _execute_signal_with_risk_management(
        self, signal: int | None, price: Decimal, timestamp: pd.Timestamp
    ) -> None:
        """Execute trading signal with enhanced risk management.

        Args:
            signal: Trading signal (-1, 0, 1, None)
            price: Current price
            timestamp: Current timestamp
        """
        if not self.context or signal is None:
            return

        # Validate signal
        if self.context.risk_limits.validate_signals:
            if not self._validate_signal(signal):
                self.context.signal_validation_errors += 1
                return

        symbol = self.config.data.symbol
        current_position = self.context.portfolio.get_position(symbol)

        # Check position size limits before executing
        if self._would_violate_position_limits(signal, current_position):
            self.context.position_violations += 1
            logger.debug(f"Signal blocked by position size limits: {signal}")
            return

        # Execute signal
        self._execute_validated_signal(signal, price, timestamp, current_position)

    def _validate_signal(self, signal: Any) -> bool:
        """Validate trading signal format.

        Args:
            signal: Signal to validate

        Returns:
            True if signal is valid
        """
        if signal is None:
            return True

        if not isinstance(signal, int):
            logger.warning(f"Invalid signal type: {type(signal)}, expected int")
            return False

        if signal not in [-1, 0, 1]:
            logger.warning(f"Invalid signal value: {signal}, expected -1, 0, or 1")
            return False

        return True

    def _would_violate_position_limits(
        self, signal: int, current_position: Position | None
    ) -> bool:
        """Check if signal would violate position size limits.

        Args:
            signal: Trading signal
            current_position: Current position if any

        Returns:
            True if limits would be violated
        """
        if not self.context or not self.context.risk_limits.position_size_limit_enabled:
            return False

        max_size = self.context.risk_limits.max_position_size

        # Calculate what the new position size would be
        current_size = current_position.quantity if current_position else 0

        if signal > 0:  # Buy signal
            if current_position is None:
                new_size = 1  # Opening new long position
            elif current_position.side == PositionSide.SHORT:
                new_size = 1  # Closing short, opening long
            else:
                # Already long, no change in this simple implementation
                return False
        elif signal < 0:  # Sell signal
            if current_position is None:
                new_size = 1  # Opening new short position (count as 1 for limits)
            elif current_position.side == PositionSide.LONG:
                new_size = 1  # Closing long, opening short
            else:
                # Already short, no change
                return False
        else:  # Flat signal
            return False  # Closing positions never violates limits

        return abs(new_size) > max_size

    def _execute_validated_signal(
        self,
        signal: int,
        price: Decimal,
        timestamp: pd.Timestamp,
        current_position: Position | None,
    ) -> None:
        """Execute a validated trading signal.

        Args:
            signal: Validated trading signal
            price: Current price
            timestamp: Current timestamp
            current_position: Current position if any
        """
        symbol = self.config.data.symbol

        # Determine action based on signal and current position
        if signal > 0:  # Buy signal
            if current_position is None:
                # Open long position
                self._open_position(symbol, PositionSide.LONG, price, timestamp)
            elif current_position.side == PositionSide.SHORT:
                # Close short and open long
                self._close_position(current_position, price, timestamp)
                self._open_position(symbol, PositionSide.LONG, price, timestamp)

        elif signal < 0:  # Sell signal
            if current_position is None:
                # Open short position
                self._open_position(symbol, PositionSide.SHORT, price, timestamp)
            elif current_position.side == PositionSide.LONG:
                # Close long and open short
                self._close_position(current_position, price, timestamp)
                self._open_position(symbol, PositionSide.SHORT, price, timestamp)

        elif signal == 0 and current_position:  # Flat signal
            # Close current position
            self._close_position(current_position, price, timestamp)

    def _open_position(
        self, symbol: str, side: PositionSide, price: Decimal, timestamp: pd.Timestamp
    ) -> None:
        """Open a new position.

        Args:
            symbol: Trading symbol
            side: Position side
            price: Entry price
            timestamp: Entry timestamp
        """
        if not self.context:
            return

        position = self.context.portfolio.open_position(
            symbol=symbol,
            side=side,
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
            side="BUY" if side == PositionSide.LONG else "SELL",
        )

        logger.debug(f"Opened {side.value} position: {symbol} @ {price}")

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

        logger.debug(
            f"Closed {position.side.value} position: {position.symbol} @ {price}"
        )

    def _close_all_positions(self) -> None:
        """Close all open positions at end of backtest."""
        if not self.context:
            return

        # Use last known prices from portfolio
        for symbol, positions in self.context.portfolio.positions.items():
            for position in positions:
                if position.is_open:
                    # Use current price from position
                    last_price = position.current_price
                    # Use current time as close time
                    last_timestamp = pd.Timestamp.now()

                    self._close_position(position, last_price, last_timestamp)

        logger.info("Closed all remaining positions")

    def _process_stop_loss_take_profit_triggers(self, timestamp: pd.Timestamp) -> None:
        """Process stop-loss and take-profit triggers for all positions.

        Args:
            timestamp: Current timestamp
        """
        if not self.context:
            return

        triggers = self.context.portfolio.check_stop_loss_take_profit_triggers(
            timestamp
        )

        for position, trigger_type in triggers:
            # Close position at current price
            current_price = position.current_price

            # Close the position
            self._close_position(position, current_price, timestamp)

            # Log the trigger
            logger.info(
                f"{trigger_type.replace('_', ' ').title()} triggered for {position.symbol} @ {current_price}"
            )

            # Update metrics for trigger type
            if not hasattr(self.context, "stop_loss_triggers"):
                self.context.stop_loss_triggers = 0
                self.context.take_profit_triggers = 0

            if trigger_type == "stop_loss":
                self.context.stop_loss_triggers += 1
            elif trigger_type == "take_profit":
                self.context.take_profit_triggers += 1

    def _process_order_queue_batch(
        self, prices: dict[str, Decimal], timestamp: pd.Timestamp
    ) -> None:
        """Process a batch of orders from the queue.

        Args:
            prices: Current market prices
            timestamp: Current timestamp
        """
        if not self.context:
            return

        executed_orders = self.context.order_queue.process_batch(
            current_prices=prices,
            current_time=timestamp,
            portfolio=self.context.portfolio,
            current_tick=self.context.processed_ticks,
        )

        # Update metrics for each executed order
        for order in executed_orders:
            # Track order execution in metrics
            trade_id = len(self.context.metrics.metrics.completed_trades) + 1

            if order.side == PositionSide.LONG:
                self.context.metrics.open_trade(
                    trade_id=trade_id,
                    entry_price=order.executed_price,
                    quantity=order.executed_quantity,
                    entry_time=order.executed_at,
                    side="BUY",
                )
            elif order.side == PositionSide.SHORT:
                self.context.metrics.open_trade(
                    trade_id=trade_id,
                    entry_price=order.executed_price,
                    quantity=order.executed_quantity,
                    entry_time=order.executed_at,
                    side="SELL",
                )

    def submit_order(
        self,
        symbol: str,
        side: PositionSide,
        quantity: int,
        order_type: OrderType = OrderType.MARKET,
        price: Decimal | None = None,
        stop_price: Decimal | None = None,
        expires_at: pd.Timestamp | None = None,
        stop_loss_price: Decimal | None = None,
        take_profit_price: Decimal | None = None,
        strategy_id: str | None = None,
        notes: str | None = None,
    ) -> str:
        """Submit an order to the queue for batch processing.

        Args:
            symbol: Trading symbol
            side: Order side (LONG/SHORT)
            quantity: Order quantity
            order_type: Type of order
            price: Limit price (for limit orders)
            stop_price: Stop price (for stop orders)
            expires_at: Order expiration time
            stop_loss_price: Stop loss level for position
            take_profit_price: Take profit level for position
            strategy_id: Strategy that created the order
            notes: Additional notes

        Returns:
            Order ID
        """
        if not self.context:
            raise RuntimeError("Execution context not initialized")

        return self.context.order_queue.submit_order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            price=price,
            stop_price=stop_price,
            expires_at=expires_at,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            strategy_id=strategy_id,
            notes=notes,
        )

    def _should_stop_execution(self) -> bool:
        """Check if execution should be stopped.

        Returns:
            True if execution should stop
        """
        if not self.context:
            return False

        return self.context.circuit_breaker_triggered

    def _update_progress(self) -> None:
        """Update progress tracking and reporting."""
        if not self.context:
            return

        self.context.update_progress()

        if (
            self._progress_bar
            and self.context.processed_ticks % self.config.execution.progress_interval
            == 0
        ):
            self._progress_bar.update(self.config.execution.progress_interval)

            # Update progress bar description with performance info
            if hasattr(self.context.portfolio, "total_equity"):
                current_pnl = float(
                    self.context.portfolio.total_equity
                    - self.config.execution.initial_capital
                )
                self._progress_bar.set_description(
                    f"Backtesting {self.config.strategy.name} (P&L: ${current_pnl:.2f})"
                )

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
        """Generate enhanced backtest results with comprehensive metrics.

        Returns:
            BacktestResult object with comprehensive performance metrics
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
                exit_price=float(position.exit_price) if position.exit_price else 0.0,
                quantity=position.quantity,
                pnl=float(position.realized_pnl),
                commission=float(position.commission),
            )
            trades.append(trade)

        # Calculate comprehensive performance metrics
        logger.info("Calculating comprehensive performance metrics...")
        metrics_calculator = ComprehensiveMetricsCalculator(
            risk_free_rate=0.02,  # 2% risk-free rate - could be configurable
            periods_per_year=252,  # Daily trading periods
        )

        # Convert portfolio trades to performance trades
        portfolio_trades = self.context.portfolio.closed_positions
        performance_trades = convert_portfolio_trades_to_performance_trades(
            portfolio_trades
        )

        # Get equity curve data
        equity_curve = self.context.portfolio.equity_curve
        timestamps = self.context.portfolio.timestamps
        initial_capital = self.config.execution.initial_capital

        # Calculate all comprehensive metrics
        comprehensive_metrics = metrics_calculator.calculate_all_metrics(
            trades=performance_trades,
            equity_curve=equity_curve,
            timestamps=timestamps,
            initial_capital=initial_capital,
        )

        # Create enhanced result with comprehensive metrics
        result = BacktestResult(
            config=self.config,
            start_time=datetime.fromtimestamp(self.context.start_time),
            end_time=datetime.now(),
            # Performance metrics from comprehensive calculation
            total_pnl=float(comprehensive_metrics.performance.total_pnl),
            total_return=comprehensive_metrics.total_return,
            annualized_return=comprehensive_metrics.annualized_return,
            excess_return=comprehensive_metrics.excess_return,
            total_trades=comprehensive_metrics.trade_stats.total_trades,
            winning_trades=comprehensive_metrics.trade_stats.winning_trades,
            losing_trades=comprehensive_metrics.trade_stats.losing_trades,
            win_rate=float(comprehensive_metrics.trade_stats.win_rate),
            profit_factor=float(comprehensive_metrics.trade_stats.profit_factor),
            expectancy=float(comprehensive_metrics.trade_stats.expectancy),
            avg_win=float(comprehensive_metrics.trade_stats.avg_win),
            avg_loss=float(comprehensive_metrics.trade_stats.avg_loss),
            largest_win=float(comprehensive_metrics.trade_stats.largest_win),
            largest_loss=float(comprehensive_metrics.trade_stats.largest_loss),
            # Risk metrics from comprehensive calculation
            max_drawdown=float(comprehensive_metrics.risk.max_drawdown),
            sharpe_ratio=comprehensive_metrics.risk.sharpe_ratio,
            sortino_ratio=comprehensive_metrics.risk.sortino_ratio,
            calmar_ratio=comprehensive_metrics.calmar_ratio,
            volatility=comprehensive_metrics.risk.volatility,
            var_95=comprehensive_metrics.risk.var_95,
            cvar_95=comprehensive_metrics.risk.cvar_95,
            # Execution metrics
            total_ticks=self.context.processed_ticks,
            execution_time=self.context.elapsed_time,
            peak_memory_mb=self.context.peak_memory_mb,
            avg_cpu_percent=self.context.avg_cpu_percent,
            # Data
            trades=trades,
            equity_curve=[float(x) for x in equity_curve],
            timestamps=timestamps,
            # Enhanced metrics including comprehensive analysis
            custom_metrics={
                "circuit_breaker_triggered": self.context.circuit_breaker_triggered,
                "max_observed_drawdown": self.context.max_observed_drawdown,
                "position_violations": self.context.position_violations,
                "signal_validation_errors": self.context.signal_validation_errors,
                "stop_loss_triggers": getattr(self.context, "stop_loss_triggers", 0),
                "take_profit_triggers": getattr(
                    self.context, "take_profit_triggers", 0
                ),
                "order_queue_stats": self.context.order_queue.get_statistics(),
                "data_pipeline_version": "5.1",
                "comprehensive_metrics_version": "5.3",
                # Additional comprehensive metrics
                "recovery_factor": comprehensive_metrics.recovery_factor,
                "profit_to_max_dd_ratio": comprehensive_metrics.profit_to_max_dd_ratio,
                "max_consecutive_wins": comprehensive_metrics.trade_stats.max_consecutive_wins,
                "max_consecutive_losses": comprehensive_metrics.trade_stats.max_consecutive_losses,
                "best_month": {
                    "date": comprehensive_metrics.best_month[0].isoformat(),
                    "pnl": comprehensive_metrics.best_month[1],
                },
                "worst_month": {
                    "date": comprehensive_metrics.worst_month[0].isoformat(),
                    "pnl": comprehensive_metrics.worst_month[1],
                },
                "best_day": {
                    "date": comprehensive_metrics.best_day[0].isoformat(),
                    "pnl": comprehensive_metrics.best_day[1],
                },
                "worst_day": {
                    "date": comprehensive_metrics.worst_day[0].isoformat(),
                    "pnl": comprehensive_metrics.worst_day[1],
                },
            },
        )

        # Export detailed report if output directory is specified
        if self.config.output_dir:
            try:
                metrics_calculator.export_detailed_report(
                    comprehensive_metrics,
                    self.config.output_dir / "performance_analysis",
                    config_info={
                        "strategy_name": self.config.strategy.name,
                        "start_date": str(
                            getattr(self.config.data, "start_date", "N/A")
                        ),
                        "end_date": str(getattr(self.config.data, "end_date", "N/A")),
                        "initial_capital": float(initial_capital),
                    },
                )
                logger.info("Detailed performance report exported")
            except Exception as e:
                logger.warning(f"Failed to export detailed report: {e}")

        logger.info(
            f"Generated comprehensive results: {len(trades)} trades, "
            f"P&L: ${result.total_pnl:.2f}, Sharpe: {result.sharpe_ratio:.3f}"
        )
        return result

    def _cleanup(self) -> None:
        """Clean up resources."""
        if self._progress_bar:
            self._progress_bar.close()

        # Clear context
        self.context = None

        logger.info("Enhanced execution cleanup completed")

    @classmethod
    def load_from_checkpoint(
        cls,
        checkpoint_path: Path | str,
        config: BacktestConfig,
        checkpoint_dir: Path | None = None,
    ) -> tuple["EnhancedBacktestExecutor", dict]:
        """Load executor state from checkpoint.

        Args:
            checkpoint_path: Path to checkpoint file
            config: Backtest configuration
            checkpoint_dir: Directory for future checkpoints

        Returns:
            Tuple of (executor, checkpoint_data)
        """
        checkpoint_path = Path(checkpoint_path)
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint file not found: {checkpoint_path}")

        # Load checkpoint data
        with open(checkpoint_path, "rb") as f:
            checkpoint_data = pickle.load(f)

        # Create new executor
        executor = cls(config, checkpoint_dir)

        logger.info(
            f"Loaded checkpoint from {checkpoint_path} at tick {checkpoint_data['processed_ticks']}"
        )

        return executor, checkpoint_data

    def resume_from_checkpoint(self, checkpoint_data: dict) -> BacktestResult:
        """Resume backtest execution from checkpoint data.

        Args:
            checkpoint_data: Previously saved checkpoint data

        Returns:
            BacktestResult from resumed execution
        """
        logger.info(f"Resuming backtest from tick {checkpoint_data['processed_ticks']}")

        # Initialize context normally
        self._initialize_context()

        if not self.context:
            raise RuntimeError("Failed to initialize context")

        # Restore state from checkpoint
        self._restore_state_from_checkpoint(checkpoint_data)

        # Continue with data stream (need to skip to the right position)
        try:
            # Initialize data stream
            self._initialize_data_stream()

            # Resume enhanced backtest from checkpoint position
            self._run_enhanced_backtest_from_checkpoint(
                checkpoint_data["processed_ticks"]
            )

            # Generate results
            return self._generate_results()

        finally:
            # Cleanup
            self._cleanup()

    def _restore_state_from_checkpoint(self, checkpoint_data: dict) -> None:
        """Restore execution state from checkpoint data.

        Args:
            checkpoint_data: Checkpoint data to restore from
        """
        if not self.context:
            raise RuntimeError("Context not initialized")

        # Restore context state
        self.context.processed_ticks = checkpoint_data["processed_ticks"]

        # Restore risk metrics
        risk_metrics = checkpoint_data["risk_metrics"]
        self.context.max_observed_drawdown = risk_metrics["max_observed_drawdown"]
        self.context.circuit_breaker_triggered = risk_metrics[
            "circuit_breaker_triggered"
        ]
        self.context.position_violations = risk_metrics["position_violations"]
        self.context.signal_validation_errors = risk_metrics["signal_validation_errors"]

        # Restore portfolio state (this is simplified - full restoration would be more complex)
        portfolio_state = checkpoint_data["portfolio_state"]
        self.context.portfolio.cash = Decimal(str(portfolio_state["cash"]))
        self.context.portfolio.peak_equity = Decimal(
            str(portfolio_state["peak_equity"])
        )
        self.context.portfolio.current_drawdown = Decimal(
            str(portfolio_state["current_drawdown"])
        )
        self.context.portfolio.max_drawdown = Decimal(
            str(portfolio_state["max_drawdown"])
        )

        # Note: Full position restoration would require recreating Position objects
        # This is a simplified version that restores key metrics

        logger.info("State restored from checkpoint")

    def _run_enhanced_backtest_from_checkpoint(self, resume_tick: int) -> None:
        """Run enhanced backtest resuming from a specific tick.

        Args:
            resume_tick: Tick number to resume from
        """
        if not self.context:
            raise RuntimeError("Context not initialized")

        logger.info(f"Resuming enhanced backtest execution from tick {resume_tick}")

        # Initialize strategy
        self.context.strategy.initialize()

        # Get data stream
        data_stream = self.context.data_provider.get_data_stream()

        try:
            # Process data in chunks from the stream, skipping to resume position
            current_tick = 0

            for chunk in data_stream.stream_ticks():
                if self._should_stop_execution():
                    logger.warning("Execution stopped due to circuit breaker")
                    break

                # Skip ticks until we reach resume position
                for idx, row in chunk.iterrows():
                    current_tick += 1

                    # Skip ticks before resume point
                    if current_tick <= resume_tick:
                        continue

                    # Process tick normally from here
                    timestamp = (
                        pd.Timestamp(idx) if not isinstance(idx, pd.Timestamp) else idx
                    )
                    price = Decimal(str(row["price"]))
                    prices = {self.config.data.symbol: price}
                    self.context.portfolio.update_prices(prices, timestamp)

                    # Check for stop-loss and take-profit triggers
                    self._process_stop_loss_take_profit_triggers(timestamp)

                    # Process tick through strategy
                    signal = self.context.strategy.process_tick(
                        timestamp=timestamp,
                        price=float(price),
                        volume=int(row.get("volume", 0)),
                        bid=float(row.get("bid", row["price"])),
                        ask=float(row.get("ask", row["price"])),
                        level=row.get("level", "1"),
                        mdt=int(row.get("mdt", 2)),
                    )

                    # Execute trading logic with risk management
                    self._execute_signal_with_risk_management(signal, price, timestamp)

                    # Update progress
                    self._update_progress()

                    # Check for checkpointing
                    if self.context.should_create_checkpoint():
                        self.context.create_checkpoint()

                    # Check circuit breaker
                    if self.context.should_trigger_circuit_breaker():
                        self.context.circuit_breaker_triggered = True
                        logger.warning(
                            f"Circuit breaker triggered! Drawdown: "
                            f"{self.context.max_observed_drawdown:.2%}"
                        )
                        return

            # Close any remaining positions
            self._close_all_positions()

        except Exception as e:
            logger.error(f"Error during backtest execution: {e}")
            raise

        finally:
            # Finalize strategy
            self.context.strategy.cleanup()

        logger.info("Enhanced backtest execution completed")
