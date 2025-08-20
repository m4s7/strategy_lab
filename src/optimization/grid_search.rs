//! Grid search optimization implementation

use crate::backtesting::{BacktestEngine, BacktestConfig, BacktestResult, PerformanceMetrics};
use crate::strategy::{Strategy, StrategyConfig};
use crate::strategy::config::ParameterValue;
use crate::optimization::{OptimizationResult, ParameterSet, ObjectiveFunction};
use rayon::prelude::*;
use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::Instant;
use tracing::{info, debug, warn};

/// Configuration for grid search optimization
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GridSearchConfig {
    /// Parameter ranges to search
    pub parameters: HashMap<String, ParameterRange>,
    
    /// Maximum combinations to evaluate
    pub max_combinations: Option<usize>,
    
    /// Early stopping configuration
    pub early_stopping: Option<EarlyStoppingConfig>,
    
    /// Number of parallel workers
    pub num_workers: usize,
    
    /// Objective function to optimize
    pub objective: ObjectiveFunction,
    
    /// Minimum trades required for valid result
    pub min_trades: u32,
}

/// Parameter range for grid search
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParameterRange {
    pub min: f64,
    pub max: f64,
    pub step: f64,
}

impl ParameterRange {
    /// Generate all values in range
    pub fn generate_values(&self) -> Vec<f64> {
        let mut values = Vec::new();
        let mut current = self.min;
        
        while current <= self.max {
            values.push(current);
            current += self.step;
        }
        
        values
    }
    
    /// Get number of steps
    pub fn num_steps(&self) -> usize {
        ((self.max - self.min) / self.step + 1.0) as usize
    }
}

/// Early stopping configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EarlyStoppingConfig {
    /// Stop if no improvement after N evaluations
    pub patience: usize,
    
    /// Minimum improvement required
    pub min_improvement: f64,
    
    /// Maximum drawdown allowed
    pub max_drawdown: Decimal,
}

/// Grid search optimizer
pub struct GridSearchOptimizer {
    config: GridSearchConfig,
    results: Arc<Mutex<Vec<OptimizationResult>>>,
    best_result: Arc<Mutex<Option<OptimizationResult>>>,
    evaluations: Arc<Mutex<usize>>,
    start_time: Instant,
}

impl GridSearchOptimizer {
    pub fn new(config: GridSearchConfig) -> Self {
        Self {
            config,
            results: Arc::new(Mutex::new(Vec::new())),
            best_result: Arc::new(Mutex::new(None)),
            evaluations: Arc::new(Mutex::new(0)),
            start_time: Instant::now(),
        }
    }
    
