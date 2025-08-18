//! Report templates for different formats

use super::*;

/// HTML report template
pub fn html_template(report: &Report) -> String {
    format!(r#"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{} - Strategy Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .metric-label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .recommendation {{
            background: white;
            padding: 15px;
            border-left: 4px solid #667eea;
            margin-bottom: 15px;
            border-radius: 4px;
        }}
        .priority-critical {{ border-left-color: #e53e3e; }}
        .priority-high {{ border-left-color: #ed8936; }}
        .priority-medium {{ border-left-color: #ecc94b; }}
        .priority-low {{ border-left-color: #48bb78; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{}</h1>
        <p>Generated: {} | Author: {}</p>
    </div>
    
    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-label">Total Return</div>
            <div class="metric-value">{:.2}%</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Sharpe Ratio</div>
            <div class="metric-value">{:.2}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Max Drawdown</div>
            <div class="metric-value">{:.2}%</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Win Rate</div>
            <div class="metric-value">{:.1}%</div>
        </div>
    </div>
    
    <div class="chart-container">
        <h2>Key Findings</h2>
        <ul>
            {}
        </ul>
    </div>
    
    <div class="chart-container">
        <h2>Risk Analysis</h2>
        <table style="width: 100%;">
            <tr><td>Value at Risk (95%)</td><td><strong>${:.2}</strong></td></tr>
            <tr><td>Conditional VaR (95%)</td><td><strong>${:.2}</strong></td></tr>
            <tr><td>Max Consecutive Losses</td><td><strong>{}</strong></td></tr>
            <tr><td>Recovery Factor</td><td><strong>{:.2}</strong></td></tr>
        </table>
    </div>
    
    <div class="chart-container">
        <h2>Recommendations</h2>
        {}
    </div>
</body>
</html>
    "#,
        report.metadata.strategy_name,
        report.metadata.strategy_name,
        report.metadata.generated_at.format("%Y-%m-%d %H:%M:%S"),
        report.metadata.author,
        report.summary.total_return,
        report.summary.sharpe_ratio,
        report.summary.max_drawdown,
        report.summary.win_rate * 100.0,
        report.summary.key_findings.iter()
            .map(|f| format!("<li>{}</li>", f))
            .collect::<Vec<_>>()
            .join("\n"),
        report.risk_analysis.value_at_risk_95,
        report.risk_analysis.conditional_var_95,
        report.risk_analysis.max_consecutive_losses,
        report.risk_analysis.recovery_factor,
        format_recommendations(&report.recommendations)
    )
}

/// Markdown report template
pub fn markdown_template(report: &Report) -> String {
    format!(r#"
# {} Strategy Report

**Generated:** {}  
**Author:** {}  
**Data Period:** {} to {}

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Return | {:.2}% |
| Sharpe Ratio | {:.2} |
| Max Drawdown | {:.2}% |
| Win Rate | {:.1}% |
| Profit Factor | {:.2} |

## Key Findings

{}

## Risk Analysis

- **Value at Risk (95%):** ${:.2}
- **Conditional VaR (95%):** ${:.2}
- **Max Consecutive Losses:** {}
- **Recovery Factor:** {:.2}
- **Downside Deviation:** {:.2}%
- **Tail Ratio:** {:.2}

## Recommendations

{}

---
*Report generated by Strategy Lab v{}*
    "#,
        report.metadata.strategy_name,
        report.metadata.generated_at.format("%Y-%m-%d %H:%M:%S"),
        report.metadata.author,
        report.metadata.data_period.start.format("%Y-%m-%d"),
        report.metadata.data_period.end.format("%Y-%m-%d"),
        report.summary.total_return,
        report.summary.sharpe_ratio,
        report.summary.max_drawdown,
        report.summary.win_rate * 100.0,
        report.summary.profit_factor,
        report.summary.key_findings.iter()
            .map(|f| format!("- {}", f))
            .collect::<Vec<_>>()
            .join("\n"),
        report.risk_analysis.value_at_risk_95,
        report.risk_analysis.conditional_var_95,
        report.risk_analysis.max_consecutive_losses,
        report.risk_analysis.recovery_factor,
        report.risk_analysis.downside_deviation,
        report.risk_analysis.tail_ratio,
        format_recommendations_markdown(&report.recommendations),
        report.metadata.version
    )
}

/// Format recommendations for HTML
fn format_recommendations(recommendations: &[Recommendation]) -> String {
    recommendations.iter()
        .map(|rec| {
            format!(
                r#"<div class="recommendation priority-{}">
                    <h3>{}</h3>
                    <p>{}</p>
                    <p><strong>Impact:</strong> {}</p>
                </div>"#,
                format!("{:?}", rec.priority).to_lowercase(),
                rec.title,
                rec.description,
                rec.impact
            )
        })
        .collect::<Vec<_>>()
        .join("\n")
}

/// Format recommendations for Markdown
fn format_recommendations_markdown(recommendations: &[Recommendation]) -> String {
    recommendations.iter()
        .map(|rec| {
            format!(
                "### {} [{}]\n\n{}\n\n**Impact:** {}\n",
                rec.title,
                format!("{:?}", rec.priority),
                rec.description,
                rec.impact
            )
        })
        .collect::<Vec<_>>()
        .join("\n")
}