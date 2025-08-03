# Strategy Lab Trading Strategy Framework

This document provides comprehensive guidance for implementing trading strategies using the Strategy Lab framework.

## Overview

The Strategy Lab framework provides a complete template-based system for implementing high-frequency trading strategies on futures markets. All strategies inherit from the `StrategyBase` abstract class, ensuring consistent interfaces and common functionality across different strategy implementations.

## Quick Start

### Basic Strategy Implementation

```python
from strategy_lab.strategies.base import StrategyBase, StrategyConfig
from strategy_lab.backtesting.hft_integration.data_feed import TickData
from strategy_lab.backtesting.hft_integration.event_processor import OrderSide

class MyStrategy(StrategyBase):
    """Example strategy implementation."""

    def initialize(self):
        """Set up strategy-specific state."""
        self.entry_threshold = self.config.custom_params.get('entry_threshold', 0.5)
        self.price_history = []

    def process_tick(self, tick: TickData):
        """Process market data and execute trading logic."""
        self.price_history.append(tick.price)

        if self.should_enter_position(tick):
            self.submit_market_order(OrderSide.BUY, 1)

    def should_enter_position(self, tick: TickData) -> bool:
        """Strategy-specific entry logic."""
        if len(self.price_history) < 10:
            return False

        recent_avg = sum(self.price_history[-5:]) / 5
        return tick.price > recent_avg * (1 + self.entry_threshold)

    def cleanup(self):
        """Close positions and cleanup resources."""
        if not self.position_manager.get_position_info().is_flat:
            self.close_all_positions()

# Usage
config = StrategyConfig(
    strategy_name="MyStrategy",
    max_position_size=5,
    custom_params={'entry_threshold': 0.002}
)

strategy = MyStrategy(config, adapter)
strategy.start()
```

## Architecture

### Core Components

1. **StrategyBase**: Abstract base class providing framework interface
2. **SignalGenerator**: Utilities for technical analysis and signal generation
3. **PositionManager**: Position tracking and risk management
4. **StrategyConfig**: Configuration and parameter management

### Strategy Lifecycle

```
Initialize → Start → Process Ticks → Stop → Cleanup
     ↓         ↓           ↓           ↓        ↓
   Setup   Activate   Trading    Deactivate  Finalize
```

## Configuration System

### StrategyConfig Parameters

```python
config = StrategyConfig(
    # Required
    strategy_name="MyStrategy",

    # Risk Management
    max_position_size=10,           # Maximum contracts held
    max_daily_loss=1000.0,          # Daily loss limit ($)
    max_daily_trades=100,           # Daily trade limit

    # Order Management
    default_order_size=1,           # Default order size
    enable_stop_loss=True,          # Enable automatic stop losses
    stop_loss_pct=0.005,           # Stop loss percentage (0.5%)

    # Timing Controls
    trading_start_time="09:30:00",  # Market open time
    trading_end_time="16:00:00",    # Market close time

    # Custom Parameters
    custom_params={
        'param1': 'value1',
        'param2': 42,
        'param3': 0.123
    }
)
```

### Parameter Validation

The framework automatically validates all configuration parameters:

- Position sizes must be positive
- Loss limits must be positive
- Stop loss percentages must be between 0 and 1
- Trading times must be valid

## Data Access

### Level 1 Data Access

```python
def process_tick(self, tick: TickData):
    # Current market data
    last_price = self.get_last_price()
    last_volume = self.get_last_volume()

    # Tick details
    price = tick.price
    volume = tick.qty
    side = tick.side  # 1=Buy, -1=Sell, 0=Unknown
    timestamp = tick.timestamp
```

### Level 2 Data Access (Order Book)

```python
# Access through signal generator's market microstructure tools
from strategy_lab.strategies.base import MarketMicrostructure

def analyze_order_book(self, bid_price, ask_price, bid_size, ask_size):
    # Calculate spread
    spread = MarketMicrostructure.calculate_spread(bid_price, ask_price)
    spread_bps = MarketMicrostructure.calculate_spread_bps(bid_price, ask_price)

    # Order flow analysis
    imbalance = MarketMicrostructure.calculate_order_flow_imbalance(bid_size, ask_size)

    return spread, spread_bps, imbalance
```

