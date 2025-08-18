//! Position tracking and management

use crate::strategy::{OrderSide, OrderFill};
use chrono::{DateTime, Utc};
use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};

/// Current position state
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct Position {
    /// Current position size (positive for long, negative for short)
    pub size: i32,
    
    /// Average entry price
    pub avg_entry_price: Decimal,
    
    /// Realized P&L
    pub realized_pnl: Decimal,
    
    /// Unrealized P&L
    pub unrealized_pnl: Decimal,
    
    /// Total commission paid
    pub total_commission: Decimal,
    
    /// Position open time
    pub open_time: Option<DateTime<Utc>>,
    
    /// Number of fills
    pub num_fills: u32,
    
    /// Maximum position size reached
    pub max_size: i32,
    
    /// Current value of position
    pub market_value: Decimal,
}

impl Position {
    /// Create a new empty position
    pub fn new() -> Self {
        Self::default()
    }
    
    /// Check if position is flat (no position)
    pub fn is_flat(&self) -> bool {
        self.size == 0
    }
    
    /// Check if position is long
    pub fn is_long(&self) -> bool {
        self.size > 0
    }
    
    /// Check if position is short
    pub fn is_short(&self) -> bool {
        self.size < 0
    }
    
    /// Get position side
    pub fn side(&self) -> Option<OrderSide> {
        if self.is_long() {
            Some(OrderSide::Buy)
        } else if self.is_short() {
            Some(OrderSide::Sell)
        } else {
            None
        }
    }
    
    /// Update position with a fill
    pub fn apply_fill(&mut self, fill: &OrderFill) {
        let signed_quantity = match fill.side {
            OrderSide::Buy => fill.quantity,
            OrderSide::Sell => -fill.quantity,
        };
        
        let old_size = self.size;
        let new_size = old_size + signed_quantity;
        
        // Handle position changes
        if old_size == 0 {
            // Opening new position
            self.avg_entry_price = fill.price;
            self.open_time = Some(fill.timestamp);
        } else if (old_size > 0 && new_size < 0) || (old_size < 0 && new_size > 0) {
            // Position flip - realize P&L on old position
            let close_quantity = old_size.abs();
            let pnl = self.calculate_pnl(fill.price, close_quantity);
            self.realized_pnl += pnl;
            
            // New position with remaining quantity
            if new_size != 0 {
                self.avg_entry_price = fill.price;
                self.open_time = Some(fill.timestamp);
            }
        } else if new_size.abs() < old_size.abs() {
            // Reducing position - realize partial P&L
            let close_quantity = (old_size.abs() - new_size.abs()).min(fill.quantity);
            let pnl = self.calculate_pnl(fill.price, close_quantity);
            self.realized_pnl += pnl;
        } else {
            // Adding to position - update average entry
            let total_value = self.avg_entry_price * Decimal::from(old_size.abs())
                + fill.price * Decimal::from(fill.quantity);
            self.avg_entry_price = total_value / Decimal::from(new_size.abs());
        }
        
        self.size = new_size;
        self.total_commission += fill.commission;
        self.num_fills += 1;
        
        if self.size.abs() > self.max_size {
            self.max_size = self.size.abs();
        }
        
        if self.is_flat() {
            self.open_time = None;
            self.avg_entry_price = Decimal::ZERO;
        }
    }
    
    /// Calculate P&L for a position
    fn calculate_pnl(&self, exit_price: Decimal, quantity: i32) -> Decimal {
        let price_diff = if self.is_long() {
            exit_price - self.avg_entry_price
        } else {
            self.avg_entry_price - exit_price
        };
        
        price_diff * Decimal::from(quantity)
    }
    
    /// Update unrealized P&L with current market price
    pub fn update_unrealized_pnl(&mut self, current_price: Decimal) {
        if !self.is_flat() {
            self.unrealized_pnl = self.calculate_pnl(current_price, self.size.abs());
            self.market_value = current_price * Decimal::from(self.size.abs());
        } else {
            self.unrealized_pnl = Decimal::ZERO;
            self.market_value = Decimal::ZERO;
        }
    }
    
    /// Get total P&L (realized + unrealized)
    pub fn total_pnl(&self) -> Decimal {
        self.realized_pnl + self.unrealized_pnl - self.total_commission
    }
    
    /// Reset position to flat
    pub fn reset(&mut self) {
        *self = Self::new();
    }
}

/// Position manager for tracking multiple positions
pub struct PositionManager {
    positions: std::collections::HashMap<String, Position>,
    default_position: Position,
}

impl PositionManager {
    pub fn new() -> Self {
        Self {
            positions: std::collections::HashMap::new(),
            default_position: Position::new(),
        }
    }
    
    /// Get position for a symbol
    pub fn get_position(&self, symbol: &str) -> &Position {
        self.positions.get(symbol).unwrap_or(&self.default_position)
    }
    
    /// Get mutable position for a symbol
    pub fn get_position_mut(&mut self, symbol: &str) -> &mut Position {
        self.positions.entry(symbol.to_string())
            .or_insert_with(Position::new)
    }
    
    /// Apply fill to position
    pub fn apply_fill(&mut self, symbol: &str, fill: &OrderFill) {
        let position = self.get_position_mut(symbol);
        position.apply_fill(fill);
    }
    
    /// Update all positions with current prices
    pub fn update_prices(&mut self, prices: &std::collections::HashMap<String, Decimal>) {
        for (symbol, position) in &mut self.positions {
            if let Some(&price) = prices.get(symbol) {
                position.update_unrealized_pnl(price);
            }
        }
    }
    
    /// Get total P&L across all positions
    pub fn total_pnl(&self) -> Decimal {
        self.positions.values()
            .map(|p| p.total_pnl())
            .sum()
    }
    
    /// Get all open positions
    pub fn open_positions(&self) -> Vec<(&String, &Position)> {
        self.positions.iter()
            .filter(|(_, p)| !p.is_flat())
            .collect()
    }
    
    /// Reset all positions
    pub fn reset(&mut self) {
        self.positions.clear();
    }
}