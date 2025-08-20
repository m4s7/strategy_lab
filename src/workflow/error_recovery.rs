//! Error recovery and guidance system

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorRecoverySystem {
    recovery_strategies: std::collections::HashMap<String, RecoveryStrategy>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowError {
    pub error_type: String,
    pub message: String,
    pub step_id: Option<String>,
    pub context: std::collections::HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RecoveryStrategy {
    pub error_type: String,
    pub severity: ErrorSeverity,
    pub recovery_steps: Vec<RecoveryStep>,
    pub automatic_recovery: bool,
    pub user_confirmation_required: bool,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum ErrorSeverity {
    Critical,
    Warning,
    Suggestion,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RecoveryStep {
    pub description: String,
    pub action: RecoveryAction,
    pub estimated_time: chrono::Duration,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RecoveryAction {
    UserAction(String),
    AutomaticFix(String),
    Rollback(String),
    Restart(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RecoveryGuidance {
    pub immediate_actions: Vec<String>,
    pub detailed_instructions: Vec<String>,
    pub alternative_approaches: Vec<String>,
    pub prevention_tips: Vec<String>,
}

impl ErrorRecoverySystem {
    pub fn new() -> Self {
        Self {
            recovery_strategies: std::collections::HashMap::new(),
        }
    }
    
    pub fn create_recovery_guidance(&self, error: &WorkflowError) -> RecoveryGuidance {
        RecoveryGuidance {
            immediate_actions: vec!["Check error details".to_string()],
            detailed_instructions: vec!["Review input parameters".to_string()],
            alternative_approaches: vec!["Try different approach".to_string()],
            prevention_tips: vec!["Validate inputs before proceeding".to_string()],
        }
    }
}

impl WorkflowError {
    pub fn new(error_type: String, message: String) -> Self {
        Self {
            error_type,
            message,
            step_id: None,
            context: std::collections::HashMap::new(),
        }
    }
    
    pub fn validation_failed(results: Vec<crate::workflow::validation::ValidationResult>) -> Self {
        Self {
            error_type: "ValidationFailed".to_string(),
            message: format!("Validation failed with {} errors", results.iter().filter(|r| !r.is_valid).count()),
            step_id: None,
            context: std::collections::HashMap::new(),
        }
    }
    
    pub fn workflow_not_found(workflow_id: String) -> Self {
        Self {
            error_type: "WorkflowNotFound".to_string(),
            message: format!("Workflow {} not found", workflow_id),
            step_id: None,
            context: std::collections::HashMap::new(),
        }
    }
    
    pub fn instance_not_found(instance_id: String) -> Self {
        Self {
            error_type: "InstanceNotFound".to_string(),
            message: format!("Workflow instance {} not found", instance_id),
            step_id: None,
            context: std::collections::HashMap::new(),
        }
    }
    
    pub fn step_not_complete(step_id: String) -> Self {
        Self {
            error_type: "StepNotComplete".to_string(),
            message: format!("Step {} is not complete", step_id),
            step_id: Some(step_id),
            context: std::collections::HashMap::new(),
        }
    }
    
    pub fn workflow_completed() -> Self {
        Self {
            error_type: "WorkflowCompleted".to_string(),
            message: "Workflow is already completed".to_string(),
            step_id: None,
            context: std::collections::HashMap::new(),
        }
    }
}

impl Default for ErrorRecoverySystem {
    fn default() -> Self {
        Self::new()
    }
}