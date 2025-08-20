//! Workflow progress tracking with save/resume functionality

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowProgress {
    pub completed_steps: usize,
    pub total_steps: usize,
    pub completion_percentage: f64,
    pub estimated_time_remaining: Option<chrono::Duration>,
    pub milestones: Vec<ProgressMilestone>,
    pub time_tracking: TimeTracking,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProgressMilestone {
    pub id: String,
    pub name: String,
    pub description: String,
    pub completed: bool,
    pub completed_at: Option<DateTime<Utc>>,
    pub celebration_shown: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TimeTracking {
    pub started_at: DateTime<Utc>,
    pub total_time_spent: chrono::Duration,
    pub time_per_step: Vec<chrono::Duration>,
    pub average_step_time: chrono::Duration,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SaveState {
    pub auto_save_enabled: bool,
    pub save_frequency: chrono::Duration,
    pub last_saved: Option<DateTime<Utc>>,
    pub save_count: u32,
    pub recovery_data: Option<serde_json::Value>,
}

impl WorkflowProgress {
    pub fn new() -> Self {
        Self {
            completed_steps: 0,
            total_steps: 0,
            completion_percentage: 0.0,
            estimated_time_remaining: None,
            milestones: Vec::new(),
            time_tracking: TimeTracking {
                started_at: Utc::now(),
                total_time_spent: chrono::Duration::zero(),
                time_per_step: Vec::new(),
                average_step_time: chrono::Duration::zero(),
            },
        }
    }
}

impl SaveState {
    pub fn new() -> Self {
        Self {
            auto_save_enabled: true,
            save_frequency: chrono::Duration::minutes(5),
            last_saved: None,
            save_count: 0,
            recovery_data: None,
        }
    }
}