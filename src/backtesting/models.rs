//! Transaction cost and slippage models

use crate::backtesting::engine::TransactionCostConfig;
use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};

/// Model for calculating transaction costs
#[derive(Debug, Clone)]
pub struct TransactionCostModel {
    commission_per_contract: Decimal,
    exchange_fee: Decimal,
    regulatory_fee: Decimal,
}

impl TransactionCostModel {
    pub fn new(
        commission_per_contract: Decimal,
        exchange_fee: Decimal,
        regulatory_fee: Decimal,
    ) -> Self {
        Self {
            commission_per_contract,
            exchange_fee,
            regulatory_fee,
        }
    }
    
    pub fn from_config(config: &TransactionCostConfig) -> Self {
        Self::new(
            config.commission_per_contract,
            config.exchange_fee,
            config.regulatory_fee,
        )
    }
    
    /// Calculate total commission for a trade
    pub fn calculate_commission(&self, quantity: i32) -> Decimal {
        let contracts = Decimal::from(quantity.abs());
        (self.commission_per_contract + self.exchange_fee + self.regulatory_fee) * contracts
    }
    
    /// Calculate round-trip costs
    pub fn round_trip_cost(&self, quantity: i32) -> Decimal {
        self.calculate_commission(quantity) * Decimal::from(2)
    }
}

/// Model for calculating slippage
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SlippageModel {
    /// Base slippage in ticks
    pub base_slippage: Decimal,
    
    /// Slippage per unit of size
    pub size_impact: f64,
    
    /// Volatility multiplier
    pub volatility_impact: f64,
    
    /// Time of day impact
    pub time_impact: f64,
}

impl SlippageModel {
    /// Calculate expected slippage
    pub fn calculate_slippage(
        &self,
        size: i32,
        volatility: f64,
        hour: u32,
    ) -> Decimal {
        let mut slippage = self.base_slippage;
        
        // Size impact
        let size_component = Decimal::from_f64_retain(
            size as f64 * self.size_impact
        ).unwrap_or(Decimal::ZERO);
        slippage += size_component;
        
        // Volatility impact
        let vol_component = Decimal::from_f64_retain(
            volatility * self.volatility_impact
        ).unwrap_or(Decimal::ZERO);
        slippage += vol_component;
        
        // Time of day impact (higher at open/close)
        let time_multiplier = if hour < 10 || hour > 15 {
            1.5
        } else {
            1.0
        };
        
        slippage * Decimal::from_f64_retain(time_multiplier).unwrap_or(Decimal::ONE)
    }
}

/// Model for simulating latency
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LatencyModel {
    /// Base latency in milliseconds
    pub base_latency_ms: u32,
    
    /// Network jitter range
    pub jitter_ms: u32,
    
    /// Processing delay
    pub processing_ms: u32,
}

impl LatencyModel {
    /// Get total latency for order execution
    pub fn get_latency(&self) -> u32 {
        use rand::Rng;
        let mut rng = rand::thread_rng();
        
        let jitter = rng.gen_range(0..=self.jitter_ms);
        self.base_latency_ms + jitter + self.processing_ms
    }
    
    /// Simulate latency impact on fill price
    pub fn apply_latency(&self, price: Decimal, price_velocity: Decimal) -> Decimal {
        let latency_secs = self.get_latency() as f64 / 1000.0;
        let price_change = price_velocity * Decimal::from_f64_retain(latency_secs)
            .unwrap_or(Decimal::ZERO);
        
        price + price_change
    }
}

impl Default for LatencyModel {
    fn default() -> Self {
        Self {
            base_latency_ms: 1,
            jitter_ms: 2,
            processing_ms: 1,
        }
    }
}