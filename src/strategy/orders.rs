//! Order management types and utilities

use chrono::{DateTime, Utc};
use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Order to be submitted to the market
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Order {
    /// Unique order identifier
    pub id: String,
    
    /// Order type
    pub order_type: OrderType,
    
    /// Buy or sell
    pub side: OrderSide,
    
    /// Order quantity
    pub quantity: i32,
    
    /// Limit price (for limit orders)
    pub limit_price: Option<Decimal>,
    
    /// Stop price (for stop orders)
    pub stop_price: Option<Decimal>,
    
    /// Time in force
    pub time_in_force: TimeInForce,
    
    /// Order creation timestamp
    pub timestamp: DateTime<Utc>,
    
    /// Optional tag for strategy tracking
    pub tag: Option<String>,
}

impl Order {
    /// Create a new market order
    pub fn market(side: OrderSide, quantity: i32) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            order_type: OrderType::Market,
            side,
            quantity,
            limit_price: None,
            stop_price: None,
            time_in_force: TimeInForce::IOC,
            timestamp: Utc::now(),
            tag: None,
        }
    }
    
    /// Create a new limit order
    pub fn limit(side: OrderSide, quantity: i32, price: Decimal) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            order_type: OrderType::Limit,
            side,
            quantity,
            limit_price: Some(price),
            stop_price: None,
            time_in_force: TimeInForce::GTC,
            timestamp: Utc::now(),
            tag: None,
        }
    }
    
    /// Create a new stop order
    pub fn stop(side: OrderSide, quantity: i32, stop_price: Decimal) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            order_type: OrderType::Stop,
            side,
            quantity,
            limit_price: None,
            stop_price: Some(stop_price),
            time_in_force: TimeInForce::GTC,
            timestamp: Utc::now(),
            tag: None,
        }
    }
    
    /// Create a new stop-limit order
    pub fn stop_limit(side: OrderSide, quantity: i32, stop_price: Decimal, limit_price: Decimal) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            order_type: OrderType::StopLimit,
            side,
            quantity,
            limit_price: Some(limit_price),
            stop_price: Some(stop_price),
            time_in_force: TimeInForce::GTC,
            timestamp: Utc::now(),
            tag: None,
        }
    }
    
    /// Add a tag to the order
    pub fn with_tag(mut self, tag: String) -> Self {
        self.tag = Some(tag);
        self
    }
    
    /// Set time in force
    pub fn with_time_in_force(mut self, tif: TimeInForce) -> Self {
        self.time_in_force = tif;
        self
    }
}

/// Order types
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum OrderType {
    /// Market order - execute immediately at best available price
    Market,
    
    /// Limit order - execute at specified price or better
    Limit,
    
    /// Stop order - becomes market order when stop price is reached
    Stop,
    
    /// Stop-limit order - becomes limit order when stop price is reached
    StopLimit,
}

/// Order side (buy or sell)
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum OrderSide {
    Buy,
    Sell,
}

impl OrderSide {
    /// Get the opposite side
    pub fn opposite(&self) -> Self {
        match self {
            OrderSide::Buy => OrderSide::Sell,
            OrderSide::Sell => OrderSide::Buy,
        }
    }
}

/// Time in force for orders
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TimeInForce {
    /// Good Till Cancelled
    GTC,
    
    /// Immediate Or Cancel
    IOC,
    
    /// Fill Or Kill
    FOK,
    
    /// Day order
    Day,
}

/// Order status
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum OrderStatus {
    /// Order submitted but not yet acknowledged
    Pending,
    
    /// Order accepted by exchange
    Open,
    
    /// Order partially filled
    PartiallyFilled,
    
    /// Order completely filled
    Filled,
    
    /// Order cancelled
    Cancelled,
    
    /// Order rejected by exchange
    Rejected,
}

/// Order execution report
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionReport {
    pub order_id: String,
    pub status: OrderStatus,
    pub filled_quantity: i32,
    pub remaining_quantity: i32,
    pub average_price: Option<Decimal>,
    pub last_fill_price: Option<Decimal>,
    pub last_fill_quantity: Option<i32>,
    pub commission: Decimal,
    pub timestamp: DateTime<Utc>,
    pub reject_reason: Option<String>,
}