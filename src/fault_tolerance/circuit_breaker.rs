//! Circuit Breaker Pattern Implementation

use std::sync::Arc;
use std::sync::atomic::{AtomicU32, AtomicU64, Ordering};
use std::time::{Duration, Instant};
use tokio::sync::RwLock;

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum CircuitState {
    Closed,
    Open,
    HalfOpen,
}

pub struct CircuitBreaker {
    state: Arc<RwLock<CircuitState>>,
    failure_count: Arc<AtomicU32>,
    success_count: Arc<AtomicU32>,
    last_failure_time: Arc<RwLock<Option<Instant>>>,
    failure_threshold: u32,
    success_threshold: u32,
    timeout: Duration,
    half_open_max_calls: u32,
    current_half_open_calls: Arc<AtomicU32>,
}

impl CircuitBreaker {
    pub fn new(
        failure_threshold: u32,
        success_threshold: u32,
        timeout: Duration,
        half_open_max_calls: u32,
    ) -> Self {
        Self {
            state: Arc::new(RwLock::new(CircuitState::Closed)),
            failure_count: Arc::new(AtomicU32::new(0)),
            success_count: Arc::new(AtomicU32::new(0)),
            last_failure_time: Arc::new(RwLock::new(None)),
            failure_threshold,
            success_threshold,
            timeout,
            half_open_max_calls,
            current_half_open_calls: Arc::new(AtomicU32::new(0)),
        }
    }

    pub async fn call<F, T, E>(&self, f: F) -> Result<T, E>
    where
        F: FnOnce() -> Result<T, E>,
        E: std::fmt::Debug,
    {
        let state = self.state.read().await;
        
        match *state {
            CircuitState::Open => {
                drop(state);
                self.try_transition_to_half_open().await;
                let state = self.state.read().await;
                if *state == CircuitState::Open {
                    return Err(Self::circuit_open_error());
                }
            }
            CircuitState::HalfOpen => {
                let calls = self.current_half_open_calls.fetch_add(1, Ordering::SeqCst);
                if calls >= self.half_open_max_calls {
                    self.current_half_open_calls.fetch_sub(1, Ordering::SeqCst);
                    return Err(Self::circuit_open_error());
                }
            }
            _ => {}
        }
        
        drop(state);
        
        match f() {
            Ok(result) => {
                self.on_success().await;
                Ok(result)
            }
            Err(error) => {
                self.on_failure().await;
                Err(error)
            }
        }
    }

    async fn on_success(&self) {
        let mut state = self.state.write().await;
        
        match *state {
            CircuitState::HalfOpen => {
                let success_count = self.success_count.fetch_add(1, Ordering::SeqCst) + 1;
                if success_count >= self.success_threshold {
                    *state = CircuitState::Closed;
                    self.failure_count.store(0, Ordering::SeqCst);
                    self.success_count.store(0, Ordering::SeqCst);
                    self.current_half_open_calls.store(0, Ordering::SeqCst);
                }
            }
            CircuitState::Closed => {
                self.failure_count.store(0, Ordering::SeqCst);
            }
            _ => {}
        }
    }

    async fn on_failure(&self) {
        let mut state = self.state.write().await;
        let failure_count = self.failure_count.fetch_add(1, Ordering::SeqCst) + 1;
        
        match *state {
            CircuitState::Closed => {
                if failure_count >= self.failure_threshold {
                    *state = CircuitState::Open;
                    let mut last_failure = self.last_failure_time.write().await;
                    *last_failure = Some(Instant::now());
                }
            }
            CircuitState::HalfOpen => {
                *state = CircuitState::Open;
                self.failure_count.store(0, Ordering::SeqCst);
                self.success_count.store(0, Ordering::SeqCst);
                self.current_half_open_calls.store(0, Ordering::SeqCst);
                let mut last_failure = self.last_failure_time.write().await;
                *last_failure = Some(Instant::now());
            }
            _ => {}
        }
    }

    async fn try_transition_to_half_open(&self) {
        let last_failure = self.last_failure_time.read().await;
        if let Some(failure_time) = *last_failure {
            if failure_time.elapsed() >= self.timeout {
                drop(last_failure);
                let mut state = self.state.write().await;
                if *state == CircuitState::Open {
                    *state = CircuitState::HalfOpen;
                    self.failure_count.store(0, Ordering::SeqCst);
                    self.success_count.store(0, Ordering::SeqCst);
                    self.current_half_open_calls.store(0, Ordering::SeqCst);
                }
            }
        }
    }

    fn circuit_open_error<E>() -> E
    where
        E: std::fmt::Debug,
    {
        panic!("Circuit breaker is open")
    }

    pub async fn get_state(&self) -> CircuitState {
        *self.state.read().await
    }

    pub fn get_failure_count(&self) -> u32 {
        self.failure_count.load(Ordering::SeqCst)
    }

    pub async fn reset(&self) {
        let mut state = self.state.write().await;
        *state = CircuitState::Closed;
        self.failure_count.store(0, Ordering::SeqCst);
        self.success_count.store(0, Ordering::SeqCst);
        self.current_half_open_calls.store(0, Ordering::SeqCst);
        let mut last_failure = self.last_failure_time.write().await;
        *last_failure = None;
    }
}