//! Example strategy implementations demonstrating the template system
//! 
//! These strategies show how to implement scalping strategies using
//! the Strategy trait. Each example includes comprehensive comments
//! to help Rust beginners understand the implementation.

pub mod order_book_imbalance;
pub mod bid_ask_bounce;

pub use order_book_imbalance::OrderBookImbalanceStrategy;
pub use bid_ask_bounce::BidAskBounceStrategy;