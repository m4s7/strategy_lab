//! Strategy configuration using simple YAML/JSON format

use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Main strategy configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StrategyConfig {
    /// Strategy name
    pub name: String,
    
    /// Strategy version
    pub version: String,
    
    /// Core parameters
    pub parameters: StrategyParameters,
    
    /// Risk constraints
    pub constraints: RiskConstraints,
    
    /// Optimization ranges (for parameter optimization)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub optimization: Option<OptimizationConfig>,
}

/// Strategy parameters that can be optimized
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StrategyParameters {
    // Common parameters for all strategies
    
    /// Position size per trade
    pub position_size: i32,
    
    /// Stop loss in ticks
    pub stop_loss: Decimal,
    
    /// Take profit in ticks
    #[serde(skip_serializing_if = "Option::is_none")]
    pub take_profit: Option<Decimal>,
    
    /// Maximum holding time in seconds
    #[serde(skip_serializing_if = "Option::is_none")]
    pub max_holding_time: Option<u64>,
    
    // Strategy-specific parameters (use HashMap for flexibility)
    
    /// Custom parameters specific to each strategy
    #[serde(flatten)]
    pub custom: HashMap<String, ParameterValue>,
}

/// Parameter value that can be various types
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(untagged)]
pub enum ParameterValue {
    Float(f64),
    Integer(i64),
    Decimal(Decimal),
    Boolean(bool),
    String(String),
}

impl ParameterValue {
    pub fn as_f64(&self) -> Option<f64> {
        match self {
            ParameterValue::Float(v) => Some(*v),
            ParameterValue::Integer(v) => Some(*v as f64),
            ParameterValue::Decimal(v) => Some(v.to_string().parse().ok()?),
            _ => None,
        }
    }
    
    pub fn as_decimal(&self) -> Option<Decimal> {
        match self {
            ParameterValue::Decimal(v) => Some(*v),
            ParameterValue::Float(v) => Some(Decimal::from_f64_retain(*v)?),
            ParameterValue::Integer(v) => Some(Decimal::from(*v)),
            _ => None,
        }
    }
}

/// Risk management constraints
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RiskConstraints {
    /// Maximum position size
    pub max_position: i32,
    
    /// Maximum drawdown allowed
    pub max_drawdown: Decimal,
    
    /// Maximum daily loss
    #[serde(skip_serializing_if = "Option::is_none")]
    pub max_daily_loss: Option<Decimal>,
    
    /// Minimum win rate required
    #[serde(skip_serializing_if = "Option::is_none")]
    pub min_win_rate: Option<f64>,
}

/// Configuration for parameter optimization
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptimizationConfig {
    /// Parameters to optimize with their ranges
    pub parameters: HashMap<String, ParameterRange>,
    
    /// Optimization method
    pub method: OptimizationMethod,
    
    /// Objective function to optimize
    pub objective: ObjectiveFunction,
}

/// Range for parameter optimization
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParameterRange {
    pub min: ParameterValue,
    pub max: ParameterValue,
    pub step: ParameterValue,
}

/// Optimization methods
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum OptimizationMethod {
    GridSearch,
    GeneticAlgorithm,
    BayesianOptimization,
}

/// Objective functions for optimization
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ObjectiveFunction {
    SharpeRatio,
    TotalPnl,
    WinRate,
    ProfitFactor,
    MinDrawdown,
}

impl Default for StrategyConfig {
    fn default() -> Self {
        Self {
            name: "DefaultStrategy".to_string(),
            version: "1.0.0".to_string(),
            parameters: StrategyParameters {
                position_size: 1,
                stop_loss: Decimal::from(2),
                take_profit: Some(Decimal::from(4)),
                max_holding_time: Some(300), // 5 minutes
                custom: HashMap::new(),
            },
            constraints: RiskConstraints {
                max_position: 5,
                max_drawdown: Decimal::from(1000),
                max_daily_loss: Some(Decimal::from(500)),
                min_win_rate: Some(0.4),
            },
            optimization: None,
        }
    }
}

/// Example configuration builders for common strategies
impl StrategyConfig {
    /// Create configuration for order book imbalance strategy
    pub fn order_book_imbalance() -> Self {
        let mut config = Self::default();
        config.name = "OrderBookImbalance".to_string();
        
        // Add custom parameters
        config.parameters.custom.insert(
            "imbalance_threshold".to_string(),
            ParameterValue::Float(0.6),
        );
        config.parameters.custom.insert(
            "min_spread".to_string(),
            ParameterValue::Decimal(Decimal::from_str_exact("0.25").unwrap()),
        );
        config.parameters.custom.insert(
            "depth_levels".to_string(),
            ParameterValue::Integer(3),
        );
        
        config
    }
    
    /// Create configuration for bid-ask bounce strategy
    pub fn bid_ask_bounce() -> Self {
        let mut config = Self::default();
        config.name = "BidAskBounce".to_string();
        
        // Add custom parameters
        config.parameters.custom.insert(
            "bounce_threshold".to_string(),
            ParameterValue::Decimal(Decimal::from_str_exact("0.5").unwrap()),
        );
        config.parameters.custom.insert(
            "min_volume".to_string(),
            ParameterValue::Integer(100),
        );
        config.parameters.custom.insert(
            "entry_offset".to_string(),
            ParameterValue::Decimal(Decimal::from_str_exact("0.1").unwrap()),
        );
        
        config
    }
}

/// Load configuration from YAML file
pub fn load_config(path: &str) -> Result<StrategyConfig, Box<dyn std::error::Error>> {
    let contents = std::fs::read_to_string(path)?;
    let config: StrategyConfig = serde_yaml::from_str(&contents)?;
    Ok(config)
}

/// Save configuration to YAML file
pub fn save_config(config: &StrategyConfig, path: &str) -> Result<(), Box<dyn std::error::Error>> {
    let yaml = serde_yaml::to_string(config)?;
    std::fs::write(path, yaml)?;
    Ok(())
}