//! Performance and risk metrics calculation

use crate::strategy::Position;
use crate::strategy::traits::OrderFill;
use chrono::{DateTime, Utc};
use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};
use std::collections::VecDeque;

/// Performance metrics tracker
#[derive(Debug, Clone)]
pub struct PerformanceMetrics {
    pub equity_curve: Vec<(DateTime<Utc>, Decimal)>,
    pub returns: Vec<f64>,
    pub trades: Vec<TradeRecord>,
    pub high_water_mark: Decimal,
    pub current_drawdown: Decimal,
    pub max_drawdown: Decimal,
    pub total_return: f64,
    pub sharpe_ratio: f64,
    pub win_rate: f64,
    pub profit_factor: f64,
    pub total_trades: usize,
    pub avg_trade_duration_ms: u64,
    pub volatility: f64,
    pub beta: f64,
    pub alpha: f64,
}

impl PerformanceMetrics {
    pub fn new() -> Self {
        Self {
            equity_curve: Vec::new(),
            returns: Vec::new(),
            trades: Vec::new(),
            high_water_mark: Decimal::ZERO,
            current_drawdown: Decimal::ZERO,
            max_drawdown: Decimal::ZERO,
            total_return: 0.0,
            sharpe_ratio: 0.0,
            win_rate: 0.0,
            profit_factor: 0.0,
            total_trades: 0,
            avg_trade_duration_ms: 0,
            volatility: 0.0,
            beta: 0.0,
            alpha: 0.0,
        }
    }
    
    /// Update equity curve
    pub fn update_equity(&mut self, equity: Decimal, timestamp: DateTime<Utc>) {
        self.equity_curve.push((timestamp, equity));
        
        // Update drawdown
        if equity > self.high_water_mark {
            self.high_water_mark = equity;
            self.current_drawdown = Decimal::ZERO;
        } else {
            self.current_drawdown = self.high_water_mark - equity;
            if self.current_drawdown > self.max_drawdown {
                self.max_drawdown = self.current_drawdown;
            }
        }
        
        // Calculate return
        if self.equity_curve.len() > 1 {
            let prev_equity = self.equity_curve[self.equity_curve.len() - 2].1;
            if prev_equity > Decimal::ZERO {
                let return_pct = ((equity - prev_equity) / prev_equity)
                    .to_string().parse::<f64>().unwrap_or(0.0);
                self.returns.push(return_pct);
            }
        }
    }
    
    /// Update position metrics
    pub fn update_position(&mut self, position: &Position) {
        // Track position metrics if needed
    }
    
    /// Record a trade
    pub fn record_trade(&mut self, fill: &OrderFill) {
        self.trades.push(TradeRecord::from_fill(fill));
    }
    
    /// Calculate Sharpe ratio
    pub fn calculate_sharpe_ratio(&self) -> f64 {
        if self.returns.is_empty() {
            return 0.0;
        }
        
        let mean_return = self.returns.iter().sum::<f64>() / self.returns.len() as f64;
        let variance = self.returns.iter()
            .map(|r| (r - mean_return).powi(2))
            .sum::<f64>() / self.returns.len() as f64;
        let std_dev = variance.sqrt();
        
        if std_dev == 0.0 {
            0.0
        } else {
            // Annualized Sharpe (assuming daily returns, 252 trading days)
            mean_return / std_dev * (252.0_f64).sqrt()
        }
    }
    
    /// Calculate Sortino ratio
    pub fn calculate_sortino_ratio(&self) -> f64 {
        if self.returns.is_empty() {
            return 0.0;
        }
        
        let mean_return = self.returns.iter().sum::<f64>() / self.returns.len() as f64;
        let downside_returns: Vec<f64> = self.returns.iter()
            .filter(|&&r| r < 0.0)
            .copied()
            .collect();
        
        if downside_returns.is_empty() {
            return 0.0;
        }
        
        let downside_variance = downside_returns.iter()
            .map(|r| r.powi(2))
            .sum::<f64>() / downside_returns.len() as f64;
        let downside_dev = downside_variance.sqrt();
        
        if downside_dev == 0.0 {
            0.0
        } else {
            mean_return / downside_dev * (252.0_f64).sqrt()
        }
    }
    
    /// Calculate Calmar ratio
    pub fn calculate_calmar_ratio(&self) -> f64 {
        if self.max_drawdown == Decimal::ZERO || self.equity_curve.is_empty() {
            return 0.0;
        }
        
        let total_return = if self.equity_curve.len() >= 2 {
            let start = self.equity_curve.first().unwrap().1;
            let end = self.equity_curve.last().unwrap().1;
            ((end - start) / start).to_string().parse::<f64>().unwrap_or(0.0)
        } else {
            0.0
        };
        
        let max_dd = self.max_drawdown.to_string().parse::<f64>().unwrap_or(1.0);
        total_return / max_dd
    }
    
    /// Get equity curve
    pub fn get_equity_curve(&self) -> &[(DateTime<Utc>, Decimal)] {
        &self.equity_curve
    }
    
    /// Get maximum drawdown
    pub fn get_max_drawdown(&self) -> Decimal {
        self.max_drawdown
    }
}

/// Record of a single trade
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TradeRecord {
    pub timestamp: DateTime<Utc>,
    pub side: crate::strategy::OrderSide,
    pub quantity: i32,
    pub price: Decimal,
    pub commission: Decimal,
    pub slippage: Decimal,
}

impl TradeRecord {
    pub fn from_fill(fill: &OrderFill) -> Self {
        Self {
            timestamp: fill.timestamp,
            side: fill.side,
            quantity: fill.quantity,
            price: fill.price,
            commission: fill.commission,
            slippage: fill.slippage,
        }
    }
}

/// Risk metrics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RiskMetrics {
    pub max_drawdown: Decimal,
    pub max_drawdown_duration: i64,
    pub value_at_risk: Decimal,
    pub conditional_value_at_risk: Decimal,
    pub beta: f64,
    pub correlation: f64,
}

/// Trade statistics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TradeStatistics {
    pub total_trades: u32,
    pub winning_trades: u32,
    pub losing_trades: u32,
    pub avg_win: Decimal,
    pub avg_loss: Decimal,
    pub largest_win: Decimal,
    pub largest_loss: Decimal,
    pub avg_trade_duration: f64,
    pub profit_factor: f64,
    pub expectancy: Decimal,
    pub win_rate: f64,
}