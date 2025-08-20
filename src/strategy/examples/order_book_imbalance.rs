//! Order Book Imbalance Strategy
//! 
//! This strategy trades based on imbalances between bid and ask volumes
//! in the order book. When there's significantly more volume on one side,
//! it predicts price movement in that direction.

use crate::data::TickData;
use crate::market::OrderBookState;
use crate::strategy::{
    Order, OrderSide, Position, Signal, SignalType,
    Strategy, StrategyConfig, StrategyContext, StrategyMetrics,
};
use crate::strategy::traits::OrderFill;
use rust_decimal::Decimal;
use tracing::{debug, info};

/// Order book imbalance scalping strategy
/// 
/// # Strategy Logic
/// - Calculates bid/ask volume imbalance at multiple depth levels
/// - Enters long when bid volume significantly exceeds ask volume
/// - Enters short when ask volume significantly exceeds bid volume
/// - Uses tight stop losses for risk management
/// - Exits on imbalance reversal or stop loss
pub struct OrderBookImbalanceStrategy {
    /// Strategy configuration
    config: StrategyConfig,
    
    /// Current position
    position: Position,
    
    /// Performance metrics
    metrics: StrategyMetrics,
    
    /// Imbalance threshold (0.5 to 1.0, higher = stronger signal required)
    imbalance_threshold: f64,
    
    /// Minimum spread required to trade
    min_spread: Decimal,
    
    /// Number of order book levels to analyze
    depth_levels: usize,
    
    /// Last signal generated
    last_signal: Option<Signal>,
    
    /// Entry price for current trade
    entry_price: Option<Decimal>,
}

impl OrderBookImbalanceStrategy {
    /// Create a new order book imbalance strategy
    pub fn new(config: StrategyConfig) -> Self {
        // Extract custom parameters from config
        let imbalance_threshold = config.parameters.custom
            .get("imbalance_threshold")
            .and_then(|v| v.as_f64())
            .unwrap_or(0.6);
        
        let min_spread = config.parameters.custom
            .get("min_spread")
            .and_then(|v| v.as_decimal())
            .unwrap_or(Decimal::from_str_exact("0.25").unwrap());
        
        let depth_levels = config.parameters.custom
            .get("depth_levels")
            .and_then(|v| v.as_f64())
            .map(|v| v as usize)
            .unwrap_or(3);
        
        Self {
            config,
            position: Position::new(),
            metrics: StrategyMetrics::default(),
            imbalance_threshold,
            min_spread,
            depth_levels,
            last_signal: None,
            entry_price: None,
        }
    }
    
    /// Calculate order book imbalance
    fn calculate_imbalance(&self, book: &OrderBookState) -> f64 {
        // Sum volumes at specified depth levels
        let mut bid_volume = 0i64;
        let mut ask_volume = 0i64;
        
        // Get bid volumes
        for (i, (_, level)) in book.bids.iter().rev().enumerate() {
            if i >= self.depth_levels {
                break;
            }
            bid_volume += level.volume as i64;
        }
        
        // Get ask volumes
        for (i, (_, level)) in book.asks.iter().enumerate() {
            if i >= self.depth_levels {
                break;
            }
            ask_volume += level.volume as i64;
        }
        
        // Calculate imbalance ratio
        let total_volume = bid_volume + ask_volume;
        if total_volume == 0 {
            return 0.0;
        }
        
        (bid_volume - ask_volume) as f64 / total_volume as f64
    }
    
    /// Generate trading signal based on imbalance
    fn generate_signal(&mut self, imbalance: f64, context: &StrategyContext) -> Option<Signal> {
        let mid_price = context.mid_price()?;
        let spread = context.spread()?;
        
        // Check minimum spread requirement
        if spread < self.min_spread {
            debug!("Spread too tight: {} < {}", spread, self.min_spread);
            return None;
        }
        
        // Generate signals based on imbalance
        if imbalance > self.imbalance_threshold {
            // Strong bid imbalance - expect price to go up
            info!("Long signal: imbalance={:.3}, threshold={}", imbalance, self.imbalance_threshold);
            Some(Signal::long(
                imbalance.abs(),
                mid_price,
                format!("Bid imbalance: {:.3}", imbalance),
            ))
        } else if imbalance < -self.imbalance_threshold {
            // Strong ask imbalance - expect price to go down
            info!("Short signal: imbalance={:.3}, threshold={}", imbalance, self.imbalance_threshold);
            Some(Signal::short(
                imbalance.abs(),
                mid_price,
                format!("Ask imbalance: {:.3}", imbalance),
            ))
        } else if !self.position.is_flat() {
            // Check for exit conditions
            self.check_exit_conditions(imbalance, mid_price)
        } else {
            None
        }
    }
    
