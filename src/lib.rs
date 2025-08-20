//! Strategy Lab - High-performance backtesting system for MNQ futures scalping strategies
//! 
//! This library provides:
//! - High-performance tick data processing (100K-500K ticks/second)
//! - Order book reconstruction from Level 1 and Level 2 data
//! - Strategy template system for rapid development
//! - Multi-algorithm parameter optimization
//! - Real-time performance monitoring

pub mod data;
pub mod market;
pub mod strategy;
pub mod backtesting;
pub mod optimization;
pub mod monitoring;
pub mod api;
pub mod reporting;
pub mod analysis;
pub mod workflow;
pub mod database;
pub mod jobs;
pub mod statistics;
pub mod performance;
pub mod fault_tolerance;

// Re-export commonly used types
pub use data::{TickData, DataLevel, MarketDataType, IngestionConfig};
pub use market::{OrderBook, OrderBookState};
pub use strategy::{Strategy, StrategyConfig};

/// Library version
pub const VERSION: &str = env!("CARGO_PKG_VERSION");