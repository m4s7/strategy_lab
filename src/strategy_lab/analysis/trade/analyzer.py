"""Trade analysis implementation."""

import logging

import numpy as np
import pandas as pd

from .statistics import TradeStatistics, TradeSummary

logger = logging.getLogger(__name__)


class TradeAnalyzer:
    """Analyzes individual trades and trading patterns."""

    def __init__(self):
        """Initialize trade analyzer."""

    def analyze_trades(
        self, trades: pd.DataFrame, market_data: pd.DataFrame | None = None
    ) -> TradeStatistics:
        """Perform comprehensive trade analysis.

        Args:
            trades: DataFrame with trade information
            market_data: Optional market data for context

        Returns:
            TradeStatistics with analysis results
        """
        if trades.empty:
            return self._empty_statistics()

        # Basic trade analysis
        trade_summary = self._analyze_trade_summary(trades)

        # Distribution analysis
        pnl_distribution = self._analyze_pnl_distribution(trades)

        # Time analysis
        time_analysis = self._analyze_time_patterns(trades)

        # Streak analysis
        streak_analysis = self._analyze_streaks(trades)

        # Entry/exit analysis
        entry_exit_analysis = self._analyze_entry_exit(trades, market_data)

        # Position sizing analysis
        sizing_analysis = self._analyze_position_sizing(trades)

        return TradeStatistics(
            summary=trade_summary,
            pnl_distribution=pnl_distribution,
            time_analysis=time_analysis,
            streak_analysis=streak_analysis,
            entry_exit_analysis=entry_exit_analysis,
            sizing_analysis=sizing_analysis,
        )

    def _analyze_trade_summary(self, trades: pd.DataFrame) -> TradeSummary:
        """Analyze basic trade statistics."""
        winning_trades = trades[trades["pnl"] > 0]
        losing_trades = trades[trades["pnl"] < 0]

        total_trades = len(trades)
        n_winning = len(winning_trades)
        n_losing = len(losing_trades)
        n_breakeven = total_trades - n_winning - n_losing

        win_rate = n_winning / total_trades if total_trades > 0 else 0

        # PnL statistics
        total_pnl = trades["pnl"].sum()
        avg_pnl = trades["pnl"].mean()

        avg_win = winning_trades["pnl"].mean() if n_winning > 0 else 0
        avg_loss = abs(losing_trades["pnl"].mean()) if n_losing > 0 else 0

        max_win = winning_trades["pnl"].max() if n_winning > 0 else 0
        max_loss = abs(losing_trades["pnl"].min()) if n_losing > 0 else 0

        # Win/loss ratio
        win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else np.inf

        # Profit factor
        gross_profit = winning_trades["pnl"].sum() if n_winning > 0 else 0
        gross_loss = abs(losing_trades["pnl"].sum()) if n_losing > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else np.inf

        # Expectancy
        expectancy = win_rate * avg_win - (1 - win_rate) * avg_loss

        # Holding time
        if "holding_time" in trades.columns:
            avg_holding_time = trades["holding_time"].mean()
            avg_win_time = winning_trades["holding_time"].mean() if n_winning > 0 else 0
            avg_loss_time = losing_trades["holding_time"].mean() if n_losing > 0 else 0
        else:
            avg_holding_time = avg_win_time = avg_loss_time = 0

        return TradeSummary(
            total_trades=total_trades,
            winning_trades=n_winning,
            losing_trades=n_losing,
            breakeven_trades=n_breakeven,
            win_rate=win_rate,
            total_pnl=total_pnl,
            avg_pnl=avg_pnl,
            avg_win=avg_win,
            avg_loss=avg_loss,
            max_win=max_win,
            max_loss=max_loss,
            win_loss_ratio=win_loss_ratio,
            profit_factor=profit_factor,
            expectancy=expectancy,
            avg_holding_time=avg_holding_time,
            avg_win_time=avg_win_time,
            avg_loss_time=avg_loss_time,
        )

    def _analyze_pnl_distribution(self, trades: pd.DataFrame) -> dict:
        """Analyze PnL distribution characteristics."""
        pnl = trades["pnl"].values

        # Basic statistics
        distribution = {
            "mean": np.mean(pnl),
            "median": np.median(pnl),
            "std": np.std(pnl),
            "skewness": self._calculate_skewness(pnl),
            "kurtosis": self._calculate_kurtosis(pnl),
            "percentiles": {
                "1%": np.percentile(pnl, 1),
                "5%": np.percentile(pnl, 5),
                "10%": np.percentile(pnl, 10),
                "25%": np.percentile(pnl, 25),
                "50%": np.percentile(pnl, 50),
                "75%": np.percentile(pnl, 75),
                "90%": np.percentile(pnl, 90),
                "95%": np.percentile(pnl, 95),
                "99%": np.percentile(pnl, 99),
            },
        }

        # Distribution shape
        distribution["is_normal"] = self._test_normality(pnl)
        distribution["tail_ratio"] = self._calculate_tail_ratio(pnl)

        # Additional distribution metrics
        distribution["coefficient_of_variation"] = (
            np.std(pnl) / np.mean(pnl) if np.mean(pnl) != 0 else 0
        )
        distribution["interquartile_range"] = np.percentile(pnl, 75) - np.percentile(
            pnl, 25
        )

        # Outlier detection
        q1, q3 = np.percentile(pnl, [25, 75])
        iqr = q3 - q1
        outlier_bounds = {"lower": q1 - 1.5 * iqr, "upper": q3 + 1.5 * iqr}
        outliers = pnl[
            (pnl < outlier_bounds["lower"]) | (pnl > outlier_bounds["upper"])
        ]
        distribution["outliers"] = {
            "count": len(outliers),
            "percentage": len(outliers) / len(pnl) * 100,
            "bounds": outlier_bounds,
        }

        # Bins for histogram
        n_bins = min(50, max(10, len(trades) // 10))
        hist, bins = np.histogram(pnl, bins=n_bins)
        distribution["histogram"] = {"counts": hist.tolist(), "bins": bins.tolist()}

        return distribution

    def _analyze_time_patterns(self, trades: pd.DataFrame) -> dict:
        """Analyze temporal patterns in trading."""
        if "entry_time" not in trades.columns:
            return {}

        trades["hour"] = pd.to_datetime(trades["entry_time"]).dt.hour
        trades["day_of_week"] = pd.to_datetime(trades["entry_time"]).dt.dayofweek
        trades["month"] = pd.to_datetime(trades["entry_time"]).dt.month

        # Hourly analysis
        hourly_stats = (
            trades.groupby("hour")
            .agg(
                {"pnl": ["count", "mean", "sum"], "win_rate": lambda x: (x > 0).mean()}
            )
            .to_dict()
        )

        # Day of week analysis
        dow_stats = (
            trades.groupby("day_of_week")
            .agg(
                {"pnl": ["count", "mean", "sum"], "win_rate": lambda x: (x > 0).mean()}
            )
            .to_dict()
        )

        # Monthly seasonality
        monthly_stats = (
            trades.groupby("month")
            .agg(
                {"pnl": ["count", "mean", "sum"], "win_rate": lambda x: (x > 0).mean()}
            )
            .to_dict()
        )

        # Time between trades
        if len(trades) > 1:
            time_between = (
                pd.to_datetime(trades["entry_time"]).diff().dt.total_seconds() / 3600
            )
            time_between_stats = {
                "mean_hours": time_between.mean(),
                "median_hours": time_between.median(),
                "std_hours": time_between.std(),
            }
        else:
            time_between_stats = {}

        return {
            "hourly": hourly_stats,
            "day_of_week": dow_stats,
            "monthly": monthly_stats,
            "time_between_trades": time_between_stats,
        }

    def _analyze_streaks(self, trades: pd.DataFrame) -> dict:
        """Analyze winning and losing streaks."""
        is_win = trades["pnl"] > 0

        # Calculate streaks
        streaks = []
        current_streak = 0
        current_type = None

        for win in is_win:
            if current_type is None:
                current_type = win
                current_streak = 1
            elif win == current_type:
                current_streak += 1
            else:
                streaks.append((current_type, current_streak))
                current_type = win
                current_streak = 1

        if current_streak > 0:
            streaks.append((current_type, current_streak))

        # Analyze streaks
        win_streaks = [s[1] for s in streaks if s[0]]
        loss_streaks = [s[1] for s in streaks if not s[0]]

        return {
            "max_win_streak": max(win_streaks) if win_streaks else 0,
            "max_loss_streak": max(loss_streaks) if loss_streaks else 0,
            "avg_win_streak": np.mean(win_streaks) if win_streaks else 0,
            "avg_loss_streak": np.mean(loss_streaks) if loss_streaks else 0,
            "current_streak": current_streak,
            "current_streak_type": "win" if current_type else "loss",
            "n_win_streaks": len(win_streaks),
            "n_loss_streaks": len(loss_streaks),
        }

    def _analyze_entry_exit(
        self, trades: pd.DataFrame, market_data: pd.DataFrame | None
    ) -> dict:
        """Analyze entry and exit quality."""
        analysis = {}

        if "entry_price" in trades.columns and "exit_price" in trades.columns:
            # Price movement analysis
            price_moves = trades["exit_price"] - trades["entry_price"]

            analysis["avg_price_move"] = price_moves.mean()
            analysis["price_move_std"] = price_moves.std()

            # Directional accuracy
            if "direction" in trades.columns:
                correct_direction = (
                    (trades["direction"] == "long") & (price_moves > 0)
                ) | ((trades["direction"] == "short") & (price_moves < 0))
                analysis["directional_accuracy"] = correct_direction.mean()

        # Slippage analysis
        if "entry_slippage" in trades.columns:
            analysis["avg_entry_slippage"] = trades["entry_slippage"].mean()
            analysis["total_entry_slippage"] = trades["entry_slippage"].sum()

        if "exit_slippage" in trades.columns:
            analysis["avg_exit_slippage"] = trades["exit_slippage"].mean()
            analysis["total_exit_slippage"] = trades["exit_slippage"].sum()

        # Market impact
        if "volume" in trades.columns and market_data is not None:
            # Calculate participation rate
            analysis["avg_participation_rate"] = self._calculate_participation_rate(
                trades, market_data
            )

        return analysis

    def _analyze_position_sizing(self, trades: pd.DataFrame) -> dict:
        """Analyze position sizing patterns."""
        if "position_size" not in trades.columns:
            return {}

        sizes = trades["position_size"].values

        sizing = {
            "avg_size": np.mean(sizes),
            "std_size": np.std(sizes),
            "min_size": np.min(sizes),
            "max_size": np.max(sizes),
            "size_consistency": 1 - (np.std(sizes) / np.mean(sizes))
            if np.mean(sizes) > 0
            else 0,
        }

        # Size vs performance correlation
        if len(trades) > 10:
            sizing["size_pnl_correlation"] = np.corrcoef(
                trades["position_size"], trades["pnl"]
            )[0, 1]
        else:
            sizing["size_pnl_correlation"] = 0

        # Optimal sizing analysis
        winning_trades = trades[trades["pnl"] > 0]
        losing_trades = trades[trades["pnl"] < 0]

        if len(winning_trades) > 0 and len(losing_trades) > 0:
            sizing["avg_win_size"] = winning_trades["position_size"].mean()
            sizing["avg_loss_size"] = losing_trades["position_size"].mean()
            sizing["win_loss_size_ratio"] = (
                sizing["avg_win_size"] / sizing["avg_loss_size"]
            )

        return sizing

    def _empty_statistics(self) -> TradeStatistics:
        """Return empty statistics when no trades."""
        return TradeStatistics(
            summary=TradeSummary(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                breakeven_trades=0,
                win_rate=0,
                total_pnl=0,
                avg_pnl=0,
                avg_win=0,
                avg_loss=0,
                max_win=0,
                max_loss=0,
                win_loss_ratio=0,
                profit_factor=0,
                expectancy=0,
                avg_holding_time=0,
                avg_win_time=0,
                avg_loss_time=0,
            ),
            pnl_distribution={},
            time_analysis={},
            streak_analysis={},
            entry_exit_analysis={},
            sizing_analysis={},
        )

    def _calculate_skewness(self, data: np.ndarray) -> float:
        """Calculate skewness of distribution."""
        if len(data) < 3:
            return 0

        mean = np.mean(data)
        std = np.std(data)

        if std == 0:
            return 0

        return np.mean(((data - mean) / std) ** 3)

    def _calculate_kurtosis(self, data: np.ndarray) -> float:
        """Calculate kurtosis of distribution."""
        if len(data) < 4:
            return 0

        mean = np.mean(data)
        std = np.std(data)

        if std == 0:
            return 0

        return np.mean(((data - mean) / std) ** 4) - 3

    def _test_normality(self, data: np.ndarray) -> bool:
        """Test if distribution is approximately normal."""
        if len(data) < 30:
            return False

        # Simple normality test using skewness and kurtosis
        skew = abs(self._calculate_skewness(data))
        kurt = abs(self._calculate_kurtosis(data))

        return skew < 0.5 and kurt < 3

    def _calculate_tail_ratio(self, data: np.ndarray) -> float:
        """Calculate tail ratio (95th percentile / 5th percentile)."""
        if len(data) < 20:
            return 0

        p95 = np.percentile(data, 95)
        p5 = abs(np.percentile(data, 5))

        return p95 / p5 if p5 > 0 else np.inf

    def _calculate_participation_rate(
        self, trades: pd.DataFrame, market_data: pd.DataFrame
    ) -> float:
        """Calculate average market participation rate."""
        # This is a simplified implementation
        # Would need proper market volume data
        return 0.0

    def analyze_trade_clustering(self, trades: pd.DataFrame) -> dict:
        """Analyze trade clustering patterns."""
        if len(trades) < 10 or "entry_time" not in trades.columns:
            return {}

        # Time-based clustering
        entry_times = pd.to_datetime(trades["entry_time"])
        time_diffs = entry_times.diff().dt.total_seconds() / 60  # Minutes

        clustering = {
            "avg_time_between_trades": time_diffs.mean(),
            "median_time_between_trades": time_diffs.median(),
            "trade_density": len(trades)
            / ((entry_times.max() - entry_times.min()).days + 1),
        }

        # Identify clusters (trades within 60 minutes of each other)
        cluster_threshold = 60  # minutes
        clusters = []
        current_cluster = [0]

        for i in range(1, len(time_diffs)):
            if pd.notna(time_diffs.iloc[i]) and time_diffs.iloc[i] <= cluster_threshold:
                current_cluster.append(i)
            else:
                if len(current_cluster) > 1:
                    clusters.append(current_cluster)
                current_cluster = [i]

        if len(current_cluster) > 1:
            clusters.append(current_cluster)

        clustering["n_clusters"] = len(clusters)
        clustering["avg_cluster_size"] = (
            np.mean([len(c) for c in clusters]) if clusters else 0
        )
        clustering["max_cluster_size"] = (
            max([len(c) for c in clusters]) if clusters else 0
        )

        # Analyze cluster performance
        if clusters:
            cluster_pnls = []
            for cluster in clusters:
                cluster_pnl = trades.iloc[cluster]["pnl"].sum()
                cluster_pnls.append(cluster_pnl)

            clustering["avg_cluster_pnl"] = np.mean(cluster_pnls)
            clustering["cluster_win_rate"] = sum(p > 0 for p in cluster_pnls) / len(
                cluster_pnls
            )

        return clustering

    def analyze_trade_patterns(self, trades: pd.DataFrame) -> dict:
        """Analyze patterns in trade sequences."""
        if len(trades) < 20:
            return {}

        patterns = {}

        # Win/loss patterns
        is_win = (trades["pnl"] > 0).astype(int)

        # After-win/loss performance
        win_after_win = []
        win_after_loss = []

        for i in range(1, len(is_win)):
            if is_win.iloc[i - 1] == 1:  # Previous was win
                win_after_win.append(is_win.iloc[i])
            else:  # Previous was loss
                win_after_loss.append(is_win.iloc[i])

        patterns["win_rate_after_win"] = np.mean(win_after_win) if win_after_win else 0
        patterns["win_rate_after_loss"] = (
            np.mean(win_after_loss) if win_after_loss else 0
        )

        # Momentum effect
        patterns["has_momentum"] = bool(
            patterns["win_rate_after_win"] > patterns["win_rate_after_loss"]
        )

        # Mean reversion effect
        patterns["has_mean_reversion"] = bool(
            patterns["win_rate_after_loss"] > patterns["win_rate_after_win"]
        )

        # Trade size patterns after wins/losses
        if "position_size" in trades.columns:
            size_after_win = []
            size_after_loss = []

            for i in range(1, len(trades)):
                if trades.iloc[i - 1]["pnl"] > 0:
                    size_after_win.append(trades.iloc[i]["position_size"])
                else:
                    size_after_loss.append(trades.iloc[i]["position_size"])

            patterns["avg_size_after_win"] = (
                np.mean(size_after_win) if size_after_win else 0
            )
            patterns["avg_size_after_loss"] = (
                np.mean(size_after_loss) if size_after_loss else 0
            )
            patterns["scales_up_after_wins"] = (
                patterns["avg_size_after_win"] > patterns["avg_size_after_loss"]
            )

        return patterns

    def calculate_kelly_criterion(self, trades: pd.DataFrame) -> dict:
        """Calculate Kelly Criterion for optimal position sizing."""
        wins = trades[trades["pnl"] > 0]["pnl"]
        losses = trades[trades["pnl"] < 0]["pnl"]

        if len(wins) == 0 or len(losses) == 0:
            return {"kelly_fraction": 0, "half_kelly": 0}

        win_rate = len(wins) / len(trades)
        avg_win = wins.mean()
        avg_loss = abs(losses.mean())

        # Kelly formula: f = (p * b - q) / b
        # where p = win rate, q = loss rate, b = win/loss ratio
        b = avg_win / avg_loss
        kelly = (win_rate * b - (1 - win_rate)) / b

        return {
            "kelly_fraction": max(0, min(kelly, 0.25)),  # Cap at 25%
            "half_kelly": max(0, min(kelly / 2, 0.125)),  # Half Kelly
            "quarter_kelly": max(0, min(kelly / 4, 0.0625)),  # Quarter Kelly
        }
