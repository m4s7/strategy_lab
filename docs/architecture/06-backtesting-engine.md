# Strategy Lab Technical Architecture - Backtesting Engine

## Backtesting Engine Overview

The backtesting engine integrates hftbacktest as the core simulation engine, providing high-performance tick-by-tick backtesting with accurate market mechanics simulation for MNQ futures.

## hftbacktest Integration Layer

### Main Backtesting Engine

```python
from hftbacktest import HftBacktest, Asset
import numpy as np
from typing import Dict, Any, Optional

class BacktestingEngine:
    """Main backtesting engine using hftbacktest"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.hft_engine = None
        self.strategy = None
        self.results = None
        self.event_processor = None
    
    def setup_engine(self, 
                    data_path: str, 
                    strategy: BaseStrategy,
                    start_date: Optional[str] = None,
                    end_date: Optional[str] = None) -> None:
        """Initialize hftbacktest engine with data and strategy"""
        # Load and prepare data
        data = self._prepare_data(data_path, start_date, end_date)
        
        # Configure MNQ asset specifications
        asset_info = self._get_mnq_asset_info()
        
        # Initialize hftbacktest
        self.hft_engine = HftBacktest(
            data=data,
            asset=Asset(
                tick_size=asset_info['tick_size'],
                lot_size=asset_info['lot_size'],
                maker_fee=asset_info['maker_fee'],
                taker_fee=asset_info['taker_fee'],
                exchange='CME'
            ),
            initial_balance=self.config.get('initial_balance', 100_000),
            latency_model=self._create_latency_model()
        )
        
        self.strategy = strategy
        self.event_processor = EventProcessor(strategy, self.hft_engine)
    
    def run_backtest(self) -> BacktestResults:
        """Execute backtest for configured period"""
        # Reset strategy state
        self.strategy.reset_state()
        
        # Initialize tracking
        performance_tracker = PerformanceTracker()
        
        # Main event loop
        while self.hft_engine.next():
            # Get current market state
            market_data = self._get_market_data()
            
            # Generate strategy signal
            signal = self.strategy.generate_signal(market_data)
            
            # Process signal through hftbacktest
            if signal.action != 'HOLD':
                self._execute_signal(signal)
            
            # Track performance
            performance_tracker.update(self.hft_engine.get_state())
        
        # Generate final results
        self.results = self._compile_results(performance_tracker)
        return self.results
    
    def _get_mnq_asset_info(self) -> Dict[str, Any]:
        """MNQ-specific trading parameters"""
        return {
            'tick_size': 0.25,
            'lot_size': 1,
            'maker_fee': -0.50,  # Rebate for liquidity providers
            'taker_fee': 2.50,   # Fee for liquidity takers
            'margin_requirement': 1_000,
            'trading_hours': {
                'sunday_open': '17:00',
                'friday_close': '16:00',
                'daily_break': ('16:00', '17:00')
            }
        }
    
    def _create_latency_model(self):
        """Create realistic latency model for backtesting"""
        return {
            'order_latency_ns': 1_000_000,  # 1ms order latency
            'market_data_latency_ns': 500_000,  # 0.5ms data latency
            'jitter_ns': 100_000  # 0.1ms jitter
        }
```

### Data Preparation for hftbacktest

```python
class HftBacktestDataPreparer:
    """Prepares data in hftbacktest format"""
    
    def prepare_tick_data(self, 
                         raw_data: pd.DataFrame) -> np.ndarray:
        """Convert DataFrame to hftbacktest numpy format"""
        # hftbacktest expects specific column order and types
        hft_data = np.zeros(
            len(raw_data),
            dtype=[
                ('timestamp', 'i8'),
                ('price', 'f8'),
                ('qty', 'f8'),
                ('side', 'i1'),
                ('type', 'i1')
            ]
        )
        
        # Map our data to hftbacktest format
        hft_data['timestamp'] = raw_data['timestamp'].values
        hft_data['price'] = raw_data['price'].values
        hft_data['qty'] = raw_data['volume'].values
        
        # Map MDT to side/type
        hft_data['side'] = self._map_side(raw_data['mdt'].values)
        hft_data['type'] = self._map_type(raw_data['mdt'].values)
        
        return hft_data
    
    def _map_side(self, mdt_values: np.ndarray) -> np.ndarray:
        """Map MDT values to buy/sell side"""
        # 0=Ask (sell side), 1=Bid (buy side), 2=Trade
        side_map = {0: -1, 1: 1, 2: 0}
        return np.vectorize(lambda x: side_map.get(x, 0))(mdt_values)
```

