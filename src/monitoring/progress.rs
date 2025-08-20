use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::time::{Duration, Instant};
use tokio::sync::{broadcast, RwLock};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProgressTracker {
    pub job_id: String,
    pub job_type: JobType,
    pub status: JobStatus,
    pub progress: Progress,
    pub metadata: JobMetadata,
    pub timestamps: JobTimestamps,
    pub resource_usage: ResourceUsage,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum JobType {
    Optimization,
    Backtesting,
    DataIngestion,
    WalkForward,
    ParameterSweep,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum JobStatus {
    Pending,
    Running,
    Paused,
    Completed,
    Failed,
    Cancelled,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Progress {
    pub current: usize,
    pub total: usize,
    pub percentage: f64,
    pub rate_per_second: f64,
    pub estimated_remaining_ms: u64,
    pub current_phase: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JobMetadata {
    pub strategy_name: String,
    pub parameter_count: usize,
    pub data_range: String,
    pub configuration: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JobTimestamps {
    pub created: u64,
    pub started: Option<u64>,
    pub last_update: u64,
    pub completed: Option<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResourceUsage {
    pub cpu_percent: f64,
    pub memory_mb: u64,
    pub active_threads: usize,
}

pub struct ProgressManager {
    trackers: RwLock<HashMap<String, ProgressTracker>>,
    update_sender: broadcast::Sender<ProgressUpdate>,
    _update_receiver: broadcast::Receiver<ProgressUpdate>,
}

#[derive(Debug, Clone)]
pub struct ProgressUpdate {
    pub job_id: String,
    pub update_type: ProgressUpdateType,
    pub timestamp: u64,
}

#[derive(Debug, Clone)]
pub enum ProgressUpdateType {
    StatusChanged(JobStatus),
    ProgressUpdated(Progress),
    PhaseChanged(String),
    ResourceUsageUpdated(ResourceUsage),
    JobCompleted,
    JobFailed(String),
}

impl ProgressManager {
    pub fn new() -> Self {
        let (update_sender, update_receiver) = broadcast::channel(1000);
        
        Self {
            trackers: RwLock::new(HashMap::new()),
            update_sender,
            _update_receiver: update_receiver,
        }
    }

    pub async fn create_job(
        &self,
        job_id: String,
        job_type: JobType,
        metadata: JobMetadata,
        total_items: usize,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let now = chrono::Utc::now().timestamp_millis() as u64;
        
        let tracker = ProgressTracker {
            job_id: job_id.clone(),
            job_type,
            status: JobStatus::Pending,
            progress: Progress {
                current: 0,
                total: total_items,
                percentage: 0.0,
                rate_per_second: 0.0,
                estimated_remaining_ms: 0,
                current_phase: "Initializing".to_string(),
            },
            metadata,
            timestamps: JobTimestamps {
                created: now,
                started: None,
                last_update: now,
                completed: None,
            },
            resource_usage: ResourceUsage {
                cpu_percent: 0.0,
                memory_mb: 0,
                active_threads: 0,
            },
        };

        {
            let mut trackers = self.trackers.write().await;
            trackers.insert(job_id.clone(), tracker);
        }

        self.send_update(job_id, ProgressUpdateType::StatusChanged(JobStatus::Pending)).await?;
        Ok(())
    }

    pub async fn start_job(&self, job_id: &str) -> Result<(), Box<dyn std::error::Error>> {
        let now = chrono::Utc::now().timestamp_millis() as u64;
        
        {
            let mut trackers = self.trackers.write().await;
            if let Some(tracker) = trackers.get_mut(job_id) {
                tracker.status = JobStatus::Running;
                tracker.timestamps.started = Some(now);
                tracker.timestamps.last_update = now;
                tracker.progress.current_phase = "Running".to_string();
            } else {
                return Err(format!("Job {} not found", job_id).into());
            }
        }

        self.send_update(job_id.to_string(), ProgressUpdateType::StatusChanged(JobStatus::Running)).await?;
        Ok(())
    }

    pub async fn update_progress(
        &self,
        job_id: &str,
        current: usize,
        phase: Option<String>,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let now = chrono::Utc::now().timestamp_millis() as u64;
        
        {
            let mut trackers = self.trackers.write().await;
            if let Some(tracker) = trackers.get_mut(job_id) {
                let previous_current = tracker.progress.current;
                let time_diff = now - tracker.timestamps.last_update;
                
                tracker.progress.current = current;
                tracker.progress.percentage = if tracker.progress.total > 0 {
                    (current as f64 / tracker.progress.total as f64) * 100.0
                } else {
                    0.0
                };
                
                // Calculate rate
                if time_diff > 0 {
                    let items_processed = current.saturating_sub(previous_current);
                    tracker.progress.rate_per_second = 
                        (items_processed as f64 * 1000.0) / time_diff as f64;
                }
                
                // Estimate remaining time
                let remaining_items = tracker.progress.total.saturating_sub(current);
                tracker.progress.estimated_remaining_ms = if tracker.progress.rate_per_second > 0.0 {
                    ((remaining_items as f64 / tracker.progress.rate_per_second) * 1000.0) as u64
                } else {
                    0
                };
                
                if let Some(phase) = phase {
                    tracker.progress.current_phase = phase;
                }
                
                tracker.timestamps.last_update = now;
            } else {
                return Err(format!("Job {} not found", job_id).into());
            }
        }

        let progress = {
            let trackers = self.trackers.read().await;
            trackers.get(job_id).map(|t| t.progress.clone())
        };

        if let Some(progress) = progress {
            self.send_update(job_id.to_string(), ProgressUpdateType::ProgressUpdated(progress)).await?;
        }

        Ok(())
    }

    pub async fn update_resource_usage(
        &self,
        job_id: &str,
        resource_usage: ResourceUsage,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let now = chrono::Utc::now().timestamp_millis() as u64;
        
        {
            let mut trackers = self.trackers.write().await;
            if let Some(tracker) = trackers.get_mut(job_id) {
                tracker.resource_usage = resource_usage.clone();
                tracker.timestamps.last_update = now;
            } else {
                return Err(format!("Job {} not found", job_id).into());
            }
        }

        self.send_update(job_id.to_string(), ProgressUpdateType::ResourceUsageUpdated(resource_usage)).await?;
        Ok(())
    }

    pub async fn complete_job(&self, job_id: &str) -> Result<(), Box<dyn std::error::Error>> {
        let now = chrono::Utc::now().timestamp_millis() as u64;
        
        {
            let mut trackers = self.trackers.write().await;
            if let Some(tracker) = trackers.get_mut(job_id) {
                tracker.status = JobStatus::Completed;
                tracker.progress.current = tracker.progress.total;
                tracker.progress.percentage = 100.0;
                tracker.progress.current_phase = "Completed".to_string();
                tracker.timestamps.completed = Some(now);
                tracker.timestamps.last_update = now;
            } else {
                return Err(format!("Job {} not found", job_id).into());
            }
        }

        self.send_update(job_id.to_string(), ProgressUpdateType::JobCompleted).await?;
        Ok(())
    }

    pub async fn fail_job(&self, job_id: &str, error: String) -> Result<(), Box<dyn std::error::Error>> {
        let now = chrono::Utc::now().timestamp_millis() as u64;
        
        {
            let mut trackers = self.trackers.write().await;
            if let Some(tracker) = trackers.get_mut(job_id) {
                tracker.status = JobStatus::Failed;
                tracker.progress.current_phase = format!("Failed: {}", error);
                tracker.timestamps.completed = Some(now);
                tracker.timestamps.last_update = now;
            } else {
                return Err(format!("Job {} not found", job_id).into());
            }
        }

        self.send_update(job_id.to_string(), ProgressUpdateType::JobFailed(error)).await?;
        Ok(())
    }

    pub async fn pause_job(&self, job_id: &str) -> Result<(), Box<dyn std::error::Error>> {
        {
            let mut trackers = self.trackers.write().await;
            if let Some(tracker) = trackers.get_mut(job_id) {
                tracker.status = JobStatus::Paused;
                tracker.progress.current_phase = "Paused".to_string();
            } else {
                return Err(format!("Job {} not found", job_id).into());
            }
        }

        self.send_update(job_id.to_string(), ProgressUpdateType::StatusChanged(JobStatus::Paused)).await?;
        Ok(())
    }

    pub async fn resume_job(&self, job_id: &str) -> Result<(), Box<dyn std::error::Error>> {
        {
            let mut trackers = self.trackers.write().await;
            if let Some(tracker) = trackers.get_mut(job_id) {
                tracker.status = JobStatus::Running;
                tracker.progress.current_phase = "Running".to_string();
            } else {
                return Err(format!("Job {} not found", job_id).into());
            }
        }

        self.send_update(job_id.to_string(), ProgressUpdateType::StatusChanged(JobStatus::Running)).await?;
        Ok(())
    }

    pub async fn cancel_job(&self, job_id: &str) -> Result<(), Box<dyn std::error::Error>> {
        let now = chrono::Utc::now().timestamp_millis() as u64;
        
        {
            let mut trackers = self.trackers.write().await;
            if let Some(tracker) = trackers.get_mut(job_id) {
                tracker.status = JobStatus::Cancelled;
                tracker.progress.current_phase = "Cancelled".to_string();
                tracker.timestamps.completed = Some(now);
            } else {
                return Err(format!("Job {} not found", job_id).into());
            }
        }

        self.send_update(job_id.to_string(), ProgressUpdateType::StatusChanged(JobStatus::Cancelled)).await?;
        Ok(())
    }

    pub async fn get_job_status(&self, job_id: &str) -> Option<ProgressTracker> {
        let trackers = self.trackers.read().await;
        trackers.get(job_id).cloned()
    }

    pub async fn get_all_jobs(&self) -> Vec<ProgressTracker> {
        let trackers = self.trackers.read().await;
        trackers.values().cloned().collect()
    }

    pub async fn get_active_jobs(&self) -> Vec<ProgressTracker> {
        let trackers = self.trackers.read().await;
        trackers
            .values()
            .filter(|t| matches!(t.status, JobStatus::Running | JobStatus::Paused))
            .cloned()
            .collect()
    }

    pub fn subscribe_to_updates(&self) -> broadcast::Receiver<ProgressUpdate> {
        self.update_sender.subscribe()
    }

    async fn send_update(
        &self,
        job_id: String,
        update_type: ProgressUpdateType,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let update = ProgressUpdate {
            job_id,
            update_type,
            timestamp: chrono::Utc::now().timestamp_millis() as u64,
        };

        // It's okay if there are no receivers
        let _ = self.update_sender.send(update);
        Ok(())
    }

    pub async fn cleanup_completed_jobs(&self, max_age_hours: u64) {
        let cutoff_time = chrono::Utc::now().timestamp_millis() as u64 - (max_age_hours * 3600 * 1000);
        
        let mut trackers = self.trackers.write().await;
        trackers.retain(|_, tracker| {
            match tracker.status {
                JobStatus::Completed | JobStatus::Failed | JobStatus::Cancelled => {
                    tracker.timestamps.completed.map_or(true, |completed| completed > cutoff_time)
                }
                _ => true,
            }
        });
    }
}

impl Default for ProgressManager {
    fn default() -> Self {
        Self::new()
    }
}