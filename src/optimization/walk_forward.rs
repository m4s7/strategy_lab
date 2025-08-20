use crate::backtesting::{BacktestEngine, BacktestResult, BacktestConfig};
use crate::strategy::traits::Strategy;
use crate::statistics::{StatisticalAnalyzer, StatisticalTest, ConfidenceInterval};
use crate::data::{TickData, DataIngestionEngine, IngestionConfig};
use crate::optimization::{grid_search::GridSearchOptimizer, GridSearchConfig, ObjectiveFunction};
use chrono::{DateTime, Utc, Duration};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::Path;
use rust_decimal::Decimal;
use tracing::{info, debug, warn, error};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WalkForwardConfig {
    pub training_window_days: i32,
    pub testing_window_days: i32,
    pub step_size_days: i32,
    pub min_trades_per_window: u32,
    pub optimization_metric: OptimizationMetric,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum OptimizationMetric {
    SharpeRatio,
    TotalReturn,
    MaxDrawdown,
    ProfitFactor,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WalkForwardResult {
    pub windows: Vec<WalkForwardWindow>,
    pub overall_performance: WalkForwardSummary,
    pub parameter_stability: ParameterStabilityAnalysis,
    pub out_of_sample_degradation: f64,
    pub statistical_significance: Option<StatisticalTest>,
    pub predictive_power: f64,
    pub robustness_score: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WalkForwardWindow {
    pub window_id: usize,
    pub training_start: DateTime<Utc>,
    pub training_end: DateTime<Utc>,
    pub testing_start: DateTime<Utc>,
    pub testing_end: DateTime<Utc>,
    pub optimal_parameters: HashMap<String, f64>,
    pub in_sample_performance: BacktestResult,
    pub out_of_sample_performance: BacktestResult,
    pub parameter_sensitivity: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WalkForwardSummary {
    pub total_windows: usize,
    pub successful_windows: usize,
    pub average_in_sample_sharpe: f64,
    pub average_out_of_sample_sharpe: f64,
    pub consistency_score: f64,
    pub overall_out_of_sample_return: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParameterStabilityAnalysis {
    pub parameter_volatility: HashMap<String, f64>,
    pub correlation_matrix: HashMap<String, HashMap<String, f64>>,
    pub stability_score: f64,
}

pub struct WalkForwardAnalyzer {
    config: WalkForwardConfig,
}

impl WalkForwardAnalyzer {
    pub fn new(config: WalkForwardConfig) -> Self {
        Self { config }
    }

    pub async fn analyze<S: Strategy + Clone>(
        &self,
        strategy_template: S,
        parameter_ranges: HashMap<String, (f64, f64, f64)>, // (min, max, step)
        data_start: DateTime<Utc>,
        data_end: DateTime<Utc>,
    ) -> Result<WalkForwardResult, Box<dyn std::error::Error>> {
        let mut windows = Vec::new();
        let mut current_start = data_start;
        let mut window_id = 0;

        while current_start + Duration::days(self.config.training_window_days as i64) 
                + Duration::days(self.config.testing_window_days as i64) <= data_end {
            
            let training_end = current_start + Duration::days(self.config.training_window_days as i64);
            let testing_start = training_end;
            let testing_end = testing_start + Duration::days(self.config.testing_window_days as i64);

            // Run optimization on training window
            let optimal_parameters = self.optimize_on_training_window(
                &strategy_template,
                &parameter_ranges,
                current_start,
                training_end,
            ).await?;

            // Test on out-of-sample window
            let mut optimized_strategy = strategy_template.clone();
            // Apply optimal parameters to strategy (implementation depends on strategy interface)
            
            let in_sample_result = self.run_backtest(
                &optimized_strategy,
                current_start,
                training_end,
            ).await?;

            let out_of_sample_result = self.run_backtest(
                &optimized_strategy,
                testing_start,
                testing_end,
            ).await?;

            let parameter_sensitivity = self.calculate_parameter_sensitivity(&optimal_parameters);

            windows.push(WalkForwardWindow {
                window_id,
                training_start: current_start,
                training_end,
                testing_start,
                testing_end,
                optimal_parameters,
                in_sample_performance: in_sample_result,
                out_of_sample_performance: out_of_sample_result,
                parameter_sensitivity,
            });

            current_start += Duration::days(self.config.step_size_days as i64);
            window_id += 1;
        }

        let overall_performance = self.calculate_overall_performance(&windows);
        let parameter_stability = self.analyze_parameter_stability(&windows);
        let out_of_sample_degradation = self.calculate_out_of_sample_degradation(&windows);
        
        // Perform statistical significance testing on results
        let statistical_significance = self.test_statistical_significance(&windows)?;
        
        // Calculate additional robustness metrics
        let predictive_power = self.calculate_predictive_power(&windows);
        let robustness_score = self.calculate_robustness_score(&windows);
        
        info!("Walk-forward analysis completed: {} windows, degradation: {:.2}%, statistical significance: {}, robustness: {:.3}",
              windows.len(), out_of_sample_degradation * 100.0, statistical_significance.is_significant, robustness_score);

        Ok(WalkForwardResult {
            windows,
            overall_performance,
            parameter_stability,
            out_of_sample_degradation,
            statistical_significance: Some(statistical_significance),
            predictive_power,
            robustness_score,
        })
    }

    async fn optimize_on_training_window<S: Strategy>(
        &self,
        strategy: &S,
        parameter_ranges: &HashMap<String, (f64, f64, f64)>,
        start_time: DateTime<Utc>,
        end_time: DateTime<Utc>,
    ) -> Result<HashMap<String, f64>, Box<dyn std::error::Error>> {
        info!("Optimizing strategy parameters on training window: {} to {}", start_time, end_time);
        
        // Use grid search optimization for parameter tuning  
        let grid_search_config = GridSearchConfig {
            parameter_ranges: parameter_ranges.clone(),
            objective: ObjectiveFunction::SharpeRatio,
            max_iterations: 1000,
        };
        let optimizer = GridSearchOptimizer::new(grid_search_config);
        
        // Create standard backtesting configuration for training window
        let backtest_config = BacktestConfig {
            initial_capital: Decimal::from(10000),
            start_date: start_time,
            end_date: end_time,
            ..Default::default()
        };
        
        // Find optimal parameters using grid search
        let optimal_params = optimizer.optimize(
            strategy.clone(),
            parameter_ranges.clone(),
            start_time,
            end_time,
            &self.config.optimization_metric,
        ).await?;
        
        debug!("Found optimal parameters: {:?}", optimal_params);
        Ok(optimal_params)
    }

    async fn run_backtest<S: Strategy>(
        &self,
        strategy: &S,
        start_time: DateTime<Utc>,
        end_time: DateTime<Utc>,
    ) -> Result<BacktestResult, Box<dyn std::error::Error>> {
        debug!("Running backtest from {} to {}", start_time, end_time);
        
        // Create standard backtesting engine for precise simulation
        let backtest_config = BacktestConfig {
            initial_capital: Decimal::from(10000),
            start_date: start_time,
            end_date: end_time,
            ..Default::default()
        };
        
        let mut engine = BacktestEngine::new(backtest_config);
        
        // Load tick data for the specified time range
        let tick_data = self.load_tick_data(start_time, end_time).await?;
        
        if tick_data.len() < self.config.min_trades_per_window as usize {
            warn!("Insufficient data for backtest window ({} ticks)", tick_data.len());
        }
        
        // For now, return a placeholder result since we need actual data loading
        // TODO: Implement proper backtesting with loaded tick data
        let result = BacktestResult::default();
        
        debug!("Backtest completed: PnL: {}, Trades: {}, Sharpe: {:.3}", 
               result.total_pnl, result.total_trades, result.sharpe_ratio);
        
        Ok(result)
    }

    fn calculate_parameter_sensitivity(&self, parameters: &HashMap<String, f64>) -> f64 {
        if parameters.is_empty() {
            return 0.0;
        }
        
        // Simplified sensitivity calculation
        let mut total_cv = 0.0;
        let mut param_count = 0;
        
        for (_, &value) in parameters {
            if value != 0.0 {
                let estimated_std = value.abs() * 0.1;
                let cv = estimated_std / value.abs();
                total_cv += cv;
                param_count += 1;
            }
        }
        
        if param_count > 0 {
            total_cv / param_count as f64
        } else {
            0.0
        }
    }

    fn calculate_overall_performance(&self, windows: &[WalkForwardWindow]) -> WalkForwardSummary {
        let total_windows = windows.len();
        let successful_windows = windows.iter()
            .filter(|w| w.out_of_sample_performance.total_pnl > rust_decimal::Decimal::ZERO)
            .count();

        let average_in_sample_sharpe = if total_windows > 0 {
            windows.iter()
                .map(|w| w.in_sample_performance.sharpe_ratio)
                .sum::<f64>() / total_windows as f64
        } else {
            0.0
        };

        let average_out_of_sample_sharpe = if total_windows > 0 {
            windows.iter()
                .map(|w| w.out_of_sample_performance.sharpe_ratio)
                .sum::<f64>() / total_windows as f64
        } else {
            0.0
        };

        let consistency_score = if total_windows > 0 {
            successful_windows as f64 / total_windows as f64
        } else {
            0.0
        };

        let overall_out_of_sample_return = windows.iter()
            .map(|w| w.out_of_sample_performance.total_pnl.to_f64().unwrap_or(0.0))
            .sum::<f64>();

        WalkForwardSummary {
            total_windows,
            successful_windows,
            average_in_sample_sharpe,
            average_out_of_sample_sharpe,
            consistency_score,
            overall_out_of_sample_return,
        }
    }

    fn analyze_parameter_stability(&self, windows: &[WalkForwardWindow]) -> ParameterStabilityAnalysis {
        let mut parameter_volatility = HashMap::new();
        let correlation_matrix = HashMap::new();

        // Calculate parameter volatility across windows
        if !windows.is_empty() {
            let first_window_params = &windows[0].optimal_parameters;
            
            for param_name in first_window_params.keys() {
                let values: Vec<f64> = windows.iter()
                    .filter_map(|w| w.optimal_parameters.get(param_name))
                    .copied()
                    .collect();

                if values.len() > 1 {
                    let mean = values.iter().sum::<f64>() / values.len() as f64;
                    let variance = values.iter()
                        .map(|v| (v - mean).powi(2))
                        .sum::<f64>() / values.len() as f64;
                    let std_dev = variance.sqrt();
                    let volatility = if mean != 0.0 { std_dev / mean.abs() } else { 0.0 };
                    
                    parameter_volatility.insert(param_name.clone(), volatility);
                }
            }
        }
        
        let stability_score = if parameter_volatility.is_empty() {
            0.0
        } else {
            1.0 - (parameter_volatility.values().sum::<f64>() / parameter_volatility.len() as f64)
        };

        ParameterStabilityAnalysis {
            parameter_volatility,
            correlation_matrix,
            stability_score,
        }
    }

    fn calculate_out_of_sample_degradation(&self, windows: &[WalkForwardWindow]) -> f64 {
        if windows.is_empty() {
            return 0.0;
        }

        let avg_in_sample = windows.iter()
            .map(|w| w.in_sample_performance.sharpe_ratio)
            .sum::<f64>() / windows.len() as f64;

        let avg_out_of_sample = windows.iter()
            .map(|w| w.out_of_sample_performance.sharpe_ratio)
            .sum::<f64>() / windows.len() as f64;

        if avg_in_sample != 0.0 {
            (avg_in_sample - avg_out_of_sample) / avg_in_sample
        } else {
            0.0
        }
    }
    
    /// Load tick data for specified time range
    async fn load_tick_data(
        &self,
        start_time: DateTime<Utc>,
        end_time: DateTime<Utc>,
    ) -> Result<Vec<TickData>, Box<dyn std::error::Error>> {
        // This would typically load from a database or file system
        // For now, return empty vector as placeholder
        debug!("Loading tick data from {} to {}", start_time, end_time);
        
        // TODO: Implement actual data loading from TimescaleDB
        // let query = "SELECT * FROM tick_data WHERE timestamp BETWEEN $1 AND $2 ORDER BY timestamp";
        // let ticks = sqlx::query_as::<_, TickData>(query)
        //     .bind(start_time)
        //     .bind(end_time)
        //     .fetch_all(&self.database_pool)
        //     .await?;
        
        Ok(Vec::new())
    }
    
    /// Test statistical significance of walk-forward results
    fn test_statistical_significance(
        &self,
        windows: &[WalkForwardWindow],
    ) -> Result<StatisticalTest, Box<dyn std::error::Error>> {
        if windows.len() < 2 {
            return Ok(StatisticalTest {
                test_name: "insufficient_data".to_string(),
                statistic: 0.0,
                p_value: 1.0,
                is_significant: false,
                confidence_level: 0.95,
                interpretation: "No significant difference in performance".to_string(),
            });
        }
        
        // Extract in-sample and out-of-sample returns
        let in_sample_returns: Vec<f64> = windows.iter()
            .map(|w| w.in_sample_performance.sharpe_ratio)
            .collect();
            
        let out_of_sample_returns: Vec<f64> = windows.iter()
            .map(|w| w.out_of_sample_performance.sharpe_ratio)
            .collect();
        
        // Perform paired t-test to check if out-of-sample performance 
        // is significantly different from in-sample
        let analyzer = StatisticalAnalyzer::new();
        let t_test = analyzer.t_test(&in_sample_returns, &out_of_sample_returns, 0.95);
        
        info!("Statistical significance test: p-value = {:.4}, significant = {}", 
              t_test.p_value, t_test.is_significant);
        
        Ok(t_test)
    }
    
    /// Calculate predictive power of the strategy
    fn calculate_predictive_power(&self, windows: &[WalkForwardWindow]) -> f64 {
        if windows.len() < 2 {
            return 0.0;
        }
        
        // Calculate correlation between in-sample and out-of-sample performance
        let in_sample_sharpe: Vec<f64> = windows.iter()
            .map(|w| w.in_sample_performance.sharpe_ratio)
            .collect();
            
        let out_of_sample_sharpe: Vec<f64> = windows.iter()
            .map(|w| w.out_of_sample_performance.sharpe_ratio)
            .collect();
        
        // Simple correlation calculation
        let n = in_sample_sharpe.len() as f64;
        let sum_in: f64 = in_sample_sharpe.iter().sum();
        let sum_out: f64 = out_of_sample_sharpe.iter().sum();
        let sum_in_sq: f64 = in_sample_sharpe.iter().map(|x| x * x).sum();
        let sum_out_sq: f64 = out_of_sample_sharpe.iter().map(|x| x * x).sum();
        let sum_in_out: f64 = in_sample_sharpe.iter().zip(out_of_sample_sharpe.iter())
            .map(|(x, y)| x * y).sum();
        
        let numerator = n * sum_in_out - sum_in * sum_out;
        let denominator = ((n * sum_in_sq - sum_in * sum_in) * (n * sum_out_sq - sum_out * sum_out)).sqrt();
        
        if denominator == 0.0 {
            0.0
        } else {
            (numerator / denominator).abs()
        }
    }
    
    /// Calculate robustness score based on parameter stability and consistency
    fn calculate_robustness_score(&self, windows: &[WalkForwardWindow]) -> f64 {
        if windows.is_empty() {
            return 0.0;
        }
        
        // Combine multiple robustness factors
        let consistency_score = windows.iter()
            .filter(|w| w.out_of_sample_performance.total_pnl > Decimal::ZERO)
            .count() as f64 / windows.len() as f64;
        
        let parameter_stability = self.analyze_parameter_stability(windows).stability_score;
        
        let performance_stability = {
            let sharpe_ratios: Vec<f64> = windows.iter()
                .map(|w| w.out_of_sample_performance.sharpe_ratio)
                .collect();
                
            if sharpe_ratios.len() > 1 {
                let mean = sharpe_ratios.iter().sum::<f64>() / sharpe_ratios.len() as f64;
                let variance = sharpe_ratios.iter()
                    .map(|x| (x - mean).powi(2))
                    .sum::<f64>() / sharpe_ratios.len() as f64;
                let std_dev = variance.sqrt();
                
                if mean != 0.0 {
                    1.0 - (std_dev / mean.abs()).min(1.0)
                } else {
                    0.0
                }
            } else {
                1.0
            }
        };
        
        // Weighted combination of robustness factors
        0.4 * consistency_score + 0.3 * parameter_stability + 0.3 * performance_stability
    }
}

impl Default for WalkForwardConfig {
    fn default() -> Self {
        Self {
            training_window_days: 30,
            testing_window_days: 5,
            step_size_days: 7,
            min_trades_per_window: 10,
            optimization_metric: OptimizationMetric::SharpeRatio,
        }
    }
}

impl Default for WalkForwardResult {
    fn default() -> Self {
        Self {
            windows: Vec::new(),
            overall_performance: WalkForwardSummary {
                total_windows: 0,
                successful_windows: 0,
                average_in_sample_sharpe: 0.0,
                average_out_of_sample_sharpe: 0.0,
                consistency_score: 0.0,
                overall_out_of_sample_return: 0.0,
            },
            parameter_stability: ParameterStabilityAnalysis {
                parameter_volatility: HashMap::new(),
                correlation_matrix: HashMap::new(),
                stability_score: 0.0,
            },
            out_of_sample_degradation: 0.0,
            statistical_significance: None,
            predictive_power: 0.0,
            robustness_score: 0.0,
        }
    }
}

impl WalkForwardResult {
    /// Generate a comprehensive analysis report
    pub fn generate_report(&self) -> String {
        let mut report = String::new();
        
        report.push_str("\n=== Walk-Forward Analysis Report ===\n\n");
        
        // Overall Performance Summary
        report.push_str(&format!(
            "Performance Summary:\n\n\
            - Total Windows: {}\n\
            - Successful Windows: {} ({:.1}%)\n\
            - Average In-Sample Sharpe: {:.3}\n\
            - Average Out-of-Sample Sharpe: {:.3}\n\
            - Performance Degradation: {:.1}%\n\n",
            self.overall_performance.total_windows,
            self.overall_performance.successful_windows,
            self.overall_performance.consistency_score * 100.0,
            self.overall_performance.average_in_sample_sharpe,
            self.overall_performance.average_out_of_sample_sharpe,
            self.out_of_sample_degradation * 100.0
        ));
        
        // Statistical Significance
        if let Some(ref significance) = self.statistical_significance {
            report.push_str(&format!(
                "Statistical Analysis:\n\n\
                - Test: {}\n\
                - P-value: {:.4}\n\
                - Significant: {}\n\
                - Confidence Level: {:.1}%\n\n",
                significance.test_name,
                significance.p_value,
                if significance.is_significant { "Yes" } else { "No" },
                significance.confidence_level * 100.0
            ));
        }
        
        // Robustness Metrics
        report.push_str(&format!(
            "Robustness Analysis:\n\n\
            - Parameter Stability Score: {:.3}\n\
            - Predictive Power: {:.3}\n\
            - Overall Robustness Score: {:.3}\n\n",
            self.parameter_stability.stability_score,
            self.predictive_power,
            self.robustness_score
        ));
        
        // Window-by-Window Results
        report.push_str("Window Results:\n");
        for (i, window) in self.windows.iter().enumerate() {
            report.push_str(&format!(
                "Window {}: IS Sharpe: {:.3}, OOS Sharpe: {:.3}, Sensitivity: {:.3}\n",
                i + 1,
                window.in_sample_performance.sharpe_ratio,
                window.out_of_sample_performance.sharpe_ratio,
                window.parameter_sensitivity
            ));
        }
        
        report.push_str("\n=== End of Report ===\n");
        report
    }
    
    /// Check if the strategy passes robustness criteria
    pub fn is_robust(&self) -> bool {
        self.robustness_score >= 0.7 &&
        self.out_of_sample_degradation <= 0.2 &&
        self.overall_performance.consistency_score >= 0.6 &&
        self.parameter_stability.stability_score >= 0.5
    }
}

pub use WalkForwardAnalyzer as WalkForwardAnalysis;