//! Workflow templates for common patterns

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StepTemplate {
    pub id: String,
    pub name: String,
    pub template_type: TemplateType,
    pub configuration: serde_json::Value,
    pub customizable_fields: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TemplateType {
    DataIngestion,
    StrategyConfig,
    Optimization,
    Validation,
    Analysis,
    Deployment,
}

impl StepTemplate {
    pub fn basic_data_ingestion() -> Self {
        Self {
            id: "basic_data_ingestion".to_string(),
            name: "Basic Data Ingestion".to_string(),
            template_type: TemplateType::DataIngestion,
            configuration: serde_json::json!({
                "file_format": "parquet",
                "validation_level": "strict",
                "memory_limit": "32GB"
            }),
            customizable_fields: vec![
                "file_path".to_string(),
                "validation_level".to_string(),
            ],
        }
    }
}