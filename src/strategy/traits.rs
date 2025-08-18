//! Core strategy trait interface defining required methods

use crate::data::TickData;
use crate::market::OrderBookState;
use crate::strategy::{Order, Position, Signal, StrategyConfig};
use chrono::{DateTime, Utc};
use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};

/// Main strategy trait that all trading strategies must implement
/// 
/// # Example
/// ```rust
/// use strategy_lab::strategy::{Strategy, StrategyContext};
/// 
/// struct MyStrategy {
///     config: StrategyConfig,
///     position: Position,
/// }
/// 
/// impl Strategy for MyStrategy {
///     fn on_tick(&mut self, tick: &TickData, context: &StrategyContext) -> Option<Order> {
///         // Your strategy logic here
///         None
///     }
///     
///     // Implement other required methods...
/// }
/// ```
pub trait Strategy: Send + Sync {
    /// Called for each tick of market data
    /// 
    /// This is where your main strategy logic goes. Analyze the tick,
    /// check the order book state, and decide whether to place an order.
    fn on_tick(&mut self, tick: &TickData, context: &StrategyContext) -> Option<Order>;
    
    /// Called when an order is filled
    /// 
    /// Update your position tracking and any internal state when
    /// your order gets executed in the market.
    fn on_order_fill(&mut self, fill: &OrderFill);
    
    /// Get current strategy parameters
    fn get_parameters(&self) -> &StrategyConfig;
    
    /// Reset strategy state
    /// 
    /// Called at the start of each backtest run or when you need
    /// to clear all internal state and start fresh.
    fn reset(&mut self);
    
    /// Get current position
    fn get_position(&self) -> &Position;
    
    /// Get strategy metrics for performance analysis
    fn get_metrics(&self) -> StrategyMetrics;
    
    /// Optional: Called when order book state changes
    /// 
    /// Override this if your strategy needs to react to order book updates
    /// beyond just the tick data.
    fn on_order_book_update(&mut self, _book: &OrderBookState) -> Option<Signal> {
        None
    }
    
    /// Optional: Called at the end of each trading session
    /// 
    /// Use this to close positions, calculate daily metrics, etc.
    fn on_session_end(&mut self) {
        // Default: do nothing
    }
}

/// Context provided to strategies containing market state and utilities
#[derive(Debug, Clone)]
pub struct StrategyContext {
    /// Current order book state
    pub order_book: OrderBookState,
    
    /// Current timestamp
    pub timestamp: DateTime<Utc>,
    
    /// Session high price
    pub session_high: Option<Decimal>,
    
    /// Session low price
    pub session_low: Option<Decimal>,
    
    /// Session volume
    pub session_volume: i64,
    
    /// Current contract month
    pub contract: String,
    
    /// Is market open for trading
    pub market_open: bool,
}

impl StrategyContext {
    /// Get current spread
    pub fn spread(&self) -> Option<Decimal> {
        self.order_book.spread()
    }
    
    /// Get mid price
    pub fn mid_price(&self) -> Option<Decimal> {
        self.order_book.mid_price()
    }
    
    /// Get order book imbalance
    pub fn imbalance(&self) -> f64 {
        self.order_book.imbalance()
    }
    
    /// Check if we're near session high
    pub fn near_session_high(&self, threshold: Decimal) -> bool {
        if let (Some(high), Some(mid)) = (self.session_high, self.mid_price()) {
            (high - mid) <= threshold
        } else {
            false
        }
    }
    
    /// Check if we're near session low
    pub fn near_session_low(&self, threshold: Decimal) -> bool {
        if let (Some(low), Some(mid)) = (self.session_low, self.mid_price()) {
            (mid - low) <= threshold
        } else {
            false
        }
    }
}

/// Information about an order fill
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrderFill {
    /// Unique order ID
    pub order_id: String,
    
    /// Fill timestamp
    pub timestamp: DateTime<Utc>,
    
    /// Fill price
    pub price: Decimal,
    
    /// Fill quantity
    pub quantity: i32,
    
    /// Buy or sell
    pub side: crate::strategy::OrderSide,
    
    /// Commission paid
    pub commission: Decimal,
    
    /// Slippage from intended price
    pub slippage: Decimal,
}

/// Strategy performance metrics
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct StrategyMetrics {
    /// Total profit/loss
    pub total_pnl: Decimal,
    
    /// Number of trades
    pub total_trades: u32,
    
    /// Winning trades
    pub winning_trades: u32,
    
    /// Losing trades
    pub losing_trades: u32,
    
    /// Maximum drawdown
    pub max_drawdown: Decimal,
    
    /// Current drawdown
    pub current_drawdown: Decimal,
    
    /// Sharpe ratio
    pub sharpe_ratio: f64,
    
    /// Win rate percentage
    pub win_rate: f64,
    
    /// Average win amount
    pub avg_win: Decimal,
    
    /// Average loss amount
    pub avg_loss: Decimal,
    
    /// Profit factor (gross profit / gross loss)
    pub profit_factor: f64,
    
    /// Maximum consecutive wins
    pub max_consecutive_wins: u32,
    
    /// Maximum consecutive losses
    pub max_consecutive_losses: u32,
    
    /// Average trade duration in seconds
    pub avg_trade_duration: f64,
}

impl StrategyMetrics {
    /// Calculate win rate
    pub fn calculate_win_rate(&mut self) {
        if self.total_trades > 0 {
            self.win_rate = (self.winning_trades as f64 / self.total_trades as f64) * 100.0;
        }
    }
    
    /// Update metrics with a new trade
    pub fn update_trade(&mut self, pnl: Decimal, duration_secs: f64) {
        self.total_trades += 1;
        self.total_pnl += pnl;
        
        if pnl > Decimal::ZERO {
            self.winning_trades += 1;
            self.avg_win = (self.avg_win * Decimal::from(self.winning_trades - 1) + pnl) 
                / Decimal::from(self.winning_trades);
        } else {
            self.losing_trades += 1;
            self.avg_loss = (self.avg_loss * Decimal::from(self.losing_trades - 1) + pnl.abs()) 
                / Decimal::from(self.losing_trades);
        }
        
        // Update average duration
        self.avg_trade_duration = (self.avg_trade_duration * (self.total_trades - 1) as f64 
            + duration_secs) / self.total_trades as f64;
        
        // Update drawdown
        if self.total_pnl < self.current_drawdown {
            self.current_drawdown = self.total_pnl;
            if self.current_drawdown < self.max_drawdown {
                self.max_drawdown = self.current_drawdown;
            }
        }
        
        self.calculate_win_rate();
        self.calculate_profit_factor();
    }
    
    /// Calculate profit factor
    fn calculate_profit_factor(&mut self) {
        let gross_profit = self.avg_win * Decimal::from(self.winning_trades);
        let gross_loss = self.avg_loss * Decimal::from(self.losing_trades);
        
        if gross_loss > Decimal::ZERO {
            self.profit_factor = (gross_profit / gross_loss).to_string().parse().unwrap_or(0.0);
        }
    }
}