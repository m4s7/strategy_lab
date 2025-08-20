use crate::optimization::{OptimizationResult, ParameterSet};
use crate::strategy::config::OptimizationConfig;
use crate::strategy::traits::Strategy;
use crate::backtesting::{BacktestResult, PerformanceMetrics};
use rayon::prelude::*;
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use tokio::sync::mpsc;

pub struct ParallelOptimizer {
    max_threads: usize,
    progress_sender: Option<mpsc::UnboundedSender<ProgressUpdate>>,
}

#[derive(Debug, Clone)]
pub struct ProgressUpdate {
    pub completed: usize,
    pub total: usize,
    pub current_parameters: HashMap<String, f64>,
    pub current_result: Option<OptimizationResult>,
}

#[derive(Debug, Clone)]
pub struct ParameterCombination {
    pub id: usize,
    pub parameters: HashMap<String, f64>,
}

impl ParallelOptimizer {
    pub fn new(max_threads: usize) -> Self {
        Self {
            max_threads,
            progress_sender: None,
        }
    }

    pub fn with_progress_reporting(mut self, sender: mpsc::UnboundedSender<ProgressUpdate>) -> Self {
        self.progress_sender = Some(sender);
        self
    }

    pub fn generate_parameter_combinations(
        &self,
        parameter_ranges: &HashMap<String, (f64, f64, f64)>, // (min, max, step)
    ) -> Vec<ParameterCombination> {
        let mut combinations = Vec::new();
        let mut parameter_names: Vec<_> = parameter_ranges.keys().collect();
        parameter_names.sort(); // Ensure consistent ordering

        self.generate_combinations_recursive(
            &parameter_names,
            parameter_ranges,
            0,
            HashMap::new(),
            &mut combinations,
        );

        combinations
    }

    fn generate_combinations_recursive(
        &self,
        parameter_names: &[&String],
        parameter_ranges: &HashMap<String, (f64, f64, f64)>,
        depth: usize,
        current_params: HashMap<String, f64>,
        combinations: &mut Vec<ParameterCombination>,
    ) {
        if depth >= parameter_names.len() {
            combinations.push(ParameterCombination {
                id: combinations.len(),
                parameters: current_params,
            });
            return;
        }

        let param_name = parameter_names[depth];
        let (min, max, step) = parameter_ranges[param_name];
        
        let mut current_value = min;
        while current_value <= max {
            let mut new_params = current_params.clone();
            new_params.insert(param_name.clone(), current_value);
            
            self.generate_combinations_recursive(
                parameter_names,
                parameter_ranges,
                depth + 1,
                new_params,
                combinations,
            );
            
            current_value += step;
        }
    }