### Historical Data Access

```python
def initialize(self):
    # Maintain price history buffer
    self.price_history = deque(maxlen=100)
    self.volume_history = deque(maxlen=100)

def process_tick(self, tick: TickData):
    # Update history
    self.price_history.append(tick.price)
    self.volume_history.append(tick.qty)

    # Calculate indicators
    if len(self.price_history) >= 20:
        sma_20 = sum(list(self.price_history)[-20:]) / 20
```

## Signal Generation

### Built-in Technical Indicators

```python
from strategy_lab.strategies.base import TechnicalIndicators

def calculate_indicators(self, prices):
    # Moving averages
    sma_10 = TechnicalIndicators.simple_moving_average(prices, 10)
    ema_10 = TechnicalIndicators.exponential_moving_average(prices, 10)

    # Momentum indicators
    rsi = TechnicalIndicators.rsi(prices, 14)

    # Volatility indicators
    bb_bands = TechnicalIndicators.bollinger_bands(prices, 20, 2.0)

    return sma_10, ema_10, rsi, bb_bands
```

### Signal Generator Usage

```python
from strategy_lab.strategies.base import SignalGenerator, SignalType

def initialize(self):
    self.signal_generator = SignalGenerator(self.config)

def process_tick(self, tick: TickData):
    # Generate signals using built-in methods
    mean_reversion_signal = self.signal_generator.generate_mean_reversion_signal(tick)
    momentum_signal = self.signal_generator.generate_momentum_signal(tick)
    rsi_signal = self.signal_generator.generate_rsi_signal(tick)

    # Act on signals
    if mean_reversion_signal and mean_reversion_signal.signal_type == SignalType.BUY:
        if mean_reversion_signal.strength > 0.7:
            self.submit_market_order(OrderSide.BUY, 1)
```

### Custom Signal Generation

```python
def generate_custom_signal(self, tick: TickData):
    """Custom signal based on proprietary logic."""
    if len(self.price_history) < 50:
        return None

    # Custom indicator calculation
    recent_high = max(self.price_history[-20:])
    recent_low = min(self.price_history[-20:])
    current_price = tick.price

    # Generate signal
    if current_price <= recent_low * 1.001:  # Near recent low
        return Signal(
            signal_type=SignalType.BUY,
            strength=0.8,
            price=current_price,
            timestamp=tick.timestamp,
            confidence=0.75,
            metadata={'indicator': 'custom_reversal'}
        )

    return None
```

## Order Management

### Order Submission

```python
def execute_trades(self, tick: TickData):
    # Market orders (immediate execution)
    buy_order_id = self.submit_market_order(OrderSide.BUY, 2, tick.timestamp)
    sell_order_id = self.submit_market_order(OrderSide.SELL, 1, tick.timestamp)

    # Limit orders (pending execution)
    limit_order_id = self.submit_limit_order(
        OrderSide.BUY,
        1,
        13000.25,  # Limit price
        tick.timestamp
    )

    # Order cancellation
    success = self.cancel_order(limit_order_id, tick.timestamp)
```

### Position Management

```python
def check_position_status(self):
    # Current position information
    position = self.get_current_position()

    is_flat = position['is_flat']
    is_long = position['is_long']
    is_short = position['is_short']
    quantity = position['quantity']
    avg_price = position['average_price']
    unrealized_pnl = position['unrealized_pnl']
    realized_pnl = position['realized_pnl']

    # Position manager methods
    can_enter_long = self.position_manager.can_enter_long(2)
    can_add_to_position = self.position_manager.can_add_to_long(1)
    should_stop_out = self.position_manager.should_stop_out()
    should_take_profit = self.position_manager.should_take_profit()
```

## Risk Management

### Automatic Risk Controls

```python
# Configured via StrategyConfig
config = StrategyConfig(
    strategy_name="RiskManagedStrategy",
    max_position_size=5,        # Position limit
    max_daily_loss=1000.0,      # Daily loss limit
    stop_loss_pct=0.02,         # 2% stop loss
    max_daily_trades=50         # Trade frequency limit
)
```

### Custom Risk Checks

