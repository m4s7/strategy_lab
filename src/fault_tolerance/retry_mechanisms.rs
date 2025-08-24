//! Retry Mechanisms with Various Strategies

use std::time::Duration;
use tokio::time::sleep;

#[derive(Debug, Clone)]
pub struct RetryConfig {
    pub max_attempts: u32,
    pub initial_delay: Duration,
    pub max_delay: Duration,
    pub multiplier: f64,
    pub jitter: bool,
}

impl Default for RetryConfig {
    fn default() -> Self {
        Self {
            max_attempts: 3,
            initial_delay: Duration::from_millis(100),
            max_delay: Duration::from_secs(30),
            multiplier: 2.0,
            jitter: true,
        }
    }
}

#[derive(Debug, Clone)]
pub enum RetryPolicy {
    Fixed(Duration),
    Linear(Duration),
    Exponential(ExponentialBackoff),
    Custom(Box<dyn Fn(u32) -> Duration + Send + Sync>),
}

#[derive(Debug, Clone)]
pub struct ExponentialBackoff {
    pub initial_delay: Duration,
    pub max_delay: Duration,
    pub multiplier: f64,
    pub jitter: bool,
}

impl ExponentialBackoff {
    pub fn new(initial_delay: Duration, max_delay: Duration, multiplier: f64) -> Self {
        Self {
            initial_delay,
            max_delay,
            multiplier,
            jitter: true,
        }
    }

    pub fn calculate_delay(&self, attempt: u32) -> Duration {
        let mut delay = self.initial_delay.as_millis() as f64 * self.multiplier.powi(attempt as i32);
        
        if delay > self.max_delay.as_millis() as f64 {
            delay = self.max_delay.as_millis() as f64;
        }
        
        if self.jitter {
            delay *= 1.0 + (rand::random::<f64>() - 0.5) * 0.1;
        }
        
        Duration::from_millis(delay as u64)
    }
}

pub struct RetryExecutor {
    config: RetryConfig,
    policy: RetryPolicy,
}

impl RetryExecutor {
    pub fn new(config: RetryConfig, policy: RetryPolicy) -> Self {
        Self { config, policy }
    }

    pub async fn execute<F, Fut, T, E>(&self, mut f: F) -> Result<T, E>
    where
        F: FnMut() -> Fut,
        Fut: std::future::Future<Output = Result<T, E>>,
        E: std::fmt::Debug,
    {
        let mut attempts = 0;
        let mut last_error = None;

        while attempts < self.config.max_attempts {
            match f().await {
                Ok(result) => return Ok(result),
                Err(error) => {
                    attempts += 1;
                    last_error = Some(error);

                    if attempts < self.config.max_attempts {
                        let delay = self.calculate_delay(attempts);
                        sleep(delay).await;
                    }
                }
            }
        }

        Err(last_error.unwrap())
    }

    fn calculate_delay(&self, attempt: u32) -> Duration {
        match &self.policy {
            RetryPolicy::Fixed(duration) => *duration,
            RetryPolicy::Linear(base) => {
                let delay = base.as_millis() as u64 * attempt as u64;
                Duration::from_millis(delay.min(self.config.max_delay.as_millis() as u64))
            }
            RetryPolicy::Exponential(backoff) => backoff.calculate_delay(attempt),
            RetryPolicy::Custom(f) => f(attempt),
        }
    }

    pub async fn execute_with_condition<F, Fut, T, E, C>(&self, mut f: F, condition: C) -> Result<T, E>
    where
        F: FnMut() -> Fut,
        Fut: std::future::Future<Output = Result<T, E>>,
        E: std::fmt::Debug,
        C: Fn(&E) -> bool,
    {
        let mut attempts = 0;
        let mut last_error = None;

        while attempts < self.config.max_attempts {
            match f().await {
                Ok(result) => return Ok(result),
                Err(error) => {
                    if !condition(&error) {
                        return Err(error);
                    }

                    attempts += 1;
                    last_error = Some(error);

                    if attempts < self.config.max_attempts {
                        let delay = self.calculate_delay(attempts);
                        sleep(delay).await;
                    }
                }
            }
        }

        Err(last_error.unwrap())
    }
}

// Utility function for simple retry with exponential backoff
pub async fn retry_with_exponential_backoff<F, Fut, T, E>(
    f: F,
    max_attempts: u32,
    initial_delay: Duration,
) -> Result<T, E>
where
    F: FnMut() -> Fut,
    Fut: std::future::Future<Output = Result<T, E>>,
    E: std::fmt::Debug,
{
    let config = RetryConfig {
        max_attempts,
        initial_delay,
        max_delay: Duration::from_secs(60),
        multiplier: 2.0,
        jitter: true,
    };

    let backoff = ExponentialBackoff::new(initial_delay, Duration::from_secs(60), 2.0);
    let executor = RetryExecutor::new(config, RetryPolicy::Exponential(backoff));
    
    executor.execute(f).await
}

// Add rand dependency usage
use rand::Rng as _;