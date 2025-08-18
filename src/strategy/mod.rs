//! Strategy development framework
//! 
//! This module implements Story 2.1: Strategy Template System
//! Provides clear templates for Rust beginners with trading experience
//! Enables new strategy implementation in under 30 minutes

pub mod traits;
pub mod templates;
pub mod config;
pub mod signals;
pub mod orders;
pub mod position;
pub mod examples;

pub use traits::{Strategy, StrategyContext, StrategyMetrics};
pub use config::{StrategyConfig, StrategyParameters};
pub use orders::{Order, OrderType, OrderSide};
pub use position::{Position, PositionManager};
pub use signals::{Signal, SignalType};

// Re-export example strategies
pub use examples::{OrderBookImbalanceStrategy, BidAskBounceStrategy};