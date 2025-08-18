//! High-performance order book implementation with validation

use crate::data::TickData;
use crate::market::{
    operations::{OrderBookProcessor, OrderBookStatistics},
    types::{BookSide, MarketDepth, OrderBookState, OrderBookStats},
};
use chrono::{DateTime, Utc};
use rust_decimal::Decimal;
use std::collections::HashMap;
use std::time::Instant;
use tracing::{debug, info, warn};

/// High-performance order book with validation and statistics
pub struct OrderBook {
    state: OrderBookState,
    processor: OrderBookProcessor,
    validation_enabled: bool,
    stats: OrderBookStats,
    start_time: Instant,
}

impl OrderBook {
    /// Create a new order book for a specific contract
    pub fn new(contract: String, validation_enabled: bool) -> Self {
        Self {
            state: OrderBookState::new(contract),
            processor: OrderBookProcessor::new(),
            validation_enabled,
            stats: OrderBookStats {
                total_updates: 0,
                add_operations: 0,
                update_operations: 0,
                remove_operations: 0,
                book_resets: 0,
                crossed_events: 0,
                max_spread: Decimal::ZERO,
                min_spread: Decimal::MAX,
                avg_spread: Decimal::ZERO,
                max_depth_bid: 0,
                max_depth_ask: 0,
                processing_time_us: 0,
            },
            start_time: Instant::now(),
        }
    }
    
    /// Process a single tick
    pub fn process_tick(&mut self, tick: &TickData) {
        let process_start = Instant::now();
        
        // Process the tick
        self.processor.process_tick(&mut self.state, tick);
        
        // Validate if enabled
        if self.validation_enabled {
            self.validate_state();
        }
        
        // Update statistics
        self.update_statistics();
        
        let process_time = process_start.elapsed().as_micros() as u64;
        self.stats.processing_time_us += process_time;
        self.stats.total_updates += 1;
    }
    
    /// Process a batch of ticks
    pub fn process_batch(&mut self, ticks: &[TickData]) -> ProcessingResult {
        let batch_start = Instant::now();
        let initial_sequence = self.state.sequence;
        
        for tick in ticks {
            self.process_tick(tick);
        }
        
        let elapsed = batch_start.elapsed();
        let ticks_per_second = ticks.len() as f64 / elapsed.as_secs_f64();
        
        ProcessingResult {
            ticks_processed: ticks.len(),
            duration_ms: elapsed.as_millis() as u64,
            ticks_per_second,
            sequence_range: (initial_sequence, self.state.sequence),
        }
    }
    
    /// Validate order book state
    fn validate_state(&mut self) {
        // Check for crossed book
        if self.state.is_crossed() {
            warn!(
                "Crossed book detected: bid {} >= ask {}",
                self.state.best_bid.unwrap_or(Decimal::ZERO),
                self.state.best_ask.unwrap_or(Decimal::ZERO)
            );
            self.stats.crossed_events += 1;
        }
        
        // Validate bid ordering (descending)
        let mut prev_bid = Decimal::MAX;
        for (&price, _) in self.state.bids.iter().rev() {
            if price >= prev_bid {
                warn!("Invalid bid ordering at price {}", price);
            }
            prev_bid = price;
        }
        
        // Validate ask ordering (ascending)
        let mut prev_ask = Decimal::MIN;
        for (&price, _) in &self.state.asks {
            if price <= prev_ask {
                warn!("Invalid ask ordering at price {}", price);
            }
            prev_ask = price;
        }
        
        // Validate volumes
        for (_, level) in &self.state.bids {
            if level.volume <= 0 {
                warn!("Invalid bid volume: {}", level.volume);
            }
        }
        
        for (_, level) in &self.state.asks {
            if level.volume <= 0 {
                warn!("Invalid ask volume: {}", level.volume);
            }
        }
    }
    
    /// Update order book statistics
    fn update_statistics(&mut self) {
        // Update spread statistics
        if let Some(spread) = self.state.spread() {
            if spread > self.stats.max_spread {
                self.stats.max_spread = spread;
            }
            if spread < self.stats.min_spread {
                self.stats.min_spread = spread;
            }
            
            // Update running average
            let n = self.stats.total_updates.max(1) as i32;
            self.stats.avg_spread = 
                (self.stats.avg_spread * Decimal::from(n - 1) + spread) / Decimal::from(n);
        }
        
        // Update depth statistics
        let bid_depth = self.state.bids.len();
        let ask_depth = self.state.asks.len();
        
        if bid_depth > self.stats.max_depth_bid {
            self.stats.max_depth_bid = bid_depth;
        }
        if ask_depth > self.stats.max_depth_ask {
            self.stats.max_depth_ask = ask_depth;
        }
        
        // Copy processor statistics
        let proc_stats = self.processor.get_stats();
        self.stats.add_operations = proc_stats.add_operations;
        self.stats.update_operations = proc_stats.update_operations;
        self.stats.remove_operations = proc_stats.remove_operations;
        self.stats.book_resets = proc_stats.book_resets;
    }
    
