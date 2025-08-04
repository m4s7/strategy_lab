"""Walk-forward analysis scheduler for time window management."""

import logging
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class WindowDefinition:
    """Defines a time window for walk-forward analysis."""

    in_sample_start: datetime
    in_sample_end: datetime
    out_of_sample_start: datetime
    out_of_sample_end: datetime
    window_id: int

    @property
    def in_sample_period(self) -> tuple[datetime, datetime]:
        """Get in-sample period tuple."""
        return (self.in_sample_start, self.in_sample_end)

    @property
    def out_of_sample_period(self) -> tuple[datetime, datetime]:
        """Get out-of-sample period tuple."""
        return (self.out_of_sample_start, self.out_of_sample_end)

    @property
    def in_sample_days(self) -> int:
        """Get number of in-sample days."""
        return (self.in_sample_end - self.in_sample_start).days

    @property
    def out_of_sample_days(self) -> int:
        """Get number of out-of-sample days."""
        return (self.out_of_sample_end - self.out_of_sample_start).days

    def contains_date(self, date: datetime) -> str:
        """Check if date is in window and return period type."""
        if self.in_sample_start <= date <= self.in_sample_end:
            return "in_sample"
        if self.out_of_sample_start <= date <= self.out_of_sample_end:
            return "out_of_sample"
        return "none"