## Event Processing Architecture

### Event Processor Implementation

```python
class EventProcessor:
    """Processes market events and strategy signals"""
    
    def __init__(self, strategy: BaseStrategy, hft_engine: HftBacktest):
        self.strategy = strategy
        self.hft_engine = hft_engine
        self.pending_orders = {}
        self.active_orders = {}
        self.position_tracker = PositionTracker()
    
    def process_market_event(self) -> None:
        """Process current market event from hftbacktest"""
        event_type = self.hft_engine.get_event_type()
        
        if event_type == 'MARKET_DATA':
            self._handle_market_data()
        elif event_type == 'ORDER_FILL':
            self._handle_order_fill()
        elif event_type == 'ORDER_CANCEL':
            self._handle_order_cancel()
    
    def execute_signal(self, signal: Signal) -> Optional[str]:
        """Execute trading signal"""
        if signal.action == 'BUY':
            order_id = self._place_buy_order(signal)
        elif signal.action == 'SELL':
            order_id = self._place_sell_order(signal)
        else:
            return None
        
        # Track order
        self.pending_orders[order_id] = {
            'signal': signal,
            'timestamp': self.hft_engine.current_timestamp(),
            'status': 'PENDING'
        }
        
        return order_id
    
    def _place_buy_order(self, signal: Signal) -> str:
        """Place buy order through hftbacktest"""
        if signal.order_type == 'MARKET':
            return self.hft_engine.market_buy(
                qty=signal.quantity,
                user_data=signal.metadata
            )
        else:  # LIMIT
            return self.hft_engine.limit_buy(
                price=signal.price,
                qty=signal.quantity,
                user_data=signal.metadata
            )
    
    def _handle_order_fill(self) -> None:
        """Handle order fill event"""
        fill_data = self.hft_engine.get_fill_data()
        order_id = fill_data['order_id']
        
        if order_id in self.pending_orders:
            # Update order status
            self.pending_orders[order_id]['status'] = 'FILLED'
            self.pending_orders[order_id]['fill_price'] = fill_data['price']
            self.pending_orders[order_id]['fill_qty'] = fill_data['qty']
            
            # Notify strategy
            self.strategy.on_fill(
                fill_price=fill_data['price'],
                fill_quantity=fill_data['qty']
            )
            
            # Update position tracking
            self.position_tracker.update_position(
                qty=fill_data['qty'],
                price=fill_data['price'],
                side=fill_data['side']
            )
```

### Market Simulation Configuration

```python
class MarketSimulator:
    """Configures market simulation parameters"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.trading_calendar = TradingCalendar('CME')
    
    def create_simulation_params(self) -> Dict[str, Any]:
        """Create comprehensive market simulation parameters"""
        return {
            'order_latency': {
                'mean_ns': 1_000_000,  # 1ms average
                'std_ns': 100_000,     # 0.1ms standard deviation
                'min_ns': 500_000,     # 0.5ms minimum
                'max_ns': 5_000_000    # 5ms maximum
            },
            
            'fill_probability': {
                'market_order': 1.0,
                'limit_at_touch': 0.5,
                'limit_through': 1.0,
                'limit_away': 0.0
            },
            
            'slippage_model': {
                'base_slippage_ticks': 0,
                'size_impact_factor': 0.1,  # 0.1 tick per contract
                'urgency_factor': {
                    'passive': 0,
                    'normal': 0.25,
                    'aggressive': 0.5
                }
            },
            
            'market_impact': {
                'temporary_impact_factor': 0.01,
                'permanent_impact_factor': 0.001,
                'decay_time_seconds': 60
            }
        }
    
    def is_market_open(self, timestamp: int) -> bool:
        """Check if market is open at given timestamp"""
        dt = pd.Timestamp(timestamp, unit='ns')
        return self.trading_calendar.is_open(dt)
```

## Performance Tracking

### Real-time Performance Monitoring

