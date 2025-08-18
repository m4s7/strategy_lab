//! Export functionality for reports

use std::fs;
use std::path::PathBuf;
use super::*;

/// Export manager for different report formats
pub struct ExportManager {
    output_dir: PathBuf,
}

impl ExportManager {
    pub fn new(output_dir: PathBuf) -> Self {
        // Create output directory if it doesn't exist
        fs::create_dir_all(&output_dir).ok();
        Self { output_dir }
    }
    
    /// Export report in multiple formats
    pub fn export_all(
        &self,
        report: &Report,
        formats: Vec<ReportFormat>,
    ) -> Result<Vec<PathBuf>, Box<dyn std::error::Error>> {
        let mut exported_files = Vec::new();
        
        for format in formats {
            let filename = self.generate_filename(&report.metadata.strategy_name, format);
            let path = self.output_dir.join(filename);
            
            self.export_single(report, &path, format)?;
            exported_files.push(path);
        }
        
        Ok(exported_files)
    }
    
    /// Export single report
    pub fn export_single(
        &self,
        report: &Report,
        path: &PathBuf,
        format: ReportFormat,
    ) -> Result<(), Box<dyn std::error::Error>> {
        match format {
            ReportFormat::Html => {
                let html = super::templates::html_template(report);
                fs::write(path, html)?;
            }
            ReportFormat::Markdown => {
                let markdown = super::templates::markdown_template(report);
                fs::write(path, markdown)?;
            }
            ReportFormat::Json => {
                let json = serde_json::to_string_pretty(report)?;
                fs::write(path, json)?;
            }
            ReportFormat::Csv => {
                let csv = self.generate_csv(report)?;
                fs::write(path, csv)?;
            }
            ReportFormat::Pdf => {
                // PDF generation would require additional dependencies
                // For now, generate HTML and note that it can be converted
                let html = super::templates::html_template(report);
                let html_path = path.with_extension("html");
                fs::write(&html_path, html)?;
                
                // Create a note file
                let note = format!(
                    "PDF generation requires external tool.\n\
                     Convert {} to PDF using a browser or wkhtmltopdf.",
                    html_path.display()
                );
                fs::write(path.with_extension("txt"), note)?;
            }
        }
        
        Ok(())
    }
    
    /// Generate filename based on strategy and format
    fn generate_filename(&self, strategy_name: &str, format: ReportFormat) -> String {
        let timestamp = chrono::Utc::now().format("%Y%m%d_%H%M%S");
        let extension = match format {
            ReportFormat::Html => "html",
            ReportFormat::Pdf => "pdf",
            ReportFormat::Json => "json",
            ReportFormat::Csv => "csv",
            ReportFormat::Markdown => "md",
        };
        
        format!("{}_{}.{}", strategy_name, timestamp, extension)
    }
    
    /// Generate CSV content from report
    fn generate_csv(&self, report: &Report) -> Result<String, Box<dyn std::error::Error>> {
        let mut csv = String::new();
        
        // Header
        csv.push_str("Metric,Value\n");
        
        // Summary metrics
        csv.push_str(&format!("Total Return,{:.2}%\n", report.summary.total_return));
        csv.push_str(&format!("Sharpe Ratio,{:.2}\n", report.summary.sharpe_ratio));
        csv.push_str(&format!("Max Drawdown,{:.2}%\n", report.summary.max_drawdown));
        csv.push_str(&format!("Win Rate,{:.1}%\n", report.summary.win_rate * 100.0));
        csv.push_str(&format!("Profit Factor,{:.2}\n", report.summary.profit_factor));
        
        // Risk metrics
        csv.push_str(&format!("VaR 95%,{:.2}\n", report.risk_analysis.value_at_risk_95));
        csv.push_str(&format!("CVaR 95%,{:.2}\n", report.risk_analysis.conditional_var_95));
        csv.push_str(&format!("Max Consecutive Losses,{}\n", report.risk_analysis.max_consecutive_losses));
        csv.push_str(&format!("Recovery Factor,{:.2}\n", report.risk_analysis.recovery_factor));
        csv.push_str(&format!("Downside Deviation,{:.2}\n", report.risk_analysis.downside_deviation));
        csv.push_str(&format!("Tail Ratio,{:.2}\n", report.risk_analysis.tail_ratio));
        
        // Trade analysis if available
        if let Some(backtest) = &report.backtest_results {
            csv.push_str(&format!("Total Trades,{}\n", backtest.trade_analysis.total_trades));
            csv.push_str(&format!("Winning Trades,{}\n", backtest.trade_analysis.winning_trades));
            csv.push_str(&format!("Losing Trades,{}\n", backtest.trade_analysis.losing_trades));
            csv.push_str(&format!("Avg Win,{:.2}\n", backtest.trade_analysis.avg_win));
            csv.push_str(&format!("Avg Loss,{:.2}\n", backtest.trade_analysis.avg_loss));
            csv.push_str(&format!("Largest Win,{:.2}\n", backtest.trade_analysis.largest_win));
            csv.push_str(&format!("Largest Loss,{:.2}\n", backtest.trade_analysis.largest_loss));
            csv.push_str(&format!("Avg Duration (min),{:.1}\n", backtest.trade_analysis.avg_duration_minutes));
        }
        
        Ok(csv)
    }
    
    /// Create an archive of all reports
    pub fn create_archive(
        &self,
        reports: Vec<PathBuf>,
        archive_name: &str,
    ) -> Result<PathBuf, Box<dyn std::error::Error>> {
        // In production, would use zip or tar
        // For now, just create a directory
        let archive_dir = self.output_dir.join(archive_name);
        fs::create_dir_all(&archive_dir)?;
        
        for report_path in reports {
            if let Some(filename) = report_path.file_name() {
                let dest = archive_dir.join(filename);
                fs::copy(&report_path, dest)?;
            }
        }
        
        Ok(archive_dir)
    }
}