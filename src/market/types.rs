//! Core types for order book representation

use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use chrono::{DateTime, Utc};

/// Represents a single price level in the order book
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PriceLevel {
    pub price: Decimal,
    pub volume: i32,
    pub order_count: u32,
    pub market_makers: Vec<String>,
    pub last_update: DateTime<Utc>,
}

impl PriceLevel {
    pub fn new(price: Decimal, volume: i32, timestamp: DateTime<Utc>) -> Self {
        Self {
            price,
            volume,
            order_count: 1,
            market_makers: Vec::new(),
            last_update: timestamp,
        }
    }
    
    pub fn add_volume(&mut self, volume: i32, timestamp: DateTime<Utc>) {
        self.volume += volume;
        self.order_count += 1;
        self.last_update = timestamp;
    }
    
    pub fn update_volume(&mut self, new_volume: i32, timestamp: DateTime<Utc>) {
        self.volume = new_volume;
        self.last_update = timestamp;
    }
    
    pub fn remove_volume(&mut self, volume: i32, timestamp: DateTime<Utc>) {
        self.volume = self.volume.saturating_sub(volume);
        if self.order_count > 0 {
            self.order_count -= 1;
        }
        self.last_update = timestamp;
    }
}

/// Side of the order book (bid or ask)
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum BookSide {
    Bid,
    Ask,
}

/// Complete order book state at a point in time
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrderBookState {
    /// Bid levels sorted by price (descending)
    pub bids: BTreeMap<Decimal, PriceLevel>,
    
    /// Ask levels sorted by price (ascending)
    pub asks: BTreeMap<Decimal, PriceLevel>,
    
    /// Best bid price
    pub best_bid: Option<Decimal>,
    
    /// Best ask price
    pub best_ask: Option<Decimal>,
    
    /// Total bid volume
    pub total_bid_volume: i64,
    
    /// Total ask volume
    pub total_ask_volume: i64,
    
    /// Timestamp of last update
    pub last_update: DateTime<Utc>,
    
    /// Contract identifier
    pub contract: String,
    
    /// Sequence number for order tracking
    pub sequence: u64,
}

impl OrderBookState {
    pub fn new(contract: String) -> Self {
        Self {
            bids: BTreeMap::new(),
            asks: BTreeMap::new(),
            best_bid: None,
            best_ask: None,
            total_bid_volume: 0,
            total_ask_volume: 0,
            last_update: Utc::now(),
            contract,
            sequence: 0,
        }
    }
    
    /// Get the spread between best bid and ask
    pub fn spread(&self) -> Option<Decimal> {
        match (self.best_bid, self.best_ask) {
            (Some(bid), Some(ask)) => Some(ask - bid),
            _ => None,
        }
    }
    
    /// Get mid price
    pub fn mid_price(&self) -> Option<Decimal> {
        match (self.best_bid, self.best_ask) {
            (Some(bid), Some(ask)) => Some((bid + ask) / Decimal::from(2)),
            _ => None,
        }
    }
    
    /// Get order book imbalance
    pub fn imbalance(&self) -> f64 {
        let total = self.total_bid_volume + self.total_ask_volume;
        if total == 0 {
            return 0.0;
        }
        
        (self.total_bid_volume - self.total_ask_volume) as f64 / total as f64
    }
    
    /// Get depth at a specific level
    pub fn depth_at_level(&self, level: usize, side: BookSide) -> Option<&PriceLevel> {
        let levels: Vec<_> = match side {
            BookSide::Bid => self.bids.values().collect(),
            BookSide::Ask => self.asks.values().collect(),
        };
        
        levels.get(level).copied()
    }
    
    /// Check if bid/ask are crossed (invalid state)
    pub fn is_crossed(&self) -> bool {
        match (self.best_bid, self.best_ask) {
            (Some(bid), Some(ask)) => bid >= ask,
            _ => false,
        }
    }
    
    /// Update best bid/ask prices
    pub fn update_best_prices(&mut self) {
        self.best_bid = self.bids.keys().next_back().copied();
        self.best_ask = self.asks.keys().next().copied();
    }
    
    /// Clear the entire book (book reset)
    pub fn clear(&mut self, timestamp: DateTime<Utc>) {
        self.bids.clear();
        self.asks.clear();
        self.best_bid = None;
        self.best_ask = None;
        self.total_bid_volume = 0;
        self.total_ask_volume = 0;
        self.last_update = timestamp;
        self.sequence += 1;
    }
}

/// Market depth information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketDepth {
    pub timestamp: DateTime<Utc>,
    pub bids: Vec<(Decimal, i32)>,  // (price, volume) pairs
    pub asks: Vec<(Decimal, i32)>,  // (price, volume) pairs
    pub depth_levels: usize,
}

impl MarketDepth {
    pub fn from_order_book(book: &OrderBookState, max_levels: usize) -> Self {
        let bids: Vec<_> = book.bids
            .iter()
            .rev()
            .take(max_levels)
            .map(|(price, level)| (*price, level.volume))
            .collect();
        
        let asks: Vec<_> = book.asks
            .iter()
            .take(max_levels)
            .map(|(price, level)| (*price, level.volume))
            .collect();
        
        Self {
            timestamp: book.last_update,
            bids,
            asks,
            depth_levels: max_levels,
        }
    }
    
    /// Calculate weighted average price for a given volume
    pub fn weighted_average_price(&self, volume: i32, side: BookSide) -> Option<Decimal> {
        let levels = match side {
            BookSide::Bid => &self.bids,
            BookSide::Ask => &self.asks,
        };
        
        let mut remaining_volume = volume;
        let mut total_value = Decimal::ZERO;
        let mut total_volume = 0;
        
        for (price, level_volume) in levels {
            let fill_volume = remaining_volume.min(*level_volume);
            total_value += *price * Decimal::from(fill_volume);
            total_volume += fill_volume;
            remaining_volume -= fill_volume;
            
            if remaining_volume <= 0 {
                break;
            }
        }
        
        if total_volume > 0 {
            Some(total_value / Decimal::from(total_volume))
        } else {
            None
        }
    }
    
    /// Calculate market impact for a given volume
    pub fn market_impact(&self, volume: i32, side: BookSide) -> Option<Decimal> {
        let best_price = match side {
            BookSide::Bid => self.bids.first().map(|(p, _)| *p),
            BookSide::Ask => self.asks.first().map(|(p, _)| *p),
        }?;
        
        let avg_price = self.weighted_average_price(volume, side)?;
        
        Some((avg_price - best_price).abs())
    }
}

/// Statistics for order book analysis
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrderBookStats {
    pub total_updates: u64,
    pub add_operations: u64,
    pub update_operations: u64,
    pub remove_operations: u64,
    pub book_resets: u64,
    pub crossed_events: u64,
    pub max_spread: Decimal,
    pub min_spread: Decimal,
    pub avg_spread: Decimal,
    pub max_depth_bid: usize,
    pub max_depth_ask: usize,
    pub processing_time_us: u64,
}