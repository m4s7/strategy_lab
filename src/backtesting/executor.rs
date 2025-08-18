//! Strategy execution with realistic order fills and transaction costs

use crate::data::TickData;
use crate::strategy::{Order, OrderFill, OrderSide, OrderType, Position};
use crate::backtesting::{TransactionCostModel, SlippageConfig};
use chrono::Utc;
use rust_decimal::Decimal;
use uuid::Uuid;
use tracing::debug;

/// Executes strategy orders with realistic fills
pub struct StrategyExecutor {
    transaction_model: TransactionCostModel,
    current_capital: Decimal,
    initial_capital: Decimal,
    pending_orders: Vec<Order>,
    filled_orders: Vec<OrderFill>,
}

impl StrategyExecutor {
    pub fn new(transaction_model: TransactionCostModel, initial_capital: Decimal) -> Self {
        Self {
            transaction_model,
            current_capital: initial_capital,
            initial_capital,
            pending_orders: Vec::new(),
            filled_orders: Vec::new(),
        }
    }
    
    /// Execute an order with simulated market conditions
    pub fn execute_order(
        &mut self,
        order: Order,
        tick: &TickData,
        slippage_config: &SlippageConfig,
    ) -> Option<OrderFill> {
        // Simulate order execution based on type
        let fill_price = match order.order_type {
            OrderType::Market => {
                // Market orders execute immediately with slippage
                self.calculate_fill_price(tick.price, order.side, order.quantity, slippage_config)
            }
            OrderType::Limit => {
                // Check if limit price would fill
                if let Some(limit) = order.limit_price {
                    if self.would_limit_fill(limit, tick.price, order.side) {
                        limit
                    } else {
                        // Order doesn't fill
                        self.pending_orders.push(order);
                        return None;
                    }
                } else {
                    return None;
                }
            }
            OrderType::Stop | OrderType::StopLimit => {
                // Simplified stop order handling
                if let Some(stop) = order.stop_price {
                    if self.would_stop_trigger(stop, tick.price, order.side) {
                        self.calculate_fill_price(tick.price, order.side, order.quantity, slippage_config)
                    } else {
                        self.pending_orders.push(order);
                        return None;
                    }
                } else {
                    return None;
                }
            }
        };
        
        // Calculate transaction costs
        let commission = self.transaction_model.calculate_commission(order.quantity);
        let slippage = (fill_price - tick.price).abs();
        
        // Create fill
        let fill = OrderFill {
            order_id: order.id.clone(),
            timestamp: tick.timestamp,
            price: fill_price,
            quantity: order.quantity,
            side: order.side,
            commission,
            slippage,
        };
        
        // Update capital
        let trade_value = fill_price * Decimal::from(order.quantity);
        match order.side {
            OrderSide::Buy => self.current_capital -= trade_value + commission,
            OrderSide::Sell => self.current_capital += trade_value - commission,
        }
        
        self.filled_orders.push(fill.clone());
        
        debug!("Order executed: {:?} {} @ {} (slippage: {}, commission: {})",
            order.side, order.quantity, fill_price, slippage, commission);
        
        Some(fill)
    }
    
    /// Calculate fill price with slippage
    fn calculate_fill_price(
        &self,
        market_price: Decimal,
        side: OrderSide,
        quantity: i32,
        config: &SlippageConfig,
    ) -> Decimal {
        // Fixed slippage component
        let mut slippage = config.fixed_slippage;
        
        // Volume-based slippage
        let volume_slippage = Decimal::from_f64_retain(
            quantity as f64 * config.volume_slippage
        ).unwrap_or(Decimal::ZERO);
        slippage += volume_slippage;
        
        // Market impact
        let impact = Decimal::from_f64_retain(
            quantity as f64 * config.market_impact * market_price.to_string().parse::<f64>().unwrap_or(0.0)
        ).unwrap_or(Decimal::ZERO);
        slippage += impact;
        
        // Apply slippage based on side
        match side {
            OrderSide::Buy => market_price + slippage,
            OrderSide::Sell => market_price - slippage,
        }
    }
    
    /// Check if limit order would fill
    fn would_limit_fill(&self, limit_price: Decimal, market_price: Decimal, side: OrderSide) -> bool {
        match side {
            OrderSide::Buy => market_price <= limit_price,
            OrderSide::Sell => market_price >= limit_price,
        }
    }
    
    /// Check if stop order would trigger
    fn would_stop_trigger(&self, stop_price: Decimal, market_price: Decimal, side: OrderSide) -> bool {
        match side {
            OrderSide::Buy => market_price >= stop_price,
            OrderSide::Sell => market_price <= stop_price,
        }
    }
    
    /// Get current capital
    pub fn get_current_capital(&self) -> Decimal {
        self.current_capital
    }
    
    /// Get equity including open position
    pub fn get_equity(&self, position: &Position, current_price: Decimal) -> Decimal {
        let mut equity = self.current_capital;
        
        if !position.is_flat() {
            // Add unrealized P&L
            let unrealized = if position.is_long() {
                (current_price - position.avg_entry_price) * Decimal::from(position.size)
            } else {
                (position.avg_entry_price - current_price) * Decimal::from(position.size.abs())
            };
            equity += unrealized;
        }
        
        equity
    }
    
    /// Process pending orders
    pub fn process_pending_orders(&mut self, tick: &TickData, slippage_config: &SlippageConfig) -> Vec<OrderFill> {
        let mut fills = Vec::new();
        let mut remaining_orders = Vec::new();
        
        for order in self.pending_orders.drain(..) {
            if let Some(fill) = self.execute_order(order.clone(), tick, slippage_config) {
                fills.push(fill);
            } else {
                remaining_orders.push(order);
            }
        }
        
        self.pending_orders = remaining_orders;
        fills
    }
}

/// Execution context for strategies
pub struct ExecutionContext {
    pub timestamp: chrono::DateTime<Utc>,
    pub latency_ms: u32,
    pub market_open: bool,
    pub session_high: Option<Decimal>,
    pub session_low: Option<Decimal>,
    pub session_volume: i64,
}