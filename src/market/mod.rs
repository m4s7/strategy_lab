//! Market microstructure and order book reconstruction module
//! 
//! This module implements Story 1.2: Order Book Reconstruction
//! Handles Level 2 order book reconstruction from tick operations
//! Processes 100K+ operations per second with integrity validation

pub mod order_book;
pub mod types;
pub mod operations;
pub mod validation;

pub use order_book::{OrderBook, OrderBookBuilder};
pub use types::{OrderBookState, PriceLevel, BookSide, MarketDepth};
pub use operations::{OrderBookOperation, OrderBookUpdate};
pub use validation::OrderBookValidator;