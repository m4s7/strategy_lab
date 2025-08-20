//! Guided workflow system for strategy development

use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use chrono::{DateTime, Utc, Duration};
use uuid::Uuid;

pub mod onboarding;
pub mod validation;
pub mod help_system;
pub mod progress;
pub mod error_recovery;
pub mod templates;

pub use onboarding::*;
pub use validation::*;
pub use help_system::*;
pub use progress::*;
pub use error_recovery::*;
pub use templates::*;

/// Workflow step definition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowStep {
    pub id: String,
    pub name: String,
    pub description: String,
    pub step_type: WorkflowStepType,
    pub required_inputs: Vec<WorkflowInput>,
    pub validation_requirements: Vec<ValidationRequirement>,
    pub estimated_duration: Duration,
    pub dependencies: Vec<String>,
    pub optional: bool,
    pub help_content: Option<HelpContent>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum WorkflowStepType {
    DataIngestion,
    StrategyConfiguration,
    ParameterOptimization,
    Backtesting,
    StatisticalValidation,
    ResultsAnalysis,
    DeploymentPrep,
    Custom(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowInput {
    pub name: String,
    pub input_type: InputType,
    pub required: bool,
    pub validation_rules: Vec<ValidationRule>,
    pub default_value: Option<serde_json::Value>,
    pub help_text: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum InputType {
    String,
    Number,
    Boolean,
    Array,
    Object,
    File,
    DateRange,
    ParameterSet,
}

/// Complete workflow definition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Workflow {
    pub id: String,
    pub name: String,
    pub description: String,
    pub category: WorkflowCategory,
    pub steps: Vec<WorkflowStep>,
    pub metadata: WorkflowMetadata,
    pub templates: Vec<StepTemplate>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum WorkflowCategory {
    BasicStrategyDevelopment,
    ParameterOptimization,
    StrategyValidation,
    PerformanceAnalysis,
    LiveDeploymentPrep,
    Custom(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowMetadata {
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub version: String,
    pub author: String,
    pub difficulty_level: DifficultyLevel,
    pub estimated_total_duration: Duration,
    pub prerequisites: Vec<String>,
    pub learning_objectives: Vec<String>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum DifficultyLevel {
    Beginner,
    Intermediate,
    Advanced,
    Expert,
}

/// Workflow execution instance
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowInstance {
    pub instance_id: String,
    pub workflow_id: String,
    pub user_id: String,
    pub status: WorkflowStatus,
    pub current_step: usize,
    pub step_states: Vec<StepState>,
    pub progress: WorkflowProgress,
    pub save_state: SaveState,
    pub started_at: DateTime<Utc>,
    pub last_updated: DateTime<Utc>,
    pub completed_at: Option<DateTime<Utc>>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum WorkflowStatus {
    NotStarted,
    InProgress,
    Paused,
    Completed,
    Failed,
    Abandoned,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StepState {
    pub step_id: String,
    pub status: StepStatus,
    pub inputs: HashMap<String, serde_json::Value>,
    pub outputs: HashMap<String, serde_json::Value>,
    pub validation_results: Vec<ValidationResult>,
    pub started_at: Option<DateTime<Utc>>,
    pub completed_at: Option<DateTime<Utc>>,
    pub error: Option<WorkflowError>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum StepStatus {
    Pending,
    InProgress,
    Completed,
    Failed,
    Skipped,
}

/// Main workflow engine
pub struct GuidedWorkflowEngine {
    workflows: HashMap<String, Workflow>,
    active_instances: HashMap<String, WorkflowInstance>,
    validation_engine: ValidationEngine,
    help_system: HelpSystem,
    onboarding_manager: OnboardingManager,
    error_recovery: ErrorRecoverySystem,
}

impl GuidedWorkflowEngine {
    pub fn new() -> Self {
        let mut engine = Self {
            workflows: HashMap::new(),
            active_instances: HashMap::new(),
            validation_engine: ValidationEngine::new(),
            help_system: HelpSystem::new(),
            onboarding_manager: OnboardingManager::new(),
            error_recovery: ErrorRecoverySystem::new(),
        };
        
        // Load default workflow templates
        engine.load_default_workflows();
        
        engine
    }
    
    /// Start a new workflow instance
    pub fn start_workflow(&mut self, workflow_id: &str, user_id: &str) -> Result<String, WorkflowError> {
        let workflow = self.workflows.get(workflow_id)
            .ok_or_else(|| WorkflowError::WorkflowNotFound(workflow_id.to_string()))?;
        
        let instance_id = Uuid::new_v4().to_string();
        let step_states = workflow.steps.iter()
            .map(|step| StepState {
                step_id: step.id.clone(),
                status: if step.dependencies.is_empty() { StepStatus::Pending } else { StepStatus::Pending },
                inputs: HashMap::new(),
                outputs: HashMap::new(),
                validation_results: Vec::new(),
                started_at: None,
                completed_at: None,
                error: None,
            })
            .collect();
        
        let instance = WorkflowInstance {
            instance_id: instance_id.clone(),
            workflow_id: workflow_id.to_string(),
            user_id: user_id.to_string(),
            status: WorkflowStatus::InProgress,
            current_step: 0,
            step_states,
            progress: WorkflowProgress::new(),
            save_state: SaveState::new(),
            started_at: Utc::now(),
            last_updated: Utc::now(),
            completed_at: None,
        };
        
        self.active_instances.insert(instance_id.clone(), instance);
        Ok(instance_id)
    }
    
    /// Get workflow instance
    pub fn get_instance(&self, instance_id: &str) -> Option<&WorkflowInstance> {
        self.active_instances.get(instance_id)
    }
    
    /// Get workflow instance mutably
    pub fn get_instance_mut(&mut self, instance_id: &str) -> Option<&mut WorkflowInstance> {
        self.active_instances.get_mut(instance_id)
    }
    
    /// Advance to next step in workflow
    pub fn advance_step(&mut self, instance_id: &str) -> Result<(), WorkflowError> {
        let instance = self.get_instance_mut(instance_id)
            .ok_or_else(|| WorkflowError::InstanceNotFound(instance_id.to_string()))?;
        
        let workflow = self.workflows.get(&instance.workflow_id)
            .ok_or_else(|| WorkflowError::WorkflowNotFound(instance.workflow_id.clone()))?;
        
        // Validate current step is complete
        if instance.current_step < instance.step_states.len() {
            let current_state = &instance.step_states[instance.current_step];
            if current_state.status != StepStatus::Completed {
                return Err(WorkflowError::StepNotComplete(current_state.step_id.clone()));
            }
        }
        
        // Find next available step
        let next_step_index = self.find_next_available_step(instance, workflow)?;
        
        if next_step_index >= workflow.steps.len() {
            // Workflow is complete
            instance.status = WorkflowStatus::Completed;
            instance.completed_at = Some(Utc::now());
        } else {
            instance.current_step = next_step_index;
            instance.step_states[next_step_index].status = StepStatus::InProgress;
            instance.step_states[next_step_index].started_at = Some(Utc::now());
        }
        
        instance.last_updated = Utc::now();
        self.save_instance(instance_id)?;
        
        Ok(())
    }
    
    /// Set inputs for current step
    pub fn set_step_inputs(&mut self, instance_id: &str, inputs: HashMap<String, serde_json::Value>) -> Result<(), WorkflowError> {
        let instance = self.get_instance_mut(instance_id)
            .ok_or_else(|| WorkflowError::InstanceNotFound(instance_id.to_string()))?;
        
        let workflow = self.workflows.get(&instance.workflow_id)
            .ok_or_else(|| WorkflowError::WorkflowNotFound(instance.workflow_id.clone()))?;
        
        if instance.current_step >= workflow.steps.len() {
            return Err(WorkflowError::WorkflowCompleted);
        }
        
        let current_step = &workflow.steps[instance.current_step];
        
        // Validate inputs
        let validation_results = self.validation_engine.validate_step_inputs(current_step, &inputs);
        let has_errors = validation_results.iter().any(|r| !r.is_valid);
        
        if has_errors {
            return Err(WorkflowError::ValidationFailed(validation_results));
        }
        
        // Set inputs
        instance.step_states[instance.current_step].inputs = inputs;
        instance.step_states[instance.current_step].validation_results = validation_results;
        instance.last_updated = Utc::now();
        
        self.save_instance(instance_id)?;
        Ok(())
    }
    
    /// Complete current step
    pub fn complete_step(&mut self, instance_id: &str, outputs: HashMap<String, serde_json::Value>) -> Result<(), WorkflowError> {
        let instance = self.get_instance_mut(instance_id)
            .ok_or_else(|| WorkflowError::InstanceNotFound(instance_id.to_string()))?;
        
        if instance.current_step >= instance.step_states.len() {
            return Err(WorkflowError::WorkflowCompleted);
        }
        
        // Set outputs and mark as completed
        let step_state = &mut instance.step_states[instance.current_step];
        step_state.outputs = outputs;
        step_state.status = StepStatus::Completed;
        step_state.completed_at = Some(Utc::now());
        
        // Update progress
        let completed_steps = instance.step_states.iter()
            .filter(|s| s.status == StepStatus::Completed)
            .count();
        instance.progress.completed_steps = completed_steps;
        instance.progress.completion_percentage = (completed_steps as f64 / instance.step_states.len() as f64) * 100.0;
        
        instance.last_updated = Utc::now();
        self.save_instance(instance_id)?;
        
        Ok(())
    }
    
    /// Get contextual help for current step
    pub fn get_contextual_help(&self, instance_id: &str, context: &HelpContext) -> Option<HelpContent> {
        let instance = self.get_instance(instance_id)?;
        let workflow = self.workflows.get(&instance.workflow_id)?;
        
        if instance.current_step >= workflow.steps.len() {
            return None;
        }
        
        let current_step = &workflow.steps[instance.current_step];
        self.help_system.get_contextual_help(current_step, context)
    }
    
    /// Get best practice recommendations
    pub fn get_recommendations(&self, instance_id: &str, decision_point: &DecisionPoint) -> Vec<Recommendation> {
        if let Some(instance) = self.get_instance(instance_id) {
            if let Some(workflow) = self.workflows.get(&instance.workflow_id) {
                if instance.current_step < workflow.steps.len() {
                    let current_step = &workflow.steps[instance.current_step];
                    return self.help_system.get_recommendations(current_step, decision_point);
                }
            }
        }
        Vec::new()
    }
    
    /// Handle workflow error with recovery guidance
    pub fn handle_error(&mut self, instance_id: &str, error: WorkflowError) -> RecoveryGuidance {
        if let Some(instance) = self.get_instance_mut(instance_id) {
            if instance.current_step < instance.step_states.len() {
                instance.step_states[instance.current_step].status = StepStatus::Failed;
                instance.step_states[instance.current_step].error = Some(error.clone());
            }
        }
        
        self.error_recovery.create_recovery_guidance(&error)
    }
    
    /// Save workflow instance
    fn save_instance(&mut self, instance_id: &str) -> Result<(), WorkflowError> {
        if let Some(instance) = self.get_instance_mut(instance_id) {
            instance.save_state.last_saved = Some(Utc::now());
            instance.save_state.save_count += 1;
            
            // In a real implementation, this would persist to database
            // For now, we just update the in-memory state
        }
        Ok(())
    }
    
    /// Find next available step considering dependencies
    fn find_next_available_step(&self, instance: &WorkflowInstance, workflow: &Workflow) -> Result<usize, WorkflowError> {
        for (index, step) in workflow.steps.iter().enumerate().skip(instance.current_step + 1) {
            if self.are_dependencies_satisfied(step, instance) {
                return Ok(index);
            }
        }
        
        // No more steps available
        Ok(workflow.steps.len())
    }
    
    /// Check if step dependencies are satisfied
    fn are_dependencies_satisfied(&self, step: &WorkflowStep, instance: &WorkflowInstance) -> bool {
        for dep_id in &step.dependencies {
            let dep_satisfied = instance.step_states.iter()
                .any(|state| state.step_id == *dep_id && state.status == StepStatus::Completed);
            
            if !dep_satisfied {
                return false;
            }
        }
        true
    }
    
    /// Load default workflow templates
    fn load_default_workflows(&mut self) {
        // Basic Strategy Development Workflow
        let basic_workflow = create_basic_strategy_workflow();
        self.workflows.insert(basic_workflow.id.clone(), basic_workflow);
        
        // Parameter Optimization Workflow
        let optimization_workflow = create_optimization_workflow();
        self.workflows.insert(optimization_workflow.id.clone(), optimization_workflow);
        
        // Strategy Validation Workflow
        let validation_workflow = create_validation_workflow();
        self.workflows.insert(validation_workflow.id.clone(), validation_workflow);
    }
    
    /// Get available workflows
    pub fn get_workflows(&self) -> Vec<&Workflow> {
        self.workflows.values().collect()
    }
    
    /// Get workflows by category
    pub fn get_workflows_by_category(&self, category: WorkflowCategory) -> Vec<&Workflow> {
        self.workflows.values()
            .filter(|w| std::mem::discriminant(&w.category) == std::mem::discriminant(&category))
            .collect()
    }
    
    /// Resume paused workflow
    pub fn resume_workflow(&mut self, instance_id: &str) -> Result<(), WorkflowError> {
        if let Some(instance) = self.get_instance_mut(instance_id) {
            if instance.status == WorkflowStatus::Paused {
                instance.status = WorkflowStatus::InProgress;
                instance.last_updated = Utc::now();
                self.save_instance(instance_id)?;
            }
        }
        Ok(())
    }
    
    /// Pause workflow
    pub fn pause_workflow(&mut self, instance_id: &str) -> Result<(), WorkflowError> {
        if let Some(instance) = self.get_instance_mut(instance_id) {
            if instance.status == WorkflowStatus::InProgress {
                instance.status = WorkflowStatus::Paused;
                instance.last_updated = Utc::now();
                self.save_instance(instance_id)?;
            }
        }
        Ok(())
    }
}

impl Default for GuidedWorkflowEngine {
    fn default() -> Self {
        Self::new()
    }
}

/// Create basic strategy development workflow
fn create_basic_strategy_workflow() -> Workflow {
    Workflow {
        id: "basic-strategy-development".to_string(),
        name: "Basic Strategy Development".to_string(),
        description: "Complete end-to-end workflow for developing a new trading strategy".to_string(),
        category: WorkflowCategory::BasicStrategyDevelopment,
        steps: vec![
            WorkflowStep {
                id: "data-ingestion".to_string(),
                name: "Data Ingestion".to_string(),
                description: "Load and validate historical market data".to_string(),
                step_type: WorkflowStepType::DataIngestion,
                required_inputs: vec![
                    WorkflowInput {
                        name: "data_file".to_string(),
                        input_type: InputType::File,
                        required: true,
                        validation_rules: vec![ValidationRule::FileExists, ValidationRule::FileFormat("parquet".to_string())],
                        default_value: None,
                        help_text: Some("Select Parquet file containing historical tick data".to_string()),
                    }
                ],
                validation_requirements: vec![ValidationRequirement::DataQuality],
                estimated_duration: Duration::minutes(5),
                dependencies: vec![],
                optional: false,
                help_content: None,
            },
            WorkflowStep {
                id: "strategy-config".to_string(),
                name: "Strategy Configuration".to_string(),
                description: "Configure strategy parameters and rules".to_string(),
                step_type: WorkflowStepType::StrategyConfiguration,
                required_inputs: vec![
                    WorkflowInput {
                        name: "strategy_type".to_string(),
                        input_type: InputType::String,
                        required: true,
                        validation_rules: vec![ValidationRule::StringInSet(vec!["mean_reversion".to_string(), "momentum".to_string(), "arbitrage".to_string()])],
                        default_value: Some(serde_json::Value::String("mean_reversion".to_string())),
                        help_text: Some("Choose the type of trading strategy to implement".to_string()),
                    }
                ],
                validation_requirements: vec![ValidationRequirement::ParameterConsistency],
                estimated_duration: Duration::minutes(15),
                dependencies: vec!["data-ingestion".to_string()],
                optional: false,
                help_content: None,
            },
            WorkflowStep {
                id: "backtesting".to_string(),
                name: "Strategy Backtesting".to_string(),
                description: "Run backtest on historical data".to_string(),
                step_type: WorkflowStepType::Backtesting,
                required_inputs: vec![],
                validation_requirements: vec![ValidationRequirement::SufficientData],
                estimated_duration: Duration::minutes(10),
                dependencies: vec!["strategy-config".to_string()],
                optional: false,
                help_content: None,
            }
        ],
        metadata: WorkflowMetadata {
            created_at: Utc::now(),
            updated_at: Utc::now(),
            version: "1.0.0".to_string(),
            author: "Strategy Lab".to_string(),
            difficulty_level: DifficultyLevel::Beginner,
            estimated_total_duration: Duration::minutes(30),
            prerequisites: vec!["Basic understanding of trading concepts".to_string()],
            learning_objectives: vec![
                "Learn to load and validate market data".to_string(),
                "Configure basic trading strategy parameters".to_string(),
                "Run and interpret backtest results".to_string(),
            ],
        },
        templates: vec![],
    }
}

/// Create optimization workflow
fn create_optimization_workflow() -> Workflow {
    Workflow {
        id: "parameter-optimization".to_string(),
        name: "Parameter Optimization".to_string(),
        description: "Systematic optimization of strategy parameters".to_string(),
        category: WorkflowCategory::ParameterOptimization,
        steps: vec![
            WorkflowStep {
                id: "optimization-setup".to_string(),
                name: "Optimization Setup".to_string(),
                description: "Configure optimization parameters and constraints".to_string(),
                step_type: WorkflowStepType::ParameterOptimization,
                required_inputs: vec![
                    WorkflowInput {
                        name: "optimization_method".to_string(),
                        input_type: InputType::String,
                        required: true,
                        validation_rules: vec![ValidationRule::StringInSet(vec!["grid_search".to_string(), "genetic".to_string(), "bayesian".to_string()])],
                        default_value: Some(serde_json::Value::String("grid_search".to_string())),
                        help_text: Some("Choose optimization algorithm".to_string()),
                    }
                ],
                validation_requirements: vec![ValidationRequirement::ParameterRanges],
                estimated_duration: Duration::minutes(20),
                dependencies: vec![],
                optional: false,
                help_content: None,
            }
        ],
        metadata: WorkflowMetadata {
            created_at: Utc::now(),
            updated_at: Utc::now(),
            version: "1.0.0".to_string(),
            author: "Strategy Lab".to_string(),
            difficulty_level: DifficultyLevel::Intermediate,
            estimated_total_duration: Duration::hours(2),
            prerequisites: vec!["Completed basic strategy development".to_string()],
            learning_objectives: vec!["Master parameter optimization techniques".to_string()],
        },
        templates: vec![],
    }
}

/// Create validation workflow
fn create_validation_workflow() -> Workflow {
    Workflow {
        id: "strategy-validation".to_string(),
        name: "Strategy Validation".to_string(),
        description: "Comprehensive validation of strategy robustness".to_string(),
        category: WorkflowCategory::StrategyValidation,
        steps: vec![
            WorkflowStep {
                id: "statistical-validation".to_string(),
                name: "Statistical Validation".to_string(),
                description: "Perform statistical tests on results".to_string(),
                step_type: WorkflowStepType::StatisticalValidation,
                required_inputs: vec![],
                validation_requirements: vec![ValidationRequirement::SignificanceLevel],
                estimated_duration: Duration::minutes(15),
                dependencies: vec![],
                optional: false,
                help_content: None,
            }
        ],
        metadata: WorkflowMetadata {
            created_at: Utc::now(),
            updated_at: Utc::now(),
            version: "1.0.0".to_string(),
            author: "Strategy Lab".to_string(),
            difficulty_level: DifficultyLevel::Advanced,
            estimated_total_duration: Duration::hours(1),
            prerequisites: vec!["Strategy optimization completed".to_string()],
            learning_objectives: vec!["Validate strategy statistical significance".to_string()],
        },
        templates: vec![],
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_workflow_creation() {
        let mut engine = GuidedWorkflowEngine::new();
        let workflows = engine.get_workflows();
        assert!(!workflows.is_empty());
    }
    
    #[test]
    fn test_workflow_instance_lifecycle() {
        let mut engine = GuidedWorkflowEngine::new();
        let instance_id = engine.start_workflow("basic-strategy-development", "test-user").unwrap();
        
        let instance = engine.get_instance(&instance_id).unwrap();
        assert_eq!(instance.status, WorkflowStatus::InProgress);
        assert_eq!(instance.current_step, 0);
    }
}