    pub async fn optimize_parallel<S: Strategy + Clone + Send + Sync + 'static>(
        &self,
        strategy_template: S,
        parameter_ranges: HashMap<String, (f64, f64, f64)>,
        config: OptimizationConfig,
    ) -> Result<Vec<OptimizationResult>, Box<dyn std::error::Error>> {
        
        // Set thread pool size
        rayon::ThreadPoolBuilder::new()
            .num_threads(self.max_threads)
            .build_global()
            .unwrap_or(());

        let combinations = self.generate_parameter_combinations(&parameter_ranges);
        let total_combinations = combinations.len();
        
        println!("Generated {} parameter combinations", total_combinations);
        
        if total_combinations > 10000 {
            eprintln!("Warning: Large number of combinations ({}). This may take a long time.", total_combinations);
        }

        // Shared progress tracking
        let completed_count = Arc::new(Mutex::new(0usize));
        let progress_sender = self.progress_sender.clone();

        // Run optimizations in parallel
        let results: Vec<OptimizationResult> = combinations
            .into_par_iter()
            .map(|combination| {
                let mut strategy = strategy_template.clone();
                
                // Apply parameters to strategy (this would need to be implemented based on strategy interface)
                // strategy.set_parameters(combination.parameters.clone());

                // Run backtest for this parameter combination
                let result = self.run_single_optimization(
                    strategy,
                    combination.parameters.clone(),
                    &config,
                );

                // Update progress
                {
                    let mut count = completed_count.lock().unwrap();
                    *count += 1;
                    
                    if let Some(sender) = &progress_sender {
                        let progress = ProgressUpdate {
                            completed: *count,
                            total: total_combinations,
                            current_parameters: combination.parameters.clone(),
                            current_result: result.as_ref().ok().cloned(),
                        };
                        let _ = sender.send(progress);
                    }

                    if *count % 100 == 0 || *count == total_combinations {
                        println!("Progress: {}/{} combinations completed", *count, total_combinations);
                    }
                }

                result
            })
            .filter_map(|result| result.ok())
            .collect();

        Ok(results)
    }

    fn run_single_optimization<S: Strategy>(
        &self,
        strategy: S,
        parameters: HashMap<String, f64>,
        config: &OptimizationConfig,
    ) -> Result<OptimizationResult, Box<dyn std::error::Error>> {
        
        // Placeholder for single optimization run
        // In practice, this would:
        // 1. Apply parameters to strategy
        // 2. Run backtest with the strategy
        // 3. Calculate performance metrics
        // 4. Return OptimizationResult

        use crate::backtesting::PerformanceMetrics;
        use rust_decimal::Decimal;

        // Simulate some processing time
        std::thread::sleep(std::time::Duration::from_millis(1));

        // Generate mock result for testing
        let mut metrics = PerformanceMetrics::new();
        metrics.total_return = (parameters.values().sum::<f64>() % 0.2) - 0.1;
        metrics.sharpe_ratio = parameters.values().sum::<f64>() % 3.0;
        metrics.win_rate = (parameters.values().sum::<f64>() % 0.4) + 0.4;
        metrics.profit_factor = (parameters.values().sum::<f64>() % 2.0) + 0.5;
        metrics.total_trades = ((parameters.values().sum::<f64>() % 500.0) + 100.0) as usize;
        metrics.avg_trade_duration_ms = ((parameters.values().sum::<f64>() % 300000.0) + 60000.0) as u64;
        metrics.volatility = (parameters.values().sum::<f64>() % 0.3) + 0.1;
        metrics.beta = (parameters.values().sum::<f64>() % 2.0) - 1.0;
        metrics.alpha = (parameters.values().sum::<f64>() % 0.1) - 0.05;
        
        let param_set = ParameterSet::from_hashmap(parameters.clone());
        
        let mock_result = OptimizationResult {
            parameters: param_set,
            backtest_result: BacktestResult::default(),
            objective_value: metrics.sharpe_ratio,
            timestamp: chrono::Utc::now(),
            metrics,
            equity_curve: vec![],
            trade_analysis: None,
            parameter_sensitivity: Some(serde_json::json!(Self::calculate_mock_sensitivity(&parameters))),
        };

        Ok(mock_result)
    }

    fn calculate_mock_sensitivity(parameters: &HashMap<String, f64>) -> HashMap<String, f64> {
        // Mock parameter sensitivity calculation
        parameters.iter()
            .map(|(name, value)| (name.clone(), (value % 1.0) * 0.1))
            .collect()
    }

    pub fn estimate_completion_time(&self, completed: usize, total: usize, elapsed_ms: u64) -> u64 {
        if completed == 0 {
            return 0;
        }

        let avg_time_per_combination = elapsed_ms / completed as u64;
        let remaining = total - completed;
        avg_time_per_combination * remaining as u64
    }

    pub fn get_resource_usage(&self) -> ResourceUsage {
        ResourceUsage {
            active_threads: rayon::current_num_threads(),
            memory_usage_mb: self.get_memory_usage_mb(),
            cpu_usage_percent: self.get_cpu_usage(),
        }
    }

    fn get_memory_usage_mb(&self) -> u64 {
        // Placeholder for memory usage calculation
        // In practice, this would use system monitoring
        1024 // Mock 1GB usage
    }

    fn get_cpu_usage(&self) -> f64 {
        // Placeholder for CPU usage calculation
        // In practice, this would use system monitoring
        75.0 // Mock 75% CPU usage
    }
}

#[derive(Debug, Clone)]
pub struct ResourceUsage {
    pub active_threads: usize,
    pub memory_usage_mb: u64,
    pub cpu_usage_percent: f64,
}

pub async fn optimize_with_early_stopping<S: Strategy + Clone + Send + Sync + 'static>(
    optimizer: ParallelOptimizer,
    strategy: S,
    parameter_ranges: HashMap<String, (f64, f64, f64)>,
    config: OptimizationConfig,
    early_stop_threshold: f64,
    patience: usize,
) -> Result<Vec<OptimizationResult>, Box<dyn std::error::Error>> {
    
    let mut best_metric = f64::NEG_INFINITY;
    let mut patience_counter = 0;
    let mut all_results = Vec::new();
    
    // This would implement batched optimization with early stopping
    // For now, just run the full optimization
    optimizer.optimize_parallel(strategy, parameter_ranges, config).await
}