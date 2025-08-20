use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StrategyTemplate {
    pub name: String,
    pub description: String,
    pub version: String,
    pub parameters: HashMap<String, ParameterTemplate>,
    pub code_template: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParameterTemplate {
    pub name: String,
    pub param_type: String,
    pub default_value: serde_json::Value,
    pub min_value: Option<f64>,
    pub max_value: Option<f64>,
    pub description: String,
}

impl StrategyTemplate {
    pub fn order_book_imbalance() -> Self {
        let mut parameters = HashMap::new();
        
        parameters.insert("imbalance_threshold".to_string(), ParameterTemplate {
            name: "Imbalance Threshold".to_string(),
            param_type: "float".to_string(),
            default_value: serde_json::Value::Number(serde_json::Number::from_f64(0.6).unwrap()),
            min_value: Some(0.5),
            max_value: Some(0.9),
            description: "Order book imbalance threshold for signal generation".to_string(),
        });

        parameters.insert("min_spread".to_string(), ParameterTemplate {
            name: "Minimum Spread".to_string(),
            param_type: "float".to_string(),
            default_value: serde_json::Value::Number(serde_json::Number::from_f64(0.25).unwrap()),
            min_value: Some(0.1),
            max_value: Some(1.0),
            description: "Minimum bid-ask spread required for trading".to_string(),
        });

        Self {
            name: "Order Book Imbalance".to_string(),
            description: "Strategy that trades based on order book volume imbalances".to_string(),
            version: "1.0".to_string(),
            parameters,
            code_template: include_str!("examples/order_book_imbalance.rs").to_string(),
        }
    }

    pub fn bid_ask_bounce() -> Self {
        let mut parameters = HashMap::new();
        
        parameters.insert("bounce_threshold".to_string(), ParameterTemplate {
            name: "Bounce Threshold".to_string(),
            param_type: "float".to_string(),
            default_value: serde_json::Value::Number(serde_json::Number::from_f64(2.0).unwrap()),
            min_value: Some(1.0),
            max_value: Some(5.0),
            description: "Price bounce threshold in ticks".to_string(),
        });

        Self {
            name: "Bid Ask Bounce".to_string(),
            description: "Strategy that capitalizes on price bounces between bid and ask".to_string(),
            version: "1.0".to_string(),
            parameters,
            code_template: include_str!("examples/bid_ask_bounce.rs").to_string(),
        }
    }
}