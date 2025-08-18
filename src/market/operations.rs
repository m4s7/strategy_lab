//! Order book operations and updates

use crate::data::{OrderBookOperation as DataOperation, TickData};
use crate::market::types::{BookSide, OrderBookState, PriceLevel};
use chrono::{DateTime, Utc};
use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};

/// Order book update event
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrderBookUpdate {
    pub timestamp: DateTime<Utc>,
    pub operation: OrderBookOperation,
    pub side: BookSide,
    pub price: Decimal,
    pub volume: i32,
    pub depth: u8,
    pub market_maker: Option<String>,
    pub sequence: u64,
}

/// Extended order book operation with side information
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum OrderBookOperation {
    Add,
    Update,
    Remove,
    Reset,
}

impl From<DataOperation> for OrderBookOperation {
    fn from(op: DataOperation) -> Self {
        match op {
            DataOperation::Add => OrderBookOperation::Add,
            DataOperation::Update => OrderBookOperation::Update,
            DataOperation::Remove => OrderBookOperation::Remove,
        }
    }
}

/// Processes order book operations
pub struct OrderBookProcessor {
    stats: OrderBookStatistics,
}

impl OrderBookProcessor {
    pub fn new() -> Self {
        Self {
            stats: OrderBookStatistics::default(),
        }
    }
    
    /// Process a tick and update the order book
    pub fn process_tick(&mut self, book: &mut OrderBookState, tick: &TickData) {
        use crate::data::MarketDataType;
        
        // Only process L2 data and relevant L1 quotes
        match tick.level {
            crate::data::DataLevel::L2 => {
                if let Some(operation) = tick.operation {
                    self.process_l2_operation(book, tick, operation.into());
                }
            }
            crate::data::DataLevel::L1 => {
                match tick.mdt {
                    MarketDataType::BidQuote => {
                        self.process_l1_quote(book, tick, BookSide::Bid);
                    }
                    MarketDataType::AskQuote => {
                        self.process_l1_quote(book, tick, BookSide::Ask);
                    }
                    MarketDataType::BookReset => {
                        book.clear(tick.timestamp);
                        self.stats.book_resets += 1;
                    }
                    _ => {}
                }
            }
        }
        
        // Update statistics
        self.stats.total_updates += 1;
        book.sequence += 1;
        book.last_update = tick.timestamp;
        
        // Check for crossed book
        if book.is_crossed() {
            self.stats.crossed_events += 1;
        }
    }
    
    /// Process L2 order book operation
    fn process_l2_operation(
        &mut self,
        book: &mut OrderBookState,
        tick: &TickData,
        operation: OrderBookOperation,
    ) {
        let side = self.determine_side(tick);
        let depth = tick.depth.unwrap_or(0);
        
        match operation {
            OrderBookOperation::Add => {
                self.add_level(book, side, tick.price, tick.volume, tick.timestamp, depth);
                self.stats.add_operations += 1;
            }
            OrderBookOperation::Update => {
                self.update_level(book, side, tick.price, tick.volume, tick.timestamp, depth);
                self.stats.update_operations += 1;
            }
            OrderBookOperation::Remove => {
                self.remove_level(book, side, tick.price, depth);
                self.stats.remove_operations += 1;
            }
            OrderBookOperation::Reset => {
                book.clear(tick.timestamp);
                self.stats.book_resets += 1;
            }
        }
        
        // Update best prices after modification
        book.update_best_prices();
    }
    
