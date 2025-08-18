//! Objective functions for optimization

use crate::backtesting::BacktestResult;
use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};

/// Objective function for optimization
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum ObjectiveFunction {
    SharpeRatio,
    TotalPnl,
    WinRate,
    ProfitFactor,
    MinDrawdown,
    CalmarRatio,
    SortinoRatio,
    Custom,
}

impl ObjectiveFunction {
    /// Calculate objective value from backtest result
    pub fn calculate(&self, result: &BacktestResult) -> f64 {
        match self {
            ObjectiveFunction::SharpeRatio => result.sharpe_ratio,
            ObjectiveFunction::TotalPnl => {
                result.total_pnl.to_string().parse().unwrap_or(0.0)
            }
            ObjectiveFunction::WinRate => result.win_rate,
            ObjectiveFunction::ProfitFactor => result.profit_factor,
            ObjectiveFunction::MinDrawdown => {
                // Negate drawdown so minimizing drawdown = maximizing objective
                -result.max_drawdown.to_string().parse::<f64>().unwrap_or(0.0)
            }
            ObjectiveFunction::CalmarRatio => {
                self.calculate_calmar_ratio(result)
            }
            ObjectiveFunction::SortinoRatio => {
                self.calculate_sortino_ratio(result)
            }
            ObjectiveFunction::Custom => {
                // Custom weighted combination
                self.calculate_custom_objective(result)
            }
        }
    }
    
    fn calculate_calmar_ratio(&self, result: &BacktestResult) -> f64 {
        let returns = (result.final_capital - result.initial_capital) / result.initial_capital;
        let returns_f64 = returns.to_string().parse::<f64>().unwrap_or(0.0);
        let drawdown_f64 = result.max_drawdown.to_string().parse::<f64>().unwrap_or(1.0);
        
        if drawdown_f64.abs() < 0.001 {
            0.0
        } else {
            returns_f64 / drawdown_f64.abs()
        }
    }
    
    fn calculate_sortino_ratio(&self, result: &BacktestResult) -> f64 {
        // Simplified Sortino calculation
        // In production, would calculate from returns distribution
        result.sharpe_ratio * 1.2
    }
    
    fn calculate_custom_objective(&self, result: &BacktestResult) -> f64 {
        // Weighted combination of multiple objectives
        let sharpe_weight = 0.3;
        let pnl_weight = 0.2;
        let win_rate_weight = 0.2;
        let drawdown_weight = 0.3;
        
        let pnl_normalized = result.total_pnl.to_string().parse::<f64>()
            .unwrap_or(0.0) / 10000.0;
        let drawdown_normalized = result.max_drawdown.to_string().parse::<f64>()
            .unwrap_or(0.0) / 1000.0;
        
        result.sharpe_ratio * sharpe_weight
            + pnl_normalized * pnl_weight
            + result.win_rate * win_rate_weight
            - drawdown_normalized * drawdown_weight
    }
}

/// Optimization objective with constraints
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptimizationObjective {
    /// Primary objective function
    pub objective: ObjectiveFunction,
    
    /// Constraints to satisfy
    pub constraints: Vec<Constraint>,
    
    /// Weight for multi-objective optimization
    pub weight: f64,
}

/// Constraint for optimization
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Constraint {
    pub metric: ConstraintMetric,
    pub operator: ConstraintOperator,
    pub value: f64,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum ConstraintMetric {
    MinTrades,
    MaxDrawdown,
    MinWinRate,
    MinSharpe,
    MinProfitFactor,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum ConstraintOperator {
    GreaterThan,
    LessThan,
    GreaterOrEqual,
    LessOrEqual,
}

impl Constraint {
    /// Check if constraint is satisfied
    pub fn is_satisfied(&self, result: &BacktestResult) -> bool {
        let metric_value = match self.metric {
            ConstraintMetric::MinTrades => result.total_trades as f64,
            ConstraintMetric::MaxDrawdown => {
                result.max_drawdown.to_string().parse().unwrap_or(0.0)
            }
            ConstraintMetric::MinWinRate => result.win_rate,
            ConstraintMetric::MinSharpe => result.sharpe_ratio,
            ConstraintMetric::MinProfitFactor => result.profit_factor,
        };
        
        match self.operator {
            ConstraintOperator::GreaterThan => metric_value > self.value,
            ConstraintOperator::LessThan => metric_value < self.value,
            ConstraintOperator::GreaterOrEqual => metric_value >= self.value,
            ConstraintOperator::LessOrEqual => metric_value <= self.value,
        }
    }
}