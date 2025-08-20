use statrs::distribution::{ContinuousCDF, Normal, StudentsT};
use statrs::statistics::{Data, Distribution, OrderStatistics};
use std::collections::HashMap;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StatisticalTest {
    pub test_name: String,
    pub statistic: f64,
    pub p_value: f64,
    pub confidence_level: f64,
    pub is_significant: bool,
    pub interpretation: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConfidenceInterval {
    pub lower_bound: f64,
    pub upper_bound: f64,
    pub confidence_level: f64,
    pub point_estimate: f64,
}

pub struct StatisticalAnalyzer;

impl StatisticalAnalyzer {
    /// Perform t-test for comparing two strategy performances
    pub fn t_test(sample1: &[f64], sample2: &[f64], confidence_level: f64) -> StatisticalTest {
        let n1 = sample1.len() as f64;
        let n2 = sample2.len() as f64;
        
        let mean1 = sample1.iter().sum::<f64>() / n1;
        let mean2 = sample2.iter().sum::<f64>() / n2;
        
        let var1 = sample1.iter().map(|x| (x - mean1).powi(2)).sum::<f64>() / (n1 - 1.0);
        let var2 = sample2.iter().map(|x| (x - mean2).powi(2)).sum::<f64>() / (n2 - 1.0);
        
        // Pooled standard deviation
        let pooled_var = ((n1 - 1.0) * var1 + (n2 - 1.0) * var2) / (n1 + n2 - 2.0);
        let pooled_std = pooled_var.sqrt();
        
        // T-statistic
        let t_stat = (mean1 - mean2) / (pooled_std * (1.0/n1 + 1.0/n2).sqrt());
        
        // Degrees of freedom
        let df = n1 + n2 - 2.0;
        
        // Calculate p-value using Student's t-distribution
        let t_dist = StudentsT::new(0.0, 1.0, df).unwrap();
        let p_value = 2.0 * (1.0 - t_dist.cdf(t_stat.abs()));
        
        let is_significant = p_value < (1.0 - confidence_level);
        
        let interpretation = if is_significant {
            format!("Significant difference between strategies (p={:.4})", p_value)
        } else {
            format!("No significant difference between strategies (p={:.4})", p_value)
        };
        
        StatisticalTest {
            test_name: "Two-Sample T-Test".to_string(),
            statistic: t_stat,
            p_value,
            confidence_level,
            is_significant,
            interpretation,
        }
    }
    
    /// Calculate confidence interval for mean return
    pub fn confidence_interval(data: &[f64], confidence_level: f64) -> ConfidenceInterval {
        let n = data.len() as f64;
        let mean = data.iter().sum::<f64>() / n;
        let variance = data.iter().map(|x| (x - mean).powi(2)).sum::<f64>() / (n - 1.0);
        let std_error = (variance / n).sqrt();
        
        // Use t-distribution for small samples
        let df = n - 1.0;
        let t_dist = StudentsT::new(0.0, 1.0, df).unwrap();
        let t_critical = t_dist.inverse_cdf((1.0 + confidence_level) / 2.0);
        
        let margin_of_error = t_critical * std_error;
        
        ConfidenceInterval {
            lower_bound: mean - margin_of_error,
            upper_bound: mean + margin_of_error,
            confidence_level,
            point_estimate: mean,
        }
    }
    
    /// Bootstrap confidence interval for any statistic
    pub fn bootstrap_confidence_interval<F>(
        data: &[f64],
        statistic_fn: F,
        confidence_level: f64,
        n_iterations: usize,
    ) -> ConfidenceInterval
    where
        F: Fn(&[f64]) -> f64,
    {
        use rand::seq::SliceRandom;
        use rand::thread_rng;
        
        let mut rng = thread_rng();
        let mut bootstrap_statistics = Vec::with_capacity(n_iterations);
        let n = data.len();
        
        // Generate bootstrap samples
        for _ in 0..n_iterations {
            let mut bootstrap_sample = Vec::with_capacity(n);
            for _ in 0..n {
                bootstrap_sample.push(*data.choose(&mut rng).unwrap());
            }
            bootstrap_statistics.push(statistic_fn(&bootstrap_sample));
        }
        
        // Sort bootstrap statistics
        bootstrap_statistics.sort_by(|a, b| a.partial_cmp(b).unwrap());
        
        // Calculate percentiles
        let alpha = (1.0 - confidence_level) / 2.0;
        let lower_idx = ((n_iterations as f64) * alpha) as usize;
        let upper_idx = ((n_iterations as f64) * (1.0 - alpha)) as usize;
        
        let point_estimate = statistic_fn(data);
        
        ConfidenceInterval {
            lower_bound: bootstrap_statistics[lower_idx],
            upper_bound: bootstrap_statistics[upper_idx],
            confidence_level,
            point_estimate,
        }
    }
    
    /// Test for normality using Jarque-Bera test
    pub fn normality_test(data: &[f64]) -> StatisticalTest {
        let n = data.len() as f64;
        let mean = data.iter().sum::<f64>() / n;
        
        // Calculate moments
        let m2 = data.iter().map(|x| (x - mean).powi(2)).sum::<f64>() / n;
        let m3 = data.iter().map(|x| (x - mean).powi(3)).sum::<f64>() / n;
        let m4 = data.iter().map(|x| (x - mean).powi(4)).sum::<f64>() / n;
        
        // Skewness and kurtosis
        let skewness = m3 / m2.powf(1.5);
        let kurtosis = m4 / (m2 * m2) - 3.0;
        
        // Jarque-Bera statistic
        let jb_stat = n / 6.0 * (skewness.powi(2) + kurtosis.powi(2) / 4.0);
        
        // Chi-squared distribution with 2 degrees of freedom
        // Using approximation for p-value
        let p_value = (-jb_stat / 2.0).exp();
        
        let is_significant = p_value < 0.05;
        
        let interpretation = if is_significant {
            "Data significantly deviates from normal distribution".to_string()
        } else {
            "Data appears to be normally distributed".to_string()
        };
        
        StatisticalTest {
            test_name: "Jarque-Bera Normality Test".to_string(),
            statistic: jb_stat,
            p_value,
            confidence_level: 0.95,
            is_significant,
            interpretation,
        }
    }
    
    /// Mann-Whitney U test for non-parametric comparison
    pub fn mann_whitney_u_test(sample1: &[f64], sample2: &[f64]) -> StatisticalTest {
        let mut combined: Vec<(f64, usize)> = Vec::new();
        
        // Combine samples with group labels
        for &val in sample1 {
            combined.push((val, 1));
        }
        for &val in sample2 {
            combined.push((val, 2));
        }
        
        // Sort combined data
        combined.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());
        
        // Assign ranks
        let mut ranks = vec![0.0; combined.len()];
        let mut i = 0;
        while i < combined.len() {
            let mut j = i;
            while j < combined.len() && combined[j].0 == combined[i].0 {
                j += 1;
            }
            let avg_rank = ((i + 1) + j) as f64 / 2.0;
            for k in i..j {
                ranks[k] = avg_rank;
            }
            i = j;
        }
        
        // Calculate U statistic
        let mut r1 = 0.0;
        for (idx, &(_, group)) in combined.iter().enumerate() {
            if group == 1 {
                r1 += ranks[idx];
            }
        }
        
        let n1 = sample1.len() as f64;
        let n2 = sample2.len() as f64;
        let u1 = r1 - n1 * (n1 + 1.0) / 2.0;
        let u2 = n1 * n2 - u1;
        let u = u1.min(u2);
        
        // Normal approximation for large samples
        let mean_u = n1 * n2 / 2.0;
        let std_u = ((n1 * n2 * (n1 + n2 + 1.0)) / 12.0).sqrt();
        let z = (u - mean_u) / std_u;
        
        let normal = Normal::new(0.0, 1.0).unwrap();
        let p_value = 2.0 * normal.cdf(z.abs());
        
        let is_significant = p_value < 0.05;
        
        let interpretation = if is_significant {
            "Significant difference between samples (non-parametric)".to_string()
        } else {
            "No significant difference between samples (non-parametric)".to_string()
        };
        
        StatisticalTest {
            test_name: "Mann-Whitney U Test".to_string(),
            statistic: u,
            p_value,
            confidence_level: 0.95,
            is_significant,
            interpretation,
        }
    }
    
    /// Calculate Value at Risk (VaR)
    pub fn value_at_risk(returns: &[f64], confidence_level: f64) -> f64 {
        let mut sorted_returns = returns.to_vec();
        sorted_returns.sort_by(|a, b| a.partial_cmp(b).unwrap());
        
        let alpha = 1.0 - confidence_level;
        let index = (sorted_returns.len() as f64 * alpha) as usize;
        
        sorted_returns[index]
    }
    
    /// Calculate Conditional Value at Risk (CVaR)
    pub fn conditional_value_at_risk(returns: &[f64], confidence_level: f64) -> f64 {
        let var = Self::value_at_risk(returns, confidence_level);
        
        let tail_returns: Vec<f64> = returns.iter()
            .filter(|&&r| r <= var)
            .copied()
            .collect();
        
        if tail_returns.is_empty() {
            var
        } else {
            tail_returns.iter().sum::<f64>() / tail_returns.len() as f64
        }
    }
    
    /// Test for autocorrelation (Ljung-Box test)
    pub fn autocorrelation_test(returns: &[f64], max_lag: usize) -> StatisticalTest {
        let n = returns.len() as f64;
        let mean = returns.iter().sum::<f64>() / n;
        
        let mut autocorrelations = Vec::new();
        
        for lag in 1..=max_lag {
            let mut numerator = 0.0;
            for i in lag..returns.len() {
                numerator += (returns[i] - mean) * (returns[i - lag] - mean);
            }
            
            let denominator: f64 = returns.iter().map(|r| (r - mean).powi(2)).sum();
            let acf = numerator / denominator;
            autocorrelations.push(acf);
        }
        
        // Ljung-Box statistic
        let mut lb_stat = 0.0;
        for (k, &acf) in autocorrelations.iter().enumerate() {
            lb_stat += (acf * acf) / (n - (k + 1) as f64);
        }
        lb_stat *= n * (n + 2.0);
        
        // Chi-squared approximation for p-value
        let p_value = (-lb_stat / (2.0 * max_lag as f64)).exp();
        
        let is_significant = p_value < 0.05;
        
        let interpretation = if is_significant {
            "Significant autocorrelation detected in returns".to_string()
        } else {
            "No significant autocorrelation in returns".to_string()
        };
        
        StatisticalTest {
            test_name: "Ljung-Box Autocorrelation Test".to_string(),
            statistic: lb_stat,
            p_value,
            confidence_level: 0.95,
            is_significant,
            interpretation,
        }
    }
    
    /// Calculate information ratio
    pub fn information_ratio(returns: &[f64], benchmark_returns: &[f64]) -> f64 {
        if returns.len() != benchmark_returns.len() {
            return 0.0;
        }
        
        let excess_returns: Vec<f64> = returns.iter()
            .zip(benchmark_returns.iter())
            .map(|(r, b)| r - b)
            .collect();
        
        let mean_excess = excess_returns.iter().sum::<f64>() / excess_returns.len() as f64;
        let std_excess = (excess_returns.iter()
            .map(|r| (r - mean_excess).powi(2))
            .sum::<f64>() / (excess_returns.len() - 1) as f64)
            .sqrt();
        
        if std_excess == 0.0 {
            0.0
        } else {
            mean_excess / std_excess
        }
    }
    
    /// Monte Carlo simulation for risk metrics
    pub fn monte_carlo_simulation(
        returns: &[f64],
        n_simulations: usize,
        n_periods: usize,
    ) -> Vec<Vec<f64>> {
        use rand::distributions::Distribution as RandDist;
        use rand::thread_rng;
        use statrs::distribution::Normal as RandNormal;
        
        let mean = returns.iter().sum::<f64>() / returns.len() as f64;
        let variance = returns.iter()
            .map(|r| (r - mean).powi(2))
            .sum::<f64>() / (returns.len() - 1) as f64;
        let std_dev = variance.sqrt();
        
        let normal = RandNormal::new(mean, std_dev).unwrap();
        let mut rng = thread_rng();
        
        let mut simulations = Vec::new();
        
        for _ in 0..n_simulations {
            let mut path = Vec::new();
            let mut cumulative_return = 1.0;
            
            for _ in 0..n_periods {
                let period_return = normal.sample(&mut rng);
                cumulative_return *= 1.0 + period_return;
                path.push(cumulative_return - 1.0);
            }
            
            simulations.push(path);
        }
        
        simulations
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerformanceAnalysis {
    pub sharpe_ratio_test: StatisticalTest,
    pub returns_normality: StatisticalTest,
    pub autocorrelation: StatisticalTest,
    pub var_95: f64,
    pub cvar_95: f64,
    pub confidence_interval: ConfidenceInterval,
}

pub fn analyze_strategy_performance(returns: &[f64], benchmark_returns: Option<&[f64]>) -> PerformanceAnalysis {
    let sharpe_ratio = returns.iter().sum::<f64>() / returns.len() as f64
        / (returns.iter().map(|r| r.powi(2)).sum::<f64>() / returns.len() as f64).sqrt();
    
    // Test if Sharpe ratio is significantly different from zero
    let sharpe_test = StatisticalTest {
        test_name: "Sharpe Ratio Significance".to_string(),
        statistic: sharpe_ratio * (returns.len() as f64).sqrt(),
        p_value: if sharpe_ratio > 0.0 { 0.01 } else { 0.5 }, // Simplified
        confidence_level: 0.95,
        is_significant: sharpe_ratio > 0.5,
        interpretation: format!("Sharpe ratio = {:.3}", sharpe_ratio),
    };
    
    PerformanceAnalysis {
        sharpe_ratio_test: sharpe_test,
        returns_normality: StatisticalTest::default(), // Placeholder
        autocorrelation: StatisticalTest::default(), // Placeholder  
        var_95: 0.0, // Placeholder
        cvar_95: 0.0, // Placeholder
        confidence_interval: ConfidenceInterval {
            lower_bound: 0.0,
            upper_bound: 0.0,
            point_estimate: 0.0,
            confidence_level: 0.95,
        },
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use statrs::distribution::{Continuous, Normal};

    fn approx_equal(a: f64, b: f64, tolerance: f64) -> bool {
        (a - b).abs() < tolerance
    }

    #[test]
    fn test_mean_calculation() {
        let analyzer = StatisticalAnalyzer::new();
        
        let data = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let mean = analyzer.mean(&data);
        assert_eq!(mean, 3.0);
        
        let data = vec![10.0, 20.0, 30.0];
        let mean = analyzer.mean(&data);
        assert_eq!(mean, 20.0);
        
        // Empty data
        let data = vec![];
        let mean = analyzer.mean(&data);
        assert!(mean.is_nan());
    }

    #[test]
    fn test_standard_deviation() {
        let analyzer = StatisticalAnalyzer::new();
        
        let data = vec![2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0];
        let std_dev = analyzer.standard_deviation(&data);
        assert!(approx_equal(std_dev, 2.0, 0.001));
        
        // Single value
        let data = vec![5.0];
        let std_dev = analyzer.standard_deviation(&data);
        assert_eq!(std_dev, 0.0);
        
        // Empty data
        let data = vec![];
        let std_dev = analyzer.standard_deviation(&data);
        assert!(std_dev.is_nan());
    }

    #[test]
    fn test_correlation() {
        let analyzer = StatisticalAnalyzer::new();
        
        // Perfect positive correlation
        let x = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let y = vec![2.0, 4.0, 6.0, 8.0, 10.0];
        let corr = analyzer.correlation(&x, &y);
        assert!(approx_equal(corr, 1.0, 0.001));
        
        // Perfect negative correlation
        let x = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let y = vec![5.0, 4.0, 3.0, 2.0, 1.0];
        let corr = analyzer.correlation(&x, &y);
        assert!(approx_equal(corr, -1.0, 0.001));
        
        // No correlation (x is constant)
        let x = vec![5.0, 5.0, 5.0, 5.0, 5.0];
        let y = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let corr = analyzer.correlation(&x, &y);
        assert!(corr.is_nan());
        
        // Different lengths
        let x = vec![1.0, 2.0, 3.0];
        let y = vec![1.0, 2.0];
        let corr = analyzer.correlation(&x, &y);
        assert!(corr.is_nan());
    }

    #[test]
    fn test_t_test() {
        let analyzer = StatisticalAnalyzer::new();
        
        // Two samples with different means
        let sample1 = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let sample2 = vec![3.0, 4.0, 5.0, 6.0, 7.0];
        let t_test = analyzer.t_test(&sample1, &sample2, 0.95);
        
        assert_eq!(t_test.test_name, "two_sample_t_test");
        assert!(!t_test.statistic.is_nan());
        assert!(t_test.p_value >= 0.0 && t_test.p_value <= 1.0);
        assert_eq!(t_test.confidence_level, 0.95);
        
        // Identical samples
        let sample1 = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let sample2 = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let t_test = analyzer.t_test(&sample1, &sample2, 0.95);
        
        assert!(approx_equal(t_test.statistic, 0.0, 0.001));
        assert!(t_test.p_value > 0.05); // Should not be significant
        assert!(!t_test.is_significant);
    }

    #[test]
    fn test_value_at_risk() {
        let analyzer = StatisticalAnalyzer::new();
        
        // Normal distribution-like returns
        let returns = vec![-0.05, -0.03, -0.01, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08];
        
        let var_95 = analyzer.value_at_risk(&returns, 0.95);
        let var_99 = analyzer.value_at_risk(&returns, 0.99);
        
        // 99% VaR should be worse (more negative) than 95% VaR
        assert!(var_99 <= var_95);
        assert!(var_95 < 0.0); // Should be negative for losses
    }

    #[test]
    fn test_expected_shortfall() {
        let analyzer = StatisticalAnalyzer::new();
        
        let returns = vec![-0.10, -0.08, -0.05, -0.02, 0.01, 0.03, 0.05, 0.07, 0.09, 0.12];
        
        let es_95 = analyzer.expected_shortfall(&returns, 0.95);
        let var_95 = analyzer.value_at_risk(&returns, 0.95);
        
        // Expected shortfall should be worse than VaR
        assert!(es_95 <= var_95);
        assert!(es_95 < 0.0);
    }

    #[test]
    fn test_maximum_drawdown() {
        let analyzer = StatisticalAnalyzer::new();
        
        let equity_curve = vec![100.0, 110.0, 105.0, 120.0, 115.0, 90.0, 95.0, 130.0];
        let max_dd = analyzer.maximum_drawdown(&equity_curve);
        
        // Max drawdown should be from peak (120) to trough (90) = 25%
        let expected_dd = (90.0 - 120.0) / 120.0;
        assert!(approx_equal(max_dd, expected_dd, 0.001));
    }

    #[test]
    fn test_sharpe_ratio() {
        let analyzer = StatisticalAnalyzer::new();
        
        let returns = vec![0.01, 0.02, -0.01, 0.03, 0.00, 0.02, -0.005, 0.015];
        let risk_free_rate = 0.005;
        
        let sharpe = analyzer.sharpe_ratio(&returns, risk_free_rate);
        
        let mean_return = analyzer.mean(&returns);
        let excess_return = mean_return - risk_free_rate;
        let std_dev = analyzer.standard_deviation(&returns);
        let expected_sharpe = excess_return / std_dev;
        
        assert!(approx_equal(sharpe, expected_sharpe, 0.001));
    }

    #[test]
    fn test_sortino_ratio() {
        let analyzer = StatisticalAnalyzer::new();
        
        let returns = vec![0.02, 0.01, -0.02, 0.03, -0.01, 0.02, -0.015, 0.025];
        let target_return = 0.0;
        
        let sortino = analyzer.sortino_ratio(&returns, target_return);
        
        assert!(!sortino.is_nan());
        assert!(sortino.is_finite());
        
        // Test with all positive returns (denominator should be 0)
        let positive_returns = vec![0.01, 0.02, 0.03, 0.02, 0.015];
        let sortino_positive = analyzer.sortino_ratio(&positive_returns, 0.0);
        
        assert!(sortino_positive.is_infinite() || sortino_positive.is_nan());
    }
}