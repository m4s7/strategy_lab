"use client";

import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  CheckCircle,
  AlertCircle,
  AlertTriangle,
  TrendingUp,
  Shield,
  Target,
  Info,
  ExternalLink,
} from "lucide-react";
import { RiskMetrics, Recommendation } from "@/lib/risk/types";

interface RiskRecommendationsProps {
  metrics?: RiskMetrics;
}

export function RiskRecommendations({ metrics }: RiskRecommendationsProps) {
  const recommendations = useMemo(() => {
    if (!metrics) return [];

    const recs: Recommendation[] = [];

    // Analyze maximum drawdown
    if (metrics.maxDrawdown > 0.25) {
      recs.push({
        severity: 'high',
        title: 'Critical Maximum Drawdown',
        description: `Your maximum drawdown of ${(metrics.maxDrawdown * 100).toFixed(1)}% is critically high and exceeds most institutional risk tolerance levels.`,
        action: 'Immediately implement stricter stop-loss rules, reduce position sizes, and consider portfolio diversification. Review your risk management framework.'
      });
    } else if (metrics.maxDrawdown > 0.15) {
      recs.push({
        severity: 'medium',
        title: 'High Maximum Drawdown',
        description: `Your maximum drawdown of ${(metrics.maxDrawdown * 100).toFixed(1)}% exceeds recommended levels for most strategies.`,
        action: 'Consider implementing dynamic position sizing based on volatility and tighter stop-loss rules to reduce peak-to-trough losses.'
      });
    } else if (metrics.maxDrawdown > 0.10) {
      recs.push({
        severity: 'low',
        title: 'Moderate Maximum Drawdown',
        description: `Your maximum drawdown of ${(metrics.maxDrawdown * 100).toFixed(1)}% is within acceptable ranges but could be improved.`,
        action: 'Monitor drawdown patterns and consider implementing trailing stops or volatility-based position sizing.'
      });
    }

    // Analyze Value at Risk
    if (Math.abs(metrics.var95) > 0.06) {
      recs.push({
        severity: 'high',
        title: 'High Value at Risk',
        description: `Your 95% VaR of ${(Math.abs(metrics.var95) * 100).toFixed(1)}% indicates significant daily loss potential.`,
        action: 'Reduce leverage, diversify holdings, and implement intraday risk limits. Consider using VaR-based position sizing.'
      });
    } else if (Math.abs(metrics.var95) > 0.04) {
      recs.push({
        severity: 'medium',
        title: 'Elevated Value at Risk',
        description: `Your 95% VaR of ${(Math.abs(metrics.var95) * 100).toFixed(1)}% suggests moderate daily risk exposure.`,
        action: 'Monitor position concentrations and consider implementing dynamic hedging strategies during volatile periods.'
      });
    }

    // Analyze tail risk
    if (metrics.tailRatio < 0.3) {
      recs.push({
        severity: 'high',
        title: 'Negative Tail Risk Asymmetry',
        description: 'Your strategy shows poor tail risk characteristics with larger left tail losses than right tail gains.',
        action: 'Review strategy logic for asymmetric position sizing, implement better exit rules, and consider tail risk hedging strategies.'
      });
    } else if (metrics.tailRatio < 0.5) {
      recs.push({
        severity: 'medium',
        title: 'Suboptimal Tail Risk Balance',
        description: 'Your tail risk profile shows limited upside capture relative to downside exposure.',
        action: 'Consider asymmetric position sizing that increases exposure during favorable conditions and reduces it during adverse ones.'
      });
    }

    // Analyze Calmar ratio
    if (metrics.calmarRatio < 0.5) {
      recs.push({
        severity: 'high',
        title: 'Poor Risk-Adjusted Returns',
        description: `Your Calmar ratio of ${metrics.calmarRatio.toFixed(2)} indicates poor return relative to maximum drawdown.`,
        action: 'Focus on improving risk-adjusted returns through better entry/exit timing, risk management, or strategy refinement.'
      });
    } else if (metrics.calmarRatio < 1.0) {
      recs.push({
        severity: 'medium',
        title: 'Below-Average Risk-Adjusted Returns',
        description: `Your Calmar ratio of ${metrics.calmarRatio.toFixed(2)} suggests room for improvement in risk-adjusted performance.`,
        action: 'Analyze periods of underperformance and drawdown to identify optimization opportunities in your strategy.'
      });
    }

    // Analyze Sortino ratio
    if (metrics.sortinoRatio < 0.5) {
      recs.push({
        severity: 'medium',
        title: 'Poor Downside Risk Management',
        description: `Your Sortino ratio of ${metrics.sortinoRatio.toFixed(2)} indicates insufficient compensation for downside volatility.`,
        action: 'Focus on reducing downside deviation through better market timing, defensive positioning, or volatility filters.'
      });
    }

    // Analyze Omega ratio
    if (metrics.omega < 1.0) {
      recs.push({
        severity: 'high',
        title: 'Negative Omega Ratio',
        description: `Your Omega ratio of ${metrics.omega.toFixed(2)} indicates total losses exceed total gains.`,
        action: 'Immediate strategy review required. Losses are exceeding gains - consider strategy parameters, market conditions, or alternative approaches.'
      });
    } else if (metrics.omega < 1.2) {
      recs.push({
        severity: 'medium',
        title: 'Low Omega Ratio',
        description: `Your Omega ratio of ${metrics.omega.toFixed(2)} suggests limited excess return generation.`,
        action: 'Improve trade selection criteria, exit timing, or consider adding trend-following filters to capture larger moves.'
      });
    }

    // Analyze drawdown duration
    if (metrics.maxDrawdownDuration > 90) {
      recs.push({
        severity: 'high',
        title: 'Extended Drawdown Periods',
        description: `Your maximum drawdown duration of ${metrics.maxDrawdownDuration} days is concerning for capital efficiency.`,
        action: 'Implement time-based stops, periodic strategy reviews, and consider reducing exposure during extended underperformance.'
      });
    } else if (metrics.maxDrawdownDuration > 60) {
      recs.push({
        severity: 'medium',
        title: 'Long Drawdown Recovery',
        description: `Your maximum drawdown duration of ${metrics.maxDrawdownDuration} days suggests slow recovery.`,
        action: 'Monitor drawdown duration actively and consider implementing recovery acceleration techniques or temporary exposure reduction.'
      });
    }

    // Overall risk score and recommendations
    const riskScore = calculateOverallRiskScore(metrics);
    if (riskScore > 75) {
      recs.push({
        severity: 'high',
        title: 'High Overall Risk Profile',
        description: 'Multiple risk metrics indicate your strategy operates at high risk levels.',
        action: 'Conduct comprehensive risk review, implement multiple risk management layers, and consider reducing overall strategy exposure.'
      });
    }

    return recs.sort((a, b) => {
      const severityOrder = { high: 3, medium: 2, low: 1 };
      return severityOrder[b.severity] - severityOrder[a.severity];
    });
  }, [metrics]);

  const riskScore = useMemo(() => {
    return metrics ? calculateOverallRiskScore(metrics) : 0;
  }, [metrics]);

  const riskLevel = riskScore > 70 ? 'high' : riskScore > 40 ? 'medium' : 'low';
  
  const severityStats = useMemo(() => {
    const stats = { high: 0, medium: 0, low: 0 };
    recommendations.forEach(rec => stats[rec.severity]++);
    return stats;
  }, [recommendations]);

  if (!metrics) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-muted rounded w-1/4"></div>
            <div className="h-20 bg-muted rounded"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!recommendations.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <CheckCircle className="h-5 w-5 text-green-600" />
            <span>Risk Profile Assessment</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Alert>
            <CheckCircle className="h-4 w-4" />
            <AlertTitle>Excellent Risk Management</AlertTitle>
            <AlertDescription>
              Your strategy's risk metrics are within optimal parameters. Continue monitoring 
              performance and maintain current risk management practices.
            </AlertDescription>
          </Alert>
          
          <div className="mt-4">
            <div className="flex items-center space-x-2">
              <span className="text-sm text-muted-foreground">Overall Risk Score:</span>
              <Badge variant="default" className="bg-green-100 text-green-800">
                {riskScore}/100 - LOW RISK
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center space-x-2">
            <Shield className="h-5 w-5" />
            <span>Risk Management Recommendations</span>
          </CardTitle>
          
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <div className="text-sm text-muted-foreground">Risk Score</div>
              <div className="flex items-center space-x-2">
                <Progress value={riskScore} className="w-20" />
                <Badge variant={
                  riskLevel === 'high' ? 'destructive' : 
                  riskLevel === 'medium' ? 'secondary' : 'default'
                }>
                  {riskScore}/100
                </Badge>
              </div>
            </div>
          </div>
        </div>
        
        {/* Summary Stats */}
        <div className="flex items-center space-x-4 mt-4">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <span className="text-sm">
              <strong>{severityStats.high}</strong> Critical
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <AlertCircle className="h-4 w-4 text-yellow-600" />
            <span className="text-sm">
              <strong>{severityStats.medium}</strong> Medium
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <Info className="h-4 w-4 text-blue-600" />
            <span className="text-sm">
              <strong>{severityStats.low}</strong> Low
            </span>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-4">
          {recommendations.map((rec, idx) => {
            const IconComponent = 
              rec.severity === 'high' ? AlertTriangle :
              rec.severity === 'medium' ? AlertCircle : Info;
            
            const variant = 
              rec.severity === 'high' ? 'destructive' :
              rec.severity === 'medium' ? 'default' : 'default';

            return (
              <Alert key={idx} variant={rec.severity === 'high' ? 'destructive' : 'default'}>
                <IconComponent className="h-4 w-4" />
                <AlertTitle className="flex items-center justify-between">
                  <span>{rec.title}</span>
                  <Badge variant="outline" className={
                    rec.severity === 'high' ? 'border-red-200 text-red-700' :
                    rec.severity === 'medium' ? 'border-yellow-200 text-yellow-700' :
                    'border-blue-200 text-blue-700'
                  }>
                    {rec.severity.toUpperCase()}
                  </Badge>
                </AlertTitle>
                <AlertDescription className="mt-2">
                  <p className="mb-3">{rec.description}</p>
                  <div className="bg-muted/50 p-3 rounded-md">
                    <p className="text-sm">
                      <strong className="text-foreground">Recommended Action:</strong> {rec.action}
                    </p>
                  </div>
                </AlertDescription>
              </Alert>
            );
          })}
        </div>

        {/* Action Items Summary */}
        <Card className="mt-6 bg-muted/20">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center space-x-2">
              <Target className="h-4 w-4" />
              <span>Immediate Action Items</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {recommendations
                .filter(rec => rec.severity === 'high')
                .map((rec, idx) => (
                  <div key={idx} className="flex items-start space-x-3">
                    <div className="flex-shrink-0 mt-1">
                      <div className="h-2 w-2 bg-red-600 rounded-full"></div>
                    </div>
                    <p className="text-sm">{rec.action}</p>
                  </div>
                ))}
              
              {recommendations.filter(rec => rec.severity === 'high').length === 0 && (
                <p className="text-sm text-muted-foreground italic">
                  No immediate critical actions required. Continue monitoring medium-priority recommendations.
                </p>
              )}
            </div>
            
            <div className="flex items-center space-x-2 mt-4 pt-4 border-t">
              <Button variant="outline" size="sm">
                <TrendingUp className="h-4 w-4 mr-2" />
                Optimize Strategy
              </Button>
              <Button variant="outline" size="sm">
                <ExternalLink className="h-4 w-4 mr-2" />
                Risk Guidelines
              </Button>
            </div>
          </CardContent>
        </Card>
      </CardContent>
    </Card>
  );
}