class WalkForwardScheduler:
    """Manages time windows for walk-forward analysis."""

    def __init__(
        self,
        start_date: datetime,
        end_date: datetime,
        in_sample_days: int,
        out_of_sample_days: int,
        step_days: int,
        overlap: bool = False,
        gap_days: int = 0,
    ):
        """Initialize scheduler.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            in_sample_days: Number of days for in-sample period
            out_of_sample_days: Number of days for out-of-sample period
            step_days: Number of days to step forward each iteration
            overlap: Whether windows can overlap
            gap_days: Gap between in-sample and out-of-sample periods
        """
        self.start_date = start_date
        self.end_date = end_date
        self.in_sample_days = in_sample_days
        self.out_of_sample_days = out_of_sample_days
        self.step_days = step_days
        self.overlap = overlap
        self.gap_days = gap_days

        # Validate configuration
        self._validate_config()

        # Pre-generate all windows
        self.windows = list(self._generate_windows())

        logger.info(
            f"Created walk-forward scheduler with {len(self.windows)} windows "
            f"from {start_date.date()} to {end_date.date()}"
        )

    def _validate_config(self):
        """Validate scheduler configuration."""
        if self.in_sample_days <= 0:
            raise ValueError("in_sample_days must be positive")
        if self.out_of_sample_days <= 0:
            raise ValueError("out_of_sample_days must be positive")
        if self.step_days <= 0:
            raise ValueError("step_days must be positive")
        if self.gap_days < 0:
            raise ValueError("gap_days cannot be negative")
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")

        # Check if there's enough data
        total_days = (self.end_date - self.start_date).days
        min_days = self.in_sample_days + self.gap_days + self.out_of_sample_days
        if total_days < min_days:
            raise ValueError(
                f"Insufficient data: need at least {min_days} days, "
                f"but only have {total_days} days"
            )

    def _generate_windows(self) -> Iterator[WindowDefinition]:
        """Generate all walk-forward windows."""
        window_id = 0
        current_start = self.start_date

        while True:
            # Calculate window dates
            in_sample_start = current_start
            in_sample_end = in_sample_start + timedelta(days=self.in_sample_days - 1)
            out_of_sample_start = in_sample_end + timedelta(days=self.gap_days + 1)
            out_of_sample_end = out_of_sample_start + timedelta(
                days=self.out_of_sample_days - 1
            )

            # Check if window fits within data range
            if out_of_sample_end > self.end_date:
                break

            # Create window definition
            window = WindowDefinition(
                in_sample_start=in_sample_start,
                in_sample_end=in_sample_end,
                out_of_sample_start=out_of_sample_start,
                out_of_sample_end=out_of_sample_end,
                window_id=window_id,
            )

            yield window

            # Move to next window
            window_id += 1
            if self.overlap:
                current_start += timedelta(days=self.step_days)
            else:
                # Non-overlapping: start after out-of-sample period
                current_start = out_of_sample_end + timedelta(days=1)

    def get_window(self, window_id: int) -> WindowDefinition:
        """Get specific window by ID."""
        if window_id < 0 or window_id >= len(self.windows):
            raise IndexError(f"Invalid window_id: {window_id}")
        return self.windows[window_id]

    def get_windows_for_date(
        self, date: datetime
    ) -> list[tuple[WindowDefinition, str]]:
        """Get all windows containing a specific date.

        Returns:
            List of tuples (window, period_type) where period_type is
            'in_sample' or 'out_of_sample'
        """
        results = []
        for window in self.windows:
            period_type = window.contains_date(date)
            if period_type != "none":
                results.append((window, period_type))
        return results

    def get_coverage_analysis(self) -> pd.DataFrame:
        """Analyze date coverage by windows.

        Returns:
            DataFrame with date coverage statistics
        """
        date_range = pd.date_range(self.start_date, self.end_date, freq="D")
        coverage_data = []

        for date in date_range:
            windows_info = self.get_windows_for_date(date)

            in_sample_count = sum(
                1 for _, ptype in windows_info if ptype == "in_sample"
            )
            out_of_sample_count = sum(
                1 for _, ptype in windows_info if ptype == "out_of_sample"
            )

            coverage_data.append(
                {
                    "date": date,
                    "in_sample_windows": in_sample_count,
                    "out_of_sample_windows": out_of_sample_count,
                    "total_windows": len(windows_info),
                    "is_covered": len(windows_info) > 0,
                }
            )

        return pd.DataFrame(coverage_data)

    def visualize_schedule(self) -> str:
        """Create text visualization of window schedule."""
        lines = []
        lines.append(f"Walk-Forward Schedule ({len(self.windows)} windows)")
        lines.append("=" * 80)

        for i, window in enumerate(self.windows[:10]):  # Show first 10
            lines.append(f"Window {window.window_id}:")
            lines.append(
                f"  In-Sample:       {window.in_sample_start.date()} to {window.in_sample_end.date()} ({window.in_sample_days} days)"
            )
            lines.append(
                f"  Out-of-Sample:   {window.out_of_sample_start.date()} to {window.out_of_sample_end.date()} ({window.out_of_sample_days} days)"
            )

            if i < len(self.windows) - 1:
                lines.append("")

        if len(self.windows) > 10:
            lines.append(f"\n... and {len(self.windows) - 10} more windows")

        return "\n".join(lines)

    def get_summary(self) -> dict:
        """Get scheduler summary statistics."""
        coverage_df = self.get_coverage_analysis()

        return {
            "total_windows": len(self.windows),
            "total_days": (self.end_date - self.start_date).days,
            "in_sample_days": self.in_sample_days,
            "out_of_sample_days": self.out_of_sample_days,
            "step_days": self.step_days,
            "overlap": self.overlap,
            "gap_days": self.gap_days,
            "coverage_stats": {
                "days_covered": coverage_df["is_covered"].sum(),
                "max_overlapping_windows": coverage_df["total_windows"].max(),
                "avg_windows_per_day": coverage_df["total_windows"].mean(),
            },
        }

    def __len__(self) -> int:
        """Get number of windows."""
        return len(self.windows)

    def __iter__(self) -> Iterator[WindowDefinition]:
        """Iterate over windows."""
        return iter(self.windows)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"WalkForwardScheduler(windows={len(self.windows)}, "
            f"in_sample={self.in_sample_days}d, "
            f"out_of_sample={self.out_of_sample_days}d, "
            f"step={self.step_days}d)"
        )