```python
class PerformanceTracker:
    """Tracks performance metrics during backtesting"""
    
    def __init__(self):
        self.trades = []
        self.equity_curve = []
        self.positions = []
        self.drawdowns = []
        self.current_position = 0
        self.peak_equity = 0
        
    def update(self, engine_state: Dict[str, Any]) -> None:
        """Update tracking with current engine state"""
        timestamp = engine_state['timestamp']
        equity = engine_state['equity']
        position = engine_state['position']
        
        # Track equity curve
        self.equity_curve.append({
            'timestamp': timestamp,
            'equity': equity,
            'position': position
        })
        
        # Update peak and drawdown
        if equity > self.peak_equity:
            self.peak_equity = equity
        
        current_drawdown = (self.peak_equity - equity) / self.peak_equity
        self.drawdowns.append({
            'timestamp': timestamp,
            'drawdown': current_drawdown
        })
        
        # Detect new trades
        if position != self.current_position:
            self._record_trade(engine_state)
            self.current_position = position
    
    def _record_trade(self, engine_state: Dict[str, Any]) -> None:
        """Record trade details"""
        trade = {
            'timestamp': engine_state['timestamp'],
            'position_change': engine_state['position'] - self.current_position,
            'price': engine_state['last_fill_price'],
            'commission': engine_state['last_commission'],
            'realized_pnl': engine_state.get('realized_pnl', 0)
        }
        self.trades.append(trade)
    
    def calculate_metrics(self) -> PerformanceMetrics:
        """Calculate final performance metrics"""
        if not self.trades:
            return PerformanceMetrics.empty()
        
        returns = pd.Series([t['realized_pnl'] for t in self.trades])
        equity_series = pd.Series([e['equity'] for e in self.equity_curve])
        
        return PerformanceMetrics(
            total_trades=len(self.trades),
            winning_trades=len(returns[returns > 0]),
            losing_trades=len(returns[returns < 0]),
            total_pnl=returns.sum(),
            average_win=returns[returns > 0].mean() if len(returns[returns > 0]) > 0 else 0,
            average_loss=returns[returns < 0].mean() if len(returns[returns < 0]) > 0 else 0,
            win_rate=len(returns[returns > 0]) / len(returns) if len(returns) > 0 else 0,
            max_drawdown=max(self.drawdowns, key=lambda x: x['drawdown'])['drawdown'],
            sharpe_ratio=self._calculate_sharpe(equity_series),
            sortino_ratio=self._calculate_sortino(equity_series)
        )
```

## Backtest Results Compilation

### Results Aggregation

```python
class BacktestResults:
    """Comprehensive backtest results container"""
    
    def __init__(self, 
                 performance_metrics: PerformanceMetrics,
                 trades: List[Trade],
                 equity_curve: pd.DataFrame,
                 metadata: Dict[str, Any]):
        self.performance_metrics = performance_metrics
        self.trades = trades
        self.equity_curve = equity_curve
        self.metadata = metadata
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary format"""
        return {
            'summary': {
                'total_pnl': self.performance_metrics.total_pnl,
                'total_trades': self.performance_metrics.total_trades,
                'win_rate': self.performance_metrics.win_rate,
                'sharpe_ratio': self.performance_metrics.sharpe_ratio,
                'max_drawdown': self.performance_metrics.max_drawdown
            },
            'trades': [t.to_dict() for t in self.trades],
            'equity_curve': self.equity_curve.to_dict(),
            'metadata': self.metadata
        }
    
    def generate_report(self, output_path: str) -> None:
        """Generate comprehensive HTML report"""
        report_generator = BacktestReportGenerator()
        report_generator.generate(self, output_path)
```

## Integration with Strategy Framework

### Strategy Execution Bridge

```python
class StrategyExecutionBridge:
    """Bridges strategy signals with hftbacktest execution"""
    
    def __init__(self, 
                 strategy: BaseStrategy,
                 hft_engine: HftBacktest,
                 risk_manager: Optional[RiskManager] = None):
        self.strategy = strategy
        self.hft_engine = hft_engine
        self.risk_manager = risk_manager or DefaultRiskManager()
        
    def execute_tick(self) -> None:
        """Execute one tick of the backtest"""
        # Get current market data
        market_data = self._build_market_data()
        
        # Check risk limits
        if not self.risk_manager.check_limits():
            return
        
        # Generate signal
        signal = self.strategy.generate_signal(market_data)
        
        # Apply risk management
        adjusted_signal = self.risk_manager.adjust_signal(signal)
        
        # Execute if valid
        if adjusted_signal.action != 'HOLD':
            self._execute_order(adjusted_signal)
    
    def _build_market_data(self) -> MarketData:
        """Build market data object from hftbacktest state"""
        state = self.hft_engine.get_current_state()
        
        return MarketData(
            timestamp=state['timestamp'],
            bid=state['best_bid'],
            ask=state['best_ask'],
            last=state['last_price'],
            volume=state['last_volume'],
            book_state=self._get_book_state() if self.strategy.requires_l2 else None
        )
```