```python
def _validate_trade(self, side: OrderSide, quantity: int) -> bool:
    """Custom trade validation logic."""

    # Check time-based restrictions
    current_hour = datetime.now().hour
    if current_hour < 9 or current_hour > 16:
        return False

    # Check volatility conditions
    if self._calculate_volatility() > 0.05:  # 5% volatility threshold
        return False

    # Check correlation with other positions
    if self._check_correlation_risk(side):
        return False

    return True

def process_tick(self, tick: TickData):
    if self.should_enter_position(tick):
        if self._validate_trade(OrderSide.BUY, 1):
            self.submit_market_order(OrderSide.BUY, 1)
```

### Risk Metrics Monitoring

```python
def monitor_risk_metrics(self):
    """Monitor real-time risk metrics."""
    metrics = self.position_manager.get_risk_metrics()

    position_utilization = metrics['position_utilization']  # % of max position
    daily_loss_utilization = metrics['daily_loss_utilization']  # % of max loss
    current_drawdown = metrics['current_drawdown']
    max_drawdown = metrics['max_drawdown']

    # Custom risk actions
    if position_utilization > 80:
        self.reduce_position_size()

    if daily_loss_utilization > 90:
        self.pause_trading()
```

## State Management

### Strategy State Persistence

```python
def initialize(self):
    # Initialize strategy state
    self.strategy_data.update({
        'last_signal_time': 0,
        'trade_count': 0,
        'custom_indicator': 0.0
    })

def process_tick(self, tick: TickData):
    # Update state
    self.strategy_data['last_signal_time'] = tick.timestamp
    self.strategy_data['trade_count'] += 1
    self.strategy_data['custom_indicator'] = self.calculate_custom_indicator()

def save_state(self):
    """Save current strategy state."""
    state = self.get_strategy_state()
    # Save to file, database, etc.

def restore_state(self, saved_state):
    """Restore previously saved state."""
    self.set_strategy_state(saved_state)
```

### Performance Tracking

```python
def get_performance_summary(self):
    """Get comprehensive performance metrics."""
    return {
        'total_trades': self.metrics.total_trades,
        'win_rate': self.metrics.win_rate,
        'gross_pnl': self.metrics.gross_pnl,
        'net_pnl': self.metrics.net_pnl,
        'max_drawdown': self.position_manager.max_drawdown,
        'sharpe_ratio': self.calculate_sharpe_ratio(),
        'return_pct': self.position_manager.get_position_info().return_pct
    }
```

## Event Handling

### Strategy Lifecycle Events

```python
def on_market_open(self):
    """Custom logic for market open."""
    self.reset_daily_counters()
    self.recalibrate_parameters()
    logger.info("Market opened - strategy active")

def on_market_close(self):
    """Custom logic for market close."""
    self.close_all_positions()
    self.save_daily_summary()
    logger.info("Market closed - strategy inactive")

def on_order_filled(self, fill: Fill):
    """Custom logic for order fills."""
    logger.info(f"Fill: {fill.quantity} @ {fill.price}")
    self.update_custom_metrics(fill)

def on_error(self, error: Exception):
    """Custom error handling."""
    logger.error(f"Strategy error: {error}")
    if isinstance(error, CriticalError):
        self.emergency_shutdown()
```

## Example Strategies

### 1. Moving Average Crossover

See `src/strategy_lab/strategies/examples/moving_average_crossover.py` for a complete implementation demonstrating:

- Parameter configuration
- Technical indicator usage
- Signal generation and validation
- Order execution logic
- Risk management integration
- State persistence
- Performance tracking

### 2. Mean Reversion Strategy

```python
class MeanReversionStrategy(StrategyBase):
    def initialize(self):
        self.lookback_period = self.config.custom_params.get('lookback_period', 20)
        self.z_score_threshold = self.config.custom_params.get('z_score_threshold', 2.0)
        self.price_history = deque(maxlen=self.lookback_period * 2)

    def process_tick(self, tick: TickData):
        self.price_history.append(tick.price)

        if len(self.price_history) >= self.lookback_period:
            signal = self.signal_generator.generate_mean_reversion_signal(
                tick, self.lookback_period, self.z_score_threshold
            )

            if signal and signal.strength > 0.6:
                if signal.signal_type == SignalType.BUY:
                    self.submit_market_order(OrderSide.BUY, 1)
                elif signal.signal_type == SignalType.SELL:
                    self.submit_market_order(OrderSide.SELL, 1)
```

