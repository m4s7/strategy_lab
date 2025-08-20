use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::time::{Duration, Instant};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemMetrics {
    pub timestamp: u64,
    pub cpu_usage: f64,
    pub memory_usage: u64,
    pub disk_usage: u64,
    pub network_io: NetworkIO,
    pub process_count: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NetworkIO {
    pub bytes_sent: u64,
    pub bytes_received: u64,
    pub packets_sent: u64,
    pub packets_received: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptimizationMetrics {
    pub job_id: String,
    pub current_combination: usize,
    pub total_combinations: usize,
    pub progress_percent: f64,
    pub estimated_completion_ms: u64,
    pub current_best_sharpe: f64,
    pub combinations_per_second: f64,
    pub resource_usage: ResourceMetrics,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResourceMetrics {
    pub cpu_cores_used: usize,
    pub memory_mb_used: u64,
    pub memory_mb_available: u64,
    pub disk_io_read_mb_per_sec: f64,
    pub disk_io_write_mb_per_sec: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BacktestMetrics {
    pub strategy_name: String,
    pub ticks_processed: u64,
    pub ticks_per_second: f64,
    pub trades_executed: u32,
    pub current_pnl: f64,
    pub current_drawdown: f64,
    pub processing_latency_us: u64,
}

pub struct MetricsCollector {
    start_time: Instant,
    last_collection: Instant,
    metrics_history: Vec<SystemMetrics>,
    optimization_metrics: HashMap<String, OptimizationMetrics>,
    backtest_metrics: HashMap<String, BacktestMetrics>,
}

impl MetricsCollector {
    pub fn new() -> Self {
        let now = Instant::now();
        Self {
            start_time: now,
            last_collection: now,
            metrics_history: Vec::new(),
            optimization_metrics: HashMap::new(),
            backtest_metrics: HashMap::new(),
        }
    }

    pub fn collect_system_metrics(&mut self) -> SystemMetrics {
        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_millis() as u64;

        // In a real implementation, these would use system APIs
        let metrics = SystemMetrics {
            timestamp: now,
            cpu_usage: self.get_cpu_usage(),
            memory_usage: self.get_memory_usage(),
            disk_usage: self.get_disk_usage(),
            network_io: self.get_network_io(),
            process_count: self.get_process_count(),
        };

        self.metrics_history.push(metrics.clone());
        
        // Keep only last 1000 metrics to prevent memory growth
        if self.metrics_history.len() > 1000 {
            self.metrics_history.drain(0..100);
        }

        self.last_collection = Instant::now();
        metrics
    }

    pub fn update_optimization_metrics(&mut self, job_id: String, metrics: OptimizationMetrics) {
        self.optimization_metrics.insert(job_id, metrics);
    }

    pub fn update_backtest_metrics(&mut self, strategy_name: String, metrics: BacktestMetrics) {
        self.backtest_metrics.insert(strategy_name, metrics);
    }

    pub fn get_optimization_metrics(&self, job_id: &str) -> Option<&OptimizationMetrics> {
        self.optimization_metrics.get(job_id)
    }

    pub fn get_backtest_metrics(&self, strategy_name: &str) -> Option<&BacktestMetrics> {
        self.backtest_metrics.get(strategy_name)
    }

    pub fn get_recent_system_metrics(&self, duration: Duration) -> Vec<&SystemMetrics> {
        let cutoff_time = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_millis() as u64 
            - duration.as_millis() as u64;

        self.metrics_history
            .iter()
            .filter(|m| m.timestamp >= cutoff_time)
            .collect()
    }

    pub fn get_performance_summary(&self) -> PerformanceSummary {
        let uptime = self.start_time.elapsed();
        
        let avg_cpu = if self.metrics_history.is_empty() {
            0.0
        } else {
            self.metrics_history.iter().map(|m| m.cpu_usage).sum::<f64>() / self.metrics_history.len() as f64
        };

        let current_memory = self.metrics_history
            .last()
            .map(|m| m.memory_usage)
            .unwrap_or(0);

        let active_optimizations = self.optimization_metrics.len();
        let active_backtests = self.backtest_metrics.len();

        PerformanceSummary {
            uptime_seconds: uptime.as_secs(),
            average_cpu_usage: avg_cpu,
            current_memory_usage: current_memory,
            active_optimizations,
            active_backtests,
            metrics_collected: self.metrics_history.len(),
        }
    }

    fn get_cpu_usage(&self) -> f64 {
        // Placeholder - in real implementation, would use system APIs
        use rand::Rng;
        let mut rng = rand::thread_rng();
        rng.gen_range(20.0..80.0)
    }

    fn get_memory_usage(&self) -> u64 {
        // Placeholder - in real implementation, would use system APIs
        use rand::Rng;
        let mut rng = rand::thread_rng();
        rng.gen_range(2_000_000_000..8_000_000_000) // 2-8 GB in bytes
    }

    fn get_disk_usage(&self) -> u64 {
        // Placeholder - in real implementation, would use system APIs
        use rand::Rng;
        let mut rng = rand::thread_rng();
        rng.gen_range(100_000_000_000..500_000_000_000) // 100-500 GB in bytes
    }

    fn get_network_io(&self) -> NetworkIO {
        // Placeholder - in real implementation, would use system APIs
        use rand::Rng;
        let mut rng = rand::thread_rng();
        NetworkIO {
            bytes_sent: rng.gen_range(1_000_000..10_000_000),
            bytes_received: rng.gen_range(1_000_000..10_000_000),
            packets_sent: rng.gen_range(1000..10000),
            packets_received: rng.gen_range(1000..10000),
        }
    }

    fn get_process_count(&self) -> usize {
        // Placeholder - in real implementation, would use system APIs
        use rand::Rng;
        let mut rng = rand::thread_rng();
        rng.gen_range(100..300)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerformanceSummary {
    pub uptime_seconds: u64,
    pub average_cpu_usage: f64,
    pub current_memory_usage: u64,
    pub active_optimizations: usize,
    pub active_backtests: usize,
    pub metrics_collected: usize,
}

impl Default for MetricsCollector {
    fn default() -> Self {
        Self::new()
    }
}

pub struct MetricsAggregator {
    collectors: HashMap<String, MetricsCollector>,
}

impl MetricsAggregator {
    pub fn new() -> Self {
        Self {
            collectors: HashMap::new(),
        }
    }

    pub fn add_collector(&mut self, name: String, collector: MetricsCollector) {
        self.collectors.insert(name, collector);
    }

    pub fn collect_all_metrics(&mut self) -> HashMap<String, SystemMetrics> {
        let mut all_metrics = HashMap::new();
        
        for (name, collector) in self.collectors.iter_mut() {
            let metrics = collector.collect_system_metrics();
            all_metrics.insert(name.clone(), metrics);
        }

        all_metrics
    }

    pub fn get_aggregated_summary(&self) -> AggregatedSummary {
        let total_optimizations: usize = self.collectors.values()
            .map(|c| c.optimization_metrics.len())
            .sum();

        let total_backtests: usize = self.collectors.values()
            .map(|c| c.backtest_metrics.len())
            .sum();

        let avg_cpu = if self.collectors.is_empty() {
            0.0
        } else {
            self.collectors.values()
                .map(|c| c.metrics_history.last().map(|m| m.cpu_usage).unwrap_or(0.0))
                .sum::<f64>() / self.collectors.len() as f64
        };

        AggregatedSummary {
            total_collectors: self.collectors.len(),
            total_optimizations,
            total_backtests,
            average_cpu_usage: avg_cpu,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AggregatedSummary {
    pub total_collectors: usize,
    pub total_optimizations: usize,
    pub total_backtests: usize,
    pub average_cpu_usage: f64,
}

impl Default for MetricsAggregator {
    fn default() -> Self {
        Self::new()
    }
}