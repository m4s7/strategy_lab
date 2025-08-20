use redis::{aio::ConnectionManager, AsyncCommands, RedisResult};
use serde::{Deserialize, Serialize};
use std::time::Duration;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Job {
    pub id: String,
    pub job_type: JobType,
    pub payload: serde_json::Value,
    pub status: JobStatus,
    pub priority: i32,
    pub created_at: u64,
    pub started_at: Option<u64>,
    pub completed_at: Option<u64>,
    pub error: Option<String>,
    pub result: Option<serde_json::Value>,
    pub retry_count: u32,
    pub max_retries: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum JobType {
    Backtest,
    Optimization,
    DataIngestion,
    ReportGeneration,
    WalkForward,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum JobStatus {
    Pending,
    Running,
    Completed,
    Failed,
    Cancelled,
    Retrying,
}

pub struct JobQueue {
    redis_conn: ConnectionManager,
    queue_name: String,
}

impl JobQueue {
    pub async fn new(redis_url: &str, queue_name: &str) -> RedisResult<Self> {
        let client = redis::Client::open(redis_url)?;
        let redis_conn = ConnectionManager::new(client).await?;
        
        Ok(Self {
            redis_conn,
            queue_name: queue_name.to_string(),
        })
    }

    pub async fn enqueue(&mut self, job: Job) -> RedisResult<String> {
        let job_id = job.id.clone();
        let job_json = serde_json::to_string(&job).unwrap();
        
        // Store job details
        let job_key = format!("job:{}", job_id);
        self.redis_conn.set_ex(&job_key, &job_json, 86400).await?; // Expire after 24 hours
        
        // Add to priority queue
        let queue_key = format!("queue:{}", self.queue_name);
        self.redis_conn.zadd(&queue_key, &job_id, -job.priority).await?; // Negative for higher priority first
        
        // Publish job event
        let event = JobEvent {
            event_type: JobEventType::Enqueued,
            job_id: job_id.clone(),
            timestamp: chrono::Utc::now().timestamp_millis() as u64,
        };
        let event_json = serde_json::to_string(&event).unwrap();
        self.redis_conn.publish("job_events", event_json).await?;
        
        Ok(job_id)
    }

    pub async fn dequeue(&mut self) -> RedisResult<Option<Job>> {
        let queue_key = format!("queue:{}", self.queue_name);
        
        // Get highest priority job
        let job_ids: Vec<String> = self.redis_conn
            .zrange_limit(&queue_key, 0, 1)
            .await?;
        
        if job_ids.is_empty() {
            return Ok(None);
        }
        
        let job_id = &job_ids[0];
        
        // Remove from queue
        self.redis_conn.zrem(&queue_key, job_id).await?;
        
        // Get job details
        let job_key = format!("job:{}", job_id);
        let job_json: Option<String> = self.redis_conn.get(&job_key).await?;
        
        if let Some(json) = job_json {
            let mut job: Job = serde_json::from_str(&json).unwrap();
            job.status = JobStatus::Running;
            job.started_at = Some(chrono::Utc::now().timestamp_millis() as u64);
            
            // Update job status
            let updated_json = serde_json::to_string(&job).unwrap();
            self.redis_conn.set_ex(&job_key, &updated_json, 86400).await?;
            
            // Publish event
            let event = JobEvent {
                event_type: JobEventType::Started,
                job_id: job_id.clone(),
                timestamp: chrono::Utc::now().timestamp_millis() as u64,
            };
            let event_json = serde_json::to_string(&event).unwrap();
            self.redis_conn.publish("job_events", event_json).await?;
            
            Ok(Some(job))
        } else {
            Ok(None)
        }
    }

    pub async fn complete_job(&mut self, job_id: &str, result: serde_json::Value) -> RedisResult<()> {
        let job_key = format!("job:{}", job_id);
        let job_json: Option<String> = self.redis_conn.get(&job_key).await?;
        
        if let Some(json) = job_json {
            let mut job: Job = serde_json::from_str(&json).unwrap();
            job.status = JobStatus::Completed;
            job.completed_at = Some(chrono::Utc::now().timestamp_millis() as u64);
            job.result = Some(result);
            
            let updated_json = serde_json::to_string(&job).unwrap();
            self.redis_conn.set_ex(&job_key, &updated_json, 86400).await?;
            
            // Publish event
            let event = JobEvent {
                event_type: JobEventType::Completed,
                job_id: job_id.to_string(),
                timestamp: chrono::Utc::now().timestamp_millis() as u64,
            };
            let event_json = serde_json::to_string(&event).unwrap();
            self.redis_conn.publish("job_events", event_json).await?;
        }
        
        Ok(())
    }

    pub async fn fail_job(&mut self, job_id: &str, error: String) -> RedisResult<()> {
        let job_key = format!("job:{}", job_id);
        let job_json: Option<String> = self.redis_conn.get(&job_key).await?;
        
        if let Some(json) = job_json {
            let mut job: Job = serde_json::from_str(&json).unwrap();
            
            if job.retry_count < job.max_retries {
                // Retry the job
                job.retry_count += 1;
                job.status = JobStatus::Retrying;
                
                let updated_json = serde_json::to_string(&job).unwrap();
                self.redis_conn.set_ex(&job_key, &updated_json, 86400).await?;
                
                // Re-enqueue with lower priority
                let queue_key = format!("queue:{}", self.queue_name);
                self.redis_conn.zadd(&queue_key, &job_id, -(job.priority - 10)).await?;
                
                // Publish retry event
                let event = JobEvent {
                    event_type: JobEventType::Retrying,
                    job_id: job_id.to_string(),
                    timestamp: chrono::Utc::now().timestamp_millis() as u64,
                };
                let event_json = serde_json::to_string(&event).unwrap();
                self.redis_conn.publish("job_events", event_json).await?;
            } else {
                // Mark as failed
                job.status = JobStatus::Failed;
                job.completed_at = Some(chrono::Utc::now().timestamp_millis() as u64);
                job.error = Some(error);
                
                let updated_json = serde_json::to_string(&job).unwrap();
                self.redis_conn.set_ex(&job_key, &updated_json, 86400).await?;
                
                // Publish failure event
                let event = JobEvent {
                    event_type: JobEventType::Failed,
                    job_id: job_id.to_string(),
                    timestamp: chrono::Utc::now().timestamp_millis() as u64,
                };
                let event_json = serde_json::to_string(&event).unwrap();
                self.redis_conn.publish("job_events", event_json).await?;
            }
        }
        
        Ok(())
    }

    pub async fn get_job_status(&mut self, job_id: &str) -> RedisResult<Option<Job>> {
        let job_key = format!("job:{}", job_id);
        let job_json: Option<String> = self.redis_conn.get(&job_key).await?;
        
        if let Some(json) = job_json {
            let job: Job = serde_json::from_str(&json).unwrap();
            Ok(Some(job))
        } else {
            Ok(None)
        }
    }

    pub async fn get_queue_length(&mut self) -> RedisResult<u64> {
        let queue_key = format!("queue:{}", self.queue_name);
        self.redis_conn.zcard(&queue_key).await
    }

    pub async fn get_pending_jobs(&mut self, limit: isize) -> RedisResult<Vec<String>> {
        let queue_key = format!("queue:{}", self.queue_name);
        self.redis_conn.zrange_limit(&queue_key, 0, limit).await
    }

    pub async fn cancel_job(&mut self, job_id: &str) -> RedisResult<bool> {
        let job_key = format!("job:{}", job_id);
        let job_json: Option<String> = self.redis_conn.get(&job_key).await?;
        
        if let Some(json) = job_json {
            let mut job: Job = serde_json::from_str(&json).unwrap();
            
            if matches!(job.status, JobStatus::Pending | JobStatus::Running) {
                job.status = JobStatus::Cancelled;
                job.completed_at = Some(chrono::Utc::now().timestamp_millis() as u64);
                
                let updated_json = serde_json::to_string(&job).unwrap();
                self.redis_conn.set_ex(&job_key, &updated_json, 86400).await?;
                
                // Remove from queue if pending
                if matches!(job.status, JobStatus::Pending) {
                    let queue_key = format!("queue:{}", self.queue_name);
                    self.redis_conn.zrem(&queue_key, job_id).await?;
                }
                
                // Publish cancellation event
                let event = JobEvent {
                    event_type: JobEventType::Cancelled,
                    job_id: job_id.to_string(),
                    timestamp: chrono::Utc::now().timestamp_millis() as u64,
                };
                let event_json = serde_json::to_string(&event).unwrap();
                self.redis_conn.publish("job_events", event_json).await?;
                
                Ok(true)
            } else {
                Ok(false)
            }
        } else {
            Ok(false)
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JobEvent {
    pub event_type: JobEventType,
    pub job_id: String,
    pub timestamp: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum JobEventType {
    Enqueued,
    Started,
    Completed,
    Failed,
    Cancelled,
    Retrying,
}

pub struct JobWorker {
    queue: JobQueue,
    running: bool,
}

impl JobWorker {
    pub async fn new(redis_url: &str, queue_name: &str) -> RedisResult<Self> {
        let queue = JobQueue::new(redis_url, queue_name).await?;
        Ok(Self {
            queue,
            running: false,
        })
    }

    pub async fn start<F>(&mut self, processor: F) 
    where
        F: Fn(Job) -> Result<serde_json::Value, String> + Send + 'static,
    {
        self.running = true;
        
        while self.running {
            match self.queue.dequeue().await {
                Ok(Some(job)) => {
                    let job_id = job.id.clone();
                    
                    // Process job
                    match processor(job) {
                        Ok(result) => {
                            if let Err(e) = self.queue.complete_job(&job_id, result).await {
                                eprintln!("Failed to mark job as complete: {}", e);
                            }
                        }
                        Err(error) => {
                            if let Err(e) = self.queue.fail_job(&job_id, error).await {
                                eprintln!("Failed to mark job as failed: {}", e);
                            }
                        }
                    }
                }
                Ok(None) => {
                    // No jobs available, wait a bit
                    tokio::time::sleep(Duration::from_millis(100)).await;
                }
                Err(e) => {
                    eprintln!("Error dequeuing job: {}", e);
                    tokio::time::sleep(Duration::from_secs(1)).await;
                }
            }
        }
    }

    pub fn stop(&mut self) {
        self.running = false;
    }
}

impl Default for Job {
    fn default() -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            job_type: JobType::Backtest,
            payload: serde_json::Value::Null,
            status: JobStatus::Pending,
            priority: 50,
            created_at: chrono::Utc::now().timestamp_millis() as u64,
            started_at: None,
            completed_at: None,
            error: None,
            result: None,
            retry_count: 0,
            max_retries: 3,
        }
    }
}