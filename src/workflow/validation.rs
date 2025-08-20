//! Real-time validation system for workflow inputs

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use crate::workflow::{WorkflowStep, WorkflowInput, InputType};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationEngine {
    field_validators: HashMap<String, FieldValidator>,
    cross_field_validators: Vec<CrossFieldValidator>,
    workflow_validators: HashMap<String, WorkflowValidator>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationResult {
    pub field_name: String,
    pub is_valid: bool,
    pub error_message: Option<String>,
    pub warning_message: Option<String>,
    pub suggestion: Option<String>,
    pub severity: ValidationSeverity,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum ValidationSeverity {
    Error,
    Warning,
    Info,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ValidationRule {
    Required,
    MinValue(f64),
    MaxValue(f64),
    MinLength(usize),
    MaxLength(usize),
    Pattern(String),
    StringInSet(Vec<String>),
    FileExists,
    FileFormat(String),
    Custom(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ValidationRequirement {
    DataQuality,
    ParameterConsistency,
    ParameterRanges,
    SufficientData,
    SignificanceLevel,
    Custom(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FieldValidator {
    pub field: String,
    pub rules: Vec<ValidationRule>,
    pub error_messages: HashMap<String, String>,
    pub suggestions: HashMap<String, String>,
    pub real_time: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CrossFieldValidator {
    pub fields: Vec<String>,
    pub validation_logic: String,
    pub dependency_rules: Vec<DependencyRule>,
    pub error_message: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DependencyRule {
    pub field: String,
    pub depends_on: String,
    pub condition: DependencyCondition,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum DependencyCondition {
    Equals(String),
    NotEquals(String),
    GreaterThan(f64),
    LessThan(f64),
    IsSet,
    IsEmpty,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowValidator {
    pub workflow_step: String,
    pub validation_rules: Vec<ValidationRule>,
    pub requirements: Vec<ValidationRequirement>,
}

impl ValidationEngine {
    pub fn new() -> Self {
        let mut engine = Self {
            field_validators: HashMap::new(),
            cross_field_validators: Vec::new(),
            workflow_validators: HashMap::new(),
        };
        
        engine.initialize_default_validators();
        engine
    }
    
    /// Validate step inputs in real-time
    pub fn validate_step_inputs(&self, step: &WorkflowStep, inputs: &HashMap<String, serde_json::Value>) -> Vec<ValidationResult> {
        let mut results = Vec::new();
        
        // Validate individual fields
        for input_spec in &step.required_inputs {
            let validation_result = self.validate_field(input_spec, inputs.get(&input_spec.name));
            results.push(validation_result);
        }
        
        // Validate cross-field dependencies
        for cross_validator in &self.cross_field_validators {
            if self.is_validator_applicable(&cross_validator.fields, step) {
                let cross_result = self.validate_cross_field(cross_validator, inputs);
                if let Some(result) = cross_result {
                    results.push(result);
                }
            }
        }
        
        // Validate workflow-specific requirements
        if let Some(workflow_validator) = self.workflow_validators.get(&step.id) {
            let workflow_results = self.validate_workflow_requirements(workflow_validator, inputs);
            results.extend(workflow_results);
        }
        
        results
    }
    
    /// Validate individual field
    fn validate_field(&self, input_spec: &WorkflowInput, value: Option<&serde_json::Value>) -> ValidationResult {
        let mut result = ValidationResult {
            field_name: input_spec.name.clone(),
            is_valid: true,
            error_message: None,
            warning_message: None,
            suggestion: None,
            severity: ValidationSeverity::Info,
        };
        
        // Check if required field is present
        if input_spec.required && value.is_none() {
            result.is_valid = false;
            result.error_message = Some(format!("{} is required", input_spec.name));
            result.severity = ValidationSeverity::Error;
            return result;
        }
        
        if let Some(value) = value {
            // Validate against rules
            for rule in &input_spec.validation_rules {
                match self.validate_rule(rule, value, &input_spec.input_type) {
                    Ok(_) => {},
                    Err(error) => {
                        result.is_valid = false;
                        result.error_message = Some(error);
                        result.severity = ValidationSeverity::Error;
                        
                        // Add suggestions based on rule type
                        result.suggestion = self.get_rule_suggestion(rule, value);
                        break;
                    }
                }
            }
        }
        
        result
    }
    
    /// Validate single rule against value
    fn validate_rule(&self, rule: &ValidationRule, value: &serde_json::Value, input_type: &InputType) -> Result<(), String> {
        match rule {
            ValidationRule::Required => {
                if value.is_null() {
                    Err("Value is required".to_string())
                } else {
                    Ok(())
                }
            }
            ValidationRule::MinValue(min) => {
                if let Some(num) = value.as_f64() {
                    if num < *min {
                        Err(format!("Value must be at least {}", min))
                    } else {
                        Ok(())
                    }
                } else {
                    Err("Value must be a number".to_string())
                }
            }
            ValidationRule::MaxValue(max) => {
                if let Some(num) = value.as_f64() {
                    if num > *max {
                        Err(format!("Value must be at most {}", max))
                    } else {
                        Ok(())
                    }
                } else {
                    Err("Value must be a number".to_string())
                }
            }
            ValidationRule::MinLength(min) => {
                if let Some(str_val) = value.as_str() {
                    if str_val.len() < *min {
                        Err(format!("Value must be at least {} characters", min))
                    } else {
                        Ok(())
                    }
                } else {
                    Err("Value must be a string".to_string())
                }
            }
            ValidationRule::MaxLength(max) => {
                if let Some(str_val) = value.as_str() {
                    if str_val.len() > *max {
                        Err(format!("Value must be at most {} characters", max))
                    } else {
                        Ok(())
                    }
                } else {
                    Err("Value must be a string".to_string())
                }
            }
            ValidationRule::Pattern(pattern) => {
                if let Some(str_val) = value.as_str() {
                    // Simple pattern matching - in real implementation, use regex
                    if pattern == "email" && !str_val.contains('@') {
                        Err("Invalid email format".to_string())
                    } else {
                        Ok(())
                    }
                } else {
                    Err("Value must be a string".to_string())
                }
            }
            ValidationRule::StringInSet(valid_values) => {
                if let Some(str_val) = value.as_str() {
                    if valid_values.contains(&str_val.to_string()) {
                        Ok(())
                    } else {
                        Err(format!("Value must be one of: {}", valid_values.join(", ")))
                    }
                } else {
                    Err("Value must be a string".to_string())
                }
            }
            ValidationRule::FileExists => {
                if let Some(path) = value.as_str() {
                    if std::path::Path::new(path).exists() {
                        Ok(())
                    } else {
                        Err(format!("File does not exist: {}", path))
                    }
                } else {
                    Err("Value must be a file path".to_string())
                }
            }
            ValidationRule::FileFormat(format) => {
                if let Some(path) = value.as_str() {
                    if path.ends_with(&format!(".{}", format)) {
                        Ok(())
                    } else {
                        Err(format!("File must be in {} format", format))
                    }
                } else {
                    Err("Value must be a file path".to_string())
                }
            }
            ValidationRule::Custom(rule_name) => {
                self.validate_custom_rule(rule_name, value, input_type)
            }
        }
    }
    
    /// Get suggestion for failed rule
    fn get_rule_suggestion(&self, rule: &ValidationRule, value: &serde_json::Value) -> Option<String> {
        match rule {
            ValidationRule::MinValue(min) => {
                Some(format!("Try a value of {} or higher", min))
            }
            ValidationRule::MaxValue(max) => {
                Some(format!("Try a value of {} or lower", max))
            }
            ValidationRule::StringInSet(valid_values) => {
                Some(format!("Valid options are: {}", valid_values.join(", ")))
            }
            ValidationRule::FileExists => {
                Some("Check the file path and ensure the file exists".to_string())
            }
            ValidationRule::FileFormat(format) => {
                Some(format!("Select a file with .{} extension", format))
            }
            _ => None,
        }
    }
    
    /// Validate custom rule
    fn validate_custom_rule(&self, rule_name: &str, value: &serde_json::Value, _input_type: &InputType) -> Result<(), String> {
        match rule_name {
            "positive_number" => {
                if let Some(num) = value.as_f64() {
                    if num > 0.0 {
                        Ok(())
                    } else {
                        Err("Value must be positive".to_string())
                    }
                } else {
                    Err("Value must be a number".to_string())
                }
            }
            "valid_sharpe_ratio" => {
                if let Some(num) = value.as_f64() {
                    if num >= -5.0 && num <= 10.0 {
                        Ok(())
                    } else {
                        Err("Sharpe ratio must be between -5 and 10".to_string())
                    }
                } else {
                    Err("Sharpe ratio must be a number".to_string())
                }
            }
            "reasonable_drawdown" => {
                if let Some(num) = value.as_f64() {
                    if num >= -50.0 && num <= 0.0 {
                        Ok(())
                    } else {
                        Err("Drawdown should be between -50% and 0%".to_string())
                    }
                } else {
                    Err("Drawdown must be a number".to_string())
                }
            }
            "grid_search_size" => {
                if let Some(num) = value.as_f64() {
                    if num <= 10000.0 {
                        Ok(())
                    } else {
                        Err("Grid search too large - may take excessive time".to_string())
                    }
                } else {
                    Err("Grid search size must be a number".to_string())
                }
            }
            _ => Err(format!("Unknown custom rule: {}", rule_name))
        }
    }
    
    /// Validate cross-field dependencies
    fn validate_cross_field(&self, validator: &CrossFieldValidator, inputs: &HashMap<String, serde_json::Value>) -> Option<ValidationResult> {
        // Check all required fields are present
        let mut missing_fields = Vec::new();
        for field in &validator.fields {
            if !inputs.contains_key(field) {
                missing_fields.push(field);
            }
        }
        
        if !missing_fields.is_empty() {
            return None; // Can't validate cross-field if fields are missing
        }
        
        // Validate dependency rules
        for dep_rule in &validator.dependency_rules {
            if let (Some(field_value), Some(dep_value)) = (inputs.get(&dep_rule.field), inputs.get(&dep_rule.depends_on)) {
                if !self.check_dependency_condition(&dep_rule.condition, field_value, dep_value) {
                    return Some(ValidationResult {
                        field_name: dep_rule.field.clone(),
                        is_valid: false,
                        error_message: Some(validator.error_message.clone()),
                        warning_message: None,
                        suggestion: Some(format!("Adjust {} based on {} value", dep_rule.field, dep_rule.depends_on)),
                        severity: ValidationSeverity::Error,
                    });
                }
            }
        }
        
        None
    }
    
    /// Check dependency condition
    fn check_dependency_condition(&self, condition: &DependencyCondition, field_value: &serde_json::Value, dep_value: &serde_json::Value) -> bool {
        match condition {
            DependencyCondition::Equals(expected) => {
                dep_value.as_str().map_or(false, |s| s == expected)
            }
            DependencyCondition::NotEquals(expected) => {
                dep_value.as_str().map_or(true, |s| s != expected)
            }
            DependencyCondition::GreaterThan(threshold) => {
                dep_value.as_f64().map_or(false, |n| n > *threshold)
            }
            DependencyCondition::LessThan(threshold) => {
                dep_value.as_f64().map_or(false, |n| n < *threshold)
            }
            DependencyCondition::IsSet => {
                !dep_value.is_null()
            }
            DependencyCondition::IsEmpty => {
                dep_value.is_null() || (dep_value.is_string() && dep_value.as_str().map_or(false, |s| s.is_empty()))
            }
        }
    }
    
    /// Validate workflow requirements
    fn validate_workflow_requirements(&self, validator: &WorkflowValidator, inputs: &HashMap<String, serde_json::Value>) -> Vec<ValidationResult> {
        let mut results = Vec::new();
        
        for requirement in &validator.requirements {
            match requirement {
                ValidationRequirement::DataQuality => {
                    if let Some(data_file) = inputs.get("data_file") {
                        if let Some(path) = data_file.as_str() {
                            // Check file size (simplified validation)
                            if let Ok(metadata) = std::fs::metadata(path) {
                                if metadata.len() < 1000000 { // Less than 1MB
                                    results.push(ValidationResult {
                                        field_name: "data_file".to_string(),
                                        is_valid: false,
                                        error_message: Some("Data file seems too small for meaningful analysis".to_string()),
                                        warning_message: None,
                                        suggestion: Some("Use a larger dataset with more historical data".to_string()),
                                        severity: ValidationSeverity::Warning,
                                    });
                                }
                            }
                        }
                    }
                }
                ValidationRequirement::ParameterConsistency => {
                    // Check parameter consistency (simplified)
                    if let Some(strategy_type) = inputs.get("strategy_type") {
                        if strategy_type.as_str() == Some("mean_reversion") {
                            // Mean reversion strategies should have certain parameter constraints
                            if let Some(lookback) = inputs.get("lookback_period") {
                                if let Some(num) = lookback.as_f64() {
                                    if num < 5.0 || num > 100.0 {
                                        results.push(ValidationResult {
                                            field_name: "lookback_period".to_string(),
                                            is_valid: false,
                                            error_message: Some("Lookback period should be between 5-100 for mean reversion".to_string()),
                                            warning_message: None,
                                            suggestion: Some("Try values between 10-50 for better results".to_string()),
                                            severity: ValidationSeverity::Warning,
                                        });
                                    }
                                }
                            }
                        }
                    }
                }
                ValidationRequirement::SufficientData => {
                    // Check if there's sufficient data for backtesting
                    results.push(ValidationResult {
                        field_name: "data_sufficiency".to_string(),
                        is_valid: true,
                        error_message: None,
                        warning_message: None,
                        suggestion: Some("Ensure at least 30 days of data for reliable results".to_string()),
                        severity: ValidationSeverity::Info,
                    });
                }
                _ => {} // Handle other requirements
            }
        }
        
        results
    }
    
    /// Check if validator applies to step
    fn is_validator_applicable(&self, validator_fields: &[String], step: &WorkflowStep) -> bool {
        let step_input_names: std::collections::HashSet<_> = step.required_inputs.iter()
            .map(|input| &input.name)
            .collect();
        
        validator_fields.iter().any(|field| step_input_names.contains(field))
    }
    
    /// Initialize default validators
    fn initialize_default_validators(&mut self) {
        // Parameter optimization validators
        self.cross_field_validators.push(CrossFieldValidator {
            fields: vec!["optimization_method".to_string(), "max_iterations".to_string()],
            validation_logic: "grid_search_size_check".to_string(),
            dependency_rules: vec![
                DependencyRule {
                    field: "max_iterations".to_string(),
                    depends_on: "optimization_method".to_string(),
                    condition: DependencyCondition::Equals("grid_search".to_string()),
                }
            ],
            error_message: "Grid search with too many iterations will be very slow".to_string(),
        });
        
        // Walk-forward analysis validators
        self.workflow_validators.insert("walk-forward-setup".to_string(), WorkflowValidator {
            workflow_step: "walk-forward-setup".to_string(),
            validation_rules: vec![
                ValidationRule::Custom("positive_number".to_string()),
            ],
            requirements: vec![
                ValidationRequirement::SufficientData,
                ValidationRequirement::ParameterRanges,
            ],
        });
    }
    
    /// Validate in real-time (non-blocking)
    pub fn validate_real_time(&self, field_name: &str, value: &serde_json::Value, input_spec: &WorkflowInput) -> ValidationResult {
        self.validate_field(input_spec, Some(value))
    }
    
    /// Get validation summary for all inputs
    pub fn get_validation_summary(&self, step: &WorkflowStep, inputs: &HashMap<String, serde_json::Value>) -> ValidationSummary {
        let results = self.validate_step_inputs(step, inputs);
        
        let error_count = results.iter().filter(|r| !r.is_valid && r.severity == ValidationSeverity::Error).count();
        let warning_count = results.iter().filter(|r| r.severity == ValidationSeverity::Warning).count();
        let is_valid = error_count == 0;
        
        ValidationSummary {
            is_valid,
            error_count,
            warning_count,
            results,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationSummary {
    pub is_valid: bool,
    pub error_count: usize,
    pub warning_count: usize,
    pub results: Vec<ValidationResult>,
}

impl Default for ValidationEngine {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::workflow::{WorkflowInput, InputType};
    
    #[test]
    fn test_required_field_validation() {
        let engine = ValidationEngine::new();
        let input = WorkflowInput {
            name: "test_field".to_string(),
            input_type: InputType::String,
            required: true,
            validation_rules: vec![ValidationRule::Required],
            default_value: None,
            help_text: None,
        };
        
        let result = engine.validate_field(&input, None);
        assert!(!result.is_valid);
        assert!(result.error_message.is_some());
    }
    
    #[test]
    fn test_numeric_range_validation() {
        let engine = ValidationEngine::new();
        let input = WorkflowInput {
            name: "numeric_field".to_string(),
            input_type: InputType::Number,
            required: true,
            validation_rules: vec![ValidationRule::MinValue(0.0), ValidationRule::MaxValue(100.0)],
            default_value: None,
            help_text: None,
        };
        
        let valid_value = serde_json::Value::Number(serde_json::Number::from(50));
        let result = engine.validate_field(&input, Some(&valid_value));
        assert!(result.is_valid);
        
        let invalid_value = serde_json::Value::Number(serde_json::Number::from(150));
        let result = engine.validate_field(&input, Some(&invalid_value));
        assert!(!result.is_valid);
    }
    
    #[test]
    fn test_string_set_validation() {
        let engine = ValidationEngine::new();
        let input = WorkflowInput {
            name: "choice_field".to_string(),
            input_type: InputType::String,
            required: true,
            validation_rules: vec![ValidationRule::StringInSet(vec!["option1".to_string(), "option2".to_string()])],
            default_value: None,
            help_text: None,
        };
        
        let valid_value = serde_json::Value::String("option1".to_string());
        let result = engine.validate_field(&input, Some(&valid_value));
        assert!(result.is_valid);
        
        let invalid_value = serde_json::Value::String("option3".to_string());
        let result = engine.validate_field(&input, Some(&invalid_value));
        assert!(!result.is_valid);
    }
}