## Testing

### Unit Testing

```python
import pytest
from unittest.mock import Mock
from strategy_lab.strategies.base import StrategyConfig
from my_strategy import MyStrategy

def test_strategy_initialization():
    config = StrategyConfig(strategy_name="Test")
    adapter = Mock()
    strategy = MyStrategy(config, adapter)

    strategy.initialize()
    assert strategy.entry_threshold is not None

def test_signal_generation():
    # Test signal generation logic
    strategy = create_test_strategy()
    tick = create_test_tick(price=13000.0)

    signal = strategy.generate_custom_signal(tick)
    assert signal is None  # Insufficient data

    # Add sufficient data
    for price in range(13000, 13050):
        strategy.process_tick(create_test_tick(price=price))

    signal = strategy.generate_custom_signal(tick)
    assert signal is not None
```

### Integration Testing

```python
def test_strategy_with_backtest():
    """Test strategy with full backtest simulation."""
    config = create_test_config()
    adapter = create_test_adapter()
    strategy = MyStrategy(config, adapter)

    # Run simulated backtest
    results = run_test_backtest(strategy, test_data)

    assert results.total_trades > 0
    assert results.net_pnl != 0
    assert abs(results.max_drawdown) < 1000  # Risk limit check
```

## Best Practices

### 1. Parameter Management
- Use `custom_params` for strategy-specific configuration
- Validate all parameters in `initialize()`
- Document parameter ranges and defaults
- Use meaningful parameter names

### 2. Risk Management
- Always implement position limits
- Use stop losses and take profits
- Monitor daily loss limits
- Implement correlation checks

### 3. Performance Optimization
- Use efficient data structures (deque for buffers)
- Limit historical data retention
- Cache expensive calculations
- Profile critical code paths

### 4. Error Handling
- Handle all exceptions gracefully
- Log errors with sufficient context
- Implement fallback logic
- Use circuit breakers for critical errors

### 5. Logging and Monitoring
- Log all trading decisions
- Track performance metrics
- Monitor risk exposures
- Alert on unusual conditions

### 6. Code Organization
- Keep trading logic in `process_tick()`
- Use helper methods for complex calculations
- Separate signal generation from execution
- Document all public methods

## Troubleshooting

### Common Issues

1. **Strategy not receiving ticks**: Check callback registration
2. **Orders not executing**: Verify risk limit compliance
3. **Position tracking errors**: Check fill processing logic
4. **Memory issues**: Limit historical data buffers
5. **Performance degradation**: Profile indicator calculations

### Debug Tools

```python
def debug_strategy_state(self):
    """Print comprehensive strategy state for debugging."""
    print(f"Strategy: {self.config.strategy_name}")
    print(f"State: {self.state.value}")
    print(f"Position: {self.get_current_position()}")
    print(f"Metrics: {self.metrics}")
    print(f"Custom Data: {self.strategy_data}")
    print(f"Risk Metrics: {self.position_manager.get_risk_metrics()}")
```

## Advanced Features

### Multi-Asset Strategies

```python
class MultiAssetStrategy(StrategyBase):
    def initialize(self):
        self.symbols = ['MNQ', 'MES', 'MYM']  # Multiple futures
        self.correlations = {}

    def process_tick(self, tick: TickData):
        symbol = self.detect_symbol(tick)  # Custom symbol detection
        self.update_correlations(symbol, tick.price)

        if self.check_arbitrage_opportunity():
            self.execute_arbitrage_trade()
```

### Machine Learning Integration

```python
class MLStrategy(StrategyBase):
    def initialize(self):
        self.model = self.load_trained_model()
        self.feature_buffer = deque(maxlen=100)

    def process_tick(self, tick: TickData):
        features = self.extract_features(tick)
        self.feature_buffer.append(features)

        if len(self.feature_buffer) >= self.model.input_size:
            prediction = self.model.predict(list(self.feature_buffer))

            if prediction > 0.7:  # High confidence buy
                self.submit_market_order(OrderSide.BUY, 1)
```

This framework provides everything needed to implement sophisticated trading strategies while maintaining proper risk management and performance monitoring. The template-based approach ensures consistency and reliability across different strategy implementations.