    /// Check if we should exit current position
    fn check_exit_conditions(&self, imbalance: f64, current_price: Decimal) -> Option<Signal> {
        // Exit if imbalance reverses
        if self.position.is_long() && imbalance < 0.0 {
            return Some(Signal::exit(
                current_price,
                "Imbalance reversed against long position".to_string(),
            ));
        }
        
        if self.position.is_short() && imbalance > 0.0 {
            return Some(Signal::exit(
                current_price,
                "Imbalance reversed against short position".to_string(),
            ));
        }
        
        // Check stop loss
        if let Some(entry) = self.entry_price {
            let pnl = if self.position.is_long() {
                current_price - entry
            } else {
                entry - current_price
            };
            
            if pnl < -self.config.parameters.stop_loss {
                return Some(Signal::exit(
                    current_price,
                    format!("Stop loss triggered: PnL={}", pnl),
                ));
            }
            
            // Check take profit if configured
            if let Some(take_profit) = self.config.parameters.take_profit {
                if pnl > take_profit {
                    return Some(Signal::exit(
                        current_price,
                        format!("Take profit triggered: PnL={}", pnl),
                    ));
                }
            }
        }
        
        None
    }
}

impl Strategy for OrderBookImbalanceStrategy {
    fn on_tick(&mut self, tick: &TickData, context: &StrategyContext) -> Option<Order> {
        // Update position P&L
        if let Some(mid_price) = context.mid_price() {
            self.position.update_unrealized_pnl(mid_price);
        }
        
        // Calculate imbalance
        let imbalance = self.calculate_imbalance(&context.order_book);
        debug!("Order book imbalance: {:.3}", imbalance);
        
        // Generate signal
        let signal = self.generate_signal(imbalance, context)?;
        self.last_signal = Some(signal.clone());
        
        // Convert signal to order
        match signal.signal_type {
            SignalType::Long if self.position.is_flat() => {
                self.entry_price = Some(tick.price);
                Some(Order::market(OrderSide::Buy, self.config.parameters.position_size))
            }
            SignalType::Short if self.position.is_flat() => {
                self.entry_price = Some(tick.price);
                Some(Order::market(OrderSide::Sell, self.config.parameters.position_size))
            }
            SignalType::Exit if !self.position.is_flat() => {
                let side = if self.position.is_long() {
                    OrderSide::Sell
                } else {
                    OrderSide::Buy
                };
                Some(Order::market(side, self.position.size.abs()))
            }
            _ => None,
        }
    }
    
    fn on_order_fill(&mut self, fill: &OrderFill) {
        // Update position
        let was_flat = self.position.is_flat();
        self.position.apply_fill(fill);
        
        // Update metrics if position closed
        if !was_flat && self.position.is_flat() {
            let pnl = self.position.realized_pnl;
            let duration = fill.timestamp.signed_duration_since(
                self.position.open_time.unwrap_or(fill.timestamp)
            ).num_seconds() as f64;
            
            self.metrics.update_trade(pnl, duration);
            self.entry_price = None;
        }
        
        info!("Order filled: {:?}, Position: {} @ {}", 
            fill.side, self.position.size, self.position.avg_entry_price);
    }
    
    fn get_parameters(&self) -> &StrategyConfig {
        &self.config
    }
    
    fn reset(&mut self) {
        self.position.reset();
        self.metrics = StrategyMetrics::default();
        self.last_signal = None;
        self.entry_price = None;
        info!("Strategy reset");
    }
    
    fn get_position(&self) -> &Position {
        &self.position
    }
    
    fn get_metrics(&self) -> StrategyMetrics {
        self.metrics.clone()
    }
    
    fn on_order_book_update(&mut self, book: &OrderBookState) -> Option<Signal> {
        // Additional order book analysis can be performed here
        // For now, we handle everything in on_tick
        None
    }
}