function calculateOverallRiskScore(metrics: RiskMetrics): number {
  let score = 0;
  
  // Max drawdown score (0-25 points)
  const ddScore = Math.min(25, (metrics.maxDrawdown / 0.3) * 25);
  score += ddScore;
  
  // VaR score (0-20 points)
  const varScore = Math.min(20, (Math.abs(metrics.var95) / 0.08) * 20);
  score += varScore;
  
  // Tail ratio score (0-15 points) - inverted (lower is worse)
  const tailScore = Math.max(0, 15 - (metrics.tailRatio * 15));
  score += tailScore;
  
  // Calmar ratio score (0-15 points) - inverted
  const calmarScore = Math.max(0, 15 - Math.min(15, metrics.calmarRatio * 7.5));
  score += calmarScore;
  
  // Sortino ratio score (0-10 points) - inverted  
  const sortinoScore = Math.max(0, 10 - Math.min(10, metrics.sortinoRatio * 5));
  score += sortinoScore;
  
  // Omega ratio score (0-10 points) - inverted
  const omegaScore = Math.max(0, 10 - Math.min(10, (metrics.omega - 0.5) * 10));
  score += omegaScore;
  
  // Duration score (0-5 points)
  const durationScore = Math.min(5, (metrics.maxDrawdownDuration / 120) * 5);
  score += durationScore;
  
  return Math.round(Math.min(100, score));
}