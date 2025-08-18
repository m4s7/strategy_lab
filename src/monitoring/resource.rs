//! System resource monitoring

use serde::{Deserialize, Serialize};
use sysinfo::{System, SystemExt, ProcessExt, CpuExt};
use std::sync::{Arc, Mutex};

/// Resource usage data
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResourceUsage {
    pub cpu_percent: f64,
    pub memory_gb: f64,
    pub memory_percent: f64,
    pub disk_read_mb_s: f64,
    pub disk_write_mb_s: f64,
    pub active_threads: usize,
    pub active_cores: usize,
}

/// Resource monitor
#[derive(Clone)]
pub struct ResourceMonitor {
    system: Arc<Mutex<System>>,
}

impl ResourceMonitor {
    pub fn new() -> Self {
        let mut system = System::new_all();
        system.refresh_all();
        
        Self {
            system: Arc::new(Mutex::new(system)),
        }
    }
    
    /// Get current resource usage
    pub fn get_current_usage(&self) -> ResourceUsage {
        let mut system = self.system.lock().unwrap();
        system.refresh_all();
        
        // CPU usage
        let cpu_percent = system.global_cpu_info().cpu_usage() as f64;
        
        // Memory usage
        let total_memory = system.total_memory() as f64 / 1_073_741_824.0; // Convert to GB
        let used_memory = system.used_memory() as f64 / 1_073_741_824.0;
        let memory_percent = (used_memory / total_memory) * 100.0;
        
        // Count active cores
        let active_cores = system.cpus().iter()
            .filter(|cpu| cpu.cpu_usage() > 5.0)
            .count();
        
        // Get process info
        let current_pid = sysinfo::get_current_pid().ok();
        let active_threads = if let Some(pid) = current_pid {
            system.process(pid)
                .map(|p| p.tasks.len())
                .unwrap_or(1)
        } else {
            1
        };
        
        ResourceUsage {
            cpu_percent,
            memory_gb: used_memory,
            memory_percent,
            disk_read_mb_s: 0.0, // Would need additional monitoring
            disk_write_mb_s: 0.0,
            active_threads,
            active_cores,
        }
    }
    
    /// Check if resources are within limits
    pub fn check_limits(&self, max_cpu: f64, max_memory_gb: f64) -> bool {
        let usage = self.get_current_usage();
        usage.cpu_percent <= max_cpu && usage.memory_gb <= max_memory_gb
    }
}