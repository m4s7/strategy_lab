//! Bid-Ask Bounce Strategy
//! 
//! This strategy trades the bounce between bid and ask prices,
//! entering positions when price touches one side and expecting
//! it to bounce back to the other side.

use crate::data::TickData;
use crate::market::OrderBookState;
use crate::strategy::{
    Order, OrderFill, OrderSide, Position, Signal, SignalType,
    Strategy, StrategyConfig, StrategyContext, StrategyMetrics,
};
use rust_decimal::Decimal;
use tracing::{debug, info};

/// Bid-ask bounce scalping strategy
/// 
/// # Strategy Logic
/// - Monitors when price touches the bid or ask
/// - Enters long when price hits bid with sufficient volume
/// - Enters short when price hits ask with sufficient volume
/// - Expects price to bounce back to mid or opposite side
/// - Uses tight stops and quick exits
pub struct BidAskBounceStrategy {
    /// Strategy configuration
    config: StrategyConfig,
    
    /// Current position
    position: Position,
    
    /// Performance metrics
    metrics: StrategyMetrics,
    
    /// Minimum bounce expected (in ticks)
    bounce_threshold: Decimal,
    
    /// Minimum volume required at touch
    min_volume: i32,
    
    /// Offset from bid/ask for entry
    entry_offset: Decimal,
    
    /// Last touch side tracked
    last_touch_side: Option<TouchSide>,
    
    /// Number of touches before entry
    touch_count: u32,
    
    /// Required touches before entering
    required_touches: u32,
}

#[derive(Debug, Clone, Copy, PartialEq)]
enum TouchSide {
    Bid,
    Ask,
}

impl BidAskBounceStrategy {
    /// Create a new bid-ask bounce strategy
    pub fn new(config: StrategyConfig) -> Self {
        // Extract custom parameters
        let bounce_threshold = config.parameters.custom
            .get("bounce_threshold")
            .and_then(|v| v.as_decimal())
            .unwrap_or(Decimal::from_str_exact("0.5").unwrap());
        
        let min_volume = config.parameters.custom
            .get("min_volume")
            .and_then(|v| v.as_f64())
            .map(|v| v as i32)
            .unwrap_or(100);
        
        let entry_offset = config.parameters.custom
            .get("entry_offset")
            .and_then(|v| v.as_decimal())
            .unwrap_or(Decimal::from_str_exact("0.1").unwrap());
        
        Self {
            config,
            position: Position::new(),
            metrics: StrategyMetrics::default(),
            bounce_threshold,
            min_volume,
            entry_offset,
            last_touch_side: None,
            touch_count: 0,
            required_touches: 2,
        }
    }
    
    /// Detect if price is touching bid or ask
    fn detect_touch(&mut self, tick: &TickData, book: &OrderBookState) -> Option<TouchSide> {
        let (best_bid, best_ask) = match (book.best_bid, book.best_ask) {
            (Some(bid), Some(ask)) => (bid, ask),
            _ => return None,
        };
        
        // Check if price is at bid
        if (tick.price - best_bid).abs() < Decimal::from_str_exact("0.01").unwrap() {
            if tick.volume >= self.min_volume {
                return Some(TouchSide::Bid);
            }
        }
        
        // Check if price is at ask
        if (tick.price - best_ask).abs() < Decimal::from_str_exact("0.01").unwrap() {
            if tick.volume >= self.min_volume {
                return Some(TouchSide::Ask);
            }
        }
        
        None
    }
    
    /// Generate signal based on bounce pattern
    fn generate_signal(&mut self, touch: TouchSide, context: &StrategyContext) -> Option<Signal> {
        let mid_price = context.mid_price()?;
        
        // Track consecutive touches on same side
        if Some(touch) == self.last_touch_side {
            self.touch_count += 1;
        } else {
            self.touch_count = 1;
            self.last_touch_side = Some(touch);
        }
        
        // Need multiple touches to confirm
        if self.touch_count < self.required_touches {
            return None;
        }
        
        // Generate signals based on touch side
        match touch {
            TouchSide::Bid => {
                // Price at bid - expect bounce up
                info!("Bounce signal at bid: {} touches", self.touch_count);
                Some(Signal::long(
                    0.7,
                    mid_price,
                    format!("Bounce from bid after {} touches", self.touch_count),
                ))
            }
            TouchSide::Ask => {
                // Price at ask - expect bounce down
                info!("Bounce signal at ask: {} touches", self.touch_count);
                Some(Signal::short(
                    0.7,
                    mid_price,
                    format!("Bounce from ask after {} touches", self.touch_count),
                ))
            }
        }
    }
    