    /// Run grid search optimization
    pub async fn optimize<S, F>(
        &mut self,
        strategy_factory: F,
        backtest_config: BacktestConfig,
        data_path: &str,
    ) -> Result<Vec<OptimizationResult>, Box<dyn std::error::Error>>
    where
        S: Strategy + Send + 'static,
        F: Fn(ParameterSet) -> S + Send + Sync + 'static,
    {
        info!("Starting grid search optimization with {} parameters",
            self.config.parameters.len());
        
        // Generate all parameter combinations
        let combinations = self.generate_combinations();
        let total_combinations = combinations.len();
        
        info!("Generated {} parameter combinations", total_combinations);
        
        if let Some(max) = self.config.max_combinations {
            if total_combinations > max {
                warn!("Limiting to {} combinations (from {})", max, total_combinations);
            }
        }
        
        // Set up thread pool
        let pool = rayon::ThreadPoolBuilder::new()
            .num_threads(self.config.num_workers)
            .build()?;
        
        // Process combinations in parallel
        let results = Arc::clone(&self.results);
        let best_result = Arc::clone(&self.best_result);
        let evaluations = Arc::clone(&self.evaluations);
        let config = self.config.clone();
        
        pool.install(|| {
            combinations.par_iter()
                .take(config.max_combinations.unwrap_or(usize::MAX))
                .for_each(|params| {
                    // Check early stopping
                    if let Some(early_stop) = &config.early_stopping {
                        let evals = evaluations.lock().unwrap();
                        if *evals > early_stop.patience {
                            // Check if we should stop
                            let best = best_result.lock().unwrap();
                            if let Some(best_res) = &*best {
                                // Logic for early stopping would go here
                            }
                        }
                    }
                    
                    // Create strategy with parameters
                    let strategy = strategy_factory(params.clone());
                    
                    // Run backtest
                    let rt = tokio::runtime::Runtime::new().unwrap();
                    let result = rt.block_on(async {
                        let mut engine = BacktestEngine::new(backtest_config.clone());
                        let mut strategy = strategy;
                        engine.run_backtest(&mut strategy, data_path).await
                    });
                    
                    // Process result
                    if let Ok(backtest_result) = result {
                        if backtest_result.total_trades >= config.min_trades {
                            let opt_result = OptimizationResult {
                                parameters: params.clone(),
                                backtest_result: backtest_result.clone(),
                                objective_value: config.objective.calculate(&backtest_result),
                                timestamp: chrono::Utc::now(),
                                metrics: PerformanceMetrics::new(),
                                equity_curve: Vec::new(),
                                trade_analysis: None,
                                parameter_sensitivity: None,
                            };
                            
                            // Update results
                            let mut res = results.lock().unwrap();
                            res.push(opt_result.clone());
                            
                            // Update best result
                            let mut best = best_result.lock().unwrap();
                            if best.is_none() || opt_result.objective_value > best.as_ref().unwrap().objective_value {
                                *best = Some(opt_result);
                            }
                            
                            // Update evaluation count
                            let mut evals = evaluations.lock().unwrap();
                            *evals += 1;
                            
                            if *evals % 10 == 0 {
                                debug!("Evaluated {} / {} combinations", evals, total_combinations);
                            }
                        }
                    }
                });
        });
        
        let elapsed = self.start_time.elapsed();
        let final_results = self.results.lock().unwrap().clone();
        
        info!("Grid search completed: {} combinations in {:.2}s ({:.1} comb/sec)",
            final_results.len(),
            elapsed.as_secs_f64(),
            final_results.len() as f64 / elapsed.as_secs_f64()
        );
        
        Ok(final_results)
    }
    
    /// Generate all parameter combinations
    fn generate_combinations(&self) -> Vec<ParameterSet> {
        let mut combinations = vec![ParameterSet::new()];
        
        for (name, range) in &self.config.parameters {
            let values = range.generate_values();
            let mut new_combinations = Vec::new();
            
            for combo in &combinations {
                for value in &values {
                    let mut new_combo = combo.clone();
                    new_combo.parameters.insert(
                        name.clone(),
                        ParameterValue::Float(*value),
                    );
                    new_combinations.push(new_combo);
                }
            }
            
            combinations = new_combinations;
        }
        
        combinations
    }
    
    /// Get best result found so far
    pub fn get_best_result(&self) -> Option<OptimizationResult> {
        self.best_result.lock().unwrap().clone()
    }
    
    /// Get all results
    pub fn get_results(&self) -> Vec<OptimizationResult> {
        self.results.lock().unwrap().clone()
    }
    
    /// Get optimization progress
    pub fn get_progress(&self) -> OptimizationProgress {
        let evaluations = *self.evaluations.lock().unwrap();
        let elapsed = self.start_time.elapsed();
        
        OptimizationProgress {
            evaluations,
            elapsed_secs: elapsed.as_secs_f64(),
            evaluations_per_sec: evaluations as f64 / elapsed.as_secs_f64(),
            best_objective: self.best_result.lock().unwrap()
                .as_ref()
                .map(|r| r.objective_value),
        }
    }
}

/// Optimization progress tracking
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptimizationProgress {
    pub evaluations: usize,
    pub elapsed_secs: f64,
    pub evaluations_per_sec: f64,
    pub best_objective: Option<f64>,
}