    /// Get current order book state
    pub fn get_state(&self) -> &OrderBookState {
        &self.state
    }
    
    /// Get market depth snapshot
    pub fn get_market_depth(&self, max_levels: usize) -> MarketDepth {
        MarketDepth::from_order_book(&self.state, max_levels)
    }
    
    /// Get order book statistics
    pub fn get_stats(&self) -> &OrderBookStats {
        &self.stats
    }
    
    /// Get processing rate (operations per second)
    pub fn get_processing_rate(&self) -> f64 {
        let elapsed = self.start_time.elapsed().as_secs_f64();
        if elapsed > 0.0 {
            self.stats.total_updates as f64 / elapsed
        } else {
            0.0
        }
    }
    
    /// Generate performance report
    pub fn generate_report(&self) -> String {
        let elapsed = self.start_time.elapsed().as_secs_f64();
        let rate = self.get_processing_rate();
        let avg_latency = if self.stats.total_updates > 0 {
            self.stats.processing_time_us as f64 / self.stats.total_updates as f64
        } else {
            0.0
        };
        
        format!(
            r#"
Order Book Performance Report
==============================
Contract: {}
Processing Time: {:.2}s
Total Updates: {}
Processing Rate: {:.0} ops/sec

Operations Breakdown:
- Add Operations: {}
- Update Operations: {}
- Remove Operations: {}
- Book Resets: {}

Market Quality:
- Crossed Events: {}
- Max Spread: {}
- Min Spread: {}
- Avg Spread: {}

Order Book Depth:
- Max Bid Levels: {}
- Max Ask Levels: {}
- Current Bid Levels: {}
- Current Ask Levels: {}

Performance Metrics:
- Average Latency: {:.2} μs
- Total Processing Time: {} μs
- Current Best Bid: {:?}
- Current Best Ask: {:?}
- Current Spread: {:?}
"#,
            self.state.contract,
            elapsed,
            self.stats.total_updates,
            rate,
            self.stats.add_operations,
            self.stats.update_operations,
            self.stats.remove_operations,
            self.stats.book_resets,
            self.stats.crossed_events,
            self.stats.max_spread,
            self.stats.min_spread,
            self.stats.avg_spread,
            self.stats.max_depth_bid,
            self.stats.max_depth_ask,
            self.state.bids.len(),
            self.state.asks.len(),
            avg_latency,
            self.stats.processing_time_us,
            self.state.best_bid,
            self.state.best_ask,
            self.state.spread()
        )
    }
}

/// Result of batch processing
#[derive(Debug)]
pub struct ProcessingResult {
    pub ticks_processed: usize,
    pub duration_ms: u64,
    pub ticks_per_second: f64,
    pub sequence_range: (u64, u64),
}

/// Builder for creating order books with specific configurations
pub struct OrderBookBuilder {
    contract: String,
    validation_enabled: bool,
    max_depth: Option<usize>,
}

impl OrderBookBuilder {
    pub fn new(contract: String) -> Self {
        Self {
            contract,
            validation_enabled: true,
            max_depth: None,
        }
    }
    
    pub fn with_validation(mut self, enabled: bool) -> Self {
        self.validation_enabled = enabled;
        self
    }
    
    pub fn with_max_depth(mut self, depth: usize) -> Self {
        self.max_depth = Some(depth);
        self
    }
    
    pub fn build(self) -> OrderBook {
        OrderBook::new(self.contract, self.validation_enabled)
    }
}

/// Multi-contract order book manager
pub struct OrderBookManager {
    books: HashMap<String, OrderBook>,
    validation_enabled: bool,
}

impl OrderBookManager {
    pub fn new(validation_enabled: bool) -> Self {
        Self {
            books: HashMap::new(),
            validation_enabled,
        }
    }
    
    /// Get or create order book for a contract
    pub fn get_or_create(&mut self, contract: &str) -> &mut OrderBook {
        self.books
            .entry(contract.to_string())
            .or_insert_with(|| OrderBook::new(contract.to_string(), self.validation_enabled))
    }
    
    /// Process tick, routing to appropriate order book
    pub fn process_tick(&mut self, tick: &TickData) {
        let book = self.get_or_create(&tick.contract_month);
        book.process_tick(tick);
    }
    
    /// Get all active contracts
    pub fn active_contracts(&self) -> Vec<String> {
        self.books.keys().cloned().collect()
    }
    
    /// Generate consolidated report
    pub fn generate_report(&self) -> String {
        let mut report = String::from("Multi-Contract Order Book Report\n");
        report.push_str("=================================\n\n");
        
        for (contract, book) in &self.books {
            report.push_str(&format!("Contract: {}\n", contract));
            report.push_str(&format!("  Updates: {}\n", book.get_stats().total_updates));
            report.push_str(&format!("  Rate: {:.0} ops/sec\n", book.get_processing_rate()));
            report.push_str(&format!("  Spread: {:?}\n", book.get_state().spread()));
            report.push_str("\n");
        }
        
        report
    }
}