    /// Check exit conditions for bounce trade
    fn check_exit(&self, current_price: Decimal, book: &OrderBookState) -> Option<Signal> {
        if self.position.is_flat() {
            return None;
        }
        
        let entry = self.position.avg_entry_price;
        let pnl = if self.position.is_long() {
            current_price - entry
        } else {
            entry - current_price
        };
        
        // Exit if we've reached bounce target
        if pnl >= self.bounce_threshold {
            return Some(Signal::exit(
                current_price,
                format!("Bounce target reached: PnL={}", pnl),
            ));
        }
        
        // Stop loss
        if pnl < -self.config.parameters.stop_loss {
            return Some(Signal::exit(
                current_price,
                format!("Stop loss: PnL={}", pnl),
            ));
        }
        
        // Exit if spread widens too much
        if let Some(spread) = book.spread() {
            if spread > self.bounce_threshold * Decimal::from(3) {
                return Some(Signal::exit(
                    current_price,
                    "Spread too wide, exiting".to_string(),
                ));
            }
        }
        
        None
    }
}

impl Strategy for BidAskBounceStrategy {
    fn on_tick(&mut self, tick: &TickData, context: &StrategyContext) -> Option<Order> {
        // Update P&L
        if let Some(mid_price) = context.mid_price() {
            self.position.update_unrealized_pnl(mid_price);
        }
        
        // Check for exit first
        if let Some(signal) = self.check_exit(tick.price, &context.order_book) {
            if signal.signal_type == SignalType::Exit {
                let side = if self.position.is_long() {
                    OrderSide::Sell
                } else {
                    OrderSide::Buy
                };
                return Some(Order::market(side, self.position.size.abs()));
            }
        }
        
        // Only look for new entries if flat
        if !self.position.is_flat() {
            return None;
        }
        
        // Detect touches
        let touch = self.detect_touch(tick, &context.order_book)?;
        
        // Generate signal
        let signal = self.generate_signal(touch, context)?;
        
        // Convert to order
        match signal.signal_type {
            SignalType::Long => {
                // Enter with limit order slightly above bid
                let entry_price = context.order_book.best_bid? + self.entry_offset;
                Some(Order::limit(
                    OrderSide::Buy,
                    self.config.parameters.position_size,
                    entry_price,
                ))
            }
            SignalType::Short => {
                // Enter with limit order slightly below ask
                let entry_price = context.order_book.best_ask? - self.entry_offset;
                Some(Order::limit(
                    OrderSide::Sell,
                    self.config.parameters.position_size,
                    entry_price,
                ))
            }
            _ => None,
        }
    }
    
    fn on_order_fill(&mut self, fill: &OrderFill) {
        let was_flat = self.position.is_flat();
        self.position.apply_fill(fill);
        
        // Reset touch count on entry
        if was_flat && !self.position.is_flat() {
            self.touch_count = 0;
            self.last_touch_side = None;
        }
        
        // Update metrics on exit
        if !was_flat && self.position.is_flat() {
            let pnl = self.position.realized_pnl;
            let duration = fill.timestamp.signed_duration_since(
                self.position.open_time.unwrap_or(fill.timestamp)
            ).num_seconds() as f64;
            
            self.metrics.update_trade(pnl, duration);
        }
        
        info!("Fill: {:?} {} @ {}, Position: {}", 
            fill.side, fill.quantity, fill.price, self.position.size);
    }
    
    fn get_parameters(&self) -> &StrategyConfig {
        &self.config
    }
    
    fn reset(&mut self) {
        self.position.reset();
        self.metrics = StrategyMetrics::default();
        self.last_touch_side = None;
        self.touch_count = 0;
    }
    
    fn get_position(&self) -> &Position {
        &self.position
    }
    
    fn get_metrics(&self) -> StrategyMetrics {
        self.metrics.clone()
    }
}