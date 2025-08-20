use crate::strategy::traits::{Strategy, Signal};
use crate::market::{MarketTick, OrderBookState};
use crate::data::types::MNQTick;
use rust_decimal::Decimal;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::VecDeque;

/// High-frequency backtesting engine with nanosecond precision
pub struct HFTBacktestEngine {
    config: HFTEngineConfig,
    order_book: OrderBookState,
    position: Position,
    equity_history: Vec<EquityPoint>,
    trades: Vec<Trade>,
    metrics: PerformanceMetrics,
    latency_model: LatencyModel,
    slippage_model: SlippageModel,
    commission_model: CommissionModel,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HFTEngineConfig {
    pub initial_capital: Decimal,
    pub max_position_size: u32,
    pub commission_per_contract: Decimal,
    pub min_tick_size: Decimal,
    pub enable_realistic_fills: bool,
    pub feed_latency_ns: u64,
    pub order_latency_ns: u64,
    pub queue_position_modeling: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Position {
    pub size: i32,
    pub avg_entry_price: Decimal,
    pub unrealized_pnl: Decimal,
    pub realized_pnl: Decimal,
    pub last_update_time: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Trade {
    pub trade_id: u64,
    pub entry_time: u64,
    pub exit_time: u64,
    pub side: TradeSide,
    pub entry_price: Decimal,
    pub exit_price: Decimal,
    pub quantity: u32,
    pub pnl: Decimal,
    pub commission: Decimal,
    pub slippage: Decimal,
    pub max_adverse_excursion: Decimal,
    pub max_favorable_excursion: Decimal,
    pub entry_latency_ns: u64,
    pub exit_latency_ns: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TradeSide {
    Long,
    Short,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EquityPoint {
    pub timestamp: u64,
    pub equity: Decimal,
    pub position_value: Decimal,
    pub cash: Decimal,
    pub unrealized_pnl: Decimal,
    pub drawdown: f64,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct PerformanceMetrics {
    pub total_return: f64,
    pub annualized_return: f64,
    pub sharpe_ratio: f64,
    pub sortino_ratio: f64,
    pub max_drawdown: f64,
    pub calmar_ratio: f64,
    pub win_rate: f64,
    pub profit_factor: f64,
    pub total_trades: u32,
    pub avg_trade_duration_ns: u64,
    pub avg_win: f64,
    pub avg_loss: f64,
    pub largest_win: f64,
    pub largest_loss: f64,
    pub consecutive_wins: u32,
    pub consecutive_losses: u32,
    pub max_consecutive_wins: u32,
    pub max_consecutive_losses: u32,
    pub commission_total: Decimal,
    pub slippage_total: Decimal,
}

pub struct LatencyModel {
    feed_latency_ns: u64,
    order_latency_ns: u64,
    jitter_range_ns: u64,
}

pub struct SlippageModel {
    base_slippage_ticks: f64,
    volume_impact_factor: f64,
    volatility_impact_factor: f64,
}

pub struct CommissionModel {
    per_contract: Decimal,
    minimum_fee: Decimal,
    exchange_fees: Decimal,
    clearing_fees: Decimal,
}

impl Default for HFTEngineConfig {
    fn default() -> Self {
        Self {
            initial_capital: Decimal::new(100_000, 0), // $100,000
            max_position_size: 10,
            commission_per_contract: Decimal::new(250, 2), // $2.50
            min_tick_size: Decimal::new(25, 2), // $0.25 for MNQ
            enable_realistic_fills: true,
            feed_latency_ns: 500_000, // 500 microseconds
            order_latency_ns: 1_000_000, // 1 millisecond
            queue_position_modeling: true,
        }
    }
}

impl HFTBacktestEngine {
    pub fn new(config: HFTEngineConfig) -> Self {
        Self {
            config: config.clone(),
            order_book: OrderBookState::default(),
            position: Position {
                size: 0,
                avg_entry_price: Decimal::ZERO,
                unrealized_pnl: Decimal::ZERO,
                realized_pnl: Decimal::ZERO,
                last_update_time: 0,
            },
            equity_history: Vec::new(),
            trades: Vec::new(),
            metrics: PerformanceMetrics::default(),
            latency_model: LatencyModel::new(config.feed_latency_ns, config.order_latency_ns),
            slippage_model: SlippageModel::default(),
            commission_model: CommissionModel::new(config.commission_per_contract),
        }
    }

    pub async fn run_backtest<S: Strategy>(
        &mut self,
        mut strategy: S,
        ticks: Vec<MNQTick>,
        start_time: u64,
        end_time: u64,
    ) -> Result<BacktestResult, BacktestError> {
        
        // Initialize strategy
        strategy.initialize();

        let mut processed_ticks = 0;
        let mut pending_orders: VecDeque<PendingOrder> = VecDeque::new();
        let mut current_signals: Vec<Signal> = Vec::new();

        println!("Starting HFT backtest with {} ticks", ticks.len());

        for (tick_index, tick) in ticks.iter().enumerate() {
            if tick.timestamp < start_time || tick.timestamp > end_time {
                continue;
            }

            // Apply feed latency
            let delayed_timestamp = tick.timestamp + self.latency_model.get_feed_latency();

            // Update order book with tick data
            self.update_order_book_from_tick(tick);

            // Process any pending orders that should now be filled
            self.process_pending_orders(&mut pending_orders, tick, delayed_timestamp);

            // Update position valuation
            self.update_position_valuation(tick);

            // Get strategy signals with latency-adjusted data
            match tick.mdt {
                // Only process signals on trade ticks and top-of-book updates
                2 => { // Last trade
                    if let Some(signal) = strategy.on_tick(&MarketTick::from_mnq_tick(tick)) {
                        current_signals.push(signal);
                    }
                },
                0 | 1 => { // Bid/Ask updates
                    if let Some(signal) = strategy.on_order_book_update(&self.order_book) {
                        current_signals.push(signal);
                    }
                },
                _ => {}
            }

            // Process signals and generate orders
            for signal in current_signals.drain(..) {
                if let Some(order) = self.process_signal(signal, tick, delayed_timestamp) {
                    pending_orders.push_back(order);
                }
            }

            // Record equity point every 1000 ticks to manage memory
            if tick_index % 1000 == 0 {
                self.record_equity_point(tick.timestamp);
            }

            processed_ticks += 1;

            if processed_ticks % 100_000 == 0 {
                println!("Processed {} ticks ({:.1}%)", 
                    processed_ticks, 
                    (tick_index as f64 / ticks.len() as f64) * 100.0
                );
            }
        }

        // Process any remaining pending orders
        self.close_all_positions(end_time);

        // Calculate final metrics
        self.calculate_performance_metrics(start_time, end_time);

        Ok(BacktestResult {
            initial_capital: self.config.initial_capital,
            final_equity: self.get_current_equity(),
            performance: self.metrics.clone(),
            trades: self.trades.clone(),
            equity_curve: self.equity_history.clone(),
            ticks_processed: processed_ticks,
            start_time,
            end_time,
        })
    }

    fn update_order_book_from_tick(&mut self, tick: &MNQTick) {
        match tick.mdt {
            0 => { // Ask
                self.order_book.best_ask = Some(tick.price);
                self.order_book.ask_volume = Some(tick.volume as u32);
            },
            1 => { // Bid
                self.order_book.best_bid = Some(tick.price);
                self.order_book.bid_volume = Some(tick.volume as u32);
            },
            2 => { // Last trade
                self.order_book.last_trade_price = Some(tick.price);
                self.order_book.last_trade_volume = Some(tick.volume as u32);
                self.order_book.last_trade_time = tick.timestamp;
            },
            _ => {}
        }
        self.order_book.last_update_time = tick.timestamp;
    }

    fn process_signal(&mut self, signal: Signal, tick: &MNQTick, timestamp: u64) -> Option<PendingOrder> {
        let order_latency = self.latency_model.get_order_latency();
        let fill_timestamp = timestamp + order_latency;

        match signal {
            Signal::Buy { quantity, price } => {
                if self.position.size + quantity as i32 <= self.config.max_position_size as i32 {
                    Some(PendingOrder {
                        side: OrderSide::Buy,
                        quantity,
                        price,
                        timestamp: fill_timestamp,
                        original_timestamp: timestamp,
                        latency_ns: order_latency,
                    })
                } else {
                    None // Position size limit exceeded
                }
            },
            Signal::Sell { quantity, price } => {
                if self.position.size - quantity as i32 >= -(self.config.max_position_size as i32) {
                    Some(PendingOrder {
                        side: OrderSide::Sell,
                        quantity,
                        price,
                        timestamp: fill_timestamp,
                        original_timestamp: timestamp,
                        latency_ns: order_latency,
                    })
                } else {
                    None // Position size limit exceeded
                }
            },
            _ => None,
        }
    }

    fn process_pending_orders(&mut self, pending_orders: &mut VecDeque<PendingOrder>, tick: &MNQTick, timestamp: u64) {
        let mut orders_to_remove = Vec::new();

        for (i, order) in pending_orders.iter().enumerate() {
            if timestamp >= order.timestamp {
                if self.should_fill_order(order, tick) {
                    let fill_price = self.calculate_fill_price(order, tick);
                    self.execute_order(order, fill_price, timestamp);
                    orders_to_remove.push(i);
                }
            }
        }

        // Remove filled orders (in reverse order to maintain indices)
        for &i in orders_to_remove.iter().rev() {
            pending_orders.remove(i);
        }
    }

    fn should_fill_order(&self, order: &PendingOrder, tick: &MNQTick) -> bool {
        if tick.mdt != 2 { // Only fill on actual trades
            return false;
        }

        match order.side {
            OrderSide::Buy => {
                // Buy order fills if market price is at or below our price
                tick.price <= order.price
            },
            OrderSide::Sell => {
                // Sell order fills if market price is at or above our price  
                tick.price >= order.price
            },
        }
    }

    fn calculate_fill_price(&self, order: &PendingOrder, tick: &MNQTick) -> Decimal {
        let mut fill_price = order.price;

        // Apply slippage
        let slippage = self.slippage_model.calculate_slippage(order, &self.order_book);
        match order.side {
            OrderSide::Buy => fill_price += Decimal::from_f64_retain(slippage).unwrap_or(Decimal::ZERO),
            OrderSide::Sell => fill_price -= Decimal::from_f64_retain(slippage).unwrap_or(Decimal::ZERO),
        }

        fill_price
    }

    fn execute_order(&mut self, order: &PendingOrder, fill_price: Decimal, timestamp: u64) {
        let commission = self.commission_model.calculate_commission(order.quantity);
        
        match order.side {
            OrderSide::Buy => {
                if self.position.size <= 0 {
                    // Opening long or covering short
                    if self.position.size < 0 {
                        // Covering short position
                        let cover_quantity = (-self.position.size).min(order.quantity as i32);
                        let cover_pnl = (self.position.avg_entry_price - fill_price) * Decimal::from(cover_quantity);
                        self.position.realized_pnl += cover_pnl - commission;
                        
                        if cover_quantity < order.quantity as i32 {
                            // Opening new long position with remaining quantity
                            let long_quantity = order.quantity as i32 - cover_quantity;
                            self.position.size = long_quantity;
                            self.position.avg_entry_price = fill_price;
                        } else {
                            self.position.size += cover_quantity;
                        }
                    } else {
                        // Opening long position
                        self.position.size = order.quantity as i32;
                        self.position.avg_entry_price = fill_price;
                    }
                } else {
                    // Adding to long position
                    let total_value = (self.position.avg_entry_price * Decimal::from(self.position.size)) + 
                                     (fill_price * Decimal::from(order.quantity));
                    let total_quantity = self.position.size + order.quantity as i32;
                    self.position.avg_entry_price = total_value / Decimal::from(total_quantity);
                    self.position.size = total_quantity;
                }
            },
            OrderSide::Sell => {
                if self.position.size >= 0 {
                    // Closing long or opening short
                    if self.position.size > 0 {
                        // Closing long position
                        let close_quantity = self.position.size.min(order.quantity as i32);
                        let close_pnl = (fill_price - self.position.avg_entry_price) * Decimal::from(close_quantity);
                        self.position.realized_pnl += close_pnl - commission;
                        
                        if close_quantity < order.quantity as i32 {
                            // Opening new short position with remaining quantity
                            let short_quantity = order.quantity as i32 - close_quantity;
                            self.position.size = -short_quantity;
                            self.position.avg_entry_price = fill_price;
                        } else {
                            self.position.size -= close_quantity;
                        }
                    } else {
                        // Opening short position
                        self.position.size = -(order.quantity as i32);
                        self.position.avg_entry_price = fill_price;
                    }
                } else {
                    // Adding to short position
                    let total_value = (self.position.avg_entry_price * Decimal::from(-self.position.size)) + 
                                     (fill_price * Decimal::from(order.quantity));
                    let total_quantity = (-self.position.size) + order.quantity as i32;
                    self.position.avg_entry_price = total_value / Decimal::from(total_quantity);
                    self.position.size = -total_quantity;
                }
            },
        }

        self.position.last_update_time = timestamp;
        
        // Record the trade (simplified for now)
        // In a full implementation, we'd track individual trade legs
    }

    fn update_position_valuation(&mut self, tick: &MNQTick) {
        if tick.mdt == 2 && self.position.size != 0 { // Last trade tick
            let current_price = tick.price;
            if self.position.size > 0 {
                // Long position
                self.position.unrealized_pnl = (current_price - self.position.avg_entry_price) * Decimal::from(self.position.size);
            } else {
                // Short position
                self.position.unrealized_pnl = (self.position.avg_entry_price - current_price) * Decimal::from(-self.position.size);
            }
        }
    }

    fn record_equity_point(&mut self, timestamp: u64) {
        let current_equity = self.get_current_equity();
        let position_value = if self.position.size != 0 {
            self.position.avg_entry_price * Decimal::from(self.position.size.abs())
        } else {
            Decimal::ZERO
        };

        // Calculate drawdown
        let peak_equity = self.equity_history.iter()
            .map(|p| p.equity)
            .fold(self.config.initial_capital, |acc, e| acc.max(e));
        
        let drawdown = if peak_equity > Decimal::ZERO {
            ((peak_equity - current_equity) / peak_equity).to_f64().unwrap_or(0.0)
        } else {
            0.0
        };

        self.equity_history.push(EquityPoint {
            timestamp,
            equity: current_equity,
            position_value,
            cash: self.config.initial_capital + self.position.realized_pnl,
            unrealized_pnl: self.position.unrealized_pnl,
            drawdown,
        });
    }

    fn get_current_equity(&self) -> Decimal {
        self.config.initial_capital + self.position.realized_pnl + self.position.unrealized_pnl
    }

    fn close_all_positions(&mut self, timestamp: u64) {
        if self.position.size != 0 {
            // Force close position at last known price
            // This is a simplification - in practice we'd need the last market price
            self.position.realized_pnl += self.position.unrealized_pnl;
            self.position.unrealized_pnl = Decimal::ZERO;
            self.position.size = 0;
            self.position.last_update_time = timestamp;
        }
    }

    fn calculate_performance_metrics(&mut self, start_time: u64, end_time: u64) {
        // Calculate basic performance metrics
        let initial_equity = self.config.initial_capital;
        let final_equity = self.get_current_equity();
        
        self.metrics.total_return = ((final_equity - initial_equity) / initial_equity).to_f64().unwrap_or(0.0);
        
        // Calculate other metrics based on equity curve
        if !self.equity_history.is_empty() {
            let returns: Vec<f64> = self.equity_history.windows(2)
                .map(|window| {
                    let prev = window[0].equity;
                    let curr = window[1].equity;
                    if prev > Decimal::ZERO {
                        ((curr - prev) / prev).to_f64().unwrap_or(0.0)
                    } else {
                        0.0
                    }
                })
                .collect();

            if !returns.is_empty() {
                let mean_return = returns.iter().sum::<f64>() / returns.len() as f64;
                let variance = returns.iter()
                    .map(|r| (r - mean_return).powi(2))
                    .sum::<f64>() / returns.len() as f64;
                let std_dev = variance.sqrt();

                self.metrics.sharpe_ratio = if std_dev > 0.0 { mean_return / std_dev } else { 0.0 };
                
                // Calculate max drawdown
                let mut peak = initial_equity;
                let mut max_dd = 0.0;
                for point in &self.equity_history {
                    if point.equity > peak {
                        peak = point.equity;
                    }
                    let dd = ((peak - point.equity) / peak).to_f64().unwrap_or(0.0);
                    if dd > max_dd {
                        max_dd = dd;
                    }
                }
                self.metrics.max_drawdown = max_dd;
            }
        }

        // Set trade-related metrics
        self.metrics.total_trades = self.trades.len() as u32;
        
        // Additional metrics would be calculated here...
        self.metrics.profit_factor = 1.0; // Placeholder
        self.metrics.win_rate = 0.5; // Placeholder
    }
}

#[derive(Debug, Clone)]
struct PendingOrder {
    side: OrderSide,
    quantity: u32,
    price: Decimal,
    timestamp: u64,
    original_timestamp: u64,
    latency_ns: u64,
}

#[derive(Debug, Clone)]
pub enum OrderSide {
    Buy,
    Sell,
}

impl LatencyModel {
    pub fn new(feed_latency_ns: u64, order_latency_ns: u64) -> Self {
        Self {
            feed_latency_ns,
            order_latency_ns,
            jitter_range_ns: feed_latency_ns / 10, // 10% jitter
        }
    }

    pub fn get_feed_latency(&self) -> u64 {
        // Add some randomness to simulate real-world conditions
        use rand::Rng;
        let mut rng = rand::thread_rng();
        let jitter = rng.gen_range(0..self.jitter_range_ns);
        self.feed_latency_ns + jitter
    }

    pub fn get_order_latency(&self) -> u64 {
        use rand::Rng;
        let mut rng = rand::thread_rng();
        let jitter = rng.gen_range(0..self.jitter_range_ns);
        self.order_latency_ns + jitter
    }
}

impl Default for SlippageModel {
    fn default() -> Self {
        Self {
            base_slippage_ticks: 0.1, // 0.1 ticks base slippage
            volume_impact_factor: 0.01,
            volatility_impact_factor: 0.02,
        }
    }
}

impl SlippageModel {
    pub fn calculate_slippage(&self, _order: &PendingOrder, _order_book: &OrderBookState) -> f64 {
        // Simplified slippage calculation
        // In practice, this would consider order size, market depth, volatility, etc.
        self.base_slippage_ticks * 0.25 // Convert to dollar amount (MNQ tick = $0.25)
    }
}

impl CommissionModel {
    pub fn new(per_contract: Decimal) -> Self {
        Self {
            per_contract,
            minimum_fee: Decimal::new(100, 2), // $1.00 minimum
            exchange_fees: Decimal::new(42, 2), // $0.42 exchange fee
            clearing_fees: Decimal::new(2, 2),  // $0.02 clearing fee
        }
    }

    pub fn calculate_commission(&self, quantity: u32) -> Decimal {
        let base_commission = self.per_contract * Decimal::from(quantity);
        let total_fees = (self.exchange_fees + self.clearing_fees) * Decimal::from(quantity);
        (base_commission + total_fees).max(self.minimum_fee)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BacktestResult {
    pub initial_capital: Decimal,
    pub final_equity: Decimal,
    pub performance: PerformanceMetrics,
    pub trades: Vec<Trade>,
    pub equity_curve: Vec<EquityPoint>,
    pub ticks_processed: u64,
    pub start_time: u64,
    pub end_time: u64,
}

impl Default for BacktestResult {
    fn default() -> Self {
        Self {
            initial_capital: Decimal::new(100_000, 0),
            final_equity: Decimal::new(100_000, 0),
            performance: PerformanceMetrics::default(),
            trades: Vec::new(),
            equity_curve: Vec::new(),
            ticks_processed: 0,
            start_time: 0,
            end_time: 0,
        }
    }
}

#[derive(Debug, thiserror::Error)]
pub enum BacktestError {
    #[error("Invalid configuration: {0}")]
    InvalidConfig(String),
    #[error("Data error: {0}")]
    DataError(String),
    #[error("Strategy error: {0}")]
    StrategyError(String),
    #[error("Engine error: {0}")]
    EngineError(String),
}