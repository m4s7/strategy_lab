//! Order book validation module

use crate::market::types::{OrderBookState, BookSide};
use rust_decimal::Decimal;
use std::collections::HashSet;

/// Validator for order book integrity
pub struct OrderBookValidator {
    strict_mode: bool,
    max_spread_threshold: Option<Decimal>,
    min_volume_threshold: i32,
}

impl OrderBookValidator {
    pub fn new(strict_mode: bool) -> Self {
        Self {
            strict_mode,
            max_spread_threshold: None,
            min_volume_threshold: 0,
        }
    }
    
    pub fn with_spread_threshold(mut self, threshold: Decimal) -> Self {
        self.max_spread_threshold = Some(threshold);
        self
    }
    
    pub fn with_volume_threshold(mut self, threshold: i32) -> Self {
        self.min_volume_threshold = threshold;
        self
    }
    
    /// Validate order book state
    pub fn validate(&self, book: &OrderBookState) -> ValidationResult {
        let mut errors = Vec::new();
        
        // Check for crossed book
        if book.is_crossed() {
            errors.push(ValidationError::CrossedBook {
                bid: book.best_bid.unwrap_or(Decimal::ZERO),
                ask: book.best_ask.unwrap_or(Decimal::ZERO),
            });
        }
        
        // Validate bid price ordering
        let mut prev_bid = None;
        for (price, level) in book.bids.iter().rev() {
            if let Some(prev) = prev_bid {
                if price >= prev {
                    errors.push(ValidationError::InvalidBidOrdering {
                        current: *price,
                        previous: prev,
                    });
                }
            }
            prev_bid = Some(*price);
            
            // Validate volume
            if level.volume < self.min_volume_threshold {
                errors.push(ValidationError::InvalidVolume {
                    price: *price,
                    volume: level.volume,
                    side: BookSide::Bid,
                });
            }
        }
        
        // Validate ask price ordering
        let mut prev_ask = None;
        for (price, level) in &book.asks {
            if let Some(prev) = prev_ask {
                if price <= prev {
                    errors.push(ValidationError::InvalidAskOrdering {
                        current: *price,
                        previous: prev,
                    });
                }
            }
            prev_ask = Some(*price);
            
            // Validate volume
            if level.volume < self.min_volume_threshold {
                errors.push(ValidationError::InvalidVolume {
                    price: *price,
                    volume: level.volume,
                    side: BookSide::Ask,
                });
            }
        }
        
        // Check spread threshold
        if let Some(threshold) = self.max_spread_threshold {
            if let Some(spread) = book.spread() {
                if spread > threshold {
                    errors.push(ValidationError::ExcessiveSpread {
                        spread,
                        threshold,
                    });
                }
            }
        }
        
        // Strict mode checks
        if self.strict_mode {
            // Check for duplicate market makers at same price level
            let mut seen_makers = HashSet::new();
            for (_, level) in &book.bids {
                for maker in &level.market_makers {
                    if !seen_makers.insert(maker.clone()) {
                        errors.push(ValidationError::DuplicateMarketMaker {
                            maker: maker.clone(),
                        });
                    }
                }
            }
            
            // Check total volume consistency
            let calculated_bid_volume: i64 = book.bids.values()
                .map(|l| l.volume as i64)
                .sum();
            
            if calculated_bid_volume != book.total_bid_volume {
                errors.push(ValidationError::VolumeInconsistency {
                    calculated: calculated_bid_volume,
                    stored: book.total_bid_volume,
                    side: BookSide::Bid,
                });
            }
            
            let calculated_ask_volume: i64 = book.asks.values()
                .map(|l| l.volume as i64)
                .sum();
            
            if calculated_ask_volume != book.total_ask_volume {
                errors.push(ValidationError::VolumeInconsistency {
                    calculated: calculated_ask_volume,
                    stored: book.total_ask_volume,
                    side: BookSide::Ask,
                });
            }
        }
        
        ValidationResult {
            is_valid: errors.is_empty(),
            errors,
            warnings: Vec::new(),
        }
    }
}

#[derive(Debug)]
pub struct ValidationResult {
    pub is_valid: bool,
    pub errors: Vec<ValidationError>,
    pub warnings: Vec<ValidationWarning>,
}

#[derive(Debug, Clone)]
pub enum ValidationError {
    CrossedBook {
        bid: Decimal,
        ask: Decimal,
    },
    InvalidBidOrdering {
        current: Decimal,
        previous: Decimal,
    },
    InvalidAskOrdering {
        current: Decimal,
        previous: Decimal,
    },
    InvalidVolume {
        price: Decimal,
        volume: i32,
        side: BookSide,
    },
    ExcessiveSpread {
        spread: Decimal,
        threshold: Decimal,
    },
    DuplicateMarketMaker {
        maker: String,
    },
    VolumeInconsistency {
        calculated: i64,
        stored: i64,
        side: BookSide,
    },
}

#[derive(Debug, Clone)]
pub enum ValidationWarning {
    LowLiquidity {
        total_volume: i64,
    },
    WideSpread {
        spread: Decimal,
    },
    StaleData {
        seconds_old: u64,
    },
}