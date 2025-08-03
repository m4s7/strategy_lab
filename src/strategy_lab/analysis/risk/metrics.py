"""Risk metrics data structures."""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class RiskMetrics:
    """Comprehensive risk metrics."""

    volatility: float
    downside_deviation: float
    var_95: float  # Value at Risk (95%)
    var_99: float  # Value at Risk (99%)
    cvar_95: float  # Conditional Value at Risk (95%)
    cvar_99: float  # Conditional Value at Risk (99%)
    skewness: float
    kurtosis: float
    max_drawdown_duration: int
    risk_of_ruin: float
    tail_ratio: float
    concentration_risk: float
    correlation_risk: float
    beta: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "volatility": self.volatility,
            "downside_deviation": self.downside_deviation,
            "var_95": self.var_95,
            "var_99": self.var_99,
            "cvar_95": self.cvar_95,
            "cvar_99": self.cvar_99,
            "skewness": self.skewness,
            "kurtosis": self.kurtosis,
            "max_drawdown_duration": self.max_drawdown_duration,
            "risk_of_ruin": self.risk_of_ruin,
            "tail_ratio": self.tail_ratio,
            "concentration_risk": self.concentration_risk,
            "correlation_risk": self.correlation_risk,
            "beta": self.beta,
        }

    def get_risk_score(self) -> float:
        """Calculate overall risk score (0-100, higher is riskier)."""
        score = 0.0

        # Volatility component (0-30 points)
        if self.volatility < 0.10:
            vol_score = 0
        elif self.volatility < 0.20:
            vol_score = 15
        else:
            vol_score = 30
        score += vol_score

        # Tail risk component (0-20 points)
        if self.tail_ratio > 2.0:
            tail_score = 0
        elif self.tail_ratio > 1.0:
            tail_score = 10
        else:
            tail_score = 20
        score += tail_score

        # Drawdown component (0-20 points)
        if self.max_drawdown_duration < 30:
            dd_score = 0
        elif self.max_drawdown_duration < 90:
            dd_score = 10
        else:
            dd_score = 20
        score += dd_score

        # Skewness component (0-15 points)
        if self.skewness > 0:
            skew_score = 0
        elif self.skewness > -1:
            skew_score = 7
        else:
            skew_score = 15
        score += skew_score

        # Risk of ruin component (0-15 points)
        score += self.risk_of_ruin * 15

        return min(score, 100)