    /// Process L1 quote update
    fn process_l1_quote(&mut self, book: &mut OrderBookState, tick: &TickData, side: BookSide) {
        // L1 quotes update the best bid/ask directly
        match side {
            BookSide::Bid => {
                // Clear old best bid if different
                if let Some(old_best) = book.best_bid {
                    if old_best != tick.price {
                        book.bids.remove(&old_best);
                    }
                }
                
                // Insert new best bid
                let level = PriceLevel::new(tick.price, tick.volume, tick.timestamp);
                book.bids.insert(tick.price, level);
                book.best_bid = Some(tick.price);
            }
            BookSide::Ask => {
                // Clear old best ask if different
                if let Some(old_best) = book.best_ask {
                    if old_best != tick.price {
                        book.asks.remove(&old_best);
                    }
                }
                
                // Insert new best ask
                let level = PriceLevel::new(tick.price, tick.volume, tick.timestamp);
                book.asks.insert(tick.price, level);
                book.best_ask = Some(tick.price);
            }
        }
    }
    
    /// Add a new price level
    fn add_level(
        &mut self,
        book: &mut OrderBookState,
        side: BookSide,
        price: Decimal,
        volume: i32,
        timestamp: DateTime<Utc>,
        _depth: u8,
    ) {
        let level = PriceLevel::new(price, volume, timestamp);
        
        match side {
            BookSide::Bid => {
                book.bids.insert(price, level);
                book.total_bid_volume += volume as i64;
            }
            BookSide::Ask => {
                book.asks.insert(price, level);
                book.total_ask_volume += volume as i64;
            }
        }
    }
    
    /// Update an existing price level
    fn update_level(
        &mut self,
        book: &mut OrderBookState,
        side: BookSide,
        price: Decimal,
        new_volume: i32,
        timestamp: DateTime<Utc>,
        _depth: u8,
    ) {
        match side {
            BookSide::Bid => {
                if let Some(level) = book.bids.get_mut(&price) {
                    let old_volume = level.volume;
                    level.update_volume(new_volume, timestamp);
                    book.total_bid_volume += (new_volume - old_volume) as i64;
                } else {
                    // If level doesn't exist, add it
                    self.add_level(book, side, price, new_volume, timestamp, _depth);
                }
            }
            BookSide::Ask => {
                if let Some(level) = book.asks.get_mut(&price) {
                    let old_volume = level.volume;
                    level.update_volume(new_volume, timestamp);
                    book.total_ask_volume += (new_volume - old_volume) as i64;
                } else {
                    // If level doesn't exist, add it
                    self.add_level(book, side, price, new_volume, timestamp, _depth);
                }
            }
        }
    }
    
    /// Remove a price level
    fn remove_level(
        &mut self,
        book: &mut OrderBookState,
        side: BookSide,
        price: Decimal,
        _depth: u8,
    ) {
        match side {
            BookSide::Bid => {
                if let Some(level) = book.bids.remove(&price) {
                    book.total_bid_volume -= level.volume as i64;
                }
            }
            BookSide::Ask => {
                if let Some(level) = book.asks.remove(&price) {
                    book.total_ask_volume -= level.volume as i64;
                }
            }
        }
    }
    
    /// Determine the side of the book from tick data
    fn determine_side(&self, tick: &TickData) -> BookSide {
        // Use MDT to determine side if available
        use crate::data::MarketDataType;
        
        match tick.mdt {
            MarketDataType::BidQuote | MarketDataType::ImpliedBid => BookSide::Bid,
            MarketDataType::AskQuote | MarketDataType::ImpliedAsk => BookSide::Ask,
            _ => {
                // Default heuristic: compare with mid price if available
                // This is a simplified approach - in production, use more sophisticated logic
                BookSide::Bid
            }
        }
    }
    
    pub fn get_stats(&self) -> &OrderBookStatistics {
        &self.stats
    }
}

/// Statistics for order book processing
#[derive(Debug, Default, Clone, Serialize, Deserialize)]
pub struct OrderBookStatistics {
    pub total_updates: u64,
    pub add_operations: u64,
    pub update_operations: u64,
    pub remove_operations: u64,
    pub book_resets: u64,
    pub crossed_events: u64,
}

impl OrderBookStatistics {
    pub fn processing_rate(&self, duration_secs: f64) -> f64 {
        if duration_secs > 0.0 {
            self.total_updates as f64 / duration_secs
        } else {
            0.0
        }
    }
}