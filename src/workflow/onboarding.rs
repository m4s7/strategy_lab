//! Interactive onboarding system

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OnboardingManager {
    sequences: std::collections::HashMap<String, OnboardingSequence>,
    user_progress: std::collections::HashMap<String, UserProgress>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OnboardingSequence {
    pub id: String,
    pub name: String,
    pub description: String,
    pub modules: Vec<OnboardingModule>,
    pub estimated_duration: chrono::Duration,
    pub prerequisites: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OnboardingModule {
    pub id: String,
    pub title: String,
    pub description: String,
    pub learning_objectives: Vec<String>,
    pub interactive_elements: Vec<InteractiveElement>,
    pub validation_checkpoints: Vec<ValidationCheckpoint>,
    pub estimated_duration: chrono::Duration,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InteractiveElement {
    pub element_type: InteractiveType,
    pub content: serde_json::Value,
    pub completion_criteria: CompletionCriteria,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum InteractiveType {
    GuidedTour,
    HandsOnExercise,
    DecisionSimulation,
    ConceptExplanation,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationCheckpoint {
    pub id: String,
    pub description: String,
    pub validation_type: ValidationType,
    pub passing_criteria: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ValidationType {
    QuizQuestion,
    PracticalExercise,
    ConceptCheck,
    SkillDemonstration,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CompletionCriteria {
    pub criteria_type: CriteriaType,
    pub target_value: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum CriteriaType {
    TimeSpent,
    InteractionCount,
    ScoreAchieved,
    TaskCompleted,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserProgress {
    pub user_id: String,
    pub sequence_id: String,
    pub current_module: usize,
    pub completed_modules: Vec<String>,
    pub started_at: DateTime<Utc>,
    pub last_activity: DateTime<Utc>,
    pub completion_percentage: f64,
}

impl OnboardingManager {
    pub fn new() -> Self {
        Self {
            sequences: std::collections::HashMap::new(),
            user_progress: std::collections::HashMap::new(),
        }
    }
    
    pub fn start_onboarding(&mut self, user_id: &str, sequence_id: &str) -> Result<(), String> {
        if !self.sequences.contains_key(sequence_id) {
            return Err(format!("Onboarding sequence {} not found", sequence_id));
        }
        
        let progress = UserProgress {
            user_id: user_id.to_string(),
            sequence_id: sequence_id.to_string(),
            current_module: 0,
            completed_modules: Vec::new(),
            started_at: Utc::now(),
            last_activity: Utc::now(),
            completion_percentage: 0.0,
        };
        
        self.user_progress.insert(user_id.to_string(), progress);
        Ok(())
    }
}

impl Default for OnboardingManager {
    fn default() -> Self {
        Self::new()
    }
}